# Connect the no-Python worker

Use this after the manual Excel pilot passes. All steps operate inside the organization's environment. No custom API host, Python service or premium AI action is required for the reviewed-JSON workbook path. Availability of Office Scripts and each selected connector must still be confirmed. Optional automatic extraction, Graph retrieval or audio may have additional licensing and permissions.

## Prepare three files and one folder

- `readiness-profile.json`: reviewed profile from the wizard.
- `closing-dates.json`: JSON array of dates still awaiting close, initially `[]`. The worker also adds yesterday and today automatically.
- Optional `block-schedule.json`: versioned OR block sessions. Omit and use an empty parameter if not needed.
- `Reviewed Records`: only approved version-2 JSON arrays. Keep drafts and raw VTT in different folders. Use immutable revision IDs; a correction gets a new ID. Each file may contain at most 50 records and be at most 500,000 characters.

Keep these in approved storage, separate from the GitHub repository. Store flow configuration privately. Start with a small pilot. The Excel connector has file, request, throttling and runtime limits; this workbook engine also fails explicitly before truncating oversized history.

## One scheduled writer, ready-to-map sequence

Create a **Scheduled cloud flow**. Use a 15-minute recurrence for the pilot, or a cadence appropriate to your meeting times. Set **trigger concurrency control to On, degree 1**. Disable concurrent workbook writes from other flows and do not manually run the script while the worker is running.

Use these exact action names if you paste the expressions below. Choose either SharePoint or OneDrive for Business file actions consistently. OneDrive action names are shown; SharePoint may expose file content under a different dynamic-content label.

| Order / action name | Action and mapping | Success condition |
| --- | --- | --- |
| `Read_profile` | Get file content for `readiness-profile.json`. | JSON text is readable. |
| `Profile_text` | Compose: choose **File content** from Read_profile. If the connector provides `$content`, decode that base64 property first. Verify the Compose output begins with `{`. | Plain JSON text, not the content wrapper. |
| `Local_day` | Compose with `convertTimeZone(utcNow(),'UTC','Eastern Standard Time','yyyy-MM-dd')`. Replace the Windows timezone label from the wizard. Do not pass an IANA label here. | Actual local calendar date. |
| `Read_closing_dates` | Get file content for `closing-dates.json`. | Array of ISO calendar dates. |
| `Closing_dates_text` | Compose using the decoded file content, as with Profile_text. | Plain JSON array. |
| `List_reviewed_files` | List files in the approved folder; enable pagination and set a sufficient limit. Restrict intake to the chosen folder and `.json` files. | No raw transcripts or drafts enter intake. |
| `For_each_reviewed_file` | Apply to each listed file, **concurrency off / degree 1**. | Files processed serially. |
| `Read_record_file` (inside loop) | Get file content by the listed file identifier. | Plain JSON array after decoding as needed. |
| `Record_text` (inside loop) | Compose decoded content. | Array begins with `[`. |
| `Ingest_and_refresh` (inside loop) | Excel Online (Business), **Run script**, select target workbook and saved RunReadinessNoPython. Map profileJson to Profile_text; reviewedRecordsJson to Record_text; reportDate to Local_day; closeDatesJson to `[]`; blockScheduleJson blank; readOnly false. | Returned result JSON has `status: updated`. |
| `Dates_to_try` (after loop) | Compose expression below. | Unique prior unfinished dates plus yesterday and today. |
| `Refresh_and_close` (after loop) | Same Run script. reviewedRecordsJson `[]`; closeDatesJson `string(outputs('Dates_to_try'))`; reportDate Local_day; profileJson Profile_text; readOnly false; optional block schedule file text. | Snapshot refreshed, each requested date returns `closed` or `waiting`. |
| `Worker_result` | Compose: `json(body('Refresh_and_close')?['result'])` | Structured runtime result for subsequent checks. |
| `Waiting_dates` | Filter array over `outputs('Worker_result')?['closing']`, keeping `status` equal to `waiting`. | Pending days retained, including older missing transcripts. |
| `Waiting_date_strings` | Select in **text mode** over Waiting_dates, expression `item()?['date']`. | Array of strings, not objects. |
| `Save_closing_queue` | Update closing-dates.json with `string(body('Waiting_date_strings'))`. | Unfinished dates survive tomorrow's run. |
| `Log_completion` | Append run metadata to an approved list/log: run ID, status, date, source count, waiting dates and workbook link. | Explicit final status, not an assumed success. |

`Dates_to_try` expression:

```text
union(json(outputs('Closing_dates_text')),createArray(formatDateTime(addDays(outputs('Local_day'),-1),'yyyy-MM-dd'),outputs('Local_day')))
```

If the date queue exceeds 31 days, stop and resolve backlog in reviewed batches. Do not drop waiting dates. The recurrence refreshes the seven-day view even if no new transcript arrives. It attempts closing only after all intake files for this run have been processed.

Keep approved record files available for retries during the pilot. Re-reading identical IDs is safe. For larger installations, use a reviewed queue/archive policy after successful intake; the workbook journal retains committed records. Do not silently limit listing to the first page. Monitor history size and plan archive/migration before limits are reached.

## Failures, retries and notifications

Put worker actions inside a **Try** scope. Configure the script action retry policy for one retry with a suitable delay, then a **Catch** scope that runs after failure or timeout. If both attempts fail, record the failure and optionally notify the configured recipient. Do not claim the workbook refreshed. Do not advance a source file to processed until its script action returns success.

If a script committed journal records but failed during output formatting, a retry rebuilds views from the committed journal using the original intake times and frozen daily records. If a write stopped before its journal commit marker, the incomplete transaction remains visible in the diagnostic count and is ignored. Investigate any nonzero count. A damaged committed checksum fails closed; restore an approved workbook version.

If final queue saving fails, rerunning is safe: an already closed day returns its existing close. Limit all writers across flows, not just parallel actions within one flow.

## Transcript intake, separate from the workbook writer

For each confirmed meeting occurrence:

1. Capture stable meeting ID, local meeting date, scheduled/actual end and transcript source route.
2. Check for a transcript at end time plus the configured delay, default 60 minutes. Use the actual end if later. A missing transcript stays pending while retries remain.
3. Retrieve permitted Teams transcripts or check the approved shared folder. If access is unavailable, request the owner's approved shared file. Do not assume meeting attendance grants transcript access.
4. For email intake, search both the configured Inbox and Sent Items folders by subject, meeting identity and date. Keep the email/attachment reference and retrieval timestamp. Do not forward transcripts by default.
5. Run the generated meeting-specific extraction prompt. Review the draft with evidence cues. Only approved JSON goes into Reviewed Records. A transcript-free run does not create invented facts or an all-clear.
6. If the meeting was cancelled or the source is unavailable, create an explicit `not_held` or `unavailable` record with a reason and no facts. A person decides this status; elapsed time alone is not confirmation.

The separate stages preserve context: discovery, extraction, review, workbook update and briefing. They can be separate flows/agent tools, but only one worker writes the readiness workbook. Their implementation status is listed in `automation/no-python-workflow.json`.

## Tenant import and proof

The JSON action map is not an importable solution. A tenant maker can package the tested flows, agent, connection references and environment variables into a Power Platform solution after local acceptance. Do not rename the setup ZIP as a solution ZIP. Microsoft requires the destination connections and authentication to be configured when importing an agent solution: [solution import/export](https://learn.microsoft.com/en-us/microsoft-copilot-studio/authoring-solutions-import-export).
