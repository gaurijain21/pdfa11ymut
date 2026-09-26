"""Build the second-pass audit artifacts from canonical study inputs.

This script is intentionally descriptive: it does not change mutant validity,
validator classifications, exclusions, or the manuscript's scientific scope.
It emits reproducibility and traceability views that are safe to regenerate.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ANALYSIS = ROOT / "analysis"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text_lf(path: Path, text: str) -> None:
    """Write generated text with stable LF line endings on every platform."""
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def build_applicability() -> None:
    mutants = [json.loads(line) for line in (DATA / "mutants.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    exclusions = {r["mutant_id"] for r in read_csv(DATA / "mutant_exclusions.csv") if r.get("status")}
    failures = [json.loads(line) for line in (DATA / "generation_failures.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    sources = {r["artifact_id"] for r in read_csv(DATA / "corpus_inventory.csv")}
    operators = [f"M{i:02d}" for i in range(1, 11)]
    rows = []
    for op in operators:
        op_records = [r for r in mutants if r.get("operator") == op]
        applicable = [r for r in op_records if r.get("status") == "valid" or r.get("generation_status") in {"valid", "excluded"}]
        generated = [r for r in op_records if r.get("status") == "valid"]
        active = [r for r in generated if r.get("mutant_id") not in exclusions and r.get("verification", {}).get("mutation_valid") is True]
        fail_count = sum(1 for r in failures if r.get("operator") == op)
        rows.append({
            "operator": op,
            "baseline_pdfs": len(sources),
            "applicable_baselines_or_records": len(applicable),
            "successful_generation_records": len(generated),
            "generation_failure_records": fail_count,
            "documented_exclusions": sum(1 for r in exclusions if r.startswith("PDFUA-Ref-2-") and f"-{op}" in r),
            "active_mutants": len(active),
            "selection_rule": "first eligible reachable target in stable structure traversal order",
            "denominator_note": "applicable count is record-based because generation ledger retains only applicable attempts; active excludes documented exclusions",
        })
    write_csv(DATA / "operator_applicability.csv", rows, list(rows[0]))


def build_capability() -> None:
    mapping = {r["operator"]: r for r in read_csv(DATA / "operator_standard_mapping.csv")}
    validators = [
        ("PAC", "26.1.0.0", "Formal", "REQUIRES_USER_VERIFICATION", "PAC Formal report export; data/pac_formal_run_metadata.json"),
        ("Acrobat", "2026.002.21931", "Full Check", "31-of-32 native-session configuration", "Acrobat native-session note; data/acrobat_run_metadata.json"),
        ("veraPDF", "1.30.2", "PDF/UA-1 ua1", "ua1", "data/verapdf_setup.json; official veraPDF PDF/UA profile documentation"),
    ]
    class_a = {"M03", "M07", "M08", "M09", "M10"}
    rows = []
    for op in [f"M{i:02d}" for i in range(1, 11)]:
        m = mapping[op]
        for validator, version, config, profile, source in validators:
            if op not in class_a:
                expected = "NO"; coverage = "outside formal automated obligation; semantic/representation property"
            elif op == "M10" and validator == "Acrobat":
                expected = "CONDITIONAL"; coverage = "profile/check-specific; Headers proxy is separately validated"
            else:
                expected = "YES"; coverage = "documented machine-oriented/profile-specific condition in study"
            rows.append({
                "validator": validator,
                "version": version,
                "configuration": config,
                "operator": op,
                "relevant_rule": m.get("matterhorn_or_technique", "see operator mapping"),
                "machine_checkable": m.get("machine_or_human_status", "YES" if op in class_a else "NO_OR_UNESTABLISHED"),
                "validator_claims_coverage": coverage,
                "expected_automated_detection": expected,
                "evidence_source": source,
            })
    write_csv(DATA / "validator_capability_mapping.csv", rows, list(rows[0]))


def build_leave_one_out() -> None:
    rows = read_csv(ANALYSIS / "generated" / "formal_results_freeze.csv")
    class_a = {r["artifact_id"] for r in rows if r["operator"] in {"M03", "M07", "M08", "M09", "M10"}}
    sources = sorted({r["source_golden"] for r in rows})
    validators = ["PAC", "Acrobat", "veraPDF"]
    output = []
    for source in sources:
        for validator in validators:
            kept = [r for r in rows if r["source_golden"] != source and r["validator"] == validator and r["artifact_id"] in class_a]
            detected = sum(1 for r in kept if r["interpreted_outcome"] in {"DIRECT_OR_VALIDATED_TARGET_DETECTION", "CONSEQUENCE_PROXY_DETECTION"})
            proxy = sum(1 for r in kept if r["interpreted_outcome"] == "CONSEQUENCE_PROXY_DETECTION")
            direct = detected - proxy
            manual = sum(1 for r in kept if r["interpreted_outcome"] == "MANUAL_REVIEW")
            no_target = len(kept) - detected - manual
            output.append({
                "excluded_baseline": source,
                "validator": validator,
                "class_scope": "Class A",
                "remaining_rows": len(kept),
                "direct_kills": direct,
                "proxy_kills": proxy,
                "approved_kills_direct_plus_proxy": detected,
                "manual_review": manual,
                "no_target_finding": no_target,
                "automated_denominator": detected + no_target,
                "approved_kill_rate": f"{detected / (detected + no_target):.6f}" if detected + no_target else "",
                "conclusion_stable": "YES" if detected + no_target and detected > 0 else "NO_OR_NOT_ESTIMABLE",
                "interpretation": "Descriptive leave-one-baseline-out sensitivity; mutants from one source are removed together.",
            })
    write_csv(ANALYSIS / "leave_one_source_out.csv", output, list(output[0]))


def build_checksums() -> None:
    paths: set[Path] = set()
    for pattern in ["corpus/golden/*.pdf", "corpus/mutants/*.pdf", "corpus/controls/*.pdf", "evidence/pac/**/*.pdf", "evidence/acrobat/**/*.html", "evidence/verapdf/**/*.json", "evidence/controls/**/*.pdf", "evidence/controls/**/*.json", "evidence/controls/**/*.html", "evidence/at/**/*.txt", "evidence/at/**/*.png", "evidence/independent_verification/**/*.json", "evidence/independent_verification_v2/**/*.json"]:
        paths.update(ROOT.glob(pattern))
    # Mismatch backups are private debugging artifacts and are excluded from
    # the public boundary; they must not become checksum requirements.
    paths = {path for path in paths if ".mismatch-backup-" not in path.name}
    # Include canonical ledgers and manifests, but not the checksum file itself.
    for rel in ["STUDY_MANIFEST.json", "data/mutants.jsonl", "data/mutant_exclusions.csv", "data/validator_runs.csv", "data/controls.csv", "data/control_results.csv", "data/at_observations.csv", "data/operator_target_selection.csv", "data/mutant_delta_manifest.jsonl", "paper/pdfa11ymut_ieee.tex", "paper/pdfa11ymut_ieee.pdf"]:
        if (ROOT / rel).is_file(): paths.add(ROOT / rel)
    lines = []
    for path in sorted(paths):
        lines.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    write_text_lf(DATA / "evidence_checksums.sha256", "# Generated by scripts/build_second_pass_artifacts.py\n" + "\n".join(lines) + "\n")


def main() -> None:
    build_applicability()
    build_capability()
    build_leave_one_out()
    build_checksums()
    print(json.dumps({"status": "PASS", "outputs": ["data/operator_applicability.csv", "data/validator_capability_mapping.csv", "analysis/leave_one_source_out.csv", "data/evidence_checksums.sha256"]}, indent=2))


if __name__ == "__main__":
    main()
