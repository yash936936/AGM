"""Command-line interface. Only this module writes human-readable output to stdout."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from .config import ensure_loopback_host, load_key_registry
from .models import Ctx, WriteItem
from .store import MemoryStore


def _demo() -> int:
    with tempfile.TemporaryDirectory(prefix="agm-demo-") as tmp:
        db_path = str(Path(tmp) / "demo.db")
        ctx = Ctx(tenant_id="demo", writer_id="demo-cli", tier="human_verified")
        with MemoryStore(db_path) as store:
            first = store.write(ctx, WriteItem(
                kind="fact", entity="AGM", attribute="phase", value="draft",
                text="AGM is in draft phase", valid_from="2026-01-01T00:00:00Z",
            ))
            corrected = store.write(ctx, WriteItem(
                kind="fact", entity="AGM", attribute="phase", value="Phase 3",
                text="AGM is in Phase 3", valid_from="2026-03-01T00:00:00Z",
            ))
            store.write(ctx, WriteItem(
                kind="episode", text="The design uses an append-only event log.",
            ))
            print("Current memories:")
            for item in store.retrieve(ctx, "AGM phase", entity="AGM", k=8).items:
                print(f"  {item.entity}.{item.attribute} = {item.value} [{item.id}]")
            print("Including superseded memories:")
            for item in store.retrieve(ctx, "AGM phase", entity="AGM", k=8, include_superseded=True).items:
                print(f"  {item.value} [{item.id}]")
            deleted = store.delete(ctx, str(first.item_id))
            print(f"Delete old draft: {deleted.deleted}; replacement: {corrected.item_id}")
    return 0


def _serve_api(args: argparse.Namespace) -> int:
    ensure_loopback_host(args.host)
    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit("REST API dependencies are missing. Run `python -m pip install -e '.[dev]'`.") from exc
    from .api import create_app
    registry = load_key_registry(args.keys)
    if not registry.identities:
        raise SystemExit(
            "No API keys are configured. Copy examples/agm.keys.example.json to agm.keys.json, "
            "replace the sample values with long random keys, and retry."
        )
    uvicorn.run(
        create_app(db_path=args.db, key_registry=registry),
        host=args.host,
        port=args.port,
        log_level="info",
    )
    return 0


def _serve_mcp(args: argparse.Namespace) -> int:
    try:
        from .mcp_server import serve_mcp
        return serve_mcp(transport=args.transport, host=args.host, port=args.port, db_path=args.db)
    except (ImportError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agm", description="Adaptive Graph Memory, Phase 3")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("demo", help="run a temporary write/retrieve/correction/delete demo")

    rebuild = subparsers.add_parser("rebuild", help="rebuild all views from the event log")
    rebuild.add_argument("--db", required=True, metavar="PATH")

    api = subparsers.add_parser("serve-api", help="run the authenticated local REST API")
    api.add_argument("--db", default=None, metavar="PATH", help="SQLite path (default: AGM_DB_PATH or ./agm.db)")
    api.add_argument("--keys", default=None, metavar="PATH", help="JSON API-key file (default: AGM_KEYS_FILE or ./agm.keys.json)")
    api.add_argument("--host", default="127.0.0.1", help="loopback bind address; remote binds are disabled")
    api.add_argument("--port", type=int, default=8765)

    mcp = subparsers.add_parser("serve-mcp", help="run the local MCP server")
    mcp.add_argument("--transport", choices=("stdio", "streamable-http"), default="stdio")
    mcp.add_argument("--db", default=None, metavar="PATH", help="SQLite path (default: AGM_DB_PATH or ./agm.db)")
    mcp.add_argument("--host", default="127.0.0.1", help="loopback bind address for streamable HTTP")
    mcp.add_argument("--port", type=int, default=8766)

    args = parser.parse_args(argv)
    if args.command == "demo":
        return _demo()
    if args.command == "rebuild":
        with MemoryStore(args.db) as store:
            store.rebuild_views()
            count = int(store.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0])
            print(f"Rebuilt views: {count} nodes")
        return 0
    if args.command == "serve-api":
        return _serve_api(args)
    if args.command == "serve-mcp":
        if args.transport == "streamable-http":
            ensure_loopback_host(args.host)
        return _serve_mcp(args)
    return 2
