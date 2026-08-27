# PDFa11yMut: Mutation-Based Evaluation of Automated PDF Accessibility Validators

## Abstract

Automated validators are widely used to assess PDF accessibility, but their detection boundaries are difficult to measure without controlled ground truth. A validator-clean PDF may be free of the implemented machine-checkable failures, or it may contain accessibility-relevant structural defects that the validator does not detect. This paper introduces PDFa11yMut, a controlled mutation-based benchmark for evaluating automated PDF accessibility validators against independently verified PDF structure defects.

We generated 23 verified mutants from five validator-clean golden PDFs using five mutation operators targeting reading order, omitted assistive structure, heading hierarchy, marked-content association, and internal marked-content sequence. Each generated mutant was independently verified at the PDF structure level and checked for parseability, page-count preservation, and absence of detected visual differences. We then evaluated the mutants with three validators: PAC, Adobe Acrobat Accessibility Checker, and veraPDF, with veraPDF run using the PDF/UA-1 profile.

The validators detected a small and highly operator-specific subset of the verified mutants. PAC detected 4/23 mutants (17.4%), while Acrobat and veraPDF each detected 5/23 mutants (21.7%). All three validators detected every generated heading-hierarchy mutant (M03, 4/4). None detected the reading-order swap, omitted-structure, or internal MCID-order mutants. Acrobat and veraPDF also detected one marked-content association mutant, G02-M04, that PAC missed. The practical implication is that a validator-clean result can coexist with verified, visually invisible structure defects that affect the assistive representation of a PDF. These results should not be interpreted as general accessibility accuracy scores. Instead, they show that controlled mutation testing can expose the boundary between machine-checkable conformance failures and independently verified accessibility-relevant structural defects that survive automated checking.

## 1. Introduction

PDF accessibility validators are software systems that check whether document structures satisfy accessibility-related requirements. Their output is often treated as evidence that a PDF is accessible or inaccessible, but this interpretation is only as strong as the checker rules being exercised. This matters because PDFs remain a widely used global format for education, research, government, healthcare, legal records, financial documents, and public services. When a visually correct PDF exposes headings, lists, tables, or reading order incorrectly to assistive technologies, the barrier is not visible on the page but can still affect access to essential information. Some of these defects may fall outside a validator's automated checks.

This creates a benchmark problem. A validator-clean result may mean that the PDF is structurally sound with respect to the implemented checks. It may also mean that the PDF contains an accessibility-relevant defect outside the validator's automated detection boundary. Without controlled ground truth, it is difficult to tell whether a checker is detecting a defect, missing it, or simply not designed to evaluate that property.

Mutation testing provides a way to make this boundary measurable. Rather than relying only on naturally occurring PDFs with ambiguous defects, a mutation-based benchmark starts from validator-clean golden documents, injects controlled defects, verifies those defects independently, and measures whether validators detect them. Ma11y applies this idea to web accessibility testing tools [Tafreshipour2024], and GateTruth uses mutation testing as a benchmark-auditing method in hardware design evaluation [Bhadra2026]. PDF accessibility lacks an equivalent mutation benchmark for automated validators.

This paper presents PDFa11yMut, a controlled mutation benchmark for automated PDF accessibility validators. PDFa11yMut starts from validator-clean golden PDFs, injects structure-level PDF accessibility mutations, verifies the intended structural change independently from validator output, and then measures whether validators report a relevant automated failure. This design turns an otherwise vague concern about checker limitations into measurable evidence: for each injected defect, the benchmark records whether the defect is present, whether the page still renders as expected, and whether the validator reports a corresponding failure. A surviving mutant is therefore interpreted carefully: not as proof that the PDF is accessible, and not as proof that a validator is generally inaccurate, but as evidence that a verified mutation survived the validator's automated checks under the tested configuration.

We instantiate this approach with five mutation operators applied to five golden PDFs, producing 23 generated and independently verified mutants. We evaluate these mutants with PAC, Adobe Acrobat Accessibility Checker, and veraPDF. The experiment asks whether validator detection is broad across mutation types or concentrated in particular machine-checkable structures, and whether different validators agree on the same controlled defects.

The paper makes the following contributions for software testing, benchmark construction, and accessibility validation:

