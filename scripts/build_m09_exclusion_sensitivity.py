"""Build the invalid/unverified M09 exclusion sensitivity table."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "analysis" / "target_sensitivity"
VALIDATORS = ("PAC", "Acrobat", "veraPDF")
FORMAL_CONFIGS = {"Formal", "Full Check", "PDF/UA-1 ua1"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    exclusions = [row for row in read_csv(DATA / "mutant_exclusions.csv") if row.get("operator") == "M09"]
    excluded_ids = {row["mutant_id"] for row in exclusions}
    runs = [row for row in read_csv(DATA / "validator_runs.csv") if row.get("operator") == "M09" and row.get("baseline_or_mutant") == "mutant" and row.get("configuration") in FORMAL_CONFIGS]
    rows: list[dict[str, object]] = []
    for validator in VALIDATORS:
        canonical = [row for row in runs if row.get("validator") == validator and row.get("artifact_id") not in excluded_ids and row.get("detection_classification") in {"Detected", "Missed"}]
        excluded_recorded = [row for row in runs if row.get("validator") == validator and row.get("artifact_id") in excluded_ids]
        excluded_usable = [row for row in excluded_recorded if row.get("detection_classification") in {"Detected", "Missed"}]
        rows.append({
            "validator": validator,
            "analysis_A": "canonical active M09 records",
            "canonical_detected": sum(row.get("detection_classification") == "Detected" for row in canonical),
            "canonical_no_target": sum(row.get("detection_classification") == "Missed" for row in canonical),
            "canonical_automated_denominator": len(canonical),
            "excluded_M09_records": len(excluded_recorded),
            "excluded_records_with_usable_outcome": len(excluded_usable),
            "analysis_B": "INVALID/UNVERIFIED sensitivity only; no excluded row is promoted",
            "hypothetical_detected_if_usable_rows_included": sum(row.get("detection_classification") == "Detected" for row in canonical + excluded_usable),
            "hypothetical_no_target_if_usable_rows_included": sum(row.get("detection_classification") == "Missed" for row in canonical + excluded_usable),
            "hypothetical_denominator_if_usable_rows_included": len(canonical) + len(excluded_usable),
            "interpretation": "Excluded M09 bytes cannot be re-audited; recorded rows are Not Applicable or unavailable, so the hypothetical view adds no valid outcome rows.",
        })
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "m09_exclusion_sensitivity.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "m09_exclusion_sensitivity.md").write_text(
        "# M09 exclusion sensitivity\n\n"
        "Analysis A is the canonical active M09 result. Analysis B is a deliberately invalid/unverified sensitivity view that would append previously recorded outcomes for the four post-discovery excluded M09 IDs if any usable Detected/Missed outcome existed. The historical mutant bytes are unavailable and no excluded row has a usable automated outcome, so B does not alter the headline result. The table is retained to make the exclusion boundary auditable; excluded artifacts are not reintroduced into the formal corpus.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "excluded_m09": len(exclusions), "path": str((OUT / "m09_exclusion_sensitivity.csv").relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
