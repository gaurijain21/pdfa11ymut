# G02-M04 contamination audit

## Verdict

**Permanently excluded.** The historical G02-M04 case is not certified clean, repaired, or counted as an M04 detection. This decision is final for the current study release unless the exact historical artifacts are recovered in a future, versioned study.

## Evidence available

The historical summary says that G02-M04 exchanged marked-content associations while retaining sibling list order, and that Acrobat and veraPDF reported list-related failures while PAC reported no automated failure. A repository-wide search found no historical `G02` golden PDF, mutant PDF, COS-level verification record, or complete raw PAC/Acrobat/veraPDF report bundle. The current imported corpus contains nine `PDFUA-Ref-2-*` files and current hash-linked M04 mutants, but no file is mapped to the historical `G02` identifier. The historical case therefore cannot support a scientific result.

## Required answers before any future reopening

1. Objects changed: currently not determinable from repository evidence.
2. `/K` arrays and parent/child relationships: currently not determinable.
3. `/LI`, `/Lbl`, `/LBody`, `/L`, `/TR`, `/TD`, and related containment: currently not determinable.
4. M04-only versus collateral containment mutation: currently not determinable; the validator reports are a contamination warning, not proof of a clean M04.
5. Exact veraPDF rule IDs and messages: currently unavailable because no raw veraPDF report is present.
6. Direct intended defect versus collateral consequences: cannot be classified until the COS delta and raw reports are hash-linked.

## Future reopening procedure

Only a future, explicitly versioned study may reopen this case. It must supply the exact G02 golden and mutant PDFs plus raw PAC/Acrobat/veraPDF evidence, run an independent COS-level comparison, record every changed object in `evidence/verification/G02-M04.json`, and issue a new audit decision. Existing historical summary detections remain non-results and are not resurrected by the current corpus.

## Current local M04 mutants

The current corpus contains independently verified M04 mutants with IDs such as `PDFUA-Ref-2-02_Invoice-M04`. They are separate artifacts, have their own golden/mutant hashes and verification records, and may be used only under the current Class B semantic protocol. They must not be relabeled as G02-M04 or used to reconstruct the missing historical case.
