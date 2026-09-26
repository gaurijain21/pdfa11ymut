# External-gate status

The experimental corpus and mutation set are ready. The following gates are resolved for the current scoped study and public bundle; any future release that expands the scope must reopen the stated external checks:

1. **Resolved and verified 2026-09-24:** the nine local `PDFUA-Ref-2-*` files map to items 2-01 through 2-06 and 2-08 through 2-10, with exact filename and local SHA-256 checks recorded in [`data/provenance_verification_2026-09-24.md`](data/provenance_verification_2026-09-24.md). The omitted 2-07 item is the Nordic Council of Ministers / TemaNord 2016 publication and is not part of this corpus.
2. **Resolved and verified 2026-09-24 at collection level:** the official PDF Association page states that the suite is freely available under CC BY 4.0 and identifies the contributing organizations. Per-file descriptive attribution and reproducible mirror URLs are recorded in [`data/corpus_provenance_sources.csv`](data/corpus_provenance_sources.csv).
3. **Resolved for this study:** the local PDFs are documented as the PDF/UA reference files used here. The repository records the collection license and attribution text; it does not claim that the historical download archive or timestamp was preserved.
4. **Documented limitation:** the inventory records `PDF/UA-1 (collection-level)` because the source page provides a collection-level conformance statement, not a per-file conformance manifest. Do not upgrade this field without file-level source evidence.
5. The formal validator stage and the 207-case role-labeled classification/adjudication stage are complete for PAC Formal, Acrobat Full Check, and veraPDF in the canonical data. This is retained as audit provenance, not presented as independently identified human coding. Do not rerun or overwrite those reports unless a new, explicitly versioned study run is intended. The final queue and adjudication are recorded in [`data/double_coding_queue.csv`](data/double_coding_queue.csv), with the original decision files and correction ledger preserved for audit.
6. Do not convert the deferred PAC AI cohort into detections or non-detections. The PAC AI selection file contains 42 intentionally deferred queue rows, and the classification file contains 34 review-required aggregate-only records plus one remaining TODO. A future PAC build/interface must expose semantic finding identity/text and a reproducible semantic export/API before that phase can be reopened.
7. The nine selected NVDA observations are now recorded as single-observer illustrative exploratory observations. A clean paired M01 rerun is complete and preserved with separate Speech Viewer captures; the historical instability remains disclosed as context rather than deleted. The historical G02-M04 case is permanently excluded; the current local M04 observation is separate.
8. Resolved: the clean M01 rerun was completed through the native Acrobat/NVDA bridge with hash-verified golden and mutant inputs and separate Speech Viewer captures. The historical instability and the single-observer limitation remain documented; do not treat this pilot as a universal AT result.

9. **Resolved for the current public bundle:** raw PAC, Acrobat, veraPDF, NVDA, and Speech Viewer reports, screenshots, and logs are explicitly excluded. No vendor or participant redistribution clearance is claimed or required for excluded bytes. Hashes, protocols, classifications, and observation summaries remain in the public manifest/data. See [`release/CURRENT_RELEASE_POLICY.md`](release/CURRENT_RELEASE_POLICY.md) and [`release/PUBLIC_RELEASE_EXCLUSION_LEDGER.md`](release/PUBLIC_RELEASE_EXCLUSION_LEDGER.md).
10. **Still venue-dependent:** the local manuscript PDF review found that the current tagged PDF has metadata and link tags but lacks a usable document/heading/paragraph semantic tree. It is not yet a venue-ready PDF/UA submission artifact. See [`docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`](docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md).
## veraPDF setup

Use the official stable Greenfield release from the [veraPDF software downloads](https://software.verapdf.org/) page and its [installation instructions](https://docs.verapdf.org/install/). Do not use a development build for this experiment. The official Windows package contains `vera-install.bat`; run that supplied installer and choose a stable location such as `C:\\Tools\\veraPDF\\<version>`. The CLI should then be under the installation `bin` directory, for example `C:\\Tools\\veraPDF\\<version>\\bin\\verapdf.bat`.

Test the executable with the documented Windows help/version commands:

```text
"C:\\Tools\\veraPDF\\<version>\\bin\\verapdf.bat" --version
"C:\\Tools\\veraPDF\\<version>\\bin\\verapdf.bat" --help
```

Then run the project batch:

```text
python scripts/run_verapdf_batch.py --executable "C:\\Tools\\veraPDF\\<version>\\bin\\verapdf.bat"
```

The project runner used PDF/UA-1 `ua1` JSON for the recorded formal batch and preserved the raw reports and run metadata. A future rerun should use a new versioned evidence directory; no per-file veraPDF manual work is required.

No mutation should be interpreted as a validator detection until its matching golden baseline exists for the same validator configuration.
