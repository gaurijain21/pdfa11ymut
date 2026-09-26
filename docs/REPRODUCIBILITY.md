# Reproducibility protocol

Run commands from the repository root (`C:\Gauri\ma11ypdf`) with the recorded Python environment and local validator evidence available.

## Canonical regeneration and checks

```powershell
python scripts/build_study_manifest.py
python scripts/rebuild_analysis.py
python scripts/build_formal_freeze.py
python scripts/independent_audit.py
python scripts/verify_study_state.py --verify
python scripts/check_evidence.py
python scripts/audit_submission.py
python -m unittest discover -s tests -p "test*.py" -q
```

`build_study_manifest.py` derives the canonical manifest and machine-readable provenance, exclusions, mapping, target-selection, control, and environment views. `rebuild_analysis.py` derives current result tables from `data/mutants.jsonl`, `data/mutant_exclusions.csv`, and the hash-linked validator ledger; it does not read `data/pdfa11ymut_*` historical summaries. `independent_audit.py` never rewrites PDFs or reclassifies validator rows.

## Rebuilding the manuscript

The current working tree includes a local Tectonic 0.17.0 executable used for the validated manuscript build:

```powershell
New-Item -ItemType Directory -Force tmp/paper_build_current
tmp/tectonic/bin/tectonic.exe --keep-logs --outdir tmp/paper_build_current paper/pdfa11ymut_ieee.tex
Copy-Item tmp/paper_build_current/pdfa11ymut_ieee.pdf paper/pdfa11ymut_ieee.pdf
```

Before replacing a paper PDF, render all pages with Poppler `pdftoppm`, inspect the images, and check `pdfinfo` plus pypdf for `Tagged`, `/Lang`, `/MarkInfo`, and `/StructTreeRoot`. The current build is visually inspected and reports tagged structural metadata; semantic PDF/UA quality still requires venue-level checking.

## Evidence requirements

Every active formal row must have a source and mutant SHA-256, validator/build/profile metadata, a raw report path and report hash, baseline-relative status, a classification reason, and the preserved role-labeled coding/adjudication fields. These fields are audit provenance, not evidence of independent human coding. `scripts/audit_submission.py` fails if any required relationship is missing or inconsistent.

## Reproducing validators

The repository retains native reports and run metadata rather than assuming current installations are equivalent. PAC Formal used PAC 26.1.0.0 with AI disabled; Acrobat used Accessibility Full Check 2026.002.21931 with all pages and no auto-tagging. The canonical configuration record uses 31/32 selected checks, supported by the preserved native-session note and G01 report context; the older 31/31 metadata wording remains as historical provenance. veraPDF used Greenfield 1.30.2 with the PDF/UA-1 `ua1` profile and the repository-local Java launcher. See `data/validator_environment.csv` and the source metadata JSON files for settings. This reconciliation changes documentation only; no Acrobat reports or classifications were rewritten.

## Freeze discipline

The current manifest records the Git HEAD, worktree state, manuscript source/PDF hashes, and its own audit-derived status. A submission freeze should be made only after the manuscript has been regenerated from the canonical outputs, the final consistency audit passes, and the exact commit plus manifest hash are recorded. The recommended tag is `paper-freeze-v1`; no tag or release is created by this audit automatically.
