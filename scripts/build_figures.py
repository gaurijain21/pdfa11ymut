from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis" / "generated" / "figures"


def svg(title: str, body: str, desc: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320" viewBox="0 0 900 320" role="img"><title>{title}</title><desc>{desc}</desc><rect width="900" height="320" fill="white"/><text x="40" y="52" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="#1f2937">{title}</text>{body}</svg>'''


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rates_path = ROOT / "analysis" / "generated" / "overall_rates.csv"
    rows = []
    if rates_path.exists():
        with rates_path.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    has_classified_rows = any(int(r.get("total_with_classification", "0") or 0) > 0 for r in rows if r.get("total_with_classification", "").isdigit())
    if not rows or "validator" not in rows[0] or not has_classified_rows:
        body = '<text x="40" y="130" font-family="Arial,sans-serif" font-size="20" fill="#92400e">Evidence pending</text><text x="40" y="170" font-family="Arial,sans-serif" font-size="15" fill="#4b5563">No supported validator outcomes are available in the canonical dataset.</text>'
        desc = "Current analysis has no canonical classified validator outcomes; no rate comparison is drawn."
    else:
        body_parts = []
        for index, row in enumerate(rows):
            x = 60 + index * 260
            label = row["validator"]
            rate = float(row["rate"] or 0) * 100
            height = rate * 1.7
            body_parts.append(f'<rect x="{x}" y="270" width="120" height="{height:.2f}" fill="#2f5d7c"/><text x="{x + 60}" y="295" text-anchor="middle" font-family="Arial,sans-serif" font-size="15">{label}</text><text x="{x + 60}" y="{260-height:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="14">{rate:.1f}%</text>')
        body = "".join(body_parts)
        desc = "Rates are calculated from canonical validator runs only."
    (OUT / "active_outcomes.svg").write_text(svg("PDFa11yMut active outcomes", body, desc), encoding="utf-8")
    print(OUT / "active_outcomes.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
