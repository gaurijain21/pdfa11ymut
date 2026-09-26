# Validator capability table

Complete the version/build/profile cells from actual run evidence before publication.

| Validator | Version/build | Type | Formal PDF/UA rules | Manual-review output | Semantic/AI component | Profile/configuration |
|---|---|---|---|---|---|---|
| PAC Formal | 26.1.0.0; build `26.1.0.0 (PAC.exe FileVersion/ProductVersion)` | PDF/UA checker | PDF/UA formal/traditional mode; relevant report labels are recorded per row | As reported by tool | No | Formal/traditional PDF/UA check, AI OFF |
| PAC AI | 26.1.0.0; native semantic run not reproducibly completed | AI-assisted semantic analysis | Not equivalent to formal rules | Aggregate panel counts only; no finding identity/text/export | Yes | Separate AI cohort; 34 rows remain aggregate-only future work |
| Adobe Acrobat Accessibility Checker | 2026.002.21931; build `2026.002.21931 (64-bit)` | Commercial accessibility checker | Full Check automated findings, baseline-relative | “Needs Manual Check” retained separately | No AI claim assumed | Accessibility Checker / Full Check; remediation disabled |
| veraPDF | 1.30.2; `Greenfield 1.30.2; Java 17.0.20.1` | Open-source standards validator | Built-in PDF/UA-1 `ua1` profile | No user-facing semantic judgment assumed | No | Profile `ua1` |

PAC Formal and PAC AI must never be merged. Tool differences mean raw output and scope are part of the evidence, not noise to be normalized away.
