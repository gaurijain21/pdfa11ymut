# PDFa11yMut Submission Fix Log

This log records material changes made after `SUBMISSION_AUDIT.md`. Raw PDFs, raw validator reports, screenshots, and historical artifacts are not deleted or overwritten.

## 2026-09-25 — stale final-artifact records corrected

- Updated the current build-status, paper-freeze, semantic-review, and external-gate records to the final manuscript PDF hash `3ce4b9bcafa9bc74dcce30a327d0df4b9d87e8eefe0ec68d7b80acb809a5dc13`.
- Corrected obsolete statements that described the final PDF as untagged or lacking a semantic tree. Those statements remain historical records of earlier builds; the current PDF passes the bounded local semantic gate.
- Recorded that the generated-results table spacing repair removed the prior overfull-box warning. The remaining compiler messages are underfull spacing warnings only.

Entries below this point preserve earlier intermediate states for audit history. Their hashes and accessibility findings are superseded by the correction above and by the current values in `STUDY_MANIFEST.json`.

## 2026-09-25 — current manuscript PDF rebuilt and archived

- Built the repaired manuscript source with the local Tectonic 0.17.0 executable after MiKTeX could not complete first-run setup.
- Archived the pre-rebuild PDF at `paper/archive/pre_current_rebuild/pdfa11ymut_ieee_2026-09-24.pdf` and promoted the validated four-page build to `paper/pdfa11ymut_ieee.pdf`. The current PDF hash is `187d25831e9d709119d7a230b8bbea4d47b20dbcac7a1f7296a13ce314d0f78f`.
- Rendered all four pages with Poppler at 120 DPI and inspected them. No clipping, overlap, broken table, or unreadable-glyph defect was found. Tectonic still reported layout warnings, including one 8.3pt overfull box in the generated results fragment; this remains a presentation risk to review.
- PDF metadata inspection reports Tagged: no and no document language, MarkInfo, or StructTreeRoot. This remains an explicit delivery limitation; no scientific content was changed to manufacture tags.
- This changes the manuscript artifact and freeze hashes only. It does not change raw validator evidence, classifications, active denominators, or study counts.

## 2026-09-25 — current evidence vocabulary and provenance gates tightened

- Added `interpreted_outcome` to the generated formal freeze. Class B non-findings are now labeled `NO_AUTOMATED_FINDING`; Class A non-findings are `SURVIVED_AUTOMATED_CHECKS`; direct/proxy/collateral/manual categories remain distinct. Raw validator classifications remain unchanged for traceability.
- Corrected the coding manifest and queue documentation so the two recorded decision fields are not described as proof of independent human coding. The 204/207 agreement and kappa calculation are retained with the provenance limitation.
- Added a post-audit repair addendum recording the fresh PDF build, official collection-level CC BY 4.0 evidence, the missing historical acquisition archive, and the unresolved Acrobat 31/31 versus 31/32 discrepancy.

## 2026-09-25 — final consistency run

- Rebuilt the manifest and derived analysis/freeze outputs after the vocabulary and protocol repairs.
- Final checks passed: submission audit, evidence audit (173/173), study-state verification, and 15 unit tests.
- Final hashes: STUDY_MANIFEST.json `e431d8b056ed3cbd57d12e5ec6788c979b1cfc3387300ba98faa8bdc4a21659e`; manuscript source `9ba7aa57e6c51b80d9c5eb5d200806ce432f9b160f02cec2586f363e0fe7e36a`; manuscript PDF `187d25831e9d709119d7a230b8bbea4d47b20dbcac7a1f7296a13ce314d0f78f`.

## 2026-09-25 — completed operator-aware independent audit

- Extended `scripts/independent_audit.py` with normalized PyMuPDF/MuPDF raw-COS checks for M01, M02, M04, and M05, including inline MCR parsing and whole-tree expected-result comparison across pypdf object-number remapping.
- Re-ran all 69 active pairs into `evidence/independent_verification_v2/`: 69/69 intended deltas confirmed, 69/69 independent render checks passed, and 69/69 records reached `HIGH` confidence under the documented artifact-verification definition. No raw validator evidence was changed.
- Updated the methodology, manuscript, and Phase 1 audit to remove the now-stale claim that these four operators were structurally review-required. The semantic/Class B interpretation remains unchanged.
- Added explicit manifest fields distinguishing 73 generation records, 72 materialized mutant PDFs, 70 valid verified mutants, and 69 active mutants; README and audit text now use those meanings rather than collapsing them into one count.

