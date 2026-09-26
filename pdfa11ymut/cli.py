from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .core import write_mutant
from .verify import sha256, verify_mutation, write_json


ROOT = Path(__file__).resolve().parents[1]


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def append_failure(input_path: Path, operator: str, error: Exception) -> None:
    append_jsonl(ROOT / "data" / "generation_failures.jsonl", {"input": str(input_path), "operator": operator, "error": f"{type(error).__name__}: {error}"})


def remove_failure(input_path: Path, operator: str) -> None:
    path = ROOT / "data" / "generation_failures.jsonl"
    if not path.exists():
        return
    kept = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("input") == str(input_path) and row.get("operator") == operator:
            continue
        kept.append(json.dumps(row, sort_keys=True, default=str))
    path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def upsert_manifest(path: Path, row: dict) -> None:
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing = json.loads(line)
                if existing.get("mutant_id") != row.get("mutant_id"):
                    rows.append(existing)
    rows.append(row)
    path.write_text("\n".join(json.dumps(item, sort_keys=True, default=str) for item in rows) + "\n", encoding="utf-8")


def remove_manifest_row(path: Path, mutant_id: str) -> None:
    """Remove a stale prior record when a formerly applicable target disappears."""
    if not path.exists():
        return
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("mutant_id") != mutant_id:
                rows.append(row)
    path.write_text("\n".join(json.dumps(item, sort_keys=True, default=str) for item in rows) + ("\n" if rows else ""), encoding="utf-8")


def manifest_has_status(path: Path, mutant_id: str, status: str) -> bool:
    if not path.exists():
        return False
    return any(
        row.get("mutant_id") == mutant_id and row.get("status") == status
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    )


def generate(args: argparse.Namespace) -> int:
    input_path = Path(args.input).resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"input PDF does not exist: {input_path}")
    output_path = Path(args.output).resolve()
    try:
        generation = write_mutant(input_path, output_path, args.operator, args.target)
        verification = verify_mutation(input_path, output_path, args.operator, generation["delta"], dpi=args.dpi)
    except Exception as exc:
        if output_path.exists():
            output_path.unlink()
        raise RuntimeError(f"generation refused: {type(exc).__name__}: {exc}") from exc
    record = {
        "mutant_id": args.mutant_id or output_path.stem,
        "operator": args.operator,
        "source_pdf": str(input_path),
        "mutant_pdf": str(output_path),
        "source_sha256": sha256(input_path),
        "mutant_sha256": sha256(output_path),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generation_version": __version__,
        "generation": generation,
        "verification": verification,
        "status": "valid" if verification.get("mutation_valid") else "excluded",
    }
    manifest = ROOT / "data" / "mutants.jsonl"
    upsert_manifest(manifest, record)
    write_json(ROOT / "evidence" / "verification" / f"{record['mutant_id']}.json", record)
    if record["status"] != "valid":
        output_path.unlink(missing_ok=True)
        raise RuntimeError(f"mutant excluded after verification: {verification.get('exclusion_reason', 'unknown')}")
    remove_failure(input_path, args.operator)
    print(json.dumps({"status": "valid", "mutant_id": record["mutant_id"], "output": str(output_path), "sha256": record["mutant_sha256"]}, indent=2))
    return 0


def generate_all(args: argparse.Namespace) -> int:
    golden_dir = Path(os.environ.get("PDFa11YMUT_GOLDEN_DIR", ROOT / "corpus" / "golden"))
    pdfs = sorted(golden_dir.glob("*.pdf"))
    if not pdfs:
        print("No golden PDFs found in corpus/golden. Automated generation is blocked; see USER_ACTION_REQUIRED.md.")
        return 2
    if args.reset_manifests:
        for manifest in (ROOT / "data" / "mutants.jsonl", ROOT / "data" / "generation_failures.jsonl"):
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_text("", encoding="utf-8")
    operators = args.operators or [f"M{i:02d}" for i in range(1, 11)]
    failures = 0
    for source in pdfs:
        golden_id = source.stem
        for operator in operators:
            output = ROOT / "corpus" / "mutants" / f"{golden_id}-{operator}.pdf"
            child = argparse.Namespace(input=str(source), output=str(output), operator=operator, target="auto", mutant_id=f"{golden_id}-{operator}", dpi=args.dpi)
            try:
                generate(child)
            except Exception as exc:
                failures += 1
                mutant_id = f"{golden_id}-{operator}"
                manifest_path = ROOT / "data" / "mutants.jsonl"
                # A failed precondition can invalidate a stale prior valid
                # row; a post-verification exclusion is already written by
                # generate() and must remain available for audit.
                if manifest_has_status(manifest_path, mutant_id, "valid"):
                    remove_manifest_row(manifest_path, mutant_id)
                (ROOT / "evidence" / "verification" / f"{mutant_id}.json").unlink(missing_ok=True)
                append_failure(source, operator, exc)
                print(f"EXCLUDED {mutant_id}: {exc}", file=sys.stderr)
    return 1 if failures else 0


def manual_plan(_: argparse.Namespace) -> int:
    from .phase2 import audit_purity, distribution, write_queue

    purity = audit_purity()
    if purity["flagged"]:
        raise RuntimeError(f"purity audit flagged {len(purity['flagged'])} mutant(s); queue not regenerated")
    summary = distribution()
    print(json.dumps({"purity": purity, "distribution": summary}, indent=2, sort_keys=True))
    write_queue()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pdfa11ymut")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="generate and verify one mutant")
    gen.add_argument("--input", required=True)
    gen.add_argument("--operator", required=True, choices=[f"M{i:02d}" for i in range(1, 11)])
    gen.add_argument("--target", default="auto")
    gen.add_argument("--output", required=True)
    gen.add_argument("--mutant-id")
    gen.add_argument("--dpi", type=int, default=150)
    gen.set_defaults(func=generate)
    all_cmd = sub.add_parser("generate-all", help="generate all applicable operators for all golden PDFs")
    all_cmd.add_argument("--operators", nargs="*")
    all_cmd.add_argument("--dpi", type=int, default=150)
    all_cmd.add_argument("--reset-manifests", action="store_true", help="clear generated mutant/failure manifests before the run")
    all_cmd.set_defaults(func=generate_all)
    plan = sub.add_parser("manual-plan", help="regenerate GUI/manual evidence rows from valid mutants")
    plan.set_defaults(func=manual_plan)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
