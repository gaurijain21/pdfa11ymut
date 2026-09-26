# PDFa11yMut

PDFa11yMut is a controlled mutation-testing artifact for studying the boundary of automated PDF accessibility checking configurations. It starts from a reference-suite baseline PDF, applies a specified structure-level transformation, verifies the transformation with generator-side and scoped independent checks, checks exact visual preservation, and records validator evidence against the tested file hash.

It does not measure general accessibility accuracy, prove that a validator-clean PDF is accessible, or treat a semantic mutation outside a tool's stated automated scope as a validator failure.

## Current evidence status

Nine reference-suite PDFs are present and the pipeline has produced 73 valid verified generation records with parse, page/content, operator-specific, and exact 150-DPI rendering checks passing. G09-M08 and four historical M09 records remain excluded from active interpretation; three newly generated M09 candidates are documented separately and are not substitutes for historical validator evidence. The formal scope therefore remains 69 active mutants and 207 classified formal validator rows. PAC AI remains a separate aggregate-only future-work experiment; no PAC-AI detection or non-detection is reported.

The generation ledger contains 73 records and 72 materialized mutant PDFs; all 73 records are valid and verified, of which 69 are active after documented exclusions. The current formal outcomes are PAC 30 detections and 39 no-target findings, Acrobat 26 automated detections, 28 no-target findings, and 15 separate manual-check rows, and veraPDF 30 detections and 39 no-target findings. Any displayed rate uses only Detected/(Detected + no automated target finding) rows in the stated denominator; these are mutation-specific detection/kill rates, not full accuracy. Class A contains 30 mutants and Class B contains 39. No Class B mutant received an automated detection in the tested configurations; this is not a claim that every Class B property was machine-checkable. All 18 negative-control artifacts and all 18 PAC, Acrobat, and veraPDF control runs are hash-linked and complete. Formal rows retain paired baseline/mutant classifications, rationale, and adjudication metadata for auditability. The public study claim does not rely on independent-coder identities or an independent-human double-coding claim.

Nine selected NVDA observations are complete as illustrative exploratory evidence from one observer under one fixed NVDA/Acrobat/Windows configuration. A clean paired rerun confirms the M01 reading-order effect: the golden announces the logo first, while the mutant announces the address block first. M08 preserves the observed no-difference result. AT observations are separate from validator detection rates. The fresh M01 Speech Viewer captures and prior session log are preserved under `evidence/at/nvda/`; screenshots remain targeted evidence rather than a universal user-study claim.

The current manuscript source and PDF are hash-linked in `STUDY_MANIFEST.json`. The PDF was rebuilt with Tectonic 0.17.0 and visually inspected. It contains document language, title/subject metadata, `/MarkInfo`, and a `/StructTreeRoot`, but the 2026-09-25 semantic review found no usable document/heading/paragraph tree. It is not yet a venue-ready PDF/UA submission artifact; see `docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`. The prior PDF is archived under `paper/archive/pre_current_rebuild/`.

## Experimental model

- Class A: machine-checkable/conformance-oriented defects, such as heading hierarchy, missing figure alternate text, missing language metadata, invalid role mapping, and illegal table-child roles.
- Class B: semantic/human-judgment/assistive-representation defects, including reading-order swaps, omissions, marked-content association swaps, internal MCID-order reversal, and the structurally confirmed duplicate list-item reference. These are reported as surviving/no automated finding unless a validator explicitly claims the property.

The complete preconditions, transformations, invariants, standards mappings, controls, and evidence fields are in [`operators/operators.yaml`](operators/operators.yaml).

## Layout

```text
corpus/golden/                 immutable source PDFs supplied with provenance
corpus/mutants/                generated PDFs (never hand edited)
operators/operators.yaml       operator specifications M01-M10
pdfa11ymut/                    generator and validator-independent verifier
data/mutants.jsonl             generation and verification manifest
data/validator_runs.csv        canonical validator evidence schema
data/at_observations.csv       canonical AT observation schema
data/corpus_inventory.csv      corpus provenance and baseline schema
evidence/                      raw reports, screenshots, and verification JSON
analysis/generated/            outputs generated only from canonical data
paper/                         active manuscript source
scripts/                       reproduction and analysis commands
```

