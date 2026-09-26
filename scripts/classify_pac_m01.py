"""Classify the completed PAC Formal M01 sub-batch against golden baselines."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASSIFICATIONS = {
    "INTENDED_DETECTION", "COLLATERAL_DETECTION", "BASELINE_CARRIED",
    "UNRELATED_FAILURE", "AMBIGUOUS", "SURVIVED_AUTOMATED_CHECKS",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def split_rules(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def main() -> int:
    runs_path = ROOT / "data" / "validator_runs.csv"
    runs = read_csv(runs_path)
    baselines = {
        row["artifact_id"]: row
        for row in runs
        if row.get("validator") == "PAC"
        and row.get("configuration") == "Formal"
        and row.get("baseline_or_mutant") == "golden_baseline"
    }
    mutants = sorted(
        [
            row for row in runs
            if row.get("validator") == "PAC"
            and row.get("configuration") == "Formal"
            and row.get("baseline_or_mutant") == "mutant"
            and row.get("operator") == "M01"
        ],
        key=lambda row: row.get("artifact_id", ""),
    )
    if len(mutants) != 9:
        raise SystemExit(f"Expected 9 PAC Formal M01 records, found {len(mutants)}")

    matrix = []
    for mutant in mutants:
        golden = baselines.get(mutant.get("source_golden", ""))
        if not golden:
            raise SystemExit(f"Missing PAC Formal golden baseline for {mutant['artifact_id']}")
        golden_rules = split_rules(golden.get("relevant_rule_ids", ""))
        mutant_rules = split_rules(mutant.get("relevant_rule_ids", ""))
        new_rules = sorted(mutant_rules - golden_rules)
        baseline_carried = sorted(mutant_rules & golden_rules)
        mutant_text = mutant.get("relevant_rule_text", "")
        intended_terms = ("reading order", "reading-order", "logical order", "content sequence")
        intended = [
            rule for rule in sorted(mutant_rules)
            if any(term in (rule + " " + mutant_text).lower() for term in intended_terms)
        ]
        manual_items = mutant.get("notes", "")
        if intended:
            classification = "INTENDED_DETECTION"
            reason = "A new PAC automated finding explicitly matches the M01 reading-order/semantic-order property."
        elif new_rules:
            classification = "COLLATERAL_DETECTION"
            reason = "The mutant adds automated rule(s) outside M01 reading-order semantics: " + ", ".join(new_rules) + "."
        elif mutant.get("automated_pass_fail") == "FAIL" and baseline.get("automated_pass_fail") == "FAIL":
            classification = "BASELINE_CARRIED"
            reason = "All mutant automated failures are already present in the matching PAC golden baseline."
        elif mutant.get("automated_pass_fail") in {"PASS", "FAIL"}:
            classification = "SURVIVED_AUTOMATED_CHECKS"
            reason = "PAC reported no new automated finding relevant to M01 reading-order/semantic-order mutation."
        else:
            classification = "AMBIGUOUS"
            reason = "PAC outcome could not be classified from the available report."
        if classification not in CLASSIFICATIONS:
            raise SystemExit(f"Unexpected classification for {mutant['artifact_id']}: {classification}")
        mutant["raw_detection_classification"] = classification
        mutant["detection_classification"] = classification
        mutant["classification_reason"] = reason
        mutant["notes"] = (mutant.get("notes", "") + f";m01_new_rule_ids={';'.join(new_rules)};m01_baseline_carried_rule_ids={';'.join(baseline_carried)};m01_intended_property_findings={';'.join(intended)}").strip(";")
        matrix.append({
            "mutant_id": mutant.get("artifact_id", ""),
            "operator": "M01",
            "source_golden": mutant.get("source_golden", ""),
            "mutant_pdf_sha256": mutant.get("file_sha256", ""),
            "golden_pdf_sha256": golden.get("file_sha256", ""),
            "golden_automated_findings": golden.get("relevant_rule_ids", "") or "none",
            "mutant_automated_findings": mutant.get("relevant_rule_ids", "") or "none",
            "new_automated_findings": ";".join(new_rules) or "none",
            "manual_check_items": mutant.get("manual_check_prompts", "0") or "0",
            "baseline_carried_findings": ";".join(baseline_carried) or "none",
            "intended_property_finding": ";".join(intended) or "none",
            "baseline_status": mutant.get("baseline_status", ""),
            "classification": classification,
            "raw_report_path": mutant.get("raw_report_path", ""),
            "report_sha256": mutant.get("report_sha256", ""),
            "audit_note": reason,
        })

    fields = [
        "record_id", "artifact_id", "baseline_or_mutant", "source_golden", "operator", "file_sha256",
        "validator", "configuration", "validator_version", "build", "platform", "profile",
        "PAC_AI_enabled", "run_timestamp", "automated_pass_fail", "relevant_rule_ids", "relevant_rule_text",
        "manual_check_prompts", "raw_report_path", "report_sha256", "raw_detection_classification",
        "baseline_status", "baseline_file_sha256", "baseline_run_id", "detection_classification",
        "classification_reason", "coder_1", "coder_2", "adjudication", "notes",
    ]
    with runs_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader(); writer.writerows(sorted(runs, key=lambda row: row.get("record_id", "")))

    delta_path = ROOT / "data" / "baseline_deltas.csv"
    deltas = read_csv(delta_path)
    by_record = {row.get("record_id", ""): row for row in deltas}
    for mutant in mutants:
        key = mutant.get("record_id", "")
        if key in by_record:
            by_record[key]["delta_state"] = mutant["detection_classification"]
            by_record[key]["notes"] = mutant["classification_reason"]
    if deltas:
        delta_fields = list(deltas[0])
        with delta_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=delta_fields)
            writer.writeheader(); writer.writerows(sorted(by_record.values(), key=lambda row: row.get("record_id", "")))

    matrix_path = ROOT / "analysis" / "generated" / "pac_formal_m01_matrix.csv"
    matrix_path.parent.mkdir(parents=True, exist_ok=True)
    matrix_fields = list(matrix[0])
    with matrix_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=matrix_fields)
        writer.writeheader(); writer.writerows(matrix)

    counts = {}
    for row in matrix:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1
    print(f"Classified {len(matrix)} PAC Formal M01 records: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
