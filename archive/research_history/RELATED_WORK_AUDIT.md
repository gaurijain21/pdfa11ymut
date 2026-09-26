# Related-work and prior-art audit

Verified 2026-09-17 against primary or official sources where available.

## Kumar, Padath, and Wang (ASSETS 2025)

The paper and its repository describe an expert-validated PDF accessibility benchmark with seven criteria. The construction includes controlled modifications in Adobe Acrobat Pro and a final set of 125 PDF documents derived from a larger scholarly corpus. This is materially closer prior art than a generic “expert-labeled dataset” description. PDFa11yMut must distinguish its explicit low-level structure transformations, mutation preconditions/invariants, validator-independent verification, and operator-level kill/survival analysis from their expert-validated and LLM-oriented evaluation framework.

Primary sources: [paper PDF](https://llwang.net/assets/pdf/2025_kumar_a11ybenchmark_assets.pdf), [DOI landing page](https://doi.org/10.1145/3663547.3746380), and [authors' dataset repository](https://github.com/Anukriti12/PDF-Accessibility-Benchmark). Exact operator-by-operator overlap is not independently verified here, so no priority or “first” claim is made.

## Ma11y

Ma11y is the closest direct methodological predecessor in web accessibility mutation testing. Its official ISSTA page reports 25 mutation operators, an automated oracle, and evaluation of web accessibility testing tools. PDFa11yMut should claim domain transfer and PDF structure/COS evidence only where the rebuilt artifact demonstrates it.

Source: [ISSTA 2024 paper page](https://2024.issta.org/details/issta-2024-papers/9/Ma11y-A-Mutation-Framework-for-Web-Accessibility-Testing).

## Android accessibility mutation testing

Android accessibility mutation testing is broader accessibility mutation precedent. It supports the idea of accessibility-specific mutation operators but does not establish PDF-specific novelty.

Source metadata requires an author-verified bibliographic record before submission; the current DOI record is not used to support a novelty claim.

## PDF Association Techniques and Matterhorn

The PDF Association Techniques provide atomic PASS/FAIL examples and procedures for recognized accessibility requirements. The Matterhorn Protocol 1.1 is a PDF/UA-1 conformance-testing model that distinguishes machine-verifiable and human checks. These are sources for operator motivation and classification, not evidence that the operators are novel.

Sources: [Techniques](https://pdfa.org/techniques-for-accessible-pdf/), [background and scope](https://pdfa.org/techniques-for-accessible-pdf-background/), and [Matterhorn Protocol 1.1 PDF](https://pdfa.org/download-area/publications/Matterhorn-Protocol-1-1.pdf).

## veraPDF corpus and Isartor

The veraPDF corpus contains atomic test files for PDF/A, PDF/UA, and PDF specification requirements and states that it complements Isartor. It is licensed CC BY 4.0 according to its repository. Isartor is important validator-testing prior art, but its official terms permit validation and structural analysis while prohibiting redistribution absent permission. Neither should be silently bundled into this artifact.

Sources: [veraPDF corpus](https://github.com/veraPDF/veraPDF-corpus), [PDF Association veraPDF test suite resource](https://pdfa.org/resource/verapdf-test-suite/), and [Isartor terms](https://pdfa.org/wp-content/uploads/2011/08/Isartor-Test-Suite4.pdf).

## Cross-validator comparison

The PDF Association's December 2025 comparative article reports a comparison of four PDF/UA validators on 155 reference files. This is directly relevant evidence that validator outputs differ, but it is an industry/practitioner report rather than a peer-reviewed mutation study. It should be cited as context, not treated as evidence for the novelty or scientific validity of mutation testing.

Source: [Understanding PDF/UA Validation Results: A Comparative Study Across Tools](https://pdfa.org/understanding-pdfua-validation-results-a-comparative-study-across-tools/).

| Work | Ground-truth unit | Mutation / PDF structure | Validator comparison | Controls and uncertainty | Relation to PDFa11yMut |
|---|---|---|---|---|---|
| Kumar et al., ASSETS 2025 | Expert-validated criteria and document labels | Systematically manipulated PDF variants; benchmark spans seven criteria | Automated and LLM-based approaches | Benchmark-level evaluation; not the same operator-paired COS kill/survival unit | Closest PDF benchmark; distinguish transformation-level evidence, not benchmark size or general accuracy |
| Ma11y, ISSTA 2024 | Expected accessibility violation created by an operator | 25 WCAG-derived web accessibility mutations | Evaluates web accessibility testing tools | Web-domain setup; not PDF/UA control design | Direct mutation-testing predecessor; PDF/COS domain transfer is not novelty by itself |
| PDF Association, 2025 comparative article | 155 reference files | No mutation framework described in the article | Four PDF/UA validators | Comparative descriptive study; practitioner/industry publication | Establishes practical validator-comparison context, not a peer-reviewed mutation benchmark |
| PDF Association Techniques / Matterhorn | Normative or protocol test conditions | Atomic PDF accessibility conditions and machine/human-check boundary | Conformance-oriented checks | Not a mutation-testing experiment | Motivates failure classes and capability boundaries, not operator novelty |
| PDFa11yMut (this project) | Paired source and mutant, with intended structural delta and visual invariants | Ten PDF structure/semantics operators, applied where preconditions hold | PAC, Acrobat, and veraPDF evidence; scope differs by validator | 18 no-op/benign controls, source-clustered corpus, formal independent double-coding still pending | Narrow contribution is the paired, hash-linked mutation/evidence workflow; detection results remain conditional until human coding closes |

This is a scoped comparison, not an exhaustive systematic literature review. Do not claim “first,” exhaustive coverage, general PDF accessibility accuracy, or superiority over the benchmark or commercial validators. Before submission, verify the final bibliographic metadata and access date for the PDF Association article and search citation indexes for intervening PDF-specific mutation work.

## Novelty disposition

The broad historical statement that PDF accessibility has no equivalent mutation benchmark is removed from the active paper. The defensible provisional claim is that this repository implements a paired, hash-linked, structure-level mutation and verification workflow for PDF accessibility validator evaluation. “First” is not used until an exhaustive literature audit supports it.
