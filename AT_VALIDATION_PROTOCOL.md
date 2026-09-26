# Representative NVDA / assistive-technology validation

This is a small validation study, not a second full experiment. The selected cases are in `data/at_selection.csv` and the queue batch is `B09_AT_REPRESENTATIVE`. It contains one valid mutant per meaningful operator with a stable expected assistive effect, except M09. M09 is excluded because unresolved RoleMap behavior is parser/viewer dependent and a single NVDA observation would not be a reliable validation of the mutation.

## Before starting

Record NVDA version, Windows version, PDF viewer/product and version, speech synthesizer, speech rate, and whether browse mode or document/reading mode is used. Keep those settings fixed for all selected cases. Complete each selected golden comparison immediately before its mutant comparison.

## For each selected case

1. Open the selected golden PDF and verify the SHA-256 in `data/corpus_inventory.csv`.
2. Use the exact navigation procedure in the `exact_at_observation` column of `data/at_selection.csv`.
3. Record the observed golden behavior using the smallest faithful transcript possible.
4. Open the selected mutant, verify its SHA-256 from `manual_runs_todo.csv`, and repeat the identical procedure.
5. Record the observed mutant behavior, including “not observed” when the expected effect does not occur.
6. Save a transcript or timestamped screenshot/recording as `evidence/at/nvda/{artifact_id}__{sha256}.txt` (or the prescribed companion media extension).
7. Add one row to `data/at_observations.csv` with the exact hashes, software versions, procedure, observation, and evidence path.

## Interpretation

Record observations; do not convert them into validator detection rates. A golden-vs-mutant difference supports the expected assistive effect for that sampled case only. A no-difference observation is valid evidence and must not be edited into the expected outcome. M09 remains a machine/conformance case without an artificial AT claim.
