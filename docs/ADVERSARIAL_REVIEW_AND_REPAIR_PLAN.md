# Adversarial review and repair plan

> Historical planning record. It contains pre-repair acceptance criteria and must not be read as the current study status. The current coding evidence has two recorded decision fields plus adjudication, but independent-human coder provenance is not substantiated; see docs/DOUBLE_CODING_QUEUE.md and data/double_coding_manifest.json.

> Historical repair-plan snapshot. The dated attack table below preserves the pre-repair state and proposed gates; current status is authoritative in `SUBMISSION_AUDIT.md`, `SUBMISSION_FIX_LOG.md`, and `FINAL_REVIEWER_ATTACK.md`.

Reviewed 2026-09-22 against the canonical data, the current manuscript PDF/source, the verification scripts, the release archive, and recent primary/comparative work. The central direction remains viable: measure mutation-specific PDF accessibility-validator detection with evidence-locked positive and negative cases. The current artifact is conditionally strong, but a hostile reviewer can still break several claims.

## Bottom line

After genuine double-coding and adjudication, the formal evidence gate will be complete. That will not by itself make the paper publication-hard. The remaining risks are methodological rather than cosmetic:

1. the independent-verification claim is too broad for the semantic operators;
2. the negative controls do not yet support operator-level specificity estimates;
3. the point estimates ignore source clustering and small per-operator denominators;
4. the semantic/assistive RQ is a nine-case, one-observer pilot;
5. the uniqueness claim needs a sharper comparison against PDF benchmark and validator-comparison work;
6. the paper/release must be regenerated only after the final evidence and analyses are frozen.

## Kill tests

