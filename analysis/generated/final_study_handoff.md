# PDFa11yMut Final Study Handoff

**Repository:** project root  
**Handoff status:** `CONDITIONALLY_READY_FORMAL_AND_AT_COMPLETE_PAC_AI_FUTURE_WORK`  
**Analysis status:** `formal_complete_at_complete_pac_ai_future_work`

This handoff records the reconciled canonical state. Formal validation is complete for the active scope, and nine NVDA observations are complete as a qualitative single-observer pilot. PAC AI remains unresolved future work and is not required for the formal study completion.

## Completed validation phases

### Formal validation

- Formal validation is frozen and complete: **207/207 classified formal rows**.
- The active formal mutant scope is 69 verified mutants (73 valid verified generation records before documented exclusions; three replacement M09 candidates remain outside active interpretation).
- Canonical analysis reports `classified_formal_rows=207` and `required_classified_formal_rows=207`.
- PAC Formal, Acrobat Full Check, veraPDF, and all 18 negative-control reports are present in the repository’s canonical evidence and validator-run records.

### Acrobat B05

- `B05_MUTANT_ACROBAT`: **69/69 active mutants complete**.
- The documented excluded artifact is `PDFUA-Ref-2-09_Scanned-M08`.
- Four historical M09 artifacts remain excluded as `EXCLUDED_UNVERIFIABLE_TARGET` because their original mutant bytes are unavailable for re-audit. The active generator now requires the mutated custom role to be used by a reachable structure element.
- Acrobat evidence is preserved under `evidence/acrobat` and remains separate from formal classifications during collection and adjudication.
- Acrobat automated failures remain separate from `Needs Manual Check` findings.

## Unresolved PAC AI phase

- PAC AI cohort: 8 B07 goldens and 34 B08 mutants.
- Semantic capture manifest: 42 artifacts; raw native semantic screenshots are preserved.
- PAC AI classifications: **34/34 `AI_AMBIGUOUS` and `REVIEW_REQUIRED`**; all selected rows now have artifact-specific native capture, but canonical admission remains gated by the missing complete semantic export/API.
- PAC AI classified mutants: **0/34**.
- No detection or non-detection has been inferred from aggregate counts.
- Current status is `formal_complete_at_complete_pac_ai_future_work`; PAC AI remains unresolved future work and is not a formal-study completion gate.

The canonical limitation and decision record is:

`analysis/generated/pac_ai_aggregate_count_adjudication.md`

That record documents PAC 26.1.0.0, the one-golden/one-mutant native pilot, verified pilot SHA-256 values, the preserved aggregate-only package, the element-level finding text/scores exposed by the fresh pilot, the absence of a supported complete semantic export/API, and the reason the full 34-row cohort remains gated despite all selected rows now having artifact-specific native capture.

The final pilot result is `FAILED_SEMANTIC_EVIDENCE_GATE`: golden and mutant filepath/SHA-256 verification passed and PAC exposed element-level finding identity/text, scores, and page visualization, but no supported complete semantic export/API was available for a reproducible full-cohort run. The frozen rerun was not started.

## Baseline conflicts and exclusions

- Baseline operator conflicts: **1 directly resolved row** in `data/baseline_conflict_resolutions.csv`, plus the separately documented G09-M08 exclusion.
  - G05-M06 is retained with a documented baseline delta; pre-existing Acrobat `Lbl and LBody` failures are not counted as M06 detections.
  - G09-M08 is retained as a documented tool-specific baseline conflict and excluded from active interpretation.
- Cross-validator baseline disagreements: **4 documented** in `analysis/generated/baseline_cross_validator_disagreements.csv`; the prescribed baseline-relative actions are recorded there.
- G09 baseline-fail descendants remain excluded from active interpretation.
- Historical G02-M04 is permanently excluded because its exact pair and COS-level audit trail are absent; current local M04 mutants remain separate.

## AT status

- Nine selected cases are `COMPLETE` in `data/at_observations.csv` and `data/at_selection.csv`.
- Evidence combines the preserved transcript/log provenance with targeted Speech Viewer captures for M01 and M08; screenshots are not required for every pilot case.
- The design is a single-observer illustrative exploratory sample under one fixed NVDA/Acrobat/Windows configuration; it is not representative and is not a user study.
- The clean paired M01 rerun confirms the reading-order effect in the tested NVDA/Acrobat configuration; the historical instability is retained as context rather than silently discarded.
- M08 preserves the observed no-difference result.
- AT observations are qualitative and are not validator detection rates.

## Integrity and scope controls

- No tested PDF was modified, repaired, tagged, optimized, flattened, overwritten, or saved over.
- Canonical validator metadata was reconciled with raw report hashes, versions, builds, profiles, and explicit no-rule/manual-check fields.
- Baseline inventory records now reference all three formal validator baselines per golden and document the G05-M06 and G09-M08 conflicts.
- Corpus hygiene is documented in `data/corpus_extra_artifacts.csv`; the mismatch-backup PDF is retained but excluded from the reproducible corpus.
- Analysis and formal-freeze outputs were regenerated from canonical data.

The clean paired M01 rerun is complete. Acrobat and NVDA were targetable through the native bridge, both inputs were hash-verified, and separate Speech Viewer captures preserve the opening sequence for the golden and mutant.

## Required continuation gate

A different PAC build or supported interface must expose semantic finding identity or text with reproducible export/API. The current formal and AT phases do not depend on PAC AI completion.

Negative-control execution is complete: `data/controls.csv` contains 18 `COMPLETE` rows with PAC, Acrobat, and veraPDF report hashes. Role-labeled coding fields and adjudication are preserved for all 207 rows as internal audit provenance; no independent-human coding claim is made. No full-accuracy claim is made because this study estimates mutation-specific detection behavior, not population-level validator accuracy.
