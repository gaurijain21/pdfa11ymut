# 2026 literature and tool-landscape check

Checked 2026-09-25 against authoritative/primary pages. This is a scope check, not a request to rerun the frozen three-configuration experiment.

## Findings relevant to wording

- Ma11y remains a direct accessibility-mutation precedent, but for web accessibility; Android accessibility mutation testing is a separate mobile precedent. The paper already cites both and does not claim PDF mutation testing is the first mutation-testing work in accessibility.
- The PDF Association's PDF/UA Reference Suite, Matterhorn Protocol, and Techniques for Accessible PDF remain prior sources of curated examples, requirements, and procedures. They do not by themselves supply the paired transformation/evidence unit used here.
- Horn is an open-source PDF/UA-1 checker based on Matterhorn and advertises machine-oriented checks, JSON/SARIF/JUnit output, and CI use. Its existence reinforces the need to say “tested configurations” rather than make permanent claims about validators. It was not added to the frozen experiment.
- PDF4WCAG Desktop 1.10.1 (June 25, 2026) is a current desktop interface built around veraPDF. It is an additional tool/product layer, not evidence that the existing veraPDF run is stale or that the study must be expanded.
- The PDF Association currently documents ISO 14289-2:2024 (PDF/UA-2), ISO/TS 32005:2023, and WTPDF. The present artifact is deliberately PDF/UA-1/ISO 14289-1 scoped; these standards are acknowledged as scope/future-work context and are not retrofitted into the operators or denominators.
- Current validator/tool pages emphasize that automated and human checks have different scope. The manuscript therefore uses “PDF accessibility checking configurations,” separates Acrobat manual prompts, and does not call the rates accuracy or general sensitivity.

## Sources checked

- Horn official repository: https://github.com/focusring/horn
- PDF4WCAG Desktop: https://pdf4wcag.com/desktop-app/
- PDF Association accessibility standards overview: https://pdfa.org/accessibility
- PDF Association Well-Tagged PDF: https://pdfa.org/wtpdf/
- PDF Association ISO/TS 32005: https://pdfa.org/resource/iso-32005/
- PDF Association current ISO status: https://pdfa.org/iso-status/
- veraPDF CLI documentation: https://docs.verapdf.org/cli/validation/
- Ma11y publication record: https://escholarship.org/uc/item/6wm923wc

## Decision

No current finding invalidates the study's narrow novelty or requires a new validator run. The appropriate repair is bounded related-work/context wording, which is now recorded here and reflected by the manuscript's explicit PDF/UA-1 scope.
