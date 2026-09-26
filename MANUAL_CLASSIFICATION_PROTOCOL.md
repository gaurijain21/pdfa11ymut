# Double-coding protocol

Use this protocol for any validator report that requires interpreting which failure corresponds to the injected mutation.

1. Coder 1 receives the hash-linked raw report and the operator specification, but not Coder 2's decision.
2. Coder 1 records one project label (`Detected`, `Missed`, `Outside Scope`, `Needs Manual Check`, `Unrelated`, or `Ambiguous`) and quotes the relevant rule ID/text in the blinded queue.
3. Coder 2 independently repeats the classification from the same evidence.
4. Set `agree`/coder fields only after both decisions are recorded. If they disagree, adjudicate with the operator precondition/invariant record and preserve both original decisions.
5. Count `Detected` only when an emitted automated failure corresponds to the intended mutated property or a predeclared, operator-specific direct-consequence proxy whose conditions are all verified.
6. Do not count baseline failures, unrelated failures, collateral failures as intended kills, or generic manual-check prompts as automated detections.

## Decision precedence

Apply these rules in order after comparing the matched baseline and mutant evidence:

1. `Detected`: a newly failed exact operator rule, or a qualifying proxy listed below.
2. `Outside Scope`: the validator/configuration makes no automated claim about the intended semantic property and emits no qualifying exact rule or proxy.
3. `Unrelated`: a new failure exists, but it is generic or concerns a different property and therefore cannot be attributed to the mutation.
4. `Missed`: the intended property is within the validator's declared automated scope, but no exact rule or qualifying proxy newly fails.
5. `Needs Manual Check`: the tool explicitly requires a human check that could resolve the intended property; state what was not performed.
6. `Ambiguous`: use only when two or more evidence-supported interpretations remain after applying the operator specification, baseline comparison, proxy registry, and custody checks. Never use it merely because a report is generic or the property is outside automated scope.

## Predeclared direct-consequence proxies

### M10 / Acrobat Full Check / `Headers`

Treat a newly failed Acrobat `Headers` checkpoint as `Detected` for M10 only when every condition below is true:

- the hash-linked mutant manifest records the exact direct-child role change `/TH` to `/P`;
- fresh structural verification confirms the target remains under the same `/TR`, its `/K` content is unchanged, non-target roles and containment are unchanged, page-content hashes match, and rendering is pixel-identical;
- the matched golden Acrobat report passes `Headers` and the mutant report newly fails `Headers`;
- no baseline-carried `Headers` failure is present.

This proxy is specific to loss of table-header semantics from the verified `/TH` to `/P` mutation. It must not be generalized to other operators, other role changes, or an unverified generic header finding.

## Generic findings that do not justify ambiguity

- PAC `PDF Syntax` alone is not an M04 content-association rule. Code a new generic syntax failure as `Unrelated` unless the report identifies the mutated association itself.
- PAC `Structure elements` alone does not identify M01 logical order or M02 content completeness. In PAC Formal, code those semantic properties as `Outside Scope` unless a report names an operator-specific automated rule.
- Evidence-packet identity mismatches are custody defects, not scientific ambiguity. Quarantine the misassigned file, rerun or recover correctly identified evidence, update the hash link, and then adjudicate from the corrected pair while preserving the original coder records.

The paper should report genuinely unresolved cases rather than forcing agreement. PAC AI observations use the same coding discipline but remain a separate configuration from PAC Formal.
