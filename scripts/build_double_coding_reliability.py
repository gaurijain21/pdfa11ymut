"""Derive transparent pre-adjudication reliability from preserved coder fields."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "double_coding_decisions.csv"
OUTPUT = ROOT / "data" / "double_coding_reliability.csv"


def main() -> int:
    with SOURCE.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    labels_1 = [row["coder_1_decision"] for row in rows]
    labels_2 = [row["coder_2_decision"] for row in rows]
    n = len(rows)
    agreement = sum(a == b for a, b in zip(labels_1, labels_2))
    observed = agreement / n if n else 0.0
    c1, c2 = Counter(labels_1), Counter(labels_2)
    expected = sum((c1[label] / n) * (c2[label] / n) for label in set(c1) | set(c2)) if n else 0.0
    kappa = (observed - expected) / (1 - expected) if n and expected != 1 else 1.0
    out = [
        {"scope": "active formal rows", "n": n, "raw_agreement_count": agreement, "raw_agreement": f"{observed:.6f}", "cohen_kappa": f"{kappa:.6f}", "interpretation": "Pre-adjudication agreement between the two recorded coder decision fields; coder identity/independence provenance is not independently substantiated by this repository."},
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    print(out[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
