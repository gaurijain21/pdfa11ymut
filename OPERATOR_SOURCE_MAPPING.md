# Operator source and rule-mapping audit

This is the pre-implementation rationale for the added Class A operators. The table below records the observed rule identifiers/labels from the canonical reports. These labels are evidence metadata, not claims that different validators implement equivalent rules; all classifications remain baseline-relative and operator-specific.

| Operator | Authoritative requirement | Machine-verifiability rationale | Rule/profile status |
|---|---|---|---|
| M03 | PDF/UA heading hierarchy requirement; Matterhorn Protocol 1.1 | A changed heading role and skipped level are structurally inspectable. | PAC `Structure elements`; Acrobat `Appropriate nesting`; veraPDF `7.4.2`. |
| M06 | PDF Association list-structure techniques and Matterhorn list-semantic checks; no explicit duplicate-reference failure condition identified | The duplicate direct `/LI` reference is independently observable in the COS/tree and can change structural traversal, but the reviewed authoritative material does not establish a dedicated machine-checkable PDF/UA rule for reference uniqueness. | Class B structural/assistive-representation observation; no new relevant automated rule was observed in the active PAC, Acrobat, or veraPDF rows. |
| M07 | PDF/UA figure alternate-description requirement; PDF Association Techniques | Presence/absence of `/Alt` is mechanically inspectable, while description quality is not. | PAC `Alternative Descriptions`; Acrobat `Figures alternate text`; veraPDF `7.3`. |
| M08 | PDF/UA document-language requirement; PDF Association accessible-PDF guidance | Catalog `/Lang` presence is mechanically inspectable. | PAC `Natural language`; Acrobat `Primary language`; veraPDF `7.2`; G09-M08 remains excluded for baseline conflict. |
| M09 | PDF/UA role mapping requirement; Matterhorn Protocol 1.1 | Resolving a used custom role to an undefined target is a structural lookup. | PAC `Role mapping`; veraPDF `7.1` on the three active used-role cases; four unused-role artifacts were retired. |
| M10 | PDF/UA table containment requirement; PDF Association table techniques | A `/TR` direct child role can be compared to the allowed `/TD`/`/TH` set. | PAC `Structure tree`; veraPDF `7.2`; Acrobat emitted no relevant automated detection in the active rows. |

Primary references: [Matterhorn Protocol 1.1](https://pdfa.org/download-area/publications/Matterhorn-Protocol-1-1.pdf), [Techniques for Accessible PDF](https://pdfa.org/techniques-for-accessible-pdf/), and [Techniques background](https://pdfa.org/techniques-for-accessible-pdf-background/).

If a target does not exist or a validator profile does not claim the property, the case remains N/A or is analyzed as outside scope. The added operators are not included in any result denominator until a clean target and relevant evidence exist.