1. A controlled mutation methodology for PDF accessibility structures.
2. Five mutation operators targeting accessibility-relevant PDF structure defects.
3. A verified mutant set derived from five golden PDFs.
4. A three-validator detection matrix for PAC, Adobe Acrobat Accessibility Checker, and veraPDF.
5. An analysis showing operator-specific detection behavior and one cross-validator disagreement case.

## 2. Research Questions

RQ1. To what extent do automated PDF accessibility validators detect independently verified structure-only accessibility mutations in otherwise validator-clean PDF/UA-oriented documents?

RQ2. Are detection outcomes concentrated in particular mutation operators rather than distributed evenly across reading-order, omission, list/table association, and MCID-order defects?

RQ3. How much do commonly used validators agree or disagree on the same controlled PDF accessibility mutants, and which mutation cases explain disagreement?

RQ4. What does mutation-based evaluation reveal about the boundary between machine-checkable conformance failures and verified accessibility-relevant defects that survive automated checking?

## 3. Background and Related Work

### 3.1 PDF Accessibility Evaluation

Recent work has shown that PDF accessibility remains a persistent problem in scholarly communication. Kumar and Wang studied approximately 20,000 scholarly PDFs published between 2014 and 2023 and found low compliance across measured accessibility criteria, including a reported decline after 2019 [KumarWang2024]. Their work is important for PDFa11yMut because it demonstrates the scale of the problem and the practical role of automated accessibility checking in large document collections. At the same time, their findings caution against treating automated checker output as a complete account of user-facing accessibility. They report that automated checks are useful for large-scale assessment but can miss important accessibility qualities, including the usefulness of alternative text and the experience of screen-reader users.

This recent work builds on earlier studies of scholarly PDF accessibility. Brady, Zhong, and Bigham analyzed conference proceedings from CHI, ASSETS, and W4A and documented accessibility barriers in research-paper PDFs [Brady2015]. Nganji later examined PDFs from disability-related journals and found low rates of tagging and alternative text despite the availability of HTML alternatives [Nganji2018]. Ribera, Pozzobon, and Sayago reported a case study on producing accessible proceedings for DSAI 2016, emphasizing the labor and workflow coordination required to produce accessible PDFs [Ribera2020]. Together, these studies show that PDF accessibility failures are persistent across venues and that tool support remains central to scalable evaluation and remediation.

Kumar, Padath, and Wang later proposed a benchmark for PDF accessibility evaluation that includes expert-validated annotations across seven criteria, including alternative text quality, logical reading order, semantic tagging, table structure, functional hyperlinks, color contrast, and font readability [KumarPadathWang2025]. Their benchmark evaluates both automated and LLM-based approaches and emphasizes that PDF accessibility assessment requires more nuanced labels than a simple binary pass/fail result. This is the closest prior PDF-specific benchmark work to PDFa11yMut. The difference is methodological: their benchmark uses expert-labeled documents and criterion-level annotations, while PDFa11yMut uses controlled structural mutations introduced into validator-clean golden PDFs. These approaches are complementary. Expert-labeled datasets measure evaluator performance against human judgments, while mutation benchmarks isolate whether a checker detects specific injected defects.

Work on PDF remediation tools also motivates the need for better evaluator diagnostics. Paliwal et al. present FormA11y, a tool for remediating PDF forms for accessibility [Paliwal2024]. Remediation work highlights the complexity of repairing accessibility defects once they exist. PDFa11yMut addresses an adjacent problem: before remediation, tool builders and researchers need benchmark data showing which classes of PDF structure defects automated evaluators can detect reliably.

### 3.2 PDF/UA, Matterhorn, and Machine-Checkable Criteria

PDF/UA provides technical requirements for accessible PDF files, while the Matterhorn Protocol operationalizes PDF/UA-1 conformance testing as a set of checkpoints and failure conditions [PDFAssociation2021]. This distinction matters because the protocol explicitly separates checks that can be determined by software from checks that require human judgment. The PDF Association describes the Matterhorn Protocol as a list of possible ways to fail PDF/UA-1, and veraPDF's documentation similarly notes that, for PDF/UA, veraPDF performs only machine-verifiable checks [veraPDFValidation].

