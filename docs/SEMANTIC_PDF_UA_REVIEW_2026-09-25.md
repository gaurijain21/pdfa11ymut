# Semantic PDF/UA review of the manuscript PDF

Date: 2026-09-25  
Artifact: `paper/pdfa11ymut_ieee.pdf`  
Scope: local venue-style semantic review of the current IEEE-format working draft; no target venue was specified.

## Result

**FAIL / not venue-ready.** The PDF is visually readable and contains basic
tagging metadata, but the body is not represented by a defensible semantic
structure tree. A venue-specific PDF/UA review must be rerun after a modern
tagging rebuild.

## Checks performed

- `pdfinfo` reports four pages, `Tagged: yes`, no encryption, and no JavaScript.
- The catalog contains `/Lang` (`en-US`), `/MarkInfo` with `/Marked true`,
  `/StructTreeRoot`, `/Outlines`, and `/PageLabels`.
- `/Title` and `/Subject` metadata are present.
- Poppler rendered all four pages at 150 DPI; visual inspection found no
  clipping, overlap, missing glyphs, or unreadable table.
- A pypdf structure-tree walk found sixteen `/Link` structure elements but no
  usable `/Document`, heading, paragraph, list, or table structure for the
  manuscript body. The links are attached directly under the structure root.

## Interpretation

The current file is tagged in the narrow structural sense reported by
`pdfinfo`, but that is insufficient for semantic PDF/UA acceptance. In
particular, the current tree does not support a credible heading/navigation
hierarchy or paragraph-level reading order. The result must not be described
as PDF/UA-conformant or venue-accessible solely because `Tagged: yes` is
reported.

## Rebuild limitation

The Codex built-in LaTeX compiler was unavailable in this host. A local
MiKTeX retry with `xelatex --disable-installer` failed because
`pdfmanagement-testphase.sty` is not installed. A source-only tagging change
was therefore reverted, and the known-good PDF was not overwritten.

## Required close-out action

Rebuild with a current LaTeX tagging stack (preferably a current LuaLaTeX/
LaTeX release with `\\DocumentMetadata{tagging=on}` and supported IEEEtran
tagging), then repeat the structure-tree inspection, PAC/veraPDF semantic
checks, page rendering, and manual reading-order/table review. Record the
final PDF hash and the target venue's PDF accessibility policy before calling
the manuscript submission-ready.
