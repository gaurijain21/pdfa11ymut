# Third-party notices

The Python pipeline depends on pypdf, Pillow, and PyYAML. Their package licenses and exact versions are recorded in `requirements.txt`; their upstream license texts should be included in a release bundle according to each package's terms.

The project may use Poppler's `pdftoppm` for rendering. Poppler is a system dependency and is not bundled by this repository. Record the exact Poppler version in each verification manifest.

This working repository contains third-party-derived PDFs, generated derivatives, validator reports, screenshots, and AT logs for reproducibility. They are not covered by the MIT license. Redistribution must follow the item-level terms in `DATA_LICENSES.md`, `CORPUS_LICENSES.md`, and the provenance records; artifacts without confirmed redistribution permission must be omitted from a public release.

The repository's historical release archives must not be treated as clean redistributable bundles. The current public Git freeze explicitly excludes raw PAC, Acrobat, veraPDF, NVDA, and Speech Viewer evidence; it carries hashes, schemas, classifications, protocols, and provenance indexes instead. A future bundle that includes raw vendor or AT evidence requires a new, explicit clearance record. The public freeze includes only artifacts whose license/provenance record permits redistribution, plus this notice and the required PDF/UA Reference Suite attribution.
