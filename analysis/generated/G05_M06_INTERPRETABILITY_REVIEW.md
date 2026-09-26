# G05-M06 interpretability review

## Acrobat raw evidence

Raw report: `evidence/acrobat/PDFUA-Ref-2-05_BookChapter-german__fc525b8899da31779b6143c16053779cd560d4417018a901472de33c71252352.accreport.html`

The native Acrobat report has one automated failure:

- Rule: `Lbl and LBody`
- Status: `Failed`
- Description: `Lbl and LBody must be children of LI`
- Anchor: `#LblLBody`
- Report summary: `Failed: 1`, `Passed: 28`, `Needs manual check: 2`, `Skipped: 1`
- Object/location detail: none is supplied by the native report.

The two manual prompts are `Logical Reading Order` and `Color contrast`. They are not automated detections.

## G05 structure audit

The G05 structure tree has 8 `/L`, 37 `/LI`, 58 `/Lbl`, and 37 `/LBody` nodes. All 37 `/LBody` nodes are children of `/LI`. Twenty-one `/Lbl` nodes are instead direct children of `/Link` nodes in the table-of-contents/reference branch. A representative chain is:

`/Lbl 1135 0 R <- /Link 323 0 R <- /Reference 322 0 R <- /TOCI 321 0 R <- /TOC 320 0 R <- /Story 318 0 R <- /Article 314 0 R <- /Document 313 0 R`

The representative `/Lbl 1135 0 R` has `/K=[MCID 77, MCID 79]`. The other offending `/Lbl` objects are `1134, 1133, 1132, 1153, 1152, 1151, 1150, 1149, 1148, 1147, 1146, 1145, 1144, 1143, 1142, 1141, 1140, 1139, 1138, 1137 0 R`; each is directly under a `/Link` in the same TOC/reference branch.

The Acrobat failure is therefore a substantive additional list-structure property checked by Acrobat, not a parser/report defect. It is outside the M06 target list.

## M06 comparison

M06 duplicates the first direct `/LI` reference in an `/L /K` array. Its G05 target is `/L 430 0 R`, with source `/K=[/LI 431 0 R, /LI 435 0 R, /LI 440 0 R]`. `/LI 431 0 R` contains `/Lbl 432 0 R` and `/LBody 434 0 R`, both as children of `/LI`.

G05-M06 rewrites the target as `/L 453 0 R`, with `/K=[/LI 454 0 R, /LI 454 0 R, /LI 458 0 R, /LI 463 0 R]`. The duplicate reference is the intended M06 delta. The mutant retains the same unrelated `/Link -> /Lbl` relationships and does not create or alter the 21 baseline violations.

Source SHA-256: `fc525b8899da31779b6143c16053779cd560d4417018a901472de33c71252352`

Mutant SHA-256: `823c2b5ddc120128c9e6eb07963de30f15be94f72a40d781b698af48fb5833a6`

## Verdict

`VALID_WITH_BASELINE_DELTA`

M06 introduces a genuinely new duplicate `/LI` reference in an otherwise independent list branch. The unchanged Acrobat `Lbl and LBody` failure must be carried forward as baseline context and must not be counted as an M06 detection.

## Action

Keep G05 and G05-M06. Do not replace or exclude the mutant. Preserve the raw Acrobat report and this review, and apply baseline-delta comparison when Acrobat mutant evidence is later collected.
