# Paper-freeze identifier

This is a preparation record, not a Git tag or release.

- repository HEAD at final repair audit: `7b78a42dfe7a9e6ebe936d8aabbe1417e3a0b99c`
- working tree: dirty before the final freeze; a clean public Git freeze must exclude raw vendor/AT evidence and historical bundles
- canonical manifest: `STUDY_MANIFEST.json`
- canonical manifest SHA-256: `3ca72697e60e97b88c14f8be9a9c4624460bb570656a3db3e66e8194ab70b83f`
- manuscript source SHA-256: `16abce33b726ece6521afe2373c43c95e5ee1d909ead1070c7768bfe03dba854`
- current manuscript PDF SHA-256: `e3d432ba99b3f4dee0c9506ffa940d08d9cc2d7ea51b0f55156587b16066ffe6`
- recommended eventual tag: `paper-freeze-v1`

The canonical artifact is reproducible and hash-identified. The public Git freeze must stage only the intended current artifact set, exclude raw vendor/AT evidence and historical bundles, run the checks below, commit it, and create the local tag `paper-freeze-v1`. The tag freezes the current study state; it does not imply that the manuscript has passed venue-level semantic PDF/UA review.

The current PDF was rebuilt from the current source with Tectonic 0.17.0, rendered and visually inspected, and reports Tagged=yes with catalog language and structure metadata. The semantic audit found no usable document/heading/paragraph structure; see `docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`. Raw evidence is excluded from the public freeze, so no redistribution clearance is claimed for those bytes.