## 2026-09-25 — paper-build gate rechecked

- Re-attempted a local MiKTeX build using an isolated writable user-root and `-no-install`. MiKTeX still fails before compilation because its fresh installation requires setup and attempts to create the protected roaming configuration directory. The existing four-page PDF was not overwritten or presented as current.
- Updated `docs/PAPER_FREEZE.md` with the current manuscript-source and manifest hashes. The untagged/stale PDF remains an explicit final artifact gate.

## 2026-09-24/25 — Phase 1 audit and canonicalization foundation

- Added `SUBMISSION_AUDIT.md` with the repository/manuscript audit, provisional canonical counts, issue-by-issue dispositions, and submission blockers.
- Inspected the latest manuscript source and PDF without rewriting the paper. The active PDF is four pages and visually readable but untagged (`Tagged: no`); this remains an open artifact-accessibility issue.
- Ran the existing read-only checks: the unit suite passed 10 tests; `verify_study_state.py --verify` reported no errors; `check_evidence.py` reported 173/173 prescribed files; `reproduce.py` completed its verification stage but exposed a separate 210-row manual queue with 42 PAC-AI TODOs.
- Invoked the existing `scripts/reconcile_canonical.py` reconciliation command during audit. It rewrote already-recorded validator/AT/release metadata fields while preserving raw evidence and classifications. This was not a scientific reclassification and is recorded here because the command is write-capable.
- Added `scripts/build_study_manifest.py`, which derives the canonical manifest and requested provenance/selection/mapping/control views from active artifacts. It does not read legacy 23-mutant summaries.
- Added the PyMuPDF raw-COS M06 second-route check in `scripts/independent_audit.py`. It follows the selected structure-tree path across pypdf serialization, identifies repeated direct `/LI` references, and compares non-target list signatures. Re-audit confirmed all seven active M06 pairs; this changes verification evidence/assurance, not validator classifications or denominators.
- Updated `docs/M06_VALIDITY_AUDIT.md` to record the confirmed structural result and retain the unresolved normative/machine-checkability gate.
- Added `scripts/audit_submission.py` and `tests/test_submission_audit.py`. The new fail-closed audit checks active counts, hashes, report evidence, exclusions, operator mapping, target-selection coverage, and generated rate denominators.
- Added `docs/METHODOLOGY.md`, `docs/REPRODUCIBILITY.md`, and `docs/EVIDENCE_SCHEMA.md`; added generated `data/validator_environment.csv` with validator/runtime versions and settings.
- Extended `scripts/rebuild_analysis.py` to emit explicit rate numerator/denominator fields, direct/proxy/manual/baseline classification types, and `analysis/generated/disagreement_analysis.csv`.
- Corrected the AT-selection metadata for `PDFUA-Ref-2-02_Invoice-M01` so its selected golden is the matching invoice baseline. This is a provenance/metadata correction; the AT transcript, hashes, and formal denominator were not changed.
- Added `scripts/build_double_coding_reliability.py` and generated `data/double_coding_reliability.csv`: 204/207 raw agreement (98.5507%), Cohen's kappa 0.979024. The generated interpretation explicitly states that coder identity/independence provenance is not independently substantiated by the repository.

Future entries must state whether a change alters raw data, active denominators, classifications, paper presentation only, or validator evidence requirements.

## 2026-09-25 — Standards, classification, manuscript, and release-hygiene repairs

