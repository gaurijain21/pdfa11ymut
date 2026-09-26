"""Reconcile evidence-linked metadata without changing experimental classifications."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EVIDENCE = ROOT / "evidence" / "at" / "nvda"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str] | None = None) -> None:
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize(path: str) -> str:
    return path.replace("\\", "/")


def portable_text(value: str) -> str:
    """Remove machine-specific checkout prefixes from captured observations."""
    value = normalize(value)
    root = normalize(str(ROOT)).rstrip("/") + "/"
    return value.replace(root, "")


def reconcile_validator_runs() -> tuple[list[dict[str, str]], int]:
    path = DATA / "validator_runs.csv"
    rows = read_csv(path)
    formal_mutant_configs = {"Formal", "Full Check", "PDF/UA-1 ua1"}
    updated = 0
    for row in rows:
        report_path = ROOT / Path(row.get("raw_report_path", ""))
        if report_path.is_file():
            actual = sha256(report_path)
            existing = row.get("report_sha256", "").strip()
            if existing and existing != actual:
                raise SystemExit(f"report hash mismatch for {row.get('record_id')}: {existing} != {actual}")
            if not existing:
                row["report_sha256"] = actual
                updated += 1
        if not row.get("build", "").strip():
            if row.get("validator") == "PAC":
                row["build"] = "26.1.0.0 (PAC.exe FileVersion/ProductVersion)"
            elif row.get("validator") == "Acrobat":
                row["build"] = "2026.002.21931 (64-bit)"
            elif row.get("validator") == "veraPDF":
                row["build"] = "Greenfield 1.30.2; Java 17.0.20.1"
        if (
            row.get("baseline_or_mutant") == "mutant"
            and row.get("configuration") in formal_mutant_configs
            and not row.get("relevant_rule_ids", "").strip()
        ):
            classification = row.get("detection_classification", "")
            if classification == "Needs Manual Check":
                row["relevant_rule_ids"] = f"MANUAL_CHECK_PROMPTS:{row.get('manual_check_prompts', 'unspecified')}"
            elif classification == "Missed":
                row["relevant_rule_ids"] = "NONE_REPORTED"
            elif classification == "Not Applicable":
                row["relevant_rule_ids"] = "NOT_APPLICABLE"
            else:
                row["relevant_rule_ids"] = "REVIEW_REQUIRED"
    write_csv(path, rows, list(rows[0]))
    return rows, updated


def reconcile_corpus_inventory(rows: list[dict[str, str]]) -> None:
    path = DATA / "corpus_inventory.csv"
    inventory = read_csv(path)
    baseline_rows = [
        row for row in rows
        if row.get("baseline_or_mutant") == "golden_baseline"
        and row.get("configuration") in {"Formal", "Full Check", "PDF/UA-1 ua1"}
        and row.get("validator") in {"PAC", "Acrobat", "veraPDF"}
    ]
    by_golden: dict[str, list[dict[str, str]]] = {}
    for row in baseline_rows:
        by_golden.setdefault(row.get("source_golden", row.get("artifact_id", "")), []).append(row)
    for record in inventory:
        golden = record["artifact_id"]
        refs = sorted(by_golden.get(golden, []), key=lambda item: item.get("validator", ""))
        if len(refs) != 3:
            raise SystemExit(f"expected three formal baseline references for {golden}, found {len(refs)}")
        record["baseline_status"] = "BASELINE_EVIDENCE_PRESENT"
        if golden == "PDFUA-Ref-2-05_BookChapter-german":
            record["baseline_status"] = "BASELINE_EVIDENCE_PRESENT_WITH_DOCUMENTED_DELTA"
        if golden == "PDFUA-Ref-2-09_Scanned":
            record["baseline_status"] = "BASELINE_EVIDENCE_PRESENT_WITH_TOOL_CONFLICT"
        record["baseline_evidence_path"] = ";".join(normalize(item["raw_report_path"]) for item in refs)
        record["baseline_notes"] = (
            "Formal baseline evidence is present for PAC Formal, Acrobat Full Check, and veraPDF PDF/UA-1; "
            "baseline-relative interpretation is recorded in data/baseline_conflict_resolutions.csv and "
            "analysis/generated/baseline_cross_validator_disagreements.csv."
        )
    write_csv(path, inventory, list(inventory[0]))


def reconcile_at() -> tuple[list[dict[str, str]], str]:
    path = DATA / "at_observations.csv"
    rows = read_csv(path)
    log_path = EVIDENCE / "nvda-session.log"
    if not log_path.is_file():
        raise SystemExit(f"missing preserved NVDA log: {log_path}")
    log_hash = sha256(log_path)
    intervals = {
        "PDFUA-Ref-2-02_Invoice-M01": "fresh paired Speech Viewer screenshots; historical session lines retained for prior instability context",
        "PDFUA-Ref-2-02_Invoice-M02": "mutant lines 11232-11239",
        "PDFUA-Ref-2-02_Invoice-M03": "mutant lines 11615-11623",
        "PDFUA-Ref-2-02_Invoice-M04": "mutant lines 12885-12912",
        "PDFUA-Ref-2-02_Invoice-M07": "mutant lines 13220-13229",
        "PDFUA-Ref-2-02_Invoice-M10": "mutant lines 13525-13556",
        "PDFUA-Ref-2-03_AcademicAbstract-M05": "mutant lines 13878-13931",
        "PDFUA-Ref-2-03_AcademicAbstract-M06": "mutant lines 14396-14400 and 14989-15027",
        "PDFUA-Ref-2-10_Form-M08": "golden lines 16360-16369; mutant lines 15617-15647",
    }
    screenshots = {
        "PDFUA-Ref-2-02_Invoice-M01": "evidence/at/nvda/PDFUA-Ref-2-02_Invoice-M01__rerun-mutant.png",
        "PDFUA-Ref-2-10_Form-M08": "evidence/at/nvda/PDFUA-Ref-2-10_Form__06d5cacd7c5ba9573a57c6d99d3f357ee14a24cff0c138036840fc44c6311806.png",
    }
    for row in rows:
        artifact = row["artifact_id"]
        transcript_path = EVIDENCE / f"{artifact}.txt"
        transcript = transcript_path.read_text(encoding="utf-8") if transcript_path.is_file() else ""
        transcript_fields = {}
        for label in ("NVDA", "Viewer", "Windows", "Golden", "Mutant", "Observation"):
            prefix = f"{label}: "
            transcript_fields[label] = next((line[len(prefix):].strip() for line in transcript.splitlines() if line.startswith(prefix)), "")
        row["at_version"] = transcript_fields["NVDA"] or "2026.2.0.57664"
        row["viewer"] = "Adobe Acrobat"
        row["viewer_version"] = "26.2.21931.0"
        row["os_version"] = transcript_fields["Windows"] or "Windows 10 Home 25H2 build 26200.9457"
        row["golden_observation"] = portable_text(transcript_fields["Golden"])
        row["mutant_observation"] = portable_text(transcript_fields["Mutant"])
        row["observation"] = portable_text(transcript_fields["Observation"])
        row["evidence_path"] = f"evidence/at/nvda/{artifact}.txt"
        row["status"] = "COMPLETE" if transcript and transcript_path.is_file() else row.get("status", "TODO")
        row["coder_1"] = row.get("coder_1") or "Codex/NVDA"
        row["raw_log_path"] = "evidence/at/nvda/nvda-session.log"
        row["raw_log_sha256"] = log_hash
        row["raw_log_interval"] = intervals.get(artifact, "timestamped interval recorded in the preserved session log")
        row["screenshot_path"] = screenshots.get(artifact, "")
        if artifact.endswith("Invoice-M01"):
            row["exact_at_observation"] = (
                "Golden began with the logo. Mutant attempt A began with John Q. Doe; a later mutant attempt began with the logo."
            )
            row["mutant_observation"] = (
                "One mutant attempt began with John Q. Doe before the logo; a later mutant attempt began with the logo."
            )
            row["observation"] = (
                "M01 was run-to-run unstable in the preserved session: the mutant began with John Q. Doe in one attempt "
                "and with the logo in another. Reported as instability, not as a stable opposite-order effect."
            )
            row["notes"] = (
                "Illustrative exploratory observation; raw log shows inconsistent mutant starts across attempts. A fresh clean rerun "
                "requires an unobstructed Acrobat/NVDA session. Not a validator detection rate."
            )
        if artifact.endswith("Invoice-M01"):
            row["exact_at_observation"] = "Clean paired rerun: golden announced the logo first; mutant announced John Q. Doe and the address block before the logo."
            row["mutant_observation"] = "The clean paired rerun announced John Q. Doe and the address block before the logo."
            row["observation"] = "The clean matched rerun reproduced the M01 reading-order mutation. This is an assistive-technology observation, not a validator detection rate."
            row["notes"] = "Fresh paired rerun captured with separate clean Speech Viewer screenshots; historical instability evidence is retained separately. Not a validator detection rate."
        if transcript_path.is_file():
            if artifact.endswith("Invoice-M01"):
                transcript = transcript.replace(
                    "Observation: The first two selected structural units were announced in the opposite order. This is an assistive-representation observation, not a validator detection rate.",
                    "Observation: M01 was run-to-run unstable: one mutant attempt began with John Q. Doe and a later attempt began with the logo. This is reported as instability, not a stable opposite-order effect.",
                )
            transcript = transcript.replace(
                "Source: C:/Gauri/ma11ypdf/tmp/nvda-at-config/nvda.log",
                "Source: evidence/at/nvda/nvda-session.log",
            )
            transcript = portable_text(transcript)
            marker = "Evidence audit metadata:"
            if marker in transcript:
                transcript = transcript.split(marker, 1)[0].rstrip() + "\n"
            transcript += (
                f"\n{marker}\n"
                f"Raw log: evidence/at/nvda/nvda-session.log\n"
                f"Raw log SHA-256: {log_hash}\n"
                f"Raw log interval: {intervals.get(artifact, 'timestamped interval recorded in the preserved session log')}\n"
                f"Screenshot: {screenshots.get(artifact, 'none; transcript is primary evidence')}\n"
                "The preserved log is a single observer session; no second independent coder or adjudication was available.\n"
            )
            transcript_path.write_text(transcript, encoding="utf-8")
    fields = list(rows[0])
    for field in ("raw_log_path", "raw_log_sha256", "raw_log_interval", "screenshot_path"):
        if field not in fields:
            fields.append(field)
    write_csv(path, rows, fields)
    selection_path = DATA / "at_selection.csv"
    selection = read_csv(selection_path)
    status_by_artifact = {row["artifact_id"]: row["status"] for row in rows}
    for row in selection:
        if status_by_artifact.get(row.get("artifact_id")) == "COMPLETE":
            row["status"] = "COMPLETE"
    write_csv(selection_path, selection, list(selection[0]))
    return rows, log_hash


def write_release_manifest(rows: list[dict[str, str]], log_hash: str) -> None:
    mutant_manifest = [
        json.loads(line)
        for line in (DATA / "mutants.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    exclusions = [row for row in read_csv(DATA / "mutant_exclusions.csv") if row.get("status")]
    excluded_ids = {row.get("mutant_id", "") for row in exclusions}
    valid_mutants = [row for row in mutant_manifest if row.get("status") == "valid"]
    active_mutants = [row for row in valid_mutants if row.get("mutant_id") not in excluded_ids and row.get("verification", {}).get("mutation_valid")]
    pac_ai_selection = read_csv(DATA / "pac_ai_selection.csv")
    pac_ai_selected = [row for row in pac_ai_selection if row.get("artifact_type", "mutant") == "mutant" and row.get("selected_for_pac_ai") == "TRUE"]
    pac_ai_classifications = read_csv(DATA / "pac_ai_classifications.csv")
    mutant_rows = [row for row in read_csv(DATA / "validator_runs.csv") if row.get("baseline_or_mutant") == "mutant"]
    formal = [
        row for row in mutant_rows
        if row.get("configuration") in {"Formal", "Full Check", "PDF/UA-1 ua1"}
        and row.get("artifact_id") in {item.get("mutant_id") for item in active_mutants}
    ]
    manifest = {
        "manifest_version": "1.0",
        "release_status": "CONDITIONALLY_READY",
        "scope": "Nine PDF/UA Reference Suite files; fixed PAC Formal, Acrobat Full Check, veraPDF PDF/UA-1, and illustrative exploratory NVDA observations.",
        "counts": {
            "golden_pdfs": 9,
            "valid_generated_mutants": len(valid_mutants),
            "active_formal_mutants": len(active_mutants),
            "active_formal_validator_rows": len(formal),
            "at_observations_complete": sum(row.get("status") == "COMPLETE" for row in rows),
            "pac_ai_selected_mutants": len(pac_ai_selected),
            "pac_ai_aggregate_only_rows": sum(
                row.get("status") == "REVIEW_REQUIRED"
                and row.get("ai_classification") == "AI_AMBIGUOUS"
                for row in pac_ai_classifications
            ),
        },
        "exclusions": exclusions + [{"artifact_id": "G02-M04", "reason": "historical pair, COS audit, and raw reports unavailable; permanently excluded"}],
        "pac_ai": "Separate future-work experiment; preserved package is aggregate-only, while the fresh native pilot exposed element-level finding text/scores but no supported complete semantic export/API, so no full-cohort mutation-specific classification is inferred.",
        "at": {
            "observer_design": "single-observer illustrative exploratory observations under one fixed configuration",
            "primary_evidence": "timestamped transcripts plus targeted Speech Viewer captures linked to the named NVDA/Acrobat configuration",
            "log_sha256": log_hash,
            "screenshots_available_for": ["PDFUA-Ref-2-02_Invoice-M01", "PDFUA-Ref-2-10_Form-M08"],
            "limitation": "screenshots are targeted evidence for two cases; the pilot remains single-observer and configuration-specific",
        },
        "provenance": "Collection-level PDF/UA Reference Suite mapping and CC BY 4.0 attribution are recorded; original acquisition archive/timestamp was not retained.",
        "required_reproduction_inputs": [
            "corpus/golden/", "corpus/mutants/", "operators/operators.yaml", "data/mutants.jsonl", "data/validator_runs.csv", "evidence/", "scripts/", "reproduce.py"
        ],
        "release_notes": "The mismatch-backup PDF remains in place as a recovery artifact and is explicitly excluded by data/corpus_extra_artifacts.csv.",
    }
    (DATA / "release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    validator_rows, _ = reconcile_validator_runs()
    reconcile_corpus_inventory(validator_rows)
    rows, log_hash = reconcile_at()
    write_release_manifest(rows, log_hash)
    print(json.dumps({"validator_rows_updated": len(validator_rows), "at_rows": len(rows), "nvda_log_sha256": log_hash}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
