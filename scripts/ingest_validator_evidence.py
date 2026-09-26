"""Ingest hash-addressed validator evidence without inventing classifications."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_FIELDS = [
    "record_id", "artifact_id", "baseline_or_mutant", "source_golden", "operator", "file_sha256",
    "validator", "configuration", "validator_version", "build", "platform", "profile",
    "PAC_AI_enabled", "run_timestamp", "automated_pass_fail", "relevant_rule_ids",
    "relevant_rule_text", "manual_check_prompts", "raw_report_path", "report_sha256", "raw_detection_classification",
    "baseline_status", "baseline_file_sha256", "baseline_run_id", "detection_classification",
    "classification_reason", "coder_1", "coder_2", "adjudication", "notes",
]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def json_facts(path: Path) -> tuple[str, str, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "", "", "JSON_PARSE_ERROR"
    # veraPDF 1.30.x stores the result under report.jobs[].validationResult[].
    # Parse that schema directly so compliant baselines are not mistaken for
    # failures merely because the JSON uses whitespace around separators.
    results = []
    report = data.get("report") if isinstance(data, dict) else None
    for job in (report or {}).get("jobs", []) if isinstance(report, dict) else []:
        results.extend(job.get("validationResult", []))
    if results:
        rule_ids = []
        rule_text = []
        failed_count = 0
        outcomes = []
        for result in results:
            if not isinstance(result, dict):
                continue
            outcomes.append(result.get("compliant"))
            details = result.get("details", {}) or {}
            failed_count += int(details.get("failedRules", 0) or 0)
            for summary in details.get("ruleSummaries", []) or []:
                if not isinstance(summary, dict):
                    continue
                identifier = summary.get("clause") or summary.get("testNumber") or summary.get("ruleId")
                if identifier is not None:
                    rule_ids.append(str(identifier))
                description = summary.get("description") or summary.get("errorMessage")
                if description:
                    rule_text.append(str(description))
        if any(value is False for value in outcomes) or failed_count:
            outcome = "FAIL"
        elif outcomes and all(value is True for value in outcomes):
            outcome = "PASS"
        else:
            outcome = ""
        note = f"parsed_verapdf_json;failed_rule_count={failed_count}"
        if rule_text:
            note += ";failed_rule_text=" + " || ".join(dict.fromkeys(rule_text))
        return ";".join(dict.fromkeys(rule_ids)), outcome, note
    text = json.dumps(data, ensure_ascii=False)
    return facts_from_text(text, "parsed_json")


class AcrobatReportParser(HTMLParser):
    """Parse Acrobat's native accessibility-report HTML without flattening statuses."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.in_dd = False
        self.in_li = False
        self.in_row = False
        self.in_cell = False
        self.cell_text: list[str] = []
        self.row_cells: list[str] = []
        self.rows: list[list[str]] = []
        self.list_items: list[str] = []
        self.title_text = ""
        self.dd_text = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self.in_title = True
        elif tag == "dd":
            self.in_dd = True
        elif tag == "li":
            self.in_li = True
            self._text = []
        elif tag == "tr":
            self.in_row = True
            self.row_cells = []
        elif tag == "td" and self.in_row:
            self.in_cell = True
            self.cell_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "dd":
            self.in_dd = False
        elif tag == "li" and self.in_li:
            self.list_items.append(" ".join("".join(self._text).split()))
            self.in_li = False
        elif tag == "td" and self.in_cell:
            self.row_cells.append(" ".join("".join(self.cell_text).split()))
            self.in_cell = False
        elif tag == "tr" and self.in_row:
            if self.row_cells:
                self.rows.append(self.row_cells)
            self.in_row = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_text += data
        if self.in_dd:
            self.dd_text += data
        if self.in_li:
            self._text.append(data)
        if self.in_cell:
            self.cell_text.append(data)


def acrobat_html_facts(path: Path) -> tuple[str, str, str]:
    try:
        parser = AcrobatReportParser()
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, ValueError):
        return "", "", "ACROBAT_HTML_PARSE_ERROR"
    detail_rows = [row for row in parser.rows if len(row) == 3 and row[1].strip()]
    if not detail_rows:
        return "", "", "ACROBAT_HTML_PARSE_ERROR_NO_DETAIL_ROWS"
    failed = [row for row in detail_rows if row[1].strip().lower() == "failed"]
    manual = [row for row in detail_rows if row[1].strip().lower() == "needs manual check"]
    skipped = [row for row in detail_rows if row[1].strip().lower() == "skipped"]
    passed_manually = [row for row in detail_rows if row[1].strip().lower() == "passed manually"]
    failed_manually = [row for row in detail_rows if row[1].strip().lower() == "failed manually"]
    known = {"passed", "failed", "needs manual check", "skipped", "passed manually", "failed manually"}
    unknown = [row for row in detail_rows if row[1].strip().lower() not in known]
    if unknown:
        outcome = ""
    else:
        outcome = "FAIL" if failed else "PASS"
    names = lambda rows: "|".join(row[0] for row in rows)
    note = "parsed_acrobat_html"
    note += f";automated_failure_count={len(failed)};automated_failure_names={names(failed)}"
    note += f";manual_check_count={len(manual)};manual_check_names={names(manual)}"
    note += f";skipped_count={len(skipped)};skipped_names={names(skipped)}"
    note += f";passed_manually_count={len(passed_manually)};failed_manually_count={len(failed_manually)}"
    note += f";unknown_status_count={len(unknown)}"
    if failed:
        note += ";failed_rule_text=" + "|".join(f"{row[0]}: {row[2]}" for row in failed)
    if manual:
        note += ";manual_check_descriptions=" + "|".join(f"{row[0]}: {row[2]}" for row in manual)
    if skipped:
        note += ";skipped_descriptions=" + "|".join(f"{row[0]}: {row[2]}" for row in skipped)
    return ";".join(dict.fromkeys(row[0] for row in failed)), outcome, note


def facts_from_text(text: str, note: str) -> tuple[str, str, str]:
    ids = sorted(set(re.findall(r"(?:ruleId|ruleID|rule_id|clause|testNumber)[\"']?\s*[:=]\s*[\"']?([^,}\"']+)", text, re.I)))
    lower = text.lower()
    if re.search(r'"(?:iscompliant|compliant|valid)"\s*:\s*true', lower):
        outcome = "PASS"
    elif re.search(r'"(?:iscompliant|compliant|valid)"\s*:\s*false', lower):
        outcome = "FAIL"
    elif re.search(r"\bfailed\s*[:(]?\s*[1-9]\d*", lower) or ("failed" in lower and "failed 0" not in lower and "failed: 0" not in lower):
        outcome = "FAIL"
    elif "passed" in lower and "failed" not in lower:
        outcome = "PASS"
    else:
        outcome = ""
    return ";".join(ids), outcome, note


