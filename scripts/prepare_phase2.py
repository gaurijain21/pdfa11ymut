"""Prepare the frozen PAC AI and illustrative exploratory AT phase.

This script only audits and writes manifests/templates. It never launches PAC,
changes PAC settings, opens a PDF, or modifies a tested PDF.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "analysis" / "generated"
FREEZE = OUT / "formal_results_freeze.csv"

AI_CLASSES = [
    "AI_INTENDED_FINDING", "AI_RELATED_BUT_INCOMPLETE", "AI_UNRELATED_FINDING",
    "AI_BASELINE_CARRIED", "AI_NO_RELEVANT_FINDING", "AI_AMBIGUOUS",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_relative(path: Path) -> str:
    """Serialize repository paths portably instead of leaking a local checkout."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def file_metadata(path: Path) -> dict:
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path) if path.is_file() else "MISSING",
        "row_count": max(0, len(read_csv(path)) if path.suffix.lower() == ".csv" else 0),
        "exists": path.is_file(),
    }


def write_formal_freeze_manifest() -> dict:
    rows = read_csv(FREEZE)
    active = {row["artifact_id"] for row in rows}
    excluded = [row for row in read_csv(DATA / "mutant_exclusions.csv") if row.get("status")]
    manifest = {
        "manifest_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "freeze": {
            **file_metadata(FREEZE),
            "expected_row_count": len(rows),
            "unique_mutants": len(active),
            "expected_unique_mutants": len(active),
            "all_ambiguous_or_confounded_false": all(row.get("ambiguous_or_confounded") == "FALSE" for row in rows),
            "classified_rows": sum(bool(row.get("detection_classification")) for row in rows),
        },
        "excluded_artifacts": excluded,
        "inputs": [
            file_metadata(DATA / "validator_runs.csv"),
            file_metadata(DATA / "baseline_deltas.csv"),
            file_metadata(DATA / "baseline_conflict_resolutions.csv"),
            file_metadata(OUT / "baseline_operator_conflicts.csv"),
            file_metadata(OUT / "baseline_cross_validator_disagreements.csv"),
            file_metadata(DATA / "pac_evidence_manifest.csv"),
            file_metadata(DATA / "acrobat_evidence_manifest.csv"),
            file_metadata(DATA / "verapdf_runs.csv"),
        ],
        "integrity_status": "PASS" if len(rows) == len(active) * 3 and all(row.get("ambiguous_or_confounded") == "FALSE" for row in rows) else "REVIEW_REQUIRED",
        "note": "Formal classifications are frozen. This manifest records provenance; it does not authorize changes to formal_results_freeze.csv.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "formal_freeze_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def write_ai_metadata() -> dict:
    formal = {}
    formal_path = DATA / "pac_formal_run_metadata.json"
    if formal_path.exists():
        formal = json.loads(formal_path.read_text(encoding="utf-8"))
    metadata = {
        "metadata_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pac_version": formal.get("pac_version", "26.1.0.0"),
        "pac_build": formal.get("pac_build", "26.1.0.0 (PAC.exe FileVersion/ProductVersion)"),
        "pac_executable": formal.get("pac_executable", "C:\\Users\\iamga\\AppData\\Local\\PAC\\PAC.exe"),
        "platform": formal.get("platform", platform.platform()),
        "profile": "PDF/UA formal/traditional check with PAC AI semantic analysis",
        "run_configuration": "PAC AI",
        "ai_enabled": False,
        "ai_state": "PENDING_NATIVE_CONTROL",
        "requested_ai_enabled": True,
        "ai_registry_path": "HKCU\\Software\\axes4\\PAC\\EnableAIChecks",
        "ai_registry_target_value": 1,
        "ai_registry_value_observed": formal.get("ai_registry_value", 0),
        "model_info": "PAC-managed AI model; record exact model/build shown by PAC at first controlled run.",
        "settings": {
            "formal_checks": "unchanged from PAC Formal baseline configuration",
            "ai_analysis": "enabled for the AI batch only",
            "remediation": "disabled",
            "pdf_modification": "forbidden",
        },
        "native_control_status": "UNAVAILABLE_AFTER_REQUIRED_RETRY_AND_REINITIALIZATION",
        "limitation": "PAC AI was not launched or enabled because native Windows Computer Use returned no app inventory. Reconfirm native control before execution.",
    }
    (DATA / "pac_ai_run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def write_ai_batches(selection: list[dict]) -> list[dict]:
    mutants = {row["mutant_id"]: row for row in read_jsonl(DATA / "mutants.jsonl")}
    selected = [row for row in selection if row.get("artifact_type") == "mutant" and row.get("selected_for_ai") == "TRUE"]
    rows: list[dict] = []
    selected_goldens = sorted({row["source_golden"] for row in selected})
    for golden in selected_goldens:
        path = ROOT / "corpus" / "golden" / f"{golden}.pdf"
        digest = sha256(path)
        rows.append({
            "batch_id": "B07_GOLDEN_PAC_AI_SELECTED", "artifact_type": "golden", "artifact_id": golden,
            "operator": "", "source_golden": golden, "filepath": repo_relative(path), "sha256": digest,
            "expected_report": f"{golden}__{digest}.pdf", "evidence_path": "evidence/pac/ai",
            "configuration": "AI", "ai_state": "ON_REQUIRED", "control_type": "golden_baseline",
            "status": "TODO", "selection_reason": "Required golden baseline for selected PAC AI mutants.",
        })
    for row in selected:
        item = mutants[row["artifact_id"]]
        path = Path(item["mutant_pdf"])
        digest = item["mutant_sha256"]
        rows.append({
            "batch_id": "B08_MUTANT_PAC_AI_SELECTED", "artifact_type": "mutant", "artifact_id": row["artifact_id"],
            "operator": row["operator"], "source_golden": row["source_golden"], "filepath": repo_relative(path), "sha256": digest,
            "expected_report": f"{row['artifact_id']}__{digest}.pdf", "evidence_path": "evidence/pac/ai",
            "configuration": "AI", "ai_state": "ON_REQUIRED", "control_type": row["control_type"],
            "status": "TODO", "selection_reason": row["selection_reason"],
        })
    target = OUT / "pac_ai_batch_checklist.csv"
    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["status"])
        writer.writeheader(); writer.writerows(rows)
    return rows


