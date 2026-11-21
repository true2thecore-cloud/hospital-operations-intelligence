# Original-material verification for this development branch

The original Automation Building package, two perioperative meeting documents and reference workbook were inspected read-only. Thirty-three source artifacts were fingerprinted in a private local evidence manifest. No original operational workbook, transcript, personal identity, tenant path or credentials are copied into this repository.

The workbook structure was checked directly: 139 tabs, beginning with Executive Snapshot, Master Table, Legend and Hand-Off Review, followed by dated meeting tabs. Its Master Table has one date column plus census/capacity/discharge, surgical/receiving-bed, escalation, throughput and source-confidence fields. The reusable profile preserves these concepts with configurable department labels and stable keys.

## Requirement coverage

| Original requirement | Preserved or added destination | Verification / boundary |
| --- | --- | --- |
| Full daily executive brief: recent calendar, email, Teams and staffing context; nine-section output | Existing `prompts/leadership-brief.md` and `skills/daily-executive-brief/SKILL.md`; new agent setup guide | Canonical files unchanged. Generated brief adds organization preferences. Actual retrieval requires configured actions. |
| Daily readiness skill and separate extraction, refresh, failure and validation blocks | Existing refresh/follow-through skills plus no-Python guides and action map | Kept intact; no generic summary substituted. |
| Common and meeting-specific extraction | Existing common prompt plus generated meeting prompts and field maps | Missing values, evidence, observed/applicable dates and review gate validated by runtime tests. |
| Detailed morning report-out and operational follow-up | `prompts/perioperative-plan-ahead-am.md` and perioperative profile | Compared with the original morning document: starts, cardiac, PreOp, PACU, OR charge, SPD, specialty, Biomed, throughput/support, patient experience, supply chain and assistant managers. |
| Afternoon room/staffing and throughput questions | `prompts/perioperative-plan-ahead-pm.md` and added typed fields | Compared with the afternoon document: anesthesia tomorrow, running rooms, RN/CST coverage, remaining PreOp/PACU cases, unit staffing and late-hold support. |
| Source discovery through calendar, Teams, shared files and transcript email | Agent guide, source choices and transcript-intake sequence | Inbox and Sent Items retained. Manual fallback explicit. No claim of live retrieval. |
| Current executive view, master history and dated meeting tabs | Shared TypeScript runtime and generated Office Script | Synthetic intake, repeat runs, morning/afternoon values and frozen daily rows checked. |
| Source status, names, retrieval timestamp, confidence and notes | Source Audit Log, optional source metadata and immutable journal | Missing confidence is UNKNOWN; optional `capturedAt` is separate from runtime receipt time. No confidence inferred from source type. |
| Unresolved handoff and resolved history | Snapshot/open issues, seven-day events and Issue History | Resolved events remain in the window; old unresolved issues remain in handoff. |
| Workbook formatting and audit readability | Existing publisher reused by generated script | Repeated-refresh regression tests preserve numeric formats, section colors, row heights and complete long-text continuation. |
| One retry, failure after second attempt, concise confirmation | Prepared worker/action map and failure instructions | Tenant configuration and actual notification tests still required. |
| Connection map, custom connector and agent tools | Existing scaffold preserved; no-Python path uses file actions and Excel Run script | Original Swagger file explicitly required a real endpoint. No endpoint is invented or advertised as deployed. |
| Configurable setup for other departments | Eight-step wizard, custom fields/units, meeting roles/order and source choices | Generated profile and prompts retain canonical operational content. |
| Historical OR block review | Versioned schedule input and TypeScript lookback | Previous session and previous-month matching block checked; historical context is not a validated prediction. |
| Staffing and charge Forms companion | Existing companion contracts retained; no-Python source-selection and review guidance added | Snapshot evidence feeds reviewed records. Live cross-workbook retrieval remains a tenant integration test. |

## Deliberate differences from older originals

The later user clarifications govern this branch:

- Executive Snapshot refreshes current validated information. Its concern tracker contains only the last seven calendar days of HIGH/MEDIUM events, including resolved events until the original event date expires.
- Master Table appends one immutable row per date only after the configurable closing gate and meeting processing checks. Older instructions allowing same-day overwrites are not carried into the new engine.
- Late corrections retain a new record revision and refresh current views, without rewriting a closed day.
- No unsupported add-ons, headcounts, risk levels, owners, deadlines or source confidence are invented.
- The original patient-movement example is treated as organization-specific practice, not a universal clinical protocol.
- Notifications and audio are optional and disabled until configured. Source-file instructions do not authorize sending messages.

## Local proof versus production proof

Local checks cover shared-engine behavior, full Office Script execution against a workbook test adapter, preserved legacy regressions, browser wizard/export behavior and generated bundle integrity. A TypeScript 4.0.3 check with the used Excel API signatures checks language compatibility; it is not the tenant Office Scripts compiler.

Microsoft sign-in, DLP, actual Office Scripts execution, flow creation/import, connector permissions, unattended retrieval, tenant performance and spoken delivery are **not verified by local tests**. Complete `NO-PYTHON-ACCEPTANCE.md` in an approved test environment before merging or enabling production automation.

Existing canonical operational prompts, skill MD files, agents and workbook templates are preserved byte-for-byte against the branch base. New files supplement them. README and CI changes only expose and test the new route. The original Python runtime remains available and unchanged.
