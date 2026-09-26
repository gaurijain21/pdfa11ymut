# Final hostile reviewer attack

Review date: 2026-09-25

This is an adversarial pre-submission review of the current artifact after the canonical-data and manuscript-source repairs. It does not treat a passing script as proof that every scientific claim is strong.

## Attack 1 — The claimed Class-A blind spot may not be a normative validator miss

**Attack:** M06 was previously presented as a formal duplicate-list-reference defect that all tools missed, but a generated COS mutation is not automatically a PDF/UA failure.

**Disposition:** Resolved by narrowing. The independent PyMuPDF/raw-COS audit confirms all seven active deltas, but the Matterhorn/Techniques review did not establish a dedicated duplicate-reference machine condition. M06 is now Class B and contributes no Class-A kill/survival rate. The paper reports only “no automated finding under the tested configurations.”

## Attack 2 — Four M09 records may be denominator repair by post hoc exclusion

**Attack:** The historical M09 records were once called invalid because RoleMap entries were unused, but Matterhorn says RoleMap checks apply regardless of tag use. Excluding them could look like removing inconvenient results.

**Disposition:** Mitigated, not erased. The old mutant bytes are unavailable, so neither the intended delta nor purity can now be re-audited. The records are retained in `data/exclusions.csv` as `EXCLUDED_UNVERIFIABLE_TARGET`, with the original rationale explicitly rejected. They are excluded from the active reachable-target denominator because their validity cannot be established, not because their validator outcomes were undesirable.

## Attack 3 — The second oracle is not independent for every operator

**Attack:** The generator uses pypdf, and the same generator-side assumptions may determine the mutation. M01/M02/M04/M05 still lack a second-route exact structural confirmation.

**Disposition:** Mitigated for active artifact validity. The completed v2 MuPDF/raw-COS audit confirms the intended operator-specific delta and whole-tree expected-result signature for all 69 active pairs, and independent rendering checks pass for all 69. This does not make the Class B semantic properties machine-checkable or imply that a validator is required to report them. The four historical M09 pairs remain unreproducible because their original mutant bytes are unavailable.

## Attack 4 — “Two independent coders” is unsupported

**Attack:** The CSV has two fields, but not auditable identities, human status, independence, blinding, or timing. Agreement statistics could be meaningless if both fields were produced by one process.

**Disposition:** Resolved by narrowing the public claim. The manuscript and README no longer report agreement/kappa as evidence of independent coding and make no independent-human double-coding claim. The raw role-labeled decision fields and adjudication are preserved as internal audit provenance; missing identities are an explicit limitation, not silently inferred.

## Attack 5 — Acrobat’s denominator is still easy to misread

**Attack:** Acrobat has 15 manual rows; a reader may compare 26/54 with 30/69 as if they were equivalent validator accuracy measures.

**Disposition:** Resolved in current generated analysis and source wording. Tables carry numerator, denominator, denominator definition, and manual counts; the paper states 26/54 automated decisions and keeps 15 manual-review rows separate. The metric is named mutation-specific detection/kill behavior, not accuracy or sensitivity in the population sense.

## Attack 6 — M10 is proxy detection, not direct target detection

**Attack:** The Acrobat Headers result can be an indirect consequence and may not prove the intended table-child rule was directly checked.

**Disposition:** Mitigated. The evidence schema distinguishes direct target, validated consequence proxy, collateral, baseline-carried, no-target, and manual-review outcomes. The proxy rule is structural and fixed before final adjudication; a proxy-separated sensitivity view remains available in generated analysis. The paper does not silently equate proxy and direct detection.

## Attack 7 — The corpus is clustered and narrow

**Attack:** Nine files from one reference-suite family cannot support general claims across authoring tools, genres, languages, or real-world production PDFs.

**Disposition:** Unavoidable limitation, disclosed. The paper keeps the Reference Suite because it supplies defensible reference baselines, states source clustering and the omitted 2-07 item, and does not add an unlicensed/random secondary corpus. Operator-level within-corpus evidence is the intended scope.

## Attack 8 — “Controls” are being inflated into specificity evidence

**Attack:** Eighteen no-op/benign controls are too small and too paired to estimate false-positive rates or specificity.

**Disposition:** Resolved by claim narrowing. `data/control_results.csv` reports paired count changes and persistent baseline findings. The paper calls them sanity checks/false-positive safeguards and does not estimate general specificity.

## Attack 9 — AT observations overreach

**Attack:** Nine observations from one observer and one NVDA/Acrobat/Windows configuration cannot establish representative or reproducible AT behavior.

**Disposition:** Resolved in wording, limited evidence remains. The paper now calls them illustrative exploratory observations, records versions/procedure/hashes, and keeps them secondary to formal validator results. They cannot support universal screen-reader claims.

## Attack 10 — PAC AI remains a scope distraction

**Attack:** Aggregate PAC-AI evidence cannot be mapped to mutant-specific outcomes and could undermine the central study.

**Disposition:** Resolved for the primary claim. PAC AI is absent from the abstract and formal rates; 34 rows remain separate and unresolved future work. The formal result survives without PAC AI.

## Attack 11 — Historical artifacts can still confuse reproduction

**Attack:** The repository contains old 23-mutant analyses, old submission directories, and generated artifacts with obsolete language.

