import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
MANIFEST = Path(r"C:\Users\iamga\AppData\Local\Temp\codex-file-preview-2KwQjb\manual_validator_manifest.csv")


operator_names = {
    "M01": "Structural reading-order swap",
    "M02": "Omit visible content from tag structure",
    "M03": "Incorrect heading level / skipped hierarchy",
    "M04": "Wrong marked-content association",
    "M05": "Internal MCID sequence reversal",
}

non_generated = {
    ("G05", "M03"): "Not generated: no suitable heading-hierarchy target in G05.",
    ("G05", "M05"): "Not generated: no suitable multi-MCID target in G05.",
}

detected_by = {
    "PAC": {"G01_M03", "G02_M03", "G03_M03", "G04_M03"},
    "Acrobat": {"G01_M03", "G02_M03", "G02_M04", "G03_M03", "G04_M03"},
    "veraPDF": {"G01_M03", "G02_M03", "G02_M04", "G03_M03", "G04_M03"},
}

failure_details = {
    "PAC": {
        "G01_M03": ("Not compliant", "Structure Elements", ">=1", "Detected"),
        "G02_M03": ("Not compliant", "Structure Elements", ">=1", "Detected"),
        "G03_M03": ("Not compliant", "Structure Elements", "1", "Detected"),
        "G04_M03": ("Not compliant", "Structure Elements", ">=1", "Detected"),
    },
    "Acrobat": {
        "G01_M03": ("Failed", "Headings: Appropriate nesting", "1", "Detected"),
        "G02_M03": ("Failed", "Headings: Appropriate nesting", "1", "Detected"),
        "G02_M04": ("Failed", "Lists: List items; Lbl and LBody", "2", "Detected"),
        "G03_M03": ("Failed", "Headings: Appropriate nesting", "1", "Detected"),
        "G04_M03": ("Failed", "Headings: Appropriate nesting", "1", "Detected"),
    },
    "veraPDF": {
        "G01_M03": ("Failed", "ISO 14289-1:2014 7.4.2 test 1: heading hierarchy skips level", "1", "Detected"),
        "G02_M03": ("Failed", "ISO 14289-1:2014 7.4.2 test 1: heading hierarchy skips level", "1", "Detected"),
        "G02_M04": ("Failed", "ISO 14289-1:2014 7.2 tests 17-20: list containment/child constraints", "4", "Detected"),
        "G03_M03": ("Failed", "ISO 14289-1:2014 7.4.2 test 1: heading hierarchy skips level", "1", "Detected"),
        "G04_M03": ("Failed", "ISO 14289-1:2014 7.4.2 test 1: heading hierarchy skips level", "1", "Detected"),
    },
}


def read_manifest():
    with MANIFEST.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def validator_fields(validator, mutant_id):
    if mutant_id in detected_by[validator]:
        return failure_details[validator][mutant_id]
    return ("Passed/no automated failure", "None", "0", "Missed")


def pct(n, d):
    return "" if d == 0 else round(n / d, 4)