def rule_text_from_note(note: str) -> str:
    return note_value(note, "failed_rule_text")


def note_value(note: str, key: str) -> str:
    marker = key + "="
    for field in note.split(";"):
        if field.startswith(marker):
            return field[len(marker):]
    return ""


def pdf_facts(path: Path) -> tuple[str, str, str]:
    text = pdf_report_text(path)
    if not text:
        return "", "", "PDF_PARSE_ERROR"
    if "PAC Test Report" in text or "PDF Accessibility Checker" in text:
        summary_rows = []
        row_pattern = re.compile(r"^\s*(.+?)\s+(\d+|-)\s+(\d+|-)\s+(\d+|-)\s*$")
        for line in text.splitlines():
            match = row_pattern.match(line)
            if match:
                name, passed, warned, failed = match.groups()
                summary_rows.append((name.strip(), passed, warned, failed))
        failures = [(name, count) for name, _passed, _warned, count in summary_rows if count != "-" and int(count) > 0]
        warnings = [(name, count) for name, _passed, count, _failed in summary_rows if count != "-" and int(count) > 0]
        manual_names = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and re.search(r"manual\s+check|needs\s+manual", stripped, re.I):
                if stripped not in manual_names:
                    manual_names.append(stripped)
        failure_names = [name for name, _count in failures]
        warning_names = [name for name, _count in warnings]
        outcome = "PASS" if "requirements checked by PAC are fulfilled" in text else "FAIL" if "not PDF/UA compliant" in text else ""
        note = "parsed_pac_pdf"
        note += f";automated_failure_count={len(failures)}"
        note += ";automated_failure_names=" + "|".join(failure_names)
        note += f";warning_count={len(warnings)}"
        note += ";warning_names=" + "|".join(warning_names)
        note += f";manual_check_count={len(manual_names)}"
        note += ";manual_check_names=" + "|".join(manual_names)
        if failures:
            note += ";failed_rule_text=" + "|".join(f"{name} ({count})" for name, count in failures)
        return ";".join(failure_names), outcome, note
    return facts_from_text(text, "parsed_pdf_report")


def manual_prompt_count(path: Path) -> int:
    try:
        if path.suffix.lower() == ".pdf":
            text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path), strict=False).pages)
        elif path.suffix.lower() == ".json":
            text = path.read_text(encoding="utf-8")
        elif path.name.lower().endswith(".accreport.html"):
            text = path.read_text(encoding="utf-8", errors="replace")
            return len(re.findall(r"<td>\s*needs\s+manual\s+check\s*</td>", text, re.I))
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0
    return len(re.findall(r"needs\s+manual\s+check|manual\s+check", text, re.I))


def pac_formal_metadata() -> dict:
    path = ROOT / "data" / "pac_formal_run_metadata.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def acrobat_metadata() -> dict:
    path = ROOT / "data" / "acrobat_run_metadata.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def baseline_conflict_resolutions() -> list[dict[str, str]]:
    return read_csv(ROOT / "data" / "baseline_conflict_resolutions.csv")


def evidence_path_for_task(task: dict[str, str]) -> Path:
    """Return the prescribed path, or Acrobat's preserved native report companion."""
    expected = ROOT / task["evidence_destination"] / task["exact_output_filename"]
    if expected.exists():
        return expected
    if task.get("validator") == "Acrobat" and expected.suffix.lower() == ".json":
        native = expected.with_suffix(".accreport.html")
        if native.exists():
            return native
        candidates = sorted(expected.parent.glob(f"{task.get('artifact_id', '')}__*.accreport.html"))
        if len(candidates) == 1:
            return candidates[0]
    return expected


def metadata_complete(metadata: dict) -> bool:
    required = ("pac_version", "pac_build", "platform", "profile")
    return bool(metadata) and all(str(metadata.get(key, "")).strip() and not str(metadata.get(key)).startswith("REQUIRES_") for key in required) and metadata.get("ai_enabled") is False


def b01_status(queue: list[dict], metadata: dict) -> tuple[bool, list[str]]:
    tasks = [row for row in queue if row.get("batch_id") == "B01_GOLDEN_PAC_FORMAL"]
    missing = []
    paths = []
    report_hashes = {}
    for task in tasks:
        expected = ROOT / task["evidence_destination"] / task["exact_output_filename"]
        paths.append(str(expected.resolve()))
        input_path = ROOT / task["filepath"]
        if not expected.exists():
            missing.append(task["artifact_id"] + " (report missing)")
        elif not input_path.exists() or digest(input_path) != task["sha256"]:
            missing.append(task["artifact_id"] + " (input hash mismatch)")
        else:
            report_hash = digest(expected)
            if report_hash in report_hashes:
                missing.append(task["artifact_id"] + " (report reused from " + report_hashes[report_hash] + ")")
            report_hashes[report_hash] = task["artifact_id"]
            if task["filepath"].split("\\")[-1].lower() not in pdf_report_text(expected).lower():
                missing.append(task["artifact_id"] + " (report does not identify the expected input PDF)")
    if len(paths) != len(set(paths)):
        missing.append("duplicate evidence path in queue")
    if not metadata_complete(metadata):
        missing.append("PAC metadata incomplete: fill data/pac_formal_run_metadata.json")
    return not missing and len(tasks) == 9, missing


def b02_status(queue: list[dict], metadata: dict) -> tuple[bool, list[str]]:
    tasks = [row for row in queue if row.get("batch_id") == "B02_GOLDEN_ACROBAT"]
    missing = []
    report_hashes: dict[str, str] = {}
    required_metadata = ("product", "version", "build", "bitness", "platform", "checker", "configuration", "run_configuration")
    if not metadata or any(not str(metadata.get(key, "")).strip() or str(metadata.get(key)).startswith("REQUIRES_") for key in required_metadata):
        missing.append("Acrobat metadata incomplete: fill data/acrobat_run_metadata.json")
    for task in tasks:
        report = evidence_path_for_task(task)
        input_path = ROOT / task["filepath"]
        if not report.exists():
            missing.append(task["artifact_id"] + " (native report missing)")
            continue
        if not input_path.exists() or digest(input_path) != task["sha256"]:
            missing.append(task["artifact_id"] + " (input hash mismatch)")
        report_hash = digest(report)
        if report_hash in report_hashes:
            missing.append(task["artifact_id"] + " (report reused from " + report_hashes[report_hash] + ")")
        report_hashes[report_hash] = task["artifact_id"]
        expected_name = Path(task["filepath"]).name.lower()
        raw = report.read_text(encoding="utf-8", errors="replace").lower()
        if expected_name not in raw:
            missing.append(task["artifact_id"] + " (report does not identify the expected input PDF)")
        _rule_ids, outcome, parse_note = acrobat_html_facts(report)
        if not parse_note.startswith("parsed_acrobat_html") or outcome not in {"PASS", "FAIL"}:
            missing.append(task["artifact_id"] + " (native report parse/validation failed)")
    return not missing and len(tasks) == 9, missing


