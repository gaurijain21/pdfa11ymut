# Data and evidence licensing

The MIT license at the repository root applies to project code and original documentation only. It does not automatically apply to PDFs, generated PDF derivatives, validator reports, screenshots, NVDA logs, or other third-party material.

| Artifact family | Current status | Governing record | Release rule |
|---|---|---|---|
| PDF/UA-1 Reference Suite baselines | Mapped to the collection-level CC BY 4.0 statement | [`CORPUS_LICENSES.md`](CORPUS_LICENSES.md), [`data/corpus_inventory.csv`](data/corpus_inventory.csv) | Retain attribution, license link, and indication of changes; verify the item-level source before redistribution. |
| Mutated PDFs | Derivatives of the reference-suite files | [`CORPUS_LICENSES.md`](CORPUS_LICENSES.md), [`data/baseline_provenance.csv`](data/baseline_provenance.csv) | Redistribute only where the source license permits derivatives; label as generated changes and preserve source attribution. |
| PAC, Acrobat, and veraPDF reports | Tool-generated evidence | [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md), `data/validator_environment.csv` | Raw files are explicitly excluded from the current public Git freeze; only hashes, schemas, classifications, and provenance indexes are public substitutes. |
| Screenshots, Speech Viewer output, and NVDA logs | Evidence captured from third-party software | `evidence/at/`, `data/at_observations.csv` | Raw files are explicitly excluded from the current public Git freeze; only hashes, protocol, and observation summaries are public substitutes. |
| Historical release archives | Not a clean release artifact | `RELEASE_README.md` | Do not submit or redistribute as the current paper freeze. |

The original acquisition archive and timestamp for the local reference-suite files were not retained. The repository records the public source mapping, local hashes, and stated collection-level license, but does not infer rights beyond those records.
