# Data

This folder contains machine-readable summary data for the PDFa11yMut experiment.

## Files

- `pdfa11ymut_detection_matrix.csv` - full mutant-by-validator matrix, preserving N/A cases.
- `pdfa11ymut_overall_rates.csv` - overall validator detection rates.
- `pdfa11ymut_per_operator_rates.csv` - detection rates by mutation operator.
- `pdfa11ymut_validator_agreement.csv` - pairwise validator agreement summary.
- `pdfa11ymut_metrics_summary.json` - compact metrics summary.
- `pdfa11ymut_detection_analysis_data.json` - structured analysis data used to build outputs.

Detection means the validator reported a relevant automated failure corresponding to the injected mutation category. Missed means no relevant automated failure was reported for an independently verified mutant. N/A means the mutant was not generated and is excluded from detection-rate denominators.
