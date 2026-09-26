# M09 historical recovery audit

The active study does not silently substitute newly generated M09 PDFs for historical validator evidence. Four historical M09 records were excluded because their original mutant bytes are unavailable for independent re-audit. The old rationale that an unused `RoleMap` entry was sufficient was rejected: the reviewed Matterhorn condition applies to the mapping entry itself, so the historical target cannot be called invalid or valid without the bytes and a complete audit trail.

On 2026-09-25 the current deterministic generator was run against the four named baselines. It produced three new reachable-target candidates and correctly refused the scanned baseline because no target satisfied the M09 precondition. The candidate hashes, paths, and promotion restrictions are recorded in `data/m09_recovery_candidates.csv`.

These candidates are recovery leads, not replacements. They are not in `data/mutants.jsonl`, have no validator reports, do not alter the 69-mutant denominator, and require a fresh complete validator run plus the normal independent verification and purity checks before any future study could promote them. The historical exclusion remains objective and transparent.
