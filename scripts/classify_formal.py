"""Classify active formal validator runs against their matching golden evidence.

The classifier writes the existing ``validator_runs.csv`` classification fields and
updates ``baseline_deltas.csv``.  It does not inspect or modify any PDF.  Rule
matching is intentionally conservative: only an exact, documented automated
checkpoint (or an explicitly named Acrobat manual checkpoint) can affect the
classification.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN_FIELDS = [
    "record_id", "artifact_id", "baseline_or_mutant", "source_golden", "operator", "file_sha256",
    "validator", "configuration", "validator_version", "build", "platform", "profile",
    "PAC_AI_enabled", "run_timestamp", "automated_pass_fail", "relevant_rule_ids",
    "relevant_rule_text", "manual_check_prompts", "raw_report_path", "report_sha256",
    "raw_detection_classification", "baseline_status", "baseline_file_sha256", "baseline_run_id",
    "detection_classification", "classification_reason", "coder_1", "coder_2", "adjudication", "notes",
]
FINAL = {"Detected", "Missed", "Needs Manual Check", "Not Applicable"}
VALIDATORS = {"PAC", "Acrobat", "veraPDF"}
FORMAL_CONFIGS = {"Formal", "Full Check", "PDF/UA-1 ua1"}

# These are the exact checkpoint names/descriptions observed in the canonical
# reports and mapped by the operator specifications.  Generic structural,
# syntax, header, or parser findings are deliberately not included.
AUTOMATED_TERMS = {
    ("PAC", "M03"): ("structure elements",),
    ("PAC", "M07"): ("alternative descriptions",),
    ("PAC", "M08"): ("natural language",),
    ("PAC", "M09"): ("role mapping",),
    ("PAC", "M10"): ("structure tree",),
    ("Acrobat", "M03"): ("appropriate nesting",),
    ("Acrobat", "M07"): ("figures alternate text",),
    ("Acrobat", "M08"): ("primary language",),
    ("Acrobat", "M06"): ("list items", "lbl and lbody"),
    ("Acrobat", "M10"): ("th and td", "rows"),
    ("veraPDF", "M03"): ("heading", "heading hierarchy"),
    ("veraPDF", "M06"): ("list item", "list containment", "duplicate"),
    ("veraPDF", "M07"): ("alternate description", "figure"),
    ("veraPDF", "M08"): ("natural language",),
    ("veraPDF", "M09"): ("rolemap", "role map", "role mapping", "custom role", "undefined role"),
    ("veraPDF", "M10"): ("tr element may contain only th and td", "table child", "prohibited"),
}
MANUAL_TERMS = {
    ("Acrobat", "M01"): ("logical reading order",),
    ("Acrobat", "M05"): ("logical reading order",),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def split(value: str) -> set[str]:
    sentinels = {"NONE", "NONE_REPORTED"}
    return {part.strip() for part in value.split(";") if part.strip() and part.strip().upper() not in sentinels}


def text_matches(value: str, terms: tuple[str, ...]) -> list[str]:
    lower = value.lower()
    return [term for term in terms if term in lower]


def active_mutant_records() -> dict[str, dict]:
    excluded = {row.get("mutant_id", "") for row in read_csv(ROOT / "data" / "mutant_exclusions.csv") if row.get("status")}
    active: dict[str, dict] = {}
    path = ROOT / "data" / "mutants.jsonl"
    if not path.exists():
        return active
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("status") == "valid" and item.get("verification", {}).get("mutation_valid") and item.get("mutant_id") not in excluded:
            active[item.get("mutant_id", "")] = item
    return active


def acrobat_m10_headers_proxy(
    row: dict[str, str],
    baseline: dict[str, str],
    new_rules: set[str],
    mutant: dict | None,
) -> bool:
    """Apply the M10 direct-consequence proxy fixed before final adjudication, fail-closed."""
    if row.get("validator") != "Acrobat" or row.get("operator") != "M10" or not mutant:
        return False
    if row.get("automated_pass_fail") != "FAIL" or "headers" not in {rule.lower() for rule in new_rules}:
        return False
    if "headers" in {rule.lower() for rule in split(baseline.get("relevant_rule_ids", ""))}:
        return False
    delta = mutant.get("generation", {}).get("delta", {})
    verification = mutant.get("verification", {})
    checks = verification.get("invariant_checks", {})
    required_checks = (
        "operator_specific_delta",
        "page_content_byte_hashes_equal",
        "rendering_preserved",
        "source_and_mutant_hash_differ",
    )
    return (
        delta.get("old_role") == "/TH"
        and delta.get("new_role") == "/P"
        and mutant.get("mutant_sha256") == row.get("file_sha256")
        and mutant.get("source_sha256") == baseline.get("file_sha256")
        and verification.get("mutation_valid") is True
        and all(checks.get(name) is True for name in required_checks)
    )


def main() -> int:
    runs_path = ROOT / "data" / "validator_runs.csv"
    runs = read_csv(runs_path)
    if not runs:
        raise SystemExit("validator_runs.csv is empty")
    active_records = active_mutant_records()
    active = set(active_records)
    excluded_ids = {row.get("mutant_id", "") for row in read_csv(ROOT / "data" / "mutant_exclusions.csv") if row.get("status")}
    baselines = {
        (row.get("artifact_id", ""), row.get("validator", ""), row.get("configuration", "")): row
        for row in runs
        if row.get("baseline_or_mutant") == "golden_baseline" and row.get("validator") in VALIDATORS
    }
    counts: dict[str, dict[str, int]] = {validator: {label: 0 for label in sorted(FINAL)} for validator in sorted(VALIDATORS)}
    classified_ids: set[str] = set()

    # PAC AI has its own aggregate-only adjudication table.  Never leave a
    # formal classification in these rows, including residue from older runs.
    for row in runs:
        if row.get("validator") == "PAC" and row.get("configuration") == "AI":
            row["raw_detection_classification"] = ""
            row["detection_classification"] = ""
            row["classification_reason"] = (
                "PAC AI is evaluated separately in data/pac_ai_classifications.csv; "
                "no formal mutation-specific classification is inferred here."
            )
            note_parts = [part for part in row.get("notes", "").split(";") if part and not part.startswith("formal_classification=")]
            row["notes"] = ";".join(note_parts)

    for row in runs:
        if (
            row.get("baseline_or_mutant") != "mutant"
            or row.get("artifact_id") not in active
            or row.get("validator") not in VALIDATORS
            or row.get("configuration") not in FORMAL_CONFIGS
        ):
            continue
        key = (row.get("source_golden", ""), row.get("validator", ""), row.get("configuration", ""))
        baseline = baselines.get(key)
        if not baseline:
            classification = "Needs Manual Check"
            reason = "No matching golden baseline record exists; classification is withheld pending baseline review."
            baseline_rules: set[str] = set()
            new_rules: set[str] = set()
        else:
            baseline_rules = split(baseline.get("relevant_rule_ids", ""))
            mutant_rules = split(row.get("relevant_rule_ids", ""))
            new_rules = mutant_rules - baseline_rules
            evidence = " ".join((row.get("relevant_rule_ids", ""), row.get("relevant_rule_text", "")))
            terms = AUTOMATED_TERMS.get((row.get("validator", ""), row.get("operator", "")), ())
            intended = text_matches(evidence, terms)
            manual = text_matches(row.get("notes", ""), MANUAL_TERMS.get((row.get("validator", ""), row.get("operator", "")), ()))
            # Match only new automated findings.  A rule already present in the
            # golden is baseline-carried and cannot be a mutation detection.
            new_evidence = " ".join(sorted(new_rules)) + " " + row.get("relevant_rule_text", "")
            intended_new = text_matches(new_evidence, terms) if new_rules else []
            m10_headers_proxy = acrobat_m10_headers_proxy(row, baseline, new_rules, active_records.get(row.get("artifact_id", "")))
            if intended_new and row.get("automated_pass_fail") == "FAIL":
                classification = "Detected"
                reason = f"New automated checkpoint(s) {', '.join(intended_new)} match the intended {row.get('operator')} property."
            elif m10_headers_proxy:
                classification = "Detected"
                reason = (
                    "New Acrobat Headers failure satisfies the M10 direct-consequence proxy fixed before final adjudication: "
                    "the hash-linked manifest verifies the sole semantic change is /TH to /P under the same table row, "
                    "with target content, non-target structure, page content, and rendering preserved."
                )
            elif manual and row.get("validator") == "Acrobat":
                classification = "Needs Manual Check"
                reason = f"Acrobat emitted the manual checkpoint(s) {', '.join(manual)}; manual prompts are retained separately and are not automated detections."
            elif row.get("automated_pass_fail") in {"PASS", "FAIL"}:
                classification = "Missed"
                if new_rules:
                    reason = f"No new automated checkpoint matched the intended {row.get('operator')} property; unrelated/collateral new finding(s) {', '.join(sorted(new_rules))} are not counted."
                else:
                    reason = f"No new automated checkpoint matched the intended {row.get('operator')} property."
            else:
                classification = "Needs Manual Check"
                reason = "Validator outcome is not machine-classifiable from the canonical report."
            if row.get("source_golden") == "PDFUA-Ref-2-05_BookChapter-german" and row.get("validator") == "Acrobat":
                reason += " G05's pre-existing Lbl and LBody failure is baseline context; only new operator-specific failures are considered."
            if row.get("source_golden") == "PDFUA-Ref-2-09_Scanned" and row.get("validator") == "PAC":
                reason += " G09's Natural language baseline failure is confined to excluded M08; active operators are compared only on new rules."

            baseline_report = baseline.get("raw_report_path", "") if baseline else "missing"
            reason += (
                f" Evidence: baseline report={baseline_report}; mutant report={row.get('raw_report_path', '')};"
                f" baseline_sha256={baseline.get('file_sha256', '') if baseline else 'missing'};"
                f" mutant_sha256={row.get('file_sha256', '')}; baseline_rules={';'.join(sorted(baseline_rules)) or 'none'};"
                f" mutant_rules={row.get('relevant_rule_ids', '') or 'none'}."
            )
        row["raw_detection_classification"] = classification
        row["detection_classification"] = classification
        row["classification_reason"] = reason
        if row.get("baseline_or_mutant") == "mutant":
            note_parts = [part for part in row.get("notes", "").split(";") if part and not part.startswith("formal_classification=")]
            row["notes"] = ";".join(note_parts + [f"formal_classification={classification}"])
        counts[row.get("validator", "")][classification] += 1
        classified_ids.add(row.get("artifact_id", "") + "::" + row.get("validator", ""))

    # Keep the documented excluded evidence explicit without adding it to the
    # active-mutant denominator.
    for row in runs:
        if (
            row.get("baseline_or_mutant") == "mutant"
            and row.get("artifact_id") in excluded_ids
            and row.get("configuration") in FORMAL_CONFIGS
        ):
            row["raw_detection_classification"] = "Not Applicable"
            row["detection_classification"] = "Not Applicable"
            row["classification_reason"] = (
                "Not applicable to the active formal denominator: this mutant is excluded by the documented baseline conflict in "
                "data/mutant_exclusions.csv; retain its raw report as audit evidence."
            )

    write_csv(runs_path, sorted(runs, key=lambda item: item.get("record_id", "")), RUN_FIELDS)

    # The steward key is not shown to blinded coders, but its canonical field
    # must follow the authoritative formal classification after adjudication.
    key_path = ROOT / "data" / "double_coding_key.csv"
    key_rows = read_csv(key_path)
    if key_rows:
        classification_by_record = {row.get("record_id", ""): row.get("detection_classification", "") for row in runs}
        for item in key_rows:
            if item.get("record_id", "") in classification_by_record:
                item["canonical_classification"] = classification_by_record[item["record_id"]]
        write_csv(key_path, key_rows, list(key_rows[0]))

    delta_path = ROOT / "data" / "baseline_deltas.csv"
    deltas = read_csv(delta_path)
    by_record = {row.get("record_id", ""): row for row in deltas}
    for row in runs:
        if row.get("record_id") in by_record and row.get("artifact_id", "") in active:
            by_record[row["record_id"]]["delta_state"] = row.get("detection_classification", "")
            by_record[row["record_id"]]["notes"] = row.get("classification_reason", "")
    if deltas:
        write_csv(delta_path, sorted(by_record.values(), key=lambda item: item.get("record_id", "")), list(deltas[0]))

    print(json.dumps({"active_mutants": len(active), "classified_rows": len(classified_ids), "counts": counts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
