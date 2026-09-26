"""Generate deterministic operator-level formal mutant run guides from the queue."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "docs" / "runs"
SUBRUNS = RUNS / "subbatches"


def read_queue() -> list[dict[str, str]]:
    with (ROOT / "manual_runs_todo.csv").open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def canonical_active_count() -> int:
    excluded = {row.get("mutant_id", "") for row in read_queue_exclusions() if row.get("status")}
    manifest = ROOT / "data" / "mutants.jsonl"
    if not manifest.exists():
        return 0
    return sum(
        item.get("status") == "valid"
        and item.get("verification", {}).get("mutation_valid")
        and item.get("mutant_id") not in excluded
        for item in (json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line.strip())
    )


def read_queue_exclusions() -> list[dict[str, str]]:
    with (ROOT / "data" / "mutant_exclusions.csv").open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def row_line(row: dict[str, str], validator: str) -> str:
    configuration = row["configuration"]
    ai = "OFF" if validator == "PAC" else "Not applicable"
    expected_report = row["exact_output_filename"]
    if validator == "Acrobat":
        expected_report += f" (native: {Path(expected_report).with_suffix('.accreport.html').name})"
    return (
        f"| [ ] | `{row['artifact_id']}` | `{row['operator']}` | `{row['source_golden']}` | "
        f"`{row['filepath']}` | `{row['sha256']}` | "
        f"`{expected_report}` | `{row['evidence_destination']}` | "
        f"`{configuration}` | `{ai}` | `{row['status']}` |"
    )


def procedure(validator: str) -> list[str]:
    if validator == "PAC":
        return [
            "- Required configuration: PAC `26.1.0.0`, Formal/traditional PDF/UA check, AI OFF.",
            "- Before each file, confirm `HKCU\\Software\\axes4\\PAC\\EnableAIChecks=0` and verify the input SHA-256 matches this checklist.",
            "- Open the exact mutant PDF, run the Formal check, and export the PDF report without remediation or saving over the input.",
            "- Save the report using the exact hash-addressed filename under `evidence/pac/formal/`.",
            "- Record automated failures separately from manual-review prompts. Do not classify findings during collection.",
        ]
    return [
        "- Required configuration: Adobe Acrobat Pro Continuous Release `2026.002.21931`, Accessibility Checker / Full Check, all 31 checks, all pages.",
        "- Auto-tagging, remediation, and document modification remain disabled.",
        "- Before each file, verify the input SHA-256, run Full Check, and export the native HTML report.",
        "- Preserve the native report under `evidence/acrobat/` using the exact hash-addressed `.accreport.html` filename associated with the queue row.",
        "- Record automated failures separately from `Needs Manual Check` items. Do not classify findings during collection.",
    ]


def write_subbatch(batch: str, validator: str, operator: str, rows: list[dict[str, str]]) -> None:
    path = SUBRUNS / f"{batch}_{operator}.md"
    lines = [
        f"# {batch}_{operator}",
        "",
        f"Canonical sub-batch for `{validator}` mutant evidence. It contains only active `{operator}` mutants; excluded mutants are not listed.",
        "",
        "## Procedure",
        "",
        *procedure(validator),
        "",
        "## Checklist",
        "",
        "| Done | Mutant ID | Operator | Source golden | Exact input path | SHA-256 | Expected report | Evidence destination | Configuration | AI state | Queue status |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    lines.extend(row_line(row, validator) for row in rows)
    lines += [
        "",
        "## Completion",
        "",
        f"After this sub-batch is complete, run `python scripts/ingest_validator_evidence.py --sub-batch {batch}_{operator}`. The command reports only this sub-batch's missing/invalid reports and preserves previously ingested records.",
        "",
        "Do not count manual prompts, baseline-carried findings, or unrelated failures as detections. Classification happens only after evidence ingestion and baseline comparison.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_batch(batch: str, validator: str, rows: list[dict[str, str]]) -> None:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["operator"]].append(row)
    lines = [
        f"# {batch}",
        "",
        f"This is the canonical `{validator}` mutant evidence batch. It contains {len(rows)} active mutants and excludes `PDFUA-Ref-2-09_Scanned-M08`.",
        "",
        "The narrative labels `B03_MUTANT_PAC_FORMAL` and `B04_MUTANT_ACROBAT` are not queue IDs because `B03_VERAPDF_SETUP` is already established. The canonical mapping is PAC Formal=`B04_MUTANT_PAC_FORMAL`; Acrobat=`B05_MUTANT_ACROBAT`.",
        "",
        "## Fixed configuration",
        "",
        *procedure(validator),
        "",
        "## Operator sub-batches",
        "",
    ]
    for operator in sorted(grouped):
        sub = f"{batch.split('_', 1)[0]}_{operator}"
        lines.append(f"- [`{sub}`](subbatches/{sub}.md) — {len(grouped[operator])} PDFs")
    lines += [
        "",
        "## Baseline-delta rules",
        "",
        "Compare every mutant with the exact matching golden baseline for the same validator and configuration. Baseline-carried failures, manual prompts, unrelated failures, and collateral findings are not intended-defect detections.",
        "",
        "For `PDFUA-Ref-2-05_BookChapter-german-M06`, the Acrobat baseline's pre-existing `Lbl and LBody` failure is outside the M06 target branch. It must be retained as baseline context and never counted as an M06 detection.",
        "",
        "## Evidence ingestion",
        "",
        f"Run `python scripts/ingest_validator_evidence.py --batch {batch}` after the complete batch, or use the operator-specific command in each sub-batch guide for incremental ingestion.",
        "",
    ]
    (RUNS / f"{batch}.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = read_queue()
    for batch, validator in (("B04_MUTANT_PAC_FORMAL", "PAC"), ("B05_MUTANT_ACROBAT", "Acrobat")):
        active = [row for row in rows if row.get("batch_id") == batch and row.get("baseline_or_mutant") == "mutant"]
        expected = canonical_active_count()
        if len(active) != expected:
            raise SystemExit(f"{batch}: expected {expected} active rows, found {len(active)}")
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in active:
            grouped[row["operator"]].append(row)
        for operator, operator_rows in grouped.items():
            write_subbatch(batch.split("_", 2)[0], validator, operator, sorted(operator_rows, key=lambda r: int(r["order"])))
        write_batch(batch, validator, active)
    print("Generated canonical PAC and Acrobat mutant batch guides and operator sub-batches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
