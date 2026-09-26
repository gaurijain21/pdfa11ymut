# Second-pass state audit and final consolidation handoff

Audit date: 2026-09-26 (America/Los_Angeles)

The user-requested working directory is an empty staging checkout. The populated scientific checkout audited here is `C:\Gauri\ma11ypdf`; its final freeze is created only after the repairs recorded in `FINAL_CONSOLIDATION_AUDIT.md`.

## Repository identity

| Field | Value |
|---|---|
| Branch | `main` |
| HEAD before final consolidation | `2e86edb` (`Strengthen reviewer readiness and reproducibility disclosures`) |
| Historical tag | `paper-freeze-v1` (immutable; retains the earlier anonymous manuscript) |
| Working tree before final consolidation | Clean |
| Remote relation before final consolidation | `main` matched `origin/main` at the audited starting point |
| Release status | Final v2 commit/tag is pending this consolidation pass; raw vendor/AT evidence remains excluded from any public bundle |

## Canonical experiment

| Quantity | Canonical value | Evidence |
|---|---:|---|
| Reference baselines | 9 | `data/corpus_inventory.csv`, `corpus/golden/` |
| Operators | M01--M10 (10) | `operators/operators.yaml` |
| Valid verified generation records | 73 | `data/mutants.jsonl`, `STUDY_MANIFEST.json` |
| Materialized mutant PDFs | 72 | manifest notes; one exploratory/history record is not materialized in the canonical mutant folder |
| Documented exclusion rows | 5 | `data/exclusions.csv`, `data/mutant_exclusions.csv` |
| Active mutants | 69 | `data/mutants.jsonl` minus documented exclusions |
| Active formal validator rows | 207 | 69 mutants x PAC, Acrobat, veraPDF |
| Controls | 18 | 9 no-op + 9 benign; `data/control_results.csv` |
| AT cases | 9 | `data/at_observations.csv`; one fixed NVDA/Acrobat configuration |

Class A has 30 active mutants (M03, M07--M10); Class B has 39 (M01, M02, M04--M06). Formal configurations are PAC Formal 26.1.0.0, Acrobat Full Check 2026.002.21931, and veraPDF 1.30.2 with PDF/UA-1 `ua1`. Acrobat manual-review rows remain separate from automated detections.

## Active paper

The manuscript currently representing the study is `paper/pdfa11ymut_ieee.tex`, with compiled artifact `paper/pdfa11ymut_ieee.pdf`. `arxiv_submission/` is not the active source. The current source and PDF are hash-linked in the manifest regenerated after the final second-pass edits.

## State conclusion

The canonical scientific state is 9 baselines / 10 operators / 73 valid verified generation records / 69 active mutants / 207 formal rows / 18 controls / 9 exploratory AT cases. Historical 23-mutant summaries are not active inputs. Principal release caveats are post-discovery exclusions for unavailable M09 bytes and one baseline conflict, collection-level corpus provenance without the original acquisition archive, and external-validator/AT evidence that cannot be recreated solely from open-source commands. The public clone reproduces analysis and integrity checks; authorized native evidence is retained separately.
