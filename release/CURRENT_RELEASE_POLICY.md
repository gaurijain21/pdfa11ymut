# Current release policy

This file governs a future public artifact assembled from the canonical `STUDY_MANIFEST.json`. Historical ZIP files in the repository are archival and must not be treated as the current release.

## Redistributable by default

- Source code, operator specifications, scripts, tests, documentation, generated tables, and machine-readable manifests are released under the repository's MIT license.
- The nine locally retained PDF/UA Reference Suite baselines and the generated derivatives are distributed only under the collection-level terms documented in `CORPUS_LICENSES.md`: CC BY 4.0 attribution is required, and modifications must be identified. The release must carry the attribution and link in `THIRD_PARTY_NOTICES.md`.

## Not included without separate clearance

- Native PAC, Acrobat, and veraPDF reports, screenshots, and NVDA/Speech Viewer logs are evidence artifacts, not automatically cleared third-party assets. A public bundle may include their hashes, schemas, classifications, and provenance index, but it must omit the raw files unless the applicable vendor/participant redistribution terms are confirmed.
- PAC AI aggregate-only metadata may remain as unresolved audit data, but it is not a formal result and does not create a release entitlement for vendor output.
- Historical ZIP files, stale analysis exports, and artifacts whose provenance or license cannot be established are excluded from a new release.

## Current public-release decision (2026-09-25)

The public Git freeze deliberately excludes every raw PAC, Acrobat, veraPDF,
NVDA, and Speech Viewer report, screenshot, and log. Their hashes, schemas,
classifications, protocols, and provenance indexes remain available in the
canonical data where appropriate. This is an explicit non-redistribution
decision, not a claim that vendor or participant terms were cleared. No vendor
or participant clearance is required for the public bundle while those raw
bytes remain excluded. The private research checkout retains the raw evidence
for audit and reproduction by an authorized holder.

The PDF/UA Reference Suite inputs and generated derivatives remain governed by
the collection-level CC BY 4.0 attribution record in `CORPUS_LICENSES.md`.

## Assembly gate

A release builder must regenerate from the canonical manifest, verify every included file's hash, emit `THIRD_PARTY_NOTICES.md`, and fail closed when a raw evidence file lacks an explicit redistribution decision. No release is called submission-ready until this gate passes.

For the current public bundle, the explicit exclusion decision above satisfies
the raw-evidence branch of this gate. A future bundle that includes raw vendor
or AT artifacts must obtain and record separate clearance before publication.
