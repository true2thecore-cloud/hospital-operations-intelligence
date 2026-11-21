# Portable setup

For the complete version-2 readiness workbook workflow, start with [Readiness quickstart](READINESS-QUICKSTART.md). The instructions below describe the retained version-1 baseline unless stated otherwise.

## 1. Prepare a private workspace

Download and extract the repository. Use an approved Python 3.11+ installation. Open PowerShell or a terminal in the extracted repository folder. If `python` is not found on Windows, your approved installation may use `py -3` instead.

```powershell
Copy-Item config/site.example.json config/site.local.json
python -m hospital_ops --config config/site.local.json init
```

Edit `site.local.json` with your hospital label, leader role, meeting sequence and signal definitions. Keep `datasetMode` set to `operational`. Local configuration and `data/` are excluded from Git. Store the SQLite database on a local approved disk, not a network share or synchronized OneDrive folder.

## 2. Use the browser workbench

```powershell
python -m hospital_ops --config config/site.local.json serve
```

Open `http://127.0.0.1:8765`. Keep the terminal open while using the workbench.

1. Select the meeting type.
2. Enter its actual local start date/time with a UTC offset, for example `2027-01-04T09:00:00-05:00`. During daylight saving time, use the applicable offset. Do not relabel a local time as UTC.
3. Select the `.vtt` file and click **Import transcript**.
4. The workbench supplies a meeting ID. Click **Get review draft**.
5. Read the cue text and suggestions. A mention can describe a resolved issue, a negation, a hypothetical or another date. Suggestions do not change the dashboard.
6. Copy the `reviewTemplate` object into a JSON file. Use `templates/review.example.json` for the entry shape. Add only confirmed observations, with the exact cue IDs.
7. Set `reviewerRole`. Use a stable `issueId` across follow-up meetings. For a correction, create a new review ID and include the complete corrected interpretation of that meeting.
8. Import the reviewed JSON. Enter the report date and open the brief.
9. Download report JSON if you want the Excel Operations View.

The browser UI is intentionally local and single-user. It is not an authenticated web application for a hospital network. Do not expose its port through a tunnel, reverse proxy or public address.

## 3. Command-line equivalent

```powershell
python -m hospital_ops --config config/site.local.json ingest examples/morning.vtt --kind plan_ahead_am --starts-at 2026-01-05T09:00:00-05:00 --meeting-id example-am
python -m hospital_ops --config config/site.local.json draft example-am --out data/draft.json
python -m hospital_ops --config config/site.local.json review templates/review.example.json
python -m hospital_ops --config config/site.local.json report --date 2026-01-05 --out data/morning-brief
```

Run this example only in a separate test database if you have begun operational use. Add `--db data/test.sqlite` before the command. Production observations should come from your reviewed evidence, not the sample file.

The three outputs are `morning-brief.html`, `morning-brief.json`, and `morning-brief.csv`. HTML works offline and includes source evidence. CSV opens in Excel. JSON is accepted by `scripts/ImportOperationsBrief.ts`.

## 4. Watch an approved folder

The watcher reads complete intake files and refreshes the brief when new records arrive or the local calendar date changes. Windows may need the small `tzdata` package for IANA timezone support. Obtain it through your approved package process; the explicit-date CLI and workbench do not require it.

```powershell
python -m pip install tzdata
python -m hospital_ops --config config/site.local.json watch --inbox "C:\ApprovedOps\Intake" --out "C:\ApprovedOps\Published" --interval 60
```

Use organization-approved paths. `Intake` and `Published` can be approved SharePoint/OneDrive synchronized folders. Keep the database itself local. The computer must remain running, signed in where sync requires it, and connected for cloud sync. If IT permits, schedule the same command at sign-in with Task Scheduler. Set the working directory to this repository. Stop with Ctrl+C. `--once` performs one scan.

| File suffix | Content |
| --- | --- |
| `.meeting.json` | `templates/meeting.example.json`, referencing a VTT in the same intake folder. |
| `.review.json` | A reviewed observation object. Transcripts must already exist or arrive in the same scan. |
| `.staffing.json` | Companion staffing export JSON. |
| `.handoff.json` | Companion handoff export JSON. |

Write files atomically, or upload the VTT first and its metadata second. Partial JSON is not ingested; the next scan retries it. Duplicate IDs with identical contents are skipped. Conflicting changes require a new revision ID. Archive processed intake files after verifying the output; persistent records remain in the database.

Outputs are `operations.html`, `operations.json`, `operations.csv` and `intake-errors.json`. Failed intake files are listed for review and do not stop valid imports. The worker never emails or posts messages.
