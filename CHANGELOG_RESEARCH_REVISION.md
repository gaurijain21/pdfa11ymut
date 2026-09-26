# Research revision changelog

## 2026-09-21 - formal evidence reconciliation

- Rebuilt active analysis from the canonical 292-row validator file: 222 formal rows across 74 active mutants are classified, with PAC-AI rows kept separate.
- Corrected the formal-freeze builder so PAC-AI rows cannot enter the formal freeze; regenerated the 222-row freeze and hash manifest.
- Updated the active manuscript to include generated formal results and to treat PAC AI as unresolved future work rather than the study's main result.
- The remaining blockers are nine NVDA observations and LaTeX/release QA. Corpus filename mapping and collection-level licensing are now documented; the historical download archive/timestamp remains an explicit limitation. The historical G02-M04 case is closed by permanent exclusion.
- The historical G02-M04 audit is now closed as permanently excluded because the exact pair and COS-level/raw-report trail are absent; current local M04 mutants remain separate.

## 2026-09-18 - corpus generation and verifier hardening

- Imported nine golden reference PDFs and generated 75 valid mutants after parse, structure, content, and exact-render checks.
- Added Poppler discovery through `PDFa11YMUT_PDFTOPPM` plus the bundled runtime fallback.
- Added custom-role traversal and cycle protection, golden-render caching, manifest upsert, and clean rerun support.
- Corrected M07 verification to account for path renumbering/shared structure references; all five previously excluded M07 cases now pass.
- Rebuilt the manual queue with 300 TODO rows; validator and AT evidence remain pending.

## 2026-09-17 - evidence-first rebuild

- Audited the existing repository and recorded the missing corpus, generator, verifier, raw evidence, and provenance in `AUDIT.md`.
- Added formal operator metadata for M01-M10, including Class A versus Class B, preconditions, invariants, expected deltas, and evidence TODOs.
- Added a deterministic pypdf-based generation pipeline and validator-independent structural/render verification path. It fails closed on missing targets and failed invariants.
- Added canonical data schemas for mutants, validator runs, AT observations, corpus provenance, and controls.
- Replaced the hardcoded analysis entry point with a data-driven rebuild that excludes historical summary tables.
- Added one-command reproduction, manual PAC Formal/PAC AI/Acrobat/NVDA protocol, TODO file, license/provenance files, and quality/reviewer documents.
- Marked the old 23-mutant numerical results stale for active analysis. They are not deleted from historical Git history, but they are not reproduced or restated by the rebuilt pipeline.
- Historical G02-M04 is permanently excluded because the golden and mutant PDFs required for COS-level purity analysis are absent. It is not counted as a result; current local M04 mutants are separate.
