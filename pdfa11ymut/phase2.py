from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader
from pypdf.generic import IndirectObject

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "corpus" / "golden"
MUTANTS = ROOT / "corpus" / "mutants"

QUEUE_FIELDS = [
    "batch_id", "sub_batch_id", "order", "artifact_id", "filepath", "sha256", "operator",
    "source_golden", "validator", "configuration", "baseline_or_mutant",
    "exact_output_filename", "evidence_destination", "status", "notes",
]

AT_FIELDS = [
    "artifact_id", "source_golden", "mutant_id", "operator", "selected_golden",
    "reason", "expected_golden_behavior", "expected_mutant_behavior",
    "exact_at_observation", "status",
]

PAC_AI_FIELDS = [
    "artifact_id", "artifact_type", "operator", "operator_class", "source_golden",
    "PAC_formal_classification", "selected_for_ai", "selection_reason", "control_type",
    "expected_ai_question", "status", "golden_id", "PAC_formal_result", "selected_for_pac_ai",
]

OPERATOR_CLASSES = {
    "M01": "semantic", "M02": "semantic", "M03": "machine-checkable", "M04": "semantic",
    "M05": "semantic", "M06": "machine-checkable", "M07": "machine-checkable",
    "M08": "machine-checkable", "M09": "machine-checkable", "M10": "machine-checkable",
}

AI_UNRESOLVED_ARTIFACTS = {}

