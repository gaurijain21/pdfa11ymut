"""Fail-closed consistency audit for the evidence-backed study freeze.

This check validates relationships among canonical inputs, derived tables, and
hash-linked evidence. It deliberately does not decide unresolved scientific
questions such as whether a semantic mutation is machine-checkable.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FORMAL_VALIDATORS = {"PAC", "Acrobat", "veraPDF"}
FORMAL_CONFIGS = {"Formal", "Full Check", "PDF/UA-1 ua1"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    manifest_path = ROOT / "STUDY_MANIFEST.json"
    if not manifest_path.is_file():
        print("FAIL: STUDY_MANIFEST.json is missing")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    current_dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    recorded_repo = manifest.get("repository", {})
    if recorded_repo.get("git_head") != current_head:
        fail(errors, f"manifest git_head={recorded_repo.get('git_head')} but current HEAD={current_head}")
    if recorded_repo.get("worktree_dirty") is not current_dirty:
        fail(errors, f"manifest worktree_dirty={recorded_repo.get('worktree_dirty')} but current state is {current_dirty}")
    paper_meta = manifest.get("paper_artifacts", {})
    for key, relative in (("source", "paper/pdfa11ymut_ieee.tex"), ("pdf", "paper/pdfa11ymut_ieee.pdf")):
        path = ROOT / relative
        expected = paper_meta.get(key, {}).get("sha256")
        if path.is_file() and expected and sha256(path) != expected:
            fail(errors, f"manifest hash mismatch for {relative}")
    mutants = read_jsonl(DATA / "mutants.jsonl")
    exclusions = read_csv(DATA / "mutant_exclusions.csv")
    runs = read_csv(DATA / "validator_runs.csv")
    active_valid = [
        row for row in mutants
        if str(row.get("status", "")).lower() == "valid"
        and row.get("verification", {}).get("mutation_valid") is True
        and row.get("mutant_id") not in {x.get("mutant_id") for x in exclusions if x.get("status")}
    ]
    valid = [
        row for row in mutants
        if str(row.get("status", "")).lower() == "valid"
        and row.get("verification", {}).get("mutation_valid") is True
    ]
    active_ids = {row["mutant_id"] for row in active_valid}
    if len({row.get("mutant_id") for row in mutants}) != len(mutants):
        fail(errors, "mutants.jsonl contains duplicate mutant IDs")
    if len(active_valid) != manifest["counts"]["active_mutants"]:
        fail(errors, f"manifest active_mutants={manifest['counts']['active_mutants']} but computed {len(active_valid)}")
    if len(valid) != manifest["counts"]["valid_verified_mutants"]:
        fail(errors, f"manifest valid_verified_mutants={manifest['counts']['valid_verified_mutants']} but computed {len(valid)}")
    if len(exclusions) != manifest["counts"]["documented_exclusions"]:
        fail(errors, "manifest documented exclusion count is stale")
    for row in exclusions:
        if not row.get("mutant_id") or not row.get("status") or not row.get("reason"):
            fail(errors, f"exclusion is undocumented: {row}")

    # Hash-linked artifact checks for every active mutant.
    for row in active_valid:
        mutant_id = row["mutant_id"]
        for field in ("source_pdf", "mutant_pdf"):
            path = ROOT / row[field]
            if not path.is_file():
                fail(errors, f"{mutant_id} missing {field}: {row[field]}")
        if (ROOT / row["source_pdf"]).is_file() and sha256(ROOT / row["source_pdf"]) != row.get("source_sha256"):
            fail(errors, f"{mutant_id} source hash mismatch")
        if (ROOT / row["mutant_pdf"]).is_file() and sha256(ROOT / row["mutant_pdf"]) != row.get("mutant_sha256"):
            fail(errors, f"{mutant_id} mutant hash mismatch")
        audit_path = ROOT / "evidence" / "independent_verification_v2" / f"{mutant_id}.json"
        if not audit_path.is_file():
            fail(errors, f"{mutant_id} missing independent verification record")

    # Formal validator ledger completeness and report hashes.
    active_formal = [
        row for row in runs
        if row.get("artifact_id") in active_ids
        and row.get("baseline_or_mutant") == "mutant"
        and row.get("validator") in FORMAL_VALIDATORS
        and row.get("configuration") in FORMAL_CONFIGS
    ]
    expected_rows = len(active_valid) * len(FORMAL_VALIDATORS)
    if len(active_formal) != expected_rows:
        fail(errors, f"formal ledger has {len(active_formal)} active rows; expected {expected_rows}")
    by_validator = Counter(row.get("validator") for row in active_formal)
    for validator in sorted(FORMAL_VALIDATORS):
        if by_validator[validator] != len(active_valid):
            fail(errors, f"{validator} has {by_validator[validator]} active rows; expected {len(active_valid)}")
    seen_records = set()
    for row in active_formal:
        record_id = row.get("record_id")
        if record_id in seen_records:
            fail(errors, f"duplicate validator record ID: {record_id}")
        seen_records.add(record_id)
        report = ROOT / row.get("raw_report_path", "")
        if not report.is_file():
            fail(errors, f"{record_id} missing raw report: {row.get('raw_report_path')}")
        elif row.get("report_sha256") and sha256(report) != row["report_sha256"]:
            fail(errors, f"{record_id} raw report hash mismatch")
        if not row.get("file_sha256") or not row.get("baseline_file_sha256"):
            fail(errors, f"{record_id} lacks mutant or baseline hash")
        if not row.get("detection_classification") or not row.get("classification_reason"):
            fail(errors, f"{record_id} lacks classification evidence")

    # All ten operators and all active targets must be represented by the
    # machine-readable derived views.
    mapping = read_csv(DATA / "operator_standard_mapping.csv")
    selection = read_csv(DATA / "operator_target_selection.csv")
    delta_path = DATA / "mutant_delta_manifest.jsonl"
    delta_rows = read_jsonl(delta_path) if delta_path.is_file() else []
    operators = {f"M{i:02d}" for i in range(1, 11)}
    if {row.get("operator") for row in mapping} != operators:
        fail(errors, "operator_standard_mapping.csv does not contain exactly M01-M10")
    if {row.get("mutant_id") for row in selection} != active_ids:
        fail(errors, "operator_target_selection.csv does not cover exactly the active mutant IDs")
    if len({row.get("mutant_id") for row in selection}) != len(selection):
        fail(errors, "operator_target_selection.csv contains duplicate mutant IDs")
    if {row.get("mutant_id") for row in delta_rows} != active_ids:
        fail(errors, "mutant_delta_manifest.jsonl does not cover exactly the active mutant IDs")
    if any(not row.get("allowed_changes") or not row.get("required_invariants") for row in delta_rows):
        fail(errors, "mutant delta manifest has an active row without allowed changes or required invariants")

    # Generated overall rates must state a denominator that can be recomputed
    # from its displayed categories. Manual rows are not silently included in
    # an automated detection rate.
    rates_path = ROOT / "analysis" / "generated" / "overall_rates.csv"
    if rates_path.is_file():
        for row in read_csv(rates_path):
            detected = int(row["detected"])
            missed = int(row["missed"])
            manual = int(row["needs_manual_check"])
            total = int(row["total_with_classification"])
            if detected + missed + manual + int(row["not_applicable"]) != total:
                fail(errors, f"{row['validator']} overall categories do not sum to total")
            expected_rate = detected / (detected + missed) if detected + missed else ""
            actual_rate = row.get("rate", "")
            if expected_rate == "" and actual_rate:
                fail(errors, f"{row['validator']} rate has no automated denominator")
            elif expected_rate != "" and not math.isclose(float(actual_rate), expected_rate, rel_tol=0, abs_tol=0.0002):
                fail(errors, f"{row['validator']} rate denominator is inconsistent")

    # Active README/manuscript count guard. Historical directories are allowed
    # to retain old numbers, but the two current-facing artifacts must expose
    # the manifest-derived study state and must not revive the old 23-mutant
    # experiment or the superseded class split.
    current_facing = {
        "README.md": ROOT / "README.md",
        "paper/pdfa11ymut_ieee.tex": ROOT / "paper" / "pdfa11ymut_ieee.tex",
    }
    required_fragments = {
        "73 valid verified generation records": "valid mutant count",
        "69 active mutants": "active mutant count",
        "Class A contains 30": "Class A count",
        "Class B contains 39": "Class B count",
    }
    forbidden_fragments = {
        "Class A contains 37": "superseded Class A count",
        "Class B contains 32": "superseded Class B count",
        "23-mutant": "historical 23-mutant wording",
    }
    for label, path in current_facing.items():
        if not path.is_file():
            fail(errors, f"current-facing artifact missing: {label}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for fragment, description in required_fragments.items():
            if fragment not in text:
                fail(errors, f"{label} missing manifest-derived {description}: {fragment}")
        if "207 active formal" not in text and "207 classified formal validator rows" not in text:
            fail(errors, f"{label} missing manifest-derived formal-row count")
        for fragment, description in forbidden_fragments.items():
            if fragment in text:
                fail(errors, f"{label} contains {description}: {fragment}")

    # Second-pass generated views and immutable evidence snapshot.
    applicability = DATA / "operator_applicability.csv"
    capability = DATA / "validator_capability_mapping.csv"
    loo = ROOT / "analysis" / "leave_one_source_out.csv"
    checksums = DATA / "evidence_checksums.sha256"
    if not applicability.is_file():
        fail(errors, "operator_applicability.csv is missing")
    elif len(read_csv(applicability)) != 10:
        fail(errors, "operator_applicability.csv must contain one row per operator")
    if not capability.is_file():
        fail(errors, "validator_capability_mapping.csv is missing")
    else:
        expected_capability_fields = {
            "validator", "version", "configuration", "operator", "relevant_rule",
            "machine_checkable", "validator_claims_coverage", "expected_automated_detection", "evidence_source",
        }
        actual_fields = set(read_csv(capability)[0]) if read_csv(capability) else set()
        if actual_fields != expected_capability_fields:
            fail(errors, "validator_capability_mapping.csv has the wrong schema")
        if len(read_csv(capability)) != 30:
            fail(errors, "validator_capability_mapping.csv must contain 10 operators x 3 configurations")
    if not loo.is_file() or len(read_csv(loo)) != 27:
        fail(errors, "analysis/leave_one_source_out.csv must contain 9 baselines x 3 validators")
    if not checksums.is_file():
        fail(errors, "data/evidence_checksums.sha256 is missing")
    else:
        checksum_lines = [line for line in checksums.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
        if not checksum_lines:
            fail(errors, "evidence checksum manifest is empty")
        for line in checksum_lines:
            parts = line.split("  ", 1)
            if len(parts) != 2:
                fail(errors, f"malformed evidence checksum line: {line}")
                continue
            expected_hash, relative = parts
            path = ROOT / relative.replace("/", "\\")
            if not path.is_file():
                fail(errors, f"checksum target is missing: {relative}")
            elif sha256(path) != expected_hash:
                fail(errors, f"checksum mismatch: {relative}")

    if errors:
        print(f"FAIL: {len(errors)} consistency issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(json.dumps({
        "status": "PASS",
        "active_mutants": len(active_valid),
        "formal_rows": len(active_formal),
        "formal_rows_per_validator": dict(sorted(by_validator.items())),
        "documented_exclusions": len(exclusions),
        "operator_mapping_rows": len(mapping),
        "target_selection_rows": len(selection),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
