import subprocess
import sys
import tempfile
import unittest
import csv
import json
import hashlib
from pathlib import Path

import yaml
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

from pdfa11ymut.core import write_mutant
from pdfa11ymut.verify import operator_delta_ok, structure_map, verify_mutation


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def make_fixture(self, path: Path):
        writer = PdfWriter()
        page = writer.add_blank_page(width=300, height=300)
        page_ref = writer._add_object(page)
        def obj(role, k=None, **extra):
            value = DictionaryObject({NameObject("/S"): NameObject(role)})
            if k is not None:
                value[NameObject("/K")] = ArrayObject(k)
            for key, item in extra.items():
                value[NameObject("/" + key)] = item
            return writer._add_object(value)
        def mcr(mcid):
            return writer._add_object(DictionaryObject({NameObject("/Type"): NameObject("/MCR"), NameObject("/MCID"): NumberObject(mcid), NameObject("/Pg"): page_ref}))
        li1 = obj("/LI", [mcr(0)])
        li2 = obj("/LI", [mcr(1)])
        list_ref = obj("/L", [li1, li2])
        paragraph = obj("/P", [mcr(2), mcr(3)])
        heading = obj("/H2", [mcr(4)])
        figure = obj("/Figure", [mcr(5)], Alt=TextStringObject("A figure"))
        cell = obj("/TD", [mcr(6)])
        row = obj("/TR", [cell])
        table = obj("/Table", [row])
        custom = obj("/Custom", [mcr(7)])
        document = obj("/Document", [heading, list_ref, paragraph, figure, table, custom])
        struct_root = DictionaryObject({NameObject("/Type"): NameObject("/StructTreeRoot"), NameObject("/K"): document, NameObject("/RoleMap"): DictionaryObject({NameObject("/UnusedCustom"): NameObject("/Figure"), NameObject("/Custom"): NameObject("/P")})})
        struct_root_ref = writer._add_object(struct_root)
        writer._root_object[NameObject("/StructTreeRoot")] = struct_root_ref
        writer._root_object[NameObject("/Lang")] = TextStringObject("en-US")
        with path.open("wb") as fh:
            writer.write(fh)

    def test_operator_specification_is_complete(self):
        data = yaml.safe_load((ROOT / "operators" / "operators.yaml").read_text(encoding="utf-8"))
        operators = data["operators"]
        self.assertEqual([item["id"] for item in operators], [f"M{i:02d}" for i in range(1, 11)])
        for item in operators:
            for field in ("name", "class", "preconditions", "transformation", "invariants", "expected_structural_delta", "expected_assistive_effect", "expected_automated_detectability"):
                self.assertIn(field, item, item["id"])
            for field in ("source_reference", "checkpoint_or_technique", "machine_checkable", "validator_dependent", "semantic_or_at_evidence_required", "invalid_target_conditions", "baseline_conflict_conditions", "collateral_change_conditions", "positive_control", "applicability_notes"):
                self.assertIn(field, item, item["id"])
            self.assertNotIn("TODO", json.dumps(item).upper(), item["id"])
            self.assertIn(item["class"], {"class_a", "class_b"})

    def test_canonical_denominator_is_derived_and_exclusions_are_honored(self):
        mutants = [json.loads(line) for line in (ROOT / "data" / "mutants.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        with (ROOT / "data" / "mutant_exclusions.csv").open(encoding="utf-8-sig", newline="") as fh:
            exclusions = {row["mutant_id"] for row in csv.DictReader(fh)}
        active = {row["mutant_id"] for row in mutants if row.get("status", "").lower() == "valid" and row.get("verification", {}).get("mutation_valid") is True} - exclusions
        with (ROOT / "data" / "validator_runs.csv").open(encoding="utf-8-sig", newline="") as fh:
            runs = list(csv.DictReader(fh))
        formal = [row for row in runs if row.get("baseline_or_mutant") == "mutant" and row.get("artifact_id") in active and row.get("configuration") in {"Formal", "Full Check", "PDF/UA-1 ua1"}]
        self.assertEqual(len(active), 69)
        self.assertEqual(len(formal), 207)
        self.assertFalse(any(row.get("artifact_id") in exclusions for row in formal))

    def test_double_coding_queue_is_blinded_and_hash_linked(self):
        with (ROOT / "data" / "double_coding_queue.csv").open(encoding="utf-8-sig", newline="") as fh:
            queue = list(csv.DictReader(fh))
        with (ROOT / "data" / "double_coding_key.csv").open(encoding="utf-8-sig", newline="") as fh:
            key = list(csv.DictReader(fh))
        self.assertEqual(len(queue), 207)
        self.assertEqual(len(key), len(queue))
        self.assertEqual(len({row["case_id"] for row in queue}), len(queue))
        decision_fields = ("coder_1_decision", "coder_2_decision", "adjudication_decision")
        queue_is_completed = any(row[field] for row in queue for field in decision_fields)
        allowed_decisions = {
            "Detected", "Missed", "Needs Manual Check", "Baseline Conflict",
            "Outside Scope", "Ambiguous", "Unrelated",
        }
        for row in queue:
            self.assertNotIn("artifact_id", row)
            self.assertNotIn("operator", row)
            self.assertNotIn("validator", row)
            evidence = ROOT / row["evidence_path"]
            digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
            self.assertEqual(digest, row["evidence_sha256"], row["case_id"])
            if not queue_is_completed:
                self.assertFalse(any(row[field] for field in decision_fields))
                continue
            self.assertIn(row["coder_1_decision"], allowed_decisions, row["case_id"])
            self.assertIn(row["coder_2_decision"], allowed_decisions, row["case_id"])
            self.assertIn(row["adjudication_decision"], allowed_decisions, row["case_id"])
            self.assertTrue(row["coder_1_id"] and row["coder_2_id"] and row["adjudicator_id"], row["case_id"])
            self.assertNotEqual(row["coder_1_id"], row["coder_2_id"], row["case_id"])
            expected_agreement = "agree" if row["coder_1_decision"] == row["coder_2_decision"] else "disagree"
            self.assertEqual(row["agreement"], expected_agreement, row["case_id"])
            self.assertTrue(row["coder_1_rationale"] and row["coder_2_rationale"] and row["adjudication_rationale"], row["case_id"])
        self.assertFalse(any(row["adjudication_decision"] == "Ambiguous" for row in queue))

    def test_double_coding_corrections_preserve_original_packets(self):
        with (ROOT / "data" / "double_coding_corrections.csv").open(encoding="utf-8-sig", newline="") as fh:
            corrections = list(csv.DictReader(fh))
        self.assertEqual({row["case_id"] for row in corrections}, {"DC-0096", "DC-0105"})
        for row in corrections:
            original = ROOT / row["original_evidence_path"]
            corrected = ROOT / row["corrected_evidence_path"]
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), row["original_evidence_sha256"])
            self.assertEqual(hashlib.sha256(corrected.read_bytes()).hexdigest(), row["corrected_evidence_sha256"])
            self.assertEqual(row["coder_decisions_preserved"], "true")
        for name in ("double_coding_queue_coder_1.csv", "double_coding_queue_coder_2.csv"):
            with (ROOT / "data" / name).open(encoding="utf-8-sig", newline="") as fh:
                coder_rows = list(csv.DictReader(fh))
            self.assertEqual(len(coder_rows), 207)
            for row in coder_rows:
                evidence = ROOT / row["evidence_path"]
                self.assertEqual(hashlib.sha256(evidence.read_bytes()).hexdigest(), row["evidence_sha256"], f"{name}:{row['case_id']}")

    def test_double_coding_is_applied_to_canonical_rows(self):
        with (ROOT / "data" / "double_coding_queue.csv").open(encoding="utf-8-sig", newline="") as fh:
            queue = {row["case_id"]: row for row in csv.DictReader(fh)}
        with (ROOT / "data" / "double_coding_key.csv").open(encoding="utf-8-sig", newline="") as fh:
            key = list(csv.DictReader(fh))
        with (ROOT / "data" / "validator_runs.csv").open(encoding="utf-8-sig", newline="") as fh:
            runs = {row["record_id"]: row for row in csv.DictReader(fh)}
        for item in key:
            decision = queue[item["case_id"]]
            canonical = runs[item["record_id"]]
            self.assertEqual(canonical["coder_1"], decision["coder_1_id"], item["case_id"])
            self.assertEqual(canonical["coder_2"], decision["coder_2_id"], item["case_id"])
            self.assertEqual(canonical["adjudication"], decision["adjudication_decision"], item["case_id"])

    def test_formal_classifier_does_not_populate_pac_ai_rows(self):
        with (ROOT / "data" / "validator_runs.csv").open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
        ai_mutants = [row for row in rows if row["validator"] == "PAC" and row["configuration"] == "AI" and row["baseline_or_mutant"] == "mutant"]
        self.assertTrue(ai_mutants)
        self.assertTrue(all(not row["raw_detection_classification"] and not row["detection_classification"] for row in ai_mutants))

    def test_generation_fails_closed_without_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(__import__("os").environ)
            env["PDFa11YMUT_GOLDEN_DIR"] = tmp
            result = subprocess.run([sys.executable, "-m", "pdfa11ymut", "generate-all"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("No golden PDFs", result.stdout)

    def test_m10_objr_rewrites_do_not_create_false_structural_deltas(self):
        records = {
            item["mutant_id"]: item
            for item in (
                json.loads(line)
                for line in (ROOT / "data" / "mutants.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        for mutant_id in (
            "PDFUA-Ref-2-02_Invoice-M10",
            "PDFUA-Ref-2-05_BookChapter-german-M10",
            "PDFUA-Ref-2-08_BookChapter-M10",
            "PDFUA-Ref-2-09_Scanned-M10",
        ):
            record = records[mutant_id]
            golden = PdfReader(str(ROOT / record["source_pdf"]), strict=False)
            mutant = PdfReader(str(ROOT / record["mutant_pdf"]), strict=False)
            before, after = structure_map(golden), structure_map(mutant)
            changed = sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
            ok, reason = operator_delta_ok("M10", record["generation"]["delta"], before, after, changed, golden, mutant)
            self.assertTrue(ok, f"{mutant_id}: {reason}; changed={changed}")

    def test_analysis_does_not_use_historical_summary(self):
        result = subprocess.run([sys.executable, "scripts/rebuild_analysis.py"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = (ROOT / "analysis" / "generated" / "metrics_summary.json").read_text(encoding="utf-8")
        self.assertIn("formal_complete_at_complete_pac_ai_future_work", summary)
        self.assertIn('"classified_formal_rows": 207', summary)
        self.assertIn('"class_summary"', summary)
        self.assertNotIn("17.4", summary)

    def test_all_operators_run_on_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "fixture.pdf"
            self.make_fixture(source)
            for number in range(1, 11):
                operator = f"M{number:02d}"
                mutant = tmp_path / f"fixture-{operator}.pdf"
                generation = write_mutant(source, mutant, operator, "auto")
                if operator == "M09":
                    self.assertEqual(generation["delta"]["role_key"], "/Custom")
                verification = verify_mutation(source, mutant, operator, generation["delta"])
                self.assertTrue(verification["parseability"], operator)
                self.assertTrue(verification["page_count_preserved"], operator)
                self.assertTrue(verification["invariant_checks"]["page_content_byte_hashes_equal"], operator)
                self.assertTrue(verification["invariant_checks"]["rendering_preserved"], operator)
                self.assertTrue(verification["mutation_valid"], operator)


if __name__ == "__main__":
    unittest.main()
