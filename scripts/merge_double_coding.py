"""Validate and optionally merge completed double-coding decisions.

The default mode is a read-only validation. ``--apply`` is intentionally
required before this script changes ``data/validator_runs.csv``. It refuses
partial, hash-mismatched, same-coder, or unresolved-disagreement queues.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = {"Detected", "Missed", "Needs Manual Check", "Baseline Conflict", "Outside Scope", "Ambiguous", "Unrelated"}
REQUIRED_QUEUE_FIELDS = {
    "case_id", "evidence_path", "evidence_sha256", "coder_1_id", "coder_1_decision",
    "coder_1_rationale", "coder_2_id", "coder_2_decision", "coder_2_rationale",
    "agreement", "adjudicator_id", "adjudication_decision", "adjudication_rationale",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(queue: list[dict[str, str]], key: list[dict[str, str]], runs: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if not queue:
        return ["double-coding queue is empty"]
    missing = REQUIRED_QUEUE_FIELDS - set(queue[0])
    if missing:
        errors.append(f"queue is missing fields: {', '.join(sorted(missing))}")
        return errors
    key_by_case = {row.get("case_id", ""): row for row in key}
    run_by_id = {row.get("record_id", ""): row for row in runs}
    if len(key_by_case) != len(key):
        errors.append("steward key contains duplicate case IDs")
    if len({row.get("case_id", "") for row in queue}) != len(queue):
        errors.append("queue contains duplicate case IDs")
    for row in queue:
        case = row.get("case_id", "")
        label = f"{case or '<blank case>'}"
        if case not in key_by_case:
            errors.append(f"{label}: no steward-key row")
            continue
        evidence = ROOT / row["evidence_path"]
        if not evidence.is_file():
            errors.append(f"{label}: missing evidence {evidence}")
        elif sha256(evidence) != row["evidence_sha256"]:
            errors.append(f"{label}: evidence hash mismatch")
        c1, c2 = row.get("coder_1_id", "").strip(), row.get("coder_2_id", "").strip()
        d1, d2 = row.get("coder_1_decision", "").strip(), row.get("coder_2_decision", "").strip()
        if not c1 or not c2 or c1 == c2:
            errors.append(f"{label}: two distinct coder IDs are required")
        if d1 not in DECISIONS or d2 not in DECISIONS:
            errors.append(f"{label}: both coder decisions must be one of {sorted(DECISIONS)}")
        agreement = row.get("agreement", "").strip().lower()
        if agreement not in {"agree", "disagree"}:
            errors.append(f"{label}: agreement must be agree or disagree")
        elif agreement == "agree" and d1 != d2:
            errors.append(f"{label}: agreement=agree but coder decisions differ")
        elif agreement == "disagree":
            if d1 == d2:
                errors.append(f"{label}: agreement=disagree but coder decisions match")
            if not row.get("adjudicator_id", "").strip() or row.get("adjudication_decision", "") not in DECISIONS:
                errors.append(f"{label}: disagreement requires adjudicator ID and decision")
        if not row.get("coder_1_rationale", "").strip() or not row.get("coder_2_rationale", "").strip():
            errors.append(f"{label}: both coder rationales are required")
        if not row.get("adjudication_rationale", "").strip():
            errors.append(f"{label}: adjudication rationale is required")
        canonical = key_by_case[case]
        run = run_by_id.get(canonical.get("record_id", ""))
        if not run:
            errors.append(f"{label}: canonical record is missing")
        elif run.get("report_sha256") != canonical.get("report_sha256"):
            errors.append(f"{label}: canonical report hash differs from steward key")
        elif run.get("coder_1") or run.get("coder_2") or run.get("adjudication"):
            errors.append(f"{label}: canonical coder fields are already populated; refusing overwrite")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", type=Path, default=ROOT / "data" / "double_coding_queue.csv")
    parser.add_argument("--key", type=Path, default=ROOT / "data" / "double_coding_key.csv")
    parser.add_argument("--apply", action="store_true", help="write validated decisions to data/validator_runs.csv")
    args = parser.parse_args()

    queue = read_csv(args.queue)
    key = read_csv(args.key)
    runs_path = ROOT / "data" / "validator_runs.csv"
    runs = read_csv(runs_path)
    errors = validate(queue, key, runs)
    if errors:
        print(json.dumps({"status": "REJECTED", "error_count": len(errors), "errors": errors[:25]}, indent=2))
        return 1
    if not args.apply:
        print(json.dumps({"status": "VALIDATED_NOT_APPLIED", "cases": len(queue), "canonical_path": str(runs_path)}, indent=2))
        return 0

    key_by_case = {row["case_id"]: row for row in key}
    run_by_id = {row["record_id"]: row for row in runs}
    decision_fields = [
        "case_id", "record_id", "artifact_id", "source_golden", "operator", "validator", "configuration",
        "evidence_path", "evidence_sha256", "coder_1_id", "coder_1_decision", "coder_1_rationale",
        "coder_1_relevant_rule_ids", "coder_1_manual_check_status", "coder_1_baseline_conflict",
        "coder_1_outside_scope", "coder_1_collateral_or_unrelated", "coder_2_id", "coder_2_decision",
        "coder_2_rationale", "coder_2_relevant_rule_ids", "coder_2_manual_check_status",
        "coder_2_baseline_conflict", "coder_2_outside_scope", "coder_2_collateral_or_unrelated",
        "agreement", "adjudicator_id", "adjudication_decision", "adjudication_rationale",
    ]
    detailed_decisions: list[dict[str, str]] = []
    for row in queue:
        canonical = key_by_case[row["case_id"]]
        target = run_by_id[canonical["record_id"]]
        target["coder_1"] = row["coder_1_id"]
        target["coder_2"] = row["coder_2_id"]
        target["adjudication"] = row["adjudication_decision"]
        target["notes"] = (target.get("notes", "") + ";double_coding_agreement=" + row["agreement"]).strip(";")
        detailed_decisions.append({
            **{field: canonical.get(field, "") for field in ("case_id", "record_id", "artifact_id", "source_golden", "operator", "validator", "configuration")},
            **{field: row.get(field, "") for field in decision_fields if field not in {"case_id", "record_id", "artifact_id", "source_golden", "operator", "validator", "configuration"}},
        })
    fields = list(runs[0])
    with runs_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(runs, key=lambda item: item.get("record_id", "")))
    decisions_path = ROOT / "data" / "double_coding_decisions.csv"
    with decisions_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=decision_fields)
        writer.writeheader()
        writer.writerows(sorted(detailed_decisions, key=lambda item: item.get("case_id", "")))
    print(json.dumps({"status": "APPLIED", "cases": len(queue), "canonical_path": str(runs_path), "detailed_decisions_path": str(decisions_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
