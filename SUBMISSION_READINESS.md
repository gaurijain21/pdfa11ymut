# Submission readiness

This is the current reviewer-facing readiness summary for PDFa11yMut. Historical checklists and attack reports are preserved under `archive/research_history/` and do not override the files or gates described here.

## Scientific state

The canonical frozen study contains:

- 9 reference PDFs and 10 structure-level operators.
- 73 generation-ledger records; 71 materialized mutant PDFs, including the auxiliary AT artifact.
- 5 documented exclusions: 4 within the valid-generation manifest and 1 historical exclusion-only/non-materialized record.
- 69 active independently re-audited mutants: 30 Class A and 39 Class B.
- 207 active checker-configuration rows across PAC Formal, Acrobat Full Check, and veraPDF PDF/UA-1.
- 18 paired no-op/benign controls; none produced a new target-relevant automated finding under the paired count comparison.
- 9 exploratory AT observations: 8 active-formal-mutant cases and 1 auxiliary M01 assistive-representation demonstration. Eight of nine selected pairs showed an observed difference; M08 did not.

Class A is the scored conformance-oriented set. Class B is descriptive and is not assigned an automated detection rate. M06 remains Class B. Acrobat's Class-A result is reported as 23 direct findings plus 3 prespecified M10 consequence-proxy findings; the proxy is not hidden inside the direct count.

## Public reproduction boundary

The public/open layer includes the mutation framework, structural and purity checks, generated analysis, sanitized evidence metadata, hashes, tests, and CI. Reviewers should run:

```powershell
python -m unittest discover -s tests -p "test*.py" -q
python scripts/regenerate_scratch.py
python scripts/rebuild_analysis.py
python scripts/verify_study_state.py --verify
python scripts/check_evidence.py
python scripts/audit_submission.py
```

PAC, Acrobat, and NVDA recollection requires authorized native applications and the recorded versions/settings. Raw vendor and AT report bytes are intentionally excluded from the public bundle; `data/public_evidence_records.csv` supplies sanitized classifications, hashes, rule identifiers, and rationales.

## Current gates

The final ship pass requires the unit tests, CSV/schema audit, evidence hash check, generated-file check, manuscript compilation/render review, clean working tree, and public synchronization to pass. Venue-specific anonymity, PDF/UA acceptance, and supplemental-artifact policies remain submission-stage decisions.
