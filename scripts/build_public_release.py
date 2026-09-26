"""Build the scoped public bundle without raw vendor or assistive-technology evidence."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from datetime import date
from pathlib import Path


EXCLUDED_DIRS = {
    ".git",
    "tmp",
    "__pycache__",
    "evidence",
    "arxiv_submission",
}
EXCLUDED_RELATIVE_DIRS = {Path("paper") / "archive"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def is_excluded(relative: Path, output_name: str, digest_name: str, manifest_name: str) -> bool:
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return True
    if any(relative.parts[: len(root.parts)] == root.parts for root in EXCLUDED_RELATIVE_DIRS):
        return True
    if relative.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if relative.suffix.lower() == ".zip":
        return True
    if relative.parts and relative.parts[0] == "release" and relative.name.startswith("pdfa11ymut_release_"):
        return True
    if relative.name in {output_name, digest_name, manifest_name}:
        return True
    return False


def collect_files(root: Path, output_name: str, digest_name: str, manifest_name: str) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if is_excluded(relative, output_name, digest_name, manifest_name):
            continue
        files.append(relative)
    return sorted(files, key=lambda item: item.as_posix().lower())


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
    release_dir = root / "release"
    stamp = date.today().isoformat()
    output = (args.output or release_dir / f"pdfa11ymut_public_{stamp}.zip").resolve()
    digest_path = output.with_suffix(output.suffix + ".sha256")
    manifest_path = output.with_suffix(".manifest.txt")
    output.parent.mkdir(parents=True, exist_ok=True)

    relative_files = collect_files(root, output.name, digest_path.name, manifest_path.name)
    forbidden = [
        relative
        for relative in relative_files
        if "evidence" in relative.parts
        or ".git" in relative.parts
        or "tmp" in relative.parts
        or relative.suffix.lower() in {".zip", ".pyc", ".pyo"}
    ]
    if forbidden:
        raise SystemExit(f"excluded files selected: {forbidden[:5]}")

    prefix = output.stem
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in relative_files:
            archive.write(root / relative, f"{prefix}/{relative.as_posix()}")

    output_hash = sha256(output)
    digest_path.write_text(f"{output_hash}  {output.name}\n", encoding="utf-8")
    manifest_path.write_text(
        "\n".join(
            [
                "PDFa11yMut scoped public release bundle",
                f"date: {stamp}",
                f"package: {output.name}",
                f"package_sha256: {output_hash}",
                f"file_count: {len(relative_files)}",
                "excluded: raw evidence/, .git/, tmp/, arxiv_submission/, paper/archive/, historical release ZIPs, Python bytecode",
                "legal_boundary: public bundle retains hashes, protocols, classifications, and summaries; raw vendor/AT evidence remains excluded",
                "venue_boundary: target-venue PDF/UA and anonymity policies remain external submission checks",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        {
            "status": "PASS",
            "package": str(output),
            "sha256": output_hash,
            "files": len(relative_files),
            "excluded_raw_evidence": True,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
