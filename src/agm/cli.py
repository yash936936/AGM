"""Command-line interface. Only this module writes human-readable output to stdout."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from .config import ensure_loopback_host, load_key_registry
from .models import Ctx, Readback, TaskState, WriteItem
from .store import MemoryStore
from .trust import DEFAULT_ARCHIVE_THRESHOLD, lifecycle_candidates


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
                kind="fact", entity="AGM", attribute="phase", value="Phase 5",
                text="AGM is in Phase 5", valid_from="2026-03-01T00:00:00Z",
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
            task = TaskState(
                goal="Continue the AGM prototype safely",
                plan=["Compare flat and graph retrieval", "Review lifecycle candidates"],
                decisions=[{"text": "Keep SQLite as the event store", "rationale": "Single-file local prototype"}],
                open_questions=["Review synthetic evaluation limitations"],
            )
            packet = store.handoff_save(ctx, "phase5-demo", task)
            resumed = store.handoff_resume(ctx, packet.id, "demo-target-model", token_budget=160)
            readback = store.handoff_readback(ctx, packet.id, Readback(
                goal="Continue the AGM prototype safely",
                decisions=["Keep SQLite as the event store"],
                open_items=["Review synthetic evaluation limitations"],
            ))
            print(f"Handoff saved: {packet.id}; estimated context tokens: {resumed.estimated_tokens}")
            print(f"Handoff readback passed: {readback.passed}")
    return 0


def _lifecycle(args: argparse.Namespace) -> int:
    if not args.dry_run:
        raise SystemExit("Phase 5 only supports `agm lifecycle --dry-run`; no archival writes are implemented.")
    try:
        candidates_threshold = float(args.threshold)
    except (TypeError, ValueError) as exc:
        raise SystemExit("--threshold must be a number between 0 and 1") from exc
    if not 0.0 <= candidates_threshold <= 1.0:
        raise SystemExit("--threshold must be between 0 and 1")
    with MemoryStore(args.db) as store:
        candidates = lifecycle_candidates(
            store.conn, threshold=candidates_threshold,
            tenant=args.tenant, project=args.project,
        )
        print(f"Lifecycle dry run: {len(candidates)} candidate(s); threshold={candidates_threshold:.2f}")
        print("No events or memory views were changed.")
        for item in candidates:
            entity = f" entity={item['entity']}" if item["entity"] else ""
            print(
                f"  {item['id']} kind={item['kind']}{entity} "
                f"idle_days={item['idle_days']} decay_weight={item['decay_weight']:.4f} "
                f"usage_count={item['usage_count']}"
            )
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


def _doctor(args: argparse.Namespace) -> int:
    from .diagnostics import run_doctor

    ctx = Ctx(
        tenant_id=args.tenant,
        writer_id=args.writer,
        tier="trusted_agent",
        project=args.project,
    )
    queries = None
    if args.query:
        queries = [
            {
                "id": f"custom-{index + 1}",
                "family": "custom",
                "query": query,
                "entity": args.entity,
                "as_of": args.as_of,
                "gold": [],
            }
            for index, query in enumerate(args.query)
        ]
    with MemoryStore(args.db) as store:
        report = run_doctor(
            store,
            ctx,
            queries=queries,
            modes=args.mode,
            k=args.k,
            log_path=args.log,
            include_content=args.include_content,
            tail_events=args.tail_events,
        )
    print(f"Memory Doctor: {report['status']} (structural audit: {report['audit_status']})")
    print(f"Scope: tenant={args.tenant}, project={args.project}")
    print(f"Retrieval probes: {report['probe_count']}")
    for row in report["queries"]:
        accuracy = "n/a" if row["correctness"] is None else f"{100 * row['correctness']:.1f}%"
        print(
            f"  {row['mode']:5s} {row['family']:16s} {row['probe_id']}: "
            f"correctness={accuracy}, results={row['result_count']}, "
            f"abstain={row['harness_abstain']}, latency={row['elapsed_ms']:.2f} ms, "
            f"SQL={row['sql_statement_count']}"
        )
        for diagnosis in row["diagnosis"]:
            print(f"    DIAGNOSIS: {diagnosis}")
    for finding in report["findings"]:
        print(f"[{finding['severity']}] {finding['code']}: {finding['message']}")
    print(f"Full JSONL trace: {args.log}")
    has_errors = any(row["severity"] == "ERROR" for row in report["findings"])
    return 1 if has_errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agm", description="Adaptive Graph Memory, Phase 5")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("demo", help="run a temporary write/retrieve/correction/delete demo")

    rebuild = subparsers.add_parser("rebuild", help="rebuild all views from the event log")
    rebuild.add_argument("--db", required=True, metavar="PATH")

    api = subparsers.add_parser("serve-api", help="run the authenticated local REST API")
    api.add_argument("--db", default=None, metavar="PATH", help="SQLite path (default: AGM_DB_PATH or ./agm.db)")
    api.add_argument("--keys", default=None, metavar="PATH", help="JSON API-key file (default: AGM_KEYS_FILE or ./agm.keys.json)")
    api.add_argument("--host", default="127.0.0.1", help="loopback bind address; remote binds are disabled")
    api.add_argument("--port", type=int, default=8765)

    lifecycle = subparsers.add_parser("lifecycle", help="inspect memories that would be archived (read-only)")
    lifecycle.add_argument("--db", required=True, metavar="PATH")
    lifecycle.add_argument("--dry-run", action="store_true", required=True,
                          help="required; Phase 5 does not perform archival writes")
    lifecycle.add_argument("--threshold", type=float, default=DEFAULT_ARCHIVE_THRESHOLD,
                          help=f"archive-candidate decay threshold, 0..1 (default: {DEFAULT_ARCHIVE_THRESHOLD})")
    lifecycle.add_argument("--tenant", default=None, help="optional tenant filter")
    lifecycle.add_argument("--project", default=None, help="optional project filter")

    doctor = subparsers.add_parser("doctor", help="audit memory consistency and trace flat/graph retrieval")
    doctor.add_argument("--db", required=True, metavar="PATH", help="SQLite path to inspect")
    doctor.add_argument("--tenant", required=True, help="tenant scope to inspect")
    doctor.add_argument("--project", default="default", help="project scope (default: default)")
    doctor.add_argument("--writer", default="memory-doctor", help="diagnostic identity")
    doctor.add_argument("--query", action="append", help="custom query; repeat to trace multiple queries")
    doctor.add_argument("--entity", default=None, help="optional entity scope for all custom queries")
    doctor.add_argument("--as-of", default=None, help="optional ISO timestamp for temporal custom queries")
    doctor.add_argument("--mode", choices=("flat", "graph"), action="append", help="retrieval mode; default runs both")
    doctor.add_argument("--k", type=int, default=8, help="max retrieved items (default: 8)")
    doctor.add_argument("--log", default="logs/memory-doctor.jsonl", help="append-only JSONL trace path")
    doctor.add_argument("--include-content", action="store_true", help="include secret-redacted query/content snippets in local logs")
    doctor.add_argument("--tail-events", type=int, default=20, help="number of recent tenant events to include (0 disables; default: 20)")

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
    if args.command == "lifecycle":
        return _lifecycle(args)
    if args.command == "serve-api":
        return _serve_api(args)
    if args.command == "doctor":
        return _doctor(args)
    if args.command == "serve-mcp":
        if args.transport == "streamable-http":
            ensure_loopback_host(args.host)
        return _serve_mcp(args)
    return 2
