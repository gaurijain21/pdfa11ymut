"""Build a minimal, flattened arXiv TeX source package."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from datetime import date
from pathlib import Path


GENERATED_INPUTS = {
    r"\input{../analysis/generated/results_fragment.tex}": "results_fragment.tex",
    r"\input{../analysis/generated/operator_table_fragment.tex}": "operator_table_fragment.tex",
    r"\input{../analysis/generated/study_macros.tex}": "study_macros.tex",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    stamp = date.today().isoformat()
    release_dir = root / "release"
    output = (args.output or release_dir / f"arxiv_submission_{stamp}.zip").resolve()
    digest_path = output.with_suffix(output.suffix + ".sha256")
    manifest_path = output.with_suffix(".manifest.txt")
    staging = root / "tmp" / f"arxiv_submission_{stamp}"
    staging.mkdir(parents=True, exist_ok=True)

    source = (root / "paper" / "pdfa11ymut_ieee.tex").read_text(encoding="utf-8")
    for repository_input, package_name in GENERATED_INPUTS.items():
        if source.count(repository_input) != 1:
            raise SystemExit(f"expected exactly one repository-relative input: {repository_input}")
        source = source.replace(repository_input, rf"\input{{{package_name}}}")
        generated = root / "analysis" / "generated" / package_name
        if not generated.is_file():
            raise SystemExit(f"missing generated input: {generated}")
        (staging / package_name).write_text(generated.read_text(encoding="utf-8"), encoding="utf-8")
    (staging / "pdfa11ymut_ieee.tex").write_text(source, encoding="utf-8")

    source_files = sorted(path.name for path in staging.iterdir() if path.is_file())
    if source_files != ["operator_table_fragment.tex", "pdfa11ymut_ieee.tex", "results_fragment.tex", "study_macros.tex"]:
        raise SystemExit(f"unexpected arXiv source package contents: {source_files}")
    source_text = "\n".join((staging / name).read_text(encoding="utf-8", errors="replace") for name in source_files)
    forbidden = [r"C:\\Users\\", "C:/Users/", "<script", "javascript:", "\\input{../"]
    found = [fragment for fragment in forbidden if fragment.lower() in source_text.lower()]
    if found:
        raise SystemExit(f"forbidden arXiv source content: {found}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in source_files:
            archive.write(staging / name, name)

    package_hash = sha256(output)
    digest_path.write_text(f"{package_hash}  {output.name}\n", encoding="utf-8")
    manifest_path.write_text(
        "\n".join(
            [
                "PDFa11yMut arXiv source package",
                f"date: {stamp}",
                f"package: {output.name}",
                f"package_sha256: {package_hash}",
                f"files: {', '.join(source_files)}",
                "compile_boundary: arXiv must compile the source with its selected TeX Live processor; local Tectonic compilation is a preflight only",
                "source_boundary: no PDF, auxiliary files, logs, hidden files, repository evidence, or JavaScript included",
                "official_guidance: https://info.arxiv.org/help/submit_tex.html",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print({"status": "PASS", "package": str(output), "sha256": package_hash, "files": source_files})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
