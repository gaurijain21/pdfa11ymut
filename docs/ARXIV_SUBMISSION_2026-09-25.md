# arXiv submission package

The target for this release is arXiv. The current official [TeX submission guidance](https://info.arxiv.org/help/submit_tex.html) says that arXiv compiles uploaded TeX inputs from the submission root, that only files needed to process the paper should be included, and that PDFs, auxiliary files, logs, hidden files, and embedded JavaScript should not be submitted.

The package is generated with:

```powershell
python scripts/build_arxiv_submission.py
```

The builder flattens the manuscript source so the generated results fragment is available as `results_fragment.tex` at the package root. The package contains exactly:

- `pdfa11ymut_ieee.tex`
- `results_fragment.tex`

It intentionally omits the locally compiled PDF, `.aux`/`.log` files, repository evidence, private reports, historical packages, and temporary files. The arXiv server's TeX Live processor remains the authoritative compilation environment; the local Tectonic build is only a preflight.

The generated ZIP, SHA-256 sidecar, and manifest are ignored by Git because the ZIP is a submission artifact rather than repository source. The committed builder makes the package reproducible.
