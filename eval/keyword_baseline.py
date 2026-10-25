#!/usr/bin/env python3
"""Run the standalone fixture-level lexical baseline on a labelled AGM JSONL set.

This baseline uses transparent token overlap and simulates declared lifecycle
operations from the fixture. It is not AGM's SQLite FTS implementation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from eval.benchmark_runner import evaluate_keyword_baseline
from scripts.evaluate_real_history import load_cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmark", type=Path, help="labelled JSONL benchmark")
    parser.add_argument("--output", type=Path, help="optional aggregate JSON report path")
    args = parser.parse_args()
    try:
        cases = load_cases(args.benchmark)
        report = {
            "protocol": "agm_fixture_keyword_baseline_v1",
            "cases": len(cases),
            "baseline": evaluate_keyword_baseline(cases),
        }
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    output = json.dumps(report, indent=2, sort_keys=True)
    print(output)
    if args.output:
        args.output.write_text(output + "\\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
