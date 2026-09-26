# Paper-freeze identifier

This is a preparation record, not a Git tag or release.

- manifest-generation commit: `a67850dbe9d0d729baabf2b42ce1b5c315da11a7`
- working tree: dirty before the final freeze; a clean public Git freeze must exclude raw vendor/AT evidence and historical bundles
- canonical manifest: `STUDY_MANIFEST.json`
- canonical manifest SHA-256: `9EFE24EEE0A4B59D0A836ED9B866CCFC0ABE7AC40BDE8C096F860DCC0F2679B6`
- manuscript source SHA-256: `C863A406407A8AE2D43EED2B596882457D2696BDA458E97E6DEBB25AE27D27C6`
- current manuscript PDF SHA-256: `3D2B7BCF245ADFABAA0049D3C792C793F158AF3A5210DFFE5D1E6E028AD9691F`
- recommended eventual tag: `paper-freeze-v1`

The canonical artifact is reproducible and hash-identified. The public Git freeze must stage only the intended current artifact set, exclude raw vendor/AT evidence and historical bundles, run the checks below, commit it, and create the local tag `paper-freeze-v1`. The tag freezes the current study state; the local semantic gate passes, while any target venue's additional PDF/UA policy remains venue-specific.

The current PDF was rebuilt from the current source with Tectonic 0.17.0, rendered and visually inspected, and reports Tagged=yes with catalog language and explicit document/heading/paragraph/table structure; see `docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`. Raw evidence is excluded from the public freeze, so no redistribution clearance is claimed for those bytes.
