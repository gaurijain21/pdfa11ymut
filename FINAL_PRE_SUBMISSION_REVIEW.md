# Final Pre-Submission Review

This review covers the paper-freeze-v2 preparation state after the final analysis, evidence, manuscript, and reproducibility repairs. It is a submission-readiness assessment, not a claim of venue acceptance or universal PDF/UA conformance.

## Summary

The canonical study state is internally consistent: 73 valid verified generation records, 5 documented exclusions, 69 active mutants, 30 Class-A mutants, 39 descriptive Class-B mutants, 207 classified formal validator rows, 18 controls, and 9 assistive-technology observations. The paper and generated fragments now use counts-only reporting for the combined scope, score only Class A, and report Class B descriptively. The final PDF compiles to five tagged pages.

## Remaining major concerns

- Proprietary PAC and Acrobat evidence cannot be redistributed as raw vendor reports. Sanitized, hash-linked public evidence records are provided; reproduction of those two configurations requires the recorded local software and settings.
- Class-B mutations are semantic or assistive-representation changes without an automated target-finding ground truth. They are intentionally descriptive, not a second scored detection study.
- Assistive-technology results are a single-observer, single NVDA/Acrobat/Windows configuration and are illustrative rather than population-level accessibility evidence.
- The six-pair alternate-target exercise verifies structural invariants only; native PAC/Acrobat reruns were not performed for that secondary sample.
- The M09 exclusion sensitivity exercise has no usable historical validator outcomes and therefore cannot establish a replacement effect estimate.

## Remaining minor concerns

- Some TeX underfull-box warnings remain in dense tables and prose, but no overfull box remains and the final PDF is five pages.
- The native Codex LaTeX compiler was unavailable on this Windows host; the paper was compiled successfully with the repository-pinned local Tectonic binary and independently inspected with PDF metadata/render checks.

## Validity and claim review

### Novelty risk

MITIGATED. The contribution is framed as a transformation-based, mutation-specific benchmark and evidence pipeline, not as the invention of accessibility checking or a claim that all validators are comprehensively characterized. Kumar et al. is positioned as adjacent benchmark precedent; PDF/UA Techniques and Matterhorn are treated as standards/testing context.

### Construct validity

MITIGATED. The unit of analysis, Class-A/Class-B boundary, exclusion arithmetic, validator configurations, manual-review category, controls, and AT scope are explicit. Class B remains an inherent limitation for automated detection rates.

### Internal validity

RESOLVED for the recorded canonical state. Generation invariants, hash-linked reports, double-coded corrections, control rows, manifest-derived counts, CSV schemas, and independent verification records pass the audit and tests. Target-choice sensitivity and M09 recovery limitations remain documented inherent limitations.

### External validity

INHERENT LIMITATION. The corpus contains nine reference PDFs and the checker results are configuration-specific. The manuscript does not generalize the observed rates to all PDFs, tools, versions, or assistive technologies.

### Reproducibility

RESOLVED for the open-source portion and MITIGATED for proprietary evidence. Scratch regeneration is verify-only and isolated; final-freeze writing is separated; CI runs tests, scratch regeneration, analysis rebuild, and audit. Public sanitized evidence is hash-linked, while raw proprietary/AT evidence remains local by design.

### Artifact quality

RESOLVED. The source, tagged five-page PDF, generated fragments/macros, manifest, release notes, sensitivity artifacts, sanitized evidence ledger, and checksums are prepared for the v2 boundary. `paper-freeze-v1` remains untouched.

### Claims still too strong

RESOLVED in current-facing artifacts. Combined-scope percentages, Class-B automated rates, “validator-clean” language, informal “atomic bad PDF” terminology, and universal conformance implications were removed or narrowed. Any future revision should preserve these boundaries.

### Prior-art overlap

MITIGATED. The related-work language distinguishes benchmark precedent, PDF/UA testing resources, and this repository’s mutation-specific transformation/evidence contribution. A reviewer may still request a broader literature comparison; that is not a freeze blocker.

## Submission blockers

None identified for the local paper-freeze-v2 boundary. Venue-specific requirements remain outside this repository’s evidence scope, especially proprietary PDF/UA acceptance gates and any required human accessibility review.

## Issue classification

Issues 1–30 and checks A–H from `FINAL_CONSOLIDATION_AUDIT.md` are classified as follows:

| Items | Classification | Resolution |
|---|---|---|
| 1–2, 25–26, 29–30 | RESOLVED | v2 freeze procedure, release boundary, stale-state handling, and scope language are explicit; v1 remains immutable. |
| 3–12, 15, 18–20, 24, 28 | RESOLVED | Counts, manuscript framing, operator table, related work, AT wording, schemas, configurations, commands, terminology, controls, and layout were repaired and regenerated. |
| 13 | MITIGATED | Six-pair structural alternate-target sensitivity passes; native proprietary checker reruns are outside the secondary check. |
| 14 | INHERENT LIMITATION | Historical M09 evidence is unavailable; hypothetical replacement outcomes are not promoted. |
| 16–17, 27 | MITIGATED | Clean CI, sanitized public evidence, tagged-PDF checks, and explicit proprietary/venue boundaries are present; raw vendor evidence and venue acceptance remain external. |
| 21–23 | RESOLVED | Current-facing novelty and academic-language risks were narrowed and stale tool-catalog material was removed from the manuscript. |
| A–H | RESOLVED or INHERENT LIMITATION as documented above | Manifest-derived numbers, source clusters, exclusions, hashes, privacy boundaries, and claim scope pass; the remaining limitations are explicitly preserved rather than hidden. |

