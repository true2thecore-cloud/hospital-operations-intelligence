# No-Python acceptance and limits

Run this in a fresh **synthetic** workbook first. Record the flow run ID, script result and observed workbook values. A saved connection or successful action response alone does not establish correct operational output.

| Case | Expected result |
| --- | --- |
| One complete reviewed meeting | Dated meeting sheet, source audit, issues and current snapshot agree with the evidence. |
| Raw draft / missing reviewer | Rejected before any workbook mutation. |
| Missing evidence or wrong numeric type | Rejected; unknown counts are not converted to zero. |
| AM and PM different counts | Distinct dated meeting records; current metric uses the latest applicable observation. |
| Tomorrow's cases | Remain upcoming, not today's actual count. |
| Pending transcript | No invented facts; requested closing remains waiting. |
| Explicit unavailable/not-held record | Reason required, no extracted facts; may satisfy meeting coverage after the time gate. |
| Weekend / cancelled meeting | Use configured weekdays or explicit date override; no invented attendance. |
| After-midnight receipt | Original local meeting date retained; actual end plus delay governs closing. |
| DST clock transition | Repeated local closing time uses the later instant; nonexistent local clock produces a clear waiting/error condition requiring an explicit schedule adjustment. |
| Same ID twice | Zero new records and zero duplicate historical rows. |
| Same ID with changed facts | Rejected; a correction needs a new revision ID. |
| Closed day followed by late correction | Executive/current meeting view updates; closed Master Table row remains byte-equivalent in value. |
| Resolved HIGH/MEDIUM event | Visible until its original event date leaves the seven-calendar-day window. |
| LOW/UNKNOWN concern | Excluded from executive risk tracker; may remain in unresolved handoff/history. |
| Unresolved concern older than seven days | Remains in Hand-Off Review and permanent history. |
| Source source-name/capture/confidence notes | Optional metadata is retained. Absent confidence is UNKNOWN, not inferred. |
| Block lookback | Matches explicit prior surgeon session and previous-month weekday ordinal/block, with evidence and no causal prediction. |
| Unrelated sheet / changed historical schema | Stops before journal/output mutation. |
| Failure after journal commit | Retry rebuilds views without new intake times or changing closed records. |
| Failure before journal commit | Incomplete transaction ignored and counted; source file can be retried. Investigate the count. |
| Damaged committed journal | Fails closed; restore an approved version. |
| Repeated refresh | Numeric counts remain whole numbers; section bars and widths recover; long text remains accessible in Audit Details; row heights do not grow on every run. |
| Tenant flow failure twice | Run marked failed; optional configured notification sends only after actual failure. No false success. |
| Spoken brief | Optional delivery service verified separately; written evidence companion retained. |

## Implementation boundaries

- The Office Script is a complete no-Python processing implementation for **reviewed version-2 records**. It does not transcribe audio, retrieve Outlook/Teams content or run an AI model.
- The hidden journal is append-only by this script, with SHA-256 checksums and a final commit marker. It is not tamper-proof storage or a transactional database. Use approved version history, backups and one writer.
- The publisher reuses the existing layout implementation. Excel can fail between writes across multiple sheets; the journal makes retry recoverable, but does not make those writes atomic.
- New-engine workbooks have a journal and expanded source audit. Existing Python-produced history is not imported automatically. Do not mix both engines on one workbook.
- Changing field order, type, unit or definition after records exist requires a reviewed migration or a new workbook. Meeting names, focus and schedules remain configurable; preserve stable keys and original records.
- Supported guardrails: 100 fields, 50 incoming records per run, 31 closing dates, 500,000 characters of incoming records, 2 million characters of journal state/payload, 20,000 journal/view rows and 32,000 characters per output cell. The script stops rather than dropping historical data. Large hospital-wide deployments require planned archive/storage design and tenant performance tests.
- The wizard's optional source connections and briefing delivery remain unverified until configured in the actual environment. The setup ZIP is not a Power Platform solution package.

## Maintainer checks

End users do not run these commands. Maintainers use Node 24 to regenerate the self-contained browser page and complete Office Script:

```text
node setup/build.mjs
node --test tests/office.test.mjs tests/readiness-office.test.mjs tests/no-python.test.mjs tests/setup-package.test.mjs
```

Keep the original Python regression suite passing because the alternative path is still supported. Compare generated-file checksums after a build. See [original verification](NO-PYTHON-SOURCE-VERIFICATION.md) for preserved sources, clarified rule differences and verification evidence.
