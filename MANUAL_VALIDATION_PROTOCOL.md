# Manual validation protocol

This is the operational run guide for the rows in [`manual_runs_todo.csv`](manual_runs_todo.csv). Run batches in file order. Do not change a validator setting within a batch. Every report must be saved under the destination and use the exact filename in its queue row.

## Current repository status

The canonical formal stage is complete for 69 active mutants: PAC Formal, Acrobat Full Check, and veraPDF reports are present and classified against matching baselines. The remaining queue is primarily the nine representative NVDA observations plus setup/review rows. The preserved PAC AI package is aggregate-only, while a fresh native one-golden/one-mutant pilot exposed element-level finding text and scores in `Results in Detail` but no supported complete semantic export/API. All 34 selected mutant rows now have artifact-specific native PAC AI capture and remain `AI_AMBIGUOUS`/`REVIEW_REQUIRED` because the reproducible complete semantic export/API gate is still unmet. None can be admitted to canonical classification until that gate is met. Do not rerun completed formal batches or treat PAC AI aggregate counts as classifications.

## Global rules

Before each file, verify the displayed filename and compute the input SHA-256. It must equal the queue row. Do not repair, tag, optimize, flatten, or otherwise save over a tested PDF. Keep the original PDF unchanged.

For a mutant, first find the matching golden row with the same `source_golden`, validator, and configuration. A mutant failure that is already present in the golden is baseline-existing, not a mutation detection. Missing or unclear baselines remain unresolved.

Required report identity fields: tested artifact ID, tested SHA-256, validator name, version/build, OS, profile/configuration, run timestamp, and exported report path. A screenshot may supplement a report but does not replace the required identity record.

For B01/B04 PAC Formal, record the one-time PAC metadata in `data/pac_formal_run_metadata.json`. The ingestion command will not mark B01 complete while any value remains `REQUIRES_USER_ENTRY`.

## Staged batch order

1. `B00_CORPUS_PROVENANCE_REVIEW` — confirm the remaining source/license mappings.
2. `B01_GOLDEN_PAC_FORMAL` — 9 golden baselines. See [`docs/runs/B01_GOLDEN_PAC_FORMAL.md`](docs/runs/B01_GOLDEN_PAC_FORMAL.md).
3. `B02_GOLDEN_ACROBAT` — 9 golden baselines.
4. `B03_VERAPDF_SETUP` — install and run the automated 84-file batch; this is not a 75-row manual task.
5. `B04_MUTANT_PAC_FORMAL` — 69 active mutants, deferred until golden baselines are complete and reviewed; `PDFUA-Ref-2-09_Scanned-M08` is retained as an excluded baseline-conflict record.
6. `B05_MUTANT_ACROBAT` — 69 active mutants, deferred until golden baselines are complete and reviewed; `PDFUA-Ref-2-09_Scanned-M08` is retained as an excluded baseline-conflict record.
7. `B06_PAC_AI_SELECTION` — automatic selection after PAC Formal evidence is ingested; no PAC AI mutant run is currently actionable.
8. `B07_GOLDEN_PAC_AI_SELECTED` / `B08_MUTANT_PAC_AI_SELECTED` — only the selected semantic survivors and small machine-checkable controls.
9. `B09_AT_REPRESENTATIVE` — 9 comparisons after the formal/AI stages.

The narrative plan's `B03_MUTANT_PAC_FORMAL` and `B04_MUTANT_ACROBAT` labels are not used as queue IDs: `B03_VERAPDF_SETUP` already occupies B03. The canonical mapping is `B03_MUTANT_PAC_FORMAL` → `B04_MUTANT_PAC_FORMAL` and `B04_MUTANT_ACROBAT` → `B05_MUTANT_ACROBAT`. Use only the canonical IDs and their operator sub-batches (`B04_M01`–`B04_M10`, `B05_M01`–`B05_M10`) in evidence filenames and ingestion commands.

## PAC Formal

Before starting: record PAC version/build, Windows version, PDF/UA profile, language/region settings, and the AI state as disabled. Use one stable formal configuration for B01 and B04.

