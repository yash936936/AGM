"""Command-line interface. Only this module writes to stdout."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

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
                kind="fact", entity="AGM", attribute="phase", value="Phase 1",
                text="AGM is in Phase 1", valid_from="2026-02-01T00:00:00Z",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agm", description="Adaptive Graph Memory, Phase 1")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("demo", help="run a temporary write/retrieve/correction/delete demo")
    rebuild = subparsers.add_parser("rebuild", help="rebuild all views from the event log")
    rebuild.add_argument("--db", required=True, metavar="PATH")
    args = parser.parse_args(argv)
    if args.command == "demo":
        return _demo()
    if args.command == "rebuild":
        with MemoryStore(args.db) as store:
            store.rebuild_views()
            count = int(store.conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0])
            print(f"Rebuilt views: {count} nodes")
        return 0
    return 2
