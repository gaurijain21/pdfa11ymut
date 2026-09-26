# Standards-mapping review

Reviewed 2026-09-25 against the PDF Association's Matterhorn Protocol 1.1 and Techniques for Accessible PDF. The machine-readable per-operator table is `data/operator_standard_mapping.csv`; this note records the important scope decisions.

## Matterhorn interpretation

The Matterhorn Protocol describes 136 PDF/UA-1 failure conditions, with a machine/human “How” field. Relevant mappings used in the study are:

- M01: 09-001, tags not in logical reading order — Human.
- M02: related to 01-005/01-006, but the exact effect of removing a reachable structure reference is content-completeness/semantic scope and is not treated as a universal automated target.
- M03: 14-003, skipped numbered heading levels — Machine.
- M04: related to 09-003 semantic appropriateness — Human for the exchanged marked-content association.
- M05: related to 09-001 logical reading order — Human for the intra-element sequence effect.
- M06: 09-005 is the general machine condition for list-related structure syntax, but the reviewed source does not state that repeating one `/LI` reference is itself a machine-checkable failure. M06 is therefore Class B in this study despite independent structural confirmation.
- M07: 13-004, missing Figure alternative/replacement text — Machine.
- M08: 11-001, natural language for page content cannot be determined — Machine; the mutation is removal of the catalog `/Lang` representation and the G09 baseline conflict is retained separately.
- M09: 02-001, a non-standard tag mapping does not terminate with a standard type — Machine. Matterhorn explicitly says RoleMap conditions apply regardless of whether a tag is used. This is why the four historical unused-target M09 artifacts are now described as unverifiable due to missing original mutant PDFs, not as definitively invalid.
- M10: 09-004, table-related structure syntax — Machine in general; the direct `/TR` child-role predicate and Acrobat `Headers` observation remain configuration-specific.

## Sources

- PDF Association, [Matterhorn Protocol 1.1](https://pdfa.org/download-area/publications/Matterhorn-Protocol-1-1.pdf), especially the definitions of Machine/Human conditions, Role Mapping checkpoint 02, Appropriate Tags checkpoint 09, Natural Language checkpoint 11, Graphics checkpoint 13, Headings checkpoint 14, Tables checkpoint 15, and Lists checkpoint 16.
- PDF Association, [Techniques for Accessible PDF](https://pdfa.org/techniques-for-accessible-pdf/), including the heading, list, figure, and structure examples.
- PDF Association, [Understanding Techniques for Accessible PDF](https://pdfa.org/understanding-pdf-accessibility-techniques/), for the human procedures for logical order and semantic appropriateness.

No ISO clause number is added where the repository does not retain a licensed normative copy. The table uses PDF/UA-1 clause references already present in the operator specifications only where the corresponding Matterhorn/technique mapping is recorded and bounded by tool/profile scope.
