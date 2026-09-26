# Manuscript PDF accessibility QA

The manuscript is produced from `paper/pdfa11ymut_ieee.tex` with the IEEE conference LaTeX layout. The current local PDF was inspected visually as a four-page artifact and with `pdfinfo`/pypdf.

Current inspection:

- visual rendering: readable four-page IEEE-style layout;
- tagged PDF: `yes`;
- document language: `/Lang` is `en-US`;
- structure metadata: `/MarkInfo` is present and `/StructTreeRoot` is present;
- title metadata: `/Title` and `/Subject` are present;
- final build: completed with local Tectonic 0.17.0 after explicit low-level semantic tagging; all four rendered pages were visually inspected.

## Semantic review result (2026-09-25)

The local venue-style semantic review **passes**. Direct inspection of the
structure tree found a document root, heading hierarchy, paragraphs, captions,
tables, rows, header cells, data cells, and links. This is a bounded local gate,
not a universal PDF/UA-conformance claim; apply the chosen venue's policy
before submission.

The full review, including the exact commands and the final structure counts,
is recorded in
[`SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`](SEMANTIC_PDF_UA_REVIEW_2026-09-25.md).
