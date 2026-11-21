# Start the complete readiness workbook workflow

Use this path for the Executive Snapshot, permanent daily Master Table and dated meeting sheets. The earlier portable issue-review commands remain supported but use a different version-1 record format. Do not feed a version-2 reviewed record into the older `hospital_ops review` command.

## 1. Preview the result

Download and extract the repository. Open [the synthetic example workbook](../assets/Readiness%20Synthetic%20Example.xlsx) or [preview image](../assets/readiness-preview.png). It contains invented meeting metrics, a resolved high-risk event still visible inside seven days, two permanent daily rows and dated meeting sheets.

For operational use, copy [the blank readiness workbook](../templates/Daily%20Operational%20Readiness.xlsx) to your approved location. Do not reuse the synthetic workbook for live data.

## 2. Configure your organization

Use approved Python 3.11+ from a terminal in the extracted folder. Windows may require the `tzdata` package for named timezones, obtained through your approved software process.

```powershell
python -m pip install tzdata
python -m hospital_ops.configure
```

The questionnaire asks for meeting names, end times, weekdays, information needs, fields, sources, workbook destination and optional automation preferences. It creates `data/setup/profile.json` and one extraction prompt per selected meeting. It does not authenticate or deploy anything.

Review [Onboarding](ONBOARDING.md) to add new departments/fields or meetings beyond the supplied examples. Then validate:

```powershell
python -m hospital_ops.readiness --profile data/setup/profile.json validate
```

**Success:** the profile validates and generated prompts match what your meetings actually report. A connection is still unverified until tested in the tenant.

## 3. Run the synthetic workflow

```powershell
python -m hospital_ops.readiness_demo
```

This creates a separate synthetic database and `data/readiness-demo/readiness.json`. To test publication, use a separate copy of the synthetic workbook or an empty test workbook. In Excel **Automate > New Script**, paste [UpdateReadinessWorkbook.ts](../scripts/UpdateReadinessWorkbook.ts), save, and pass the JSON text into `payloadJson` when running. Do not select the operational template for this synthetic run.

**Success:** the executive view refreshes, two Master Table rows appear, and repeating the same payload appends zero duplicate rows. The published workbook is a view of reviewed data, not a formula-driven transcript parser.

## 4. Import a reviewed meeting

Export an approved transcript, identify its meeting occurrence and use that meeting's generated extraction prompt. The [reviewed record example](../templates/reviewed-meeting.example.json) shows the exact shape. Keep all real files in approved private storage.

A human checks source references, values, dates, issue matches, owners and severity. Set reviewerRole and use a stable record ID. A correction requires a new record ID for the same occurrence. Numeric fields omit unknown observations. Supplemental source conflicts must be explicitly reviewed.

```powershell
python -m hospital_ops.readiness --profile data/setup/profile.json ingest data/reviewed-meeting.json
python -m hospital_ops.readiness --profile data/setup/profile.json export --date 2027-01-22 --out data/readiness.json
```

Replace the example date and file path with the actual reporting date and reviewed input. Import `data/readiness.json` into the operational workbook using the script. Initially the Master Table has no row: the day has not closed.

**Success:** the meeting sheet and executive values show evidence and dates. The script refuses an unrelated existing sheet or synthetic/operational mix. For a custom field schema, start with an empty dedicated workbook; the publisher creates the mapped sheets. The distributed blank template matches the supplied default schema.

## 5. Close the day

```powershell
python -m hospital_ops.readiness --profile data/setup/profile.json close --date 2027-01-22
python -m hospital_ops.readiness --profile data/setup/profile.json export --date 2027-01-22 --out data/readiness.json
```

The close waits until local closing time, the final meeting's transcript window, and reviewed terminal records for all expected meetings. Use unavailable/not_held records with a reason for missing/cancelled meetings. Pending sources block closure. Publish again after closing to append the frozen daily row. Repeat closing returns the same record. Late corrections update current views and meeting history, never that row.

## 6. Optional approved-folder automation

```powershell
python -m hospital_ops.readiness_watch --profile data/setup/profile.json --inbox "C:\ApprovedOps\Reviewed" --out "C:\ApprovedOps\Published"
```

Use your approved paths. Deliver complete reviewed files with `.readiness.json` suffix, using atomic upload/rename. The worker scans every 60 seconds by default, refreshes `readiness.json`, and attempts today's and yesterday's closing checks. `readiness-status.json` shows intake errors and waiting reasons. The computer and worker must remain running; schedule at sign-in only where permitted. Do not run two writers against the same database. The database stays on approved local storage, even if intake/publication folders sync.

Stop with Ctrl+C. `--once` runs a single scan. Older missed dates require an explicit close command. [Automation setup](AUTOMATION-SETUP.md) explains transcript email, tenant publication and optional brief delivery.

## 7. Optional OR block lookback

Create a private copy of the [block schedule template](../templates/block-schedule.example.json). Enter dated sessions from the approved monthly grid; keep previous versions.

```powershell
python -m hospital_ops.readiness --profile data/setup/profile.json lookback --date 2027-02-19 --schedule data/block-schedule.json
```

The result distinguishes the prior surgeon session from the prior-month matching weekday/block. Only explicitly associated reviewed issues are returned. Supply this context to the briefing prompt; do not present it as a prediction.

Complete the [validation checklist](VALIDATION.md) before using live publication and scheduled briefings.