def b02_report_count(queue: list[dict]) -> int:
    return sum(1 for task in queue if task.get("batch_id") == "B02_GOLDEN_ACROBAT" and evidence_path_for_task(task).exists())


def b02_valid_count(queue: list[dict], metadata: dict) -> int:
    required_metadata = ("product", "version", "build", "bitness", "platform", "checker", "configuration", "run_configuration")
    if not metadata or any(not str(metadata.get(key, "")).strip() or str(metadata.get(key)).startswith("REQUIRES_") for key in required_metadata):
        return 0
    count = 0
    seen: set[str] = set()
    for task in [row for row in queue if row.get("batch_id") == "B02_GOLDEN_ACROBAT"]:
        report = evidence_path_for_task(task)
        input_path = ROOT / task["filepath"]
        if not report.exists() or not input_path.exists() or digest(input_path) != task["sha256"]:
            continue
        report_hash = digest(report)
        if report_hash in seen:
            continue
        seen.add(report_hash)
        raw = report.read_text(encoding="utf-8", errors="replace").lower()
        if Path(task["filepath"]).name.lower() not in raw:
            continue
        _rule_ids, outcome, parse_note = acrobat_html_facts(report)
        if parse_note.startswith("parsed_acrobat_html") and outcome in {"PASS", "FAIL"}:
            count += 1
    return count


def pdf_report_text(path: Path) -> str:
    try:
        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path), strict=False).pages)
    except Exception:
        return ""


def canonicalize_b01_reports(queue: list[dict]) -> list[str]:
    """Copy uniquely mapped PAC exports to the queue's hash-addressed names.

    PAC's export dialog may choose a descriptive report stem instead of the
    queue name. This is safe only when the artifact-specific candidate is
    unique and the PDF text names the exact expected input file. The original
    export is retained as raw evidence.
    """
    copied = []
    used = set()
    evidence_dir = ROOT / "evidence" / "pac" / "formal"
    for task in queue:
        if task.get("batch_id") != "B01_GOLDEN_PAC_FORMAL":
            continue
        expected = ROOT / task["evidence_destination"] / task["exact_output_filename"]
        if expected.exists():
            continue
        candidates = [p for p in sorted(evidence_dir.glob(task["artifact_id"] + "_*.pdf")) if p.resolve() not in used]
        input_name = Path(task["filepath"]).name
        valid = [p for p in candidates if input_name.lower() in pdf_report_text(p).lower()]
        if len(valid) != 1:
            continue
        source = valid[0]
        expected.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, expected)
        used.add(source.resolve())
        copied.append(f"{source.name} -> {expected.name}")
    return copied


