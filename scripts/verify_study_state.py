"""Verify the evidence-locked study state without modifying it."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FORMAL_CONFIGS = {"Formal", "Full Check", "PDF/UA-1 ua1"}
VALID_CLASSES = {"Detected", "Missed", "Needs Manual Check", "Not Applicable"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def study_counts() -> dict:
    mutants = read_jsonl(ROOT / "data" / "mutants.jsonl")
    exclusions = read_csv(ROOT / "data" / "mutant_exclusions.csv")
    excluded_ids = {row.get("mutant_id", "") for row in exclusions if row.get("status")}
    verified = {row["mutant_id"] for row in mutants if str(row.get("status", "")).lower() == "valid" and row.get("verification", {}).get("mutation_valid") is True}
    active = verified - excluded_ids
    runs = read_csv(ROOT / "data" / "validator_runs.csv")
    formal = [row for row in runs if row.get("baseline_or_mutant") == "mutant" and row.get("artifact_id") in active and row.get("configuration") in FORMAL_CONFIGS]
    classified = [row for row in formal if row.get("detection_classification") in VALID_CLASSES]
    operators = {row["mutant_id"]: row.get("operator", "") for row in mutants if row["mutant_id"] in active}
    operator_specs = yaml.safe_load((ROOT / "operators" / "operators.yaml").read_text(encoding="utf-8"))["operators"]
    class_a_ops = {item["id"] for item in operator_specs if item.get("class") == "class_a"}
    controls = read_csv(ROOT / "data" / "controls.csv")
    return {
        "golden_pdfs": len(list((ROOT / "corpus" / "golden").glob("*.pdf"))),
        "valid_verified_mutants": len(verified),
        "documented_exclusions": len(exclusions),
        "exclusions_present_in_manifest": len(excluded_ids & {row["mutant_id"] for row in mutants}),
        "active_mutants": len(active),
        "formal_validator_rows": len(formal),
        "classified_formal_rows": len(classified),
        "classified_rows_per_validator": {name: sum(row.get("validator") == name for row in classified) for name in ("PAC", "Acrobat", "veraPDF")},
        "class_a_mutants": sum(operator in class_a_ops for operator in operators.values()),
        "class_b_mutants": sum(operator not in class_a_ops for operator in operators.values()),
        "at_observations": len(read_csv(ROOT / "data" / "at_observations.csv")),
        "pac_ai_rows": len(read_csv(ROOT / "data" / "pac_ai_classifications.csv")),
        "control_rows": len(controls),
        "artifact_verified_control_rows": sum(row.get("status") in {"ARTIFACT_VERIFIED_PENDING_VALIDATORS", "VERAPDF_EXECUTED_PENDING_PAC_ACROBAT", "COMPLETE"} for row in controls),
        "verapdf_control_rows": sum(row.get("status") in {"VERAPDF_EXECUTED_PENDING_PAC_ACROBAT", "COMPLETE"} for row in controls),
        "executed_control_rows": sum(row.get("status") == "COMPLETE" for row in controls),
        "baseline_conflict_rows": len(read_csv(ROOT / "data" / "baseline_conflict_resolutions.csv")),
        "ambiguous_or_missing_formal_rows": sum(not row.get("detection_classification") or row.get("detection_classification") not in VALID_CLASSES for row in formal),
        "double_coded_formal_rows": sum(bool(row.get("coder_1") and row.get("coder_2") and row.get("adjudication")) for row in formal),
        "active_ids": sorted(active),
        "excluded_ids": sorted(excluded_ids),
    }


def verify_hash_columns() -> list[str]:
    errors: list[str] = []
    exclusions = {row.get("mutant_id", "") for row in read_csv(ROOT / "data" / "mutant_exclusions.csv") if row.get("status")}
    mutants = {row["mutant_id"]: row for row in read_jsonl(ROOT / "data" / "mutants.jsonl")}
    for artifact_id, row in mutants.items():
        # Historical/invalid exclusions may intentionally retain only the
        # decision record, not a redistributable mutant PDF.
        if str(row.get("status", "")).lower() != "valid" and artifact_id in exclusions:
            continue
        for key, label in (("source_pdf", "source"), ("mutant_pdf", "mutant")):
            path = Path(row.get(key, ""))
            if not path.is_absolute():
                path = ROOT / path
            if not path.is_file():
                errors.append(f"{artifact_id}: missing {label} file {path}")
            elif row.get(f"{label}_sha256") and sha256(path) != row[f"{label}_sha256"]:
                errors.append(f"{artifact_id}: {label} hash mismatch")
    for row in read_csv(ROOT / "data" / "validator_runs.csv"):
        report = ROOT / row.get("raw_report_path", "")
        expected = row.get("report_sha256", "")
        if expected and report.is_file() and sha256(report) != expected:
            errors.append(f"{row.get('record_id')}: report hash mismatch")
        if expected and not report.is_file():
            errors.append(f"{row.get('record_id')}: missing report {report}")
    return errors


def verify_generated_claims(counts: dict) -> list[str]:
    errors: list[str] = []
    summary_path = ROOT / "analysis" / "generated" / "metrics_summary.json"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        for key, expected in (("valid_mutants", counts["active_mutants"]), ("classified_formal_rows", counts["classified_formal_rows"]), ("required_classified_formal_rows", counts["active_mutants"] * 3)):
            if summary.get(key) != expected:
                errors.append(f"generated metrics {key}={summary.get(key)!r}, expected {expected}")
    text = (ROOT / "analysis" / "generated" / "results_fragment.tex").read_text(encoding="utf-8") if (ROOT / "analysis" / "generated" / "results_fragment.tex").is_file() else ""
    if text and f"{counts['active_mutants']} verified mutants" not in text:
        errors.append("results_fragment.tex does not contain the canonical active denominator")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="run the checks")
    args = parser.parse_args()
    counts = study_counts()
    errors = verify_hash_columns() + verify_generated_claims(counts)
    tests = list((ROOT / "tests").glob("test*.py"))
    if not tests:
        errors.append("test discovery found zero test files")
    if not (ROOT / "data" / "controls.csv").is_file():
        errors.append("controls.csv is missing")
    print(json.dumps({"counts": counts, "errors": errors}, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