- Reviewed the authoritative Matterhorn Protocol 1.1 and Techniques for Accessible PDF materials. M06 has a confirmed duplicate `/LI` structural delta, but no dedicated duplicate-reference failure condition was established; M06 was reclassified from Class A to Class B in `operators/operators.yaml`, `scripts/verify_study_state.py`, the generated tables, README, and manuscript. This changes interpretation/class denominators, not raw PDFs, raw validator reports, or the active 69-mutant denominator.
- Corrected the four historical M09 exclusion rationales. The old unused-RoleMap rationale is not defensible because Matterhorn checkpoint 02 applies whether a tag is used or not. Original mutant bytes are unavailable, so the records are now `EXCLUDED_UNVERIFIABLE_TARGET` with `ORIGINAL_ARTIFACT_UNAVAILABLE`; they remain outside the active denominator without being called invalid.
- Regenerated the formal freeze, analysis outputs, manifest, provenance/selection/mapping/control/environment tables, and generated manuscript fragment from canonical inputs. Current active outcomes are PAC 30/69, Acrobat 26/54 automated decisions plus 15 manual rows, and veraPDF 30/69; Class A=30 and Class B=39.
- Added foundational mutation-testing citation and rewrote the current manuscript’s Related Work, experimental model, verification scope, coder/adjudication wording, AT wording, disagreement analysis, rates, threats, conclusion, and M06/M09 interpretation. PAC AI is not in the abstract or formal claim.
- Added `DATA_LICENSES.md`, `LICENSES/README.md`, and revised `THIRD_PARTY_NOTICES.md`/`RELEASE_README.md` to separate MIT code from corpus, derivatives, reports, screenshots, logs, and historical release bundles. No artifact was deleted or relicensed.
- Updated active analysis/control documentation to remove stale “independent double-coding,” “representative AT,” and “invalid unused-RoleMap” claims. Historical 23-mutant documents remain labeled audit records and are not active analysis inputs.
- Attempted to rebuild the manuscript PDF with the installed MiKTeX pdfLaTeX/XeLaTeX toolchains. The local installation could not complete first-run setup/package resolution and no new PDF was produced; the existing PDF remains visually readable but untagged. This is a toolchain/venue release gate, not a validator-data change.
- Verification after repairs: `python scripts/audit_submission.py` PASS and `python -m unittest discover -s tests -p "test*.py" -q` PASS (13 tests). No native PAC, Acrobat, veraPDF, or AT rerun was required because validator evidence and PDFs were not changed.
- Preserved an Acrobat configuration discrepancy rather than normalizing it: `data/acrobat_run_metadata.json` records “All 31 of 31 checks selected,” while the historical native-session note reports “31 of 32.” The generated environment table now exposes both records and the final review treats re-capture as an open public-freeze gate.

## 2026-09-25 — Follow-up repair pass

- Removed the unsupported public implication of independent human coders. The manuscript and README now retain only paired classifications/rationale/adjudication as audit provenance; identities and agreement statistics are not part of the study claim. Raw decision packets were preserved.
- Reconciled Acrobat configuration metadata to the native-session/G01-supported value `31 of 32 checks selected`; the old `31 of 31` wording remains in a dedicated historical field. No raw Acrobat report or classification changed, so no validator rerun was required.
- Added `data/m09_recovery_candidates.csv` and `docs/M09_RECOVERY_AUDIT.md`. Three newly generated reachable-target candidates are recorded but are not substituted for unavailable historical M09 bytes or validator rows; the scanned baseline has no eligible target. The active denominator remains 69.
- Added `release/CURRENT_RELEASE_POLICY.md` and `data/public_release_manifest.json`, separating MIT source/docs, CC BY 4.0 corpus/derivatives, and raw vendor/AT evidence requiring separate redistribution clearance.
- Rebuilt the manuscript with Tectonic 0.17.0 using PDF management/tagging support. The current four-page PDF reports `Tagged: yes`, `/Lang`, `/MarkInfo`, `/StructTreeRoot`, `/Title`, and `/Subject`; all pages were rendered and visually inspected. This changes presentation metadata only and does not alter study data or validator evidence.
- Rebuilt the canonical manifest after these changes. Current machine-derived counts are 9 golden PDFs, 73 generation records, 73 valid verified generation records, 72 materialized mutant PDFs, 69 active mutants, 207 formal rows, 18 controls, 9 AT observations, and 34 PAC-AI rows outside formal rates.
- Added dated exclusion metadata to the generated `data/exclusions.csv`: all current exclusion decisions are explicitly labeled as after-discovery audit decisions rather than prospective/preregistered rules.
- Extended `STUDY_MANIFEST.json` with an explicit machine-readable coding-provenance status: identities are unavailable, independent-human coding is not claimed, and role-labeled decisions/adjudication are internal audit provenance only.
