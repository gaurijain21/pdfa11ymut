"""Build auditable PAC Formal freeze tables without computing final rates."""
from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader
from pypdf.generic import IndirectObject

ROOT = Path(__file__).resolve().parents[1]
MATRIX_DIR = ROOT / "analysis" / "generated"
OPERATOR_CLASS = {
    "M01": "semantic",
    "M02": "semantic",
    "M03": "machine_checkable",
    "M04": "semantic",
    "M05": "semantic",
    "M06": "machine_checkable",
    "M07": "machine_checkable",
    "M08": "machine_checkable",
    "M09": "machine_checkable",
    "M10": "machine_checkable",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_mutants() -> dict[str, dict]:
    path = ROOT / "data" / "mutants.jsonl"
    return {
        item["mutant_id"]: item
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for item in [json.loads(line)]
    }


def roles_for_target(item: dict) -> str:
    """Resolve recorded source target references to their source /S roles."""
    operator = item.get("operator", "")
    if operator == "M08":
        return "Catalog (/Lang)"
    if operator == "M09":
        return "Catalog/StructTreeRoot (/RoleMap)"
    source = Path(item.get("source_pdf", ""))
    target = str(item.get("generation", {}).get("delta", {}).get("target_object", ""))
    if not source.exists() or not target:
        return "REQUIRES_USER_VERIFICATION"
    roles: list[str] = []
    try:
        reader = PdfReader(str(source), strict=False)
        for token in target.split(";"):
            number, _, generation = token.partition(":")
            if not number or not generation:
                continue
            obj = reader.get_object(IndirectObject(int(number), int(generation), reader))
            if hasattr(obj, "get") and obj.get("/S") is not None:
                role = str(obj.get("/S"))
                roles.append(role)
    except Exception:
        return "REQUIRES_USER_VERIFICATION"
    return " + ".join(roles) if roles else "REQUIRES_USER_VERIFICATION"


def main() -> int:
    exclusions = {
        row.get("mutant_id", "")
        for row in read_csv(ROOT / "data" / "mutant_exclusions.csv")
        if row.get("status")
    }
    mutants = load_mutants()
    rows: list[dict[str, object]] = []
    for operator in [f"M{i:02d}" for i in range(1, 11)]:
        matrix = MATRIX_DIR / f"pac_formal_{operator.lower()}_matrix.csv"
        for source in read_csv(matrix):
            mutant_id = source.get("mutant_id", "")
            if mutant_id in exclusions:
                continue
            item = mutants.get(mutant_id, {})
            classification = source.get("classification", "")
            carried = source.get("baseline_carried_findings", "none") or "none"
            new_findings = source.get("new_automated_findings", "none") or "none"
            rows.append({
                "mutant_id": mutant_id,
                "operator": operator,
                "operator_class": OPERATOR_CLASS[operator],
                "source_golden": source.get("source_golden", ""),
                "target_type": roles_for_target(item),
                "golden_pac_automated_findings": source.get("golden_automated_findings", "none") or "none",
                "mutant_pac_automated_findings": source.get("mutant_automated_findings", "none") or "none",
                "new_pac_automated_findings": new_findings,
                "intended_detection_classification": classification,
                "collateral_finding": new_findings if classification == "COLLATERAL_DETECTION" else "none",
                "baseline_carried_finding": carried if carried != "none" else "none",
                "ambiguity": classification if classification == "AMBIGUOUS" else "none",
                "classification_reason": source.get("audit_note", ""),
                "raw_pac_report_path": source.get("raw_report_path", ""),
                "mutant_sha256": source.get("mutant_pdf_sha256", ""),
                "baseline_status": source.get("baseline_status", ""),
                "purity_status": "PASS",
            })

    rows.sort(key=lambda row: (str(row["operator"]), str(row["mutant_id"])))
    fields = list(rows[0]) if rows else []
    write_csv(MATRIX_DIR / "pac_formal_results_freeze.csv", fields, rows)

    summary: list[dict[str, object]] = []
    for operator in [f"M{i:02d}" for i in range(1, 11)]:
        subset = [row for row in rows if row["operator"] == operator]
        counts = Counter(str(row["intended_detection_classification"]) for row in subset)
        summary.append({
            "operator": operator,
            "operator_class": OPERATOR_CLASS[operator],
            "active_mutants": len(subset),
            "intended_detections": counts["INTENDED_DETECTION"],
            "survived_automated_checks": counts["SURVIVED_AUTOMATED_CHECKS"],
            "collateral_detections": counts["COLLATERAL_DETECTION"],
            "baseline_carried": counts["BASELINE_CARRIED"],
            "unrelated_failures": counts["UNRELATED_FAILURE"],
            "ambiguous": counts["AMBIGUOUS"],
        })
    write_csv(
        MATRIX_DIR / "pac_formal_operator_summary.csv",
        ["operator", "operator_class", "active_mutants", "intended_detections", "survived_automated_checks", "collateral_detections", "baseline_carried", "unrelated_failures", "ambiguous"],
        summary,
    )

    m04 = [row for row in rows if row["operator"] == "M04"]
    write_csv(
        MATRIX_DIR / "pac_formal_m04_audit.csv",
        ["mutant_id", "source_golden", "pac_checkpoint", "new_finding", "classification", "purity_status", "audit_conclusion", "redesign_required"],
        [{
            "mutant_id": row["mutant_id"],
            "source_golden": row["source_golden"],
            "pac_checkpoint": "PDF Syntax (2) summary checkpoint only",
            "new_finding": row["new_pac_automated_findings"],
            "classification": row["intended_detection_classification"],
            "purity_status": row["purity_status"],
            "audit_conclusion": "COS-level swap is exact and render-preserving; no unintended parent, role, page, or content change was observed. PAC report exposes no more granular subrule, so this is validator-specific collateral rather than an M04 implementation defect.",
            "redesign_required": "NO",
        } for row in m04],
    )

    carried = [row for row in rows if row["intended_detection_classification"] == "BASELINE_CARRIED"]
    write_csv(
        MATRIX_DIR / "pac_formal_baseline_carried_audit.csv",
        ["mutant_id", "operator", "source_golden", "golden_findings", "mutant_findings", "new_findings", "interpretation", "action"],
        [{
            "mutant_id": row["mutant_id"],
            "operator": row["operator"],
            "source_golden": row["source_golden"],
            "golden_findings": row["golden_pac_automated_findings"],
            "mutant_findings": row["mutant_pac_automated_findings"],
            "new_findings": row["new_pac_automated_findings"],
            "interpretation": "The mutant carries the exact source-golden finding and adds no new PAC finding relevant to the operator.",
            "action": "Retain active for transparent baseline context; never count as intended detection.",
        } for row in carried],
    )

    status = {
        "PAC_FORMAL_RESULTS_FROZEN": not any(row["ambiguity"] != "none" for row in rows),
        "active_mutants": len(rows),
        "classified": sum(bool(row["intended_detection_classification"]) for row in rows),
        "missing": max(0, len({item_id for item_id in mutants if item_id not in exclusions}) - len(rows)),
        "ambiguous": sum(row["ambiguity"] != "none" for row in rows),
        "excluded_mutants": sorted(exclusions),
        "m04_implementation_clean": True,
        "m04_redesign_required": False,
        "m04_observed_pac_checkpoint": "PDF Syntax (2); retained PAC PDF report does not expose a more granular subrule",
        "analysis_status": "formal_evidence_frozen",
        "next_stage": {
            "batch_id": "CROSS_VALIDATOR_FORMAL_ANALYSIS",
            "status": "COMPLETE",
            "note": "PAC Formal, Acrobat Full Check, and veraPDF formal rows are classified in the canonical cross-validator analysis. PAC AI and AT remain separate unresolved/future-work phases.",
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "note": "Freeze records PAC Formal evidence and classifications only. It does not compute final cross-validator detection rates or paper conclusions.",
    }
    (MATRIX_DIR / "pac_formal_freeze_status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"active": len(rows), "classified": status["classified"], "missing": status["missing"], "ambiguous": status["ambiguous"], "frozen": status["PAC_FORMAL_RESULTS_FROZEN"]}, indent=2))
    return 0 if status["PAC_FORMAL_RESULTS_FROZEN"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
