"""Apply documented post-coding evidence and policy corrections.

Original coder decisions are never rewritten.  The two coder-specific queue
copies are repointed to preserved original packets when a custody defect was
repaired; only the merged adjudication queue receives corrected evidence and
final post-audit decisions.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "double_coding_queue.csv"
KEY_PATH = ROOT / "data" / "double_coding_key.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


CORRECTED_EVIDENCE = {
    "DC-0096": {
        "merged_path": "evidence/double_coding/DC-0096.pdf",
        "original_path": "evidence/double_coding/original_misassigned/DC-0096_original-named-Presentation_actual-AcademicAbstract.pdf",
        "expected_original_hash": "3c67048a5c45f687182b2e3fcc32655f00c6d1c9cc78f9342b651553011a3170",
    },
    "DC-0105": {
        "merged_path": "evidence/double_coding/DC-0105.pdf",
        "original_path": "evidence/double_coding/original_misassigned/DC-0105_original-named-BookChapterGerman_actual-Presentation.pdf",
        "expected_original_hash": "1c354fc80cbbabfa50b483b742d9eb3ff834e8dd01187cc7aa550a6a180c40c7",
    },
}

M04_UNRELATED = {"DC-0073", "DC-0081", "DC-0088", "DC-0095", "DC-0104", "DC-0114", "DC-0122", "DC-0131"}
SEMANTIC_OUTSIDE_SCOPE = {"DC-0119", "DC-0120", "DC-0128", "DC-0129"}
M05_OUTSIDE_SCOPE = set(CORRECTED_EVIDENCE)
M10_PROXY = {"DC-0041", "DC-0058", "DC-0066"}


def main() -> int:
    queue = read_csv(QUEUE_PATH)
    by_case = {row["case_id"]: row for row in queue}
    key = read_csv(KEY_PATH)
    key_by_case = {row["case_id"]: row for row in key}
    runs = {row["record_id"]: row for row in read_csv(ROOT / "data" / "validator_runs.csv")}

    corrections: list[dict[str, str]] = []
    for case_id, item in CORRECTED_EVIDENCE.items():
        merged = ROOT / item["merged_path"]
        original = ROOT / item["original_path"]
        if digest(original) != item["expected_original_hash"]:
            raise SystemExit(f"{case_id}: preserved original packet hash mismatch")
        corrected_hash = digest(merged)
        row = by_case[case_id]
        row["evidence_path"] = item["merged_path"]
        row["evidence_sha256"] = corrected_hash
        canonical = key_by_case[case_id]
        run = runs[canonical["record_id"]]
        if run["report_sha256"] != corrected_hash:
            raise SystemExit(f"{case_id}: corrected packet does not match the canonical report")
        canonical["report_sha256"] = corrected_hash
        corrections.append({
            "case_id": case_id,
            "issue": "PAC report was assigned to the wrong input artifact",
            "original_evidence_path": item["original_path"],
            "original_evidence_sha256": item["expected_original_hash"],
            "corrected_evidence_path": item["merged_path"],
            "corrected_evidence_sha256": corrected_hash,
            "coder_decisions_preserved": "true",
            "correction_date": date.today().isoformat(),
        })

    for case_id in M04_UNRELATED:
        row = by_case[case_id]
        row["adjudication_decision"] = "Unrelated"
        row["adjudication_rationale"] = (
            "Post-coding protocol audit: relative to the matched baseline, the mutant adds only generic PAC PDF Syntax "
            "failures. The report does not identify the M04 content-association exchange, so the new finding is "
            "collateral/unrelated rather than ambiguous. Original coder decisions are preserved."
        )
    for case_id in SEMANTIC_OUTSIDE_SCOPE:
        row = by_case[case_id]
        property_name = "logical reading order" if key_by_case[case_id]["operator"] == "M01" else "content completeness"
        row["adjudication_decision"] = "Outside Scope"
        row["adjudication_rationale"] = (
            f"Post-coding protocol audit: PAC's generic Structure elements finding does not identify the intended {property_name} "
            "property. PAC Formal makes no operator-specific automated claim for this Class B mutation, so the final label is "
            "Outside Scope, not Ambiguous. Original coder decisions are preserved."
        )
    for case_id in M05_OUTSIDE_SCOPE:
        row = by_case[case_id]
        row["adjudication_decision"] = "Outside Scope"
        row["adjudication_rationale"] = (
            "Post-coding custody correction: the original mismatched packet is preserved, and the corrected hash-linked PAC "
            "report identifies the expected mutant and passes. M05 intra-element content order is a Class B semantic property "
            "outside PAC Formal's automated claim, so the final label is Outside Scope. Original coder decisions are preserved."
        )
    for case_id in M10_PROXY:
        row = by_case[case_id]
        row["adjudication_decision"] = "Detected"
        row["adjudication_rationale"] = (
            "The matched baseline passes Acrobat Headers and the mutant newly fails it. The M10 proxy fixed before final adjudication applies "
            "because hash-linked 150-DPI verification confirms the exact direct-child /TH to /P change under the same /TR, "
            "unchanged target content and non-target structure, equal page-content hashes, and pixel-identical rendering."
        )

    if any(row["adjudication_decision"] == "Ambiguous" for row in queue):
        raise SystemExit("Unresolved Ambiguous adjudication remains")
    write_csv(QUEUE_PATH, queue)
    write_csv(KEY_PATH, key)

    for coder_path in (
        ROOT / "data" / "double_coding_queue_coder_1.csv",
        ROOT / "data" / "double_coding_queue_coder_2.csv",
    ):
        rows = read_csv(coder_path)
        for row in rows:
            if row["case_id"] in CORRECTED_EVIDENCE:
                item = CORRECTED_EVIDENCE[row["case_id"]]
                row["evidence_path"] = item["original_path"]
                row["evidence_sha256"] = item["expected_original_hash"]
        write_csv(coder_path, rows)

    write_csv(ROOT / "data" / "double_coding_corrections.csv", corrections)
    manifest_path = ROOT / "data" / "double_coding_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "status": "ADJUDICATED_WITH_DOCUMENTED_CORRECTIONS",
        "agreement_count": sum(row["agreement"] == "agree" for row in queue),
        "disagreement_count": sum(row["agreement"] == "disagree" for row in queue),
        "ambiguous_final_count": 0,
        "correction_ledger": "data/double_coding_corrections.csv",
        "original_coder_packets_preserved": True,
    })
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "cases": len(queue),
        "agreements": manifest["agreement_count"],
        "disagreements": manifest["disagreement_count"],
        "ambiguous_final": 0,
        "custody_corrections": len(corrections),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
