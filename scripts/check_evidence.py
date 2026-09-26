from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    queue_path = ROOT / "manual_runs_todo.csv"
    if not queue_path.exists():
        print("Evidence status: blocked; manual_runs_todo.csv is missing.")
        return 2
    with queue_path.open(newline="", encoding="utf-8-sig") as fh:
        queue = list(csv.DictReader(fh))
    expected = [
        row for row in queue
        if row.get("baseline_or_mutant") != "setup"
        # PAC AI remains an explicitly deferred aggregate-only future-work
        # cohort; its selection queue is not a completed evidence gate.
        and row.get("batch_id") != "B08_MUTANT_PAC_AI_SELECTED"
    ]
    public_records_path = ROOT / "data" / "public_evidence_records.csv"
    raw_evidence_present = any((ROOT / "evidence" / directory).exists() for directory in ("pac", "acrobat", "verapdf", "at", "controls", "double_coding"))
    if not raw_evidence_present and public_records_path.is_file():
        with public_records_path.open(newline="", encoding="utf-8-sig") as fh:
            public_records = list(csv.DictReader(fh))
        if len(public_records) == 207 and all(row.get("raw_evidence_sha256") for row in public_records):
            print("Evidence status: public sanitized boundary; 207 formal evidence records and preserved raw hashes are present; excluded native report bytes are not required in the public checkout.")
            return 0
        print("Evidence status: public sanitized boundary is incomplete; expected 207 hash-linked formal records.")
        return 1
    found = []
    missing = []
    for row in expected:
        # B09 is represented by the canonical AT ledger and the preserved raw
        # NVDA log rather than by the legacy hash-named manual queue files.
        at_complete = False
        if row.get("validator") == "NVDA" and row.get("batch_id") == "B09_AT_REPRESENTATIVE":
            observations_path = ROOT / "data" / "at_observations.csv"
            if observations_path.exists():
                with observations_path.open(newline="", encoding="utf-8") as observations_file:
                    for observation in csv.DictReader(observations_file):
                        if observation.get("artifact_id") == row.get("artifact_id"):
                            evidence_path = ROOT / observation.get("evidence_path", "")
                            raw_log_path = ROOT / observation.get("raw_log_path", "")
                            at_complete = (
                                observation.get("status") == "COMPLETE"
                                and evidence_path.is_file()
                                and raw_log_path.is_file()
                            )
                            break
        path = ROOT / row["evidence_destination"] / row["exact_output_filename"]
        native = path.with_suffix(".accreport.html") if row.get("validator") == "Acrobat" and path.suffix.lower() == ".json" else None
        if at_complete or path.is_file() or (native is not None and native.is_file()):
            found.append(row)
        else:
            missing.append(row)
    print(f"Evidence status: {len(found)}/{len(expected)} prescribed files found; {len(missing)} remain TODO.")
    for row in missing[:40]:
        print(f"TODO {row['batch_id']} {row['validator']} {row['artifact_id']} {row['sha256']}")
    if len(missing) > 40:
        print(f"... {len(missing) - 40} additional TODO rows omitted")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
