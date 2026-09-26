# B04_MUTANT_PAC_FORMAL

This is the canonical `PAC` mutant evidence batch. It contains 69 active mutants and excludes all documented exclusions, including `PDFUA-Ref-2-09_Scanned-M08`.

The narrative labels `B03_MUTANT_PAC_FORMAL` and `B04_MUTANT_ACROBAT` are not queue IDs because `B03_VERAPDF_SETUP` is already established. The canonical mapping is PAC Formal=`B04_MUTANT_PAC_FORMAL`; Acrobat=`B05_MUTANT_ACROBAT`.

## Fixed configuration

- Required configuration: PAC `26.1.0.0`, Formal/traditional PDF/UA check, AI OFF.
- Before each file, confirm `HKCU\Software\axes4\PAC\EnableAIChecks=0` and verify the input SHA-256 matches this checklist.
- Open the exact mutant PDF, run the Formal check, and export the PDF report without remediation or saving over the input.
- Save the report using the exact hash-addressed filename under `evidence/pac/formal/`.
- Record automated failures separately from manual-review prompts. Do not classify findings during collection.

## Operator sub-batches

- [`B04_M01`](subbatches/B04_M01.md) — 9 PDFs
- [`B04_M02`](subbatches/B04_M02.md) — 9 PDFs
- [`B04_M03`](subbatches/B04_M03.md) — 8 PDFs
- [`B04_M04`](subbatches/B04_M04.md) — 8 PDFs
- [`B04_M05`](subbatches/B04_M05.md) — 7 PDFs
- [`B04_M06`](subbatches/B04_M06.md) — 7 PDFs
- [`B04_M07`](subbatches/B04_M07.md) — 7 PDFs
- [`B04_M08`](subbatches/B04_M08.md) — 8 PDFs
- [`B04_M09`](subbatches/B04_M09.md) — 3 PDFs
- [`B04_M10`](subbatches/B04_M10.md) — 4 PDFs

## Baseline-delta rules

Compare every mutant with the exact matching golden baseline for the same validator and configuration. Baseline-carried failures, manual prompts, unrelated failures, and collateral findings are not intended-defect detections.

For `PDFUA-Ref-2-05_BookChapter-german-M06`, the Acrobat baseline's pre-existing `Lbl and LBody` failure is outside the M06 target branch. It must be retained as baseline context and never counted as an M06 detection.

## Evidence ingestion

Run `python scripts/ingest_validator_evidence.py --batch B04_MUTANT_PAC_FORMAL` after the complete batch, or use the operator-specific command in each sub-batch guide for incremental ingestion.