## Install and run

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

Generate and verify one mutant after placing a licensed input at `corpus/golden/G01.pdf`:

```text
python -m pdfa11ymut generate --input corpus/golden/G01.pdf --operator M03 --target auto --output corpus/mutants/G01-M03.pdf
```

For scratch regeneration of every applicable operator, use the isolated command:

```text
python scripts/regenerate_scratch.py
```

The scratch command refuses missing targets, writes only to a temporary directory, performs parseability/page/content/structure checks, renders both PDFs with Poppler `pdftoppm` at 150 DPI, and uses exact RGB pixel equality. The legacy `python -m pdfa11ymut generate-all` command is a final-freeze writer and must not be used as a verification command.

Rebuild active analysis as an explicit freeze step:

```text
python scripts/rebuild_analysis.py
python -m pdfa11ymut manual-plan
python scripts/audit_submission.py
```

The analysis never reads the historical summary tables. Formal results are generated into `analysis/generated/`; PAC AI remains separate and unresolved, while AT observations are retained as qualitative evidence rather than merged into rates.

Check hash-named evidence after manual runs:

```text
python scripts/check_evidence.py
```

## Validator and AT runs

PAC Formal, PAC AI, Acrobat, and NVDA are GUI/manual configurations in this environment. PAC Formal, Acrobat, and veraPDF evidence has been ingested with raw report hashes, versions, profiles, and baseline-relative classifications. The 18-control native evidence is linked by [`data/controls.csv`](data/controls.csv) and can be re-ingested with `python scripts/ingest_control_evidence.py`. [`MANUAL_VALIDATION_PROTOCOL.md`](MANUAL_VALIDATION_PROTOCOL.md) gives the exact procedures and ingestion commands for reruns or extensions; do not type summary detection sets.

PAC Formal and PAC AI are separate configurations. AI findings are never merged with formal PDF/UA failures. AT observations are evidence of observed representation under a named AT/version, not universal user-study results.

## Reproduction boundary

`python reproduce.py` is verify-only: it checks dependencies, canonical hashes, freeze counts, report hashes, and evidence completeness without generating mutants or rewriting analysis. Use `python scripts/regenerate_scratch.py` for temporary regeneration and `python scripts/build_study_freeze.py` for an explicit final-freeze update.

## Paper status

The active paper source is [`paper/pdfa11ymut_ieee.tex`](paper/pdfa11ymut_ieee.tex). Its results fragment is generated from canonical data by `scripts/rebuild_analysis.py`; it separates conformance from semantics, documents the PAC-AI limitation, narrows M06 to Class B, and explains the historical M09 exclusions. `arxiv_submission/` and the historical release package retain prior artifacts and must not be submitted without regeneration.

## Licensing

Code is MIT-licensed. PDFs, validator reports, screenshots, and third-party assets require separate documented permission. See [`CORPUS_LICENSES.md`](CORPUS_LICENSES.md), [`data/corpus_inventory.csv`](data/corpus_inventory.csv), and [`data/corpus_provenance_sources.csv`](data/corpus_provenance_sources.csv). The nine working PDFs are mapped to the PDF/UA Reference Suite and the collection-level CC BY 4.0 terms are recorded; the historical download archive and timestamp were not retained.

## Quality gate

Use [`PRE_SUBMISSION_CHECKLIST.md`](PRE_SUBMISSION_CHECKLIST.md), [`FINAL_REVIEWER_ATTACK.md`](FINAL_REVIEWER_ATTACK.md), and [`CONTRIBUTION_EVIDENCE_MATRIX.md`](CONTRIBUTION_EVIDENCE_MATRIX.md) before submission. The current status is **CANONICAL DATA RECONCILED, PUBLIC RAW-EVIDENCE EXCLUSION RECORDED, SEMANTIC PDF/UA REVIEW OPEN**: the study data gate passes and the public bundle excludes raw vendor/AT evidence, while the manuscript PDF still needs a semantic tagging rebuild before venue submission. This is a scoped mutation-specific study, not a claim of general validator accuracy. PAC AI remains optional future work; corpus mapping and collection-level licensing are documented, with the unretained historical download archive recorded as a limitation. Historical ZIP packages must not be submitted without regeneration from the canonical manifest.
