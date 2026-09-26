"""Classify completed PAC Formal M04-M10 batches against golden baselines."""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = {
    "M04": {
        "terms": ("content association", "parent tree", "association"),
        "description": "marked-content association",
    },
    "M05": {
        "terms": ("content sequence", "reading order", "marked content"),
        "description": "internal marked-content sequence",
    },
    "M06": {
        "terms": ("lbl and lbody", "list item", "list containment", "duplicate list"),
        "description": "duplicate list-item reference",
    },
    "M07": {
        "terms": ("alternative descriptions", "alternate description", "alt", "figure"),
        "description": "missing figure alternate description",
    },
    "M08": {
        "terms": ("natural language", "language", "lang"),
        "description": "missing document language metadata",
    },
    "M09": {
        "terms": ("role mapping", "rolemap", "role map", "custom role", "unknown role"),
        "description": "invalid RoleMap target",
    },
    "M10": {
        "terms": ("structure tree", "table", "th", "td", "cell"),
        "description": "illegal table-child role",
    },
}
CLASSIFICATIONS = {
    "INTENDED_DETECTION",
    "COLLATERAL_DETECTION",
    "BASELINE_CARRIED",
    "UNRELATED_FAILURE",
    "AMBIGUOUS",
    "SURVIVED_AUTOMATED_CHECKS",
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
    all_matrix: dict[str, list[dict[str, str]]] = {operator: [] for operator in OPS}

    for operator, spec in OPS.items():
        mutants = sorted(
            [
                row for row in runs
                if row.get("validator") == "PAC"
                and row.get("configuration") == "Formal"
                and row.get("baseline_or_mutant") == "mutant"
                and row.get("operator") == operator
            ],
            key=lambda row: row.get("artifact_id", ""),
        )
        if not mutants:
            raise SystemExit(f"No PAC Formal {operator} records found")

        for mutant in mutants:
            golden = baselines.get(mutant.get("source_golden", ""))
            if not golden:
                raise SystemExit(f"Missing PAC Formal golden baseline for {mutant['artifact_id']}")
            golden_rules = split_rules(golden.get("relevant_rule_ids", ""))
            mutant_rules = split_rules(mutant.get("relevant_rule_ids", ""))
            new_rules = sorted(mutant_rules - golden_rules)
            baseline_carried = sorted(mutant_rules & golden_rules)
            evidence = " ".join([
                " ".join(new_rules),
                mutant.get("relevant_rule_text", ""),
            ]).lower()
            intended = [
                rule for rule in new_rules
                if any(term in (rule + " " + evidence) for term in spec["terms"])
            ]

            if intended:
                classification = "INTENDED_DETECTION"
                if operator == "M10" and "Structure tree" in intended:
                    reason = "PAC reported a new Structure tree failure, the direct structural consequence of the illegal table-child role."
                else:
                    reason = f"PAC reported a new automated finding corresponding to the M04-M10 {spec['description']} mutation."
            elif new_rules:
                classification = "COLLATERAL_DETECTION"
                reason = "The mutant adds automated rule(s), but they do not correspond to the intended " + spec["description"] + " property: " + ", ".join(new_rules) + "."
            elif mutant.get("automated_pass_fail") == "FAIL" and golden.get("automated_pass_fail") == "FAIL":
                classification = "BASELINE_CARRIED"
                reason = "All mutant automated failures are already present in the matching PAC golden baseline."
            elif mutant.get("automated_pass_fail") in {"PASS", "FAIL"}:
                classification = "SURVIVED_AUTOMATED_CHECKS"
                reason = "PAC reported no new automated finding corresponding to the intended " + spec["description"] + " property."
            else:
                classification = "AMBIGUOUS"
                reason = "PAC outcome could not be classified from the available report."

            if classification not in CLASSIFICATIONS:
                raise SystemExit(f"Unexpected classification for {mutant['artifact_id']}: {classification}")
            mutant["raw_detection_classification"] = classification
            mutant["detection_classification"] = classification
            mutant["classification_reason"] = reason
            note = (
                f"{operator.lower()}_new_rule_ids={';'.join(new_rules)};"
                f"{operator.lower()}_baseline_carried_rule_ids={';'.join(baseline_carried)};"
                f"{operator.lower()}_intended_property_findings={';'.join(intended)}"
            )
            mutant["notes"] = (mutant.get("notes", "") + ";" + note).strip(";")
            all_matrix[operator].append({
                "mutant_id": mutant.get("artifact_id", ""),
                "operator": operator,
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

    fields = list(runs[0])
    with runs_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(runs, key=lambda row: row.get("record_id", "")))

    delta_path = ROOT / "data" / "baseline_deltas.csv"
    deltas = read_csv(delta_path)
    by_record = {row.get("record_id", ""): row for row in deltas}
    for mutant in runs:
        if mutant.get("operator") in OPS and mutant.get("validator") == "PAC" and mutant.get("configuration") == "Formal" and mutant.get("baseline_or_mutant") == "mutant":
            key = mutant.get("record_id", "")
            if key in by_record:
                by_record[key]["delta_state"] = mutant.get("detection_classification", "")
                by_record[key]["notes"] = mutant.get("classification_reason", "")
    if deltas:
        delta_fields = list(deltas[0])
        with delta_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=delta_fields)
            writer.writeheader()
            writer.writerows(sorted(by_record.values(), key=lambda row: row.get("record_id", "")))

    counts: dict[str, int] = {}
    for operator, matrix in all_matrix.items():
        path = ROOT / "analysis" / "generated" / f"pac_formal_{operator.lower()}_matrix.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        matrix_fields = list(matrix[0])
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=matrix_fields)
            writer.writeheader()
            writer.writerows(matrix)
        for row in matrix:
            counts[row["classification"]] = counts.get(row["classification"], 0) + 1
        print(f"{operator}: {len(matrix)} records")
    print("Totals: " + ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
