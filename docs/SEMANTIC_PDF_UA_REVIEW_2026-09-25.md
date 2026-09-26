# Semantic PDF/UA review of the manuscript PDF

Date: 2026-09-25  
Artifact: `paper/pdfa11ymut_ieee.pdf`  
Scope: local venue-style semantic review of the current IEEE-format working draft; no target venue was specified.

## Result

**PASS for the local semantic gate; venue-specific policy remains open.** The
final four-page PDF is visually readable and carries an explicit semantic
structure tree for the document, headings, paragraphs, captions, tables, rows,
header cells, data cells, and links. This is a bounded artifact review, not a
claim of universal PDF/UA conformance or approval by an unspecified venue.

## Checks performed

- `pdfinfo` reports four pages, `Tagged: yes`, no encryption, and no JavaScript.
- The catalog contains `/Lang` (`en-US`), `/MarkInfo` with `/Marked true`,
  `/StructTreeRoot`, `/Outlines`, and `/PageLabels`.
- `/Title` and `/Subject` metadata are present.
- Poppler rendered all four pages at 150 DPI; visual inspection found no
  clipping, overlap, missing glyphs, or unreadable table.
- A pypdf structure-tree walk found `/Document`, 10 `/H1`, 1 `/H2`, 24 `/P`,
  1 `/L` with 4 `/LI` and 4 `/LBody`, 3 `/Table`, 3 `/Caption`, 22 `/TR`,
  21 `/TH`, 140 `/TD`, and 16 `/Link` elements. Each table has a caption and
  row children; every row has explicit header/data-cell children.
- The PDF was rebuilt with local Tectonic 0.17.0 using tagpdf's low-level API,
  because the bundled 2022 LaTeX format does not support the newer
  `\\DocumentMetadata{tagging=on}` key.

## Interpretation

The local semantic gate is closed for this artifact: the former failure mode
(links only under the structure root) is gone. The document is not described
as universally PDF/UA-conformant because no venue was named and no external
vendor validator clearance is being claimed for the excluded raw evidence.
Before submission, apply the chosen venue's current PDF/UA policy and rerun its
required checker if one is specified.

## Final artifact identity

- PDF SHA-256: `3d2b7bcf245adfabaa0049d3c792c793f158af3a5210dffe5d1e6e028ad9691f`
- Source: `paper/pdfa11ymut_ieee.tex`
- Generated results: `analysis/generated/results_fragment.tex`
