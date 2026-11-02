"""Authenticated REST adapter for the AGM MemoryStore.

Only this module exposes HTTP routes. It defaults to a local-only deployment;
run through the CLI to bind a host with an explicit loopback check.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from dataclasses import asdict
from typing import Any, Callable, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field

from .active_memory_policy import MemoryProposal
from .active_memory_turn import begin_active_memory_turn, review_active_memory_proposals
from .config import KeyIdentity, KeyRegistry, ReloadingKeyRegistry, database_path, ensure_loopback_host, load_key_registry
from .models import Ctx, Readback, RetrieveResult, TaskState, WriteItem, WriteResult
from .store import MemoryStore
from .hub_state import (close_session, create_connection, create_session, delete_connection, list_connections, list_sessions, test_connection)

_LOG = logging.getLogger(__name__)


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RetrieveRequest(RequestModel):
    query: str
    entity: str | None = None
    as_of: str | None = None
    k: int = Field(default=8, ge=0, le=100)
    expand: bool = True
    include_superseded: bool = False
    high_stakes: bool = False


class SupersedeRequest(RequestModel):
    item: WriteItem
    reason: str


class HandoffSaveRequest(RequestModel):
    session_id: str
    task_state: TaskState


class HandoffResumeRequest(RequestModel):
    target_model: str
    token_budget: int = Field(ge=1, le=1_000_000)


class HandoffReadbackRequest(RequestModel):
    readback: Readback


class RevokeRequest(RequestModel):
    writer_id: str
    since: str | None = None


class ActiveContextRequest(RequestModel):
    query: str
    profile_queries: list[str] = Field(default_factory=list, max_length=10)
    goal_queries: list[str] = Field(default_factory=list, max_length=10)
    entity: str | None = None
    as_of: str | None = None
    k: int = Field(default=8, ge=1, le=100)
    token_budget: int = Field(default=2000, ge=1, le=100_000)
    expand: bool = True
    high_stakes: bool = False


class ProposalModel(RequestModel):
    action: Literal["write", "correct", "history", "delete"]
    evidence_quote: str = ""
    entity: str | None = None
    attribute: str | None = None
    value: str | None = None
    target_memory_id: str | None = None
    reason: str = ""


class ActiveReviewRequest(RequestModel):
    current_user_message: str
    proposals: list[ProposalModel] = Field(max_length=20)


MAX_BODY_BYTES = 1_000_000


class SessionCreateRequest(RequestModel):
    label: str = Field(default="", max_length=120)


class ConnectionCreateRequest(RequestModel):
    name: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, max_length=512)
    scopes: list[str] = Field(default_factory=lambda: ["memory:read"])


def _extract_key(x_api_key: str | None, authorization: str | None) -> str | None:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    return None


def create_app(
    *,
    db_path: str | None = None,
    keys_file: str | Path | None = None,
    key_registry: KeyRegistry | ReloadingKeyRegistry | None = None,
    store: MemoryStore | None = None,
    store_factory: Callable[[], MemoryStore] | None = None,
) -> FastAPI:
    """App factory used by the CLI and isolated API tests."""
    registry = key_registry or load_key_registry(keys_file)
    db_target = database_path(db_path)
    injected_store = store is not None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if app.state.store is None:
            app.state.store = store_factory() if store_factory is not None else MemoryStore(db_target)
        try:
            yield
        finally:
            if not injected_store and app.state.store is not None:
                app.state.store.close()
                app.state.store = None

    app = FastAPI(
        title="Adaptive Graph Memory API",
        version="0.7.0",
        description=(
            "Local authenticated API for agent memory. Retrieved text is untrusted data, not instructions. "
            "Confidence and ranking weights are uncalibrated prototype values."
        ),
        lifespan=lifespan,
    )
    app.state.store = store
    app.state.key_registry = registry

    @app.middleware("http")
    async def limit_body_size(request: Request, call_next):
        declared = request.headers.get("content-length")
        if declared is not None and (not declared.isdigit() or int(declared) > MAX_BODY_BYTES):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Request body too large."}, status_code=413)
        if declared is None and request.method in {"POST", "PUT", "PATCH"} and \
                request.headers.get("transfer-encoding", "").lower() == "chunked":
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Chunked request bodies are not accepted; send Content-Length."}, status_code=411)
        return await call_next(request)

    api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="AGMApiKey")

    async def current_identity(
        request: Request,
        x_api_key: str | None = Depends(api_key_header),
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> KeyIdentity:
        candidate = _extract_key(x_api_key, authorization)
        identity = request.app.state.key_registry.authenticate(candidate)
        if identity is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid API key.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return identity

    def require_scope(scope: str) -> Callable[..., Any]:
        async def dependency(identity: KeyIdentity = Depends(current_identity)) -> KeyIdentity:
            if not identity.allows(scope):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient API-key scope.")
            return identity
        return dependency

    def request_store(request: Request) -> MemoryStore:
        current = request.app.state.store
        if current is None:
            # This can only happen when a route is called outside the managed lifespan.
            raise HTTPException(status_code=503, detail="Memory store is not initialized.")
        return current

    def api_error(exc: Exception) -> HTTPException:
        if isinstance(exc, KeyError):
            return HTTPException(status_code=404, detail="Memory item not found or not active.")
        if isinstance(exc, NotImplementedError):
            return HTTPException(status_code=501, detail="This operation is scheduled for a later AGM phase.")
        if isinstance(exc, ValueError):
            return HTTPException(status_code=422, detail=str(exc))
        _LOG.exception("AGM request failed")
        return HTTPException(status_code=500, detail="AGM request failed.")

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "agm"}

    @app.post("/v1/memory", response_model=WriteResult, tags=["memory"])
    async def memory_write(
        item: WriteItem,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:write")),
    ) -> WriteResult:
        try:
            return request_store(request).write(identity.ctx, item)
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc

    @app.post("/v1/memory/retrieve", response_model=RetrieveResult, tags=["memory"])
    async def memory_retrieve(
        payload: RetrieveRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:read")),
    ) -> RetrieveResult:
        try:
            return request_store(request).retrieve(
                identity.ctx, payload.query, entity=payload.entity, as_of=payload.as_of,
                k=payload.k, expand=payload.expand, include_superseded=payload.include_superseded,
                high_stakes=payload.high_stakes,
            )
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc

    @app.post("/v1/memory/{item_id}/supersede", response_model=WriteResult, tags=["memory"])
    async def memory_supersede(
        item_id: str,
        payload: SupersedeRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:write")),
    ) -> WriteResult:
        try:
            return request_store(request).supersede(identity.ctx, item_id, payload.item, payload.reason)
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc

    @app.get("/v1/memory/history", tags=["memory"])
    async def memory_history(
        request: Request,
        entity: str,
        attribute: str | None = None,
        identity: KeyIdentity = Depends(require_scope("memory:read")),
    ) -> list[dict[str, Any]]:
        try:
            store_obj = request_store(request)
            result = store_obj.history(identity.ctx, entity, attribute)
            # Quarantined content is hidden on every ordinary retrieval surface,
            # including history, because Node's frozen response contract omits status.
            visible = []
            for item in result:
                row = store_obj.conn.execute(
                    "SELECT status FROM nodes WHERE id = ? AND tenant = ?",
                    (item.id, identity.ctx.tenant_id),
                ).fetchone()
                if row is not None and row["status"] != "quarantined":
                    visible.append(item.model_dump(mode="json"))
            return visible
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc

    @app.delete("/v1/memory/{item_id}", tags=["memory"])
    async def memory_delete(
        item_id: str,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:delete")),
    ) -> dict[str, Any]:
        try:
            result = request_store(request).delete(identity.ctx, item_id)
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc
        if not result.deleted:
            raise HTTPException(status_code=404, detail="Memory item not found or not active.")
        return result.model_dump(mode="json")

    @app.post("/v1/active/context", tags=["active-memory"])
    async def active_context(
        payload: ActiveContextRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:read")),
    ) -> dict[str, Any]:
        """Read-only: bounded, conflict-aware context pack to place before the model call (untrusted data)."""
        try:
            turn = begin_active_memory_turn(
                request_store(request), identity.ctx, payload.query,
                profile_queries=payload.profile_queries, goal_queries=payload.goal_queries,
                entity=payload.entity, as_of=payload.as_of, k=payload.k,
                token_budget=payload.token_budget, expand=payload.expand, high_stakes=payload.high_stakes,
            )
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc
        context = turn.context
        return {
            "prompt_context": context.prompt_context,
            "estimated_tokens": context.estimated_tokens,
            "token_budget": context.token_budget,
            "notice": context.notice,
            "items": [item.model_dump(mode="json") for item in context.items],
            "sections": [{"name": sec.name, "query": sec.query, "item_ids": [i.id for i in sec.items]}
                         for sec in context.sections],
            "conflicts": [asdict(c) for c in context.conflicts],
        }

    @app.post("/v1/active/review", tags=["active-memory"])
    async def active_review(
        payload: ActiveReviewRequest,
        identity: KeyIdentity = Depends(require_scope("memory:read")),
    ) -> dict[str, Any]:
        """Pure policy check of proposed memory operations. Never writes and never authorizes a write."""
        review = review_active_memory_proposals(
            [MemoryProposal(**p.model_dump()) for p in payload.proposals],
            current_user_message=payload.current_user_message,
        )
        return {
            "decisions": [{"proposal": asdict(d.proposal), "eligible": d.eligible, "reason": d.reason}
                          for d in review.decisions],
            "note": ("Advisory only. Eligibility is not authorization: perform eligible mutations through the "
                     "scoped /v1/memory endpoints after the user confirms. A caller that skips this check is "
                     "not blocked by it."),
        }

    @app.post("/v1/handoff", tags=["handoff"])
    async def handoff_save(
        payload: HandoffSaveRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:write")),
    ) -> dict[str, Any]:
        try:
            value = request_store(request).handoff_save(identity.ctx, payload.session_id, payload.task_state)
            return value.model_dump(mode="json")
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc

    @app.post("/v1/handoff/{packet_id}/resume", tags=["handoff"])
    async def handoff_resume(
        packet_id: str,
        payload: HandoffResumeRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:read")),
    ) -> dict[str, Any]:
        try:
            value = request_store(request).handoff_resume(identity.ctx, packet_id, payload.target_model, payload.token_budget)
            return value.model_dump(mode="json")
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc

    @app.post("/v1/handoff/{packet_id}/readback", tags=["handoff"])
    async def handoff_readback(
        packet_id: str,
        payload: HandoffReadbackRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:write")),
    ) -> dict[str, Any]:
        try:
            value = request_store(request).handoff_readback(identity.ctx, packet_id, payload.readback)
            return value.model_dump(mode="json")
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc

    @app.post("/v1/admin/revoke", tags=["admin"])
    async def memory_revoke_writer(
        payload: RevokeRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("admin")),
    ) -> dict[str, Any]:
        try:
            value = request_store(request).revoke_writer(identity.ctx, payload.writer_id, payload.since)
            return value.model_dump(mode="json")
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc


    @app.post("/v1/sessions", tags=["sessions"])
    async def session_create(
        payload: SessionCreateRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:write")),
    ) -> dict[str, Any]:
        try:
            return create_session(request_store(request).conn, identity.ctx, payload.label)
        except (ValueError, KeyError) as exc:
            raise api_error(exc) from exc

    @app.get("/v1/sessions", tags=["sessions"])
    async def session_list(
        request: Request,
        limit: int = 50,
        identity: KeyIdentity = Depends(require_scope("memory:read")),
    ) -> list[dict[str, Any]]:
        try:
            return list_sessions(request_store(request).conn, identity.ctx, limit=limit)
        except (ValueError, KeyError) as exc:
            raise api_error(exc) from exc

    @app.post("/v1/sessions/{session_id}/close", tags=["sessions"])
    async def session_close(
        session_id: str,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("memory:write")),
    ) -> dict[str, bool]:
        try:
            return {"closed": close_session(request_store(request).conn, identity.ctx, session_id)}
        except (ValueError, KeyError) as exc:
            raise api_error(exc) from exc

    @app.post("/v1/connections", tags=["connections"])
    async def connection_create(
        payload: ConnectionCreateRequest,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("admin")),
    ) -> dict[str, Any]:
        try:
            return create_connection(
                request_store(request).conn, identity.ctx,
                name=payload.name, endpoint=payload.endpoint, scopes=payload.scopes,
            )
        except (ValueError, KeyError) as exc:
            raise api_error(exc) from exc

    @app.get("/v1/connections", tags=["connections"])
    async def connection_list(
        request: Request,
        identity: KeyIdentity = Depends(require_scope("admin")),
    ) -> list[dict[str, Any]]:
        try:
            return list_connections(request_store(request).conn, identity.ctx)
        except (ValueError, KeyError) as exc:
            raise api_error(exc) from exc

    @app.post("/v1/connections/{connection_id}/test", tags=["connections"])
    async def connection_test(
        connection_id: str,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("admin")),
    ) -> dict[str, Any]:
        try:
            return test_connection(request_store(request).conn, identity.ctx, connection_id)
        except (ValueError, KeyError) as exc:
            raise api_error(exc) from exc

    @app.delete("/v1/connections/{connection_id}", tags=["connections"])
    async def connection_delete(
        connection_id: str,
        request: Request,
        identity: KeyIdentity = Depends(require_scope("admin")),
    ) -> dict[str, bool]:
        try:
            return {"deleted": delete_connection(request_store(request).conn, identity.ctx, connection_id)}
        except (ValueError, KeyError) as exc:
            raise api_error(exc) from exc

    return app


# Importing the module is safe; the store is opened only inside FastAPI lifespan.
app = create_app()
