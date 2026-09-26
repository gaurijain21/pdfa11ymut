# Reviewer 2 adversarial report

Audit date: 2026-09-25. This report evaluates the candidate artifact as a skeptical reviewer who did not observe its development history.

## Summary

PDFa11yMut presents a scoped mutation-testing artifact for PDF accessibility checking configurations. The active evidence is coherent at 69 mutants and 207 formal rows, with paired baselines, operator-specific deltas, archived reports, and explicit Class A/Class B interpretation.

## Strengths

- The unit of analysis is an explicit baseline/mutant pair rather than an unpaired defect label.
- Active counts, exclusions, hashes, validator rows, and control rows are machine-audited.
- M06 is no longer presented as a normative validator failure; its dedicated audit separates structural confirmation from machine-checkability.
- Baseline-carried findings, Acrobat manual prompts, proxy detections, and Class B no-findings are separated in generated analysis.
- The paper avoids unsupported independent-coder, representative-AT, and global-accuracy claims.

## Major Concerns

1. Four historical M09 records cannot be independently re-audited. This is documented in `data/exclusions.csv`, `data/m09_recovery_candidates.csv`, and `docs/M09_RECOVERY_AUDIT.md`. Status: MITIGATED; they remain excluded and are not silently replaced.
2. The corpus is nine files from one reference-suite family. `data/corpus_inventory.csv` and the manuscript's Threats section make the clustering and omitted 2-07 item explicit. Status: INHERENT LIMITATION.
3. Validator evidence is version/configuration specific and partly GUI-derived. `data/validator_environment.csv`, native reports, and `FRESH_CLONE_REPRODUCIBILITY.md` separate analysis regeneration from evidence recollection. Status: MITIGATED.
4. The Class A/B boundary is study-specific, especially for M06 and M10. `docs/M06_VALIDITY_AUDIT.md`, `data/operator_standard_mapping.csv`, and the capability mapping make this explicit. Status: MITIGATED.

## Minor Concerns

- Historical 23-mutant files remain in the repository and can confuse casual readers. Notices and the active audit guard them, but public packaging should keep them visibly archival. Status: MITIGATED.
- Acrobat has separate manual rows and a historical 31/31 metadata string. The canonical narrative uses the native-session 31/32 setting and retains the old string as provenance. Status: MITIGATED.
- The paper's tagged-PDF status is a local structural gate, not proof of complete venue-level PDF/UA conformance. `docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md` says so. Status: INHERENT LIMITATION.

## Questions for Authors

- Which artifacts are legally redistributable? See `release/CURRENT_RELEASE_POLICY.md`, `data/public_release_manifest.json`, and `DATA_LICENSES.md`; raw vendor/AT evidence is excluded pending clearance.
- Can the final submission identify the exact freeze commit? Yes: the current pushed commit is recorded in `SECOND_PASS_STATE.md` and the generated study/release manifests; the public release boundary excludes raw proprietary vendor/AT bytes.

## Reproducibility Assessment

Analysis and audit reproduction are strong from the archived candidate copy. Native validator and AT recollection are intentionally not claimed. `data/evidence_checksums.sha256`, canonical ledgers, and `FRESH_CLONE_REPRODUCIBILITY.md` provide the boundary. Status: MITIGATED.

## Novelty Assessment

The defensible novelty is the reusable transformation/evidence unit: paired source and mutant PDFs, explicit preconditions and invariants, hash-linked validator outcomes, and operator-level analysis. Atomic PDF/UA examples, reference suites, validator benchmarks, Ma11y, and Android mutation testing are acknowledged as prior or complementary work. No “first ever” claim is required. Status: MITIGATED.

## Threats to Validity

Source clustering, target-selection order, parser/rendering dependence, post-discovery exclusions, validator scope/version, AT variability, limited PDF/UA-1 scope, baseline conflicts, and legal/provenance boundaries remain. `analysis/leave_one_source_out.csv` adds a descriptive source-cluster sensitivity view; it does not create a population estimate. Status: INHERENT LIMITATION where applicable.

## Claims That Are Too Strong

The artifact must not say that a validator “cannot detect” a mutation, that Class B rows are validator failures, that rendering equality is universal visual identity, that AT observations establish user harm, that controls estimate specificity, or that coder fields prove independent human coding. The current manuscript uses bounded alternatives. Status: RESOLVED.

## Artifact Problems

The original requested checkout is empty; the actual candidate is the local checkout. The repaired state is committed and pushed to `origin/main`; the final manifest records the exact commit and dirty state. Raw vendor/AT evidence remains intentionally outside the public freeze. Status: MITIGATED.

## Remaining Work Before Submission

- Preserve the final manifest/commit identity if the artifact is frozen again.
- Keep the final gate commands in the release checklist.
- Review the release manifest for item-level redistribution clearance and submit only the permitted evidence subset.
- Apply venue-specific final PDF accessibility review.

There is no remaining scientific submission blocker in the current scoped artifact. Remaining items are release bookkeeping, legal clearance, and venue QA.
