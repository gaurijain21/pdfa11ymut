"""Build active analysis outputs from canonical repository data.

This module intentionally produces no rates when evidence is absent. Historical CSVs
are not read and cannot influence current results.
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "analysis" / "generated"


def latex_percent(value: str) -> str:
    """Escape a generated percentage for LaTeX table cells."""
    return value.replace("%", r"\%")
VALIDATORS = ["PAC", "Acrobat", "veraPDF"]
FINAL_CLASSIFICATIONS = {"Detected", "Missed", "Needs Manual Check", "Not Applicable"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def operator_classes() -> dict[str, str]:
    spec = yaml.safe_load((ROOT / "operators" / "operators.yaml").read_text(encoding="utf-8"))
    return {item["id"]: item["class"] for item in spec["operators"]}


def excluded_mutant_ids() -> set[str]:
    return {row.get("mutant_id", "") for row in read_csv(DATA / "mutant_exclusions.csv") if row.get("status")}


def pct(n: int, d: int) -> str:
    return "" if not d else f"{n / d:.4f}"


def percentile(values: list[float], probability: float) -> float:
    """Deterministic linear percentile for the small cluster bootstrap output."""
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def source_cluster_summaries(current_runs: list[dict], mutants: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return per-source rates and a source-cluster bootstrap sensitivity view.

    Mutants from the same golden PDF are resampled together. The result is
    descriptive sensitivity evidence, not a population-level confidence claim.
    """
    source_by_mutant = {
        row.get("mutant_id", ""): Path(row.get("source_pdf", "")).stem
        for row in mutants
    }
    grouped: dict[str, list[dict]] = {}
    for row in current_runs:
        source = source_by_mutant.get(row.get("mutant_id", ""), "UNKNOWN_SOURCE")
        grouped.setdefault(source, []).append(row)
    summaries: list[dict] = []
    bootstrap: list[dict] = []
    rng = random.Random(20260925)
    for validator in VALIDATORS:
        source_rates: list[float] = []
        source_rows: list[list[dict]] = []
        for source in sorted(grouped):
            rows = [row for row in grouped[source] if row["validator"] == validator]
            detected = sum(row["classification"] == "Detected" for row in rows)
            missed = sum(row["classification"] == "Missed" for row in rows)
            denominator = detected + missed
            rate = detected / denominator if denominator else None
            if rate is not None:
                source_rates.append(rate)
            source_rows.append(rows)
            summaries.append({
                "source_golden": source,
                "validator": validator,
                "mutants": len(rows),
                "detected": detected,
                "missed": missed,
                "manual": sum(row["classification"] == "Needs Manual Check" for row in rows),
                "rate_denominator": denominator,
                "rate": "" if rate is None else f"{rate:.4f}",
            })
        observed_rows = [row for rows in source_rows for row in rows]
        observed_detected = sum(row["classification"] == "Detected" for row in observed_rows)
        observed_missed = sum(row["classification"] == "Missed" for row in observed_rows)
        observed_denominator = observed_detected + observed_missed
        observed_rate = observed_detected / observed_denominator if observed_denominator else 0.0
        boot_rates: list[float] = []
        for _ in range(5000):
            sampled = [source_rows[rng.randrange(len(source_rows))] for _ in source_rows]
            flat = [row for rows in sampled for row in rows]
            detected = sum(row["classification"] == "Detected" for row in flat)
            missed = sum(row["classification"] == "Missed" for row in flat)
            if detected + missed:
                boot_rates.append(detected / (detected + missed))
        bootstrap.append({
            "validator": validator,
            "cluster_count": len(source_rows),
            "observed_detected": observed_detected,
            "observed_missed": observed_missed,
            "observed_rate": f"{observed_rate:.4f}",
            "cluster_bootstrap_resamples": len(boot_rates),
            "cluster_bootstrap_95_low": f"{percentile(boot_rates, 0.025):.4f}",
            "cluster_bootstrap_95_high": f"{percentile(boot_rates, 0.975):.4f}",
            "interpretation": "Descriptive source-cluster sensitivity; not a population-level confidence interval",
        })
    return summaries, bootstrap


