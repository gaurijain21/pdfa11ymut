# Public release exclusion ledger

Decision date: 2026-09-25

The current public Git freeze excludes raw third-party/vendor evidence. This
is a deliberate non-redistribution decision; it does not assert that any
vendor or participant license was obtained.

Excluded families:

- `evidence/acrobat/`
- `evidence/pac/`
- `evidence/verapdf/`
- `evidence/controls/`
- `evidence/at/`
- `evidence/double_coding/`
- `evidence/double_coding_baselines/`
- `evidence/pac_ai/`

Public substitutes retained in the freeze:

- report and input SHA-256 values;
- validator versions, profiles, settings, and timestamps;
- canonical classifications and baseline-relative reasons;
- AT protocol, versions, hashes, and observation summaries;
- corpus provenance, attribution, and the collection-level CC BY 4.0 notice.

If a future release includes any excluded raw bytes, it must add an
artifact-specific redistribution decision before publication.
