"""Validate and aggregate a recorded PNG-only reconstruction evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = (
    PROJECT_ROOT
    / "evals"
    / "png-blackbox"
    / "runs"
    / "2026-07-31-golden-v5"
)
SCORE_KEYS = (
    "metadata",
    "ingredients",
    "setup",
    "operations",
    "flow_topology",
    "temporal_completion",
    "outputs_roles",
    "evidence_discipline",
)
CORE_SCORE_KEYS = (
    "ingredients",
    "operations",
    "flow_topology",
    "outputs_roles",
)
ROLES = {"intermediate", "final", "reserved", "waste", "garnish"}


class EvaluationError(ValueError):
    """One or more recorded evaluation artifacts violate the run contract."""


def _load_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise EvaluationError(f"missing file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"expected a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _string(value: Any, *, path: str, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError(f"{path} must be a non-empty string")


def _string_list(value: Any, *, path: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise EvaluationError(f"{path} must be a list of non-empty strings")
    return value


def _object_list(value: Any, *, path: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise EvaluationError(f"{path} must be a list of objects")
    return value


def _unique_ids(items: list[dict[str, Any]], *, path: str) -> set[str]:
    identifiers: list[str] = []
    for index, item in enumerate(items):
        _string(item.get("id"), path=f"{path}/{index}/id")
        identifiers.append(item["id"])
    if len(identifiers) != len(set(identifiers)):
        raise EvaluationError(f"{path} contains duplicate IDs")
    return set(identifiers)


def _validate_reconstruction(path: Path, slug: str) -> None:
    value = _load_object(path)
    schema_version = value.get("schema_version", value.get("schema"))
    if schema_version != "recipeflow.png-reconstruction/v1":
        raise EvaluationError(f"{path}: invalid reconstruction schema_version")
    if value.get("slug") != slug:
        raise EvaluationError(f"{path}: slug must be {slug!r}")
    _string(value.get("title"), path=f"{path}/title")
    _string(value.get("yield_text"), path=f"{path}/yield_text", nullable=True)

    setup = _object_list(value.get("setup"), path=f"{path}/setup")
    ingredients = _object_list(
        value.get("ingredients"),
        path=f"{path}/ingredients",
    )
    operations = _object_list(
        value.get("operations"),
        path=f"{path}/operations",
    )
    final_output_ids = _string_list(
        value.get("final_output_ids"),
        path=f"{path}/final_output_ids",
    )
    _string_list(value.get("ambiguities"), path=f"{path}/ambiguities")
    _string_list(value.get("evidence_notes"), path=f"{path}/evidence_notes")
    if not ingredients:
        raise EvaluationError(f"{path}: reconstruction needs at least one ingredient")
    if not operations:
        raise EvaluationError(f"{path}: reconstruction needs at least one operation")
    if not final_output_ids:
        raise EvaluationError(f"{path}: reconstruction needs a final output")

    setup_ids = _unique_ids(setup, path=f"{path}/setup")
    setup_requirement_ids = set(setup_ids)
    ingredient_ids = _unique_ids(ingredients, path=f"{path}/ingredients")
    operation_ids = _unique_ids(operations, path=f"{path}/operations")
    for index, item in enumerate(setup):
        _string(item.get("action"), path=f"{path}/setup/{index}/action")
        _string(
            item.get("target"),
            path=f"{path}/setup/{index}/target",
            nullable=True,
        )
        _string(
            item.get("temperature"),
            path=f"{path}/setup/{index}/temperature",
            nullable=True,
        )
        _string(
            item.get("duration"),
            path=f"{path}/setup/{index}/duration",
            nullable=True,
        )
        if "notes" in item:
            _string_list(item.get("notes"), path=f"{path}/setup/{index}/notes")
        produces = item.get("produces")
        if isinstance(produces, list):
            produced_ids = _string_list(
                produces,
                path=f"{path}/setup/{index}/produces",
            )
        else:
            _string(
                produces,
                path=f"{path}/setup/{index}/produces",
                nullable=True,
            )
            produced_ids = [] if produces is None else [produces]
        setup_requirement_ids.update(produced_ids)
        required_by = _string_list(
            item.get("required_by"),
            path=f"{path}/setup/{index}/required_by",
        )
        unknown = sorted(set(required_by) - operation_ids)
        if unknown:
            raise EvaluationError(
                f"{path}/setup/{index}/required_by references unknown operations: "
                f"{unknown}"
            )

    for index, item in enumerate(ingredients):
        _string(item.get("label"), path=f"{path}/ingredients/{index}/label")
        for field in ("quantity", "source_text", "preparation"):
            _string(
                item.get(field),
                path=f"{path}/ingredients/{index}/{field}",
                nullable=True,
            )
        if not isinstance(item.get("optional"), bool):
            raise EvaluationError(
                f"{path}/ingredients/{index}/optional must be a boolean"
            )

    output_ids: set[str] = set()
    outputs_by_id: dict[str, dict[str, Any]] = {}
    for operation_index, operation in enumerate(operations):
        _string(
            operation.get("action"),
            path=f"{path}/operations/{operation_index}/action",
        )
        _string_list(
            operation.get("inputs"),
            path=f"{path}/operations/{operation_index}/inputs",
        )
        allocations = operation.get("input_allocations", {})
        if not isinstance(allocations, dict) or any(
            not isinstance(key, str)
            or not isinstance(quantity, str)
            or not quantity.strip()
            for key, quantity in allocations.items()
        ):
            raise EvaluationError(
                f"{path}/operations/{operation_index}/input_allocations must map "
                "material IDs to visible quantity strings"
            )
        unknown_allocations = sorted(set(allocations) - set(operation["inputs"]))
        if unknown_allocations:
            raise EvaluationError(
                f"{path}/operations/{operation_index}/input_allocations references "
                f"non-input materials: {unknown_allocations}"
            )
        outputs = _object_list(
            operation.get("outputs"),
            path=f"{path}/operations/{operation_index}/outputs",
        )
        for output_index, output in enumerate(outputs):
            _string(
                output.get("id"),
                path=(
                    f"{path}/operations/{operation_index}/outputs/"
                    f"{output_index}/id"
                ),
            )
            identifier = output["id"]
            if identifier in ingredient_ids or identifier in output_ids:
                raise EvaluationError(f"{path}: duplicate material ID {identifier!r}")
            output_ids.add(identifier)
            outputs_by_id[identifier] = output
            _string(
                output.get("label"),
                path=(
                    f"{path}/operations/{operation_index}/outputs/"
                    f"{output_index}/label"
                ),
            )
            if output.get("role") not in ROLES:
                raise EvaluationError(
                    f"{path}: invalid role for output {identifier!r}"
                )
        requires = _string_list(
            operation.get("requires"),
            path=f"{path}/operations/{operation_index}/requires",
        )
        unknown_requires = sorted(set(requires) - setup_requirement_ids)
        if unknown_requires:
            raise EvaluationError(
                f"{path}/operations/{operation_index}/requires references unknown "
                f"setup prerequisites: {unknown_requires}"
            )
        for field in ("duration", "temperature", "until", "repeat"):
            _string(
                operation.get(field),
                path=f"{path}/operations/{operation_index}/{field}",
                nullable=True,
            )

    known_materials = ingredient_ids | output_ids
    for operation_index, operation in enumerate(operations):
        unknown_inputs = sorted(set(operation["inputs"]) - known_materials)
        if unknown_inputs:
            raise EvaluationError(
                f"{path}/operations/{operation_index}/inputs references unknown "
                f"materials: {unknown_inputs}"
            )

    unknown_finals = sorted(set(final_output_ids) - output_ids)
    if unknown_finals:
        raise EvaluationError(
            f"{path}/final_output_ids references unknown outputs: {unknown_finals}"
        )
    incorrectly_typed = sorted(
        identifier
        for identifier in final_output_ids
        if outputs_by_id[identifier].get("role") != "final"
    )
    if incorrectly_typed:
        raise EvaluationError(
            f"{path}: final outputs must use role 'final': {incorrectly_typed}"
        )


def _validate_boundary_attestation(
    path: Path,
    expected_files: set[str],
) -> None:
    value = _load_object(path)
    if value.get("input_boundary") != "png-only":
        raise EvaluationError(f"{path}: input_boundary must be 'png-only'")
    if value.get("other_repo_files_read") is not False:
        raise EvaluationError(f"{path}: other_repo_files_read must be false")
    files = _string_list(value.get("files"), path=f"{path}/files")
    if {Path(item).name for item in files} != expected_files:
        raise EvaluationError(
            f"{path}: files do not match assigned reconstruction outputs"
        )


def _normalized_path(value: str) -> str:
    return value.replace("\\", "/")


def _normalized_candidate_path(value: str) -> str:
    normalized = _normalized_path(value)
    for suffix in (".reconstruction.json", ".tabular.json", ".json"):
        if normalized.endswith(suffix):
            return f"{normalized.removesuffix(suffix)}.reconstruction.json"
    return normalized


def _validate_judge_boundary_attestation(
    path: Path,
    expected_pairs: set[tuple[str, str]],
) -> None:
    value = _load_object(path)
    boundary_confirmed = (
        value.get("input_boundary") == "candidate-and-original-only"
        or value.get("candidate_and_original_only") is True
    )
    if not boundary_confirmed:
        raise EvaluationError(
            f"{path}: input_boundary must be 'candidate-and-original-only'"
        )
    other_files_read = value.get(
        "other_repo_files_read",
        value.get("other_files_read", value.get("other_files_consulted")),
    )
    if other_files_read is not False:
        raise EvaluationError(f"{path}: other_repo_files_read must be false")
    pairs = _object_list(value.get("pairs"), path=f"{path}/pairs")
    actual_pairs: set[tuple[str, str]] = set()
    for index, pair in enumerate(pairs):
        candidate = pair.get("candidate", pair.get("candidate_file"))
        original = pair.get("original", pair.get("original_file"))
        _string(candidate, path=f"{path}/pairs/{index}/candidate")
        _string(original, path=f"{path}/pairs/{index}/original")
        actual_pairs.add(
            (
                _normalized_candidate_path(candidate),
                _normalized_path(original),
            )
        )
    if len(actual_pairs) != len(pairs) or actual_pairs != expected_pairs:
        raise EvaluationError(f"{path}: pairs do not match assigned judge inputs")


def _equivalence(
    scores: dict[str, int],
    critical_findings: list[dict[str, Any]],
    major_findings: list[dict[str, Any]],
    *,
    threshold: int,
    core_minimum: int,
) -> bool:
    return (
        not critical_findings
        and not major_findings
        and sum(scores.values()) >= threshold
        and all(scores[key] >= core_minimum for key in CORE_SCORE_KEYS)
    )


def _validate_findings(value: Any, *, path: str) -> list[dict[str, Any]]:
    findings = _object_list(value, path=path)
    for index, finding in enumerate(findings):
        _string(finding.get("summary"), path=f"{path}/{index}/summary")
        _string(finding.get("evidence"), path=f"{path}/{index}/evidence")
    return findings


def _validate_judgment(
    path: Path,
    *,
    judge_id: str,
    slug: str,
    candidate_file: str,
    original_file: str,
    threshold: int,
    core_minimum: int,
) -> dict[str, Any]:
    value = _load_object(path)
    if value.get("schema_version") != "recipeflow.png-semantic-judgment/v1":
        raise EvaluationError(f"{path}: invalid judgment schema_version")
    if value.get("judge_id") != judge_id or value.get("slug") != slug:
        raise EvaluationError(f"{path}: judge_id or slug does not match assignment")
    _string(value.get("candidate_file"), path=f"{path}/candidate_file")
    _string(value.get("original_file"), path=f"{path}/original_file")
    if _normalized_candidate_path(value["candidate_file"]) != candidate_file:
        raise EvaluationError(f"{path}: candidate_file does not match assignment")
    if _normalized_path(value["original_file"]) != original_file:
        raise EvaluationError(f"{path}: original_file does not match assignment")
    scores = value.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(SCORE_KEYS):
        raise EvaluationError(f"{path}/scores must contain the eight rubric dimensions")
    if any(
        not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 4
        for score in scores.values()
    ):
        raise EvaluationError(f"{path}/scores values must be integers from 0 to 4")
    total = sum(scores.values())
    if value.get("total_score") != total:
        raise EvaluationError(f"{path}: total_score must equal {total}")
    critical = _validate_findings(
        value.get("critical_findings"),
        path=f"{path}/critical_findings",
    )
    major = _validate_findings(
        value.get("major_findings"),
        path=f"{path}/major_findings",
    )
    _validate_findings(
        value.get("minor_findings"),
        path=f"{path}/minor_findings",
    )
    expected_equivalence = _equivalence(
        scores,
        critical,
        major,
        threshold=threshold,
        core_minimum=core_minimum,
    )
    if value.get("semantically_equivalent") is not expected_equivalence:
        raise EvaluationError(
            f"{path}: semantically_equivalent must be {expected_equivalence}"
        )
    confidence = value.get("confidence")
    if (
        not isinstance(confidence, int | float)
        or isinstance(confidence, bool)
        or not 0 <= confidence <= 1
    ):
        raise EvaluationError(f"{path}/confidence must be between 0 and 1")
    _string(value.get("rationale"), path=f"{path}/rationale")
    return value


def _report(
    run: dict[str, Any],
    candidate_agents: dict[str, str],
    judgments: dict[str, list[dict[str, Any]]],
) -> tuple[str, dict[str, int]]:
    lines = [
        f"# PNG black-box evaluation: {run['run_id']}",
        "",
        "Fresh reconstruction agents received PNGs only. Separate fresh judges compared",
        "the neutral reconstructions with the original RecipeFlow YAML. Each fixture has",
        "two independent judgments.",
        "",
        "| Fixture | Reconstructor | Judge scores | Equivalent votes | Result |",
        "| --- | --- | --- | --- | --- |",
    ]
    counts = {"pass": 0, "review": 0, "fail": 0}
    dimension_totals = {key: 0 for key in SCORE_KEYS}
    judgment_count = 0
    for slug in sorted(candidate_agents):
        slug_judgments = sorted(
            judgments[slug],
            key=lambda item: item["judge_id"],
        )
        votes = sum(
            1 for item in slug_judgments if item["semantically_equivalent"]
        )
        status = "pass" if votes == 2 else "fail" if votes == 0 else "review"
        counts[status] += 1
        score_text = ", ".join(
            f"{item['judge_id']}: {item['total_score']}/32"
            for item in slug_judgments
        )
        lines.append(
            f"| {slug} | {candidate_agents[slug]} | {score_text} | "
            f"{votes}/2 | {status} |"
        )
        for item in slug_judgments:
            judgment_count += 1
            for key in SCORE_KEYS:
                dimension_totals[key] += item["scores"][key]

    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Pass: {counts['pass']}",
            f"- Review: {counts['review']}",
            f"- Fail: {counts['fail']}",
            f"- Recorded judgments: {judgment_count}",
            "",
            "Average dimension scores:",
            "",
        ]
    )
    for key in SCORE_KEYS:
        average = dimension_totals[key] / judgment_count if judgment_count else 0
        lines.append(f"- `{key}`: {average:.2f}/4")

    findings_present = False
    findings_lines = ["", "## Judge findings", ""]
    for slug in sorted(judgments):
        for judgment in sorted(judgments[slug], key=lambda item: item["judge_id"]):
            for severity in ("critical", "major", "minor"):
                for finding in judgment[f"{severity}_findings"]:
                    findings_present = True
                    findings_lines.append(
                        f"- **{slug} / {judgment['judge_id']} / {severity}:** "
                        f"{finding['summary']} — {finding['evidence']}"
                    )
    if findings_present:
        lines.extend(findings_lines)
    else:
        lines.extend(["", "## Judge findings", "", "No findings."])
    lines.append("")
    return "\n".join(lines), counts


def check(run_root: Path, *, write_report: bool, require_all_pass: bool) -> int:
    run_path = run_root / "run.json"
    run = _load_object(run_path)
    if run.get("schema_version") != "recipeflow.png-blackbox-run/v1":
        raise EvaluationError(f"{run_path}: invalid run schema_version")
    reconstruction_assignments = run.get("reconstruction_assignments")
    judge_assignments = run.get("judge_assignments")
    if not isinstance(reconstruction_assignments, dict) or not isinstance(
        judge_assignments,
        dict,
    ):
        raise EvaluationError(f"{run_path}: assignments must be objects")
    threshold = run.get("equivalence_threshold")
    core_minimum = run.get("core_score_minimum")
    if not isinstance(threshold, int) or not isinstance(core_minimum, int):
        raise EvaluationError(f"{run_path}: invalid equivalence policy")
    input_png_root = run.get("input_png_root", "examples/golden")
    original_root = run.get("original_root", "examples/golden")
    if not isinstance(input_png_root, str) or not isinstance(original_root, str):
        raise EvaluationError(f"{run_path}: corpus roots must be strings")
    png_root = PROJECT_ROOT / input_png_root
    recipe_root = PROJECT_ROOT / original_root

    assigned_slugs = {
        slug
        for raw_slugs in reconstruction_assignments.values()
        if isinstance(raw_slugs, list)
        for slug in raw_slugs
        if isinstance(slug, str)
    }
    input_png_sha256 = run.get("input_png_sha256")
    if input_png_sha256 is not None:
        if (
            not isinstance(input_png_sha256, dict)
            or set(input_png_sha256) != assigned_slugs
            or any(
                not isinstance(value, str)
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
                for value in input_png_sha256.values()
            )
        ):
            raise EvaluationError(
                f"{run_path}: input_png_sha256 must pin every assigned PNG"
            )

    candidate_agents: dict[str, str] = {}
    for agent_id, raw_slugs in reconstruction_assignments.items():
        _string(agent_id, path=f"{run_path}/reconstruction_assignments")
        slugs = _string_list(
            raw_slugs,
            path=f"{run_path}/reconstruction_assignments/{agent_id}",
        )
        expected_files = {f"{slug}.tabular.png" for slug in slugs}
        agent_root = run_root / "candidates" / agent_id
        _validate_boundary_attestation(
            agent_root / "agent-result.json",
            expected_files,
        )
        for slug in slugs:
            if slug in candidate_agents:
                raise EvaluationError(f"duplicate reconstruction assignment: {slug}")
            candidate_agents[slug] = agent_id
            _validate_reconstruction(
                agent_root / f"{slug}.reconstruction.json",
                slug,
            )
            png_path = png_root / f"{slug}.tabular.png"
            if not png_path.is_file():
                raise EvaluationError(f"missing golden PNG for {slug}")
            if (
                input_png_sha256 is not None
                and _sha256(png_path) != input_png_sha256[slug]
            ):
                raise EvaluationError(
                    f"golden PNG hash changed since the recorded run: {slug}"
                )
            if not (recipe_root / f"{slug}.recipe.yaml").is_file():
                raise EvaluationError(f"missing original RecipeFlow YAML for {slug}")

    judgments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    assigned_judges: dict[str, set[str]] = defaultdict(set)
    for judge_id, raw_slugs in judge_assignments.items():
        _string(judge_id, path=f"{run_path}/judge_assignments")
        slugs = _string_list(
            raw_slugs,
            path=f"{run_path}/judge_assignments/{judge_id}",
        )
        expected_pairs: set[tuple[str, str]] = set()
        for slug in slugs:
            if slug not in candidate_agents:
                raise EvaluationError(f"judge assigned unknown fixture: {slug}")
            if judge_id in assigned_judges[slug]:
                raise EvaluationError(f"duplicate judge assignment: {judge_id}/{slug}")
            assigned_judges[slug].add(judge_id)
            candidate_file = (
                "evals/png-blackbox/runs/"
                f"{run['run_id']}/candidates/{candidate_agents[slug]}/"
                f"{slug}.reconstruction.json"
            )
            original_file = f"{original_root}/{slug}.recipe.yaml"
            expected_pairs.add((candidate_file, original_file))
            judgments[slug].append(
                _validate_judgment(
                    run_root / "judgments" / judge_id / f"{slug}.judgment.json",
                    judge_id=judge_id,
                    slug=slug,
                    candidate_file=candidate_file,
                    original_file=original_file,
                    threshold=threshold,
                    core_minimum=core_minimum,
                )
            )
        _validate_judge_boundary_attestation(
            run_root / "judgments" / judge_id / "agent-result.json",
            expected_pairs,
        )

    expected_judges = run.get("judge_count_per_fixture")
    if not isinstance(expected_judges, int) or expected_judges < 1:
        raise EvaluationError(f"{run_path}: invalid judge_count_per_fixture")
    for slug in sorted(candidate_agents):
        if len(assigned_judges[slug]) != expected_judges:
            raise EvaluationError(
                f"{slug}: expected {expected_judges} judges, "
                f"received {len(assigned_judges[slug])}"
            )

    report, counts = _report(run, candidate_agents, judgments)
    report_path = run_root / "REPORT.md"
    if write_report:
        report_path.write_text(report, encoding="utf-8", newline="\n")
    elif not report_path.is_file() or report_path.read_text(encoding="utf-8") != report:
        raise EvaluationError(
            f"{report_path}: missing or stale; rerun with --write-report"
        )
    if require_all_pass and (counts["review"] or counts["fail"]):
        raise EvaluationError(
            "semantic acceptance failed: "
            f"{counts['pass']} pass, {counts['review']} review, "
            f"{counts['fail']} fail"
        )
    print(
        "PNG black-box evaluation passed integrity checks: "
        f"{len(candidate_agents)} fixtures, "
        f"{sum(len(items) for items in judgments.values())} judgments; "
        f"{counts['pass']} pass, {counts['review']} review, {counts['fail']} fail"
    )
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "run_root",
        nargs="?",
        type=Path,
        default=DEFAULT_RUN,
        help="Recorded run directory.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write the deterministic aggregate REPORT.md.",
    )
    parser.add_argument(
        "--require-all-pass",
        action="store_true",
        help="Fail when any fixture is not unanimously equivalent.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    run_root = args.run_root.resolve()
    try:
        return check(
            run_root,
            write_report=args.write_report,
            require_all_pass=args.require_all_pass,
        )
    except EvaluationError as exc:
        print(f"PNG black-box evaluation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
