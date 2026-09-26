"""Prepare a blinded, hash-linked first-pass queue for formal double-coding.

This script never writes ``data/validator_runs.csv`` and never changes a
classification.  It creates an opaque evidence packet for independent coders,
plus a steward-only key that restores the canonical artifact/operator labels
for adjudication.  The packet is intentionally incomplete until two people
record decisions and an adjudicator resolves disagreements.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL_CONFIGS = {"Formal", "Full Check", "PDF/UA-1 ua1"}
VALIDATORS = {"PAC", "Acrobat", "veraPDF"}

QUEUE_FIELDS = [
    "case_id", "evidence_path", "evidence_sha256", "evidence_format",
    "coder_1_id", "coder_1_decision", "coder_1_rationale",
    "coder_1_relevant_rule_ids", "coder_1_manual_check_status",
    "coder_1_baseline_conflict", "coder_1_outside_scope",
    "coder_1_collateral_or_unrelated",
    "coder_2_id", "coder_2_decision", "coder_2_rationale",
    "coder_2_relevant_rule_ids", "coder_2_manual_check_status",
    "coder_2_baseline_conflict", "coder_2_outside_scope",
    "coder_2_collateral_or_unrelated", "agreement",
    "adjudicator_id", "adjudication_decision", "adjudication_rationale",
]

KEY_FIELDS = [
    "case_id", "record_id", "artifact_id", "source_golden", "operator",
    "validator", "configuration", "report_path", "report_sha256",
    "file_sha256", "baseline_run_id", "baseline_report_path",
    "baseline_report_sha256", "canonical_classification",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def active_mutants() -> set[str]:
    excluded = {
        row["mutant_id"]
        for row in read_csv(ROOT / "data" / "mutant_exclusions.csv")
        if row.get("status")
    }
    return {
        row["mutant_id"]
        for row in read_jsonl(ROOT / "data" / "mutants.jsonl")
        if row.get("status") == "valid"
        and row.get("verification", {}).get("mutation_valid") is True
        and row["mutant_id"] not in excluded
    }


def formal_rows() -> list[dict[str, str]]:
    active = active_mutants()
    rows = read_csv(ROOT / "data" / "validator_runs.csv")
    selected = [
        row for row in rows
        if row.get("baseline_or_mutant") == "mutant"
        and row.get("artifact_id") in active
        and row.get("configuration") in FORMAL_CONFIGS
        and row.get("validator") in VALIDATORS
    ]
    return sorted(selected, key=lambda row: row["record_id"])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="copy reports to opaque evidence/double_coding/DC-*.ext paths",
    )
    args = parser.parse_args()

    rows = formal_rows()
    if not rows:
        raise SystemExit("No active formal validator rows found")

    baselines = {
        (row.get("source_golden", ""), row.get("validator", ""), row.get("configuration", "")): row
        for row in read_csv(ROOT / "data" / "validator_runs.csv")
        if row.get("baseline_or_mutant") == "golden_baseline"
    }
    packet_dir = ROOT / "evidence" / "double_coding"
    packet_dir.mkdir(parents=True, exist_ok=True)
    queue: list[dict[str, str]] = []
    key: list[dict[str, str]] = []

    for index, row in enumerate(rows, start=1):
        case_id = f"DC-{index:04d}"
        source = ROOT / row["raw_report_path"]
        if not source.is_file():
            raise SystemExit(f"Missing raw report for {case_id}: {source}")
        suffix = source.suffix.lower() or ".bin"
        destination = packet_dir / f"{case_id}{suffix}"
        if args.materialize:
            shutil.copyfile(source, destination)
            if sha256(destination) != row["report_sha256"]:
                raise SystemExit(f"Materialized hash mismatch for {case_id}")
        evidence_path = destination.relative_to(ROOT).as_posix() if args.materialize else row["raw_report_path"].replace("\\", "/")
        baseline = baselines.get((row.get("source_golden", ""), row.get("validator", ""), row.get("configuration", "")), {})
        queue.append({
            "case_id": case_id,
            "evidence_path": evidence_path,
            "evidence_sha256": row["report_sha256"],
            "evidence_format": suffix.lstrip("."),
            **{field: "" for field in QUEUE_FIELDS[4:]},
        })
        key.append({
            "case_id": case_id,
            "record_id": row["record_id"],
            "artifact_id": row["artifact_id"],
            "source_golden": row["source_golden"],
            "operator": row["operator"],
            "validator": row["validator"],
            "configuration": row["configuration"],
            "report_path": row["raw_report_path"].replace("\\", "/"),
            "report_sha256": row["report_sha256"],
            "file_sha256": row["file_sha256"],
            "baseline_run_id": baseline.get("record_id", ""),
            "baseline_report_path": baseline.get("raw_report_path", ""),
            "baseline_report_sha256": baseline.get("report_sha256", ""),
            "canonical_classification": row.get("detection_classification", ""),
        })

    write_csv(ROOT / "data" / "double_coding_queue.csv", queue, QUEUE_FIELDS)
    write_csv(ROOT / "data" / "double_coding_key.csv", key, KEY_FIELDS)
    manifest = {
        "status": "READY_FOR_INDEPENDENT_CODING",
        "case_count": len(queue),
        "source": "data/validator_runs.csv",
        "scope": "active mutant rows with Formal, Full Check, or PDF/UA-1 ua1 configuration",
        "blinding": "queue omits artifact, source, operator, validator, configuration, and canonical classification; steward key retains them",
        "materialized": args.materialize,
        "queue_path": "data/double_coding_queue.csv",
        "key_path": "data/double_coding_key.csv",
        "packet_path": "evidence/double_coding",
        "completion_rule": "Do not populate canonical coder fields until two separately recorded decision fields and any adjudication are recorded; this process does not establish independent human coding unless external provenance is retained.",
    }
    (ROOT / "data" / "double_coding_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "cases": len(queue), "materialized": args.materialize}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
