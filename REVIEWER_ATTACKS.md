# Reviewer attacks

This document is intentionally adversarial. Status is current as of the evidence-first rebuild.

| Attack | Why it matters | Current response/evidence | Remaining risk |
|---|---|---|---|
| This rediscovers Matterhorn's machine/human distinction. | The distinction itself is not a contribution. | Accepted; the contribution is operational paired mutation methodology, not the distinction. | AT evidence is qualitative and single-observer; a clean M01 rerun remains open. |
| Kumar et al. already created controlled variants. | Novelty may be overstated. | Accepted; revise related work to distinguish expert-labeled variants from structure-level validator kill/survival ground truth. | Citation and exact overlap audit pending. |
| Isartor already validates validators. | PDF conformance mutation is prior art. | Accepted; claim methodology for PDF accessibility-validator mutation, not intentional PDF testing generally. | Need direct comparison. |
| Operators are not novel. | Recognized defect classes cannot be claimed as inventions. | Accepted; operators cite PDF/UA/Matterhorn/PDF Association motivations and claim operationalization. | Exact overlap should be independently checked before submission; no novelty claim depends on it. |
| Nine PDFs are too few. | Source clustering invalidates generalization. | Current paper is scoped to the nine-file corpus; multiple targets are supported by the pipeline. | Per-file provenance and redistribution confirmation remain open. |
| Mutants are artificial. | Synthetic defects may not represent field failures. | Threat documented; each operator requires explicit rationale, preconditions, and AT/semantic evidence. | AT pilot is complete for nine cases; a clean paired M01 rerun confirms the tested reading-order effect, with historical instability retained as context. |
| Historical G02-M04 is contaminated or untraceable. | Its validator failures may be collateral and its pair is absent. | Permanently excluded from the current study; current hash-linked M04 mutants are analyzed separately. | A future versioned study would require the exact historical PDFs and raw reports. |
| Verifier shares generator assumptions. | Circular ground truth is possible. | Generator and verifier are separate modules and the verifier does not call validators. | Both use pypdf; an independent parser or direct COS audit remains desirable. |
| Low detection is expected for semantic defects. | It is unfair to call these misses. | Class B terminology is “survived automated checks”; only claimed automated properties are scored. | Tool-scope evidence required. |
| Overall percentages mislead. | Aggregate rates obscure operator/class behavior. | Active analysis reports per-operator/class outcomes, explains denominators, and excludes manual checks from automated rates. | Results remain scoped to this corpus and builds. |
| PAC AI invalidates conclusions. | AI and formal checks have different semantics. | Separate PAC Formal/PAC AI schemas; aggregate-only PAC AI rows are explicitly unresolved and excluded from formal claims. | A usable semantic export/API is still unavailable. |
| Validators have different scopes. | Agreement/ranking is invalid. | Tool capability table and exact profile/build/settings fields are recorded for the formal runs. | Results remain descriptive, not a global ranking. |
| Benchmark is not reproducible. | Central validity failure. | Generator, verifier, hashes, schemas, reproduction script, formal freeze, and fail-closed behavior are present. | Full render regeneration is slow; fresh-clone and final release QA remain. |
| Human interpretation is subjective. | Detection coding may be biased. | Double-coder fields and adjudication are in the canonical schema/protocol; AT is explicitly single-observer because a second coder is unavailable. | Independent AT observer remains future work. |
| Visual sameness does not imply accessibility impact. | Visual comparison is not semantic truth. | Paper separates rendering invariance from assistive effect and links nine NVDA transcripts to a preserved raw log. | Screenshots are incomplete and M01 requires a clean rerun. |
| No screen-reader evidence exists. | Expected effects may not occur. | Nine representative NVDA observations are complete and remain qualitative, not validator detections. | Single observer; M01 instability remains open. |
| One mutant per source/operator confounds effects. | Operator claims are unstable. | Pipeline supports multiple applicable targets and records source/target identity. | Corpus/target inventory pending. |
| “First” claim is unsupported. | Prior-art error damages credibility. | Broad first claim removed from active README/paper direction. | Exhaustive literature audit pending. |
| Corpus is too small to call a benchmark. | Terminology overclaims. | Current wording is artifact/mutation pipeline with scoped claims; benchmark label is qualified. | Larger release would strengthen it. |
| Results change across versions. | External validity is limited. | Exact version/build/profile/hash fields and per-run raw evidence are required. | Versioned runs pending. |
