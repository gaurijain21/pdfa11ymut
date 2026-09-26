"""Regenerate mutants in an isolated temporary directory.

This command is intentionally incapable of updating data/, corpus/, evidence/,
release manifests, or generated analysis.  It is the safe counterpart to the
historical generate-all workflow.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from pdfa11ymut.core import write_mutant
from pdfa11ymut.verify import verify_mutation

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden-dir", type=Path, default=ROOT / "corpus" / "golden")
    parser.add_argument("--operators", nargs="*", default=[f"M{i:02d}" for i in range(1, 11)])
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()
    goldens = sorted(args.golden_dir.glob("*.pdf"))
    if not goldens:
        print("No golden PDFs found; scratch regeneration is blocked.")
        return 2
    records: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="pdfa11ymut-scratch-") as scratch:
        scratch_dir = Path(scratch)
        for golden in goldens:
            for operator in args.operators:
                output = scratch_dir / f"{golden.stem}-{operator}.pdf"
                try:
                    generation = write_mutant(golden, output, operator, "auto")
                    verification = verify_mutation(golden, output, operator, generation["delta"], dpi=args.dpi)
                    records.append({"artifact_id": output.stem, "operator": operator, "status": "valid" if verification.get("mutation_valid") else "excluded", "verification": verification})
                except Exception as exc:
                    records.append({"artifact_id": output.stem, "operator": operator, "status": "inapplicable", "error": f"{type(exc).__name__}: {exc}"})
    counts = {"valid": sum(r["status"] == "valid" for r in records), "excluded": sum(r["status"] == "excluded" for r in records), "inapplicable": sum(r["status"] == "inapplicable" for r in records)}
    print(json.dumps({"mode": "scratch", "golden_count": len(goldens), "record_count": len(records), "counts": counts}, indent=2, sort_keys=True))
    return 0 if not counts["excluded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
