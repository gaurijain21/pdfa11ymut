# PAC AI aggregate-count adjudication

**Decision:** `REJECTED_AS_INSUFFICIENT_EVIDENCE`

**Scope:** 34 active B08 mutant rows, each compared with its exact B07 PAC AI golden baseline. The comparison uses the three preserved native PAC semantic panels: Classification of the elements (C), Unrecognized structural elements (U), and Missing structural elements (M). Each tuple is `passed/warning/error`; `-` is the native visible dash.

**Observed configuration and limitation:** PAC version `26.1.0.0`; 8 B07 golden captures and 34 B08 mutant captures; 168 raw screenshots in the preserved semantic capture set. That preserved package exposes aggregate counts only. A fresh native one-golden/one-mutant pilot additionally exposed element-level finding text, scores, and page visualization, but the tested build still exposes no supported complete semantic export/API or AI model/build identifier for a reproducible full-cohort run.

## Final blocker-closure pilot audit

The required one-golden/one-mutant pilot was executed in native PAC before authorizing any full PAC AI rerun:

- PAC executable: PAC 26.1.0.0 (installation path intentionally omitted for portability).
- PAC version/build: `26.1.0.0`.
- Windows: Windows 10 Home 25H2, build `26200.9457`, x64.
- AI enablement: visibly active in the native PAC AI tab; the expected registry path was not present, so enablement is not inferred from a registry value.
- Profile: `PDF/UA formal/traditional check with PAC AI semantic analysis`.
- Language/region: `en-US` / `US`.
- Remediation and PDF modification: disabled; no tested PDF was modified.

Pilot artifacts were opened from the exact queue paths and their displayed filenames and SHA-256 values were verified:

| Role | Artifact | SHA-256 |
|---|---|---|
| B07 golden | `corpus/golden/PDFUA-Ref-2-01_Magazine-danish.pdf` | `AEF89AF13C9C94FC4F4E1A8C5872450CC4C8FFF7DE544D8ADA6A0912425AA434` |
| B08 mutant | `corpus/mutants/PDFUA-Ref-2-01_Magazine-danish-M01.pdf` | `A52E75193364438A1701F76C986FC047EE3B98DD691EC662D2C1D380C5D2DF` |

Pilot result: `FAILED_SEMANTIC_EVIDENCE_GATE`. The three PAC AI panels—`Classification of the elements`, `Unrecognized structural elements`, and `Missing structural elements`—exposed aggregate totals, while `Results in Detail` exposed four element-level findings with text, scores, and page visualization for both the exact golden and M01 mutant. No supported complete semantic export/API or AI model/build identifier was available. The native PDF report likewise contained only the formal PDF/UA summary.

Because the pilot did not provide a supported complete export/API, the element-level observation cannot be reproduced or generalized to the full cohort. The exact M01 pilot showed the same four findings for golden and mutant and therefore supports a pilot-level `Missed` interpretation for that mutation, but it does not establish a canonical result for any of the 34 full-cohort rows. The full 8-golden/34-mutant rerun was not started.

The canonical schema has no explicit blocked/evidence-unavailable completion disposition. Consequently, all 34 rows with artifact-specific native capture remain `AI_AMBIGUOUS` with `REVIEW_REQUIRED`; no full-cohort PAC AI detection or non-detection is inferred because the complete semantic export/API gate remains unmet. The PAC AI phase remains unresolved future work because its preserved package lacks a supported complete export/API. The current formal study and nine-case AT pilot are complete independently of that future-work item.

Required external dependency to continue: a PAC build or supported interface that exposes semantic finding identity or text and provides a reproducible complete semantic export/API. If such a build/interface becomes available, the study must first repeat and pass this one-B07-golden/one-B08-mutant pilot, including filepath/SHA verification and reproducible semantic capture, before any full rerun.

No additional AT execution is authorized as part of the PAC AI continuation while this dependency is absent; the separately completed nine-case NVDA pilot remains valid under the AT protocol. G09 baseline-fail descendants remain excluded. Historical G02-M04 is permanently excluded; the current local M04 artifacts are separate and do not receive PAC AI conclusions from this aggregate-only experiment.

## Adjudication rule

