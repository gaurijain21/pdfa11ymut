"""Create the hash-linked study-freeze manifest from canonical inputs."""
from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path

from verify_study_state import ROOT, read_csv, read_jsonl, sha256, study_counts


def package_versions() -> dict[str, str]:
    versions = {}
    for name in ("pypdf", "Pillow", "PyYAML", "PyMuPDF"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "MISSING"
    return versions


def hash_paths(paths: list[Path]) -> list[dict[str, str]]:
    output = []
    for path in sorted({p.resolve() for p in paths if p.is_file()}):
        output.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(path)})
    return output


def main() -> int:
    counts = study_counts()
    mutants = read_jsonl(ROOT / "data" / "mutants.jsonl")
    runs = read_csv(ROOT / "data" / "validator_runs.csv")
    controls = read_csv(ROOT / "data" / "controls.csv")
    active = set(counts["active_ids"])
    source_paths = [ROOT / row["source_pdf"] for row in mutants if row["mutant_id"] in active]
    mutant_paths = [ROOT / row["mutant_pdf"] for row in mutants if row["mutant_id"] in active]
    report_paths = [ROOT / row["raw_report_path"] for row in runs if row.get("artifact_id") in active or row.get("baseline_or_mutant") == "golden_baseline"]
    for row in controls:
        for field in ("verapdf_report_path", "pac_report_path", "acrobat_report_path"):
            report_paths.append(ROOT / row.get(field, "").replace("\\", "/"))
    analysis_paths = list((ROOT / "scripts").glob("*.py")) + [ROOT / "operators" / "operators.yaml"]
    figure_paths = list((ROOT / "paper" / "figures").glob("*")) + list((ROOT / "analysis" / "generated" / "figures").glob("*"))
    independent_dir = ROOT / "evidence" / "independent_verification_v2"
    if not independent_dir.is_dir():
        independent_dir = ROOT / "evidence" / "independent_verification"
    manuscript = ROOT / "paper" / "pdfa11ymut_ieee.tex"
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
    if counts["executed_control_rows"] == counts["control_rows"]:
        control_status = "COMPLETE"
        control_reason = "All planned controls have hash-linked artifact, veraPDF, PAC, and Acrobat evidence."
    elif counts["verapdf_control_rows"] == counts["control_rows"]:
        control_status = "VERAPDF_EXECUTED_PENDING_PAC_ACROBAT"
        control_reason = "All control PDFs pass artifact verification and veraPDF PDF/UA-1 has run; PAC and Acrobat runs remain pending."
    elif counts["artifact_verified_control_rows"] == counts["control_rows"]:
        control_status = "ARTIFACTS_VERIFIED_PENDING_VALIDATORS"
        control_reason = "All control PDFs pass independent artifact verification; PAC, Acrobat, and veraPDF runs remain pending."
    else:
        control_status = "NOT_EXECUTED"
        control_reason = "Control artifacts or validator runs remain incomplete."
    double_coding_complete = counts["double_coded_formal_rows"] == counts["formal_validator_rows"]
    freeze = {
        "manifest_version": "2.0",
        "study_id": "PDFa11yMut-2026-09-21",
        "authoritative_basis": "data/mutants.jsonl valid verified rows minus every documented data/mutant_exclusions.csv row; formal rows are matching active IDs under the three named formal configurations",
        "repository_commit": commit,
        "python": sys.version,
        "platform": platform.platform(),
        "dependency_versions": package_versions(),
        "counts": counts,
        "active_mutant_ids": counts["active_ids"],
        "excluded_mutant_ids": counts["excluded_ids"],
        "source_pdf_hashes": hash_paths(sorted(set(source_paths))),
        "mutant_pdf_hashes": hash_paths(sorted(set(mutant_paths))),
        "validator_report_hashes": hash_paths(report_paths),
        "independent_audit_hashes": hash_paths(list(independent_dir.glob("*.json"))),
        "at_evidence_hashes": hash_paths([ROOT / row.get("evidence_path", "") for row in read_csv(ROOT / "data" / "at_observations.csv")] + [ROOT / row.get("raw_log_path", "") for row in read_csv(ROOT / "data" / "at_observations.csv")]),
        "analysis_script_hashes": hash_paths(analysis_paths),
        "manuscript_hash": {"path": str(manuscript.relative_to(ROOT)), "sha256": sha256(manuscript)} if manuscript.is_file() else None,
        "figure_hashes": hash_paths(figure_paths),
        "double_coding": {
            "status": "COMPLETE" if double_coding_complete else "INCOMPLETE",
            "coded_rows": counts["double_coded_formal_rows"],
            "required_rows": counts["formal_validator_rows"],
            "reason": (
                "All formal rows contain two recorded coder decision fields and a final adjudication; coder identity/independence provenance is not substantiated by this repository, and original decisions plus documented evidence corrections are preserved."
                if double_coding_complete
                else "One or more formal rows lack coder_1, coder_2, or adjudication fields in the canonical validator ledger."
            ),
        },
        "negative_controls": {"status": control_status, "path": "data/controls.csv", "artifact_verified_rows": counts["artifact_verified_control_rows"], "verapdf_rows": counts["verapdf_control_rows"], "pac_rows": sum(row.get("pac_parse_status") == "PASS" for row in controls), "acrobat_rows": sum(row.get("acrobat_parse_status") == "PASS" for row in controls), "executed_rows": counts["executed_control_rows"], "reason": control_reason + " Controls remain descriptive baseline/false-positive evidence rather than positive-study outcomes."},
        "independent_oracle": {"parser_a": "pypdf", "parser_b": "PyMuPDF/MuPDF", "renderer_a": "Poppler pdftoppm", "renderer_b": "MuPDF pixmap", "command": "python scripts/independent_audit.py"},
        "commands": {
            "verify": "python reproduce.py",
            "scratch_regeneration": "python scripts/regenerate_scratch.py",
            "analysis": "python scripts/rebuild_analysis.py",
            "independent_audit": "python scripts/independent_audit.py",
            "control_artifact_verification": "python scripts/execute_controls.py",
            "tests": "python -m unittest discover -s tests -p \"test*.py\" -q",
            "evidence_check": "python scripts/check_evidence.py",
            "release_verify": "python scripts/verify_study_state.py --verify",
        },
        "status": "CONDITIONAL" if counts["double_coded_formal_rows"] != counts["formal_validator_rows"] or counts["formal_validator_rows"] != counts["active_mutants"] * 3 else "READY",
    }
    output = ROOT / "analysis" / "generated" / "study_freeze_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "status": freeze["status"], "counts": counts}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
