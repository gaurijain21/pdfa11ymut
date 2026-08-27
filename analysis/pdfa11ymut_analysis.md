# PDFa11yMut Experimental Detection Analysis

## Scope And Provenance

- Corpus scope: 5 golden PDFs, 23 generated and independently verified mutants, 2 non-generated/N/A cases.
- Mutation verification is independent from validator detection: every generated mutant was programmatically confirmed as generated, parseable, page-count preserving, mutation-verified, and visually unchanged for the checked visual-difference signal.
- PAC evidence is from the recorded PAC run in the prior research conversation: all goldens passed; G01/G02/G03/G04-M03 failed Structure Elements; all other generated mutants passed.
- Acrobat evidence is from the recorded Acrobat Accessibility Checker report/results in the prior research conversation: all five goldens had 29 passed, 0 failed, 2 manual checks, and 1 skipped; G01/G02/G03/G04-M03 and G02-M04 had automated failures; all other generated mutants had 0 automated failures.
- veraPDF evidence is from `vera_evaluation.docx`: veraPDF 1.30.2, GreenField parser, PDF/UA-1 validation profile with 106 rules; all five goldens passed.

Important interpretation rule: a validator `Missed` result means no relevant automated failure was reported for a mutant whose intended defect was independently verified. It does not mean the PDF is accessible, and it does not measure full checker accuracy.

## Overall Detection Rates

| Validator | Detected | Missed | Total generated/verified | Detection rate |
|---|---:|---:|---:|---:|
| PAC | 4 | 19 | 23 | 17.4% |
| Acrobat | 5 | 18 | 23 | 21.7% |
| veraPDF | 5 | 18 | 23 | 21.7% |

## Per-Operator Detection Rates

| Mutation | Operator | Validator | Detected | Total | Detection rate |
|---|---|---|---:|---:|---:|
| M01 | Structural reading-order swap | PAC | 0 | 5 | 0.0% |
| M01 | Structural reading-order swap | Acrobat | 0 | 5 | 0.0% |
| M01 | Structural reading-order swap | veraPDF | 0 | 5 | 0.0% |
| M02 | Omit visible content from tag structure | PAC | 0 | 5 | 0.0% |
| M02 | Omit visible content from tag structure | Acrobat | 0 | 5 | 0.0% |
| M02 | Omit visible content from tag structure | veraPDF | 0 | 5 | 0.0% |
| M03 | Incorrect heading level / skipped hierarchy | PAC | 4 | 4 | 100.0% |
| M03 | Incorrect heading level / skipped hierarchy | Acrobat | 4 | 4 | 100.0% |
| M03 | Incorrect heading level / skipped hierarchy | veraPDF | 4 | 4 | 100.0% |
| M04 | Wrong marked-content association | PAC | 0 | 5 | 0.0% |
| M04 | Wrong marked-content association | Acrobat | 1 | 5 | 20.0% |
| M04 | Wrong marked-content association | veraPDF | 1 | 5 | 20.0% |
| M05 | Internal MCID sequence reversal | PAC | 0 | 4 | 0.0% |
| M05 | Internal MCID sequence reversal | Acrobat | 0 | 4 | 0.0% |
| M05 | Internal MCID sequence reversal | veraPDF | 0 | 4 | 0.0% |

## Validator Agreement

| Validator pair | Agree | Disagree | Total | Agreement rate | Disagreement cases |
|---|---:|---:|---:|---:|---|
| PAC vs Acrobat | 22 | 1 | 23 | 95.7% | G02_M04 |
| PAC vs veraPDF | 22 | 1 | 23 | 95.7% | G02_M04 |
| Acrobat vs veraPDF | 23 | 0 | 23 | 100.0% | None |

| Three-validator pattern | Count | Share |
|---|---:|---:|
| Detected/Detected/Detected | 4 | 17.4% |
| Missed/Detected/Detected | 1 | 4.3% |
| Missed/Missed/Missed | 18 | 78.3% |

## Final Detection Matrix

| Mutant | Operator | PAC | Acrobat | veraPDF | Note |
|---|---|---|---|---|---|
| G01_M01 | M01 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G01_M02 | M02 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G01_M03 | M03 | Detected | Detected | Detected | Detected consistently by all three validators. |
| G01_M04 | M04 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G01_M05 | M05 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G02_M01 | M01 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G02_M02 | M02 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G02_M03 | M03 | Detected | Detected | Detected | Detected consistently by all three validators. |
| G02_M04 | M04 | Missed | Detected | Detected | Only validator disagreement case: PAC missed; Acrobat and veraPDF detected list-structure failures. |
| G02_M05 | M05 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G03_M01 | M01 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G03_M02 | M02 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G03_M03 | M03 | Detected | Detected | Detected | Detected consistently by all three validators. |
| G03_M04 | M04 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G03_M05 | M05 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G04_M01 | M01 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G04_M02 | M02 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G04_M03 | M03 | Detected | Detected | Detected | Detected consistently by all three validators. |
| G04_M04 | M04 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G04_M05 | M05 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G05_M01 | M01 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G05_M02 | M02 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G05_M03 | M03 | N/A | N/A | N/A | Not generated: no suitable heading-hierarchy target in G05. |
| G05_M04 | M04 | Missed | Missed | Missed | Survived all automated validators despite independent mutation verification. |
| G05_M05 | M05 | N/A | N/A | N/A | Not generated: no suitable multi-MCID target in G05. |

## Defensible Research Questions

RQ1. To what extent do automated PDF accessibility validators detect independently verified structure-only accessibility mutations in otherwise validator-clean PDF/UA-oriented documents?

RQ2. Are detection outcomes concentrated in particular mutation operators, such as heading-hierarchy violations, rather than distributed evenly across reading-order, omission, list/table association, and MCID-order defects?

RQ3. How much do commonly used validators agree or disagree on the same controlled PDF accessibility mutants, and which mutation cases explain disagreement?

RQ4. What does mutation-based evaluation reveal about the boundary between machine-checkable conformance failures and verified accessibility-relevant defects that survive automated checking?

## Results And Discussion Findings

1. The golden baseline is clean for the three evaluated validators. This supports attributing later automated failures to the injected mutations rather than to pre-existing baseline defects.

2. Detection is highly operator-specific. All three validators detected every generated M03 heading-hierarchy mutant (4/4). None detected M01, M02, or M05. For M04, Acrobat and veraPDF detected only G02-M04, while PAC detected none.

3. Overall automated detection is limited for this controlled mutant set: PAC detected 4/23 (17.4%), while Acrobat and veraPDF each detected 5/23 (21.7%). These are mutation-detection rates for this benchmark, not general accessibility accuracy rates.

4. Acrobat and veraPDF agreed on every generated mutant at the detected/missed level. PAC agreed with them on 22/23 mutants and differed only on G02-M04.

5. G02-M04 is the strongest cross-validator disagreement case. The mutation was independently verified as a marked-content association swap in a list; Acrobat reported two list failures, veraPDF reported four ISO 14289-1 Clause 7.2 list failures, and PAC reported no automated failure.

6. Surviving mutants should not be described as false negatives unless the paper carefully defines the target property. A safer phrasing is that these verified mutants survived the validators' automated checks under the tested settings.