def build_rows():
    manifest = read_manifest()
    generated = {(r["golden_id"], r["mutation_id"]): r for r in manifest}
    rows = []
    for golden in ["G01", "G02", "G03", "G04", "G05"]:
        for mutation in ["M01", "M02", "M03", "M04", "M05"]:
            key = (golden, mutation)
            if key in generated:
                r = generated[key]
                mutant_id = r["mutant_id"]
                row = {
                    "golden_id": golden,
                    "mutation_id": mutation,
                    "mutant_id": mutant_id,
                    "generated": "Yes",
                    "mutation_operator": operator_names[mutation],
                    "short_mutation_description": r["short_mutation_description"],
                    "expected_accessibility_effect": r["expected_accessibility_effect"],
                    "independent_mutation_verification": "Verified programmatically",
                    "visual_preservation": "No visual difference detected",
                    "PAC_result": None,
                    "PAC_failed_checkpoint": None,
                    "PAC_failure_count": None,
                    "PAC_detection": None,
                    "Acrobat_result": None,
                    "Acrobat_failed_rule": None,
                    "Acrobat_failure_count": None,
                    "Acrobat_detection": None,
                    "veraPDF_result": None,
                    "veraPDF_failed_rule": None,
                    "veraPDF_failure_count": None,
                    "veraPDF_detection": None,
                    "all_three_agree": None,
                    "agreement_pattern": None,
                    "interpretation_note": "",
                }
                for validator, prefix, rule_col in [
                    ("PAC", "PAC", "failed_checkpoint"),
                    ("Acrobat", "Acrobat", "failed_rule"),
                    ("veraPDF", "veraPDF", "failed_rule"),
                ]:
                    result, rule, count, detection = validator_fields(validator, mutant_id)
                    row[f"{prefix}_result"] = result
                    row[f"{prefix}_{rule_col}"] = rule
                    row[f"{prefix}_failure_count"] = count
                    row[f"{prefix}_detection"] = detection
                detections = [row["PAC_detection"], row["Acrobat_detection"], row["veraPDF_detection"]]
                row["all_three_agree"] = "Yes" if len(set(detections)) == 1 else "No"
                row["agreement_pattern"] = "/".join(detections)
                if mutant_id == "G02_M04":
                    row["interpretation_note"] = "Only validator disagreement case: PAC missed; Acrobat and veraPDF detected list-structure failures."
                elif row["PAC_detection"] == row["Acrobat_detection"] == row["veraPDF_detection"] == "Missed":
                    row["interpretation_note"] = "Survived all automated validators despite independent mutation verification."
                elif row["PAC_detection"] == row["Acrobat_detection"] == row["veraPDF_detection"] == "Detected":
                    row["interpretation_note"] = "Detected consistently by all three validators."
                rows.append(row)
            else:
                rows.append({
                    "golden_id": golden,
                    "mutation_id": mutation,
                    "mutant_id": f"{golden}_{mutation}",
                    "generated": "No",
                    "mutation_operator": operator_names[mutation],
                    "short_mutation_description": non_generated.get(key, "Not generated."),
                    "expected_accessibility_effect": "N/A",
                    "independent_mutation_verification": "N/A",
                    "visual_preservation": "N/A",
                    "PAC_result": "N/A",
                    "PAC_failed_checkpoint": "N/A",
                    "PAC_failure_count": "N/A",
                    "PAC_detection": "N/A",
                    "Acrobat_result": "N/A",
                    "Acrobat_failed_rule": "N/A",
                    "Acrobat_failure_count": "N/A",
                    "Acrobat_detection": "N/A",
                    "veraPDF_result": "N/A",
                    "veraPDF_failed_rule": "N/A",
                    "veraPDF_failure_count": "N/A",
                    "veraPDF_detection": "N/A",
                    "all_three_agree": "N/A",
                    "agreement_pattern": "N/A",
                    "interpretation_note": non_generated.get(key, "Not generated."),
                })
    return rows


def rates(rows):
    generated = [r for r in rows if r["generated"] == "Yes"]
    validators = ["PAC", "Acrobat", "veraPDF"]
    overall = []
    for v in validators:
        n = sum(1 for r in generated if r[f"{v}_detection"] == "Detected")
        d = len(generated)
        overall.append({"validator": v, "detected": n, "total_generated_verified": d, "missed": d - n, "detection_rate": pct(n, d)})

    per_operator = []
    for mutation in ["M01", "M02", "M03", "M04", "M05"]:
        subset = [r for r in generated if r["mutation_id"] == mutation]
        for v in validators:
            n = sum(1 for r in subset if r[f"{v}_detection"] == "Detected")
            d = len(subset)
            per_operator.append({
                "mutation_id": mutation,
                "mutation_operator": operator_names[mutation],
                "validator": v,
                "detected": n,
                "total_generated_verified": d,
                "missed": d - n,
                "detection_rate": pct(n, d),
            })
    return overall, per_operator


