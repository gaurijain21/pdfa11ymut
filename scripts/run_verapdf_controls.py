"""Run the installed veraPDF PDF/UA-1 profile over all negative controls."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "data" / "controls.csv"
BAT = ROOT / "tools" / "validators" / "verapdf-app" / "verapdf.bat"
JAVA_BIN = ROOT / "tools" / "validators" / "java" / "jdk-21.0.12.1+1-jre" / "bin"
REPORT_DIR = ROOT / "evidence" / "controls" / "verapdf"


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if not BAT.is_file():
        raise SystemExit(f"veraPDF executable not found: {BAT}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with CONTROLS.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        pdf = ROOT / row["output_pdf"]
        if not pdf.is_file():
            raise SystemExit(f"missing control PDF: {pdf}")
        command = ["cmd.exe", "/d", "/c", str(BAT), "--format", "json", "--flavour", "ua1", str(pdf)]
        env = os.environ.copy()
        env["Path"] = str(JAVA_BIN) + os.pathsep + env.get("Path", "")
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        report_path = REPORT_DIR / f"{row['control_id']}.json"
        report_path.write_bytes(completed.stdout)
        try:
            report = json.loads(completed.stdout.decode("utf-8-sig"))
            result = report["report"]["jobs"][0]["validationResult"][0]
            details = result.get("details", {})
            failed_rules = details.get("failedRules", 0)
            passed_rules = details.get("passedRules", 0)
            parse_status = "PASS"
        except Exception as exc:
            failed_rules = ""
            passed_rules = ""
            parse_status = f"PARSE_ERROR:{exc}"
        row["verapdf_report_path"] = str(report_path.relative_to(ROOT))
        row["verapdf_report_sha256"] = digest_bytes(completed.stdout)
        row["verapdf_version"] = "1.30.2"
        row["verapdf_profile"] = "ua1"
        row["verapdf_exit_code"] = str(completed.returncode)
        row["verapdf_failed_rules"] = str(failed_rules)
        row["verapdf_passed_rules"] = str(passed_rules)
        row["verapdf_parse_status"] = parse_status
        row["status"] = "VERAPDF_EXECUTED_PENDING_PAC_ACROBAT"
        row["notes"] = "Artifact verified and veraPDF 1.30.2 PDF/UA-1 executed; PAC and Acrobat control runs remain pending."
        if completed.stderr:
            (REPORT_DIR / f"{row['control_id']}.stderr.txt").write_bytes(completed.stderr)
    fieldnames = list(rows[0])
    with CONTROLS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"controls": len(rows), "verapdf_runs": len(rows), "version": "1.30.2", "profile": "ua1", "status": "PENDING_PAC_ACROBAT"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
