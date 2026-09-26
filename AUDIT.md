# PDFa11yMut Repository Audit

Audit date: 2026-09-17

## Existing artifact inventory

At the initial audit the repository contained analysis summaries, duplicate paper sources, generated figures, an editable workbook, scripts, a release ZIP, and Git history, but no executable mutation pipeline or corpus. The repair work has since imported nine golden PDFs and generated 75 valid mutants. This paragraph records the initial state; the current reconciliation below supersedes its evidence-status wording.

`vera_evaluation.docx` from the supplied project mirror is not in this Git checkout. Even if copied in, it would be a narrative record rather than a raw veraPDF export.

## Reproducibility failures

- The original analysis read a manifest from `C:\Users\iamga\AppData\Local\Temp\...`, outside the repository.
- `detected_by` and `failure_details` were hardcoded in the analysis script.
- The original 23 inputs and outputs described by the paper were absent at audit time; the current nine-file corpus has now been hashed and locally verified through the rebuilt pipeline.
- Raw validator exports, exact versions/settings, PAC formal versus AI configuration, and manual classification records are absent.
- No operator specification, dependency manifest, test suite, CI workflow, or one-command reproduction existed.
- Corpus provenance, source filenames, PDF/UA version, licenses, page counts, and structural coverage were absent.
- Several artifacts use historical fixed numbers and call evidence from a prior conversation rather than a repository path.
- The active paper sources are not generated from canonical data and could not be accepted as current results.

## Scientific concerns

The historical five-operator artifact mixed semantic/human-judgment properties with machine-checkable conformance constraints without a formal taxonomy. The claimed “independent verification” was not auditable from the initial repository. Historical G02-M04 is permanently excluded because its summary reports Acrobat and veraPDF list containment failures for an intended marked-content association swap, but the exact pair and COS trees are absent. No conclusion about that historical case is scientifically supportable.

The old one-mutant-per-operator-per-document design confounds operator and source structure. The corpus is too small for broad accuracy claims, and there is no assistive-technology evidence. The old 4/23, 5/23, and 17.4%/21.7% values are historical claims only; they are not loaded by the rebuilt analysis.

## Repair disposition

This revision adds a fail-closed PDF mutation/generation and verification pipeline, machine-readable specifications for M01-M10, canonical evidence schemas, data-driven analysis, manual-run planning, reproducibility documentation, reviewer-attack and contribution-evidence documents, and an active manuscript generated from canonical data. It does not fabricate missing PDFs, validator results, AT observations, or licenses.

## Current reconciliation — 2026-09-21

- PAC Formal, Acrobat Full Check, and veraPDF raw evidence is present and hash-linked. The repaired formal freeze contains 210/210 classified rows for 70 active mutants.
- The canonical active analysis reports PAC 30 detections and 40 misses, Acrobat 23 automated detections, 31 misses, and 16 separate manual-check rows, and veraPDF 30 detections and 40 misses. PAC-AI remains separate future work at 34/34 aggregate-only rows; nine NVDA observations are complete as a qualitative single-observer pilot.
- The active exclusions are G09-M08, four prior unused-RoleMap M09 targets, and the historical G02-M04 case, permanently excluded because its exact pair and COS-level/raw-report trail are unavailable. Current hash-linked M04 mutants are separate.
- Corpus filename mapping and collection-level licensing are resolved. The original download archive/timestamp was not retained; this is documented as a provenance limitation rather than silently treated as byte-level acquisition evidence. G02-M04 is permanently excluded. The manuscript now compiles and passes raster inspection; the clean live M01 rerun is complete and the curated release archive is hash-verified. The historical NVDA log's instability is retained as context, while the fresh paired rerun is the canonical current observation.
