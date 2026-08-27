# PDFa11yMut

PDFa11yMut is a controlled mutation-based benchmark for studying how automated PDF accessibility validators respond to independently verified PDF structure mutations.

This repository contains the paper source, analysis tables, detection matrix, and scripts used to summarize the current PDFa11yMut experiment. The current benchmark includes 23 generated and independently verified mutants derived from five validator-clean golden PDFs. The evaluated validators are PAC, Adobe Acrobat Accessibility Checker, and veraPDF.

## Main Result

Across 23 generated and independently verified mutants:

| Validator | Detected | Missed | Total | Detection rate |
|---|---:|---:|---:|---:|
| PAC | 4 | 19 | 23 | 17.4% |
| Adobe Acrobat Accessibility Checker | 5 | 18 | 23 | 21.7% |
| veraPDF | 5 | 18 | 23 | 21.7% |

Detection was highly operator-specific. All three validators detected every generated heading-hierarchy mutant. None detected the generated reading-order swap, omitted-structure, or internal MCID-order mutants. Acrobat and veraPDF also detected one marked-content association mutant, G02-M04, that PAC missed.

These rates are mutation-detection rates for this controlled benchmark. They are not general accessibility accuracy scores.

## Repository Layout

```text
paper/
  pdfa11ymut_ieee.tex
  figures/

data/
  pdfa11ymut_detection_matrix.csv
  pdfa11ymut_overall_rates.csv
  pdfa11ymut_per_operator_rates.csv
  pdfa11ymut_validator_agreement.csv
  pdfa11ymut_metrics_summary.json
  pdfa11ymut_detection_analysis_data.json

analysis/
  pdfa11ymut_detection_analysis.xlsx
  pdfa11ymut_analysis.md
  pdfa11ymut_paper_draft.md
  ieee_arxiv_submission_plan.md

scripts/
  build_detection_analysis.py
  build_detection_workbook.mjs
  build_paper_figures.py
  build_ieee_assets.py

evidence/
  README.md
```

## What Is Included

- Final detection matrix for PAC, Acrobat, and veraPDF.
- Overall detection rates.
- Per-mutation-operator detection rates.
- Validator agreement summary.
- Editable analysis workbook.
- IEEE-style LaTeX paper source and figures.
- Scripts used to generate the analysis and paper figures.

## What Is Not Included Yet

This initial public package does not include golden PDFs, generated mutant PDFs, or raw validator reports. Those files should be added only after confirming that they are safe to release and do not contain copyrighted source material, private paths, personal information, or double-blind submission identifiers.

Recommended future folders:

```text
corpus/golden/
corpus/mutants/
evidence/pac/
evidence/acrobat/
evidence/verapdf/
```

## Building the Paper

The IEEE-style manuscript source is in `paper/pdfa11ymut_ieee.tex`.

From the `paper/` folder:

```bash
pdflatex pdfa11ymut_ieee.tex
pdflatex pdfa11ymut_ieee.tex
```

The second run resolves cross-references.

You can also upload `paper/pdfa11ymut_ieee.tex` and the `paper/figures/` folder to Overleaf.

## Citation

If you use this artifact, cite the accompanying paper. A placeholder citation file is provided in `CITATION.cff`; update it with the final title, author names, venue, DOI, and arXiv identifier when available.

## License

The current package uses the MIT License. If you later release PDF corpora or validator reports, confirm whether those artifacts need a separate data license or redistribution terms.
