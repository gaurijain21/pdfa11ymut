"""Run the complete veraPDF PDF/UA-1 batch with hash-addressed raw reports.

The script intentionally refuses to guess a validator executable. Set VERAPDF_CMD
or pass --executable after installing veraPDF. The default profile is ua1 and the
raw JSON from every invocation is retained under evidence/verapdf/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def discover() -> list[tuple[str, Path, str, str]]:
    items = []
    for path in sorted((ROOT / "corpus" / "golden").glob("*.pdf")):
        items.append(("golden", path, path.stem, ""))
    manifest = ROOT / "data" / "mutants.jsonl"
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("status") == "valid":
            path = Path(row["mutant_pdf"])
            items.append(("mutant", path, row["mutant_id"], Path(row["source_pdf"]).stem))
    return items


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", help="veraPDF executable or verapdf.bat; defaults to VERAPDF_CMD or PATH")
    parser.add_argument("--flavour", default="ua1", choices=["ua1", "ua2"], help="Built-in PDF/UA profile")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    command = args.executable or os.environ.get("VERAPDF_CMD") or "verapdf"
    command_parts = shlex.split(command, posix=False) if isinstance(command, str) else [command]
    version_result = subprocess.run(command_parts + ["--version"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace") if not args.dry_run else None
    verapdf_version = ((version_result.stdout or version_result.stderr).strip() if version_result else "DRY_RUN") or "REQUIRES_USER_VERIFICATION"
    items = discover()
    if len(items) != 84:
        raise SystemExit(f"Expected 84 PDFs (9 goldens + 75 mutants), found {len(items)}")
    report_dir = ROOT / "evidence" / "verapdf"
    report_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for kind, path, artifact_id, source_golden in items:
        file_hash = digest(path)
        report = report_dir / f"{artifact_id}__{file_hash}.json"
        cmd = command_parts + ["--format", "json", "--flavour", args.flavour, "--addlogs", "--maxfailuresdisplayed", "-1", str(path)]
        if args.dry_run:
            print(" ".join(shlex.quote(part) for part in cmd))
            continue
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        report.write_text(completed.stdout, encoding="utf-8")
        rows.append({
            "artifact_id": artifact_id, "baseline_or_mutant": kind,
            "source_golden": source_golden or artifact_id, "file_sha256": file_hash,
            "filepath": str(path.relative_to(ROOT)), "validator": "veraPDF",
            "profile": args.flavour, "verapdf_version": verapdf_version, "exit_code": completed.returncode,
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "raw_report_path": str(report.relative_to(ROOT)),
            "stderr": completed.stderr.strip(),
        })
    if not args.dry_run:
        with (ROOT / "data" / "verapdf_runs.csv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
        print(f"Wrote {len(rows)} hash-addressed veraPDF reports to {report_dir}")
    return 0


if __name__ == "__main__":
    main()