def canonicalize_pac_exports(queue: list[dict], batch_filter: str = "", sub_batch_filter: str = "") -> list[str]:
    """Reconcile uniquely named PAC exports into hash-addressed evidence slots.

    The human-readable export is retained. A copy is created only when the
    queue row's exact input hash is valid, the artifact-specific export name is
    unique, and PAC's PDF report parser accepts the report. Ambiguity fails
    closed and is left for the caller to report.
    """
    manifest_path = ROOT / "data" / "pac_evidence_manifest.csv"
    fields = [
        "artifact_id", "validator", "configuration", "baseline_or_mutant", "source_golden",
        "input_pdf_sha256", "input_pdf_path", "raw_export_filename", "raw_export_path",
        "raw_report_sha256", "canonical_filename", "canonical_path", "canonical_sha256",
        "mapping_method", "report_parse_note", "mapped_at",
    ]
    existing = read_csv(manifest_path)
    by_artifact = {row.get("artifact_id", ""): row for row in existing if row.get("artifact_id")}
    used_raw: dict[str, str] = {
        row.get("raw_report_sha256", ""): row.get("artifact_id", "")
        for row in existing
        if row.get("raw_report_sha256")
    }
    messages: list[str] = []
    for task in queue:
        if task.get("validator") != "PAC" or task.get("baseline_or_mutant") != "mutant":
            continue
        if batch_filter and task.get("batch_id") != batch_filter:
            continue
        if sub_batch_filter and task.get("sub_batch_id") != sub_batch_filter:
            continue
        expected = ROOT / task["evidence_destination"] / task["exact_output_filename"]
        raw_candidates = sorted(expected.parent.glob(f"{task['artifact_id']}_PAC_UA_Report.pdf"))
        input_path = ROOT / task["filepath"]
        if not input_path.exists() or digest(input_path) != task.get("sha256", ""):
            messages.append(f"{task['artifact_id']}: input PDF SHA-256 mismatch")
            continue
        if expected.exists():
            canonical_hash = digest(expected)
            _rule_ids, outcome, parse_note = pdf_facts(expected)
            expected_input_name = Path(task["filepath"]).name.lower()
            if not parse_note.startswith("parsed_pac_pdf") or outcome not in {"PASS", "FAIL"}:
                messages.append(f"{task['artifact_id']}: canonical PAC report failed validation ({parse_note})")
                continue
            if expected_input_name not in pdf_report_text(expected).lower():
                messages.append(f"{task['artifact_id']}: canonical PAC report identifies a different input PDF")
                continue
            existing_row = by_artifact.get(task["artifact_id"], {})
            if len(raw_candidates) == 1:
                raw_hash = digest(raw_candidates[0])
                if raw_hash != canonical_hash:
                    messages.append(f"{task['artifact_id']}: canonical evidence exists but differs from raw PAC export")
                    continue
                old_hash = existing_row.get("raw_report_sha256", "")
                if old_hash and used_raw.get(old_hash) == task["artifact_id"]:
                    used_raw.pop(old_hash, None)
                existing_row.update({
                    "artifact_id": task["artifact_id"], "validator": task["validator"],
                    "configuration": task["configuration"], "baseline_or_mutant": task["baseline_or_mutant"],
                    "source_golden": task["source_golden"], "input_pdf_sha256": task["sha256"],
                    "input_pdf_path": task["filepath"], "raw_export_filename": raw_candidates[0].name,
                    "raw_export_path": str(raw_candidates[0].relative_to(ROOT)), "raw_report_sha256": raw_hash,
                    "canonical_filename": expected.name, "canonical_path": str(expected.relative_to(ROOT)),
                    "canonical_sha256": canonical_hash,
                    "mapping_method": "artifact_id_exact_name_plus_input_hash_embedded_filename_and_pac_parse",
                    "report_parse_note": parse_note, "mapped_at": datetime.now(timezone.utc).isoformat(),
                })
                by_artifact[task["artifact_id"]] = existing_row
                used_raw[raw_hash] = task["artifact_id"]
            elif len(raw_candidates) > 1:
                messages.append(f"{task['artifact_id']}: ambiguous PAC export candidates ({len(raw_candidates)})")
            else:
                messages.append(f"{task['artifact_id']}: canonical report has no retained human-readable raw export")
            continue
        if len(raw_candidates) != 1:
            if raw_candidates:
                messages.append(f"{task['artifact_id']}: ambiguous PAC export candidates ({len(raw_candidates)})")
            continue
        raw = raw_candidates[0]
        _rule_ids, outcome, parse_note = pdf_facts(raw)
        if not parse_note.startswith("parsed_pac_pdf") or outcome not in {"PASS", "FAIL"}:
            messages.append(f"{task['artifact_id']}: PAC export failed report validation ({parse_note})")
            continue
        raw_hash = digest(raw)
        prior_artifact = used_raw.get(raw_hash)
        if prior_artifact and prior_artifact != task["artifact_id"]:
            messages.append(f"{task['artifact_id']}: raw report reused by {prior_artifact}")
            continue
        existing_row = by_artifact.get(task["artifact_id"])
        if existing_row and existing_row.get("raw_report_sha256") != raw_hash:
            messages.append(f"{task['artifact_id']}: conflicting prior evidence mapping")
            continue
        expected.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(raw, expected)
        canonical_hash = digest(expected)
        if canonical_hash != raw_hash:
            messages.append(f"{task['artifact_id']}: canonical copy hash mismatch")
            continue
        row = {
            "artifact_id": task["artifact_id"], "validator": task["validator"],
            "configuration": task["configuration"], "baseline_or_mutant": task["baseline_or_mutant"],
            "source_golden": task["source_golden"], "input_pdf_sha256": task["sha256"],
            "input_pdf_path": task["filepath"], "raw_export_filename": raw.name,
            "raw_export_path": str(raw.relative_to(ROOT)), "raw_report_sha256": raw_hash,
            "canonical_filename": expected.name, "canonical_path": str(expected.relative_to(ROOT)),
            "canonical_sha256": canonical_hash, "mapping_method": "artifact_id_exact_name_plus_input_hash_and_pac_parse",
            "report_parse_note": parse_note, "mapped_at": datetime.now(timezone.utc).isoformat(),
        }
        by_artifact[task["artifact_id"]] = row
        used_raw[raw_hash] = task["artifact_id"]
        messages.append(f"{raw.name} -> {expected.name}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(by_artifact.values(), key=lambda row: row.get("artifact_id", "")))
    return messages


def canonicalize_acrobat_exports(queue: list[dict], batch_filter: str = "", sub_batch_filter: str = "") -> list[str]:
    """Reconcile unique human-named Acrobat HTML exports fail-closed.

    Acrobat's native HTML export is retained under its original name. A
    canonical ``.accreport.html`` companion is copied only after the queue's
    exact input hash and the HTML report parser both validate the mapping.
    Ambiguous candidates, reused report bytes, and mismatched prior mappings
    are reported and never guessed.
    """
    manifest_path = ROOT / "data" / "acrobat_evidence_manifest.csv"
    fields = [
        "artifact_id", "validator", "configuration", "baseline_or_mutant", "source_golden",
        "input_pdf_sha256", "input_pdf_path", "raw_export_filename", "raw_export_path",
        "raw_report_sha256", "canonical_filename", "canonical_path", "canonical_sha256",
        "mapping_method", "report_parse_note", "mapped_at",
    ]
    existing = read_csv(manifest_path)
    by_artifact = {row.get("artifact_id", ""): row for row in existing if row.get("artifact_id")}
    used_raw = {row.get("raw_report_sha256", ""): row.get("artifact_id", "") for row in existing if row.get("raw_report_sha256")}
    messages: list[str] = []
    for task in queue:
        if task.get("validator") != "Acrobat" or task.get("baseline_or_mutant") == "setup":
            continue
        if batch_filter and task.get("batch_id") != batch_filter:
            continue
        if sub_batch_filter and task.get("sub_batch_id") != sub_batch_filter:
            continue
        expected = ROOT / task["evidence_destination"] / task["exact_output_filename"]
        canonical = expected.with_suffix(".accreport.html") if expected.suffix.lower() == ".json" else expected
        input_path = ROOT / task["filepath"]
        if not input_path.exists() or digest(input_path) != task.get("sha256", ""):
            messages.append(f"{task['artifact_id']}: input PDF SHA-256 mismatch")
            continue
        raw_candidates = []
        candidate_patterns = (
            f"{task['artifact_id']}_*.html",
            f"{task['artifact_id']}_*.htm",
            f"{task['artifact_id']}.pdf.accreport.html",
            f"__{task['artifact_id']}.pdf.accreport.html",
        )
        for pattern in candidate_patterns:
            for candidate in sorted(canonical.parent.glob(pattern)):
                if candidate.resolve() == canonical.resolve():
                    continue
                if candidate not in raw_candidates:
                    raw_candidates.append(candidate)
        if canonical.exists():
            raw_hashes = {digest(path) for path in raw_candidates}
            if raw_hashes and digest(canonical) not in raw_hashes:
                messages.append(f"{task['artifact_id']}: canonical Acrobat report differs from raw export")
            continue
        if len(raw_candidates) != 1:
            if raw_candidates:
                messages.append(f"{task['artifact_id']}: ambiguous Acrobat export candidates ({len(raw_candidates)})")
            continue
        raw = raw_candidates[0]
        _rule_ids, outcome, parse_note = acrobat_html_facts(raw)
        if not parse_note.startswith("parsed_acrobat_html") or outcome not in {"PASS", "FAIL"}:
            messages.append(f"{task['artifact_id']}: Acrobat export failed report validation ({parse_note})")
            continue
        raw_hash = digest(raw)
        prior_artifact = used_raw.get(raw_hash)
        if prior_artifact and prior_artifact != task["artifact_id"]:
            messages.append(f"{task['artifact_id']}: raw Acrobat report reused by {prior_artifact}")
            continue
        prior = by_artifact.get(task["artifact_id"])
        if prior and prior.get("raw_report_sha256") != raw_hash:
            messages.append(f"{task['artifact_id']}: conflicting prior Acrobat evidence mapping")
            continue
        canonical.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(raw, canonical)
        canonical_hash = digest(canonical)
        if canonical_hash != raw_hash:
            messages.append(f"{task['artifact_id']}: canonical Acrobat copy hash mismatch")
            continue
        row = {
            "artifact_id": task["artifact_id"], "validator": task["validator"],
            "configuration": task["configuration"], "baseline_or_mutant": task["baseline_or_mutant"],
            "source_golden": task["source_golden"], "input_pdf_sha256": task["sha256"],
            "input_pdf_path": task["filepath"], "raw_export_filename": raw.name,
            "raw_export_path": str(raw.relative_to(ROOT)), "raw_report_sha256": raw_hash,
            "canonical_filename": canonical.name, "canonical_path": str(canonical.relative_to(ROOT)),
            "canonical_sha256": canonical_hash,
            "mapping_method": "artifact_id_exact_prefix_plus_input_hash_and_acrobat_html_parse",
            "report_parse_note": parse_note, "mapped_at": datetime.now(timezone.utc).isoformat(),
        }
        by_artifact[task["artifact_id"]] = row
        used_raw[raw_hash] = task["artifact_id"]
        messages.append(f"{raw.name} -> {canonical.name}")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(by_artifact.values(), key=lambda row: row.get("artifact_id", "")))
    return messages


