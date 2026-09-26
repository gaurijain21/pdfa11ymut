# Scripts

The active scripts operate from repository-relative canonical data.

## Files

- `rebuild_analysis.py` - builds active matrices, rates, and status summaries from `data/`.
- `build_figures.py` - builds a status-aware SVG from generated analysis data.
- `build_detection_analysis.py` - compatibility wrapper for `rebuild_analysis.py`.
- `build_paper_figures.py` and `build_ieee_assets.py` - compatibility wrappers for the active figure builder.
- `build_detection_workbook.mjs` - refuses to write a workbook from stale values.
- `check_evidence.py` - reports missing hash-linked PAC, Acrobat, and AT evidence.
- `execute_controls.py` - creates and independently verifies the 18 no-op/benign control artifacts without running validators.
- `run_verapdf_controls.py` - runs the locally installed veraPDF PDF/UA-1 profile over all control artifacts and stores raw JSON reports plus hashes.
- `ingest_control_evidence.py` - fail-closed ingestion for all 18 PAC PDF, Acrobat native HTML, and veraPDF control reports; records report paths, hashes, versions, profiles, and parsed summary counts in `data/controls.csv`.
- `run_verapdf_batch.py` - runs all 9 goldens and 75 mutants through veraPDF's PDF/UA-1 `ua1` profile and saves hash-addressed JSON reports.
- `ingest_validator_evidence.py` - matches prescribed reports to queue rows, safely reconciles uniquely identified human-readable PAC exports into hash-addressed copies, parses machine-readable facts, and computes baseline status without inferring detections. Raw exports remain untouched and ambiguous mappings fail closed. Use `--sub-batch B04_M01` (or another canonical operator sub-batch) for incremental ingestion; missing later operators do not block the selected sub-batch.
- `build_formal_freeze.py` - emits the formal-result freeze and review gate after PAC Formal, Acrobat, and veraPDF evidence is classified.
- `prepare_double_coding.py` - prepares the 207-case blinded formal double-coding queue, steward key, and optional opaque evidence packet; it never mutates canonical classifications. Run `python scripts/prepare_double_coding.py --materialize` only when the independent-coder packet is ready.
- `merge_double_coding.py` - validates completed coder/adjudicator fields and, only with explicit `--apply`, writes the three canonical coder fields; it fails closed on partial or conflicting queues.
- `rebuild_analysis.py` - rebuilds formal rates/class summaries from canonical data and reports `formal_complete_at_complete_pac_ai_future_work`; the separate PAC-AI cohort remains gated future work because the preserved package is aggregate-only and the fresh native pilot lacks a supported complete semantic export/API.
- `independent_audit.py` - writes MuPDF rendering invariants and narrowly scoped raw-COS checks to `evidence/independent_verification_v2/`. Structural deltas are `CONFIRMED`, `CONTRADICTED`, or `UNVERIFIABLE`; generator-side verification is labeled separately. Existing v1 reports are left untouched. Use repeated `--mutant-id` arguments for targeted audits.
- `robustness_sensitivity.py` - prints Wilson and source-cluster bootstrap intervals for baseline-pass, binary machine-checkable cases, plus descriptive counts for semantic cases. It excludes baseline-confounded and non-binary/manual classifications, so denominators can be smaller than 207; it does not estimate accuracy or specificity.
- `reconcile_canonical.py` - reconciles validator metadata, report hashes, baseline inventory, AT provenance, and the release manifest.

The staged evidence-preparation queue is regenerated with `python -m pdfa11ymut manual-plan`. It writes `data/at_selection.csv`, `data/pac_ai_selection.csv`, `analysis/generated/experimental_distribution.json`, `analysis/generated/purity_audit.csv`, and `analysis/generated/manual_queue_summary.json`. PAC AI mutant rows are created only after formal PAC evidence is complete and classified.

The previous generated release files remain historical artifacts. They are not read by the active pipeline.
