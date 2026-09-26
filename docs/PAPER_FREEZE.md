# Paper-freeze preparation and v2 boundary

This file documents the final v2 freeze procedure and boundary. `paper-freeze-v1` is historical and immutable; it is not overwritten.

- historical manifest-generation commit: `dfd7a1d`
- final target: a clean commit with `STUDY_MANIFEST.json` status `PAPER_FROZEN`, followed by immutable tag `paper-freeze-v2`
- canonical manifest: `STUDY_MANIFEST.json`
- canonical manifest, manuscript source, and manuscript PDF SHA-256 values are emitted by the final freeze manifest and recorded in `data/evidence_checksums.sha256`.

The canonical artifact is reproducible and hash-identified. The public Git freeze stages the intended current artifact set, excludes raw vendor/AT evidence and historical bundles from any public bundle, runs the clean-environment tests and audit, commits the result, and creates the local tag `paper-freeze-v2`. The local semantic gate is scoped; any target venue's additional PDF/UA policy remains venue-specific.

The current PDF was rebuilt from the current source with Tectonic 0.17.0, rendered and visually inspected, and reports Tagged=yes with catalog language and explicit document/heading/paragraph/table structure; see `docs/SEMANTIC_PDF_UA_REVIEW_2026-09-25.md`. Raw evidence is excluded from the public freeze, so no redistribution clearance is claimed for those bytes.