PAC's official FAQ states that PAC itself does not currently provide a command-line batch mode; therefore these PAC rows intentionally remain GUI runs. Do not substitute unsupported UI scripting or a different product.

For each file: open the exact queue filepath; verify its SHA-256; select the traditional/formal PDF accessibility validation; run the check; click PAC's **PDF report** export; save the PDF as `evidence/pac/formal/{exact_output_filename}`. Add a companion screenshot only when the exported report omits the filename/version/mode context.

If PAC instead produces its normal human-readable `{artifact_id}_PAC_UA_Report.pdf` export, preserve that raw file and run the evidence ingester for the relevant sub-batch. The ingester will create the prescribed hash-addressed copy only when the artifact-specific export is unique, the queue input SHA-256 matches, and the report parses as a PAC report; ambiguous files fail closed.

Record: automated pass/fail; every failed rule/check ID and exact name; version/build; profile; input hash; report path; and whether the failure is relevant to the operator. Complete the golden rows before any mutant row.

Do not count: warnings without a failed rule, manual-review prompts, cosmetic warnings, or a generic failure that cannot be mapped to the operator. Formal findings and AI suggestions are separate.

## PAC AI

Before starting: record the same PAC version/build, Windows version, PDF/UA profile, and exact AI feature/state/settings. Use AI enabled and keep the formal configuration otherwise unchanged. Do not merge this batch with PAC Formal.

For each file: open and hash-check the queue filepath; run formal validation plus the documented AI semantic analysis; export the complete PAC AI output; save it as `evidence/pac/ai/{exact_output_filename}`. Record automated formal failures separately from AI-generated semantic suggestions.

Do not count: an AI suggestion as a formal PDF/UA rule failure, a manual prompt as an automated detection, or a result with unknown AI state.

## Acrobat Accessibility Checker

Before starting: record Acrobat product/version/build, Windows version, checker name, Full Check configuration, document/reading-order options, and whether auto-tagging or remediation is disabled. Use the same configuration for B03 and B06.

Acrobat Pro has a general Action Wizard for multi-file actions, but this experiment does not assume that a Full Check plus per-file report export is a supported reproducible action. Unless you can demonstrate that the action preserves each queue row's file identity and exact checker settings, run Full Check one file at a time. Use the same checker configuration for B02 and B05.

For each file: open the queue filepath; verify SHA-256; run Accessibility Checker / Full Check; export the complete report; save it under `evidence/acrobat/`. Acrobat's native export is HTML in the tested build. Preserve that native file with the hash-addressed `.accreport.html` name; the queue's `.json` name is the canonical evidence slot, and ingestion accepts the preserved native companion without relabeling it as JSON. If the export format is not JSON, retain the native export and add screenshots only for content that the export omits.

Record: automated failed rule/check names exactly as shown; “Needs Manual Check” items in a separate field; version/build; OS; configuration; input hash; report path; and operator relevance.

Do not count: “Needs Manual Check” prompts, advice, or a category that only asks a human to inspect something. Only a relevant automated failure can be a kill/detection. Baseline-existing automated failures do not count against the mutant.

## veraPDF

veraPDF is intended to be automated. After installation, record the executable path and output of `verapdf --version` (or `verapdf.bat --version`), then run:

```text
python scripts/run_verapdf_batch.py --executable "C:\\path\\to\\verapdf.bat"
```

The script invokes the built-in PDF/UA-1 profile `ua1`, emits JSON, includes logs, writes one hash-addressed raw report per golden/mutant under `evidence/verapdf/`, and records the run metadata in `data/verapdf_runs.csv`. Do not manually create 84 veraPDF rows.

## Evidence ingestion

After reports are saved, run the operator sub-batch ingestion command, for example `python scripts/ingest_validator_evidence.py --sub-batch B04_M01`. This verifies only that sub-batch while preserving all previously ingested canonical records. After a complete formal stage, run:

```text
python scripts/ingest_validator_evidence.py
python scripts/rebuild_analysis.py
```

The ingester matches exact queue filenames and input hashes, parses machine-readable JSON where possible, creates `data/baseline_deltas.csv`, and leaves classifications blank when the report is ambiguous or operator relevance has not been explicitly established. It never turns a missing report into a pass or a miss.