This machine/human boundary is central to PDFa11yMut. Some properties, such as malformed heading hierarchy or invalid list containment, are well suited to rule-based validation. Others, such as meaningful reading order, the usefulness of alternative text, or whether a structural association matches the author's intended semantics, may require contextual reasoning or human judgment. Adobe's Acrobat checker documentation also reflects this hybrid model: it describes checks that pass or fail, automatic fixes for some checks, and instructions for items requiring manual fixes [AdobeAccessibility].

PDFa11yMut does not assume that a missed mutant proves that a validator is incorrect. Instead, it records whether a verified accessibility-relevant structural mutation survives the validator's automated checks. This framing follows the same caution found in recent PDF accessibility evaluation work: automated checker output is useful evidence, but it should not be treated as a complete accessibility oracle.

### 3.3 Accessibility Mutation Testing

Mutation testing has recently been applied to accessibility evaluation outside the PDF domain. Tafreshipour et al. introduced Ma11y, a mutation framework for web accessibility testing [Tafreshipour2024]. Ma11y defines 25 mutation operators that intentionally violate accessibility principles and uses an automated oracle to determine whether web accessibility testing tools detect the injected mutants. Their evaluation on real-world websites found that current tools missed nearly half of the injected accessibility bugs.

Ma11y is the most direct methodological predecessor to PDFa11yMut. Both projects use mutation analysis to evaluate accessibility testing tools against controlled defects rather than relying only on naturally occurring accessibility issues. PDFa11yMut differs in domain and technical substrate. Ma11y mutates web content, where accessibility is typically represented through HTML, ARIA, CSS, and DOM-level properties. PDFa11yMut mutates PDF structure trees, marked-content identifiers, heading tags, list/table structures, and marked-content associations. This difference matters because PDF accessibility defects can be visually invisible while still changing the assistive representation exposed through the PDF tag tree.

Accessibility mutation testing has also been explored for mobile applications. Silva, Vergilio, and Endo proposed mutation testing for Android accessibility, defining operators derived from accessibility faults and using mutants to assess and improve test suites [Silva2022]. This work reinforces the broader idea that accessibility-specific mutation operators can reveal weaknesses in existing testing workflows. PDFa11yMut extends that principle to static document accessibility and PDF/UA-oriented validation.

### 3.4 Mutation Testing for Benchmark Auditing

GateTruth applies mutation testing to a different domain: auditing register-transfer-level design benchmarks for large language models [Bhadra2026]. It is relevant here only as a methodological analogy. Its core claim is that an evaluator should be tested against controlled, meaningful defects before its pass rates are treated as strong evidence. PDFa11yMut adapts that logic to PDF accessibility validators: a validator-clean result is not sufficient evidence that a checker would detect accessibility-relevant structural defects unless the checker is tested against verified mutants.

### 3.5 Gap Addressed by PDFa11yMut

Prior PDF accessibility benchmarks provide expert-labeled datasets and criteria-level evaluation frameworks. Prior accessibility mutation frameworks show that mutation analysis can reveal gaps in web and mobile accessibility testing. GateTruth shows that mutation testing can audit benchmark rigor more generally. What remains missing is a PDF-specific mutation benchmark for studying how automated PDF accessibility validators respond to controlled structural defects.

PDFa11yMut fills this gap by generating independently verified PDF structure mutants from validator-clean golden PDFs and evaluating them across three validators. Its contribution is not a complete taxonomy of PDF accessibility defects. Rather, it is a reproducible method for measuring validator sensitivity to specific PDF structure mutations.

## 4. Methodology

### 4.1 Corpus

The experiment began with five golden PDFs, labeled G01 through G05. These PDFs served as the baseline corpus from which mutants were generated. Before interpreting mutation results, the golden PDFs were checked with the evaluated validators to establish that validator-reported failures in mutants were not inherited from the baseline documents.

For veraPDF, all five golden PDFs passed the PDF/UA-1 validation profile. The veraPDF report identifies version 1.30.2, the GreenField parser, and a PDF/UA-1 validation profile containing 106 rules. The recorded Acrobat baseline reported 29 passed checks, 0 failed checks, 2 manual checks, and 1 skipped check for each golden PDF. The two Acrobat manual-check prompts were reviewed manually and did not identify baseline defects. The recorded PAC baseline also reported the golden PDFs as passing.

