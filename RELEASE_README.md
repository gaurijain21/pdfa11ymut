# PDFa11yMut historical release documentation

This file describes the historical 2026-09-24 study archive. The current paper freeze is `paper-freeze-v2`; this document is not its release manifest and must not be submitted or redistributed without rechecking artifact licenses and regenerating all derived outputs.

The primary formal scope is 69 active mutants and 207 classified validator rows across PAC Formal, Acrobat Full Check, and veraPDF. The negative-control ledger contains 18 `COMPLETE` rows with PAC, Acrobat, and veraPDF report hashes. Role-labeled decision fields and adjudication metadata are retained as internal audit provenance; no independent-human coding claim is made. The correction ledger preserves two post-coding PAC evidence-identity repairs without rewriting the original evidence. PAC-AI remains unresolved future work and is not included in formal conclusions.

Run from the extracted release directory:

```text
python reproduce.py
python -m unittest discover -s tests -p "test*.py" -q
python scripts/check_evidence.py
```

`reproduce.py` is verify-only. It does not regenerate mutants, rewrite canonical data, or modify raw evidence. Local PAC, Acrobat, veraPDF, Java, and other proprietary/runtime installers are intentionally excluded from this archive; the repository records the required versions and evidence metadata separately.
