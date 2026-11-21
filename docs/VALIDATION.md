# Readiness acceptance and troubleshooting

Use [the scenario checklist](../templates/acceptance-checklist.csv) to record actual results, evidence and reviewer. A passing local test is not proof of tenant authentication, live transcript access, email delivery or Excel desktop behavior.

## Local checks

```powershell
python -m unittest discover -s tests -v
python -m hospital_ops.readiness_demo
node --test tests/office.test.mjs tests/readiness-office.test.mjs
```

The new tests cover closing gates, permanent daily rows, late revisions, seven-day resolved-event retention/expiry, field types, evidence references, future operating dates, duplicate imports, block lookbacks and generated setup files. Office Script mocks exercise publication retries, append-only history, stale payload rejection, workbook ownership and formula-like source text. Workbook previews and generated file inspection complement these tests; they do not replace a live tenant acceptance run.

## Before production

- Verify only the selected Outlook, Teams, OneDrive/SharePoint, Excel and Graph connections. Verify flow-owner permissions, applicable DLP rules and credential mode.
- Confirm meeting occurrence identity, local timezone and weekdays/holiday overrides.
- Verify field definitions, units and operating dates with the reporting department.
- Confirm authoritative workbook, stable column keys and one coordinated writer.
- Confirm the final meeting window and local closing time. Define how unavailable transcripts are reviewed and recorded.
- Confirm notifications are opt-in, recipients are correct, and success occurs only after the save result.
- Test no transcript, late transcript, denied access, stale source, different AM/PM metrics, duplicate run and interrupted publication.
- Validate source-derived summaries and brief content against the original evidence. No invented owners, severity, counts or add-ons.

## Troubleshooting

| Symptom | Explanation and action |
| --- | --- |
| Master Table has no row yet | Closing is waiting. Check closing time, processing windows, expected meetings and pending sources in the status file. |
| Yesterday's row did not change after a late transcript | Correct behavior. The row is permanent; meeting records/current views carry the new information. |
| Resolved event still appears | Correct inside the seven-calendar-day event window. Resolution does not reset its event date. |
| Older unresolved event left executive tracker | Correct. It remains in Hand-Off Review and Issue History. |
| Earlier value remains on snapshot | No newer validated applicable observation exists. Its original date/time remains visible. |
| Tomorrow's cases do not replace today's | Correct. Use upcomingMetrics for next-day briefing. |
| Historical column schema changed | Do not rewrite history. Create a new workbook/schema migration and preserve the earlier workbook/database. |
| Immutable row differs | Stop. Investigate manual edits, wrong database, or a changed schema. Never force overwrite. |
| Timezone unavailable | Install approved tzdata on Windows. Do not substitute a fixed offset for a daylight-saving timezone. |
| API scaffold fails to connect | The host/endpoints/authentication must be implemented by the organization. The scaffold is not a running service. |
| VTT unavailable for shared recording | Obtain permitted transcript access or an approved transcription step. Do not bypass permissions. |
| Workbook is too large for publication | Use an approved archival/schema plan. The publisher rejects oversized payloads instead of dropping historical rows. |

For an operational pilot, record the configured version, evidence cutoff, acceptance results, worker owner and backup owner. Real-outcome validation is required before treating historical associations as predictive performance.