The two Acrobat manual-check items were not treated as automated failures. They indicate checks requiring human judgment rather than validator-detected defects, so they were documented separately from the automated mutation-detection outcomes.

### 4.2 Mutation Operators

PDFa11yMut uses five mutation operators. Each operator targets the assistive representation of the PDF while preserving visible content where possible.

Table 1 summarizes the mutation operators.

| ID | Operator | Structural change | Intended accessibility effect |
|---|---|---|---|
| M01 | Structural reading-order swap | Swap adjacent structural children, such as list items or table rows. | Assistive technology encounters content in a different order from the intended visible order. |
| M02 | Omission from assistive structure | Remove a meaningful visible element from the structure tree while leaving page content visible. | A visible heading or content item is absent from the assistive representation. |
| M03 | Incorrect heading level | Change a heading tag to an inappropriate lower level. | The document exposes a skipped or misleading heading hierarchy. |
| M04 | Wrong marked-content association | Preserve structural sibling order while swapping underlying marked-content associations. | A tag position points to the wrong visible content. |
| M05 | Internal MCID sequence reversal | Reverse the internal marked-content sequence inside one structural element. | A list item or paragraph exposes its internal chunks in the wrong order. |

These operators do not claim to exhaust PDF accessibility defects. They are a focused set selected to target distinct structure-level failure modes that are relevant to assistive representation while often preserving the visible rendering.

The practical impact of each operator comes from the difference between the visual page and the structure exposed to assistive technologies. M01, structural reading-order swap, models a case where the page looks correct but the assistive reading sequence is wrong. For example, if two adjacent list items are visually ordered as "submit the form" and then "wait for confirmation," a swapped structure tree may cause a screen reader or extraction tool to present the confirmation step before the submission step. M02, omission from assistive structure, models visible content that remains on the page but is absent from the tagged representation; for example, a visible section heading may be skipped by screen-reader navigation. M03, incorrect heading level, models a misleading document outline, such as jumping from H1 to H3 without an intervening H2. M04, wrong marked-content association, models a tag that occupies the expected structural position but points to the wrong visible content, such as a list item tag associated with its sibling's text. M05, internal MCID sequence reversal, models cases where a single structural element exists but its internal content chunks are exposed in the wrong order, which can change the meaning of a sentence, list item, or table cell without changing the visual page.

### 4.3 Mutant Generation and N/A Cases

Figure 1 summarizes the experimental pipeline.

![Figure 1. PDFa11yMut experimental pipeline](figures/figure1_pipeline.svg)

The experimental workflow was:

1. select a suitable target object in a golden PDF,
2. apply the mutation operator to the PDF structure,
3. parse the resulting PDF,
4. verify that page count was unchanged,
5. compare the targeted structure before and after mutation,
6. check that the intended mutation was present,
7. check for unexpected structural changes and detected visual differences,
8. run each validator on the verified mutant,
9. code the validator result as Detected, Missed, or N/A.

The five operators were applied where suitable targets existed in each golden PDF. This produced 23 generated mutants. Two potential cases were not generated and are preserved as N/A rather than counted as missed or detected:

G05-M03 was not generated because G05 did not contain a suitable heading-hierarchy target for the M03 operator.

G05-M05 was not generated because G05 did not contain a suitable multi-MCID target for the M05 operator.

Preserving these N/A cases avoids inflating the denominator with mutants that were not generated.

### 4.4 Independent Mutation Verification

Validator detection was separated from mutation verification. A mutant was included in the detection denominator only if the mutation generation and verification pipeline confirmed that the intended structural change was present.

For every generated mutant, the verification data recorded:

1. generation success,
2. PDF parseability,
3. unchanged page count,
4. mutation verification,
5. no unexpected structural changes,
6. no detected visual difference.

This distinction is central to the experiment. A validator result of "missed" means that the validator did not report a relevant automated failure for a mutant whose intended defect was independently verified. It does not mean the PDF is accessible, and it does not measure the validator's general accuracy.

### 4.5 Validators

The experiment evaluated three validators:

PAC. PAC was used as a dedicated PDF accessibility checker. The recorded PAC evidence identifies PAC 26.1. The recorded PAC experiment found that all golden PDFs passed. Among mutants, PAC reported Structure Elements failures for G01-M03, G02-M03, G03-M03, and G04-M03. All other generated mutants were recorded as passing.