def b01_report_count(queue: list[dict]) -> int:
    count = 0
    for task in queue:
        if task.get("batch_id") != "B01_GOLDEN_PAC_FORMAL":
            continue
        expected = ROOT / task["evidence_destination"] / task["exact_output_filename"]
        input_path = ROOT / task["filepath"]
        if expected.exists() and input_path.exists() and digest(input_path) == task["sha256"]:
            count += 1
    return count


def write_baseline_review(rows: list[dict]) -> list[dict]:
    baselines = [row for row in rows if row.get("baseline_or_mutant") == "golden_baseline" and row.get("validator") in {"PAC", "Acrobat", "veraPDF"}]
    findings = []
    for row in sorted(baselines, key=lambda item: item.get("artifact_id", "")):
        outcome = row.get("automated_pass_fail", "")
        notes = row.get("notes", "")
        failure_count = note_value(notes, "automated_failure_count") or ("1" if outcome == "FAIL" else "0")
        failure_names = note_value(notes, "automated_failure_names")
        warning_count = note_value(notes, "warning_count") or "0"
        warning_names = note_value(notes, "warning_names")
        manual_count = note_value(notes, "manual_check_count") or row.get("manual_check_prompts", "0") or "0"
        manual_names = note_value(notes, "manual_check_names")
        try:
            has_failures = int(failure_count) > 0
        except ValueError:
            has_failures = bool(failure_count)
        try:
            has_warnings = int(warning_count) > 0
        except ValueError:
            has_warnings = bool(warning_count)
        try:
            has_manual = int(manual_count) > 0
        except ValueError:
            has_manual = bool(manual_count)
        if outcome == "PASS" and not has_failures and not has_warnings and not has_manual:
            classification = "CLEAN_BASELINE"
        elif outcome == "PASS":
            classification = "USABLE_WITH_DOCUMENTED_BASELINE"
        else:
            classification = "BASELINE_REVIEW_REQUIRED"
        status = "PASS" if classification in {"CLEAN_BASELINE", "USABLE_WITH_DOCUMENTED_BASELINE"} else "BASELINE_REVIEW_REQUIRED"
        findings.append({
            "artifact_id": row.get("artifact_id", ""), "validator": row.get("validator", ""), "configuration": row.get("configuration", ""),
            "status": status, "classification": classification, "automated_pass_fail": outcome,
            "automated_failure_count": failure_count, "automated_failure_names": failure_names,
            "warning_count": warning_count, "warning_names": warning_names,
            "manual_check_count": manual_count, "manual_check_names": manual_names,
            "failed_rule_ids": row.get("relevant_rule_ids", ""), "failed_rule_text": row.get("relevant_rule_text", ""),
            "manual_check_prompts": row.get("manual_check_prompts", "0"),
            "operator_implication": "Manual prompts are not automated detections. Review failed checks against target operator assumptions before mutant interpretation; do not remove automatically."
        })
    path = ROOT / "analysis" / "generated" / "baseline_review.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        fields = ["artifact_id", "validator", "configuration", "status", "classification", "automated_pass_fail", "automated_failure_count", "automated_failure_names", "warning_count", "warning_names", "manual_check_count", "manual_check_names", "failed_rule_ids", "failed_rule_text", "manual_check_prompts", "operator_implication"]
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(findings)
    flagged = [row for row in findings if row["status"] != "PASS"]
    md = ROOT / "BASELINE_REVIEW_REQUIRED.md"
    if flagged:
        exclusion_rows = read_csv(ROOT / "data" / "mutant_exclusions.csv")
        excluded_pairs = {(row.get("source_golden", ""), row.get("operator", "")) for row in exclusion_rows if row.get("status")}
        resolutions = baseline_conflict_resolutions()
        lines = ["# Baseline review required", "", "Do not interpret active mutants implicated by a flagged baseline conflict. Explicitly excluded units remain outside the active analysis and are retained only as audit evidence.", ""]
        for row in flagged:
            excluded = [operator for golden, operator in excluded_pairs if golden == row["artifact_id"]]
            resolved = [item for item in resolutions if item.get("golden_id") == row["artifact_id"] and item.get("validator", "") == row["validator"]]
            if resolved:
                item = resolved[0]
                scope = f"Recorded resolution for `{item.get('operator', '')}`: `{item.get('verdict', '')}`. {item.get('action', '')}"
            elif excluded:
                scope = f"Affected operator(s) excluded from active analysis: {', '.join(sorted(excluded))}."
            else:
                scope = "Review whether the issue is unrelated, requires removing the golden, requires a replacement, or changes interpretation."
            lines.append(f"- `{row['artifact_id']}` / `{row['validator']} {row['configuration']}`: **{row['classification']}**; outcome=`{row['automated_pass_fail'] or 'UNKNOWN'}`; automated failures=`{row['automated_failure_names'] or 'none parsed'}`; rule IDs=`{row['failed_rule_ids'] or 'not parsed'}`; warnings=`{row['warning_names'] or 'none'}`; manual checks=`{row['manual_check_names'] or 'none'}`. {scope}")
        md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif baselines:
        md.write_text("# Baseline review\n\nAll ingested golden baseline records have an automated PASS result. Continue to apply baseline-delta logic; this is not a claim that semantic accessibility is perfect.\n", encoding="utf-8")
    return findings


