"""Build the formal-result freeze after all formal evidence is classified."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = [("PAC", "Formal"), ("Acrobat", "Full Check"), ("veraPDF", "PDF/UA-1 ua1")]
CLASSES = {"M01": "semantic", "M02": "semantic", "M03": "machine-checkable", "M04": "semantic", "M05": "semantic", "M06": "semantic", "M07": "machine-checkable", "M08": "machine-checkable", "M09": "machine-checkable", "M10": "machine-checkable"}


def read(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def excluded_mutant_ids() -> set[str]:
    return {row.get("mutant_id", "") for row in read(ROOT / "data" / "mutant_exclusions.csv") if row.get("status")}


def active_mutant_ids() -> set[str]:
    excluded = excluded_mutant_ids()
    path = ROOT / "data" / "mutants.jsonl"
    if not path.is_file():
        return set()
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if str(row.get("status", "")).lower() == "valid" and row.get("verification", {}).get("mutation_valid") is True and row.get("mutant_id") not in excluded:
            ids.add(row["mutant_id"])
    return ids


def interpreted_outcome(row: dict[str, str]) -> str:
    """Expose study vocabulary without rewriting the raw classification field."""
    classification = row.get("detection_classification", "")
    operator_class = CLASSES.get(row.get("operator", ""), "")
    reason = row.get("classification_reason", "").lower()
    if classification == "Detected":
        if "proxy" in reason:
            return "CONSEQUENCE_PROXY_DETECTION"
        if "collateral" in reason:
            return "COLLATERAL_DETECTION"
        return "DIRECT_OR_VALIDATED_TARGET_DETECTION"
    if classification == "Needs Manual Check":
        return "MANUAL_REVIEW"
    if classification == "Missed":
        return "NO_AUTOMATED_FINDING" if operator_class == "semantic" else "SURVIVED_AUTOMATED_CHECKS"
    if classification == "Not Applicable":
        return "EXCLUDED_OR_NOT_APPLICABLE"
    return "UNCLASSIFIED"


def main() -> int:
    runs = read(ROOT / "data" / "validator_runs.csv")
    active_ids = active_mutant_ids()
    mutants = [
        row for row in runs
        if row.get("baseline_or_mutant") == "mutant"
        and row.get("artifact_id") in active_ids
        and (row.get("validator"), row.get("configuration")) in set(VALIDATORS)
    ]
    rows = []
    for row in mutants:
        if row.get("validator") == "PAC":
            config = "Formal"
        elif row.get("validator") == "veraPDF":
            config = "PDF/UA-1 ua1"
        else:
            config = "Full Check"
        resolved_baseline = (
            row.get("baseline_status") in {"BASELINE_PASS", "baseline_pass"}
            or "G05's pre-existing Lbl and LBody failure is baseline context" in row.get("classification_reason", "")
            or "G09's Natural language baseline failure is confined to excluded M08" in row.get("classification_reason", "")
        )
        rows.append({
            "artifact_id": row.get("artifact_id", ""), "operator": row.get("operator", ""),
            "operator_class": CLASSES.get(row.get("operator", ""), "REQUIRES_USER_VERIFICATION"),
            "source_golden": row.get("source_golden", ""), "validator": row.get("validator", ""),
            "configuration": config, "mutant_sha256": row.get("file_sha256", ""),
            "baseline_sha256": row.get("baseline_file_sha256", ""), "baseline_status": row.get("baseline_status", ""),
            "validator_version": row.get("validator_version", ""), "build": row.get("build", ""),
            "profile": row.get("profile", ""), "raw_report_path": row.get("raw_report_path", ""),
            "raw_report_sha256": row.get("report_sha256", ""),
            "automated_pass_fail": row.get("automated_pass_fail", ""), "relevant_rule_ids": row.get("relevant_rule_ids", ""),
            "detection_classification": row.get("detection_classification", ""),
            "interpreted_outcome": interpreted_outcome(row),
            "survival_classification": "SURVIVED_FORMAL" if row.get("detection_classification") in {"Missed", "Survived", "NotDetected"} else "",
            "ambiguous_or_confounded": "TRUE" if not resolved_baseline or row.get("detection_classification") not in {"Detected", "Missed", "Needs Manual Check", "Not Applicable"} else "FALSE",
            "notes": row.get("classification_reason", ""),
        })
    out = ROOT / "analysis" / "generated" / "formal_results_freeze.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["artifact_id", "operator", "operator_class", "source_golden", "validator", "configuration", "mutant_sha256", "baseline_sha256", "baseline_status", "validator_version", "build", "profile", "raw_report_path", "raw_report_sha256", "automated_pass_fail", "relevant_rule_ids", "detection_classification", "interpreted_outcome", "survival_classification", "ambiguous_or_confounded", "notes"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(sorted(rows, key=lambda r: (r["artifact_id"], r["validator"])))
    expected = len({row.get("artifact_id") for row in mutants}) * 3
    manifest_inputs = [
        ROOT / "data" / "validator_runs.csv",
        ROOT / "data" / "baseline_deltas.csv",
        ROOT / "data" / "baseline_conflict_resolutions.csv",
        ROOT / "analysis" / "generated" / "baseline_operator_conflicts.csv",
        ROOT / "analysis" / "generated" / "baseline_cross_validator_disagreements.csv",
        ROOT / "data" / "pac_evidence_manifest.csv",
        ROOT / "data" / "acrobat_evidence_manifest.csv",
        ROOT / "data" / "verapdf_runs.csv",
    ]
    manifest = {
        "manifest_version": "1.1",
        "generated_from": "scripts/build_formal_freeze.py",
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip(),
        "excluded_artifacts": read(ROOT / "data" / "mutant_exclusions.csv"),
        "freeze": {
            "path": str(out.relative_to(ROOT)),
            "exists": out.is_file(),
            "row_count": len(rows),
            "expected_row_count": expected,
            "unique_mutants": len({row["artifact_id"] for row in rows}),
            "expected_unique_mutants": len({row["artifact_id"] for row in mutants}),
            "classified_rows": sum(row["detection_classification"] in {"Detected", "Missed", "Needs Manual Check", "Not Applicable"} for row in rows),
            "all_ambiguous_or_confounded_false": not any(row["ambiguous_or_confounded"] == "TRUE" for row in rows),
            "sha256": sha256(out),
        },
        "inputs": [],
        "integrity_status": "PASS" if len(rows) == expected and not any(row["ambiguous_or_confounded"] == "TRUE" for row in rows) else "REVIEW_REQUIRED",
    }
    for path in manifest_inputs:
        item = {"path": str(path.relative_to(ROOT)), "exists": path.is_file()}
        if path.is_file():
            item["row_count"] = len(read(path)) if path.suffix.lower() == ".csv" else None
            item["sha256"] = sha256(path)
        manifest["inputs"].append(item)
    (ROOT / "analysis" / "generated" / "formal_freeze_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    review = ROOT / "FORMAL_RESULTS_REVIEW.md"
    if len(rows) < expected or any(row["ambiguous_or_confounded"] == "TRUE" for row in rows):
        review.write_text(f"# Formal results review\n\nThe formal freeze is not yet clean: {len(rows)}/{expected} validator-mutant records are present, and {sum(row['ambiguous_or_confounded'] == 'TRUE' for row in rows)} record(s) are ambiguous or baseline-confounded. Review collateral detections, baseline-carried failures, unexpected operator anomalies, suspiciously universal failures, and parser artifacts before PAC AI interpretation.\n", encoding="utf-8")
        print(f"Formal freeze written with review flags: {len(rows)}/{expected} rows")
        return 1
    review.write_text("# Formal results review\n\nAll formal validator-mutant records have matching baseline comparisons and explicit classifications. Perform the final collateral/parser-artifact audit before interpreting PAC AI or AT evidence.\n", encoding="utf-8")
    print(f"Formal freeze complete: {len(rows)}/{expected} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
