# PDFa11yMut methodology

PDFa11yMut is a mutation-testing study of PDF accessibility checking configurations. It starts with reference-suite PDFs, applies one specified structure-level mutation at a deterministic reachable target, and retains a pair only when the mutation and non-target invariants pass.

## Study units

- A golden/reference PDF is the source artifact.
- A mutant is one source PDF plus one operator application.
- The formal outcome is one baseline-relative validator-mutant row for PAC Formal, Acrobat Accessibility Full Check, or veraPDF PDF/UA-1.
- The unit of evidence is hash-linked: source hash, mutant hash, validator configuration, raw report path/hash, classification, and coding/adjudication fields.

The current evidence-derived scope is nine reference PDFs, 73 generation-ledger records, 72 materialized mutant PDFs, 5 documented exclusions, 69 active independently re-audited mutants, and 207 active checker-configuration rows. Four exclusions are inside the valid-generation manifest and one is a historical exclusion-only/non-materialized record; therefore the counts are not a simple `73 - 5` subtraction. Three valid M09 replacement candidates remain outside the active interpretation because they cannot replace unavailable historical validator evidence. The active operator counts and all dependent counts are generated in `STUDY_MANIFEST.json`; historical 23-mutant summaries are not inputs.

## Operators and classes

M01, M02, M04, and M05 are Class B semantic/assistive-representation mutations. A lack of an automated finding is reported as no automated finding or survival of the tested automated check; it is not automatically a validator false negative.

M03, M07, M08, M09, and M10 are Class A conformance-oriented mutations in the current study design. M06 is retained as a structurally confirmed Class B list-representation mutation because the authoritative materials reviewed did not establish a specific machine-checkable duplicate-reference requirement. A detection is classified as direct target detection unless the evidence is the explicitly constrained Acrobat M10 consequence proxy. Baseline-carried findings, collateral findings, manual-review prompts, and no-target-detection outcomes are kept distinct in the evidence ledger.

## Target selection and verification

The common target rule is the first eligible reachable target in stable structure traversal order. `data/operator_target_selection.csv` records candidate count, candidate references, chosen target, precondition status, and reachability status for every active mutant. The selection is deterministic; no random seed is used.

The generator-side verifier checks parseability, intended deltas, page/content invariants, and rendering. `scripts/independent_audit.py` uses PyMuPDF/MuPDF for independent rendering and a deliberately narrow raw-COS audit. The current v2 audit confirms the intended raw-COS delta and whole-tree expected-result signature for all 69 active pairs, with MuPDF rendering invariants passing for 69/69. The checks are operator-aware: M01/M02 compare structure-tree order/reachability, M04 compares leaf content associations, M05 compares top-level content-item order, M06 compares repeated direct `/LI` references, and M03/M07-M10 compare their scoped structural deltas. This establishes independent artifact verification, not a claim that all semantic properties are machine-checkable or that validators must report them.

## Validator interpretation

PAC Formal, Acrobat Full Check, and veraPDF PDF/UA-1 are different checking configurations, not interchangeable instruments. Acrobat manual prompts are a separate category. Rates are mutation-specific detection/kill rates with the stated denominator `Detected + no automated target finding`; Class B no-finding rows are not treated as validator failures, and manual rows are reported separately. These are not estimates of general accessibility accuracy, sensitivity, or specificity.

## Secondary observations

The 18 no-op/benign controls are paired sanity checks against baseline-relative changes; none produced a new target-relevant automated finding under the paired count comparison. The nine NVDA observations are categorized in `data/at_observation_categories.csv`: eight active-formal-mutant cases and one auxiliary M01 demonstration. They are illustrative exploratory observations under one NVDA/Acrobat/Windows configuration and one observer; they are not a user study and do not enter formal checker rates. PAC AI is retained separately as aggregate/unresolved exploratory evidence and is not a prerequisite for the formal study.