**Disposition:** Mitigated, not fully cleaned. Historical files are retained for audit provenance, marked in notices, excluded from active scripts, and guarded by the submission audit. The current-facing README and manuscript source are checked for canonical counts and forbidden old wording. A public freeze should place historical material in a visibly archival path or exclude it from the submission bundle.

## Attack 12 — The manuscript PDF is not an accessible paper

**Attack:** A manuscript about PDF accessibility could still ship with weak or malformed tagging even when a PDF producer reports a tagged structure.

**Disposition:** Mitigated. The current Tectonic build reports `Tagged: yes`, contains `/Lang`, `/MarkInfo`, `/StructTreeRoot`, and title/subject metadata, and all four rendered pages were visually inspected. A venue-level PDF/UA check is still appropriate because structural presence does not prove semantic tag quality.

## Attack 13 — Release licensing is not automatically cleared by MIT

**Attack:** Corpus PDFs, derivatives, vendor reports, screenshots, and NVDA logs are not necessarily covered by the code license.

**Disposition:** Mitigated documentation; release clearance remains open. `DATA_LICENSES.md`, `CORPUS_LICENSES.md`, `LICENSES/README.md`, and `THIRD_PARTY_NOTICES.md` separate code from data/evidence and record the collection-level CC BY basis and provenance gap. A final public bundle must omit or clear artifacts whose item-level rights are not confirmed.

## Attack 14 — “Reference baseline” does not mean clean

**Attack:** Tool-specific baseline findings, especially G05 and G09, could be attributed to mutants or hidden in aggregate counts.

**Disposition:** Resolved for active classification. Baseline and mutant hashes/reports are paired; G05’s Acrobat finding is baseline-carried and G09-M08 is excluded for a documented baseline conflict. Current materials avoid “validator-clean golden.”

## Attack 15 — Tool configurations are not equivalent validators

**Attack:** PAC Formal, Acrobat Full Check/manual workflow, and veraPDF PDF/UA-1 are different products and scopes; a global ranking would be invalid.

**Disposition:** Resolved in current framing. The paper uses “PDF accessibility checking configurations,” records exact versions/settings, separates Acrobat manual rows, and reports operator-level behavior without a global winner.

## Attack 16 — Acrobat check-selection metadata is internally inconsistent

**Attack:** The recorded Acrobat metadata says “All 31 of 31 checks selected,” while the native control-session note says the UI displayed “31 of 32.” A reviewer could not tell which configuration generated the reports.

**Disposition:** Resolved for the canonical record without rewriting reports. The native-session note and G01 report context establish 31/32 as the run configuration; the old 31/31 metadata wording is retained in `historical_metadata_checked_categories` for provenance. The environment table exposes both.

## Attack 17 — The fresh PDF is readable but still not an accessible PDF artifact

**Attack:** The current Tectonic build reports a tagged structure, but the compiler still reports an 8.3pt overfull box in the generated results fragment, and tag semantics have not been checked by a full PDF/UA validator.

**Disposition:** Resolved for the local artifact gate, with venue-specific QA still open. The final four-page PDF is tagged, carries document/heading/paragraph/table/link structure, and has no remaining overfull-box warning in the generated results fragment. Visual inspection found no clipping, overlap, or unreadable table. A target venue's required PDF/UA checker remains outside this repository-only review.

## Attack 18 — Derived terminology is repaired but raw ledger labels can still mislead

**Attack:** Raw validator ledgers and coding packets retain `Missed`, and legacy scripts accept it as an input class. A reader who bypasses the current generated views could still misread Class B no-findings as ordinary misses.

**Disposition:** Mitigated, not eliminated. Raw labels are preserved for provenance; the current formal freeze now emits `interpreted_outcome`, current tables use `No target`, and the audit documents the distinction. A future schema migration could remove the ambiguity but would risk breaking historical traceability.

## Final classification

| Attack | Status |
|---|---|
| M06 normative overclaim | Resolved by Class B reclassification |
| M09 post hoc exclusion concern | Mitigated; historical bytes unavailable |
| Incomplete second-route structural oracle | Resolved for active artifacts; semantic interpretation remains bounded |
| Unsupported independent-coder claim | Resolved in wording; provenance remains open |
| Denominator and proxy ambiguity | Resolved/mitigated in generated evidence |
| Corpus clustering and AT scope | Unavoidable limitations, accurately stated |
| Historical artifact confusion | Mitigated; freeze packaging still required |
| Manuscript PDF accessibility | Current PDF reports Tagged=yes and includes language, metadata, and structure-tree entries; semantic PDF/UA acceptance remains venue-dependent |
| Licensing clearance | Release gate, not a scientific denominator defect |
| Acrobat check-selection discrepancy | Resolved for the canonical record as 31/32; older 31/31 wording preserved as historical provenance |

## Submission decision

The mutation-testing artifact and canonical formal analysis are defensible within the stated corpus/configuration scope, and the consistency gate passes. Remaining external gates are venue acceptance of the tagged PDF’s semantic quality, final raw-evidence redistribution clearance, and the user’s final clean commit/tag freeze. The missing coder identities are disclosed by omission of any independent-coding claim, and the Acrobat record is canonicalized to 31/32 with the older wording preserved. Do not hide these bounded limitations behind the 30/39 operator counts.