def agreement(rows):
    generated = [r for r in rows if r["generated"] == "Yes"]
    validators = ["PAC", "Acrobat", "veraPDF"]
    pairs = []
    for a, b in [("PAC", "Acrobat"), ("PAC", "veraPDF"), ("Acrobat", "veraPDF")]:
        same = sum(1 for r in generated if r[f"{a}_detection"] == r[f"{b}_detection"])
        both_detect = sum(1 for r in generated if r[f"{a}_detection"] == r[f"{b}_detection"] == "Detected")
        both_miss = sum(1 for r in generated if r[f"{a}_detection"] == r[f"{b}_detection"] == "Missed")
        disagree = len(generated) - same
        pairs.append({
            "validator_pair": f"{a} vs {b}",
            "agree": same,
            "disagree": disagree,
            "total": len(generated),
            "agreement_rate": pct(same, len(generated)),
            "both_detected": both_detect,
            "both_missed": both_miss,
            "disagreement_cases": "; ".join(r["mutant_id"] for r in generated if r[f"{a}_detection"] != r[f"{b}_detection"]) or "None",
        })
    patterns = Counter(r["agreement_pattern"] for r in generated)
    return pairs, [{"pattern": k, "count": v, "share": pct(v, len(generated))} for k, v in sorted(patterns.items())]


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path, rows, overall, per_operator, pairwise, patterns):
    generated = [r for r in rows if r["generated"] == "Yes"]
    lines = []
    lines.append("# PDFa11yMut Experimental Detection Analysis")
    lines.append("")
    lines.append("## Scope And Provenance")
    lines.append("")
    lines.append("- Corpus scope: 5 golden PDFs, 23 generated and independently verified mutants, 2 non-generated/N/A cases.")
    lines.append("- Mutation verification is independent from validator detection: every generated mutant was programmatically confirmed as generated, parseable, page-count preserving, mutation-verified, and visually unchanged for the checked visual-difference signal.")
    lines.append("- PAC evidence is from the recorded PAC run in the prior research conversation: all goldens passed; G01/G02/G03/G04-M03 failed Structure Elements; all other generated mutants passed.")
    lines.append("- Acrobat evidence is from the recorded Acrobat Accessibility Checker report/results in the prior research conversation: all five goldens had 29 passed, 0 failed, 2 manual checks, and 1 skipped; G01/G02/G03/G04-M03 and G02-M04 had automated failures; all other generated mutants had 0 automated failures.")
    lines.append("- veraPDF evidence is from `vera_evaluation.docx`: veraPDF 1.30.2, GreenField parser, PDF/UA-1 validation profile with 106 rules; all five goldens passed.")
    lines.append("")
    lines.append("Important interpretation rule: a validator `Missed` result means no relevant automated failure was reported for a mutant whose intended defect was independently verified. It does not mean the PDF is accessible, and it does not measure full checker accuracy.")
    lines.append("")
    lines.append("## Overall Detection Rates")
    lines.append("")
    lines.append("| Validator | Detected | Missed | Total generated/verified | Detection rate |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in overall:
        lines.append(f"| {r['validator']} | {r['detected']} | {r['missed']} | {r['total_generated_verified']} | {r['detection_rate']:.1%} |")
    lines.append("")
    lines.append("## Per-Operator Detection Rates")
    lines.append("")
    lines.append("| Mutation | Operator | Validator | Detected | Total | Detection rate |")
    lines.append("|---|---|---|---:|---:|---:|")
    for r in per_operator:
        lines.append(f"| {r['mutation_id']} | {r['mutation_operator']} | {r['validator']} | {r['detected']} | {r['total_generated_verified']} | {r['detection_rate']:.1%} |")
    lines.append("")
    lines.append("## Validator Agreement")
    lines.append("")
    lines.append("| Validator pair | Agree | Disagree | Total | Agreement rate | Disagreement cases |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for r in pairwise:
        lines.append(f"| {r['validator_pair']} | {r['agree']} | {r['disagree']} | {r['total']} | {r['agreement_rate']:.1%} | {r['disagreement_cases']} |")
    lines.append("")
    lines.append("| Three-validator pattern | Count | Share |")
    lines.append("|---|---:|---:|")
    for r in patterns:
        lines.append(f"| {r['pattern']} | {r['count']} | {r['share']:.1%} |")
    lines.append("")
    lines.append("## Final Detection Matrix")
    lines.append("")
    lines.append("| Mutant | Operator | PAC | Acrobat | veraPDF | Note |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['mutant_id']} | {r['mutation_id']} | {r['PAC_detection']} | {r['Acrobat_detection']} | {r['veraPDF_detection']} | {r['interpretation_note']} |")
    lines.append("")
    lines.append("## Defensible Research Questions")
    lines.append("")
    lines.append("RQ1. To what extent do automated PDF accessibility validators detect independently verified structure-only accessibility mutations in otherwise validator-clean PDF/UA-oriented documents?")
    lines.append("")
    lines.append("RQ2. Are detection outcomes concentrated in particular mutation operators, such as heading-hierarchy violations, rather than distributed evenly across reading-order, omission, list/table association, and MCID-order defects?")
    lines.append("")
    lines.append("RQ3. How much do commonly used validators agree or disagree on the same controlled PDF accessibility mutants, and which mutation cases explain disagreement?")
    lines.append("")
    lines.append("RQ4. What does mutation-based evaluation reveal about the boundary between machine-checkable conformance failures and verified accessibility-relevant defects that survive automated checking?")
    lines.append("")
    lines.append("## Results And Discussion Findings")
    lines.append("")
    lines.append("1. The golden baseline is clean for the three evaluated validators. This supports attributing later automated failures to the injected mutations rather than to pre-existing baseline defects.")
    lines.append("")
    lines.append("2. Detection is highly operator-specific. All three validators detected every generated M03 heading-hierarchy mutant (4/4). None detected M01, M02, or M05. For M04, Acrobat and veraPDF detected only G02-M04, while PAC detected none.")
    lines.append("")
    lines.append("3. Overall automated detection is limited for this controlled mutant set: PAC detected 4/23 (17.4%), while Acrobat and veraPDF each detected 5/23 (21.7%). These are mutation-detection rates for this benchmark, not general accessibility accuracy rates.")
    lines.append("")
    lines.append("4. Acrobat and veraPDF agreed on every generated mutant at the detected/missed level. PAC agreed with them on 22/23 mutants and differed only on G02-M04.")
    lines.append("")
    lines.append("5. G02-M04 is the strongest cross-validator disagreement case. The mutation was independently verified as a marked-content association swap in a list; Acrobat reported two list failures, veraPDF reported four ISO 14289-1 Clause 7.2 list failures, and PAC reported no automated failure.")
    lines.append("")
    lines.append("6. Surviving mutants should not be described as false negatives unless the paper carefully defines the target property. A safer phrasing is that these verified mutants survived the validators' automated checks under the tested settings.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    rows = build_rows()
    generated_rows = [r for r in rows if r["generated"] == "Yes"]
    overall, per_operator = rates(rows)
    pairwise, patterns = agreement(rows)
    write_csv(OUT / "pdfa11ymut_detection_matrix.csv", rows)
    write_csv(OUT / "pdfa11ymut_overall_rates.csv", overall)
    write_csv(OUT / "pdfa11ymut_per_operator_rates.csv", per_operator)
    write_csv(OUT / "pdfa11ymut_validator_agreement.csv", pairwise)
    write_markdown(OUT / "pdfa11ymut_analysis.md", rows, overall, per_operator, pairwise, patterns)
    (OUT / "pdfa11ymut_detection_analysis_data.json").write_text(json.dumps({
        "matrix": rows,
        "overall": overall,
        "per_operator": per_operator,
        "pairwise_agreement": pairwise,
        "patterns": patterns,
    }, indent=2), encoding="utf-8")
    summary = {
        "generated_verified_mutants": len(generated_rows),
        "non_generated_cases": len(rows) - len(generated_rows),
        "overall": overall,
        "pairwise_agreement": pairwise,
        "patterns": patterns,
    }
    (OUT / "pdfa11ymut_metrics_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
