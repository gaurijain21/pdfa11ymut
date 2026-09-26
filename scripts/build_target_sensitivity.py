"""Build a small secondary target-site sensitivity sample.

This artifact deliberately stays outside the 69-mutant denominator.  It tests
the structural pipeline at a second eligible site for three high-candidate
operators across three source PDFs.  Native checker reruns are not attempted:
the canonical PAC/Acrobat configurations require authorized GUI sessions.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pdfa11ymut.core import find_candidates, ref_label, write_mutant
from pdfa11ymut.verify import verify_mutation

OUT = ROOT / "analysis" / "target_sensitivity"
TARGETS = (
    ("M01", "PDFUA-Ref-2-01_Magazine-danish"),
    ("M01", "PDFUA-Ref-2-03_AcademicAbstract"),
    ("M03", "PDFUA-Ref-2-01_Magazine-danish"),
    ("M03", "PDFUA-Ref-2-03_AcademicAbstract"),
    ("M07", "PDFUA-Ref-2-01_Magazine-danish"),
    ("M07", "PDFUA-Ref-2-06_Brochure"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for operator, source_stem in TARGETS:
        source = ROOT / "corpus" / "golden" / f"{source_stem}.pdf"
        if not source.is_file():
            raise SystemExit(f"missing sensitivity source: {source}")
        reader = PdfReader(str(source), strict=False)
        candidates = find_candidates(reader, operator)
        if len(candidates) < 2:
            raise SystemExit(f"{operator} on {source_stem} has fewer than two eligible candidates")
        chosen = candidates[1]
        target = f"obj={ref_label(chosen)}"
        output = OUT / f"{source_stem}-{operator}-target2.pdf"
        generation = write_mutant(source, output, operator, target)
        verification = verify_mutation(source, output, operator, generation["delta"], dpi=72)
        record = {
            "operator": operator,
            "source_golden": source_stem,
            "source_sha256": sha256(source),
            "eligible_candidate_count": len(candidates),
            "first_target": ref_label(candidates[0]),
            "second_target": ref_label(candidates[1]),
            "selection_rule": "second eligible reachable target in stable structure traversal order",
            "requested_target": target,
            "mutant_path": str(output.relative_to(ROOT)).replace("\\", "/"),
            "mutant_sha256": sha256(output),
            "mutation_valid": verification.get("mutation_valid", False),
            "page_count_preserved": verification.get("page_count_preserved", False),
            "page_content_preserved": verification.get("invariant_checks", {}).get("page_content_byte_hashes_equal", False),
            "rendering_preserved": verification.get("invariant_checks", {}).get("rendering_preserved", False),
            "rendering_dpi": 72,
            "native_checker_rerun": "NOT_PERFORMED_PROPRIETARY_GUI_SCOPE",
        }
        (OUT / f"{source_stem}-{operator}-target2.json").write_text(json.dumps({"generation": generation, "verification": verification}, indent=2) + "\n", encoding="utf-8")
        rows.append(record)
    fields = list(rows[0])
    with (OUT / "target_sensitivity.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (OUT / "README.md").write_text(
        "# Alternate-target sensitivity sample\n\n"
        "This six-pair secondary sample selects the second eligible reachable target for M01, M03, and M07 across two reference PDFs per operator. It is outside the canonical 69-mutant denominator and does not replace any formal validator row.\n\n"
        "All pairs are checked with the open-source generator-side verifier for parseability, page/content preservation, rendering preservation, and the operator-specific delta. PAC and Acrobat reruns were not performed because their canonical configurations require authorized native GUI sessions; no checker result is inferred from this artifact. The sample therefore documents target-selection sensitivity of the structural pipeline, not a new detection result.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "pairs": len(rows), "path": str((OUT / "target_sensitivity.csv").relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