def write_ai_classification_template(selection: list[dict]) -> int:
    fields = [
        "record_id", "artifact_id", "source_golden", "operator", "operator_class",
        "formal_classification", "ai_classification", "ai_finding_summary",
        "golden_evidence_path", "mutant_evidence_path", "evidence_references",
        "rationale", "status", "coder_1", "coder_2", "adjudication",
    ]
    existing = {
        row.get("artifact_id", ""): row
        for row in read_csv(DATA / "pac_ai_classifications.csv")
        if row.get("artifact_id")
    }
    mutants = {row["mutant_id"]: row for row in read_jsonl(DATA / "mutants.jsonl")}
    ai_evidence = ROOT / "evidence" / "pac" / "ai"
    golden_evidence = {
        path.name.split("__", 1)[0]: path
        for path in ai_evidence.glob("*.pdf")
        if "__" in path.name and "-M" not in path.name
    }
    rows = []
    for row in selection:
        if row.get("artifact_type") != "mutant" or row.get("selected_for_ai") != "TRUE":
            continue
        item = mutants.get(row["artifact_id"], {})
        mutant_evidence = ai_evidence / f"{row['artifact_id']}__{item.get('mutant_sha256', '')}.pdf"
        base = {
            "record_id": f"PAC_AI::{row['artifact_id']}", "artifact_id": row["artifact_id"],
            "source_golden": row["source_golden"], "operator": row["operator"],
            "operator_class": row["operator_class"], "formal_classification": row["PAC_formal_classification"],
            "ai_classification": "", "ai_finding_summary": "", "golden_evidence_path": "",
            "mutant_evidence_path": "", "evidence_references": "", "rationale": "",
            "status": "TODO", "coder_1": "", "coder_2": "", "adjudication": "",
        }
        prior = existing.get(row["artifact_id"], {})
        if prior.get("status") and prior.get("status") != "TODO":
            base.update({key: value for key, value in prior.items() if key in fields})
            for key in ("golden_evidence_path", "mutant_evidence_path"):
                if base.get(key):
                    base[key] = repo_relative(Path(base[key]))
            if base.get("ai_classification") == "AI_AMBIGUOUS":
                base["rationale"] = "The preserved PAC AI package is aggregate-only; the fresh native pilot exposed element-level finding text/scores but no supported complete semantic export/API, so the canonical classification remains gated."
                base["coder_1"] = "PAC UI native semantic pilot and preserved aggregate capture"
        elif mutant_evidence.exists():
            base.update({
                "ai_classification": "AI_AMBIGUOUS",
                "golden_evidence_path": repo_relative(golden_evidence[row["source_golden"]]) if row["source_golden"] in golden_evidence else "",
                "mutant_evidence_path": repo_relative(mutant_evidence),
                "evidence_references": "analysis/generated/pac_ai_aggregate_count_adjudication.md",
                "rationale": "The preserved PAC AI package is aggregate-only; the fresh native pilot exposed element-level finding text/scores but no supported complete semantic export/API, so the canonical classification remains gated.",
                "status": "REVIEW_REQUIRED",
                "coder_1": "PAC UI aggregate capture",
            })
        rows.append(base)
    path = DATA / "pac_ai_classifications.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    return len(rows)


