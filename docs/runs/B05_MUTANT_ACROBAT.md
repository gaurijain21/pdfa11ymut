# B05_MUTANT_ACROBAT

This is the canonical `Acrobat` mutant evidence batch. It contains 69 active mutants and excludes all documented exclusions, including `PDFUA-Ref-2-09_Scanned-M08`.

The narrative labels `B03_MUTANT_PAC_FORMAL` and `B04_MUTANT_ACROBAT` are not queue IDs because `B03_VERAPDF_SETUP` is already established. The canonical mapping is PAC Formal=`B04_MUTANT_PAC_FORMAL`; Acrobat=`B05_MUTANT_ACROBAT`.

## Fixed configuration

- Required configuration: Adobe Acrobat Pro Continuous Release `2026.002.21931`, Accessibility Checker / Full Check, all 31 checks, all pages.
- Auto-tagging, remediation, and document modification remain disabled.
- Before each file, verify the input SHA-256, run Full Check, and export the native HTML report.
- Preserve the native report under `evidence/acrobat/` using the exact hash-addressed `.accreport.html` filename associated with the queue row.
- Record automated failures separately from `Needs Manual Check` items. Do not classify findings during collection.

## Operator sub-batches

- [`B05_M01`](subbatches/B05_M01.md) — 9 PDFs
- [`B05_M02`](subbatches/B05_M02.md) — 9 PDFs
- [`B05_M03`](subbatches/B05_M03.md) — 8 PDFs
- [`B05_M04`](subbatches/B05_M04.md) — 8 PDFs
- [`B05_M05`](subbatches/B05_M05.md) — 7 PDFs
- [`B05_M06`](subbatches/B05_M06.md) — 7 PDFs
- [`B05_M07`](subbatches/B05_M07.md) — 7 PDFs
- [`B05_M08`](subbatches/B05_M08.md) — 8 PDFs
- [`B05_M09`](subbatches/B05_M09.md) — 3 PDFs
- [`B05_M10`](subbatches/B05_M10.md) — 4 PDFs

## Baseline-delta rules

Compare every mutant with the exact matching golden baseline for the same validator and configuration. Baseline-carried failures, manual prompts, unrelated failures, and collateral findings are not intended-defect detections.

For `PDFUA-Ref-2-05_BookChapter-german-M06`, the Acrobat baseline's pre-existing `Lbl and LBody` failure is outside the M06 target branch. It must be retained as baseline context and never counted as an M06 detection.

## Evidence ingestion

Run `python scripts/ingest_validator_evidence.py --batch B05_MUTANT_ACROBAT` after the complete batch, or use the operator-specific command in each sub-batch guide for incremental ingestion.
