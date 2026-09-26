# Harness controls

Controls are sanity checks, not study operators and not positive-study results. The canonical ledger contains 18 controls (one byte-preserved no-op and one metadata-only benign transformation per golden). All 18 control artifacts and all three validator evidence sets now pass hash-linked verification.

## Equivalent/negative control

Copy a golden PDF without changing bytes, verify identical hashes/renderings, then run each validator against the copied file. A future structure-level no-op may be added only if it has a documented semantic equivalence argument.

## Positive machine-checkable controls

M03, M06, M07, M08, M09, and M10 are candidates for positive conformance controls because their transformations target mechanically inspectable structure or metadata constraints. Each control must be run against a clean baseline and a relevant validator profile, with raw evidence, before being used to interpret a validator's mutation results.

The canonical `data/controls.csv` file records control status and evidence. `scripts/execute_controls.py` writes the 18 control PDFs and independent JSON checks under `evidence/controls/`; `scripts/run_verapdf_controls.py` records veraPDF 1.30.2 PDF/UA-1 JSON reports; `scripts/ingest_control_evidence.py` records SHA-256-linked PAC and Acrobat observations and marks rows `COMPLETE` only after all required reports parse successfully. All 18 PAC PDF reports and all 18 Acrobat native HTML reports were run in-session under `evidence/controls/pac/` and `evidence/controls/acrobat/`. See `docs/NATIVE_VALIDATOR_SESSION.md` for the working runtime and native configuration. This completes negative-control execution/evidence; specificity, precision, false-positive rate, and full accuracy remain withheld because these controls are not positive-study results. The formal ledger contains two recorded coding fields and adjudication, but the repository does not substantiate independent-human double-coding provenance.

The ledger retains raw native findings for paired baseline review. In particular, both G05 Acrobat reports contain one failed “Lbl and LBody” rule and both G09 PAC reports contain one failed Natural language checkpoint; because the no-op and benign members agree, these are baseline observations, not mutation detections.