def write_operator_conflicts(rows: list[dict]) -> list[dict]:
    """Screen failed baseline text for operator-specific conflicts.

    A passing baseline produces no conflict rows. Missing PAC/Acrobat evidence
    is intentionally not represented as a conflict here; the stage gate keeps
    those configurations pending instead of guessing from absent evidence.
    """
    hints = {
        "M01": ("reading order", "sequence"),
        "M02": ("content omission", "missing content", "not tagged"),
        "M03": ("heading", "heading level", "heading tags"),
        "M04": ("content association", "parent tree", "association"),
        "M05": ("content sequence", "reading order", "marked content"),
        "M06": ("lbl and lbody", "list item", "list containment", "duplicate list"),
        "M07": ("alternate text", "alt", "figure"),
        "M08": ("language", "lang", "natural language"),
        "M09": ("rolemap", "role map", "custom role", "unknown role"),
        "M10": ("table", "th", "td", "cell"),
    }
    fields = ["golden_id", "operator", "conflict", "baseline_rule", "reason", "action"]
    exclusion_rows = read_csv(ROOT / "data" / "mutant_exclusions.csv")
    excluded_pairs = {(row.get("source_golden", ""), row.get("operator", "")) for row in exclusion_rows if row.get("status")}
    resolutions = baseline_conflict_resolutions()
    conflicts = []
    for row in rows:
        if row.get("baseline_or_mutant") != "golden_baseline" or row.get("automated_pass_fail") != "FAIL":
            continue
        evidence = " ".join((row.get("relevant_rule_ids", ""), row.get("relevant_rule_text", ""))).lower()
        matched = False
        for operator, terms in hints.items():
            hits = [term for term in terms if term in evidence]
            if hits:
                matched = True
                excluded = (row.get("artifact_id", ""), operator) in excluded_pairs
                conflicts.append({
                    "golden_id": row.get("artifact_id", ""), "operator": operator,
                    "conflict": "TRUE", "baseline_rule": row.get("relevant_rule_ids", ""),
                    "reason": "Baseline failure text matches operator hint(s): " + ", ".join(hits),
                    "action": "Affected mutant is excluded; retain discrepancy as evidence and interpret remaining operators." if excluded else "STOP descendant interpretation and review baseline/operator interaction.",
                })
        if not matched:
            conflicts.append({
                "golden_id": row.get("artifact_id", ""), "operator": "ALL",
                "conflict": "REQUIRES_REVIEW", "baseline_rule": row.get("relevant_rule_ids", ""),
                "reason": "Baseline automated failure was not mapped to an operator by the conservative keyword screen.",
                "action": "Review all descendants before interpretation; do not infer safety.",
            })
    for conflict in conflicts:
        matches = [
            row for row in resolutions
            if row.get("golden_id") == conflict.get("golden_id")
            and row.get("validator", "") in {"", "Acrobat"}
            and row.get("operator") == conflict.get("operator")
        ]
        if matches:
            resolution = matches[0]
            conflict["reason"] += "; resolution recorded: " + resolution.get("resolution", "")
            conflict["action"] = resolution.get("verdict", "") + "; " + resolution.get("action", "")
    path = ROOT / "analysis" / "generated" / "baseline_operator_conflicts.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader(); writer.writerows(conflicts)
    return conflicts


def write_cross_validator_disagreements(rows: list[dict], conflicts: list[dict]) -> list[dict]:
    """Record baseline result disagreements without collapsing validator semantics."""
    baselines = [row for row in rows if row.get("baseline_or_mutant") == "golden_baseline" and row.get("validator") in {"PAC", "Acrobat", "veraPDF"}]
    by_golden: dict[str, dict[str, dict]] = {}
    for row in baselines:
        by_golden.setdefault(row.get("artifact_id", ""), {})[row.get("validator", "")] = row
    labels = {"PAC": "PAC Formal", "Acrobat": "Acrobat Full Check", "veraPDF": "veraPDF PDF/UA-1"}
    output: list[dict] = []
    order = ["PAC", "Acrobat", "veraPDF"]
    for golden, validator_rows in sorted(by_golden.items()):
        for index, left in enumerate(order):
            for right in order[index + 1:]:
                a = validator_rows.get(left)
                b = validator_rows.get(right)
                if not a or not b or not a.get("automated_pass_fail") or not b.get("automated_pass_fail") or a.get("automated_pass_fail") == b.get("automated_pass_fail"):
                    continue
                relevant = []
                for item in (a, b):
                    if item.get("automated_pass_fail") == "FAIL":
                        relevant.extend(filter(None, [item.get("relevant_rule_ids", ""), item.get("relevant_rule_text", "")]))
                affected = sorted({c.get("operator", "") for c in conflicts if c.get("golden_id") == golden and c.get("operator") not in {"", "ALL"}})
                if golden.endswith("_Scanned") and left == "PAC" and right == "veraPDF":
                    interpretation = "The golden has catalog /Lang='English'. PAC rejects the language identifier as formally invalid; veraPDF's rule evaluates presence of a catalog language and therefore passes. This is a validator-scope discrepancy, not evidence that either validator is incorrect."
                    action = "G09-M08 remains excluded from active cross-validator interpretation as TOOL_SPECIFIC_AMBIGUITY; retain the golden and both raw reports."
                elif golden.endswith("_BookChapter-german") and (left == "Acrobat" or right == "Acrobat"):
                    interpretation = "Acrobat checks Lbl/LBody child containment. G05 has 21 /Lbl nodes directly under /Link in the TOC/Reference branch, while the M06 target list has /Lbl and /LBody under /LI. M06 adds a separate duplicate /LI reference, so the baseline failure is retained as a documented delta and is not itself an M06 detection."
                    action = "Retain G05 unchanged; classify G05-M06 as VALID_WITH_BASELINE_DELTA and compare only new M06-relevant failures against the G05 baseline."
                else:
                    interpretation = "Validator-specific baseline discrepancy; compare exact automated rule names and do not attribute a mutant failure when the same relevant baseline rule is present."
                    action = "Retain raw evidence and review affected descendants before formal interpretation."
                output.append({
                    "golden_id": golden, "validator_A": labels[left], "result_A": a.get("automated_pass_fail", ""),
                    "validator_B": labels[right], "result_B": b.get("automated_pass_fail", ""),
                    "relevant_rule_or_check": "; ".join(dict.fromkeys(relevant)),
                    "interpretation": interpretation, "affects_mutation_operator": ";".join(affected), "action_taken": action,
                })
    path = ROOT / "analysis" / "generated" / "baseline_cross_validator_disagreements.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["golden_id", "validator_A", "result_A", "validator_B", "result_B", "relevant_rule_or_check", "interpretation", "affects_mutation_operator", "action_taken"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(output)
    return output


def task_matches_scope(task: dict[str, str], batch_filter: str = "", sub_batch_filter: str = "") -> bool:
    if batch_filter and task.get("batch_id") != batch_filter:
        return False
    if sub_batch_filter and task.get("sub_batch_id") != sub_batch_filter:
        return False
    return True


