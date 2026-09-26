"""Build the validator capability matrix from operator specs and canonical runs."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import yaml

from verify_study_state import ROOT, read_csv, read_jsonl


def main() -> int:
    spec = yaml.safe_load((ROOT / "operators" / "operators.yaml").read_text(encoding="utf-8"))
    operators = {row["id"]: row for row in spec["operators"]}
    exclusions = {row["mutant_id"] for row in read_csv(ROOT / "data" / "mutant_exclusions.csv") if row.get("status")}
    manifest = [row for row in read_jsonl(ROOT / "data" / "mutants.jsonl") if str(row.get("status", "")).lower() == "valid" and row.get("mutant_id") not in exclusions and row.get("verification", {}).get("mutation_valid") is True]
    active_ids = {row["mutant_id"] for row in manifest}
    runs = [row for row in read_csv(ROOT / "data" / "validator_runs.csv") if row.get("baseline_or_mutant") == "mutant" and row.get("artifact_id") in active_ids and row.get("configuration") in {"Formal", "Full Check", "PDF/UA-1 ua1"}]
    output = []
    for operator, op in operators.items():
        for validator in ("PAC", "Acrobat", "veraPDF"):
            subset = [row for row in runs if row.get("operator") == operator and row.get("validator") == validator]
            rules = sorted({rule for row in subset for rule in (row.get("relevant_rule_ids") or "").split(";") if rule and rule not in {"NONE_REPORTED", "MANUAL_CHECK_PROMPTS:2"}})
            classes = Counter(row.get("detection_classification") or "UNCLASSIFIED" for row in subset)
            output.append({
                "property": op["accessibility_property"],
                "operator": operator,
                "validator": validator,
                "claimed_support": "claimed machine-checkable" if op.get("machine_checkable") else "semantic/outside formal claim",
                "tested_profile": sorted({row.get("profile", "") for row in subset})[0] if subset else "NO_RUN",
                "relevant_rule": ";".join(rules) or ";".join(op.get("known_applicable_validator_rules", [])),
                "baseline_status": ";".join(sorted({row.get("baseline_status", "") for row in subset})) or "NO_RUN",
                "detection_result": f"Detected={classes['Detected']};Missed={classes['Missed']};Manual={classes['Needs Manual Check']};NotApplicable={classes['Not Applicable']}",
                "evidence_quality": "hash-linked report; role-labeled classification fields and adjudication metadata retained as audit provenance",
                "interpretation": "mutation-specific detection outcome; Class B survival is not a validator failure" if op["class"] == "class_b" else "mutation-specific detection outcome, subject to baseline delta",
            })
    out_path = ROOT / "analysis" / "generated" / "validator_capability_matrix.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)
    print(f"Wrote {len(output)} capability rows to {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
