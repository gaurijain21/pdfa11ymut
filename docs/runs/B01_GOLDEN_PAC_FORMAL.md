# B01 - Golden PAC Formal baselines

This batch establishes the PAC Formal baseline for all nine goldens. It is the only human batch to perform next.

## Fixed configuration

- PAC version/build: record once in [`data/pac_formal_run_metadata.json`](../../data/pac_formal_run_metadata.json); do not leave `REQUIRES_USER_ENTRY`.
- Platform: record Windows version in the same metadata file.
- PAC mode: traditional/formal PDF/UA validation.
- PAC AI: **OFF**. Do not open or run the AI-assisted analysis for this batch.
- Remediation, auto-tagging, optimization, and saving over the input: disabled.
- Evidence destination: `evidence/pac/formal/`.
- Evidence filename: exactly the filename in the checklist below.

## Repetitive procedure

1. Open the next input from the checklist in PAC.
2. Confirm the displayed filename matches the checklist.
3. Verify the input SHA-256 with `Get-FileHash -Algorithm SHA256`.
4. Confirm PAC AI is off and the formal/traditional PDF/UA check is selected.
5. Run the check, click **PDF report**, and export the complete PAC report.
6. Save the exported PDF report under `evidence/pac/formal/` with the exact expected filename.
7. Add a same-stem screenshot only if the exported report omits the displayed filename, version/build, or formal-mode context. Do not edit the input PDF.

Do not decide whether any finding is a mutation detection. Record the report exactly; classification is performed during ingestion against the matching golden baseline.

## Nine-file checklist

| Done | Golden ID | Input path | SHA-256 | Expected report | Destination |
|---|---|---|---|---|---|
| [ ] | `PDFUA-Ref-2-01_Magazine-danish` | `corpus/golden/PDFUA-Ref-2-01_Magazine-danish.pdf` | `aef89af13c9c94fc4f4e1a8c5872450cc4c8fff7de544d8ada6a0912425aa434` | `PDFUA-Ref-2-01_Magazine-danish__aef89af13c9c94fc4f4e1a8c5872450cc4c8fff7de544d8ada6a0912425aa434.pdf` | `evidence/pac/formal/` |
| [ ] | `PDFUA-Ref-2-02_Invoice` | `corpus/golden/PDFUA-Ref-2-02_Invoice.pdf` | `fbae08464f192f532205833215505b78266e86df6283d9b0c439cb06927ce0b9` | `PDFUA-Ref-2-02_Invoice__fbae08464f192f532205833215505b78266e86df6283d9b0c439cb06927ce0b9.pdf` | `evidence/pac/formal/` |
| [ ] | `PDFUA-Ref-2-03_AcademicAbstract` | `corpus/golden/PDFUA-Ref-2-03_AcademicAbstract.pdf` | `e61257d371261867926eb006f8895569a95fcfbcb93fca3be04b8b9187cb93a0` | `PDFUA-Ref-2-03_AcademicAbstract__e61257d371261867926eb006f8895569a95fcfbcb93fca3be04b8b9187cb93a0.pdf` | `evidence/pac/formal/` |
| [ ] | `PDFUA-Ref-2-04_Presentation` | `corpus/golden/PDFUA-Ref-2-04_Presentation.pdf` | `90acb829ca8bfa037796592539d15010e9099d1cd2622aac1fce7d9fd3ae7575` | `PDFUA-Ref-2-04_Presentation__90acb829ca8bfa037796592539d15010e9099d1cd2622aac1fce7d9fd3ae7575.pdf` | `evidence/pac/formal/` |
| [ ] | `PDFUA-Ref-2-05_BookChapter-german` | `corpus/golden/PDFUA-Ref-2-05_BookChapter-german.pdf` | `fc525b8899da31779b6143c16053779cd560d4417018a901472de33c71252352` | `PDFUA-Ref-2-05_BookChapter-german__fc525b8899da31779b6143c16053779cd560d4417018a901472de33c71252352.pdf` | `evidence/pac/formal/` |
| [ ] | `PDFUA-Ref-2-06_Brochure` | `corpus/golden/PDFUA-Ref-2-06_Brochure.pdf` | `aefd5ab48a908b9996ffadcb14d8ff31a2c653657cbe011a46f4cf61396a589e` | `PDFUA-Ref-2-06_Brochure__aefd5ab48a908b9996ffadcb14d8ff31a2c653657cbe011a46f4cf61396a589e.pdf` | `evidence/pac/formal/` |
| [ ] | `PDFUA-Ref-2-08_BookChapter` | `corpus/golden/PDFUA-Ref-2-08_BookChapter.pdf` | `2b958600daec79373736f413f2712fcd9c604de2c352cbc1ec9d67cc5d7932f1` | `PDFUA-Ref-2-08_BookChapter__2b958600daec79373736f413f2712fcd9c604de2c352cbc1ec9d67cc5d7932f1.pdf` | `evidence/pac/formal/` |
| [ ] | `PDFUA-Ref-2-09_Scanned` | `corpus/golden/PDFUA-Ref-2-09_Scanned.pdf` | `bb46d5c723fe1427dd1bf92ccd8653f9a5cef4054f7d878168b99477fa3792ae` | `PDFUA-Ref-2-09_Scanned__bb46d5c723fe1427dd1bf92ccd8653f9a5cef4054f7d878168b99477fa3792ae.pdf` | `evidence/pac/formal/` |
| [ ] | `PDFUA-Ref-2-10_Form` | `corpus/golden/PDFUA-Ref-2-10_Form.pdf` | `06d5cacd7c5ba9573a57c6d99d3f357ee14a24cff0c138036840fc44c6311806` | `PDFUA-Ref-2-10_Form__06d5cacd7c5ba9573a57c6d99d3f357ee14a24cff0c138036840fc44c6311806.pdf` | `evidence/pac/formal/` |

## Do not manually interpret yet

Do not label a baseline “clean” from assumption, do not treat “Needs Manual Check” as an automated failure, and do not decide whether a rule is relevant to M01-M10. The ingestion step records the formal baseline facts and creates a baseline review report before mutant interpretation begins.
