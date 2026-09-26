# Paper-freeze identifier

This is a preparation record, not a Git tag or release.

- manifest-generation commit: `dfd7a1d`
- working tree: dirty before the final freeze; a clean public Git freeze must exclude raw vendor/AT evidence and historical bundles
- canonical manifest: `STUDY_MANIFEST.json`
- canonical manifest SHA-256: `55900D13CC21800E0156A3A9829A4BD6CE312EC5782A760A00FC882DA03CF115`
- manuscript source SHA-256: `02A8FCD397E771B7F626FCC37F768E4EEAEE318BE786BAB422982578B715CDF6`
- current manuscript PDF SHA-256: `3CE4B9BCAFA9BC74DCCE30A327D0DF4B9D87E8EEFE0EC68D7B80ACB809A5DC13`
- recommended eventual tag: `paper-freeze-v1`

The canonical artifact is reproducible and hash-identified. The public Git freeze must stage only the intended current artifact set, exclude raw vendor/AT evidence and historical bundles, run the checks below, commit it, and create the local tag `paper-freeze-v1`. The tag freezes the current study state; the local semantic gate passes, while any target venue's additional PDF/UA policy remains venue-specific.

The current PDF was rebuilt from the current source with Tectonic 0.17.0, rendered and visually inspected, and reports Tagged=yes with catalog language and explicit document/heading/paragraph/table structure; see `docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`. Raw evidence is excluded from the public freeze, so no redistribution clearance is claimed for those bytes.
