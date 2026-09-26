"""Prepare and independently verify the 18 negative-control artifacts.

This command does not run PAC, Acrobat, or veraPDF. It creates byte-preserved
no-op copies and metadata-only benign copies, verifies their intended invariants
with pypdf, PyMuPDF, and Poppler rendering, and records the validator-run gate
explicitly as pending.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter
import pymupdf


ROOT = Path(__file__).resolve().parents[1]
CONTROLS = ROOT / "data" / "controls.csv"
ARTIFACTS = ROOT / "corpus" / "controls"
EVIDENCE = ROOT / "evidence" / "controls"
POPPLER = Path(
    r"C:\Users\iamga\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe"
)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def page_contents(path: Path) -> list[str]:
    reader = PdfReader(str(path), strict=False)
    values = []
    for page in reader.pages:
        contents = page.get_contents()
        values.append(hashlib.sha256(contents.get_data() if contents else b"").hexdigest())
    return values


def page_boxes(path: Path) -> list[tuple[float, float, float, float]]:
    doc = pymupdf.open(str(path))
    try:
        return [tuple(round(float(v), 6) for v in page.rect) for page in doc]
    finally:
        doc.close()


def render_equal(source: Path, output: Path, scratch: Path) -> dict:
    source_prefix = scratch / "source"
    output_prefix = scratch / "output"
    for prefix, path in ((source_prefix, source), (output_prefix, output)):
        subprocess.run(
            [str(POPPLER), "-r", "150", "-png", "-singlefile", str(path), str(prefix)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    with Image.open(str(source_prefix) + ".png") as left, Image.open(str(output_prefix) + ".png") as right:
        left = left.convert("RGB")
        right = right.convert("RGB")
        if left.size != right.size:
            return {"equal": False, "different_pixels": None, "dimensions": [left.size, right.size]}
        diff = ImageChops.difference(left, right)
        bbox = diff.getbbox()
        return {
            "equal": bbox is None,
            "different_pixels": 0 if bbox is None else sum(1 for pixel in diff.getdata() if pixel != (0, 0, 0)),
            "dimensions": [left.size, right.size],
        }


def make_benign(source: Path, output: Path, control_id: str) -> None:
    writer = PdfWriter(clone_from=str(source))
    writer.add_metadata({"/Subject": f"PDFa11yMut benign control {control_id}"})
    with output.open("wb") as fh:
        writer.write(fh)


def verify_control(row: dict[str, str]) -> dict:
    control_id = row["control_id"]
    source = ROOT / row["source_pdf"]
    output = ARTIFACTS / f"{control_id}.pdf"
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    if row["control_type"] == "no-op":
        shutil.copyfile(source, output)
    elif row["control_type"] == "benign":
        make_benign(source, output, control_id)
    else:
        raise ValueError(f"unknown control type: {row['control_type']}")

    with tempfile.TemporaryDirectory(prefix=f"pdfa11ymut-control-{control_id}-") as temp:
        source_reader = PdfReader(str(source), strict=False)
        output_reader = PdfReader(str(output), strict=False)
        render = render_equal(source, output, Path(temp))
        source_doc = pymupdf.open(str(source))
        output_doc = pymupdf.open(str(output))
        try:
            source_page_count = len(source_doc)
            output_page_count = len(output_doc)
        finally:
            source_doc.close()
            output_doc.close()

    source_hash = digest(source)
    output_hash = digest(output)
    content_equal = page_contents(source) == page_contents(output)
    boxes_equal = page_boxes(source) == page_boxes(output)
    metadata = output_reader.metadata or {}
    benign_metadata_present = row["control_type"] == "no-op" or bool(metadata.get("/Subject", "").startswith("PDFa11yMut benign control"))
    result = {
        "control_id": control_id,
        "control_type": row["control_type"],
        "source_pdf": str(source.relative_to(ROOT)),
        "output_pdf": str(output.relative_to(ROOT)),
        "source_sha256": source_hash,
        "output_sha256": output_hash,
        "byte_identical": source_hash == output_hash,
        "parseable_pypdf": len(source_reader.pages) == len(output_reader.pages),
        "parseable_pymupdf": source_page_count == output_page_count,
        "page_count_preserved": source_page_count == output_page_count,
        "page_content_bytes_equal": content_equal,
        "page_boxes_equal": boxes_equal,
        "rendering": render,
        "benign_metadata_present": benign_metadata_present,
        "artifact_verification": "PASS",
        "validator_execution": "PENDING_EXTERNAL_VALIDATORS",
        "interpretation": "Artifact is prepared and independently verified; no validator result is inferred.",
    }
    if not all((result["parseable_pypdf"], result["parseable_pymupdf"], result["page_count_preserved"], result["page_content_bytes_equal"], result["page_boxes_equal"], result["rendering"]["equal"], result["benign_metadata_present"])):
        result["artifact_verification"] = "FAIL"
        raise RuntimeError(json.dumps(result, indent=2))
    evidence_path = EVIDENCE / f"{control_id}.json"
    evidence_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    with CONTROLS.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    results = [verify_control(row) for row in rows]
    for row, result in zip(rows, results):
        row["output_pdf"] = result["output_pdf"]
        row["status"] = "ARTIFACT_VERIFIED_PENDING_VALIDATORS"
        row["evidence_path"] = str((EVIDENCE / f"{row['control_id']}.json").relative_to(ROOT))
        row["notes"] = "Artifact independently verified; PAC, Acrobat, and veraPDF execution remains pending and no validator result is inferred."
    with CONTROLS.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"controls": len(results), "artifact_verified": len(results), "validator_runs": 0, "status": "PENDING_EXTERNAL_VALIDATORS"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
