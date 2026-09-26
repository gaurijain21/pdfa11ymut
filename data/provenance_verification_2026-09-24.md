# Corpus provenance verification — 2026-09-24

## Result

The nine local golden PDFs used by the formal study are confirmed as the nine-file local subset of the PDF Association PDF/UA-1 Reference Suite 1.1: items 2-01 through 2-06 and 2-08 through 2-10. Each local filename exactly matches the corresponding public-suite filename recorded in [`corpus_provenance_sources.csv`](corpus_provenance_sources.csv), and all nine local SHA-256 values match [`corpus_inventory.csv`](corpus_inventory.csv).

The PDF Association's official suite page identifies the resource as the PDF/UA-1 Reference Suite 1.1, describes a ten-document suite, names the contributing organizations, and states that the suite is freely available under CC BY 4.0:

<https://pdfa.org/resource/pdfua-reference-suite/>

The recorded public mirror URLs are retained as reproducible source URLs; web inspection resolved the corresponding named PDF resources where previewable, while two larger PDFs exceeded the preview service's content limit. The mirror is not treated as evidence of the historical acquisition path or as a byte-for-byte comparison against the unretained original download.

## Confirmed local mappings

| Suite item | Local filename | Local SHA-256 verified |
|---|---|---|
| PDFUA-Ref-2-01 | `PDFUA-Ref-2-01_Magazine-danish.pdf` | yes |
| PDFUA-Ref-2-02 | `PDFUA-Ref-2-02_Invoice.pdf` | yes |
| PDFUA-Ref-2-03 | `PDFUA-Ref-2-03_AcademicAbstract.pdf` | yes |
| PDFUA-Ref-2-04 | `PDFUA-Ref-2-04_Presentation.pdf` | yes |
| PDFUA-Ref-2-05 | `PDFUA-Ref-2-05_BookChapter-german.pdf` | yes |
| PDFUA-Ref-2-06 | `PDFUA-Ref-2-06_Brochure.pdf` | yes |
| PDFUA-Ref-2-08 | `PDFUA-Ref-2-08_BookChapter.pdf` | yes |
| PDFUA-Ref-2-09 | `PDFUA-Ref-2-09_Scanned.pdf` | yes |
| PDFUA-Ref-2-10 | `PDFUA-Ref-2-10_Form.pdf` | yes |

## Licensing and limits

The collection-level redistribution basis is CC BY 4.0. Redistributed copies must retain appropriate attribution, link the license, and indicate changes. No stronger per-file rights claim is made. The source page currently notes that one suite file was removed pending replacement; the omitted 2-07 item is therefore not silently treated as part of this nine-file experiment.

The original download archive and acquisition timestamp were not retained. This verification confirms the local filename/item mapping, local file hashes, public source references, and collection-level license; it does not reconstruct the historical download path.