A count delta was eligible only if it was deterministic, uniquely attributable to the intended mutation, distinguishable from baseline-carried or collateral findings, and sufficient to establish a PAC AI taxonomy value without relying on mutation labels, expected outcomes, or formal PDF/UA results. No row met all of those requirements. A changed count can indicate only that an aggregate total changed; it cannot identify which semantic finding changed or whether the change is intended, baseline-carried, unrelated, or collateral.

## Pairwise comparison

Every row below was matched to the listed `source_golden` and compared using the preserved manifest observations. `AI_AMBIGUOUS / REVIEW_REQUIRED` is retained for every row; no count delta is treated as a detection or non-detection.

| B08 mutant | Exact B07 golden | Golden C / U / M | Mutant C / U / M | Decision |
|---|---|---|---|---|
| PDFUA-Ref-2-01_Magazine-danish-M01 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 460/-/- ; 493/-/- ; 477/4/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-02_Invoice-M01 | PDFUA-Ref-2-02_Invoice | 9/-/- ; 9/1/- ; 14/1/- | 9/-/- ; 9/1/- ; 14/1/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-03_AcademicAbstract-M01 | PDFUA-Ref-2-03_AcademicAbstract | 30/-/- ; 33/-/- ; 40/-/- | 30/-/- ; 33/-/- ; 40/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-04_Presentation-M01 | PDFUA-Ref-2-04_Presentation | 34/2/- ; 37/-/- ; 32/-/- | 34/2/- ; 37/-/- ; 32/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-05_BookChapter-german-M01 | PDFUA-Ref-2-05_BookChapter-german | 241/1/- ; 245/-/- ; 253/-/- | 241/1/- ; 245/-/- ; 253/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-06_Brochure-M01 | PDFUA-Ref-2-06_Brochure | 27/1/- ; 30/-/- ; 29/-/- | 48/1/- ; 51/-/- ; 50/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-08_BookChapter-M01 | PDFUA-Ref-2-08_BookChapter | 252/20/- ; 286/180/- ; 225/180/- | 252/20/- ; 286/180/- ; 225/180/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-10_Form-M01 | PDFUA-Ref-2-10_Form | 6/-/- ; 7/-/- ; 15/1/- | 6/-/- ; 7/-/- ; 15/1/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-01_Magazine-danish-M02 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 459/-/- ; 491/-/- ; 476/5/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-02_Invoice-M02 | PDFUA-Ref-2-02_Invoice | 9/-/- ; 9/1/- ; 14/1/- | -/-/- ; -/-/- ; 3/12/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-03_AcademicAbstract-M02 | PDFUA-Ref-2-03_AcademicAbstract | 30/-/- ; 33/-/- ; 40/-/- | 30/-/- ; 32/-/- ; 40/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-04_Presentation-M02 | PDFUA-Ref-2-04_Presentation | 34/2/- ; 37/-/- ; 32/-/- | 29/2/- ; 31/-/- ; 26/6/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-05_BookChapter-german-M02 | PDFUA-Ref-2-05_BookChapter-german | 241/1/- ; 245/-/- ; 253/-/- | -/-/- ; -/-/- ; 20/233/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-06_Brochure-M02 | PDFUA-Ref-2-06_Brochure | 27/1/- ; 30/-/- ; 29/-/- | 48/-/- ; 50/-/- ; 49/1/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-08_BookChapter-M02 | PDFUA-Ref-2-08_BookChapter | 252/20/- ; 286/180/- ; 225/180/- | 245/16/- ; 267/178/- ; 224/181/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-10_Form-M02 | PDFUA-Ref-2-10_Form | 6/-/- ; 7/-/- ; 15/1/- | -/-/- ; -/-/- ; 8/8/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-01_Magazine-danish-M03 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 460/-/- ; 493/-/- ; 477/4/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-01_Magazine-danish-M04 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 460/-/- ; 493/-/- ; 477/4/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-03_AcademicAbstract-M04 | PDFUA-Ref-2-03_AcademicAbstract | 30/-/- ; 33/-/- ; 40/-/- | 30/-/- ; 33/-/- ; 40/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-04_Presentation-M04 | PDFUA-Ref-2-04_Presentation | 34/2/- ; 37/-/- ; 32/-/- | 34/2/- ; 37/-/- ; 32/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-05_BookChapter-german-M04 | PDFUA-Ref-2-05_BookChapter-german | 241/1/- ; 245/-/- ; 253/-/- | 241/1/- ; 245/-/- ; 253/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-06_Brochure-M04 | PDFUA-Ref-2-06_Brochure | 27/1/- ; 30/-/- ; 29/-/- | 48/1/- ; 51/-/- ; 50/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-08_BookChapter-M04 | PDFUA-Ref-2-08_BookChapter | 252/20/- ; 286/180/- ; 225/180/- | 252/20/- ; 286/180/- ; 225/180/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-01_Magazine-danish-M05 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 460/-/- ; 493/-/- ; 477/4/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-03_AcademicAbstract-M05 | PDFUA-Ref-2-03_AcademicAbstract | 30/-/- ; 33/-/- ; 40/-/- | 30/-/- ; 33/-/- ; 40/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-04_Presentation-M05 | PDFUA-Ref-2-04_Presentation | 34/2/- ; 37/-/- ; 32/-/- | 34/2/- ; 37/-/- ; 32/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-05_BookChapter-german-M05 | PDFUA-Ref-2-05_BookChapter-german | 241/1/- ; 245/-/- ; 253/-/- | 241/1/- ; 245/-/- ; 253/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-06_Brochure-M05 | PDFUA-Ref-2-06_Brochure | 27/1/- ; 30/-/- ; 29/-/- | 48/1/- ; 51/-/- ; 50/-/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-08_BookChapter-M05 | PDFUA-Ref-2-08_BookChapter | 252/20/- ; 286/180/- ; 225/180/- | 250/20/- ; 284/181/- ; 224/181/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-01_Magazine-danish-M06 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 460/-/- ; 493/-/- ; 477/4/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-01_Magazine-danish-M07 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 460/-/- ; 493/-/- ; 477/4/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-01_Magazine-danish-M08 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 460/-/- ; 493/-/- ; 477/4/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-01_Magazine-danish-M09 | PDFUA-Ref-2-01_Magazine-danish | 460/-/- ; 493/-/- ; 477/4/- | 460/-/- ; 492/-/- ; 477/4/- | AI_AMBIGUOUS |
| PDFUA-Ref-2-02_Invoice-M10 | PDFUA-Ref-2-02_Invoice | 9/-/- ; 9/1/- ; 14/1/- | 10/-/- ; 10/1/- ; 14/1/- | AI_AMBIGUOUS |

