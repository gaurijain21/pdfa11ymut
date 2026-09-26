from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(command: list[str]) -> int:
    """Run a verification-only command.

    This entry point deliberately does not invoke generation, analysis rebuilds,
    figure builders, queue writers, or any other command that can rewrite a
    canonical artifact.  Use scripts/regenerate_scratch.py for regeneration.
    """
    print("$", " ".join(command))
    return subprocess.run(command, cwd=ROOT).returncode


def main() -> int:
    failures = 0
    failures += run([sys.executable, "-c", "import pypdf, PIL, yaml, pymupdf; print('Python dependencies available')"]) != 0
    failures += run([sys.executable, "scripts/verify_study_state.py", "--verify"]) != 0
    # check_evidence.py is read-only and reports external/manual completeness.
    failures += run([sys.executable, "scripts/check_evidence.py"]) not in (0, 1, 2)
    golden = sorted((ROOT / "corpus" / "golden").glob("*.pdf"))
    todo_path = ROOT / "manual_runs_todo.csv"
    queue_rows = []
    if todo_path.exists():
        with todo_path.open(newline="", encoding="utf-8-sig") as fh:
            queue_rows = list(csv.DictReader(fh))
    todo_rows = [row for row in queue_rows if row.get("status") == "TODO"]
    pac_ai_todo = sum(row.get("batch_id") in {"B07_GOLDEN_PAC_AI_SELECTED", "B08_MUTANT_PAC_AI_SELECTED"} for row in todo_rows)
    provenance_todo = sum(row.get("batch_id") == "B00_CORPUS_PROVENANCE_REVIEW" for row in todo_rows)
    other_todo = len(todo_rows) - pac_ai_todo - provenance_todo
    if not golden:
        print("Verification incomplete: no golden PDFs are present. See USER_ACTION_REQUIRED.md.")
        return 2
    print(
        "Verification completed without modifying canonical artifacts; "
        f"{len(queue_rows)} total queue rows, {len(todo_rows)} TODO "
        f"({pac_ai_todo} PAC-AI deferred, {provenance_todo} provenance, {other_todo} other), "
        f"{len(queue_rows) - len(todo_rows)} complete."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
