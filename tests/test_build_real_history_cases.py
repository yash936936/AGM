from __future__ import annotations

import json
from pathlib import Path

from scripts.build_real_history_cases import build, main
from scripts.evaluate_real_history import evaluate

ROOT = Path(__file__).resolve().parents[1]


def test_template_builds_and_evaluates_end_to_end(tmp_path):
    out = tmp_path / "cases.jsonl"
    assert main.__module__ == "scripts.build_real_history_cases"
    cases = build(json.loads((ROOT / "examples" / "real_history_authoring.template.json").read_text(encoding="utf-8")))
    assert [c["scenario"] for c in cases] == ["cross_session_recall", "current_vs_stale", "deletion", "abstention"]
    out.write_text("".join(json.dumps(c) + "\n" for c in cases), encoding="utf-8")
    report = evaluate(out)
    assert report["cases"] == 4
    assert report["case_passes"] == 4, report
