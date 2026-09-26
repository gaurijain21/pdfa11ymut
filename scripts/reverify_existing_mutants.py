"""Re-run verification against existing, hash-linked mutants without rewriting PDFs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pdfa11ymut.verify import sha256, verify_mutation, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--operator", action="append", default=[], help="operator to reverify; repeat as needed")
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()

    manifest_path = ROOT / "data" / "mutants.jsonl"
    records = [json.loads(line) for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = [row for row in records if not args.operator or row.get("operator") in set(args.operator)]
    if not selected:
        raise SystemExit("No matching mutant records")

    updated: dict[str, dict] = {}
    failures: list[str] = []
    for row in selected:
        source = Path(row["source_pdf"])
        mutant = Path(row["mutant_pdf"])
        if not source.is_file() or not mutant.is_file():
            failures.append(f"{row['mutant_id']}: source or mutant PDF is missing")
            continue
        if sha256(source) != row.get("source_sha256") or sha256(mutant) != row.get("mutant_sha256"):
            failures.append(f"{row['mutant_id']}: current PDF hash differs from the manifest")
            continue
        delta = row.get("generation", {}).get("delta", {})
        verification = verify_mutation(source, mutant, row["operator"], delta, dpi=args.dpi)
        revised = dict(row)
        revised["verification"] = verification
        revised["status"] = "valid" if verification.get("mutation_valid") else "excluded"
        updated[row["mutant_id"]] = revised
        if revised["status"] != "valid":
            failures.append(f"{row['mutant_id']}: {verification.get('exclusion_reason', 'verification failed')}")

    if failures:
        print(json.dumps({"status": "FAILED_CLOSED", "failures": failures}, indent=2))
        return 1

    merged = [updated.get(row["mutant_id"], row) for row in records]
    manifest_path.write_text(
        "\n".join(json.dumps(row, sort_keys=True, default=str) for row in merged) + "\n",
        encoding="utf-8",
    )
    for row in updated.values():
        write_json(ROOT / "evidence" / "verification" / f"{row['mutant_id']}.json", row)
    print(json.dumps({"status": "PASS", "reverified": len(updated), "dpi": args.dpi}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