| Priority | Hostile reviewer attack | Current evidence | Why it can kill the paper | Repair and acceptance gate |
|---|---|---|---|---|
| P0 | “The second parser independently verifies every mutation.” | Historical pre-repair finding. | This was a legitimate risk at the time of the snapshot. | Current v2 audit now implements operator-aware raw-COS checks and confirms all 69 active pairs; see the current audit and fix log. |
| P0 | “The study measures full accuracy/specificity.” | There are 18 complete controls, two per golden, but not operator-matched benign controls for each property. G05 and G09 have pre-existing native findings. | A clean/no-op document can estimate false alarms only for the tested document/checkpoint context. It cannot support a general operator-level specificity claim. | Add a control-classification ledger keyed by control, validator, intended operator, and baseline-relative rule. Add property-matched benign controls for at least three source PDFs per Class-A operator, or restrict the paper to descriptive control false-positive observations. Acceptance: every specificity/precision number has an explicit control denominator and baseline-conflict treatment. |
| P0 | “The 69 mutants are independent observations.” | There are 69 active mutants across nine source PDFs, with uneven operator coverage: M09=3 and M10=4, while other operators have 7–9. | A 100% or 0% operator rate with 3–4 cases is fragile, and source clustering can make 69 rows look more independent than they are. | Add exact/Wilson intervals per validator/operator/class, source-level outcome tables, and a cluster bootstrap or exact source-cluster sensitivity analysis. Do not rank tools globally. Acceptance: every rate displays `n`, source count, and uncertainty or is labeled descriptive only. |
| P0 | “The classification is an objective oracle.” | `scripts/classify_formal.py` uses hand-maintained term matching and baseline-relative rule IDs; the canonical coder fields are still blank. | A reviewer can argue that the same team defined the mutation, selected matching strings, and judged detections, creating confirmation bias. | Finish independent double-coding; freeze a per-operator codebook with positive, collateral, baseline, manual, and outside-scope examples; report agreement and adjudication by decision dimension. Acceptance: 207/207 records have two coder decisions, rationales, and adjudication where needed. |
| P1 | “The AT result answers the semantic RQ.” | AT evidence is one NVDA/Acrobat observation for each of nine operators, one observer/configuration. | Nine paired observations can demonstrate feasibility and selected effects, not reproducible behavior across viewers/users or all semantic mutants. | Current wording labels these illustrative exploratory observations under one fixed configuration; no general AT claim is made. |
| P1 | “The work is not unique because mutation-based accessibility testing already exists.” | Ma11y already provides 25 accessibility mutation operators and an automated oracle for web tools. A 2025 PDF benchmark covers seven criteria with expert labels, multiple LLMs, and checker comparisons. A 2025 PDF Association comparison reports four validators on 155 reference files. | A reviewer can treat PDFa11yMut as a smaller reimplementation unless the causal/evidence-chain distinction is made explicit. | Add a comparison table: ground truth, mutation unit, PDF/COS specificity, validator scope, baseline pairing, independent verification, negative controls, AT evidence, and release hashes. Claim the narrow contribution: controlled PDF structure mutations plus validator-separated, baseline-relative, hash-linked kill/survival evidence—not “first” or general accessibility accuracy. |
| P1 | “Cross-validator agreement is just a ranking disguised as agreement.” | The paper reports PAC/Acrobat/veraPDF pairwise agreement on 69 rows, while the validators have different capabilities and one has 15 manual-check rows. | Agreement on a coarse `Detected/Missed` label can hide rule identity, manual status, baseline differences, and shared classification logic. | Add checkpoint-level overlap/disagreement tables and report agreement only within comparable claimed scopes. Keep pairwise mutant-level agreement descriptive; do not call it tool accuracy or superiority. |
| P1 | “The negative controls were passed despite relevant findings.” | G05 Acrobat controls share a pre-existing `Lbl and LBody` failure; G09 PAC controls share a pre-existing Natural language failure. | A reviewer can call these false positives unless the intended-property/baseline distinction is visible at row level. | Publish a control decision table with baseline rule, control rule, intended property, relevance, and final category: true negative, baseline-confounded, unrelated, or ambiguous. Acceptance: no control is counted as a true negative without a relevant-rule decision. |
| P2 | “The corpus and operator denominators are opportunistic.” | Nine PDFs are mapped to a collection-level suite; operator applicability is uneven and four M09 artifacts were excluded. | Low M09/M10 counts and source-specific applicability limit external validity and make operator rates easy to overread. | Add an applicability matrix showing eligible/ineligible targets and reasons before mutation generation. Report applicability counts separately from detection counts. Treat M09/M10 as exploratory where `n` is small. |
| P2 | “The artifact is not independently reproducible.” | The clean 2026-09-22 archive passes verify-only reproduction; proprietary PAC/Acrobat runtimes are excluded by design, and the historical acquisition archive was not retained. | A reviewer cannot reproduce the native GUI evidence from a clean environment without those exact runtimes and input provenance. | Keep the reproducibility boundary explicit: open-source structural/analysis reproduction is complete; native GUI evidence is hash-linked observational evidence. Preserve exact versions, profiles, settings, export formats, and a clean-archive check. Do not claim byte-for-byte native rerun reproducibility. |
| P2 | “The manuscript is too compressed to audit.” | The four-page paper has a large mostly empty final reference page and only seven references; exact operator-to-standard mapping is mainly outside the paper. | Reviewers may miss the actual novelty and see a results note rather than a defensible empirical study. | Add a compact operator/capability table or supplementary appendix, expand the related-work comparison, add control/statistical interpretation, and remove redundant prose before final compilation. Do not add claims; use the space to expose auditability. |
| P2 | “The PAC-AI TODOs make the study incomplete.” | 42 manual queue rows are PAC-AI deferred (8 golden + 34 mutant/cohort rows); the manuscript already excludes them from formal conclusions. | If the paper mixes PAC-AI into the contribution or release readiness, reviewers can treat the missing semantic export as a fatal hole. | Keep PAC-AI explicitly optional future work, separate from formal PDF/UA results, and report zero PAC-AI detections/non-detections. Do not spend finalization effort there unless a reproducible semantic export becomes available. |
| P2 | “The corpus license/provenance is stronger than the evidence.” | File mapping and collection-level CC BY terms are documented; the original acquisition archive/timestamp is not retained. | A distributor or reviewer may require per-file provenance and redistribution permission. | Retain the current conservative language, add per-file source URLs/attribution instructions, and make redistribution status explicit. Do not upgrade collection-level PDF/UA claims to per-file conformance claims. |

## Repair sequence that preserves the paper direction

The order below avoids repeated paper/release regeneration.

### Gate 1: independent coding (user-owned evidence)

Complete the 207-case blinded queue with two independent coders and adjudication. Merge only after the strict validator accepts all cases. Compute agreement separately for primary decision, manual status, baseline conflict, outside-scope status, and ambiguity.

### Gate 2: repair the independent audit

Fix `scripts/independent_audit.py` before interpreting its confidence labels. Add explicit operator-specific raw-COS checks and collateral-diff checks. Re-run the audit into a versioned evidence directory and update only the canonical analysis inputs after review. Semantic rows that cannot be independently verified should be `REVIEW_REQUIRED`, not silently `PASS`.

