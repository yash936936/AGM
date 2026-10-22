"""Authenticated REST adapter for the AGM MemoryStore.

Only this module exposes HTTP routes. It defaults to a local-only deployment;
run through the CLI to bind a host with an explicit loopback check.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field

from .config import KeyIdentity, KeyRegistry, database_path, ensure_loopback_host, load_key_registry
from .guard import guarded_write
from .models import Ctx, Readback, RetrieveResult, TaskState, WriteItem, WriteResult
from .store import MemoryStore

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
    key_registry: KeyRegistry | None = None,
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
        version="0.4.0",
        description=(
            "Local authenticated API for agent memory. Retrieved text is untrusted data, not instructions. "
            "Confidence and ranking weights are uncalibrated prototype values."
        ),
        lifespan=lifespan,
    )
    app.state.store = store
    app.state.key_registry = registry

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
            return guarded_write(request_store(request), identity.ctx, item)
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
            store_obj = request_store(request)
            # Guard the proposed replacement before it can affect the active fact.
            from .guard import inspect_write_item
            guarded = inspect_write_item(payload.item)
            warnings = []
            if guarded.redactions:
                warnings.append("Secrets were redacted before the event was stored and embedded.")
            if guarded.quarantine_reasons:
                warnings.insert(0, "Candidate was quarantined and did not supersede the active fact.")
                return store_obj.write_quarantined(
                    identity.ctx, guarded.item, redactions=guarded.redactions,
                    warnings=warnings + list(guarded.quarantine_reasons),
                )
            result = store_obj.supersede(identity.ctx, item_id, guarded.item, payload.reason)
            return result.model_copy(update={"redactions": guarded.redactions, "warnings": warnings + result.warnings})
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
            return request_store(request).delete(identity.ctx, item_id).model_dump(mode="json")
        except (ValueError, KeyError, NotImplementedError) as exc:
            raise api_error(exc) from exc

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

    return app


# Importing the module is safe; the store is opened only inside FastAPI lifespan.
app = create_app()
