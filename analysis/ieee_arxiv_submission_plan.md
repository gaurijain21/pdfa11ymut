# IEEE + arXiv Submission Plan for PDFa11yMut

## Chosen Direction

Primary framing: software testing / benchmark evaluation.

Working title:

PDFa11yMut: Mutation-Based Evaluation of Automated PDF Accessibility Validators

## Submission Path

1. Prepare an arXiv preprint.
2. Release or prepare the artifact bundle.
3. Submit an expanded/refined version to an IEEE software testing, software quality, or accessibility-relevant venue.

## Why This Direction Fits

The paper evaluates validator behavior using controlled mutants. That is closer to software testing and benchmark construction than to a user study. The accessibility domain remains central, but the methodological claim is:

Automated validator pass/fail behavior should be evaluated against independently verified injected defects.

## arXiv Version

Goal: public, citable preprint.

Recommended structure:

1. Introduction
2. Background and Related Work
3. PDFa11yMut Methodology
4. Mutation Operators
5. Experimental Setup
6. Results
7. Discussion
8. Threats to Validity
9. Artifact Availability
10. Conclusion

Use the current Markdown draft as the base.

## IEEE Version

Likely framing:

Mutation-based benchmark for evaluating automated PDF accessibility validators.

Emphasize:

- mutation testing,
- evaluator adequacy,
- benchmark construction,
- detection matrix,
- reproducibility,
- validator agreement/disagreement.

Reduce:

- broad accessibility advocacy language,
- venue-specific accessibility discussion,
- long HCI framing.

Keep:

- PDF/UA and Matterhorn context,
- automated vs human-checkable boundary,
- Ma11y as accessibility mutation predecessor,
- GateTruth as brief evaluator-auditing analogy.

## Strongest Current Claims

- Five mutation operators generate distinct PDF structure-level accessibility defects.
- 23 generated mutants were independently verified.
- Three validators show highly operator-specific detection.
- All validators detected generated heading-hierarchy mutants.
- Acrobat and veraPDF detected one list-related marked-content association mutant that PAC missed.
- Most verified mutants survived all automated validators.

## Claims To Avoid

- Do not claim PAC, Acrobat, or veraPDF are generally inaccurate.
- Do not call all missed mutants false negatives without defining the exact detection target.
- Do not claim the five mutation operators are comprehensive.
- Do not claim user impact without screen-reader/user validation.

## Before arXiv

- Convert Markdown to PDF or LaTeX.
- Normalize citations.
- Add author names and affiliations.
- Add artifact availability statement.
- Confirm Acrobat version/build if possible.
- Decide whether the corpus can be publicly released.

## Before IEEE Submission

- Decide target IEEE venue.
- Convert to IEEE two-column format.
- Format references in IEEE style.
- Add artifact DOI or repository URL if available.
- Consider expanding corpus beyond 5 golden PDFs and 23 mutants.
- Add implementation details for mutation generation if code is public.

## Candidate IEEE-Style Venues

- IEEE ICST, especially a testing tools/data or research track if timing fits.
- IEEE software quality/testing workshops.
- IEEE accessibility or human-centered computing venues if the call explicitly includes accessibility evaluation.

If the corpus is not expanded, a workshop/data-showcase style venue is more realistic than a top full-paper track.
