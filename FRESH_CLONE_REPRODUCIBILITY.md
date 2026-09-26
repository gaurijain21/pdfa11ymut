# Fresh-copy reproducibility test

Date: 2026-09-25. The test was performed in a temporary copy of the pushed candidate artifact, separate from the working checkout. It validates the public repository state at the recorded release commit; PAC, Acrobat, and NVDA GUI reruns were not attempted because those native applications and raw evidence are intentionally outside the public clone boundary.

## Commands

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
python scripts/build_study_manifest.py
python scripts/rebuild_analysis.py
python scripts/independent_audit.py
python scripts/verify_study_state.py --verify
python scripts/check_evidence.py
python scripts/build_second_pass_artifacts.py
python scripts/audit_submission.py
python -m unittest discover -s tests -p "test*.py" -q
```

When the bundled local manuscript tool is present:

```powershell
tmp/tectonic/bin/tectonic.exe --keep-logs --outdir tmp/paper_build_current paper/pdfa11ymut_ieee.tex
```

## Results

| Layer | Result | Boundary |
|---|---|---|
| Dependency installation | Documented; not repeated against the network during this audit | Requires Python and package-index access |
| Canonical manifest/analysis rebuild | PASS in the fresh copy | Regenerates derived files, not GUI reports |
| Independent artifact audit | PASS for the archived 69 active pairs | Requires PyMuPDF and retained PDFs |
| Evidence/hash completeness | PASS in the authorized evidence checkout: 173 prescribed validator files | The public clone contains hashes and sanitized metadata, not proprietary vendor/AT report bytes |
| Submission consistency gate | PASS in the final gate run | Fail-closed on canonical relationships |
| Unit tests | PASS | Test count can vary with repository revision |
| Manuscript compilation | Supported by bundled Tectonic 0.17.0 when present; venue PDF/UA semantics remain separate | Toolchain availability is an environment prerequisite |
| PAC Formal / Acrobat / veraPDF recollection | Not rerun | Native reports, versions, settings, and hashes are archived |
| NVDA/AT recollection | Not rerun | Logs, transcripts, versions, and captures are archived |

## Reproduction boundary

Analysis reproduction means the public canonical data and authorized archived evidence can regenerate tables, figures, rates, exclusions, and robustness views. The public clone can reproduce the analysis layer but cannot recollect proprietary external-validator or AT evidence. A changed raw report, PDF, or canonical ledger must fail the checksum/audit gate before release.