Adobe Acrobat Accessibility Checker. Acrobat was used as a widely available commercial PDF accessibility checker. The recorded Acrobat results found no automated failures in the five golden PDFs. Among mutants, Acrobat detected G01-M03, G02-M03, G03-M03, G04-M03, and G02-M04. For the M03 mutants, Acrobat reported heading nesting failures. For G02-M04, Acrobat reported list-related failures. The available experimental notes preserve the Acrobat rule outcomes; the exact Acrobat build is recorded as a reporting limitation.

veraPDF. veraPDF was used as an open-source standards-oriented validator with the PDF/UA-1 validation profile. The veraPDF report used version 1.30.2 and the GreenField parser. veraPDF detected G01-M03, G02-M03, G03-M03, G04-M03, and G02-M04. The M03 mutants failed ISO 14289-1:2014 Clause 7.4.2 Test 1. G02-M04 failed four list-structure checks under ISO 14289-1:2014 Clause 7.2.

No validator repair, auto-tagging, or manual remediation was applied to the PDFs before recording results. Validator runs were interpreted as automated evaluations of the PDFs as generated. For veraPDF, the selected profile was PDF/UA-1. For Acrobat, the check was run as the Accessibility Checker/Full Check workflow over the document. "Needs manual check" items were manually reviewed and documented, but they were not coded as automated failures.

### 4.6 Detection Coding

Each generated mutant was coded for each validator as Detected or Missed.

Detected means the validator reported an automated failure that corresponded to the injected defect category.

Missed means the validator reported no relevant automated failure for the independently verified mutant.

N/A was used only for non-generated cases and was excluded from detection-rate denominators.

Manual-check prompts were not coded as automated detections. For example, Acrobat's recurring manual-check items on the golden PDFs were manually reviewed and recorded as passing, but they were not counted as mutation detections because the experiment measures automated validator detection under fixed checker settings. A validator failure was counted as a detection only when the failed rule aligned with the mutation's intended defect category, such as heading nesting for M03 or list containment for G02-M04.

## 5. Results

### 5.1 Overall Detection Rates

Across 23 generated and independently verified mutants, PAC detected 4 mutants, Acrobat detected 5 mutants, and veraPDF detected 5 mutants. The overall mutation-detection rates were therefore:

Figure 2 visualizes these overall rates.

![Figure 2. Overall mutation-detection rates](figures/figure2_overall_detection_rates.svg)

| Validator | Detected | Missed | Total | Detection rate |
|---|---:|---:|---:|---:|
| PAC | 4 | 19 | 23 | 17.4% |
| Acrobat | 5 | 18 | 23 | 21.7% |
| veraPDF | 5 | 18 | 23 | 21.7% |

These values are mutation-detection rates for this controlled benchmark. They should not be read as general accessibility accuracy scores.

This matters because most verified structural defects in the benchmark survived all evaluated automated checks. In a workflow that relies only on these automated outputs, the surviving mutants would remain indistinguishable from the validator-clean baselines unless a separate structural inspection, assistive-technology check, or targeted structural test were used.

### 5.2 Detection by Mutation Operator

Detection was highly concentrated in one mutation operator. All three validators detected every generated M03 heading-hierarchy mutant, giving each validator a 4/4 detection rate for M03.

No validator detected any M01, M02, or M05 mutant. These operators covered structural reading-order swaps, omitted assistive structure, and internal MCID sequence reversal.

These misses are practically meaningful because the affected properties influence what assistive technologies can navigate or read, even when the page appearance is preserved. For example, omitted structure can remove visible content from the tagged representation, and reading-order or MCID-order changes can alter the sequence exposed to nonvisual users.

For M04, Acrobat and veraPDF each detected 1/5 mutants, while PAC detected 0/5. The only detected M04 case was G02-M04.

Figure 3 shows the same operator-specific pattern graphically.

![Figure 3. Detection by mutation operator](figures/figure3_per_operator_detection.svg)

| Mutation | Operator | PAC | Acrobat | veraPDF |
|---|---|---:|---:|---:|
| M01 | Structural reading-order swap | 0/5 | 0/5 | 0/5 |
| M02 | Omit visible content from tag structure | 0/5 | 0/5 | 0/5 |
| M03 | Incorrect heading level / skipped hierarchy | 4/4 | 4/4 | 4/4 |
| M04 | Wrong marked-content association | 0/5 | 1/5 | 1/5 |
| M05 | Internal MCID sequence reversal | 0/4 | 0/4 | 0/4 |

