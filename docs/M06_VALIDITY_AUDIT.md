# M06 validity audit: duplicate list-item reference

Audit status: structural validity confirmed for the active sample; normative review completed with Class B reclassification

Date: 2026-09-25

## Question under review

M06 is specified as a structurally controlled mutation that duplicates the first direct `/LI` reference in a reachable `/L` element’s `/K` array. It is retained as Class B in the current study because the authoritative materials reviewed did not establish a specific machine-checkable duplicate-reference requirement. The intended delta is a second occurrence of an existing list-item reference. The paper must not describe M06 as a formal validator failure or common surviving Class-A mutation until the following are established independently of the generator and the validator reports:

1. the baseline contains a reachable `/L` with at least one direct `/LI` child;
2. the mutant contains the same list-item reference twice in that `/L`’s direct child sequence;
3. the duplicate list item remains reachable and its `/Lbl`, `/LBody`, parent, page, and content associations are unchanged;
4. page count, page boxes, page content streams, annotations, and rendering are unchanged;
5. the transformation is mapped accurately to the normative/list-structure context without assuming a dedicated duplicate-reference machine rule;
6. no baseline defect is being counted as an M06 detection; and
7. the three checking configurations either claim or do not claim an automated rule capable of detecting the property.

## Current active cases

The active manifest contains seven M06 cases:

- `PDFUA-Ref-2-01_Magazine-danish-M06`
- `PDFUA-Ref-2-03_AcademicAbstract-M06`
- `PDFUA-Ref-2-04_Presentation-M06`
- `PDFUA-Ref-2-05_BookChapter-german-M06`
- `PDFUA-Ref-2-06_Brochure-M06`
- `PDFUA-Ref-2-08_BookChapter-M06`
- `PDFUA-Ref-2-09_Scanned-M06`

The invoice and form baselines have no eligible M06 target and therefore do not contribute M06 cases. The current paired-check outcome is 0/7 automated findings for PAC, Acrobat, and veraPDF; because M06 is Class B, this is a descriptive survival/representation result rather than a validator miss rate. Acrobat’s G05 baseline has an unrelated pre-existing `Lbl and LBody` failure that is carried forward and is not an M06 finding.

## Evidence inspected

- `operators/operators.yaml`, M06 specification: precondition `/L` with a direct `/LI`, transformation duplicates the first `/LI` reference, and page/content/role/containment invariants.
- `pdfa11ymut/core.py`: deterministic candidate traversal, first eligible target, and M06 insertion at the beginning of the target `/K` array.
- `data/mutants.jsonl`: generator-side intended/observed deltas, source and mutant hashes, parseability, page-content hashes, 150-DPI exact RGB rendering, and `mutation_valid=true` for active M06 records.
- `analysis/generated/purity_audit.csv`: all active M06 rows currently marked `PASS` by the existing purity path.
- `evidence/independent_verification_v2/*.json`: all active M06 rows have equal page count/page boxes/content stream hashes/annotations/images and MuPDF 72-DPI rendering equality. The independent PyMuPDF raw-COS route now confirms the M06 delta for all seven active cases, including ambiguous same-shaped list sites by following the selected target's structure-tree child-index path rather than trusting pypdf object numbers.
- `analysis/generated/G05_M06_INTERPRETABILITY_REVIEW.md`: the G05 list branch and unrelated Acrobat `Lbl and LBody` baseline finding are explicitly separated from the M06 target branch.
- PAC, Acrobat, and veraPDF raw reports and baseline-relative formal classifications.

## Current findings

### 1. Baseline precondition and reachability

The generator-side records identify a reachable `/L` target and a direct `/LI` child for every active M06 case. The active generator rejects baselines without an eligible target. The selection table now records candidate counts and chosen target references. This is necessary evidence, but not yet sufficient independent evidence because the candidate discovery is implemented in the same pypdf-based code path as generation.

### 2. Intended structural delta

The pypdf verification records show the target `/L` changing from a direct child sequence containing one first `/LI` occurrence to a sequence containing that same logical `/LI` twice. For example, the preserved Academic Abstract record identifies target object `208:0`, with a one-item `/K` sequence in the baseline and two copies of the same `/LI` snapshot in the mutant. The independent PyMuPDF route confirms this same delta in raw COS: it identifies the corresponding target by the baseline structure-tree path, observes a repeated direct reference to the same `/LI` object, matches the normalized `/LI` subtree twice, and verifies the non-target `/L` signatures are unchanged. Object numbers are not assumed stable across serialization.

### 3. Non-target invariants

For the seven active cases, the independent v2 records report:

- equal page counts;
- equal page boxes;
- equal page-content stream hashes;
- equal annotation signatures;
- equal intrinsic image signatures;
- equal MuPDF rendering at 72 DPI.

The primary verifier additionally reports exact 150-DPI Poppler RGB equality and unchanged page-content hashes. These are strong rendering/content invariants. Together with the raw-COS structure-tree/path check, all seven active M06 cases have independent structural status `PASS` and mutation confidence `HIGH` in the v2 records. The check is narrow and does not claim that every PDF structure property has been independently verified.

### 4. Normative status

The authoritative Matterhorn Protocol 1.1 and Techniques for Accessible PDF materials reviewed for this freeze define list-structure and tagged-content conditions, but do not establish a dedicated failure condition for this exact duplicate-reference transformation. The general list-structure context is recorded in `data/operator_standard_mapping.csv`, while M06 is Class B: a structurally controlled semantic/representation mutation whose no-finding result is not a machine-checkable validator miss rate. The mapping does not invent a clause or claim that the tested configurations were obligated to report it.

### 5. Validator scope and result interpretation

No active PAC, Acrobat, or veraPDF report emitted a new M06-specific automated rule. This supports the bounded statement “no automated finding was observed under these builds/profiles.” It does not by itself prove that all three validators failed a requirement or that the mutation is universally invalid. The Acrobat G05 `Lbl and LBody` failure is baseline-carried and outside the M06 target branch.

## Independent second-route procedure

Implement a second-route M06 structural check using MuPDF/PyMuPDF raw COS access or a normalized object/xref comparison that:

1. locates every reachable `/L` and its direct `/K` entries in both PDFs;
2. identifies the selected target by its pre-mutation object/content signature rather than trusting a pypdf object number;
3. compares the direct child identity sequence and proves exactly one duplicate occurrence of the selected `/LI` was added;
4. compares the selected `/LI` subtree, parent `/P`, `/Pg`, roles, marked-content IDs, and non-target `/L` sequences;
5. records an explicit allowed-change list and observed-change list; and
6. emits `CONFIRMED`, `CONTRADICTED`, or `UNVERIFIABLE` per case.

The route confirms all seven active cases. It does not establish that a checker is required to report the property; the completed authoritative review is why M06 is retained as Class B and excluded from Class A rates. The raw reports and structural evidence remain unchanged.

## Current conclusion

M06 is not a generator-only artifact: every active M06 pair is parseable, visually/content invariant, and independently confirmed by the PyMuPDF raw-COS route as a reachable list whose first direct `/LI` reference is repeated once. The completed standards review supports only the bounded result “seven independently structurally confirmed Class B M06 mutations with no automated target finding under the tested configurations.” It does not support a universal validator-failure claim or a Class A kill/survival rate.