### Gate 3: make controls analytically defensible

First classify the existing 18 controls relative to each validator baseline. Then decide between two honest endpoints:

- preferred: add property-matched benign/no-op controls for at least three documents per Class-A operator and compute scoped specificity/false-positive rates; or
- minimum publishable endpoint: report the current controls as descriptive baseline/false-positive evidence and do not claim a formal specificity estimate.

The central positive-mutant sensitivity study remains unchanged.

### Gate 4: add uncertainty and clustering

Generate analysis from canonical data with exact/Wilson intervals, source-level distributions, and a source-cluster bootstrap/sensitivity analysis. Keep per-operator results with small denominators visibly exploratory. Add a checkpoint-level cross-validator comparison instead of relying only on coarse detected/missed agreement.

### Gate 5: sharpen the uniqueness argument

Expand related work into an explicit comparison against Ma11y, the 2025 PDF accessibility benchmark, the PDF/UA reference/technique ecosystem, and the recent multi-validator comparison. The unique claim should be the combination of causal structure-level PDF mutations, independent mutation/invariant checks, matched baseline-relative rule classification, controls, and hash-linked release evidence.

### Gate 6: repair the manuscript and final freeze once

Only after Gates 1–5 are settled:

1. rebuild analysis and figures;
2. update the manuscript claims, tables, limitations, and related work;
3. compile and render the paper for visual inspection;
4. rebuild the study freeze and release manifest;
5. rebuild the release archive once;
6. verify the clean archive, hashes, tests, and `git diff --check`.

## Publication decision rules

- Full accuracy is claimed only if the controls support an explicit true-negative denominator and the coding gate is complete.
- Otherwise use “mutation-detection sensitivity,” “mutation-kill rate,” and “control false-positive observations.”
- A survived Class-B mutation is not a validator false negative unless the validator claims that semantic property.
- A validator is not ranked globally from these nine documents and uneven operator counts.
- PAC-AI and AT observations remain separate configurations/evidence streams.
- No “first” claim is made; uniqueness is argued by design and evidence-chain composition.

## Current status after this audit

Formal evidence checks pass: 69 active mutants, 207 classified formal rows, 18 completed controls, nine AT observations, and 173/173 prescribed evidence files. The clean release archive reproduced the same conditional study state. The only formal human-evidence gate is double-coding; the 42 PAC-AI queue rows are intentionally deferred future work. The independent-audit, control-specificity, uncertainty, and related-work repairs above should be completed before treating the paper as publication-ready.

## Repair work completed in the current pass (2026-09-22)

- `scripts/independent_audit.py` now writes versioned reports under `evidence/independent_verification_v2/`, leaves the former evidence intact, labels copied primary verification separately, and never treats unsupported structural checks as passes. The completed v2 audit confirms the intended delta for all 69 active pairs and passes MuPDF rendering checks for 69/69. The normalized raw-COS route covers M01/M02 order/reachability, M04 association exchange, M05 content-item order, M06 repeated `/LI`, and the scoped M03/M07-M10 deltas.
- `scripts/robustness_sensitivity.py` reports Wilson and source-cluster bootstrap intervals only for baseline-PASS binary machine-checkable outcomes, with semantic cases descriptive-only and manual/confounded records visible as not rate-coded. It reads the canonical formal freeze and does not rewrite generated paper/release artifacts. The current 1,000-replicate exploratory run found Class A sensitivity 27/33 PAC, 20/31 Acrobat, and 30/37 veraPDF; rerun with the default 5,000 replicates, then freeze figures only after double-coding/adjudication is complete.
- `RELATED_WORK_AUDIT.md` now explicitly compares Kumar et al. (PDF benchmark), Ma11y (web mutation testing), and the PDF Association's 2025 four-validator comparison, and narrows novelty to the evidence-chain design rather than a “first” claim.
- The manuscript source now uses “detection” rather than “accuracy” in the title, restricts its independent-verification description to a scoped subset, and says controls are descriptive rather than general specificity evidence. The PDF, release ZIPs, and release manifest have intentionally not been regenerated.

Remaining publication-critical work: user-owned double-coding/adjudication; normalized structural checks for the five unsupported operators; a rule-identity control ledger or removal of any specificity implication; final 5,000-replicate uncertainty output; and one final analysis/paper/release build after those gates close. The 9-case single-observer AT pilot and missing historical acquisition archive remain stated limitations, not repairs this project should overclaim away.
