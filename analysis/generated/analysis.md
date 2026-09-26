# Active analysis

This report is generated from `data/mutants.jsonl`, `data/mutant_exclusions.csv`, `data/validator_runs.csv`, and `data/corpus_inventory.csv`.

## Status

Formal validation is complete for 69 active mutants. PAC AI remains separate from formal outcomes: the preserved package is aggregate-only, while the fresh native pilot exposed element-level finding text and scores but no supported complete semantic export/API, so the full cohort remains gated. AT observations are complete for nine illustrative exploratory cases under one fixed configuration and are qualitative, not validator detections.

## Mutation-specific checker outcomes

| Validator | Detected | No automated target finding | Needs manual check | Not applicable | Classified total | Rate (descriptive overall view) |
|---|---:|---:|---:|---:|---:|---:|
| PAC | 30 | 39 | 0 | 0 | 69 | 43.5% |
| Acrobat | 26 | 28 | 15 | 0 | 69 | 48.1% |
| veraPDF | 30 | 39 | 0 | 0 | 69 | 43.5% |

Rates are Detected/(Detected + No automated target finding); manual and not-applicable rows are excluded. Rows without a canonical report and classification remain TODO and are excluded from rates.

Mutants are nested within nine golden baselines. `source_cluster_summary.csv` reports per-baseline descriptive rates, and `source_cluster_bootstrap.csv` resamples complete baselines together for a deterministic sensitivity interval; these intervals are not population-level confidence claims.

`detection_sensitivity.csv` separates direct target detections from the three Acrobat M10 consequence-proxy detections.

## Scope

Valid verified mutants: 73
Active mutants: 69
Corpus inventory records: 9
Canonical validator rows: 292

AI-assisted PAC rows are retained as a separate mode and are never merged with formal outcomes.
