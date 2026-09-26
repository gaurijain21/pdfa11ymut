import csv
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SubmissionAuditTests(unittest.TestCase):
    def test_submission_audit_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/audit_submission.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifest_and_derived_rates_use_current_scope(self):
        manifest = json.loads((ROOT / "STUDY_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["counts"]["generation_records"], 73)
        self.assertEqual(manifest["counts"]["generated_mutant_pdf_files"], 71)
        self.assertEqual(manifest["counts"]["active_mutants"], 69)
        self.assertEqual(manifest["counts"]["formal_rows"], 207)
        with (ROOT / "analysis" / "generated" / "overall_rates.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["validator"] for row in rows}, {"PAC", "Acrobat", "veraPDF"})
        acrobat = next(row for row in rows if row["validator"] == "Acrobat")
        self.assertEqual((acrobat["rate_numerator"], acrobat["rate_denominator"]), ("26", "54"))

    def test_required_operators_and_selection_rows_exist(self):
        with (ROOT / "data" / "operator_standard_mapping.csv").open(newline="", encoding="utf-8-sig") as handle:
            mapping = list(csv.DictReader(handle))
        with (ROOT / "data" / "operator_target_selection.csv").open(newline="", encoding="utf-8-sig") as handle:
            selection = list(csv.DictReader(handle))
        self.assertEqual({row["operator"] for row in mapping}, {f"M{i:02d}" for i in range(1, 11)})
        self.assertEqual(len({row["mutant_id"] for row in selection}), 69)

    def test_independent_verification_covers_every_active_pair(self):
        manifest = json.loads((ROOT / "STUDY_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["evidence"]["independent_verification_rows"], 69)
        self.assertEqual(manifest["evidence"]["independent_structure_status"], {"PASS": 69})
        records = []
        for path in (ROOT / "evidence" / "independent_verification_v2").glob("*.json"):
            records.append(json.loads(path.read_text(encoding="utf-8")))
        self.assertEqual(len(records), 69)
        self.assertTrue(all(record["independent_delta_status"] == "CONFIRMED" for record in records))
        self.assertTrue(all(record["independent_render_status"] == "PASS" for record in records))
        self.assertTrue(all(record["mutation_confidence"] == "HIGH" for record in records))

    def test_disagreement_breakdown_is_manifested(self):
        manifest = json.loads((ROOT / "STUDY_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["counts"]["disagreement_rows"], 38)
        self.assertEqual(manifest["counts"]["disagreement_by_cause"], {
            "ACROBAT_MANUAL_VS_AUTOMATED": 30,
            "M09_ROLEMAP_RULE_PROFILE_DIFFERENCE": 6,
            "RULE_OR_PROFILE_DIFFERENCE": 2,
        })


if __name__ == "__main__":
    unittest.main()
