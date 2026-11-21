# Microsoft 365 and Power Automate setup

This path connects cloud intake to the portable engine, then writes the resulting brief into Excel. It does not require an OpenAI API key. Copilot Studio is optional for drafting structured observations.

## Choose the deployment route

| Route | Requirements | Capability |
| --- | --- | --- |
| Manual | Approved Python plus exported VTT files | Full local history, review, analysis and reports. |
| Standard-connector file handoff | SharePoint/OneDrive, eligible Excel/Office Scripts entitlement and an approved running worker | Automated intake of files placed in the folder, snapshot transfers, and Excel publication. Transcript download and review can remain manual. |
| Teams API and Copilot assisted | Graph permissions, tenant-approved connectors, applicable premium/AI licensing and the same worker | Automated retrieval of available transcripts and optional draft extraction. Human review remains before observations are confirmed. |

**If Python cannot run:** the agendas, review structure and existing charge dashboard can still be used manually. The full portable history engine needs an approved worker or an IT-hosted adaptation. A cloud-only backend, authenticated API and deployable Power Platform solution are not bundled in version 0.1.0.

## 1. Create the folders

In the approved SharePoint document library or OneDrive for Business location, create:

```text
Operations/
  Intake/       VTT, meeting metadata, approved reviews, staffing snapshots
  Drafts/       AI draft reviews, never automatically imported
  Published/    operations.json, operations.html, operations.csv
```

Grant access according to your organization's rules. Sync only the approved folders to the worker computer. Configure the watcher from [portable setup](PORTABLE-SETUP.md). Keep its SQLite database local. The Power Automate cloud service cannot call `localhost` on your computer; synchronized files are the bridge in this design.

## 2. Start with manual transcript delivery

1. In Teams, export the available meeting transcript as `.vtt` using your permitted meeting access.
2. Save it to `Intake`, for example `2027-01-04-am.vtt`.
3. Copy `templates/meeting.example.json` and change the ID, meeting kind, actual start time and transcript filename.
4. Save it as `2027-01-04-am.meeting.json` in `Intake`.
5. Confirm the watcher imports it. Create and approve its review through the workbench or command line.
6. Save the approved review as `2027-01-04-am.review.json` in `Intake`.
7. Confirm `Published/operations.json` updates.

Do not put draft AI extraction directly in `Intake`. A keyword match or generated interpretation requires source verification.

## 3. Optional automatic Teams retrieval

Two supported paths:

**A. Graph adapter on the approved worker.** Your IT team supplies a short-lived Graph access token through its approved authentication process. The adapter does not acquire, refresh or save credentials. Set `GRAPH_ACCESS_TOKEN` privately in the process environment, then run:

```powershell
python -m hospital_ops --config config/site.local.json graph-pull --organizer USER_ID --meeting-id ONLINE_MEETING_ID --kind plan_ahead_am --starts-at 2027-01-04T09:00:00-05:00
```

Use the actual onlineMeeting ID, not a calendar event ID or the numeric join code. The adapter lists transcript segments, retrieves WebVTT and deduplicates imports. A missing transcript returns `transcript_not_available`; access failures are explicit. Token refresh and scheduled meeting discovery are deployment responsibilities.

**B. Power Automate plus an approved Graph connector.** This is a build recipe, not an importable flow package:

1. Create a recurrence after the meeting's expected end, with the site's timezone.
2. Identify the intended event using its organizer, date and configured meeting name. Prefer an explicit meeting registry to a broad search across unrelated meetings.
3. Resolve the onlineMeeting ID using the supported Graph meeting lookup. Do not substitute the event ID.
4. Call `GET /users/{organizerId}/onlineMeetings/{meetingId}/transcripts`.
5. For each transcript ID, call `/users/{organizerId}/onlineMeetings/{meetingId}/transcripts/{transcriptId}/content` with `Accept: text/vtt`.
6. Create the VTT file in `Intake`. Create its `.meeting.json` after the VTT is saved. Use a stable ID combining meeting and transcript identity.
7. If no transcript exists yet, record “pending” and use a bounded retry, such as three attempts five minutes apart. On `403`, stop and report the permissions issue. On `429`, honor `Retry-After`. Do not repeatedly bypass or broaden permissions.
8. Optionally request a draft review using the [Copilot prompt](../prompts/extract-meeting.md); place the result in `Drafts`. Route it to your chosen reviewer. Only an approved, verified review enters `Intake`.