### 5.3 Validator Agreement

Acrobat and veraPDF agreed on all 23 generated mutants at the detected/missed level. PAC agreed with Acrobat and veraPDF on 22 of 23 generated mutants.

| Validator pair | Agree | Disagree | Total | Agreement rate | Disagreement case |
|---|---:|---:|---:|---:|---|
| PAC vs Acrobat | 22 | 1 | 23 | 95.7% | G02-M04 |
| PAC vs veraPDF | 22 | 1 | 23 | 95.7% | G02-M04 |
| Acrobat vs veraPDF | 23 | 0 | 23 | 100.0% | None |

The three-validator patterns were:

| Pattern | Count | Share |
|---|---:|---:|
| Detected / Detected / Detected | 4 | 17.4% |
| Missed / Detected / Detected | 1 | 4.3% |
| Missed / Missed / Missed | 18 | 78.3% |

### 5.4 G02-M04 Disagreement Case

G02-M04 is the clearest disagreement case in the experiment. The mutation verification data confirmed that the list order remained structurally stable while the first two list items pointed to each other's underlying content. PAC reported no automated failure for this mutant.

Acrobat detected G02-M04 and reported two list-related failures: List items and Lbl/LBody. veraPDF also detected G02-M04 and reported four failures under ISO 14289-1:2014 Clause 7.2, covering list containment and allowed-child constraints.

This case is important because the disagreement is not merely an overall pass/fail mismatch. Acrobat and veraPDF both localized the issue to list structure, while PAC did not report a corresponding automated failure.

### 5.5 Final Detection Matrix

| Mutant | Operator | PAC | Acrobat | veraPDF |
|---|---|---|---|---|
| G01-M01 | M01 | Missed | Missed | Missed |
| G01-M02 | M02 | Missed | Missed | Missed |
| G01-M03 | M03 | Detected | Detected | Detected |
| G01-M04 | M04 | Missed | Missed | Missed |
| G01-M05 | M05 | Missed | Missed | Missed |
| G02-M01 | M01 | Missed | Missed | Missed |
| G02-M02 | M02 | Missed | Missed | Missed |
| G02-M03 | M03 | Detected | Detected | Detected |
| G02-M04 | M04 | Missed | Detected | Detected |
| G02-M05 | M05 | Missed | Missed | Missed |
| G03-M01 | M01 | Missed | Missed | Missed |
| G03-M02 | M02 | Missed | Missed | Missed |
| G03-M03 | M03 | Detected | Detected | Detected |
| G03-M04 | M04 | Missed | Missed | Missed |
| G03-M05 | M05 | Missed | Missed | Missed |
| G04-M01 | M01 | Missed | Missed | Missed |
| G04-M02 | M02 | Missed | Missed | Missed |
| G04-M03 | M03 | Detected | Detected | Detected |
| G04-M04 | M04 | Missed | Missed | Missed |
| G04-M05 | M05 | Missed | Missed | Missed |
| G05-M01 | M01 | Missed | Missed | Missed |
| G05-M02 | M02 | Missed | Missed | Missed |
| G05-M03 | M03 | N/A | N/A | N/A |
| G05-M04 | M04 | Missed | Missed | Missed |
| G05-M05 | M05 | N/A | N/A | N/A |

## 6. Discussion

### 6.1 Mutation Detection Is Operator-Specific

The strongest result is not simply that overall detection rates were low. The more important finding is that detection was concentrated by operator. All validators detected M03 heading-hierarchy violations, but none detected M01, M02, or M05, and only Acrobat and veraPDF detected one M04 case.

This suggests that automated PDF accessibility validators may be highly sensitive to certain standards-checkable structural constraints while remaining insensitive to other accessibility-relevant structure changes. This is consistent with the distinction between machine-checkable conformance rules and defects that require deeper semantic interpretation.

### 6.2 Surviving Mutants Are Not Proof of Accessibility

The 18 mutants missed by all three validators were not treated as valid or accessible PDFs. They were treated as verified mutants that survived the evaluated automated checks. This distinction is essential for avoiding overstatement.