AI_EXPECTED_QUESTIONS = {
    "M01": "Does PAC AI identify the intended reading-order change relative to the golden baseline?",
    "M02": "Does PAC AI identify that the intended tagged subtree is omitted from traversal?",
    "M03": "Does PAC AI identify the changed heading-level semantics?",
    "M04": "Does PAC AI identify the changed association between the two same-role leaf items?",
    "M05": "Does PAC AI identify the changed order of the targeted content chunks?",
    "M06": "Does PAC AI identify the duplicated list-item traversal effect?",
    "M07": "Does PAC AI identify the missing figure alternate description?",
    "M08": "Does PAC AI identify the missing document-language declaration?",
    "M09": "Does PAC AI identify the unresolved-role mutation without treating a generic warning as specific evidence?",
    "M10": "Does PAC AI identify the changed table-cell semantics?",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def excluded_mutant_ids() -> set[str]:
    return {row.get("mutant_id", "") for row in read_csv(ROOT / "data" / "mutant_exclusions.csv") if row.get("status")}


def valid_mutants() -> list[dict]:
    excluded = excluded_mutant_ids()
    rows = [row for row in read_jsonl(ROOT / "data" / "mutants.jsonl") if row.get("status") == "valid" and row.get("mutant_id") not in excluded]
    return sorted(rows, key=lambda row: (row["operator"], row["mutant_id"]))


def artifact_filename(row: dict, baseline: bool) -> str:
    return Path(row["source_pdf"] if baseline else row["mutant_pdf"]).name


def artifact_path(row: dict, baseline: bool) -> Path:
    return Path(row["source_pdf"] if baseline else row["mutant_pdf"])


def output_name(artifact_id: str, digest: str, suffix: str = "json") -> str:
    return f"{artifact_id}__{digest}.{suffix}"


def queue_row(batch: str, order: int, artifact_id: str, path: Path, digest: str,
             operator: str, source_golden: str, validator: str, configuration: str,
             kind: str, evidence_dir: str, notes: str = "", output_suffix: str = "json") -> dict:
    return {
        "batch_id": batch,
        "sub_batch_id": "",
        "order": order,
        "artifact_id": artifact_id,
        "filepath": str(path.relative_to(ROOT)),
        "sha256": digest,
        "operator": operator,
        "source_golden": source_golden,
        "validator": validator,
        "configuration": configuration,
        "baseline_or_mutant": kind,
        "exact_output_filename": output_name(artifact_id, digest, output_suffix),
        "evidence_destination": evidence_dir,
        "status": "TODO",
        "notes": notes,
    }


def select_at_rows(rows: list[dict]) -> list[dict]:
    # One small, reproducible sample per operator with an observable AT effect.
    # M09 is deliberately excluded: unresolved RoleMap semantics are parser/viewer
    # dependent and do not yield a stable single NVDA observation.
    choices = {
        "M01": ("PDFUA-Ref-2-01_Magazine-danish", "Active M01 candidate with a stable tagged sequence for reading-order comparison.",
                 "NVDA reads the tagged content in the baseline structural order.",
                 "The first two selected structural children are announced in the opposite order.",
                 "Compare the first two targeted content units during a line-by-line reading pass."),
        "M02": ("PDFUA-Ref-2-02_Invoice", "One-page invoice makes omission of the selected subtree easy to verify.",
                 "The complete tagged invoice content is reachable.",
                 "The selected tagged subtree is absent from structural traversal.",
                 "Record whether the selected invoice text is encountered during tagged reading."),
        "M03": ("PDFUA-Ref-2-02_Invoice", "Small heading-level mutation with a clear heading-navigation effect.",
                 "Heading navigation exposes the baseline heading level.",
                 "The selected heading is exposed at the changed/skipped level.",
                 "Record the heading level announced or shown by the viewer's heading navigation."),
        "M04": ("PDFUA-Ref-2-02_Invoice", "Simple same-role leaf pair isolates association exchange without containment changes.",
                 "Each structural position exposes its own associated text.",
                 "The two structural positions expose the sibling text associations exchanged by the mutation.",
                 "Record the text heard for each of the two targeted positions."),
        "M05": ("PDFUA-Ref-2-03_AcademicAbstract", "Two-page abstract provides a short, readable internal content sequence.",
                 "The selected paragraph content is read in its baseline chunk order.",
                 "The selected content chunks are exposed in reverse order.",
                 "Record the order of the two targeted text chunks in continuous reading."),
        "M06": ("PDFUA-Ref-2-03_AcademicAbstract", "Short document with a duplicated list-item traversal effect.",
                 "List navigation announces each list item once.",
                 "The targeted list item is encountered twice in structural traversal.",
                 "Record the number and order of announcements for the targeted list item."),
        "M07": ("PDFUA-Ref-2-02_Invoice", "One-page invoice has a concrete figure whose alternate text can be compared.",
                 "NVDA exposes the figure's alternate description.",
                 "The figure has no mutation-supplied alternate description.",
                 "Record the figure announcement and whether its description is spoken."),
        "M08": ("PDFUA-Ref-2-10_Form", "One-page form makes the document-language metadata effect easy to isolate.",
                 "The viewer/AT uses the document's declared language where supported.",
                 "The document-level language declaration is absent.",
                 "Record the document language shown/used by the viewer and any speech-language change."),
        "M10": ("PDFUA-Ref-2-02_Invoice", "Small table-role mutation permits direct table navigation comparison.",
                 "Table navigation identifies the targeted cell with its table-cell semantics.",
                 "The targeted child no longer has the baseline cell role.",
                 "Record how the targeted cell is announced during table navigation."),
    }
    selected = []
    for operator, choice in choices.items():
        golden, reason, expected_golden, expected_mutant, observation = choice
        # Preserve a completed representative observation as historical/secondary
        # evidence even when later formal exclusions remove that artifact from the
        # active validator denominator. This keeps regeneration from manufacturing
        # a new TODO for an already evidenced AT case.
        observed = [row for row in read_csv(ROOT / "data" / "at_observations.csv")
                    if row.get("operator") == operator and row.get("status") == "COMPLETE"
                    and (MUTANTS / f"{row.get('mutant_id', '')}.pdf").is_file()]
        if observed:
            prior = observed[0]
            preserved = {field: prior.get(field, "") for field in AT_FIELDS}
            defaults = {
                "selected_golden": golden + ".pdf",
                "reason": reason,
                "expected_golden_behavior": expected_golden,
                "expected_mutant_behavior": expected_mutant,
                "exact_at_observation": observation,
            }
            for field, value in defaults.items():
                if not preserved.get(field):
                    preserved[field] = value
            selected.append(preserved)
            continue
        candidates = [r for r in rows if r["operator"] == operator and Path(r["source_pdf"]).stem == golden]
        if not candidates:
            raise ValueError(f"AT selection missing valid candidate for {operator} on {golden}")
        row = candidates[0]
        selected.append({
            "artifact_id": row["mutant_id"],
            "source_golden": golden,
            "mutant_id": row["mutant_id"],
            "operator": operator,
            "selected_golden": golden + ".pdf",
            "reason": reason,
            "expected_golden_behavior": expected_golden,
            "expected_mutant_behavior": expected_mutant,
            "exact_at_observation": observation,
            "status": "TODO",
        })
    return selected


def read_validator_runs() -> list[dict]:
    path = ROOT / "data" / "validator_runs.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def evidence_present(row: dict) -> bool:
    """Recognize preserved native Acrobat HTML alongside the canonical queue slot."""
    expected = ROOT / row["evidence_destination"] / row["exact_output_filename"]
    if expected.is_file():
        return True
    if row.get("validator") == "Acrobat" and expected.suffix.lower() == ".json":
        native = expected.with_suffix(".accreport.html")
        if native.is_file():
            return True
        return len(list(expected.parent.glob(f"{row.get('artifact_id', '')}__*.accreport.html"))) == 1
    return False


def formal_run(runs: list[dict], artifact_id: str) -> dict | None:
    matches = [row for row in runs if (row.get("artifact_id") or row.get("mutant_id")) == artifact_id
               and row.get("validator") == "PAC"
               and str(row.get("configuration", "")).lower() == "formal"]
    return matches[-1] if matches else None


def formal_evidence_complete(runs: list[dict], rows: list[dict]) -> bool:
    baseline_ids = {Path(row["source_pdf"]).stem for row in rows}
    baselines = [row for row in runs if row.get("validator") == "PAC" and str(row.get("configuration", "")).lower() == "formal" and row.get("baseline_or_mutant") == "golden_baseline" and row.get("artifact_id") in baseline_ids]
    if len(baselines) != 9 or any(not row.get("automated_pass_fail") for row in baselines):
        return False
    mutant_runs = [formal_run(runs, row["mutant_id"]) for row in rows]
    return len(mutant_runs) == len(rows) and all(run and run.get("automated_pass_fail") and run.get("detection_classification") in {"Detected", "Missed", "Survived", "NotDetected"} and run.get("baseline_status") == "BASELINE_PASS" for run in mutant_runs)


def golden_baselines_ready(runs: list[dict], rows: list[dict]) -> bool:
    golden_ids = {Path(row["source_pdf"]).stem for row in rows}
    required = [("PAC", "Formal"), ("Acrobat", "Full Check"), ("veraPDF", "PDF/UA-1 ua1")]
    for validator, configuration in required:
        found = [row for row in runs if row.get("validator") == validator and row.get("configuration") == configuration and row.get("baseline_or_mutant") == "golden_baseline" and row.get("artifact_id") in golden_ids and row.get("automated_pass_fail")]
        if len(found) != 9:
            return False
    review = ROOT / "analysis" / "generated" / "baseline_review.csv"
    if review.exists():
        conflicts = read_csv(ROOT / "analysis" / "generated" / "baseline_operator_conflicts.csv")
        resolutions = read_csv(ROOT / "data" / "baseline_conflict_resolutions.csv")
        resolved_pairs = {
            (row.get("golden_id", ""), row.get("operator", ""))
            for row in resolutions
            if row.get("verdict") in {"VALID", "VALID_WITH_BASELINE_DELTA"}
        }
        active_pairs = {(Path(row["source_pdf"]).stem, row["operator"]) for row in rows}
        with review.open(newline="", encoding="utf-8-sig") as fh:
            for review_row in csv.DictReader(fh):
                if review_row.get("status") == "PASS":
                    continue
                mapped = [conflict for conflict in conflicts if conflict.get("golden_id") == review_row.get("artifact_id")]
                if not mapped:
                    return False
                if any(
                    conflict.get("operator") == "ALL"
                    or (
                        (review_row.get("artifact_id"), conflict.get("operator")) in active_pairs
                        and (review_row.get("artifact_id"), conflict.get("operator")) not in resolved_pairs
                    )
                    for conflict in mapped
                ):
                    return False
    return True


def select_pac_ai_rows(rows: list[dict]) -> list[dict]:
    """Create the frozen PAC AI cohort from the formal-results freeze.

    The selection is deliberately outcome-independent within the declared
    operator classes: all clean semantic PAC survivors are selected, while one
    reproducible machine-checkable control is selected per machine operator.
    """
    runs = read_validator_runs()
    freeze_rows = read_csv(ROOT / "analysis" / "generated" / "formal_results_freeze.csv")
    frozen_pac = {
        row["artifact_id"]: row for row in freeze_rows
        if row.get("validator") == "PAC" and row.get("configuration") == "Formal"
    }
    formal_complete = (
        len(frozen_pac) == len(rows)
        and all(row.get("detection_classification") in {"Detected", "Missed", "Needs Manual Check", "Not Applicable"} for row in frozen_pac.values())
    )
    selected_controls: set[str] = set()
    if formal_complete:
        for operator in sorted({op for op, cls in OPERATOR_CLASSES.items() if cls == "machine-checkable"}):
            candidates = [row for row in rows if row["operator"] == operator and row["mutant_id"] in frozen_pac]
            classified = [row for row in candidates if frozen_pac[row["mutant_id"]].get("detection_classification") in {"Detected", "Missed"}]
            if classified:
                selected_controls.add(sorted(classified, key=lambda row: row["mutant_id"])[0]["mutant_id"])
    output = []
    for row in rows:
        operator = row["operator"]
        golden = Path(row["source_pdf"]).stem
        frozen = frozen_pac.get(row["mutant_id"], {})
        formal_result = frozen.get("detection_classification") or "FORMAL_RESULT_PENDING"
        if not formal_complete or not frozen:
            selected = "FALSE"
            reason = "Not selectable until the formal freeze is complete."
            control_type = ""
            status = "BLOCKED_FORMAL_FREEZE"
        elif frozen.get("baseline_status") != "BASELINE_PASS":
            selected = "FALSE"
            reason = "Excluded because the matching PAC Formal golden baseline is not a clean PASS; the mutation is not interpretable for AI comparison."
            control_type = "excluded_baseline_not_interpretable"
            status = "EXCLUDED_BASELINE_NOT_INTERPRETABLE"
        elif row["mutant_id"] in AI_UNRESOLVED_ARTIFACTS:
            selected = "FALSE"
            reason = AI_UNRESOLVED_ARTIFACTS[row["mutant_id"]]
            control_type = "excluded_unresolved_applicability"
            status = "EXCLUDED_PENDING_AUDIT"
        elif OPERATOR_CLASSES[operator] == "semantic":
            survives = frozen.get("baseline_status") == "BASELINE_PASS" and formal_result == "Missed"
            selected = "TRUE" if survives else "FALSE"
            reason = "Semantic mutant survived PAC Formal with an interpretable baseline." if survives else "Excluded because PAC Formal detected it or the baseline/result was not a clean survival."
            control_type = ""
            status = "TODO" if selected == "TRUE" else "NOT_SELECTED"
        else:
            selected = "TRUE" if row["mutant_id"] in selected_controls else "FALSE"
            reason = "One reproducible machine-checkable control selected per operator to compare PAC AI with formal evidence." if selected == "TRUE" else "Not selected; one classified control per machine-checkable operator is sufficient."
            control_type = "machine_checkable_control" if selected == "TRUE" else ""
            status = "TODO" if selected == "TRUE" else "NOT_SELECTED"
        output.append({
            "artifact_id": row["mutant_id"], "artifact_type": "mutant", "operator": operator,
            "operator_class": OPERATOR_CLASSES[operator], "source_golden": golden,
            "PAC_formal_classification": formal_result, "selected_for_ai": selected,
            "selection_reason": reason, "control_type": control_type,
            "expected_ai_question": AI_EXPECTED_QUESTIONS[operator], "status": status,
            "golden_id": golden, "PAC_formal_result": formal_result,
            "selected_for_pac_ai": selected,
        })
    return output


def write_pac_ai_selection(rows: list[dict]) -> list[dict]:
    selected = select_pac_ai_rows(rows)
    selected_mutants = [row for row in selected if row["selected_for_pac_ai"] == "TRUE"]
    selected_golden_ids = sorted({row["source_golden"] for row in selected_mutants})
    golden_rows = []
    for golden in selected_golden_ids:
        golden_rows.append({
            "artifact_id": golden, "artifact_type": "golden", "operator": "",
            "operator_class": "", "source_golden": golden,
            "PAC_formal_classification": "BASELINE",
            "selected_for_ai": "TRUE",
            "selection_reason": "Required golden baseline for the selected PAC AI cohort.",
            "control_type": "golden_baseline",
            "expected_ai_question": "Does PAC AI remain at the golden baseline without a mutant-specific finding?",
            "status": "TODO", "golden_id": golden, "PAC_formal_result": "BASELINE",
            "selected_for_pac_ai": "TRUE",
        })
    selected = golden_rows + selected
    path = ROOT / "data" / "pac_ai_selection.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=PAC_AI_FIELDS)
        writer.writeheader(); writer.writerows(selected)
    return selected


def build_queue() -> tuple[list[dict], list[dict]]:
    mutants = valid_mutants()
    if not mutants:
        raise ValueError("no active valid mutants remain")
    pac_ai_selection = write_pac_ai_selection(mutants)
    selected_ai = [row for row in pac_ai_selection if row["selected_for_pac_ai"] == "TRUE" and row.get("artifact_type", "mutant") == "mutant"]
    runs = read_validator_runs()
    freeze_pac = {
        row["artifact_id"]: row for row in read_csv(ROOT / "analysis" / "generated" / "formal_results_freeze.csv")
        if row.get("validator") == "PAC" and row.get("configuration") == "Formal"
    }
    formal_complete = (
        len(freeze_pac) == len(mutants)
        and all(row.get("detection_classification") in {"Detected", "Missed", "Needs Manual Check", "Not Applicable"} for row in freeze_pac.values())
    )
    baselines_ready = golden_baselines_ready(runs, mutants)
    old_queue = []
    old_path = ROOT / "manual_runs_todo.csv"
    if old_path.exists():
        with old_path.open(newline="", encoding="utf-8-sig") as fh:
            old_queue = list(csv.DictReader(fh))
    old_status = {(row.get("batch_id"), row.get("artifact_id")): row.get("status", "TODO") for row in old_queue}
    rows: list[dict] = []
    order = 1
    goldens = sorted(GOLDEN.glob("*.pdf"))
    # One provenance confirmation is a setup task, not a validator run.
    provenance = queue_row("B00_CORPUS_PROVENANCE_REVIEW", order, "CORPUS_PROVENANCE_REVIEW", ROOT / "CORPUS_LICENSES.md", "", "", "", "Provenance", "Source/license mapping", "setup", ".", "Confirm per-file source identity and redistribution terms in USER_ACTION_REQUIRED.md.")
    provenance["exact_output_filename"] = "USER_ACTION_REQUIRED.md"
    rows.append(provenance); order += 1
    for batch, validator, config, evidence in [
        ("B01_GOLDEN_PAC_FORMAL", "PAC", "Formal", "evidence/pac/formal"),
        ("B02_GOLDEN_ACROBAT", "Acrobat", "Full Check", "evidence/acrobat"),
    ]:
        for golden in goldens:
            artifact_id = golden.stem
            suffix = "pdf" if validator == "PAC" else "json"
            item = queue_row(batch, order, artifact_id, golden, sha256(golden), "", artifact_id, validator, config, "golden_baseline", evidence, "Complete this baseline before interpreting any matching mutant.", suffix)
            item["status"] = "COMPLETE" if batch == "B02_GOLDEN_ACROBAT" and evidence_present(item) else old_status.get((batch, artifact_id), "TODO")
            rows.append(item)
            order += 1
    verapdf_manifest = ROOT / "data" / "verapdf_runs.csv"
    verapdf_reports = list((ROOT / "evidence" / "verapdf").glob("*.json"))
    verapdf_complete = verapdf_manifest.exists() and len(read_csv(verapdf_manifest)) == 84 and len(verapdf_reports) == 84
    verapdf_setup = queue_row("B03_VERAPDF_SETUP", order, "VERAPDF_BATCH_SETUP", ROOT / "scripts" / "run_verapdf_batch.py", "", "", "", "veraPDF", "PDF/UA-1 ua1 JSON batch", "setup", "evidence/verapdf", "Install veraPDF and run the single 84-file automated batch.")
    verapdf_setup["status"] = "COMPLETE" if verapdf_complete or old_status.get(("B03_VERAPDF_SETUP", "VERAPDF_BATCH_SETUP")) == "COMPLETE" else "TODO"
    rows.append(verapdf_setup)
    order += 1
    for batch, validator, config, evidence in [
        ("B04_MUTANT_PAC_FORMAL", "PAC", "Formal", "evidence/pac/formal"),
        ("B05_MUTANT_ACROBAT", "Acrobat", "Full Check", "evidence/acrobat"),
    ]:
        for row in mutants:
            path = artifact_path(row, False)
            suffix = "pdf" if validator == "PAC" else "json"
            item = queue_row(batch, order, row["mutant_id"], path, row["mutant_sha256"], row["operator"], Path(row["source_pdf"]).stem, validator, config, "mutant", evidence, "Deferred until the matching golden baseline is complete and reviewed.", suffix)
            item["sub_batch_id"] = f"{batch.split('_', 1)[0]}_{row['operator']}"
            previous = old_status.get((batch, row["mutant_id"]), "")
            item["status"] = "COMPLETE" if evidence_present(item) or previous == "COMPLETE" else "TODO" if baselines_ready else "DEFERRED_PENDING_GOLDEN_BASELINES"
            rows.append(item)
            order += 1
    ai_setup = queue_row("B06_PAC_AI_SELECTION", order, "PAC_AI_SELECTION_REVIEW", ROOT / "data" / "pac_ai_selection.csv", "", "", "", "PAC", "AI cohort selection", "setup", "evidence/pac/ai", "PAC AI mutant execution is deferred until PAC Formal evidence is classified.")
    previous_ai = old_status.get(("B06_PAC_AI_SELECTION", "PAC_AI_SELECTION_REVIEW"), "")
    ai_setup["status"] = "COMPLETE" if formal_complete else "DEFERRED_PENDING_FORMAL_RESULT"
    rows.append(ai_setup); order += 1
    if formal_complete:
        selected_golden_ids = sorted({row["golden_id"] for row in selected_ai})
        for golden_id in selected_golden_ids:
            golden = GOLDEN / f"{golden_id}.pdf"
            item = queue_row("B07_GOLDEN_PAC_AI_SELECTED", order, golden_id, golden, sha256(golden), "", golden_id, "PAC", "AI", "golden_baseline", "evidence/pac/ai", "Selected golden baseline for the post-formal PAC AI cohort.", "pdf")
            item["status"] = old_status.get(("B07_GOLDEN_PAC_AI_SELECTED", golden_id), "TODO")
            rows.append(item); order += 1
        for selection in selected_ai:
            row = next(item for item in mutants if item["mutant_id"] == selection["artifact_id"])
            item = queue_row("B08_MUTANT_PAC_AI_SELECTED", order, row["mutant_id"], artifact_path(row, False), row["mutant_sha256"], row["operator"], selection["golden_id"], "PAC", "AI", "mutant", "evidence/pac/ai", selection["selection_reason"], "pdf")
            item["status"] = old_status.get(("B08_MUTANT_PAC_AI_SELECTED", row["mutant_id"]), "TODO")
            rows.append(item); order += 1
    at_rows = select_at_rows(mutants)
    for at in at_rows:
        row = next((r for r in mutants if r["mutant_id"] == at["mutant_id"]), None)
        if row is not None:
            path = artifact_path(row, False)
            digest = row["mutant_sha256"]
        else:
            path = MUTANTS / f"{at['mutant_id']}.pdf"
            if not path.is_file():
                raise ValueError(f"AT selection references missing mutant PDF: {at['mutant_id']}")
            digest = sha256(path)
        at_queue_row = queue_row("B09_AT_REPRESENTATIVE", order, at["mutant_id"], path, digest,
                                 at["operator"], at["source_golden"], "NVDA", "Representative comparison",
                                 "mutant", "evidence/at/nvda", at["reason"])
        at_queue_row["exact_output_filename"] = output_name(at["mutant_id"], digest, "txt")
        at_queue_row["status"] = "COMPLETE" if at.get("status") == "COMPLETE" else old_status.get(("B09_AT_REPRESENTATIVE", at["mutant_id"]), "DEFERRED_PENDING_AI_EVIDENCE")
        rows.append(at_queue_row)
        order += 1
    return rows, at_rows


def write_queue() -> int:
    rows, at_rows = build_queue()
    pac_ai_rows = []
    selection_path = ROOT / "data" / "pac_ai_selection.csv"
    if selection_path.exists():
        with selection_path.open(newline="", encoding="utf-8-sig") as fh:
            pac_ai_rows = list(csv.DictReader(fh))
    selected_ai = [row for row in pac_ai_rows if row.get("selected_for_pac_ai") == "TRUE" and row.get("artifact_type", "mutant") == "mutant"]
    formal_complete = any(row["batch_id"] == "B07_GOLDEN_PAC_AI_SELECTED" for row in rows)
    with (ROOT / "manual_runs_todo.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=QUEUE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    with (ROOT / "data" / "at_selection.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=AT_FIELDS)
        writer.writeheader()
        writer.writerows(at_rows)
    queue_summary = {
        "previous_todo_count": 300,
        "new_queue_rows_including_setup": len(rows),
        "human_required_runs": sum(row["baseline_or_mutant"] != "setup" for row in rows),
        "immediate_actions": sum(row["status"] == "TODO" for row in rows),
        "future_formal_mutant_actions": sum(row["batch_id"] in {"B04_MUTANT_PAC_FORMAL", "B05_MUTANT_ACROBAT"} for row in rows),
        "pac_ai_maximum_mutants": 33 + 6,
        "pac_ai_maximum_goldens": 9,
        "pac_ai_maximum_total_runs": 33 + 6 + 9,
        "pac_ai_selected_mutants_now": len(selected_ai),
        "pac_ai_expected_after_formal_filtering": "PENDING_FORMAL_EVIDENCE" if not formal_complete else len(selected_ai),
        "nvda_comparisons": len(at_rows),
        "worst_case_total_human_actions": 20 + sum(row["baseline_or_mutant"] == "mutant" and row["batch_id"] in {"B04_MUTANT_PAC_FORMAL", "B05_MUTANT_ACROBAT"} for row in rows) + (33 + 6 + 9) + len(at_rows),
        "realistic_staged_total_excluding_unselected_ai": "PENDING_FORMAL_EVIDENCE",
        "by_validator_and_kind": {"|".join(key): value for key, value in sorted(Counter((row["validator"], row["configuration"], row["baseline_or_mutant"]) for row in rows).items(), key=str)},
        "setup_actions": sum(row["baseline_or_mutant"] == "setup" for row in rows),
        "provenance_setup_actions": sum(row["batch_id"] == "B00_CORPUS_PROVENANCE_REVIEW" for row in rows),
        "verapdf_setup_actions": sum(row["batch_id"] == "B03_VERAPDF_SETUP" for row in rows),
        "pac_ai_selection_setup_actions": sum(row["batch_id"] == "B06_PAC_AI_SELECTION" for row in rows),
        "at_representative_cases": len(at_rows),
    }
    (ROOT / "analysis" / "generated" / "manual_queue_summary.json").write_text(json.dumps(queue_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} evidence-preparation queue rows to {ROOT / 'manual_runs_todo.csv'}")
    print(f"Wrote {len(at_rows)} representative AT selections to {ROOT / 'data' / 'at_selection.csv'}")
    return len(rows)


def audit_purity() -> dict:
    rows = valid_mutants()
    findings = []
    for row in rows:
        verification = row.get("verification", {})
        parseability = verification.get("parseability", {})
        parse_ok = parseability is True or (isinstance(parseability, dict) and parseability.get("status") == "pass")
        checks = {
            "mutation_valid": verification.get("mutation_valid") is True,
            "parseability": parse_ok,
            "page_count_preserved": verification.get("page_count_preserved") is True,
            "rendering": verification.get("rendering", {}).get("status") == "pass",
            "unexpected_structural_changes_empty": not verification.get("unexpected_structural_changes"),
            "operator_delta_ok": bool(verification.get("operator_delta_reason")),
            "source_hash_stable": row.get("source_sha256") == verification.get("source_sha256"),
            "mutant_hash_stable": row.get("mutant_sha256") == verification.get("mutant_sha256"),
            "target_metadata": bool(row.get("generation", {}).get("delta", {}).get("target_object") or
                                     row.get("generation", {}).get("delta", {}).get("new_role") or
                                     row.get("generation", {}).get("delta", {}).get("new_alt") is not None or
                                     row.get("generation", {}).get("delta", {}).get("new_lang") is not None),
        }
        if row["operator"] == "M04":
            checks["m04_exact_association_delta"] = verification.get("operator_delta_reason") == "two leaf content associations exchanged"
            checks["m04_no_unintended_parent_change"] = not verification.get("unexpected_structural_changes")
        failures = [name for name, passed in checks.items() if not passed]
        findings.append({"mutant_id": row["mutant_id"], "operator": row["operator"], "status": "PASS" if not failures else "FLAG", "failures": ";".join(failures)})
    out = ROOT / "analysis" / "generated" / "purity_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["mutant_id", "operator", "status", "failures"])
        writer.writeheader(); writer.writerows(findings)
    return {"total": len(findings), "pass": sum(x["status"] == "PASS" for x in findings), "flagged": [x for x in findings if x["status"] != "PASS"]}


def distribution() -> dict:
    rows = valid_mutants()
    classes = {"M01": "semantic", "M02": "semantic", "M03": "machine-checkable", "M04": "semantic", "M05": "semantic", "M06": "machine-checkable", "M07": "machine-checkable", "M08": "machine-checkable", "M09": "machine-checkable", "M10": "machine-checkable"}
    per_operator = Counter(row["operator"] for row in rows)
    per_golden = Counter(Path(row["source_pdf"]).stem for row in rows)
    per_class = Counter(classes[row["operator"]] for row in rows)
    target_types = Counter()
    for row in rows:
        operator = row["operator"]
        delta = row.get("generation", {}).get("delta", {})
        if operator == "M08":
            target_types["Catalog (/Lang)"] += 1
            continue
        if operator == "M09":
            target_types["Catalog/StructTreeRoot (/RoleMap)"] += 1
            continue
        labels = str(delta.get("target_object", "")).split(";")
        try:
            reader = PdfReader(row["source_pdf"], strict=False)
            roles = []
            for label in labels:
                if ":" not in label:
                    continue
                obj, gen = map(int, label.split(":", 1))
                value = reader.get_object(IndirectObject(obj, gen, reader))
                if isinstance(value, dict) and value.get("/S"):
                    roles.append(str(value.get("/S")))
            target_types[" + ".join(roles) if roles else "REQUIRES_USER_VERIFICATION"] += 1
        except Exception:
            target_types["REQUIRES_USER_VERIFICATION"] += 1
    result = {"total_mutants": len(rows), "operators_total": len(classes), "machine_checkable_operators": sum(v == "machine-checkable" for v in classes.values()), "semantic_operators": sum(v == "semantic" for v in classes.values()), "mutants_per_operator": dict(sorted(per_operator.items())), "mutants_per_class": dict(per_class), "mutants_per_golden": dict(sorted(per_golden.items())), "mutants_per_target_structure_type": dict(sorted(target_types.items())), "warnings": []}
    if min(per_operator.values()) < 4:
        result["warnings"].append("An operator has fewer than four valid mutants.")
    result["warnings"].append("M10 has four valid mutants and is concentrated in the small subset of documents containing eligible table-cell targets; interpret per-operator results with coverage context.")
    out = ROOT / "analysis" / "generated" / "experimental_distribution.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