## Result and next action

- Rows classified from aggregate counts: **0/34**.
- Rows retained as `AI_AMBIGUOUS`: **34/34**.
- Rows retained as `REVIEW_REQUIRED`: **34/34**.
- Aggregate counts accepted as mutation-specific evidence: **No**.
- Tested PDFs modified: **No**.
- PAC AI phase: **blocked by a documented tool limitation**, not by a missing screenshot or an unreviewed count delta.

The exact next action is to obtain a PAC build or supported PAC interface that exposes semantic finding identity/text and a complete semantic export/API. If that capability cannot be obtained, the PAC AI semantic phase remains unresolved and must not be converted into detections or non-detections.

AT execution was previously gated during this PAC-AI adjudication phase. A subsequent nine-case NVDA pilot was recorded separately under the AT protocol; that pilot does not alter the aggregate-only PAC-AI conclusion.

## Final pilot closure

The final native PAC pilot has now been closed with result `FAILED_SEMANTIC_EVIDENCE_GATE` for PAC `26.1.0.0`. Golden and mutant filepath/SHA-256 verification passed. The tested build exposed four element-level finding texts/scores and page visualization for the matched pair, but no supported complete semantic export/API for a reproducible full-cohort rerun.

PAC `26.1.0.0` is therefore unable to provide reproducible complete semantic evidence for this study. The frozen 8-golden/34-mutant rerun was not started. All 34 artifact-backed classifications remain `AI_AMBIGUOUS` and `REVIEW_REQUIRED`; no validator evidence, queue status, tested PDF, or formal analysis conclusion was changed. The native pilot and metadata record were added as separate evidence, and generated analysis was rebuilt to reflect the export/API gate.

The project cannot make further in-repository progress until the external continuation gate is satisfied: a different PAC build or supported interface must expose semantic finding identity or text with reproducible export/API. A one-golden/one-mutant pilot must pass before any full rerun.
