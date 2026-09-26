# Manuscript PDF accessibility QA

The manuscript is produced from `paper/pdfa11ymut_ieee.tex` with the IEEE conference LaTeX layout. The current local PDF was inspected visually as a four-page artifact and with `pdfinfo`/pypdf.

Current inspection:

- visual rendering: readable four-page IEEE-style layout;
- tagged PDF: `yes`;
- document language: `/Lang` is `en-US`;
- structure metadata: `/MarkInfo` is present and `/StructTreeRoot` is present;
- title metadata: `/Title` and `/Subject` are present;
- final known-good build: completed with local Tectonic 0.17.0 before the current semantic audit; all four rendered pages were visually inspected.

## Semantic review result (2026-09-25)

The local venue-style semantic review is **not passed**. Direct inspection of
the structure tree found `/StructTreeRoot` and sixteen `/Link` structure
elements, but no usable `/Document`, heading, paragraph, list, or table
structure for the manuscript body. The PDF therefore has structural metadata
and link tagging without a defensible semantic reading-order tree. Metadata
presence must not be reported as PDF/UA conformance.

The full review, including the exact commands and the failed compiler
diagnostic, is recorded in
[`SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`](SEMANTIC_PDF_UA_REVIEW_2026-09-25.md).
The installed MiKTeX distribution could not rebuild the source because
`pdfmanagement-testphase.sty` is unavailable, and the built-in compiler was
unavailable in this host. The known-good PDF was kept unchanged; no
source/PDF mismatch was committed.
