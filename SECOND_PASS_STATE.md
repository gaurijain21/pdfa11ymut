# Second-pass state audit

Audit date: 2026-09-25 (America/Los_Angeles)

The user-requested working directory (path intentionally omitted from the release artifact) is not the scientific checkout: it has no commits and contains only the master prompt plus temporary page images. The actual artifact audited here is the local candidate checkout.

## Repository identity

| Field | Value |
|---|---|
| Branch | `main` |
| HEAD | `c94f4a33d01ded6be5b5a593041788bda1fc7768` (`Record final manifest identity`) |
| Tag | `paper-freeze-v1` |
| Working tree | Dirty after this second-pass artifact generation; pre-audit checkout was clean |
| Remote relation | `main` is six commits ahead of `origin/main` (`origin/main`=`7b78a42`) |
| Release status | The repaired study and freeze artifacts are committed and pushed to `origin/main`; raw vendor/AT evidence remains excluded from the public freeze |

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
