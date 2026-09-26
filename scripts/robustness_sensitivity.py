"""Print uncertainty summaries for the frozen mutant detection matrix.

Intervals are descriptive: Wilson intervals treat rows as binomial cases;
the source-cluster bootstrap resamples golden PDFs, not individual mutants.
Neither changes the primary classification or implies general validator
accuracy.
"""
from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "analysis" / "generated" / "formal_results_freeze.csv"
VALIDATORS = ("PAC", "Acrobat", "veraPDF")


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return (float("nan"), float("nan"))
    p = successes / total
    den = 1 + z * z / total
    center = (p + z * z / (2 * total)) / den
    half = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / den
    return center - half, center + half


def pct_interval(values: list[float]) -> tuple[float, float]:
    ordered = sorted(values)
    if not ordered:
        return (float("nan"), float("nan"))
    def quantile(q: float) -> float:
        position = (len(ordered) - 1) * q
        lo = int(position)
        hi = min(lo + 1, len(ordered) - 1)
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)
    return quantile(0.025), quantile(0.975)


def cluster_bootstrap(rows: list[dict[str, str]], validator: str, replicates: int, seed: int) -> tuple[float, float]:
    by_source: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        if row["validator"] != validator:
            continue
        by_source[row["golden_id"]].append(int(row["outcome"] == "detected"))
    sources = sorted(by_source)
    if not sources:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    samples: list[float] = []
    for _ in range(replicates):
        draw = [rng.choice(sources) for _ in sources]
        outcomes = [v for source in draw for v in by_source[source]]
        if outcomes:
            samples.append(sum(outcomes) / len(outcomes))
    return pct_interval(samples)


def fmt(value: float) -> str:
    return "NA" if value != value else f"{value:.3f}"


def fmt_interval(low: float, high: float) -> str:
    if low != low or high != high:
        return "NA"
    return f"{low:.3f}-{high:.3f}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--replicates", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260922)
    args = parser.parse_args()
    with args.input.open(newline="", encoding="utf-8-sig") as handle:
        raw_rows = list(csv.DictReader(handle))
    raw_scope = [r for r in raw_rows if r["baseline_status"] == "BASELINE_PASS"]
    rows = [
        {"golden_id": r["source_golden"], "mutation_id": r["operator"], "operator_class": r["operator_class"], "validator": r["validator"], "outcome": r["detection_classification"].strip().lower()}
        for r in raw_scope
        if r["baseline_status"] == "BASELINE_PASS"
        and r["detection_classification"].strip().lower() in {"detected", "missed"}
        and r["ambiguous_or_confounded"].strip().upper() != "TRUE"
    ]
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["operator_class"]].append(row)
    for row in rows:
        groups[row["mutation_id"]].append(row)
    print("Machine-checkable rows are eligible for descriptive detection-sensitivity intervals; semantic rows are descriptive only, not validator misses.")
    print("Wilson 95% interval is row-level; cluster-bootstrap 95% interval resamples source PDFs.")
    print("Operator intervals are exploratory when source counts or denominators are small.\n")
    print("| Class/operator | Validator | Detected / n | Not rate-coded | Sources | Rate | Wilson 95% | Source-cluster bootstrap 95% |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for label, subset in groups.items():
        for index, validator in enumerate(VALIDATORS):
            eligible = [r for r in subset if r["validator"] == validator]
            n = len(eligible)
            detected = sum(r["outcome"] == "detected" for r in eligible)
            not_coded = sum(1 for r in raw_scope if (r["operator_class"] == label or r["operator"] == label) and r["validator"] == validator) - n
            lo, hi = wilson(detected, n)
            eligible_for_sensitivity = label == "machine-checkable" or label.startswith("M") and subset[0]["operator_class"] == "machine-checkable"
            if eligible_for_sensitivity:
                blo, bhi = cluster_bootstrap(subset, validator, args.replicates, args.seed + index)
            else:
                # Semantic rows are intentionally descriptive rather than
                # rate-coded; expose that full count instead of implying a
                # zero-denominator sensitivity estimate.
                not_coded = n
                lo, hi, blo, bhi = (float("nan"),) * 4
            sources = len({r["golden_id"] for r in eligible})
            print(f"| {label} | {validator} | {detected}/{n} | {not_coded} | {sources} | {fmt(detected/n if n and eligible_for_sensitivity else float('nan'))} | {fmt_interval(lo, hi)} | {fmt_interval(blo, bhi)} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