For example, a structural reading-order swap can be accessibility-relevant even if it does not violate a validator's automated rule. A validator may correctly decline to flag a problem that requires semantic judgment. The benchmark therefore measures whether a validator detects specific controlled mutations, not whether the validator makes a complete accessibility judgment.

### 6.3 G02-M04 Shows Cross-Validator Sensitivity Differences

G02-M04 demonstrates that validators may differ even within the same operator class. PAC missed all M04 mutants, while Acrobat and veraPDF detected G02-M04. Because Acrobat and veraPDF both identified list-structure problems, this case provides stronger evidence than a generic pass/fail disagreement.

At the same time, Acrobat and veraPDF did not detect the other M04 mutants. This suggests that detection may depend not only on the abstract mutation operator but also on the specific local PDF structure where the mutation is applied.

### 6.4 Focused Operator Coverage

The five operators provide focused coverage of distinct, interpretable structure-level failure modes. They support controlled comparison across validators because each operator has a specific structural target and an independently verified mutation condition. The appropriate claim is not that the operators form a complete taxonomy of PDF accessibility defects, but that they establish a principled operator set for studying how validators respond to controlled PDF structure mutations.

### 6.5 Implications for Validator Use

The results support a practical distinction between using validators as conformance aids and treating them as complete accessibility oracles. PAC, Acrobat, and veraPDF were effective on the generated heading-hierarchy defects, and Acrobat and veraPDF also detected one list-related association defect. However, the same tools did not report relevant automated failures for verified mutations that changed reading sequence, omitted tagged content, or reversed internal marked-content order. For document producers, this means validator-clean output should be understood as evidence about the implemented automated checks, not as evidence that the assistive representation is free of structure-level defects. For tool builders, the surviving mutants identify concrete regression tests for future checker rules.

## 7. Threats to Validity

### 7.1 Corpus Size

The corpus contains five golden PDFs and 23 generated mutants. The corpus supports controlled within-benchmark claims about these five PDFs and 23 verified mutants. Broader generalization across PDF genres, authoring pipelines, and defect types requires additional corpus expansion.

### 7.2 Mutation Operator Coverage

The five mutation operators target structure-level defects. They do not cover all PDF accessibility problems, such as alternative text quality, table header semantics, language metadata, color contrast, form labeling, or natural-language reading-order coherence.

### 7.3 Validator Configuration

The results depend on the validator versions and settings used in the experiment. Different versions or configurations may report different outcomes. The available evidence records PAC 26.1 and veraPDF 1.30.2; the exact Acrobat build is a reporting limitation.

### 7.4 Detection Coding

The study codes detection based on relevant automated validator failures. Some validator outputs may include warnings, manual-check prompts, or failures that do not correspond directly to the injected mutation. This paper treats only relevant automated failures as detections.

### 7.5 Independent Verification Scope

The mutation verification process confirms the structural presence of the injected defects and the visual-preservation properties needed for this benchmark. User studies and assistive-technology traces would address a different question: how each verified structural defect affects end-user experience.

## 8. Limitations and Future Work

Future work should expand the corpus to include more document genres, authoring tools, and structural patterns. Additional mutation operators should target table header associations, alternative text, artifact tagging, language metadata, form fields, links, annotations, and reading-order defects that require semantic interpretation.

The benchmark should also be packaged as a public dataset with machine-readable manifests, mutation verification records, and validator result files. Releasing the corpus and scripts would allow other researchers to reproduce the results and evaluate additional validators.

Finally, future work can extend PDFa11yMut by measuring how surviving mutants affect assistive-technology output and remediation decisions. This would complement the present benchmark, which focuses on whether automated validators detect independently verified structural mutations.

## 9. Artifact Availability

For reproducibility, PDFa11yMut should be released with the golden PDFs, generated mutants, mutation-generation scripts, mutation-verification records, validator result matrix, and analysis workbook. The release should preserve N/A cases explicitly and include machine-readable metadata for each mutant: golden PDF ID, mutation operator, target object, intended accessibility effect, verification status, visual-preservation result, and validator outcomes.

The current analysis artifacts already include the full detection matrix, per-operator rates, validator agreement table, and paper-ready analysis notes. Before publication, these should be packaged in a public repository and, ideally, archived with a persistent identifier.