def scoped_report_status(task: dict[str, str]) -> tuple[bool, str]:
    report = evidence_path_for_task(task)
    if not report.exists():
        return False, "missing report"
    input_path = ROOT / task["filepath"]
    if not input_path.exists() or digest(input_path) != task.get("sha256", ""):
        return False, "input SHA-256 mismatch"
    if task.get("validator") == "PAC":
        _rule_ids, outcome, note = pdf_facts(report)
    elif task.get("validator") == "Acrobat":
        _rule_ids, outcome, note = acrobat_html_facts(report)
    else:
        outcome, note = "", "not a scoped PAC/Acrobat task"
    if task.get("validator") in {"PAC", "Acrobat"} and outcome not in {"PASS", "FAIL"}:
        return False, note or "report parse failed"
    return True, outcome or "evidence found"


def main(batch_filter: str = "", sub_batch_filter: str = "") -> int:
    queue = read_csv(ROOT / "manual_runs_todo.csv")
    pac_metadata = pac_formal_metadata()
    acro_metadata = acrobat_metadata()
    canonicalized = canonicalize_b01_reports(queue)
    pac_canonicalized = canonicalize_pac_exports(queue, batch_filter, sub_batch_filter)
    acrobat_canonicalized = canonicalize_acrobat_exports(queue, batch_filter, sub_batch_filter)
    existing = {row.get("record_id"): row for row in read_csv(ROOT / "data" / "validator_runs.csv") if row.get("record_id")}
    for task in queue:
        if task.get("baseline_or_mutant") == "setup" or task.get("validator") == "NVDA":
            continue
        if not task_matches_scope(task, batch_filter, sub_batch_filter):
            continue
        expected = evidence_path_for_task(task)
        if not expected.exists():
            continue
        artifact_id = task["artifact_id"]
        record_id = f"{task['validator']}::{task['configuration']}::{artifact_id}"
        report_hash = digest(expected)
        if expected.suffix.lower() == ".json":
            rule_ids, outcome, parse_note = json_facts(expected)
        elif expected.suffix.lower() == ".pdf":
            rule_ids, outcome, parse_note = pdf_facts(expected)
        elif expected.name.lower().endswith(".accreport.html") and task["validator"] == "Acrobat":
            rule_ids, outcome, parse_note = acrobat_html_facts(expected)
        else:
            rule_ids, outcome, parse_note = "", "", "non_machine_readable_evidence_requires_review"
        is_pac_formal = task["validator"] == "PAC" and task["configuration"] == "Formal"
        is_acrobat = task["validator"] == "Acrobat"
        prior = existing.get(record_id, {})
        preserve = prior.get("report_sha256") == report_hash
        existing[record_id] = {
            "record_id": record_id, "artifact_id": artifact_id,
            "baseline_or_mutant": task["baseline_or_mutant"], "source_golden": task["source_golden"],
            "operator": task["operator"], "file_sha256": task["sha256"], "validator": task["validator"],
            "configuration": task["configuration"], "validator_version": pac_metadata.get("pac_version", "REQUIRES_USER_VERIFICATION") if is_pac_formal else acro_metadata.get("version", "REQUIRES_USER_VERIFICATION") if is_acrobat else "REQUIRES_USER_VERIFICATION",
            "build": pac_metadata.get("pac_build", "REQUIRES_USER_VERIFICATION") if is_pac_formal else acro_metadata.get("build", "REQUIRES_USER_VERIFICATION") if is_acrobat else "REQUIRES_USER_VERIFICATION", "platform": pac_metadata.get("platform", "REQUIRES_USER_VERIFICATION") if is_pac_formal else acro_metadata.get("platform", "REQUIRES_USER_VERIFICATION") if is_acrobat else "REQUIRES_USER_VERIFICATION",
            "profile": "ua1" if task["validator"] == "veraPDF" else "Not applicable" if is_acrobat else "REQUIRES_USER_VERIFICATION",
            "PAC_AI_enabled": "true" if task["configuration"] == "AI" else "false",
            "run_timestamp": datetime.now(timezone.utc).isoformat(), "automated_pass_fail": outcome,
            "relevant_rule_ids": rule_ids, "relevant_rule_text": rule_text_from_note(parse_note), "manual_check_prompts": str(manual_prompt_count(expected)),
            "raw_report_path": str(expected.relative_to(ROOT)), "report_sha256": report_hash,
            "raw_detection_classification": prior.get("raw_detection_classification", "") if preserve else "", "baseline_status": "PENDING_BASELINE_DELTA",
            "baseline_file_sha256": "", "baseline_run_id": "", "detection_classification": prior.get("detection_classification", "") if preserve else "",
            "classification_reason": prior.get("classification_reason", "") if preserve else "No detection classification inferred; operator relevance and baseline delta require explicit evidence review.",
            "coder_1": prior.get("coder_1", "") if preserve else "", "coder_2": prior.get("coder_2", "") if preserve else "", "adjudication": prior.get("adjudication", "") if preserve else "", "notes": parse_note + ((";" + prior.get("notes", "")) if preserve and prior.get("notes", "") else ""),
        }
    manifest = {}
    manifest_path = ROOT / "data" / "mutants.jsonl"
    if manifest_path.exists():
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                manifest[item.get("mutant_id")] = item
    verapdf_runs = read_csv(ROOT / "data" / "verapdf_runs.csv")
    for run in verapdf_runs:
        artifact_id = run.get("artifact_id", "")
        report = ROOT / run.get("raw_report_path", "")
        if not artifact_id or not report.exists():
            continue
        item = manifest.get(artifact_id, {})
        is_mutant = run.get("baseline_or_mutant") == "mutant"
        rule_ids, outcome, parse_note = json_facts(report)
        record_id = f"veraPDF::PDF/UA-1 ua1::{artifact_id}"
        prior = existing.get(record_id, {})
        preserve = prior.get("report_sha256") == digest(report)
        existing[record_id] = {
            "record_id": record_id, "artifact_id": artifact_id,
            "baseline_or_mutant": "mutant" if is_mutant else "golden_baseline",
            "source_golden": run.get("source_golden") or artifact_id,
            "operator": item.get("operator", "") if is_mutant else "",
            "file_sha256": run.get("file_sha256", ""), "validator": "veraPDF",
            "configuration": "PDF/UA-1 ua1", "validator_version": run.get("verapdf_version", "REQUIRES_USER_VERIFICATION"),
            "build": "", "platform": "", "profile": run.get("profile", "ua1"), "PAC_AI_enabled": "false",
            "run_timestamp": run.get("run_timestamp", ""), "automated_pass_fail": outcome,
            "relevant_rule_ids": rule_ids, "relevant_rule_text": rule_text_from_note(parse_note), "manual_check_prompts": str(manual_prompt_count(report)),
            "raw_report_path": run.get("raw_report_path", ""), "report_sha256": digest(report),
            "raw_detection_classification": prior.get("raw_detection_classification", "") if preserve else "", "baseline_status": "BASELINE_RECORD" if not is_mutant else "PENDING_BASELINE_DELTA",
            "baseline_file_sha256": "", "baseline_run_id": "", "detection_classification": prior.get("detection_classification", "") if preserve else "",
            "classification_reason": prior.get("classification_reason", "") if preserve else "veraPDF report ingested; operator relevance and baseline delta remain explicit review fields.",
            "coder_1": prior.get("coder_1", "") if preserve else "", "coder_2": prior.get("coder_2", "") if preserve else "", "adjudication": prior.get("adjudication", "") if preserve else "", "notes": parse_note + ((";" + prior.get("notes", "")) if preserve and prior.get("notes", "") else ""),
        }
    rows = list(existing.values())
    for row in rows:
        if row["baseline_or_mutant"] != "mutant":
            row["baseline_status"] = "BASELINE_RECORD"
            continue
        candidates = [r for r in rows if r["baseline_or_mutant"] == "golden_baseline" and r["validator"] == row["validator"] and r["configuration"] == row["configuration"] and r["artifact_id"] == row["source_golden"]]
        if not candidates:
            row["baseline_status"] = "MISSING_BASELINE"
        else:
            base = candidates[0]
            row["baseline_file_sha256"] = base["file_sha256"]
            row["baseline_run_id"] = base["record_id"]
            base_outcome = base.get("automated_pass_fail", "")
            row["baseline_status"] = "BASELINE_PASS" if base_outcome == "PASS" else "BASELINE_FAIL" if base_outcome == "FAIL" else "BASELINE_UNCLASSIFIED"
            if row.get("relevant_rule_ids") and base.get("relevant_rule_ids"):
                new_rules = sorted(set(row["relevant_rule_ids"].split(";")) - set(base["relevant_rule_ids"].split(";")))
                row["notes"] = (row.get("notes", "") + ";new_rule_ids=" + ";".join(new_rules)).strip(";")
    out = ROOT / "data" / "validator_runs.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=VALIDATOR_FIELDS)
        writer.writeheader(); writer.writerows(sorted(rows, key=lambda r: r["record_id"]))
    baseline_findings = write_baseline_review(rows)
    operator_conflicts = write_operator_conflicts(rows)
    cross_disagreements = write_cross_validator_disagreements(rows, operator_conflicts)
    b01_complete, b01_missing = b01_status(queue, pac_metadata)
    b02_complete, b02_missing = b02_status(queue, acro_metadata)
    # Preserve evidence completion in the queue, then regenerate staged/deferred rows.
    for task in queue:
        if task.get("batch_id") == "B01_GOLDEN_PAC_FORMAL":
            task["status"] = "COMPLETE" if b01_complete else "TODO"
        elif task.get("batch_id") == "B02_GOLDEN_ACROBAT":
            task["status"] = "COMPLETE" if b02_complete else "TODO"
    with (ROOT / "manual_runs_todo.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(queue[0]) if queue else [])
        if queue:
            writer.writeheader(); writer.writerows(queue)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from pdfa11ymut.phase2 import write_queue
    write_queue()
    delta = ROOT / "data" / "baseline_deltas.csv"
    with delta.open("w", newline="", encoding="utf-8") as fh:
        fields = ["record_id", "artifact_id", "source_golden", "validator", "configuration", "baseline_status", "baseline_run_id", "baseline_file_sha256", "mutant_file_sha256", "delta_state", "notes"]
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader()
        for row in sorted(rows, key=lambda r: r["record_id"]):
            if row["baseline_or_mutant"] == "mutant":
                writer.writerow({"record_id": row["record_id"], "artifact_id": row["artifact_id"], "source_golden": row["source_golden"], "validator": row["validator"], "configuration": row["configuration"], "baseline_status": row["baseline_status"], "baseline_run_id": row["baseline_run_id"], "baseline_file_sha256": row["baseline_file_sha256"], "mutant_file_sha256": row["file_sha256"], "delta_state": "REQUIRES_CLASSIFICATION" if row["baseline_status"] == "BASELINE_PASS" else row["baseline_status"], "notes": row["notes"]})
    print(f"B01_GOLDEN_PAC_FORMAL: {b01_report_count(queue)}/9 complete")
    b02_tasks = [row for row in queue if row.get("batch_id") == "B02_GOLDEN_ACROBAT"]
    print(f"B02_GOLDEN_ACROBAT: {b02_report_count(queue)}/{len(b02_tasks)} native reports found; {b02_valid_count(queue, acro_metadata)}/{len(b02_tasks)} valid")
    if canonicalized:
        print(f"Canonicalized {len(canonicalized)} uniquely mapped PAC report(s); originals retained.")
    if pac_canonicalized:
        print(f"PAC export reconciliation: {len([item for item in pac_canonicalized if ' -> ' in item])} canonical copies created or validated.")
        for item in pac_canonicalized:
            print("  " + item)
    if acrobat_canonicalized:
        print(f"Acrobat export reconciliation: {len([item for item in acrobat_canonicalized if ' -> ' in item])} canonical copies created or validated.")
        for item in acrobat_canonicalized:
            print("  " + item)
    if b01_missing:
        print("B01 remaining: " + "; ".join(b01_missing))
    if b02_missing:
        print("B02 remaining: " + "; ".join(b02_missing))
    print(f"Ingested {len(rows)} canonical validator records; no detection classifications were inferred.")
    if any(row["status"] == "BASELINE_REVIEW_REQUIRED" for row in baseline_findings):
        print("BASELINE_REVIEW_REQUIRED: see BASELINE_REVIEW_REQUIRED.md")
    if operator_conflicts:
        print(f"Baseline operator conflicts requiring review: {len(operator_conflicts)}; see analysis/generated/baseline_operator_conflicts.csv")
    if cross_disagreements:
        print(f"Cross-validator baseline disagreements: {len(cross_disagreements)}; see analysis/generated/baseline_cross_validator_disagreements.csv")
    if batch_filter or sub_batch_filter:
        scoped = [
            task for task in queue
            if task.get("baseline_or_mutant") == "mutant"
            and task_matches_scope(task, batch_filter, sub_batch_filter)
        ]
        complete = []
        missing = []
        for task in scoped:
            ok, detail = scoped_report_status(task)
            (complete if ok else missing).append(f"{task['artifact_id']} ({detail})")
        label = sub_batch_filter or batch_filter
        print(f"{label}: {len(complete)}/{len(scoped)} expected reports valid")
        if missing:
            print("Missing or invalid: " + "; ".join(missing))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest hash-linked validator evidence without inferring detections.")
    parser.add_argument("--batch", default="", help="Canonical queue batch ID, such as B04_MUTANT_PAC_FORMAL.")
    parser.add_argument("--sub-batch", default="", help="Canonical operator sub-batch, such as B04_M01.")
    args = parser.parse_args()
    raise SystemExit(main(args.batch, args.sub_batch))
