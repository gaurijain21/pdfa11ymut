# Native validator session verified

Historical session record. The canonical configuration uses the native-session observation “31 of 32 checks selected.” The older metadata wording “All 31 of 31 checks selected” is preserved as historical provenance; no report bytes or classifications were changed when the metadata was reconciled.

Verified 2026-09-22 (local time). PAC and Acrobat both run and export reports in this session. No reinstall was needed.

## Working control path

Use the computer-use skill's native `@oai/sky` API through `mcp__node_repl__js`. The separate `mcp__cua_repl` connector is browser-only in this session; its empty apps inventory does not establish that native Windows control is unavailable.

Initialize `sky` with `await import("@oai/sky")`, use `list_apps`/`list_windows`, select the returned window with `get_window`, activate it, and inspect `get_window_state`. Use the skill's observe/action/refresh workflow. Accessibility trees were intermittently null; screenshot-based clicks and text entry worked. Some actions only focused a window; observe the result before retrying. Modal dialog screenshots can have different dimensions from the main-window screenshot.

- PAC executable: `C:\Users\iamga\AppData\Local\PAC\PAC.exe`, version 26.1.0.0.
- Acrobat executable: `C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe`, file version 26.2.21931.0.

## End-to-end smoke test: G01-NOOP

Input: `corpus/controls/G01-NOOP.pdf` (32 pages).

PAC: Open document, wait for completion, keep PDF/UA selected, PDF report, save to the evidence directory. The exported report identifies PDF/UA-1, PAC 26.1.0.0, G01-NOOP.pdf, and 2026-09-21 22:41. It states that the PDF/UA requirements checked by PAC are fulfilled, with no warned/failed checkpoints. No AI tab was selected or AI result included. The historical AI-disable registry setting could not be independently reconfirmed from the shell; do not assert it was verified during this smoke test. Dismiss the optional Windows report-viewer chooser with Escape without changing default apps.

- Raw report: `evidence/controls/pac/G01-NOOP.pdf`
- SHA-256: `CC9D8ADB2E7DCF0539DA9020A1E8C2CC388BF8CAED34EEEAE21B03B81E42023F`

Acrobat: Ctrl+O, open the input, search tools for accessibility, choose Accessibility Check. Keep All pages, Create accessibility report enabled, Attach report disabled, and no remediation. Set report folder to `C:\Gauri\ma11ypdf\evidence\controls\acrobat`. Start Checking.

- Raw report: `evidence/controls/acrobat/G01-NOOP.pdf.accreport.html`
- SHA-256: `B300D9B737D92D313EF05EFAC937D1F29E0B668B86DAE363C09A14B54D1C2CC9`
- Result: 29 passed, 0 failed, 2 needs-manual-check, 1 skipped (table Summary). The two manual checks are logical reading order and color contrast.
- Observed configuration: 31 of 32 checks selected in the session note. This agrees with the existing G01 golden report's skipped table Summary and result totals. The former wording "31 of 31" in `data/acrobat_run_metadata.json` is retained in its `historical_metadata_checked_categories` field for provenance.

## Completion boundary

All 18 negative controls now have native PAC PDF reports, native Acrobat HTML reports, and veraPDF PDF/UA-1 reports. The canonical ledger records the relative report paths and SHA-256 hashes; `evidence/controls/validator_summary.json` is the compact audit index. PAC parsing confirms the PDF/UA-1 profile and PAC 26.1.0.0 report identity. Acrobat reports were produced with the native Accessibility Checker / Full Check, all pages selected, report creation enabled, report attachment disabled, and no remediation. The native Acrobat application file version observed in-session was 26.2.21931.0; the historical metadata file retains its original build label 2026.002.21931 and the UI displayed “31 of 32 in all categories.” Both facts are preserved, with 31/32 canonical for the run record.

The G08 and G09 checks temporarily displayed “Not Responding” during rendering but recovered without force-closing Acrobat, and their reports were successfully exported. This completes item 1’s negative-control execution and evidence linkage. It does not authorize an accuracy claim: controls are not positive-study results, and manual checks are not automated failures. The formal ledger now contains two recorded coding fields and adjudication, but independent-human provenance is not substantiated. Do not rerun `execute_controls.py` blindly: it regenerates artifacts and resets statuses. The existing artifact renderer also checks only the first page and needs an all-pages audit before final study-freeze claims.

The raw control findings also preserve baseline behavior that must not be relabeled as mutation detections: both G05 Acrobat reports contain one failed “Lbl and LBody” rule, and both G09 PAC reports contain one failed Natural language checkpoint. The paired no-op and benign reports agree on those findings, so the ledger records them as observations for baseline comparison rather than treating them as positive-study results.
