# Final Consolidation Audit

This audit records the pre-repair baseline and final resolution of the submission-freeze pass. The detailed final judgment is in `FINAL_PRE_SUBMISSION_REVIEW.md`.

## Repository state

- Repository: `C:\Gauri\ma11ypdf`
- Branch: `main`
- HEAD before repairs: `2e86edb` (`Strengthen reviewer readiness and reproducibility disclosures`)
- Remote: `origin` → `https://github.com/gaurijain21/pdfa11ymut.git`
- Existing freeze tag: `paper-freeze-v1` (must remain immutable)
- Working tree before this audit: clean
- The provided working directory `C:\Users\iamga\OneDrive\Documents\ChatGPT\pdfa11ymut` is an empty, no-commit staging checkout; this audit applies to the populated research repository above.

## Issue register

| Issue | CURRENT STATE | PROBLEM CONFIRMED? | FILES INVOLVED | REQUIRED FIX | SCIENTIFIC RESULT CHANGES? | VALIDATOR RERUN REQUIRED? | STATUS |
|---|---|---|---|---|---|---|---|
| 1. Final freeze state | Inspect manifest and release state | Pending | `STUDY_MANIFEST.json`, release files | Final clean manifest and new immutable freeze tag only at end | No, unless canonical artifacts change | No | Open |
| 2. Old freeze mismatch | Audit `paper-freeze-v1` without rewriting it | Pending | tag, paper, manifest | Create `paper-freeze-v2` after repairs | No | No | Open |
| 3. 73/5/69 accounting | Verify canonical records and exclusions | Pending | `data/mutants.jsonl`, exclusions, manuscript | Make record classes and arithmetic explicit | No | No | Open |
| 4–5. Overall/Class-B rates | Inspect generated tables and paper | Pending | `data/`, `analysis/generated/`, paper | Counts-only overall table; Class A scored; Class B descriptive | No | No | Open |
| 6. Abstract | Inspect against canonical results | Pending | paper sources/fragments | Rewrite with actual Class-A/Class-B findings | No | No | Open |
| 7. Operator table | Inspect paper and operator specs | Pending | `operators/operators.yaml`, paper | Add accurate compact M01–M10 table | No | No | Open |
| 8–9. Related work | Verify cited source wording and current claims | Pending | paper, related-work audits | Correct Kumar/Matterhorn/Techniques positioning | No | No | Open |
| 10–11. AT evidence | Inspect ledger, manifest, and observations | Pending | `data/at_observations.csv`, `data/at_selection.csv`, paper | Resolve formal/auxiliary M01 status; report 8/9 conservatively if confirmed | Possibly interpretive only | No, unless a narrowly targeted rerun is necessary | Open |
| 12. RQ synthesis | Inspect discussion structure | Pending | paper | Add direct RQ1–RQ4 synthesis | No | No | Open |
| 13. Target sensitivity | Inspect candidate counts and existing support | Pending | `data/operator_target_selection.csv`, scripts | Run small sensitivity study only if safe; otherwise document limitation | Possibly secondary only | Only if feasible | Open |
| 14. M09 exclusion sensitivity | Inspect recovery records and outcomes | Pending | `data/m09_recovery_candidates.csv`, exclusions | Add invalid/unverified sensitivity table, preserve canonical corpus | No | No | Open |
| 15. CSV/schema | Inspect `data/control_results.csv` and audit coverage | Pending | CSVs, `scripts/audit_submission.py`, tests | Repair malformed rows and enforce schemas | No | No | Open |
| 16. Clean CI | Inspect workflows and packaging | Pending | `.github/workflows/`, `pyproject.toml`, docs | Add open-source clean-environment workflow | No | No | Open |
| 17. Public evidence | Inspect release boundary and evidence metadata | Pending | `evidence/`, `data/`, docs | Clarify proprietary byte limitation; add safe sanitized records if available | No | No | Open |
| 18. Validator configurations | Inspect canonical metadata | Pending | validator metadata, paper | Add exact versions/settings table or compact text | No | No | Open |
| 19. Generation commands | Search README/paper/scripts | Pending | README, paper, CLI, scripts | Define one safe reviewer workflow and separate scratch/freeze steps | No | No | Open |
| 20. Terminology | Search paper and docs | Pending | paper, analysis | Rename all-69 outcomes section; distinguish checker configurations | No | No | Open |
| 21–23. Language/novelty | Search stale/informal phrases and tool catalog | Pending | README, paper, docs | Academic wording and transformation-based novelty | No | No | Open |
| 24. Controls | Verify control data and results | Pending | `data/control_results.csv`, paper | State supported control result and scope | No | No | Open |
| 25. Stale audits | Inspect status claims and organization | Pending | root audits, docs/archive | Refresh or archive stale snapshots; maintain clear entry points | No | No | Open |
| 26. Release preparation | Inspect release files and citation metadata | Pending | `CITATION.cff`, release docs | Prepare tag/release assets; do not publish externally without authorization | No | No | Open |
| 27. Paper accessibility | Inspect final PDF/source and available checks | Pending | paper PDF/source, paper accessibility docs | Verify and document; do not claim unverified conformance | No | No | Open |
| 28. Layout | Inspect compiled PDF | Pending | paper PDF/source | Use page space for operator/RQ/configuration content | No | No | Open |
| 29–30. Scope/abstract/freeze discipline | Inspect all claims | Pending | paper, README, audit | Preserve mutation-testing scope and avoid new broad experiments | No | No | Open |
| A–H. Additional checks | Run after repairs | Pending | data, scripts, paper, repo | Claim matrix, generated numbers, source clusters, exclusions, hashes, privacy | Possibly interpretive only | As required by evidence | Open |

## Required end-state

- Canonical results remain evidence-derived and unchanged except for explicitly documented, reproducible analysis corrections.
- Class A is the scored conformance-oriented set; Class B is descriptive.
- The paper, README, generated artifacts, audit script, and reproducibility instructions agree.
- A final clean commit is created, followed by a new immutable `paper-freeze-v2` tag if all gates pass.
- `STUDY_MANIFEST.json` reports the final commit/state, `worktree_dirty: false`, and `status: PAPER_FROZEN` using the project schema.
- `FINAL_PRE_SUBMISSION_REVIEW.md` has no unresolved `BLOCKER`.

This file is the required pre-edit audit baseline and will be updated as repairs are completed.

## Final resolution note

The issue register above is the preserved pre-edit baseline. Final classifications and evidence-backed dispositions are recorded in `FINAL_PRE_SUBMISSION_REVIEW.md`: no unresolved blocker remains for the local `paper-freeze-v2` boundary; venue-specific PDF/UA gates, proprietary evidence redistribution, Class-B scoring, alternate-target native reruns, and historical M09 recovery remain explicit limitations.
