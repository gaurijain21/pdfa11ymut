# Baseline review required

Do not interpret active mutants implicated by a flagged baseline conflict. Explicitly excluded units remain outside the active analysis and are retained only as audit evidence.

- `PDFUA-Ref-2-05_BookChapter-german` / `Acrobat Full Check`: **BASELINE_REVIEW_REQUIRED**; outcome=`FAIL`; automated failures=`Lbl and LBody`; rule IDs=`Lbl and LBody`; warnings=`none`; manual checks=`Logical Reading Order|Color contrast`. Recorded resolution for `M06`: `VALID_WITH_BASELINE_DELTA`. Retain G05 unchanged; compare Acrobat M06 results against the baseline and do not count an unchanged Lbl/LBody failure as an M06 detection.
- `PDFUA-Ref-2-09_Scanned` / `PAC Formal`: **BASELINE_REVIEW_REQUIRED**; outcome=`FAIL`; automated failures=`Natural language`; rule IDs=`Natural language`; warnings=`none`; manual checks=`none`. Affected operator(s) excluded from active analysis: M08, M09.
