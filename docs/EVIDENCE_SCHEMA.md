# Evidence schema

## Mutant manifest (`data/mutants.jsonl`)

One JSON object per generated mutant. Required identity fields are `mutant_id`, `operator`, `source_pdf`, `mutant_pdf`, `source_sha256`, `mutant_sha256`, and `status`. The nested `generation` object records the target and intended delta. The nested `verification` object records parseability, target delta, page/content/render invariants, unexpected changes, and `mutation_valid`.

## Exclusions (`data/exclusions.csv`)

Each exclusion has a mutant ID, operator, source, status, objective reason, verdict, action, evidence timing, and whether the ID was present in the valid manifest. Excluded artifacts and raw reports remain in the repository; they are removed from active denominators only through this table.

## Validator ledger (`data/validator_runs.csv`)

Each row identifies `record_id`, `artifact_id`, `baseline_or_mutant`, `source_golden`, `operator`, `file_sha256`, `validator`, `configuration`, version/build/platform/profile, raw report path/hash, baseline status and hash, classification, classification reason, coder fields, adjudication, and notes. The active formal subset is mutant rows for PAC/Formal, Acrobat/Full Check, and veraPDF/PDF/UA-1 ua1.

## Independent verification (`evidence/independent_verification_v2/*.json`)

One record per active mutant pair. It includes source/mutant hashes, page/content/annotation/image invariants, MuPDF rendering status, independent delta status, observed structural details, unexpected changes, and mutation confidence. `PASS` means the narrow independent route confirmed the tested property; `REVIEW_REQUIRED` is not silently promoted to pass.

## Controls and AT

`data/controls.csv` stores the paired no-op/benign artifacts, hashes, native report paths/hashes, and native findings. `data/control_results.csv` is a derived view and keeps unresolved target-relevance judgments explicit. `data/at_observations.csv` stores the baseline/mutant hashes, software versions, OS, procedure, transcripts/log references, observed difference, and repeat status. AT observations are descriptive and separate from formal classifications.

## Derived outputs

`STUDY_MANIFEST.json` is the canonical count and scope summary. `data/baseline_provenance.csv`, `data/operator_standard_mapping.csv`, `data/operator_target_selection.csv`, `data/validator_environment.csv`, and `analysis/generated/*.csv` are generated views. Historical `data/pdfa11ymut_*` files are not canonical inputs and must be labeled historical wherever retained.