## 10. Conclusion

PDFa11yMut demonstrates that controlled mutation testing can reveal how automated PDF accessibility validators respond to independently verified structural defects. In this benchmark, three validators detected all generated heading-hierarchy mutants but missed most other verified mutations. Acrobat and veraPDF detected one list-related marked-content association mutant that PAC missed, producing the only cross-validator disagreement case.

The contribution is both methodological and practical. Methodologically, PDFa11yMut separates mutation verification from validator output, giving researchers a way to test checker behavior against known structural defects rather than ambiguous naturally occurring PDFs. Practically, the results show that validator-clean outcomes can coexist with verified defects in the assistive structure, including defects that preserve visual rendering. These results do not show that any validator is generally accurate or inaccurate. They show that mutation-based evaluation can make validator behavior more observable, especially at the boundary between machine-checkable PDF/UA conformance rules and accessibility-relevant defects that survive automated checking. PDFa11yMut therefore provides a reproducible basis for studying PDF accessibility validator sensitivity and for building regression tests that target validator blind spots.

## References

[AdobeAccessibility] Adobe. 2026. Acrobat Enterprise Toolkit: Accessibility Checker Preferences. https://www.adobe.com/devnet-docs/acrobatetk/tools/PrefRef/Windows/Accessibility.html

[Bhadra2026] Meet Bhadra. 2026. GateTruth: Auditing the Rigor of RTL Design Benchmarks via Mutation Testing. arXiv:2608.12635. https://arxiv.org/abs/2608.12635

[Brady2015] Erin Brady, Yu Zhong, and Jeffrey P. Bigham. 2015. Creating accessible PDFs for conference proceedings. Proceedings of the 12th Web for All Conference. DOI: 10.1145/2745555.2746665.

[KumarPadathWang2025] Anukriti Kumar, Tanushree Padath, and Lucy Lu Wang. 2025. Benchmarking PDF Accessibility Evaluation: A Dataset and Framework for Assessing Automated and LLM-Based Approaches for Accessibility Testing. Proceedings of the 27th International ACM SIGACCESS Conference on Computers and Accessibility. DOI: 10.1145/3663547.3746380.

[KumarWang2024] Anukriti Kumar and Lucy Lu Wang. 2024. Uncovering the New Accessibility Crisis in Scholarly PDFs. Proceedings of the ACM SIGACCESS Conference on Computers and Accessibility. https://arxiv.org/abs/2410.03022

[Nganji2018] Julius T. Nganji. 2018. An assessment of the accessibility of PDF versions of selected journal articles published in a WCAG 2.0 era (2014-2018). Learned Publishing 31, 4, 391. DOI: 10.1002/leap.1197.

[Paliwal2024] Sparsh Paliwal, Joshua Hoeflich, J. Bern Jordan, Rajiv Jain, Vlad I. Morariu, Alexa Siu, and Jonathan Lazar. 2024. FormA11y - A tool for remediating PDF forms for accessibility: Designing a PDF Form Remediation Tool. ACM Transactions on Computer-Human Interaction 32, 1, 1-39. DOI: 10.1145/3702317.

[PDFAssociation2021] PDF Association. 2021. The Matterhorn Protocol 1.1. https://pdfa.org/resource/the-matterhorn-protocol/

[Ribera2020] Mireia Ribera, Ricardo Pozzobon, and Sergio Sayago. 2020. Publishing accessible proceedings: the DSAI 2016 case study. Universal Access in the Information Society 19, 557-569. DOI: 10.1007/s10209-019-00660-3.

[Silva2022] Henrique Neves da Silva, Silvia Regina Vergilio, and Andre Takeshi Endo. 2022. Accessibility Mutation Testing of Android Applications. Journal of Software Engineering Research and Development 10. DOI: 10.5753/jserd.2022.2133.

[Tafreshipour2024] Mahan Tafreshipour, Anmol Deshpande, Forough Mehralian, Iftekhar Ahmed, and Sam Malek. 2024. Ma11y: A Mutation Framework for Web Accessibility Testing. ISSTA 2024: 100-111. DOI: 10.1145/3650212.3652113.

[veraPDFValidation] veraPDF Consortium. 2026. veraPDF Validation Documentation. https://docs.verapdf.org/validation/
