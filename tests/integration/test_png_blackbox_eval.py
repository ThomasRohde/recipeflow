from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any, cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKER = runpy.run_path(str(PROJECT_ROOT / "scripts" / "check_png_blackbox_eval.py"))
DEFAULT_RUN = cast(Path, CHECKER["DEFAULT_RUN"])
SCORE_KEYS = cast(tuple[str, ...], CHECKER["SCORE_KEYS"])
check = cast(Any, CHECKER["check"])
equivalence = cast(Any, CHECKER["_equivalence"])


@pytest.mark.integration
def test_recorded_png_blackbox_evaluation_is_complete_and_consistent() -> None:
    assert check(DEFAULT_RUN, write_report=False, require_all_pass=False) == 0
    run = cast(
        dict[str, Any],
        json.loads((DEFAULT_RUN / "run.json").read_text(encoding="utf-8")),
    )
    assert set(run["input_png_sha256"]) == {
        slug
        for slugs in run["reconstruction_assignments"].values()
        for slug in slugs
    }


def test_equivalence_requires_threshold_core_scores_and_no_major_findings() -> None:
    scores = dict.fromkeys(SCORE_KEYS, 4)
    assert equivalence(scores, [], [], threshold=28, core_minimum=3)

    scores["flow_topology"] = 2
    assert not equivalence(scores, [], [], threshold=28, core_minimum=3)

    scores["flow_topology"] = 4
    major = [{"summary": "False join", "evidence": "An ingredient enters the wrong step."}]
    assert not equivalence(scores, [], major, threshold=28, core_minimum=3)
