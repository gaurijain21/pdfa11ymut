# Verification of first-pass dispositions

The first-pass issue numbers below refer to `SUBMISSION_AUDIT.md`. Statuses are based on independent inspection of the current files, not on the first-pass prose alone.

| Prior issue | Claimed status in first pass | Evidence inspected | Actual status |
|---|---|---|---|
| 1. Version mismatch / stale 23-mutant artifacts | Repaired with manifest and guards | `STUDY_MANIFEST.json`, current README/paper, historical notices, audit gate | PARTIALLY VERIFIED: active path is guarded; archival files remain |
| 2. Mutation framework reproducibility | Repaired with scripts/docs | `README.md`, `docs/REPRODUCIBILITY.md`, fresh-copy run | VERIFIED |
| 3. Class-B terminology | Repaired in generated views/paper | formal freeze, results fragment, paper | VERIFIED: raw legacy labels remain provenance-only |
| 4. Rate denominators | Repaired | `analysis/generated/overall_rates.csv`, results fragment, audit logic | VERIFIED |
| 5. Independent structural ground truth | Upgraded with MuPDF route | `evidence/independent_verification_v2/`, `scripts/independent_audit.py` | PARTIALLY VERIFIED: strong artifact route, not universal semantic independence |
| 6. Purity / allowed-delta manifest | Added | `data/mutant_delta_manifest.jsonl`, independent records | VERIFIED for active records |
| 7. Target selection bias | Added selection metadata | `data/operator_target_selection.csv`, `operators/operators.yaml` | PARTIALLY VERIFIED: deterministic metadata exists; no alternate-site experiment was needed to change the primary denominator |
| 8. Corpus clustering | Disclosed limitation | inventory, provenance, paper Threats | INHERENT LIMITATION |
| 9. Evidence completeness | Hash-linked evidence added | `check_evidence.py`, validator manifests, checksum snapshot | VERIFIED for prescribed evidence; exploratory M01 remains outside formal corpus |
| 10. Coder independence | Public claim removed | double-coding manifest/packets, paper | VERIFIED as a claim narrowing; independent identities remain unavailable |
| 11. “Predeclared” wording | Replaced with fixed-before-adjudication wording | paper, classification protocol | VERIFIED |
| 12. Direct/proxy detection | Taxonomy added | formal freeze, validator ledger, generated analysis | VERIFIED |
| 13. Standards mapping | All-operator mapping added | `data/operator_standard_mapping.csv`, standards review | PARTIALLY VERIFIED: mappings are bounded to reviewed authoritative material |
| 14. M06 validity | Dedicated falsification audit and Class-B reclassification | `docs/M06_VALIDITY_AUDIT.md`, v2 records | VERIFIED for structural claim; normative obligation intentionally not claimed |
| 15. AT evidence strength | Scoped to exploratory observations | AT data/logs, paper | VERIFIED |
| 16. AT selection | Metadata corrected and rationale retained | `data/at_selection.csv`, paper | VERIFIED |
| 17. Disagreement decomposition | Generated decomposition | `analysis/generated/disagreement_analysis.csv`, paper | VERIFIED |
| 18. Negative controls | Paired results ledger added | `data/control_results.csv`, control reports | VERIFIED as descriptive paired evidence |
| 19. Mutation-testing literature | Foundational citations retained/expanded | paper bibliography, related work | PARTIALLY VERIFIED: literature positioning is scoped, not exhaustive |
| 20. Novelty wording | Narrow contribution wording | paper, contribution matrix, literature note | VERIFIED |
| 21. PAC-AI core claim | Removed from formal claims | abstract, paper, PAC-AI data | VERIFIED |
| 22. Baseline provenance | Canonical provenance views added | corpus inventory/provenance, manifest | VERIFIED with acquisition-archive limitation |
| 23. “Validator-clean golden” wording | Replaced in active paper | paper, README, audit guard | VERIFIED: remaining generic “validator-clean PDF” wording is qualified |
| 24. Exact environment | Environment table added | `data/validator_environment.csv`, reproduction docs | PARTIALLY VERIFIED: unavailable tools and historical configuration differences remain disclosed |
| 25. Three configurations | Configuration-scoped terminology | paper, capability mapping | VERIFIED |
| 26. Paper PDF accessibility | Tagged rebuild and QA | compiled PDF, `docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md` | PARTIALLY VERIFIED: structural gate passes; venue-level PDF/UA review remains |
| 27. Related-work breadth | Sources and current tool check | paper, `docs/LITERATURE_TOOL_LANDSCAPE_2026-09-25.md` | VERIFIED for the stated scope |
| 28. Operator-level results | Generated operator tables retained | results fragment, figures, paper | VERIFIED |
| 29. Class-B framing | Class-B vocabulary separated | operator specs, formal freeze, paper | VERIFIED |
| 30. Licensing/release hygiene | Release policy and manifest added | `release/CURRENT_RELEASE_POLICY.md`, public manifest, notices | PARTIALLY VERIFIED: item-level redistribution clearance remains a release gate |

The only remaining non-scientific gates are venue-level PDF accessibility review, item-level evidence redistribution clearance, and preserving the local freeze identity before any future commit or push. No push was performed.