def write_at_template() -> int:
    selected = read_csv(DATA / "at_selection.csv")
    existing = {
        row.get("artifact_id", ""): row
        for row in read_csv(DATA / "at_observations.csv")
        if row.get("artifact_id")
    }
    fields = [
        "record_id", "artifact_id", "source_golden", "mutant_id", "operator", "at_name",
        "at_version", "viewer", "viewer_version", "os_version", "procedure",
        "expected_golden_behavior", "expected_mutant_behavior", "exact_at_observation",
        "golden_observation", "mutant_observation", "observation", "evidence_path",
        "golden_sha256", "mutant_sha256", "status", "coder_1", "coder_2", "agree", "adjudication", "notes",
    ]
    mutants = {row["mutant_id"]: row for row in read_jsonl(DATA / "mutants.jsonl")}
    rows = []
    for row in selected:
        item = mutants.get(row.get("mutant_id"), {})
        base = {
            "record_id": f"AT::{row['mutant_id']}", "artifact_id": row["artifact_id"],
            "source_golden": row["source_golden"], "mutant_id": row["mutant_id"],
            "operator": row["operator"], "at_name": "NVDA", "at_version": "",
            "viewer": "", "viewer_version": "", "os_version": "",
            "procedure": row["exact_at_observation"],
            "expected_golden_behavior": row["expected_golden_behavior"],
            "expected_mutant_behavior": row["expected_mutant_behavior"],
            "exact_at_observation": row["exact_at_observation"], "golden_observation": "",
            "mutant_observation": "", "observation": "", "evidence_path": "",
            "golden_sha256": item.get("source_sha256", ""), "mutant_sha256": item.get("mutant_sha256", ""),
            "status": "TODO",
            "coder_1": "", "coder_2": "", "agree": "", "adjudication": "",
            "notes": "Current local M04 artifact; do not relabel as the permanently excluded historical G02-M04 case." if row.get("mutant_id") == "PDFUA-Ref-2-02_Invoice-M04" else "",
        }
        prior = existing.get(row["artifact_id"], {})
        if prior.get("status") and prior.get("status") != "TODO":
            base.update({key: value for key, value in prior.items() if key in fields})
        rows.append(base)
    path = DATA / "at_observations.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    return len(rows)


def main() -> int:
    manifest = write_formal_freeze_manifest()
    metadata = write_ai_metadata()
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from pdfa11ymut.phase2 import select_pac_ai_rows, valid_mutants
    selection = select_pac_ai_rows(valid_mutants())
    selected_mutants = [row for row in selection if row.get("artifact_type") == "mutant" and row.get("selected_for_ai") == "TRUE"]
    selected_semantic = [row for row in selected_mutants if row.get("operator_class") == "semantic"]
    selected_controls = [row for row in selected_mutants if row.get("control_type") == "machine_checkable_control"]
    # Reuse the canonical writer so the selection file remains compatible with
    # queue generation and analysis rebuilds.
    from pdfa11ymut.phase2 import write_pac_ai_selection
    selection = write_pac_ai_selection(valid_mutants())
    batches = write_ai_batches(selection)
    classification_rows = write_ai_classification_template(selection)
    at_rows = write_at_template()
    preparation = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "native_control_status": metadata["native_control_status"],
        "formal_freeze_integrity": manifest["integrity_status"],
        "selected_semantic_mutants": len(selected_semantic),
        "selected_machine_controls": len(selected_controls),
        "selected_mutants_total": len(selected_mutants),
        "selected_golden_baselines": len({row["source_golden"] for row in selected_mutants}),
        "total_pac_ai_gui_runs": len(batches),
        "pac_ai_classification_template_rows": classification_rows,
        "at_cases_prepared": at_rows,
        "ai_classification_categories": AI_CLASSES,
        "next_action": "Reconfirm native PAC control, enable PAC AI, then execute B07 golden baselines before B08 mutants.",
    }
    (OUT / "phase2_preparation.json").write_text(json.dumps(preparation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(preparation, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
