"""Fail-closed consistency audit for the evidence-backed study freeze.

This check validates relationships among canonical inputs, derived tables, and
hash-linked evidence. It deliberately does not decide unresolved scientific
questions such as whether a semantic mutation is machine-checkable.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FORMAL_VALIDATORS = {"PAC", "Acrobat", "veraPDF"}
FORMAL_CONFIGS = {"Formal", "Full Check", "PDF/UA-1 ua1"}

CSV_SCHEMAS: dict[str, tuple[list[str], str, set[str]]] = {
    "control_results.csv": (["control_id", "control_type", "source_pdf", "output_pdf", "expected_result", "artifact_status", "pac_failed_rules", "pac_warned_rules", "acrobat_failed_rules", "acrobat_manual_rules", "verapdf_failed_rules", "new_target_relevant_finding", "baseline_findings_persisted", "evidence_paths", "notes"], "control_id", {"control_type": {"no-op", "benign"}, "artifact_status": {"COMPLETE"}}),
    "controls.csv": (["control_id", "control_type", "source_pdf", "output_pdf", "expected_result", "status", "evidence_path", "notes", "verapdf_report_path", "verapdf_report_sha256", "verapdf_version", "verapdf_profile", "verapdf_exit_code", "verapdf_failed_rules", "verapdf_passed_rules", "verapdf_parse_status", "pac_report_path", "pac_report_sha256", "pac_version", "pac_profile", "pac_failed_rules", "pac_warned_rules", "pac_parse_status", "acrobat_report_path", "acrobat_report_sha256", "acrobat_version", "acrobat_profile", "acrobat_passed_rules", "acrobat_failed_rules", "acrobat_manual_rules", "acrobat_skipped_rules", "acrobat_parse_status"], "control_id", {"control_type": {"no-op", "benign"}, "status": {"COMPLETE"}}),
    "at_observations.csv": (["record_id", "artifact_id", "source_golden", "mutant_id", "operator", "at_name", "at_version", "viewer", "viewer_version", "os_version", "procedure", "expected_golden_behavior", "expected_mutant_behavior", "exact_at_observation", "golden_observation", "mutant_observation", "observation", "evidence_path", "golden_sha256", "mutant_sha256", "status", "coder_1", "coder_2", "agree", "adjudication", "notes", "raw_log_path", "raw_log_sha256", "raw_log_interval", "screenshot_path"], "record_id", {"status": {"COMPLETE"}}),
    "at_observation_categories.csv": (["record_id", "mutant_id", "operator", "artifact_category", "formal_denominator_inclusion", "notes"], "record_id", {"artifact_category": {"ACTIVE_FORMAL_MUTANT", "AUXILIARY_AT_ARTIFACT"}, "formal_denominator_inclusion": {"YES", "NO"}}),
    "at_selection.csv": (["artifact_id", "source_golden", "mutant_id", "operator", "selected_golden", "reason", "expected_golden_behavior", "expected_mutant_behavior", "exact_at_observation", "status"], "artifact_id", {"status": {"COMPLETE"}}),
    "corpus_inventory.csv": (["artifact_id", "filename", "original_filename", "source_collection", "source_reference", "collection_version", "license", "attribution_requirement", "redistribution_status", "pdf_version", "pdfua_version", "page_count", "sha256", "document_genre", "relevant_structural_features", "baseline_status", "baseline_evidence_path", "baseline_notes", "notes"], "artifact_id", {"baseline_status": {"PASS", "BASELINE_PASS", "REVIEW_REQUIRED", "BASELINE_EVIDENCE_PRESENT", "BASELINE_EVIDENCE_PRESENT_WITH_DOCUMENTED_DELTA", "BASELINE_EVIDENCE_PRESENT_WITH_TOOL_CONFLICT"}}),
    "corpus_provenance_sources.csv": (["artifact_id", "source_item_id", "official_filename", "source_title_or_description", "listed_contributor_or_context", "source_index_url", "download_url", "mapping_basis", "local_hash_evidence", "license_basis", "provenance_status", "notes"], "artifact_id", {}),
    "baseline_deltas.csv": (["record_id", "artifact_id", "source_golden", "validator", "configuration", "baseline_status", "baseline_run_id", "baseline_file_sha256", "mutant_file_sha256", "delta_state", "notes"], "record_id", {}),
    "mutant_exclusions.csv": (["mutant_id", "operator", "source_golden", "status", "verdict", "reason", "action_taken"], "mutant_id", {}),
    "exclusions.csv": (["mutant_id", "operator", "source_golden", "status", "verdict", "reason", "action_taken", "present_in_valid_manifest", "decision_date", "rule_timing"], "mutant_id", {}),
    "m09_recovery_candidates.csv": (["historical_mutant_id", "operator", "source_golden", "historical_expected_sha256", "recovery_status", "recovery_candidate_sha256", "recovery_candidate_path", "reason_not_promoted", "validator_rerun_required"], "historical_mutant_id", {}),
    "operator_applicability.csv": (["operator", "baseline_pdfs", "applicable_baselines_or_records", "successful_generation_records", "generation_failure_records", "documented_exclusions", "active_mutants", "selection_rule", "denominator_note"], "operator", {}),
    "operator_standard_mapping.csv": (["operator", "description", "operator_class", "target_structure", "accessibility_property", "pdfua_relationship", "iso_clause_or_requirement", "matterhorn_or_technique", "machine_or_human_status", "expected_checker_capability", "class_rationale", "source_reference", "mapping_status"], "operator", {"operator_class": {"class_a", "class_b"}}),
    "operator_target_selection.csv": (["mutant_id", "operator", "source_golden", "source_sha256", "requested_target", "selection_rule", "eligible_candidate_count", "eligible_candidate_refs", "chosen_target", "target_precondition_status", "target_reachability_status", "mutant_sha256"], "mutant_id", {"target_precondition_status": {"PASS"}, "target_reachability_status": {"PASS"}}),
    "validator_capability_mapping.csv": (["validator", "version", "configuration", "operator", "relevant_rule", "machine_checkable", "validator_claims_coverage", "expected_automated_detection", "evidence_source"], "validator|operator", {}),
    "validator_environment.csv": (["component", "version", "configuration", "settings", "source"], "component|configuration", {}),
    "validator_runs.csv": (["record_id", "artifact_id", "baseline_or_mutant", "source_golden", "operator", "file_sha256", "validator", "configuration", "validator_version", "build", "platform", "profile", "PAC_AI_enabled", "run_timestamp", "automated_pass_fail", "relevant_rule_ids", "relevant_rule_text", "manual_check_prompts", "raw_report_path", "report_sha256", "raw_detection_classification", "baseline_status", "baseline_file_sha256", "baseline_run_id", "detection_classification", "classification_reason", "coder_1", "coder_2", "adjudication", "notes"], "record_id", {}),
    "public_evidence_records.csv": (["record_id", "mutant_id", "source_golden", "operator", "validator", "configuration", "validator_version", "build", "profile", "baseline_sha256", "mutant_sha256", "baseline_state", "mutant_classification", "relevant_rule_ids", "raw_evidence_sha256", "rationale", "redistribution_note"], "record_id", {}),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_csv_schemas(errors: list[str]) -> None:
    """Fail closed on malformed canonical CSV records before semantic checks."""
    for filename, (expected_header, unique_key, enums) in CSV_SCHEMAS.items():
        path = DATA / filename
        if not path.is_file():
            fail(errors, f"canonical CSV is missing: data/{filename}")
            continue
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                fail(errors, f"canonical CSV is empty: data/{filename}")
                continue
            if header != expected_header:
                fail(errors, f"data/{filename} has the wrong header")
                continue
            keys: set[str] = set()
            for line_number, values in enumerate(reader, start=2):
                if len(values) != len(header):
                    fail(errors, f"data/{filename} row {line_number} has {len(values)} columns; expected {len(header)}")
                    continue
                row = dict(zip(header, values))
                key = "|".join(row.get(part, "") for part in unique_key.split("|"))
                if unique_key and (not key or any(not row.get(part, "").strip() for part in unique_key.split("|"))):
                    fail(errors, f"data/{filename} row {line_number} has an empty unique key")
                elif unique_key and key in keys:
                    fail(errors, f"data/{filename} has duplicate key {key}")
                keys.add(key)
                for field, allowed in enums.items():
                    if row.get(field, "") not in allowed:
                        fail(errors, f"data/{filename} row {line_number} has invalid {field}={row.get(field, '')!r}")


def main() -> int:
    errors: list[str] = []
    manifest_path = ROOT / "STUDY_MANIFEST.json"
    if not manifest_path.is_file():
        print("FAIL: STUDY_MANIFEST.json is missing")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    public_boundary = manifest.get("public_artifact_boundary", {}).get("raw_native_evidence_excluded") is True
    public_records = read_csv(DATA / "public_evidence_records.csv") if (DATA / "public_evidence_records.csv").is_file() else []
    public_records_by_id = {row.get("record_id"): row for row in public_records}
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    current_dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip())
    recorded_repo = manifest.get("repository", {})
    recorded_head = recorded_repo.get("git_head")
    commit_boundary = False
    if recorded_head != current_head and not current_dirty:
        # Permit clean descendant commits that only carry post-freeze packaging
        # or audit fixes while keeping the frozen scientific commit authoritative.
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", recorded_head, current_head],
            cwd=ROOT,
            check=False,
        )
        commit_boundary = ancestry.returncode == 0
    if recorded_head != current_head and not commit_boundary:
        fail(errors, f"manifest git_head={recorded_repo.get('git_head')} but current HEAD={current_head}")
    recorded_dirty = recorded_repo.get("worktree_dirty")
    if recorded_dirty is not current_dirty and not commit_boundary:
        fail(errors, f"manifest worktree_dirty={recorded_repo.get('worktree_dirty')} but current state is {current_dirty}")
    manifest_status = manifest.get("status")
    if current_dirty and manifest_status == "PAPER_FROZEN":
        fail(errors, "paper-frozen manifest is attached to a dirty worktree")
    if not current_dirty and manifest_status != "PAPER_FROZEN":
        fail(errors, f"clean worktree requires manifest status PAPER_FROZEN, found {manifest_status}")
    if not current_dirty and manifest_status == "PAPER_FROZEN":
        if recorded_repo.get("scientific_state_commit") != recorded_head or recorded_repo.get("scientific_state_clean") is not True:
            fail(errors, "frozen manifest must identify a clean scientific_state_commit")
    validate_csv_schemas(errors)
    paper_meta = manifest.get("paper_artifacts", {})
    for key, relative in (("source", "paper/pdfa11ymut_ieee.tex"), ("pdf", "paper/pdfa11ymut_ieee.pdf")):
        path = ROOT / relative
        expected = paper_meta.get(key, {}).get("sha256")
        if path.is_file() and expected and sha256(path) != expected:
            fail(errors, f"manifest hash mismatch for {relative}")
    mutants = read_jsonl(DATA / "mutants.jsonl")
    exclusions = read_csv(DATA / "mutant_exclusions.csv")
    runs = read_csv(DATA / "validator_runs.csv")
    active_valid = [
        row for row in mutants
        if str(row.get("status", "")).lower() == "valid"
        and row.get("verification", {}).get("mutation_valid") is True
        and row.get("mutant_id") not in {x.get("mutant_id") for x in exclusions if x.get("status")}
    ]
    valid = [
        row for row in mutants
        if str(row.get("status", "")).lower() == "valid"
        and row.get("verification", {}).get("mutation_valid") is True
    ]
    active_ids = {row["mutant_id"] for row in active_valid}
    if len({row.get("mutant_id") for row in mutants}) != len(mutants):
        fail(errors, "mutants.jsonl contains duplicate mutant IDs")
    if len(active_valid) != manifest["counts"]["active_mutants"]:
        fail(errors, f"manifest active_mutants={manifest['counts']['active_mutants']} but computed {len(active_valid)}")
    if len(valid) != manifest["counts"]["valid_verified_mutants"]:
        fail(errors, f"manifest valid_verified_mutants={manifest['counts']['valid_verified_mutants']} but computed {len(valid)}")
    if len(exclusions) != manifest["counts"]["documented_exclusions"]:
        fail(errors, "manifest documented exclusion count is stale")
    for row in exclusions:
        if not row.get("mutant_id") or not row.get("status") or not row.get("reason"):
            fail(errors, f"exclusion is undocumented: {row}")

    # Hash-linked artifact checks for every active mutant.
    for row in active_valid:
        mutant_id = row["mutant_id"]
        for field in ("source_pdf", "mutant_pdf"):
            path = ROOT / row[field]
            if not path.is_file():
                fail(errors, f"{mutant_id} missing {field}: {row[field]}")
        if (ROOT / row["source_pdf"]).is_file() and sha256(ROOT / row["source_pdf"]) != row.get("source_sha256"):
            fail(errors, f"{mutant_id} source hash mismatch")
        if (ROOT / row["mutant_pdf"]).is_file() and sha256(ROOT / row["mutant_pdf"]) != row.get("mutant_sha256"):
            fail(errors, f"{mutant_id} mutant hash mismatch")
        audit_path = ROOT / "evidence" / "independent_verification_v2" / f"{mutant_id}.json"
        if not audit_path.is_file():
            fail(errors, f"{mutant_id} missing independent verification record")

    # Formal validator ledger completeness and report hashes.
    active_formal = [
        row for row in runs
        if row.get("artifact_id") in active_ids
        and row.get("baseline_or_mutant") == "mutant"
        and row.get("validator") in FORMAL_VALIDATORS
        and row.get("configuration") in FORMAL_CONFIGS
    ]
    expected_rows = len(active_valid) * len(FORMAL_VALIDATORS)
    if len(active_formal) != expected_rows:
        fail(errors, f"formal ledger has {len(active_formal)} active rows; expected {expected_rows}")
    by_validator = Counter(row.get("validator") for row in active_formal)
    for validator in sorted(FORMAL_VALIDATORS):
        if by_validator[validator] != len(active_valid):
            fail(errors, f"{validator} has {by_validator[validator]} active rows; expected {len(active_valid)}")
    seen_records = set()
    for row in active_formal:
        record_id = row.get("record_id")
        if record_id in seen_records:
            fail(errors, f"duplicate validator record ID: {record_id}")
        seen_records.add(record_id)
        report = ROOT / row.get("raw_report_path", "")
        if not report.is_file():
            sanitized = public_records_by_id.get(record_id)
            if not (public_boundary and sanitized and sanitized.get("raw_evidence_sha256") == row.get("report_sha256")):
                fail(errors, f"{record_id} missing raw report: {row.get('raw_report_path')}")
        elif row.get("report_sha256") and sha256(report) != row["report_sha256"]:
            fail(errors, f"{record_id} raw report hash mismatch")
        if not row.get("file_sha256") or not row.get("baseline_file_sha256"):
            fail(errors, f"{record_id} lacks mutant or baseline hash")
        if not row.get("detection_classification") or not row.get("classification_reason"):
            fail(errors, f"{record_id} lacks classification evidence")
    if public_boundary:
        active_formal_ids = {row.get("record_id") for row in active_formal}
        if active_formal_ids != set(public_records_by_id):
            fail(errors, "public sanitized evidence ledger does not cover exactly the active formal rows")

    # All ten operators and all active targets must be represented by the
    # machine-readable derived views.
    mapping = read_csv(DATA / "operator_standard_mapping.csv")
    selection = read_csv(DATA / "operator_target_selection.csv")
    delta_path = DATA / "mutant_delta_manifest.jsonl"
    delta_rows = read_jsonl(delta_path) if delta_path.is_file() else []
    operators = {f"M{i:02d}" for i in range(1, 11)}
    if {row.get("operator") for row in mapping} != operators:
        fail(errors, "operator_standard_mapping.csv does not contain exactly M01-M10")
    if {row.get("mutant_id") for row in selection} != active_ids:
        fail(errors, "operator_target_selection.csv does not cover exactly the active mutant IDs")
    if len({row.get("mutant_id") for row in selection}) != len(selection):
        fail(errors, "operator_target_selection.csv contains duplicate mutant IDs")
    if {row.get("mutant_id") for row in delta_rows} != active_ids:
        fail(errors, "mutant_delta_manifest.jsonl does not cover exactly the active mutant IDs")
    if any(not row.get("allowed_changes") or not row.get("required_invariants") for row in delta_rows):
        fail(errors, "mutant delta manifest has an active row without allowed changes or required invariants")

    # Generated overall rates must state a denominator that can be recomputed
    # from its displayed categories. Manual rows are not silently included in
    # an automated detection rate.
    rates_path = ROOT / "analysis" / "generated" / "overall_rates.csv"
    if rates_path.is_file():
        for row in read_csv(rates_path):
            detected = int(row["detected"])
            missed = int(row["missed"])
            manual = int(row["needs_manual_check"])
            total = int(row["total_with_classification"])
            if detected + missed + manual + int(row["not_applicable"]) != total:
                fail(errors, f"{row['validator']} overall categories do not sum to total")
            expected_rate = detected / (detected + missed) if detected + missed else ""
            actual_rate = row.get("rate", "")
            if expected_rate == "" and actual_rate:
                fail(errors, f"{row['validator']} rate has no automated denominator")
            elif expected_rate != "" and not math.isclose(float(actual_rate), expected_rate, rel_tol=0, abs_tol=0.0002):
                fail(errors, f"{row['validator']} rate denominator is inconsistent")

    # Active README/manuscript count guard. Historical directories are allowed
    # to retain old numbers, but the two current-facing artifacts must expose
    # the manifest-derived study state and must not revive the old 23-mutant
    # experiment or the superseded class split.
    current_facing = {
        "README.md": ROOT / "README.md",
        "paper/pdfa11ymut_ieee.tex": ROOT / "paper" / "pdfa11ymut_ieee.tex",
    }
    required_fragments = {
        "73 generation-ledger records": "generation-ledger count",
        "69 active mutants": "active mutant count",
        "Class A contains 30": "Class A count",
        "Class B contains 39": "Class B count",
    }
    forbidden_fragments = {
        "Class A contains 37": "superseded Class A count",
        "Class B contains 32": "superseded Class B count",
        "23-mutant": "historical 23-mutant wording",
    }
    for label, path in current_facing.items():
        if not path.is_file():
            fail(errors, f"current-facing artifact missing: {label}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if label.startswith("paper/"):
            for fragment, description in {
                r"\GenerationLedgerRecords": "generated generation-ledger macro",
                r"\ActiveMutants": "generated active-mutant macro",
                r"\ClassAMutants": "generated Class-A macro",
                r"\ClassBMutants": "generated Class-B macro",
                r"\ATDifferenceCases": "generated AT-difference macro",
                r"\MaterializedMutantArtifacts": "generated materialized-artifact macro",
                r"\ActiveReauditedMutants": "generated active re-audited macro",
                r"\ClassAAcrobatDirect": "generated Acrobat direct-detection macro",
                r"\ClassAAcrobatProxy": "generated Acrobat proxy-detection macro",
                r"\FormalATCases": "generated formal-AT macro",
                r"\AuxiliaryATCases": "generated auxiliary-AT macro",
            }.items():
                if fragment not in text:
                    fail(errors, f"{label} missing {description}")
            for fragment, description in {
                "atomic bad PDF": "informal atomic bad-PDF wording",
                "atomic bad PDFs": "informal atomic bad-PDF wording",
                "validator-clean golden": "overstrong validator-clean terminology",
                "Formal validator results": "superseded all-scope section title",
                "0.0\\%": "scored zero-percent Class-B presentation",
            }.items():
                if fragment in text:
                    fail(errors, f"{label} contains {description}: {fragment}")
        for fragment, description in required_fragments.items():
            if label == "README.md" and fragment not in text:
                fail(errors, f"{label} missing manifest-derived {description}: {fragment}")
        if label == "README.md" and "207 active formal" not in text and "207 classified formal validator rows" not in text and "207 classified formal checker-configuration rows" not in text:
            fail(errors, f"{label} missing manifest-derived formal-row count")
        for fragment, description in forbidden_fragments.items():
            if fragment in text:
                fail(errors, f"{label} contains {description}: {fragment}")

    generated_fragment = ROOT / "analysis" / "generated" / "results_fragment.tex"
    if not generated_fragment.is_file():
        fail(errors, "generated results fragment is missing")
    else:
        generated_text = generated_fragment.read_text(encoding="utf-8", errors="replace")
        if "Mutation-specific checker outcomes" not in generated_text or "Conformance-oriented mutation results" not in generated_text:
            fail(errors, "generated results fragment has stale result section titles")
        if any("Class B" in line and "0.0\\%" in line for line in generated_text.splitlines()):
            fail(errors, "generated results fragment presents Class-B 0.0% as a scored rate")
    operator_fragment = ROOT / "analysis" / "generated" / "operator_table_fragment.tex"
    if not operator_fragment.is_file() or not all(f"{operator:}" in operator_fragment.read_text(encoding="utf-8") for operator in (f"M{i:02d}" for i in range(1, 11))):
        fail(errors, "generated operator table is missing or incomplete")
    current_facing_text = "\n".join((ROOT / path).read_text(encoding="utf-8", errors="replace") for path in ("README.md", "paper/pdfa11ymut_ieee.tex", "SUBMISSION_READINESS.md", "CITATION.cff" ) if (ROOT / path).is_file())
    for phrase in ("independently double-coded", "independent coders", "two independent coders", "representative AT sample"):
        if phrase.lower() in current_facing_text.lower():
            fail(errors, f"current-facing artifact contains unsupported language: {phrase}")
    paper_text = (ROOT / "paper" / "pdfa11ymut_ieee.tex").read_text(encoding="utf-8", errors="replace")
    citation_text = (ROOT / "CITATION.cff").read_text(encoding="utf-8", errors="replace")
    title_match = re.search(r"\\title\{([^}]*)\}", paper_text)
    citation_title_match = re.search(r'^title:\s*"([^"]+)"', citation_text, re.MULTILINE)
    if not title_match or not citation_title_match or title_match.group(1) != citation_title_match.group(1):
        fail(errors, "paper title and CITATION.cff title are inconsistent")
    if not (ROOT / "SUBMISSION_READINESS.md").is_file():
        fail(errors, "current-facing SUBMISSION_READINESS.md is missing")
    if not (ROOT / "docs" / "ANONYMIZATION.md").is_file():
        fail(errors, "docs/ANONYMIZATION.md is missing")
    for required in ("python scripts/regenerate_scratch.py", "final-freeze writer"):
        if required not in (ROOT / "README.md").read_text(encoding="utf-8") or required.replace("_", r"\_") not in (ROOT / "paper" / "pdfa11ymut_ieee.tex").read_text(encoding="utf-8"):
            fail(errors, f"README/manuscript generation-command boundary missing: {required}")
    if not (ROOT / "analysis" / "target_sensitivity" / "target_sensitivity.csv").is_file():
        fail(errors, "alternate-target sensitivity artifact is missing")
    if not (ROOT / "analysis" / "target_sensitivity" / "m09_exclusion_sensitivity.csv").is_file():
        fail(errors, "M09 exclusion sensitivity artifact is missing")

    # AT observations are explicitly split between active formal-mutant cases
    # and auxiliary demonstrations; the auxiliary row must not enter the 69-
    # mutant denominator.
    at_categories = read_csv(DATA / "at_observation_categories.csv") if (DATA / "at_observation_categories.csv").is_file() else []
    at_observations = read_csv(DATA / "at_observations.csv")
    active_at_ids = {row.get("artifact_id") for row in at_observations if row.get("artifact_id") in active_ids}
    category_ids = {row.get("record_id") for row in at_categories}
    if category_ids != {row.get("record_id") for row in at_observations}:
        fail(errors, "AT category ledger does not cover exactly the nine AT observations")
    if sum(row.get("artifact_category") == "ACTIVE_FORMAL_MUTANT" for row in at_categories) != len(active_at_ids):
        fail(errors, "AT active-formal category count is inconsistent with the active mutant ledger")
    if any(row.get("artifact_category") == "AUXILIARY_AT_ARTIFACT" and row.get("formal_denominator_inclusion") != "NO" for row in at_categories):
        fail(errors, "auxiliary AT artifact is marked as part of the formal denominator")

    sensitivity_path = ROOT / "analysis" / "generated" / "detection_sensitivity.csv"
    if sensitivity_path.is_file():
        sensitivity_rows = {row["validator"]: row for row in read_csv(sensitivity_path)}
        expected_acrobat = {"direct_detected": "23", "proxy_detected": "3", "all_detected": "26"}
        if any(sensitivity_rows.get("Acrobat", {}).get(key) != value for key, value in expected_acrobat.items()):
            fail(errors, "Acrobat direct/proxy Class-A sensitivity counts are inconsistent")
    control_rows = read_csv(DATA / "control_results.csv")
    if any(row.get("new_target_relevant_finding") != "NONE_OBSERVED_BY_PAIRED_COUNT_COMPARISON" for row in control_rows):
        fail(errors, "control ledger contains a new target-relevant finding")

    # Second-pass generated views and immutable evidence snapshot.
    applicability = DATA / "operator_applicability.csv"
    capability = DATA / "validator_capability_mapping.csv"
    loo = ROOT / "analysis" / "leave_one_source_out.csv"
    checksums = DATA / "evidence_checksums.sha256"
    if not applicability.is_file():
        fail(errors, "operator_applicability.csv is missing")
    elif len(read_csv(applicability)) != 10:
        fail(errors, "operator_applicability.csv must contain one row per operator")
    if not capability.is_file():
        fail(errors, "validator_capability_mapping.csv is missing")
    else:
        expected_capability_fields = {
            "validator", "version", "configuration", "operator", "relevant_rule",
            "machine_checkable", "validator_claims_coverage", "expected_automated_detection", "evidence_source",
        }
        actual_fields = set(read_csv(capability)[0]) if read_csv(capability) else set()
        if actual_fields != expected_capability_fields:
            fail(errors, "validator_capability_mapping.csv has the wrong schema")
        if len(read_csv(capability)) != 30:
            fail(errors, "validator_capability_mapping.csv must contain 10 operators x 3 configurations")
    if not loo.is_file() or len(read_csv(loo)) != 27:
        fail(errors, "analysis/leave_one_source_out.csv must contain 9 baselines x 3 validators")
    if not checksums.is_file():
        fail(errors, "data/evidence_checksums.sha256 is missing")
    else:
        checksum_lines = [line for line in checksums.read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
        if not checksum_lines:
            fail(errors, "evidence checksum manifest is empty")
        for line in checksum_lines:
            parts = line.split("  ", 1)
            if len(parts) != 2:
                fail(errors, f"malformed evidence checksum line: {line}")
                continue
            expected_hash, relative = parts
            path = ROOT / relative.replace("/", "\\")
            if not path.is_file():
                if public_boundary and relative.replace("\\", "/").startswith("evidence/"):
                    continue
                fail(errors, f"checksum target is missing: {relative}")
            elif sha256(path) != expected_hash:
                fail(errors, f"checksum mismatch: {relative}")

    if errors:
        print(f"FAIL: {len(errors)} consistency issue(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print(json.dumps({
        "status": "PASS",
        "active_mutants": len(active_valid),
        "formal_rows": len(active_formal),
        "formal_rows_per_validator": dict(sorted(by_validator.items())),
        "documented_exclusions": len(exclusions),
        "operator_mapping_rows": len(mapping),
        "target_selection_rows": len(selection),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
