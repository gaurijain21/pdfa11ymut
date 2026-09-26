"""Build the canonical study manifest and derived audit tables.

The manifest is derived from the evidence-first inputs only. Legacy files whose
names begin with ``pdfa11ymut_`` are deliberately not read. The command writes
the manifest and small, machine-readable views needed by the audit; it never
rewrites PDFs, raw validator reports, or classifications.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import platform
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from pdfa11ymut.core import find_candidates, ref_label

DATA = ROOT / "data"
EVIDENCE = ROOT / "evidence"
FORMAL_CONFIGS = {"Formal", "Full Check", "PDF/UA-1 ua1"}
CLASSIFICATIONS = {"Detected", "Missed", "Needs Manual Check", "Not Applicable"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def git_value(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def operator_specs() -> dict[str, dict]:
    data = yaml.safe_load((ROOT / "operators" / "operators.yaml").read_text(encoding="utf-8"))
    return {item["id"]: item for item in data["operators"]}


def common_target_selection_rule() -> str:
    data = yaml.safe_load((ROOT / "operators" / "operators.yaml").read_text(encoding="utf-8"))
    return str(data.get("common", {}).get("target_selection_method", "first eligible reachable target in stable structure traversal order"))


def build_environment_rows() -> list[dict[str, object]]:
    """Flatten recorded validator metadata and local runtime versions."""
    rows: list[dict[str, object]] = []
    pac = json.loads((DATA / "pac_formal_run_metadata.json").read_text(encoding="utf-8"))
    rows.append({"component": "PAC", "version": pac.get("pac_version", ""), "configuration": pac.get("run_configuration", ""), "settings": json.dumps({"profile": pac.get("profile"), "ai_enabled": pac.get("ai_enabled"), "platform": pac.get("platform")}, sort_keys=True), "source": "data/pac_formal_run_metadata.json"})
    acrobat = json.loads((DATA / "acrobat_run_metadata.json").read_text(encoding="utf-8"))
    acrobat_settings = {"checker": acrobat.get("checker"), **acrobat.get("configuration", {}), "platform": acrobat.get("platform"), "configuration_discrepancy": "Canonical record uses 31 of 32 checks selected from the preserved native session and G01 report context; the older 31 of 31 metadata wording is retained as historical provenance. Reports/classifications were not changed."}
    rows.append({"component": "Adobe Acrobat", "version": acrobat.get("version", ""), "configuration": acrobat.get("run_configuration", ""), "settings": json.dumps(acrobat_settings, sort_keys=True), "source": "data/acrobat_run_metadata.json and docs/NATIVE_VALIDATOR_SESSION.md"})
    vera = json.loads((DATA / "verapdf_setup.json").read_text(encoding="utf-8"))
    rows.append({"component": "veraPDF", "version": vera.get("version", ""), "configuration": vera.get("profile", ""), "settings": json.dumps({"implementation": vera.get("implementation"), "java_version": vera.get("java_version"), "report_format": vera.get("report_format")}, sort_keys=True), "source": "data/verapdf_setup.json"})
    rows.append({"component": "Python", "version": platform.python_version(), "configuration": "runtime", "settings": json.dumps({"platform": platform.platform()}, sort_keys=True), "source": "runtime capture"})
    for package in ("pypdf", "PyMuPDF", "Pillow", "PyYAML"):
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "UNAVAILABLE"
        rows.append({"component": package, "version": version, "configuration": "runtime", "settings": "", "source": "importlib.metadata"})
    for executable in ("pdftoppm", "qpdf", "mutool"):
        path = shutil.which(executable)
        version = "UNAVAILABLE"
        if path:
            try:
                result = subprocess.run([executable, "-v"], capture_output=True, text=True, check=False)
                version = (result.stderr or result.stdout).splitlines()[0]
            except (OSError, IndexError):
                version = "INSTALLED_VERSION_UNREAD"
        rows.append({"component": executable, "version": version, "configuration": "runtime", "settings": json.dumps({"path": path or ""}, sort_keys=True), "source": "runtime capture"})
    tectonic = ROOT / "tmp" / "tectonic" / "bin" / ("tectonic.exe" if platform.system() == "Windows" else "tectonic")
    tectonic_version = "UNAVAILABLE"
    if tectonic.is_file():
        try:
            result = subprocess.run([str(tectonic), "--version"], capture_output=True, text=True, check=False)
            tectonic_version = (result.stdout or result.stderr).strip().splitlines()[0]
        except (OSError, IndexError):
            tectonic_version = "INSTALLED_VERSION_UNREAD"
    rows.append({"component": "Tectonic", "version": tectonic_version, "configuration": "manuscript build", "settings": json.dumps({"path": str(tectonic) if tectonic.is_file() else ""}, sort_keys=True), "source": "runtime capture"})
    return rows


def active_records() -> tuple[list[dict], list[dict], set[str], set[str]]:
    mutants = read_jsonl(DATA / "mutants.jsonl")
    exclusions = read_csv(DATA / "mutant_exclusions.csv")
    excluded_ids = {row.get("mutant_id", "") for row in exclusions if row.get("status")}
    valid = [
        row for row in mutants
        if str(row.get("status", "")).lower() == "valid"
        and row.get("verification", {}).get("mutation_valid") is True
    ]
    active = [row for row in valid if row.get("mutant_id") not in excluded_ids]
    return active, exclusions, {row["mutant_id"] for row in valid}, excluded_ids


def build_target_selection(active: list[dict], specs: dict[str, dict], common_rule: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for record in active:
        source_path = ROOT / record["source_pdf"]
        reader = PdfReader(str(source_path), strict=False)
        candidates = find_candidates(reader, record["operator"])
        delta = record.get("generation", {}).get("delta", {})
        rows.append({
            "mutant_id": record["mutant_id"],
            "operator": record["operator"],
            "source_golden": Path(record["source_pdf"]).stem,
            "source_sha256": record.get("source_sha256", ""),
            "requested_target": record.get("generation", {}).get("requested_target", ""),
            "selection_rule": specs[record["operator"]].get("target_selection_method", common_rule),
            "eligible_candidate_count": len(candidates),
            "eligible_candidate_refs": ";".join(ref_label(candidate) for candidate in candidates),
            "chosen_target": delta.get("target_object", ""),
            "target_precondition_status": "PASS" if candidates else "FAIL",
            "target_reachability_status": "PASS" if record.get("verification", {}).get("mutation_valid") is True else "FAIL",
            "mutant_sha256": record.get("mutant_sha256", ""),
        })
    return rows


def build_delta_manifest(active: list[dict], specs: dict[str, dict]) -> list[dict[str, object]]:
    independent_dir = EVIDENCE / "independent_verification_v2"
    independent = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in independent_dir.glob("*.json")
    } if independent_dir.is_dir() else {}
    rows = []
    for record in active:
        operator = record["operator"]
        spec = specs[operator]
        audit = independent.get(record["mutant_id"], {})
        rows.append({
            "mutant_id": record["mutant_id"],
            "baseline_sha256": record.get("source_sha256", ""),
            "mutant_sha256": record.get("mutant_sha256", ""),
            "operator": operator,
            "target_object": record.get("generation", {}).get("delta", {}).get("target_object", record.get("generation", {}).get("requested_target", "")),
            "preconditions": spec.get("preconditions", []),
            "allowed_changes": [spec.get("expected_structural_delta", "")],
            "required_invariants": spec.get("invariants", []),
            "prohibited_collateral_changes": spec.get("collateral_change_conditions", []),
            "observed_changes": {
                "generator_delta": record.get("verification", {}).get("observed_delta", {}),
                "generator_paths": record.get("verification", {}).get("observed_changed_structure_paths", []),
                "independent_delta": audit.get("observed_delta", {}),
                "independent_unexpected_changes": audit.get("unexpected_structural_changes", []) + audit.get("unexpected_content_changes", []),
            },
            "generator_purity_pass": record.get("verification", {}).get("mutation_valid") is True and not record.get("verification", {}).get("unexpected_structural_changes"),
            "independent_structural_status": audit.get("independent_structure_status", "MISSING"),
            "purity_status": "PASS" if record.get("verification", {}).get("mutation_valid") is True and audit.get("independent_structure_status") == "PASS" else "PARTIAL_REVIEW_REQUIRED",
            "verification_methods": ["pypdf generator-side verifier", "Poppler 150-DPI exact RGB render", "PyMuPDF/MuPDF independent audit"],
        })
    return rows


def build_standard_mapping(specs: dict[str, dict]) -> list[dict[str, object]]:
    matterhorn_review = {
        "M01": "Matterhorn 09-001 (tags not in logical reading order), Human; semantic target, not an automated kill oracle",
        "M02": "Matterhorn 01-005/01-006 are related completeness/semantic conditions; exact omission interpretation is scope-dependent",
        "M03": "Matterhorn 14-003 (skipped numbered heading levels), Machine",
        "M04": "Matterhorn 09-003 (semantic appropriateness), Human; exact marked-content association is not a stable automated rule",
        "M05": "Matterhorn 09-001 (logical reading order), Human; exact intra-element sequence is semantic",
        "M06": "Matterhorn 09-005 (list syntax), Machine in general, but no explicit duplicate-reference condition was identified; retain as Class B",
        "M07": "Matterhorn 13-004 (Figure alternative/replacement text missing), Machine",
        "M08": "Matterhorn 11-001 (natural language for page content cannot be determined), Machine; catalog /Lang is the tested representation",
        "M09": "Matterhorn 02-001 (non-standard tag mapping does not terminate with a standard type), Machine; applies to RoleMap entries whether used or not",
        "M10": "Matterhorn 09-004 (table-related structure syntax), Machine; direct TR child-role interpretation is profile/tool dependent",
    }
    rows = []
    for operator in sorted(specs):
        spec = specs[operator]
        known = "; ".join(str(item) for item in spec.get("known_applicable_validator_rules", []))
        rows.append({
            "operator": operator,
            "description": spec.get("name", ""),
            "operator_class": spec.get("class", ""),
            "target_structure": "; ".join(str(item) for item in spec.get("target_structure_types", [])),
            "accessibility_property": spec.get("accessibility_property", ""),
            "pdfua_relationship": spec.get("pdfua_relationship", ""),
            "iso_clause_or_requirement": known,
            "matterhorn_or_technique": matterhorn_review.get(operator, spec.get("checkpoint_or_technique", "")),
            "machine_or_human_status": "machine-checkable/conformance-oriented" if spec.get("machine_checkable") else "semantic/human-judgment/assistive-representation",
            "expected_checker_capability": spec.get("expected_automated_detectability", ""),
            "class_rationale": "Class A: file property has a checkable structural/conformance predicate." if spec.get("machine_checkable") else "Class B: semantic, completeness, order, or representation effect is not assumed to be mechanically decidable by the tested checker.",
            "source_reference": spec.get("source_reference", ""),
            "mapping_status": "AUTHORITATIVE_MATTERHORN_REVIEWED; CLASS_B_OR_SCOPE_LIMITED" if not spec.get("machine_checkable") else "AUTHORITATIVE_MATTERHORN_REVIEWED; MACHINE_SCOPE_RECORDED",
        })
    return rows


def build_baseline_provenance(inventory: list[dict], provenance: list[dict]) -> list[dict[str, object]]:
    by_id = {row.get("artifact_id"): row for row in provenance}
    return [{
        "artifact_id": row.get("artifact_id", ""),
        "local_filename": row.get("filename", ""),
        "source": row.get("source_collection", ""),
        "suite_identifier": row.get("source_reference", ""),
        "official_filename": by_id.get(row.get("artifact_id"), {}).get("official_filename", ""),
        "sha256": row.get("sha256", ""),
        "license": row.get("license", ""),
        "acquisition_provenance": row.get("notes", ""),
        "source_url": by_id.get(row.get("artifact_id"), {}).get("download_url", ""),
        "provenance_status": by_id.get(row.get("artifact_id"), {}).get("provenance_status", ""),
        "page_count": row.get("page_count", ""),
        "baseline_status": row.get("baseline_status", ""),
    } for row in inventory]


def build_exclusions(exclusions: list[dict], valid_ids: set[str]) -> list[dict[str, object]]:
    return [{
        "mutant_id": row.get("mutant_id", ""),
        "operator": row.get("operator", ""),
        "source_golden": row.get("source_golden", ""),
        "status": row.get("status", ""),
        "verdict": row.get("verdict", ""),
        "reason": row.get("reason", ""),
        "action_taken": row.get("action_taken", ""),
        "present_in_valid_manifest": row.get("mutant_id", "") in valid_ids,
        "decision_date": "2026-09-25",
        "rule_timing": "AFTER_DISCOVERY_REVIEW; not prospective/preregistered",
    } for row in exclusions]


def build_control_results(controls: list[dict], runs: list[dict]) -> list[dict[str, object]]:
    baseline_by_key = {
        (run.get("source_golden"), run.get("validator")): run
        for run in runs
        if run.get("baseline_or_mutant") == "golden_baseline"
    }

    def note_count(run: dict, field: str) -> int:
        match = re.search(rf"{re.escape(field)}=(\d+)", run.get("notes", ""))
        return int(match.group(1)) if match else 0

    results = []
    for row in controls:
        source_id = Path(row.get("source_pdf", "")).stem
        pac = baseline_by_key.get((source_id, "PAC"), {})
        acrobat = baseline_by_key.get((source_id, "Acrobat"), {})
        vera = baseline_by_key.get((source_id, "veraPDF"), {})
        comparisons = [
            int(row.get("pac_failed_rules", "0")) == note_count(pac, "automated_failure_count"),
            int(row.get("acrobat_failed_rules", "0")) == note_count(acrobat, "automated_failure_count"),
            int(row.get("verapdf_failed_rules", "0")) == note_count(vera, "failed_rule_count"),
            int(row.get("acrobat_manual_rules", "0")) == note_count(acrobat, "manual_check_count"),
        ]
        baseline_counts = [note_count(pac, "automated_failure_count"), note_count(acrobat, "automated_failure_count"), note_count(vera, "failed_rule_count")]
        results.append({
            "control_id": row.get("control_id", ""),
            "control_type": row.get("control_type", ""),
            "source_pdf": row.get("source_pdf", ""),
            "output_pdf": row.get("output_pdf", ""),
            "expected_result": row.get("expected_result", ""),
            "artifact_status": row.get("status", ""),
            "pac_failed_rules": row.get("pac_failed_rules", ""),
            "pac_warned_rules": row.get("pac_warned_rules", ""),
            "acrobat_failed_rules": row.get("acrobat_failed_rules", ""),
            "acrobat_manual_rules": row.get("acrobat_manual_rules", ""),
            "verapdf_failed_rules": row.get("verapdf_failed_rules", ""),
            "new_target_relevant_finding": "NONE_OBSERVED_BY_PAIRED_COUNT_COMPARISON" if all(comparisons) else "POTENTIAL_NEW_FINDING_REQUIRES_REVIEW",
            "baseline_findings_persisted": "NO_BASELINE_FAILURE" if all(value == 0 for value in baseline_counts) else ("YES_UNCHANGED" if all(comparisons) else "CHANGED_REQUIRES_REVIEW"),
            "evidence_paths": ";".join(filter(None, [row.get("evidence_path", ""), row.get("pac_report_path", ""), row.get("acrobat_report_path", ""), row.get("verapdf_report_path", "")])),
            "notes": row.get("notes", "") + " Pairwise comparison is count-based; named-rule details remain in native reports.",
        })
    return results


def main() -> int:
    active, exclusions, valid_ids, excluded_ids = active_records()
    mutants = read_jsonl(DATA / "mutants.jsonl")
    runs = read_csv(DATA / "validator_runs.csv")
    corpus = read_csv(DATA / "corpus_inventory.csv")
    provenance = read_csv(DATA / "corpus_provenance_sources.csv")
    controls = read_csv(DATA / "controls.csv")
    specs = operator_specs()
    active_ids = {row["mutant_id"] for row in active}
    formal = [
        row for row in runs
        if row.get("baseline_or_mutant") == "mutant"
        and row.get("artifact_id") in active_ids
        and row.get("configuration") in FORMAL_CONFIGS
    ]
    classified = [row for row in formal if row.get("detection_classification") in CLASSIFICATIONS]
    evidence_missing = []
    mutant_by_id = {row["mutant_id"]: row for row in mutants}
    for row in formal:
        mutant = mutant_by_id.get(row.get("artifact_id"), {})
        mutant_path = ROOT / mutant.get("mutant_pdf", "")
        source_path = ROOT / mutant.get("source_pdf", "")
        report_path = ROOT / row.get("raw_report_path", "")
        missing = []
        if not mutant_path.is_file() or sha256(mutant_path) != mutant.get("mutant_sha256"): missing.append("mutant_hash")
        if not source_path.is_file() or sha256(source_path) != mutant.get("source_sha256"): missing.append("baseline_hash")
        if not report_path.is_file() or sha256(report_path) != row.get("report_sha256"): missing.append("raw_report")
        if not row.get("detection_classification"): missing.append("classification")
        if not row.get("coder_1") or not row.get("coder_2") or not row.get("adjudication"): missing.append("coding")
        if missing:
            evidence_missing.append({"record_id": row.get("record_id", ""), "missing": missing})

    outcomes = defaultdict(Counter)
    operator_outcomes = defaultdict(Counter)
    for row in classified:
        outcomes[row.get("validator", "")][row.get("detection_classification", "")] += 1
        operator_outcomes[row.get("operator", "") + ":" + row.get("validator", "")][row.get("detection_classification", "")] += 1

    independent_dir = EVIDENCE / "independent_verification_v2"
    independent = [json.loads(path.read_text(encoding="utf-8")) for path in independent_dir.glob("*.json")] if independent_dir.is_dir() else []
    at_rows = read_csv(DATA / "at_observations.csv")
    ai_rows = read_csv(DATA / "pac_ai_classifications.csv")
    double_rows = read_csv(DATA / "double_coding_decisions.csv")
    disagreement_rows = read_csv(ROOT / "analysis" / "generated" / "disagreement_analysis.csv")

    manifest = {
        "manifest_version": "1.0",
        "status": "AUDIT_DERIVED_NOT_PAPER_FROZEN",
        "generated_by": "scripts/build_study_manifest.py",
        "repository": {
            "git_head": git_value("rev-parse", "HEAD"),
            "git_branch": git_value("branch", "--show-current"),
            "worktree_dirty": bool(git_value("status", "--porcelain")),
        },
        "study_scope": "Controlled structure-level mutations applied to PDF/UA Reference Suite reference baselines; formal checker outcomes are mutation-specific and configuration-scoped.",
        "canonical_inputs": [
            "operators/operators.yaml", "data/mutants.jsonl", "data/mutant_exclusions.csv", "data/validator_runs.csv",
            "data/corpus_inventory.csv", "data/corpus_provenance_sources.csv", "data/controls.csv", "data/at_observations.csv",
        ],
        "counts": {
            "golden_reference_pdfs": len(list((ROOT / "corpus" / "golden").glob("*.pdf"))),
            "generation_records": len(mutants),
            "generated_mutant_pdf_files": len(list((ROOT / "corpus" / "mutants").glob("*.pdf"))),
            "valid_verified_mutants": len(valid_ids),
            "documented_exclusions": len(exclusions),
            "excluded_ids_in_valid_manifest": sorted(valid_ids & excluded_ids),
            "excluded_records_in_manifest": sum(row.get("status") == "excluded" for row in mutants),
            "active_mutants": len(active),
            "formal_rows": len(formal),
            "classified_formal_rows": len(classified),
            "formal_rows_per_validator": {validator: sum(row.get("validator") == validator for row in classified) for validator in ("PAC", "Acrobat", "veraPDF")},
            "controls": len(controls),
            "at_observations": len(at_rows),
            "at_complete": sum(row.get("status") == "COMPLETE" for row in at_rows),
            "pac_ai_rows": len(ai_rows),
            "formal_double_coded_rows": sum(bool(row.get("coder_1") and row.get("coder_2") and row.get("adjudication")) for row in formal),
            "disagreement_rows": len(disagreement_rows),
            "disagreement_by_cause": dict(sorted(Counter(row.get("cause_category", "UNSPECIFIED") for row in disagreement_rows).items())),
        },
        "mutants_per_operator": dict(sorted(Counter(row["operator"] for row in active).items())),
        "mutants_per_class": dict(sorted(Counter("class_a" if specs[row["operator"]].get("class") == "class_a" else "class_b" for row in active).items())),
        "excluded_mutants": build_exclusions(exclusions, valid_ids),
        "formal_outcomes": {validator: dict(sorted(counts.items())) for validator, counts in sorted(outcomes.items())},
        "formal_operator_outcomes": {key: dict(sorted(counts.items())) for key, counts in sorted(operator_outcomes.items())},
        "evidence": {
            "active_formal_rows_with_missing_evidence": evidence_missing,
            "active_formal_rows_missing_evidence_count": len(evidence_missing),
            "independent_verification_rows": len(independent),
            "independent_structure_status": dict(Counter(row.get("independent_structure_status", "MISSING") for row in independent)),
            "validator_evidence_check_command": "python scripts/check_evidence.py",
        },
        "coding_provenance": {
            "status": "ROLE_LABELED_DECISIONS_AND_ADJUDICATION_RETAINED_AS_INTERNAL_AUDIT_PROVENANCE",
            "independent_human_claim": False,
            "identity_provenance_available": False,
            "public_reporting_rule": "Do not report independent-coder identity, independence, or agreement statistics as a study claim.",
        },
        "environment_files": ["data/pac_formal_run_metadata.json", "data/acrobat_run_metadata.json", "data/verapdf_setup.json", "data/validator_environment.csv"],
        "paper_artifacts": {
            "source": {"path": rel(ROOT / "paper" / "pdfa11ymut_ieee.tex"), "sha256": sha256(ROOT / "paper" / "pdfa11ymut_ieee.tex")},
            "pdf": {"path": rel(ROOT / "paper" / "pdfa11ymut_ieee.pdf"), "sha256": sha256(ROOT / "paper" / "pdfa11ymut_ieee.pdf")},
            "paper_pdf_accessibility_status": "TAGGED_SEMANTIC_STRUCTURE_REVIEW_PASSED_LOCAL_GATE_2026-09-25",
        },
        "reproduction_commands": [
            "python scripts/build_study_manifest.py",
            "python scripts/rebuild_analysis.py",
            "python scripts/verify_study_state.py --verify",
            "python scripts/check_evidence.py",
            "python -m unittest discover -s tests -p \"test*.py\" -q",
        ],
        "notes": [
            "Legacy 23-mutant summaries are historical and are not read.",
            "PAC AI remains separate and is not part of formal rates.",
            "A manually generated Invoice-M01 PDF is used in AT evidence but has no active data/mutants.jsonl generation record; it is not in the formal denominator.",
            "An exact acquisition archive/timestamp for the local reference PDFs was not retained.",
            "Three newly generated reachable-target M09 candidates are valid generation records but remain excluded because they cannot replace historical validator evidence; see data/m09_recovery_candidates.csv.",
        ],
    }
    (ROOT / "STUDY_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    write_csv(DATA / "baseline_provenance.csv", build_baseline_provenance(corpus, provenance), [
        "artifact_id", "local_filename", "source", "suite_identifier", "official_filename", "sha256", "license",
        "acquisition_provenance", "source_url", "provenance_status", "page_count", "baseline_status",
    ])
    write_csv(DATA / "exclusions.csv", build_exclusions(exclusions, valid_ids), [
        "mutant_id", "operator", "source_golden", "status", "verdict", "reason", "action_taken",
        "present_in_valid_manifest", "decision_date", "rule_timing",
    ])
    write_csv(DATA / "operator_standard_mapping.csv", build_standard_mapping(specs), [
        "operator", "description", "operator_class", "target_structure", "accessibility_property", "pdfua_relationship",
        "iso_clause_or_requirement", "matterhorn_or_technique", "machine_or_human_status", "expected_checker_capability",
        "class_rationale", "source_reference", "mapping_status",
    ])
    write_csv(DATA / "operator_target_selection.csv", build_target_selection(active, specs, common_target_selection_rule()), [
        "mutant_id", "operator", "source_golden", "source_sha256", "requested_target", "selection_rule",
        "eligible_candidate_count", "eligible_candidate_refs", "chosen_target", "target_precondition_status",
        "target_reachability_status", "mutant_sha256",
    ])
    delta_path = DATA / "mutant_delta_manifest.jsonl"
    delta_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in build_delta_manifest(active, specs)), encoding="utf-8")
    write_csv(DATA / "control_results.csv", build_control_results(controls, runs), [
        "control_id", "control_type", "source_pdf", "output_pdf", "expected_result", "artifact_status",
        "pac_failed_rules", "pac_warned_rules", "acrobat_failed_rules", "acrobat_manual_rules", "verapdf_failed_rules",
        "new_target_relevant_finding", "baseline_findings_persisted", "evidence_paths", "notes",
    ])
    write_csv(DATA / "validator_environment.csv", build_environment_rows(), [
        "component", "version", "configuration", "settings", "source",
    ])
    print(json.dumps(manifest["counts"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
