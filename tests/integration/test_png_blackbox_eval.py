from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any, cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHECKER = runpy.run_path(str(PROJECT_ROOT / "scripts" / "check_png_blackbox_eval.py"))
DEFAULT_RUN = cast(Path, CHECKER["DEFAULT_RUN"])
COMPACT_TABLE_RUN = (
    PROJECT_ROOT
    / "evals"
    / "png-blackbox"
    / "runs"
    / "2026-07-31-compact-table-v4"
)
LEDGER_RUN = (
    PROJECT_ROOT
    / "evals"
    / "png-blackbox"
    / "runs"
    / "2026-08-01-ledger-v5"
)
SCORE_KEYS = cast(tuple[str, ...], CHECKER["SCORE_KEYS"])
check = cast(Any, CHECKER["check"])
equivalence = cast(Any, CHECKER["_equivalence"])
validate_boundary_attestation = cast(
    Any,
    CHECKER["_validate_boundary_attestation"],
)
validate_judgment = cast(Any, CHECKER["_validate_judgment"])


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


@pytest.mark.integration
def test_compact_table_png_blackbox_evaluation_requires_all_passes() -> None:
    assert check(COMPACT_TABLE_RUN, write_report=False, require_all_pass=True) == 0


@pytest.mark.integration
def test_ledger_png_blackbox_evaluation_requires_all_passes() -> None:
    assert check(LEDGER_RUN, write_report=False, require_all_pass=True) == 0


def test_equivalence_requires_threshold_core_scores_and_no_major_findings() -> None:
    scores = dict.fromkeys(SCORE_KEYS, 4)
    assert equivalence(scores, [], [], threshold=28, core_minimum=3)

    scores["flow_topology"] = 2
    assert not equivalence(scores, [], [], threshold=28, core_minimum=3)

    scores["flow_topology"] = 4
    major = [{"summary": "False join", "evidence": "An ingredient enters the wrong step."}]
    assert not equivalence(scores, [], major, threshold=28, core_minimum=3)


@pytest.mark.parametrize(
    "file_key",
    ["files", "input_png_basenames", "input_files", "inputs"],
)
def test_reader_attestation_accepts_equivalent_file_list_labels(
    tmp_path: Path,
    file_key: str,
) -> None:
    attestation = tmp_path / "agent-result.json"
    attestation.write_text(
        json.dumps(
            {
                "input_boundary": "png-only",
                "other_repo_files_read": False,
                file_key: ["fixture--color.tabular.png"],
            }
        ),
        encoding="utf-8",
    )

    validate_boundary_attestation(
        attestation,
        {"fixture--color.tabular.png"},
    )


def test_human_judgment_accepts_error_labels_and_word_confidence(
    tmp_path: Path,
) -> None:
    judgment = tmp_path / "fixture.judgment.json"
    scores = dict.fromkeys(SCORE_KEYS, 4)
    judgment.write_text(
        json.dumps(
            {
                "schema_version": "recipeflow.png-semantic-judgment/v1",
                "judge_id": "judge-1",
                "assigned_slug": "fixture--color",
                "candidate_file": "candidate.reconstruction.md",
                "original_file": "original.recipe.yaml",
                "scores": scores,
                "total_score": sum(scores.values()),
                "critical_errors": [],
                "major_errors": [],
                "minor_errors": [],
                "semantically_equivalent": True,
                "confidence": "high",
                "rationale": "The cook receives the same culinary meaning.",
            }
        ),
        encoding="utf-8",
    )

    value = validate_judgment(
        judgment,
        judge_id="judge-1",
        slug="fixture--color",
        candidate_file="candidate.reconstruction.md",
        original_file="original.recipe.yaml",
        threshold=28,
        core_minimum=3,
        candidate_suffix=".reconstruction.md",
    )

    assert value["confidence"] == 0.9