Microsoft Graph requires the relevant transcript permissions. Application access can require an application access policy; tenant controls can block transcript retrieval or speaker attribution. If attributed VTT is denied, use permitted manual export or implement the documented unattributed format adapter. This release's parser accepts VTT only. [Transcript API and permissions](https://learn.microsoft.com/en-us/graph/api/calltranscript-get?view=graph-rest-1.0), [online meeting lookup](https://learn.microsoft.com/en-us/graph/api/onlinemeeting-get?view=graph-rest-1.0).

## 4. Transfer staffing and handoff snapshots

Follow [the companion bridge](COMPANION.md). Use existing export scripts, then **Create file** to save their string results as `.staffing.json` and `.handoff.json` in `Intake`. Use unique filenames including capture time. Keep the dashboard's existing flows in place.

For the 2:45 PM staffing schedule, choose your local timezone in the Recurrence trigger. Friday selects Monday in next-business-day mode. An explicit-date mode supports holidays. Confirm the source workbook's displayed date before publishing.

## 5. Publish into Excel

1. Open your combined dashboard workbook in Excel for the web.
2. Select **Automate → New Script**. Replace the sample with `scripts/ImportOperationsBrief.ts` and save it as **Import Operations Brief**.
3. Create a Power Automate flow triggered when a file is created or modified in `Published`.
4. Add a condition: filename must equal `operations.json`. Ignore HTML, CSV, temporary and error files.
5. Use **Get file content**. If your connector exposes a base64 `$content` envelope, convert that content with `base64ToString`; if it exposes text directly, use that text. Confirm the result starts with `{` before calling the script.
6. Add **Excel Online (Business) → Run script**, select the intended workbook and **Import Operations Brief**.
7. Set `reportJson` to the JSON text and `sheetName` to `Operations View`.
8. Set trigger concurrency to one. Serialize Excel writes from all flows that share this workbook, ideally through one writer flow. Concurrency one on this flow alone does not coordinate other flows.
9. Save and run a synthetic test. Confirm the Operations View shows the expected date, evidence cutoff and SYNTHETIC banner. It rejects older cutoffs and refuses to overwrite a populated unrelated worksheet.
10. In Teams, add the shared workbook as a tab. Users see the saved Operations View and existing charge dashboard using their normal file permissions. Do not upload a separate local copy and expect it to synchronize.

The script uses fixed cell writes within its dedicated view. It does not insert worksheet rows or rewrite the charge nurse dashboard, staffing source or Forms responses. The staffing snapshot remains A1:L46, including the later-shift columns.

## 6. Confirm licensing and operational ownership

Excel Online (Business) is a standard connector. Office Scripts in Power Automate requires an eligible Microsoft 365 business license and can be restricted by administrators. Graph/HTTP/custom connectors and AI features may require additional licensing or tenant approval. Copilot Studio has separate licensing and usage considerations. Do not label the entire advanced solution “free” or assume a Microsoft 365 Copilot license covers every flow.

Official references, checked November 20, 2026:

- [Excel connector classification and limitations](https://learn.microsoft.com/en-us/connectors/excelonlinebusiness/)
- [Office Scripts with Power Automate](https://learn.microsoft.com/en-us/office/dev/scripts/develop/power-automate-integration)
- [Power Automate licensing FAQ](https://learn.microsoft.com/en-us/power-platform/admin/power-automate-licensing/faqs)
- [Copilot Studio licensing](https://learn.microsoft.com/en-us/microsoft-copilot-studio/billing-licensing)

Assign a workflow owner, source reviewer and backup reviewer. Test a missing transcript, delayed file sync, an expired token and a stopped worker before operational use. Display capture and review timestamps so leaders can recognize stale information.
