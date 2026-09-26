# Final quality gate snapshot

Checked 2026-09-25.

## Passed

- Active analysis reads canonical data only, records 73 valid verified generation records, excludes the five documented exclusion rows, and reports 69 active mutants with 207 classified formal validator rows.
- All ten operator specifications contain required metadata.
- Synthetic tagged-PDF fixture exercises M01-M10.
- Parseability, page-count, page-content, exact-rendering, and operator-delta checks pass on the fixture and all 73 valid verified generation records; the 69 active records are the five-exclusion subset used for formal analysis, and four prior M09 artifacts are explicitly retired for unused targets.
- Missing corpus fails generation closed.
- Active scripts contain no old hardcoded detection values or private temporary manifest path.
- `git diff --check` reports no whitespace errors.
- Independent double-coding and adjudication are complete for 207/207 formal rows: 204 agreements, three adjudicated disagreements, and no unresolved final `Ambiguous` labels.
- The two PAC evidence-identity defects are corrected; original blinded packets are retained under `evidence/double_coding/original_misassigned/` and recorded in `data/double_coding_corrections.csv`.
- Four M10 pairs pass fresh 150-DPI verification. Three newly failed Acrobat `Headers` checkpoints satisfy the predeclared `/TH` to `/P` direct-consequence proxy; the fourth remains a miss.

## Blocked or unresolved

- Corpus filename mapping and collection-level licensing are resolved in `data/corpus_provenance_sources.csv`; the missing 2-07 suite item and unretained historical download archive are documented limitations. Baseline-validator inventory records remain part of the evidence review.
- PAC Formal, Acrobat, veraPDF, and all 18 negative-control reports are present and hash-linked. PAC AI has native screenshots but no usable semantic finding identity/text or reproducible semantic export, so all 34 PAC AI rows remain unresolved future work.
- Nine NVDA observations are complete as a single-observer illustrative exploratory case series, not a representative pilot. A clean paired NVDA/Acrobat rerun confirms the M01 reading-order effect, while M08 preserves the observed no-difference result. Fresh M01 Speech Viewer captures and the historical raw log are preserved; AT observations remain separate from validator detection rates.
- The historical G02-M04 label is permanently excluded because its exact golden/mutant/COS audit trail is absent. Current M04 mutants pass the association-only purity gate and remain separate from that historical case.
- The clean live M01 rerun is complete. Acrobat and NVDA were targetable through the native bridge, the matched golden/mutant inputs were hash-verified, and separate Speech Viewer captures preserve the opening sequence for each file.
- The current manuscript PDF passes visual/raster inspection and the local semantic PDF/UA gate: its structure tree contains document, heading, paragraph, caption, table, row, header-cell, data-cell, and link elements. A target venue's additional policy remains to be applied; see `docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`.
- Raw vendor/AT evidence is explicitly excluded from the public Git freeze; no vendor/participant redistribution clearance is claimed for excluded bytes. Hashes and public substitutes remain canonical.
- The primary verifier uses pypdf and `scripts/independent_audit.py` adds PyMuPDF/MuPDF parser and renderer checks. M09 now requires the RoleMap key to be used by a reachable structure element; four prior unused-target M09 artifacts are explicitly retired.

## Readiness

**READY for the scoped formal study, the public bundle excluding raw vendor/AT evidence, and the local semantic PDF gate.** The formal validator phase, 207-row coding/adjudication, negative-control execution, and nine evidence-linked AT observations are complete for the active 69-mutant scope. PAC AI is optional future work and G02-M04 is permanently excluded. The artifact supports mutation-specific detection evidence and descriptive controls; it does not claim general accessibility accuracy, specificity, or population-level AT effects. Apply any chosen venue's additional PDF/UA policy before submission.
