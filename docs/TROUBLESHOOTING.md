# Troubleshooting

| Symptom | Check and action |
| --- | --- |
| Transcript imported but no warnings | Import alone creates evidence. Add a verified review, and confirm the configured rule's signals are active at the checkpoint. |
| A keyword says “no callouts” but appears as a suggestion | Suggestions are mentions only. Review negation and set cleared or omit the signal as appropriate. |
| Historical warning lacks a percentage | Insufficient comparable, known-outcome days. The software intentionally avoids a probability claim. |
| An issue stayed open after a meeting omitted it | Omission is not resolution. Add an explicit reviewed cleared state with source evidence. |
| Duplicate-ID error | Identical imports deduplicate. Changed content needs a new revision ID. Do not overwrite a source record. |
| Review refers to missing cue | Use cue IDs from that exact imported meeting, not another transcript's numbering. |
| Old historical files do not count as prospective predictions | Availability begins at actual receipt. Do not backdate them to manufacture a prospective result. |
| Friday staffing is wrong | Confirm next-business-day mode, local trigger date, source B1 date, and the expected Monday tab. Use explicit date for a holiday. |
| Graph returns 403 | Check application/delegated consent, application access policy, tenant transcript controls and speaker attribution. Use permitted manual VTT export while IT resolves access. |
| Graph returns no transcripts | Meeting may not be transcribed, may not have finished processing, may have expired, or the wrong onlineMeeting ID was supplied. Record pending/missing explicitly. |
| Graph token expired | Reauthenticate through your approved process. The adapter does not refresh tokens. |
| Watcher reports missing timezone data on Windows | Install `tzdata` through the approved package process, or use explicit-date CLI operations. |
| Published files stopped changing | Confirm worker process, local clock/timezone, folder sync and `intake-errors.json`. No input changes normally means no rewrite until the next date. |
| Excel flow succeeds but view is stale | Check workbook and script selections, source JSON cutoff, file synchronization, and whether an older report was rejected. Compare actual file IDs, not just display names. |
| Excel rows appear overwritten | Use only the dedicated marked Operations View. The importer refuses populated unrelated sheets. Do not point it to the charge dashboard. |
| Two flows interfere with Excel | Coordinate a single workbook writer across flows. Setting concurrency one on only one flow does not serialize all writers. |
| Times are shifted | Preserve original timestamps with explicit offsets. Do not apply a second timezone conversion or append Z to a local timestamp. |
| Your network blocks Python or connectors | Use the agendas and manual Excel workflow; request an approved worker path before claiming automated historical intelligence is deployed. |

When reporting an issue on GitHub, provide the software version, sanitized configuration, command, error message and a synthetic reproduction. Do not attach operational transcripts, credentials or real staffing data.
