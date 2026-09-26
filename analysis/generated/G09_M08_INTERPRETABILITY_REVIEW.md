# G09 / M08 interpretability review

## Golden object state

`corpus/golden/PDFUA-Ref-2-09_Scanned.pdf` has 82 pages. The document catalog contains a direct `/Lang` entry with the text value `English`. The entry is document-level, not inherited. No page dictionary, page-tree node, or structure element inspected contains `/Lang`. The catalog has `/StructTreeRoot`, `/Outlines`, `/Metadata`, and `/MarkInfo`; the structure tree contains no structure-element `/Lang` entries. XMP contains the title language marker `xml:lang="x-default"`, but no document-language field that substitutes for catalog `/Lang`.

## PAC evidence

The raw PAC Formal export records PDF/UA-1 and the aggregate row:

`Natural language 122460 - 1`

It reports the document language as `English` and provides no criterion number, object reference, page number, or location for the failed check. The report therefore supports the exact PAC check name and count, but not a more granular locator. PAC's published language guidance states that the document language must be a formal language code; the observed literal `English` is therefore best interpreted as an invalid language identifier rather than a missing `/Lang` entry.

## veraPDF evidence

The G09 golden veraPDF 1.30.2 PDF/UA-1 JSON report is compliant with 106 passed rules and 0 failed rules. The corresponding G09-M08 report fails ISO 14289-1:2014 clause 7.2, test 2, with `gContainsCatalogLang == true`; its contexts are outline entries and its message is `Natural language in the Outline entries cannot be determined`. This shows that the veraPDF profile checks catalog-language presence for this rule, whereas PAC also rejects the golden's language value.

## Mutant state

`PDFUA-Ref-2-09_Scanned-M08.pdf` removes only the catalog `/Lang` entry: its catalog has no `/Lang`, while pages and structure-element language entries remain absent in both files. The recorded verification is purity-clean: operator-specific delta passed, parseability passed, page count was preserved, no unexpected structural changes were recorded, and exact 150-DPI rendering equality passed with zero differing pixels. Golden SHA-256 is `bb46d5c723fe1427dd1bf92ccd8653f9a5cef4054f7d878168b99477fa3792ae`; mutant SHA-256 is `66c34b8b56d04baf6e805411a1b1c460b25232f6ee0c968e44031c365e47d54c`.

## Verdict and action

Verdict: `TOOL_SPECIFIC_AMBIGUITY`.

The mutant is locally valid and cleanly exercises removal of `/Lang`, and veraPDF shows the expected baseline-to-mutant transition. However, PAC's baseline already fails the same Natural language category because `/Lang` is present with the invalid value `English`; the PAC export cannot distinguish that condition from the mutant's missing `/Lang`. G09-M08 is therefore excluded from active cross-validator M08 interpretation. The golden, mutant, PAC report, and veraPDF reports are retained as audit evidence. No replacement mutant was generated because every other active golden already has an M08 unit; adding a duplicate solely to preserve the count would be artificial.