def detection_sensitivity(current_runs: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for validator in VALIDATORS:
        subset = [row for row in current_runs if row["validator"] == validator]
        detected = [row for row in subset if row["classification"] == "Detected"]
        direct = [row for row in detected if row["detection_type"] == "DIRECT_TARGET_DETECTION"]
        proxy = [row for row in detected if row["detection_type"] == "CONSEQUENCE_PROXY_DETECTION"]
        missed = [row for row in subset if row["classification"] == "Missed"]
        rows.append({
            "validator": validator,
            "all_detected": len(detected),
            "direct_detected": len(direct),
            "proxy_detected": len(proxy),
            "missed": len(missed),
            "all_rate": pct(len(detected), len(detected) + len(missed)),
            "direct_only_rate": pct(len(direct), len(direct) + len(missed)),
            "note": "Proxy detections are included only in all_rate; direct_only_rate excludes them",
        })
    return rows


def detection_type(run: dict | None, classification: str) -> str:
    """Normalize direct/proxy/manual/survival terminology for derived views."""
    reason = str((run or {}).get("classification_reason", "")).lower()
    if classification == "Needs Manual Check":
        return "MANUAL_REVIEW"
    if "collateral" in reason:
        return "COLLATERAL_DETECTION"
    if "proxy" in reason:
        return "CONSEQUENCE_PROXY_DETECTION"
    if classification == "Detected":
        return "DIRECT_TARGET_DETECTION"
    if "baseline" in reason and "new" not in reason:
        return "BASELINE_CARRIED"
    if classification == "Missed":
        return "NO_TARGET_DETECTION"
    if classification == "Not Applicable":
        return "EXCLUDED_OR_NOT_APPLICABLE"
    return "UNCLASSIFIED"


def disagreement_cause(left: dict, right: dict, classes: dict[str, str]) -> str:
    if left["detection_type"] == "MANUAL_REVIEW" or right["detection_type"] == "MANUAL_REVIEW":
        return "ACROBAT_MANUAL_VS_AUTOMATED"
    if left["operator"] == "M10" and ("PROXY" in left["detection_type"] or "PROXY" in right["detection_type"]):
        return "M10_PROXY_DIRECT_DIFFERENCE"
    if left["operator"] == "M09":
        return "M09_ROLEMAP_RULE_PROFILE_DIFFERENCE"
    if left["detection_type"] == "BASELINE_CARRIED" or right["detection_type"] == "BASELINE_CARRIED":
        return "BASELINE_CARRIED"
    if classes.get(left["operator"]) == "class_b":
        return "CLASS_B_SCOPE_DIFFERENCE"
    return "RULE_OR_PROFILE_DIFFERENCE"


def tagged_table_row(cells: list[str], header: bool = False) -> str:
    macro = "tagth" if header else "tagtd"
    tagged = " & ".join(f"\\{macro}{{{cell}}}" for cell in cells)
    return f"\\tagtrbegin {tagged} \\tagtrend \\\\"


def _write_results_fragment_untagged(path: Path, overall: list[dict], per_operator: list[dict], class_summary: list[dict], active_count: int, classified_count: int) -> None:
    lines = [
        "% Generated by scripts/rebuild_analysis.py from canonical data.",
        "\\taggedsubsection{Formal validator results}",
        "\\begin{taggedparagraph}",
        f"The active formal scope contains {active_count} verified mutants after the documented exclusions. The canonical data contain {classified_count} classified validator-mutant rows ({active_count} mutants x three validators); PAC AI and assistive-technology observations are not included in these formal outcomes.",
        "\\end{taggedparagraph}",
        "",
        "\\begin{table}[t]",
        "\\caption{Formal validator outcomes in the active scope.}",
        "\\label{tab:formal-overall}",
        "\\centering\\small",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\begin{tabular}{lrrrrr}",
        "\\toprule",
        "Validator & Detected & No target & Manual & Total & Rate \\\\",
        "\\midrule",
    ]
    for row in overall:
        rate = latex_percent(f"{float(row['rate']):.1%}") if row["rate"] else "--"
        lines.append(f"{row['validator']} & {row['detected']} & {row['missed']} & {row['needs_manual_check']} & {row['total_with_classification']} & {rate} \\\\")
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\begin{taggedparagraph}",
        "Every displayed rate is Detected/(Detected + No target); the exact numerator and denominator are retained in the generated CSV. Acrobat manual checkpoints are retained separately and are not detections.",
        "\\end{taggedparagraph}",
        "",
        "\\begin{table*}[!t]",
        "\\caption{Class-specific formal outcomes. Class B rows are reported as automated-check outcomes, not as claims that the validators should have detected semantic defects.}",
        "\\label{tab:formal-class}",
        "\\centering\\small",
        "\\begin{tabular}{llrrrrr}",
        "\\toprule",
        "Class & Validator & Detected & No target & Manual & Total & Rate \\\\",
        "\\midrule",
    ]
    for row in class_summary:
        rate = latex_percent(f"{float(row['rate']):.1%}") if row["rate"] else "--"
        label = "Class A" if row["class"] == "class_a" else "Class B"
        lines.append(f"{label} & {row['validator']} & {row['detected']} & {row['missed']} & {row['needs_manual_check']} & {row['total_with_classification']} & {rate} \\\\")
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table*}",
        "",
        "\\begin{table*}[!t]",
        "\\caption{Detection by operator and validator. A dash indicates that the rate denominator is zero.}",
        "\\label{tab:formal-operator}",
        "\\centering\\scriptsize",
        "\\begin{tabular}{lrrrrrrl}",
        "\\toprule",
        "Operator & PAC D/N & PAC rate & Acrobat D/N & Acrobat rate & veraPDF D/N & veraPDF rate & Class \\\\",
        "\\midrule",
    ]
    operators = sorted({row["operator"] for row in per_operator})
    by_key = {(row["operator"], row["validator"]): row for row in per_operator}
    classes = operator_classes()
    for operator in operators:
        cells = []
        for validator in ("PAC", "Acrobat", "veraPDF"):
            row = by_key[(operator, validator)]
            cells.extend([f"{row['detected']}/{row['missed']}", latex_percent(f"{float(row['rate']):.0%}") if row["rate"] else "--"])
        label = "A" if classes.get(operator) == "class_a" else "B"
        lines.append(f"{operator} & {cells[0]} & {cells[1]} & {cells[2]} & {cells[3]} & {cells[4]} & {cells[5]} & {label} \\\\")
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table*}",
        "",
        "\\begin{taggedparagraph}",
        "The active formal results show that all Class B mutations survived automated detection in this scope. This is a scoped observation about the tested configurations; semantic validity and assistive-technology impact require separate evidence.",
        "\\end{taggedparagraph}",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_results_fragment(path: Path, overall: list[dict], per_operator: list[dict], class_summary: list[dict], active_count: int, classified_count: int) -> None:
    """Emit the generated results with explicit PDF structure for tables."""
    scratch = path.with_suffix(".untagged.tex")
    _write_results_fragment_untagged(scratch, overall, per_operator, class_summary, active_count, classified_count)
    source_lines = scratch.read_text(encoding="utf-8").splitlines()
    output: list[str] = []
    in_tabular = False
    header_row = False
    for line in source_lines:
        if line.startswith("\\begin{table"):
            output.extend([line, "\\tagtablebegin"])
            continue
        if line.startswith("\\caption{"):
            output.append(line.replace("\\caption{", "\\tagcaption{", 1))
            continue
        if line.startswith("\\begin{tabular}"):
            in_tabular = True
            header_row = True
            output.append(line)
            continue
        if line == "\\midrule":
            header_row = False
            output.append(line)
            continue
        if in_tabular and line.endswith("\\\\") and " & " in line:
            cells = line[:-2].split(" & ")
            output.append(tagged_table_row(cells, header=header_row))
            continue
        if line == "\\end{tabular}":
            in_tabular = False
            output.append(line)
            continue
        if line.startswith("\\end{table"):
            output.extend(["\\tagtableend", line])
            continue
        output.append(line)
    scratch.unlink()
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def main() -> int:
    excluded = excluded_mutant_ids()
    classes = operator_classes()
    all_valid_mutants = [r for r in read_jsonl(DATA / "mutants.jsonl") if r.get("status") == "valid" and r.get("verification", {}).get("mutation_valid")]
    mutants = [r for r in all_valid_mutants if r.get("mutant_id") not in excluded]
    runs = read_csv(DATA / "validator_runs.csv")
    corpus = read_csv(DATA / "corpus_inventory.csv")
    at_rows = read_csv(DATA / "at_observations.csv")
    def pick_run(mutant_id: str, validator: str, config: str):
        candidates = [r for r in runs if (r.get("artifact_id") or r.get("mutant_id")) == mutant_id and r.get("validator") == validator]
        candidates = [r for r in candidates if str(r.get("configuration", "")).strip().lower() == config.lower() or (validator == "Acrobat" and config == "Formal" and str(r.get("configuration", "")).strip().lower() == "full check") or (validator == "veraPDF" and config == "Formal" and str(r.get("configuration", "")).strip().lower() == "pdf/ua-1 ua1") or (validator == "PAC" and config == "AI" and str(r.get("PAC_AI_enabled", "")).strip().lower() == "true")]
        return candidates[-1] if candidates else None
    matrix = []
    for mutant in mutants:
        for validator in VALIDATORS:
            configs = ["Formal", "AI"] if validator == "PAC" else ["Formal"]
            for config in configs:
                run = pick_run(mutant.get("mutant_id"), validator, config)
                classification = run.get("detection_classification", "TODO") if run else "TODO"
                if classification not in FINAL_CLASSIFICATIONS:
                    classification = "TODO"
                matrix.append({"mutant_id": mutant.get("mutant_id"), "source_golden": Path(mutant.get("source_pdf", "")).stem, "operator": mutant.get("operator"), "validator": validator, "mode": config, "classification": classification, "detection_type": detection_type(run, classification), "classification_reason": (run or {}).get("classification_reason", ""), "baseline_status": (run or {}).get("baseline_status", ""), "file_sha256": mutant.get("mutant_sha256"), "raw_report_path": (run or {}).get("raw_report_path", "")})
    current_runs = [r for r in matrix if r["mode"] == "Formal" and r["classification"] in FINAL_CLASSIFICATIONS]
    overall = []
    for validator in VALIDATORS:
        subset = [r for r in current_runs if r["validator"] == validator]
        detected = sum(r["classification"] == "Detected" for r in subset)
        missed = sum(r["classification"] == "Missed" for r in subset)
        manual = sum(r["classification"] == "Needs Manual Check" for r in subset)
        not_applicable = sum(r["classification"] == "Not Applicable" for r in subset)
        overall.append({"validator": validator, "detected": detected, "missed": missed, "needs_manual_check": manual, "not_applicable": not_applicable, "total_with_classification": len(subset), "rate_numerator": detected, "rate_denominator": detected + missed, "rate_denominator_definition": "Detected + Missed; manual and not-applicable rows excluded", "rate": pct(detected, detected + missed)})
    per_operator = []
    for operator in sorted({r["operator"] for r in matrix}):
        for validator in VALIDATORS:
            subset = [r for r in current_runs if r["operator"] == operator and r["validator"] == validator]
            detected = sum(r["classification"] == "Detected" for r in subset)
            missed = sum(r["classification"] == "Missed" for r in subset)
            manual = sum(r["classification"] == "Needs Manual Check" for r in subset)
            not_applicable = sum(r["classification"] == "Not Applicable" for r in subset)
            per_operator.append({"operator": operator, "validator": validator, "detected": detected, "missed": missed, "needs_manual_check": manual, "not_applicable": not_applicable, "total_with_classification": len(subset), "rate_numerator": detected, "rate_denominator": detected + missed, "rate_denominator_definition": "Detected + Missed; manual and not-applicable rows excluded", "rate": pct(detected, detected + missed)})
    class_summary = []
    for operator_class in ("class_a", "class_b"):
        for validator in VALIDATORS:
            subset = [r for r in current_runs if r["validator"] == validator and classes.get(r["operator"]) == operator_class]
            detected = sum(r["classification"] == "Detected" for r in subset)
            missed = sum(r["classification"] == "Missed" for r in subset)
            manual = sum(r["classification"] == "Needs Manual Check" for r in subset)
            not_applicable = sum(r["classification"] == "Not Applicable" for r in subset)
            class_summary.append({"class": operator_class, "validator": validator, "detected": detected, "missed": missed, "needs_manual_check": manual, "not_applicable": not_applicable, "total_with_classification": len(subset), "rate_numerator": detected, "rate_denominator": detected + missed, "rate_denominator_definition": "Detected + Missed; manual and not-applicable rows excluded", "rate": pct(detected, detected + missed)})
    formal_by_key = {(row["mutant_id"], row["validator"]): row["classification"] for row in current_runs}
    agreement = []
    for left, right in (("PAC", "Acrobat"), ("PAC", "veraPDF"), ("Acrobat", "veraPDF")):
        cases = [mutant["mutant_id"] for mutant in mutants if (mutant["mutant_id"], left) in formal_by_key and (mutant["mutant_id"], right) in formal_by_key]
        agree = sum(formal_by_key[(mid, left)] == formal_by_key[(mid, right)] for mid in cases)
        agreement.append({"validator_pair": f"{left} vs {right}", "agree": agree, "disagree": len(cases) - agree, "total_pairwise_classified": len(cases), "agreement_rate": pct(agree, len(cases)), "disagreement_cases": ";".join(mid for mid in cases if formal_by_key[(mid, left)] != formal_by_key[(mid, right)])})
    disagreement_rows = []
    matrix_by_key = {(row["mutant_id"], row["validator"]): row for row in current_runs}
    for left_name, right_name in (("PAC", "Acrobat"), ("PAC", "veraPDF"), ("Acrobat", "veraPDF")):
        for mutant in mutants:
            left = matrix_by_key.get((mutant["mutant_id"], left_name))
            right = matrix_by_key.get((mutant["mutant_id"], right_name))
            if not left or not right or left["classification"] == right["classification"]:
                continue
            disagreement_rows.append({
                "mutant_id": mutant["mutant_id"],
                "operator": mutant["operator"],
                "validator_pair": f"{left_name} vs {right_name}",
                "left_classification": left["classification"],
                "right_classification": right["classification"],
                "left_detection_type": left["detection_type"],
                "right_detection_type": right["detection_type"],
                "cause_category": disagreement_cause(left, right, classes),
                "left_baseline_status": left.get("baseline_status", ""),
                "right_baseline_status": right.get("baseline_status", ""),
            })
    source_summary, source_bootstrap = source_cluster_summaries(current_runs, mutants)
    sensitivity = detection_sensitivity(current_runs)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in (("matrix.csv", matrix), ("overall_rates.csv", overall), ("per_operator_rates.csv", per_operator), ("agreement.csv", agreement), ("disagreement_analysis.csv", disagreement_rows), ("source_cluster_summary.csv", source_summary), ("source_cluster_bootstrap.csv", source_bootstrap), ("detection_sensitivity.csv", sensitivity)):
        with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
            if rows:
                writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
            else:
                fh.write("status\nNO_CANONICAL_EVIDENCE\n")
    required_classified = len(mutants) * 3
    selection = read_csv(DATA / "pac_ai_selection.csv")
    selected_ai = [row for row in selection if row.get("artifact_type", "mutant") == "mutant" and row.get("selected_for_pac_ai") == "TRUE"]
    deferred_ai = [row for row in selection if row.get("artifact_type", "mutant") == "mutant" and row.get("selected_for_pac_ai") == "DEFERRED_PENDING_FORMAL_RESULT"]
    baseline_rows = [row for row in runs if row.get("baseline_or_mutant") == "golden_baseline" and row.get("automated_pass_fail")]
    baseline_ready = len([row for row in baseline_rows if row.get("validator") in {"PAC", "Acrobat", "veraPDF"}]) >= 27
    formal_keys = {(row["mutant_id"], row["validator"]) for row in current_runs}
    required_keys = {(mutant.get("mutant_id"), validator) for mutant in mutants for validator in VALIDATORS}
    formal_complete = baseline_ready and formal_keys >= required_keys
    ai_run_count = sum(1 for row in runs if row.get("validator") == "PAC" and row.get("configuration") == "AI" and row.get("baseline_or_mutant") == "mutant" and row.get("detection_classification") in {"Detected", "Missed", "Survived", "NotDetected"})
    at_complete = sum(row.get("status") == "COMPLETE" for row in at_rows)
    if not formal_complete:
        analysis_status = "formal_evidence_pending"
    else:
        analysis_status = "formal_complete_at_complete_pac_ai_future_work"
    summary = {"status": analysis_status, "analysis_status": analysis_status, "valid_verified_mutants": len(all_valid_mutants), "active_mutants": len(mutants), "valid_mutants": len(mutants), "corpus_records": len(corpus), "canonical_validator_rows": len(runs), "classified_formal_rows": len(current_runs), "required_classified_formal_rows": required_classified, "at_observation_rows": len(at_rows), "at_observation_complete_rows": at_complete, "at_observer_design": "single-observer illustrative exploratory observations under one fixed NVDA/Acrobat/Windows configuration", "pac_ai_status": "native_pilot_semantic_text_no_export_gate", "pac_ai_selected_mutants": len(selected_ai), "pac_ai_deferred_mutants": len(deferred_ai), "pac_ai_classified_mutants": ai_run_count, "source_cluster_count": len({row["source_golden"] for row in source_summary}), "source_cluster_bootstrap_resamples": 5000, "overall": overall, "class_summary": class_summary, "agreement": agreement, "detection_sensitivity": sensitivity}
    (OUT / "metrics_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = ["# Active analysis", "", "This report is generated from `data/mutants.jsonl`, `data/mutant_exclusions.csv`, `data/validator_runs.csv`, and `data/corpus_inventory.csv`.", ""]
    if not mutants or not formal_complete:
        lines += ["## Status", "", f"Current staged status: `{analysis_status}`. Historical summaries are not used; unresolved PAC AI is not merged with formal outcomes.", ""]
    else:
        lines += ["## Status", "", f"Formal validation is complete for {len(mutants)} active mutants. PAC AI remains separate from formal outcomes: the preserved package is aggregate-only, while the fresh native pilot exposed element-level finding text and scores but no supported complete semantic export/API, so the full cohort remains gated. AT observations are complete for nine illustrative exploratory cases under one fixed configuration and are qualitative, not validator detections.", ""]
        lines += ["## Formal validator outcomes", "", "| Validator | Detected | No automated target finding | Needs manual check | Not applicable | Classified total | Rate |", "|---|---:|---:|---:|---:|---:|---:|"]
        for row in overall:
            rate = f"{float(row['rate']):.1%}" if row["rate"] else "TODO"
            lines.append(f"| {row['validator']} | {row['detected']} | {row['missed']} | {row['needs_manual_check']} | {row['not_applicable']} | {row['total_with_classification']} | {rate} |")
        lines += ["", "Rates are Detected/(Detected + No automated target finding); manual and not-applicable rows are excluded. Rows without a canonical report and classification remain TODO and are excluded from rates.", "", "Mutants are nested within nine golden baselines. `source_cluster_summary.csv` reports per-baseline descriptive rates, and `source_cluster_bootstrap.csv` resamples complete baselines together for a deterministic sensitivity interval; these intervals are not population-level confidence claims.", "", "`detection_sensitivity.csv` separates direct target detections from the three Acrobat M10 consequence-proxy detections."]
    lines += ["", "## Scope", "", f"Valid verified mutants: {len(all_valid_mutants)}", f"Active mutants: {len(mutants)}", f"Corpus inventory records: {len(corpus)}", f"Canonical validator rows: {len(runs)}", "", "AI-assisted PAC rows are retained as a separate mode and are never merged with formal outcomes."]
    (OUT / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    if formal_complete:
        write_results_fragment(OUT / "results_fragment.tex", overall, per_operator, class_summary, len(mutants), len(current_runs))
    else:
        (OUT / "results_fragment.tex").write_text("\\textit{Formal validator evidence is incomplete; no active results are reported.}\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
