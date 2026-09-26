#!/usr/bin/env python3
"""Hash-link PAC, Acrobat, and veraPDF negative-control evidence.

This script is deliberately fail-closed: a control is marked COMPLETE only when
all three validator artifacts exist, are hash recorded, and contain the expected
control filename/profile markers.  It records validator observations; it does
not infer detections or study accuracy.
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "controls.csv"
MANIFEST_PATH = ROOT / "data" / "release_manifest.json"
PAC_DIR = ROOT / "evidence" / "controls" / "pac"
ACROBAT_DIR = ROOT / "evidence" / "controls" / "acrobat"
VERAPDF_DIR = ROOT / "evidence" / "controls" / "verapdf"
SUMMARY_PATH = ROOT / "evidence" / "controls" / "validator_summary.json"
ACROBAT_METADATA_PATH = ROOT / "data" / "acrobat_run_metadata.json"


NATIVE_FIELDS = [
    "pac_report_path",
    "pac_report_sha256",
    "pac_version",
    "pac_profile",
    "pac_failed_rules",
    "pac_warned_rules",
    "pac_parse_status",
    "acrobat_report_path",
    "acrobat_report_sha256",
    "acrobat_version",
    "acrobat_profile",
    "acrobat_passed_rules",
    "acrobat_failed_rules",
    "acrobat_manual_rules",
    "acrobat_skipped_rules",
    "acrobat_parse_status",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def parse_pac(control_id: str, path: Path) -> dict[str, str]:
    result = {field: "" for field in NATIVE_FIELDS[:7]}
    result["pac_report_path"] = relative(path)
    result["pac_report_sha256"] = sha256(path)
    try:
        import fitz  # PyMuPDF, already used by the study's PDF tooling.

        document = fitz.open(path)
        text = "\n".join(page.get_text() for page in document)
        document.close()
    except Exception as exc:  # pragma: no cover - exercised by a missing runtime
        result["pac_parse_status"] = f"FAIL: {type(exc).__name__}"
        return result

    version_match = re.search(r"Version:\s*([^\r\n]+)", text)
    result["pac_version"] = version_match.group(1).strip() if version_match else ""
    result["pac_profile"] = "PDF/UA-1" if "PDF/UA-1" in text else ""

    # PAC's exported text places three values after every checkpoint row:
    # passed, warned, failed.  Restrict parsing to the checkpoint table so
    # document metadata numbers cannot be mistaken for rule counts.
    table_match = re.search(r"CHECKPOINT\s+PASSED\s+WARNED\s+FAILED(.*?)RESULT", text, re.S)
    passed = warned = failed = 0
    if table_match:
        cells = re.findall(r"(?m)^\s*(\d+|-)\s*$", table_match.group(1))
        for index in range(0, len(cells) - 2, 3):
            triplet = cells[index : index + 3]
            passed += 0 if triplet[0] == "-" else int(triplet[0])
            warned += 0 if triplet[1] == "-" else int(triplet[1])
            failed += 0 if triplet[2] == "-" else int(triplet[2])
    result["pac_failed_rules"] = str(failed)
    result["pac_warned_rules"] = str(warned)

    filename_ok = re.search(r"Filename\s+" + re.escape(control_id) + r"\.pdf\b", text) is not None
    required_ok = filename_ok and result["pac_version"] == "26.1.0.0" and result["pac_profile"] == "PDF/UA-1"
    result["pac_parse_status"] = "PASS" if required_ok else "FAIL"
    return result


def parse_acrobat(control_id: str, path: Path, version: str) -> dict[str, str]:
    result = {field: "" for field in NATIVE_FIELDS[7:]}
    result["acrobat_report_path"] = relative(path)
    result["acrobat_report_sha256"] = sha256(path)
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # pragma: no cover
        result["acrobat_parse_status"] = f"FAIL: {type(exc).__name__}"
        return result

    plain = html.unescape(re.sub(r"<[^>]+>", "\n", raw))

    def count(label: str) -> str:
        match = re.search(r"(?:^|\n)\s*" + re.escape(label) + r"\s*:\s*(\d+)", plain, re.I)
        return match.group(1) if match else ""

    filename_ok = re.search(r"Filename:\s*" + re.escape(control_id) + r"\.pdf\b", plain, re.I) is not None
    result["acrobat_version"] = version
    result["acrobat_profile"] = "Full Check / all pages"
    result["acrobat_passed_rules"] = count("Passed")
    result["acrobat_failed_rules"] = count("Failed")
    result["acrobat_manual_rules"] = count("Needs manual check")
    result["acrobat_skipped_rules"] = count("Skipped")
    required_ok = (
        filename_ok
        and "Accessibility Report" in plain
        and all(result[field] != "" for field in (
            "acrobat_passed_rules",
            "acrobat_failed_rules",
            "acrobat_manual_rules",
            "acrobat_skipped_rules",
        ))
    )
    result["acrobat_parse_status"] = "PASS" if required_ok else "FAIL"
    return result


def main() -> int:
    rows = list(csv.DictReader(CSV_PATH.open(newline="", encoding="utf-8")))
    if len(rows) != 18:
        raise SystemExit(f"Expected 18 controls, found {len(rows)}")

    metadata = json.loads(ACROBAT_METADATA_PATH.read_text(encoding="utf-8"))
    acrobat_version = str(metadata.get("version", ""))
    if not acrobat_version:
        raise SystemExit("Acrobat metadata has no version")

    for field in NATIVE_FIELDS:
        if field not in (rows[0] if rows else {}):
            for row in rows:
                row[field] = ""

    summary_rows = []
    complete = 0
    for row in rows:
        control_id = row["control_id"]
        pac_path = PAC_DIR / f"{control_id}.pdf"
        acrobat_path = ACROBAT_DIR / f"{control_id}.pdf.accreport.html"
        verapdf_path = ROOT / row["verapdf_report_path"].replace("\\", "/")
        native = {}
        if pac_path.is_file():
            native.update(parse_pac(control_id, pac_path))
        else:
            native.update({field: "" for field in NATIVE_FIELDS[:7]})
            native["pac_parse_status"] = "FAIL: missing"
        if acrobat_path.is_file():
            native.update(parse_acrobat(control_id, acrobat_path, acrobat_version))
        else:
            native.update({field: "" for field in NATIVE_FIELDS[7:]})
            native["acrobat_parse_status"] = "FAIL: missing"
        row.update(native)

        verapdf_ok = verapdf_path.is_file() and row.get("verapdf_parse_status") == "PASS"
        is_complete = (
            verapdf_ok
            and row.get("pac_parse_status") == "PASS"
            and row.get("acrobat_parse_status") == "PASS"
        )
        row["status"] = "COMPLETE" if is_complete else "VERAPDF_EXECUTED_PENDING_PAC_ACROBAT"
        row["notes"] = (
            "Artifact verified; veraPDF/PAC/Acrobat control reports present and hash-linked; "
            "no control is a positive study result."
            if is_complete
            else "Fail-closed: one or more validator reports are missing or failed parsing."
        )
        complete += int(is_complete)
        summary_rows.append({
            "control_id": control_id,
            "status": row["status"],
            "pac_sha256": row.get("pac_report_sha256", ""),
            "acrobat_sha256": row.get("acrobat_report_sha256", ""),
            "verapdf_sha256": row.get("verapdf_report_sha256", ""),
            "pac_parse_status": row.get("pac_parse_status", ""),
            "acrobat_parse_status": row.get("acrobat_parse_status", ""),
        })

    fieldnames = list(rows[0].keys())
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    counts = manifest.setdefault("counts", {})
    counts["negative_control_rows_executed"] = complete
    counts["negative_control_rows_pac_executed"] = sum(row["pac_parse_status"] == "PASS" for row in rows)
    counts["negative_control_rows_acrobat_executed"] = sum(row["acrobat_parse_status"] == "PASS" for row in rows)
    counts["negative_control_rows_complete"] = complete
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    SUMMARY_PATH.write_text(json.dumps({
        "scope": "18 negative controls",
        "native_evidence": "PAC PDF and Acrobat native HTML reports",
        "acrobat_version": acrobat_version,
        "rows": summary_rows,
        "complete_rows": complete,
        "interpretation": "Evidence inventory only; no detection or accuracy classification is inferred.",
    }, indent=2) + "\n", encoding="utf-8")

    print(f"Ingested {len(rows)} controls; COMPLETE={complete}; PAC/Acrobat parsing is fail-closed.")
    return 0 if complete == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
