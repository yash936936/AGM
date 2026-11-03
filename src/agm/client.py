"""Dependency-free Python client for the AGM REST API.

Uses only the standard library so any agent runtime can import it. It sends the
API key in ``X-API-Key``, never follows redirects (so the key cannot be forwarded
to another host), and refuses plain ``http://`` to non-loopback hosts unless
``allow_insecure_http=True`` is passed explicitly.

Retrieved memory text is untrusted data. The ``notice`` field returned by
``retrieve`` must be kept in front of the model with the results.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping

DEFAULT_BASE_URL = "http://127.0.0.1:8765"
_LOOPBACK = {"127.0.0.1", "localhost", "::1"}


class AgmError(Exception):
    """Raised for HTTP errors and for connection failures (``status`` is None)."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.detail = message


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        return None


def _model_to_dict(value: Any) -> Any:
    dump = getattr(value, "model_dump", None)
    return dump(mode="json", exclude_none=True) if callable(dump) else value


class AgmClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        *,
        timeout: float = 10.0,
        allow_insecure_http: bool = False,
    ) -> None:
        self.base_url = (base_url or os.environ.get("AGM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self._api_key = api_key or os.environ.get("AGM_API_KEY") or ""
        if not self._api_key:
            raise AgmError("No API key. Set AGM_API_KEY or pass api_key.")
        self.timeout = timeout
        parsed = urllib.parse.urlparse(self.base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise AgmError(f"Invalid base URL: {self.base_url!r}")
        if parsed.scheme == "http" and parsed.hostname.lower() not in _LOOPBACK and not allow_insecure_http:
            raise AgmError("Refusing plain http to a non-loopback host; use https or allow_insecure_http=True.")
        self._opener = urllib.request.build_opener(_NoRedirect)

    @classmethod
    def from_env(cls, **kwargs: Any) -> "AgmClient":
        return cls(**kwargs)

    def __repr__(self) -> str:  # never expose the key
        return f"AgmClient(base_url={self.base_url!r})"

    def _request(self, method: str, path: str, body: Any = None, params: Mapping[str, Any] | None = None) -> Any:
        url = self.base_url + path
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            if query:
                url += "?" + query
        data = None if body is None else json.dumps(_model_to_dict(body)).encode("utf-8")
        request = urllib.request.Request(url, data=data, method=method, headers={
            "X-API-Key": self._api_key, "Accept": "application/json",
            **({"Content-Type": "application/json"} if data is not None else {}),
        })
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise AgmError(_error_detail(exc), exc.code) from None
        except (urllib.error.URLError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            if isinstance(reason, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)) and data is not None:
                # The server may answer early (for example 413) and close while a large body is still being sent;
                # on Windows the response is then lost to a connection reset.
                raise AgmError(f"Connection closed by the server while sending the request to {self.base_url}; "
                               "the request may have been rejected (too large?).") from None
            raise AgmError(f"Cannot reach AGM at {self.base_url}: {reason}") from None
        return json.loads(raw) if raw else None

    # health -----------------------------------------------------------------
    def health(self) -> dict[str, Any]:
        return self._request("GET", "/healthz")

    # memory -----------------------------------------------------------------
    def write(self, item: Mapping[str, Any] | Any) -> dict[str, Any]:
        return self._request("POST", "/v1/memory", item)

    def retrieve(
        self, query: str, *, entity: str | None = None, as_of: str | None = None, k: int = 8,
        expand: bool = True, include_superseded: bool = False, high_stakes: bool = False,
        include_contested: bool = False,
    ) -> dict[str, Any]:
        body = {"query": query, "entity": entity, "as_of": as_of, "k": k, "expand": expand,
                "include_superseded": include_superseded, "high_stakes": high_stakes,
                "include_contested": include_contested}
        return self._request("POST", "/v1/memory/retrieve", {k_: v for k_, v in body.items() if v is not None})

    def supersede(self, item_id: str, item: Mapping[str, Any] | Any, reason: str) -> dict[str, Any]:
        quoted = urllib.parse.quote(item_id, safe="")
        return self._request("POST", f"/v1/memory/{quoted}/supersede", {"item": _model_to_dict(item), "reason": reason})

    def history(self, entity: str, attribute: str | None = None) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/memory/history", params={"entity": entity, "attribute": attribute})

    def delete(self, item_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/v1/memory/{urllib.parse.quote(item_id, safe='')}")

    # active memory (read-only helpers; see D-044) ---------------------------
    def active_context(self, query: str, *, profile_queries: list[str] | None = None,
                       goal_queries: list[str] | None = None, entity: str | None = None, as_of: str | None = None,
                       k: int = 8, token_budget: int = 2000, expand: bool = True,
                       high_stakes: bool = False, include_contested: bool = False) -> dict[str, Any]:
        body = {"query": query, "profile_queries": profile_queries or [], "goal_queries": goal_queries or [],
                "entity": entity, "as_of": as_of, "k": k, "token_budget": token_budget, "expand": expand,
                "high_stakes": high_stakes, "include_contested": include_contested}
        return self._request("POST", "/v1/active/context", {k_: v for k_, v in body.items() if v is not None})

    def active_review(self, current_user_message: str, proposals: list[Mapping[str, Any]]) -> dict[str, Any]:
        return self._request("POST", "/v1/active/review",
                             {"current_user_message": current_user_message, "proposals": proposals})

    # handoff ----------------------------------------------------------------
    def handoff_save(self, session_id: str, task_state: Mapping[str, Any] | Any) -> dict[str, Any]:
        return self._request("POST", "/v1/handoff", {"session_id": session_id, "task_state": _model_to_dict(task_state)})

    def handoff_resume(self, packet_id: str, target_model: str, token_budget: int) -> dict[str, Any]:
        path = f"/v1/handoff/{urllib.parse.quote(packet_id, safe='')}/resume"
        return self._request("POST", path, {"target_model": target_model, "token_budget": token_budget})

    def handoff_readback(self, packet_id: str, readback: Mapping[str, Any] | Any) -> dict[str, Any]:
        path = f"/v1/handoff/{urllib.parse.quote(packet_id, safe='')}/readback"
        return self._request("POST", path, {"readback": _model_to_dict(readback)})

    # sessions ---------------------------------------------------------------
    def create_session(self, label: str = "") -> dict[str, Any]:
        return self._request("POST", "/v1/sessions", {"label": label})

    def list_sessions(self, limit: int = 50) -> Any:
        return self._request("GET", "/v1/sessions", params={"limit": limit})


def _error_detail(exc: urllib.error.HTTPError) -> str:
    try:
        payload = json.loads(exc.read() or b"{}")
        detail = payload.get("detail", payload) if isinstance(payload, dict) else payload
        return detail if isinstance(detail, str) else json.dumps(detail)
    except (ValueError, OSError):
        return exc.reason or "HTTP error"
