# Start here: from example to your hospital's workflow

This kit connects meeting evidence with staffing and charge nurse handoff information. Start with the example, agree on your local workflow, then connect one source at a time. You do not need to read every technical file first.

## 1. Understand the two parts

| Part | Purpose | Where to begin |
| --- | --- | --- |
| Charge Nurse Handoff Dashboard | Forms responses, staffing assignments, assigned hours and a shared Excel dashboard. | [Companion repository](https://github.com/true2thecore-cloud/charge-nurse-handoff-dashboard) |
| Hospital Operations Intelligence, this repository | Meeting evidence, reviewed concerns, follow-up, historical comparisons and an Operations View. | Continue below. |

The dashboard supplies snapshots to the intelligence layer. The intelligence layer adds meeting context and follow-through. It does not automatically turn every call-out or transcript mention into a confirmed risk.

The repositories are private during owner review. Anyone copying them needs access until they are published.

## 2. Know what works and what needs setup

| Capability | Available now | Your setup responsibility |
| --- | --- | --- |
| Example workflow | Synthetic meetings, issues, outcomes and reports. | Open the supplied example or run the demo. |
| Manual transcript intake | VTT import, source cues and review drafts. | Obtain approved transcripts, enter the correct meeting time, and review the evidence. |
| Operational memory | Local database, review history, unresolved issues and recorded outcomes. | Choose private storage, a responsible reviewer and local definitions. |
| Staffing and Forms connection | Imports snapshots produced by the companion's export scripts. | Configure source workbooks, response fields and export/import steps. |
| Afternoon staffing date | Companion supports next-business-day, same-date and explicit-date choices. | Configure the 2:45 PM flow, or your chosen time. Friday advances to Monday in next-business-day mode; holidays need an explicit date. |
| Automatically updated reports | Folder watcher refreshes reports when complete approved intake files arrive. | Run it on an approved computer or worker and configure folders. It stops when that worker stops. |
| Teams transcript retrieval | Read-only Graph adapter for a specified meeting. | Obtain tenant permission, a valid token and meeting details. Automatic meeting discovery is not included. |
| Excel Operations View | Office Script imports an operations report into a dedicated sheet. | Configure report delivery and script execution in your tenant. |
| Historical comparisons | Earlier comparable days and chronological evaluation. | Collect real outcomes and validate usefulness locally. These are not validated predictions. |
| AI-assisted review | Agent instructions and prompts for drafting observations and briefs. | Build/configure an approved agent and retain human review. No cloud agent is installed automatically. |
| Spoken morning briefing | An optional extension of the report workflow. | Audio, conversational delivery and briefing triggers are not implemented in this release. |

Downloading a ZIP does not create Power Automate flows, authenticate Microsoft connections or deploy a service. The core works with approved files without a custom EHR integration. Microsoft automation and agent options depend on the organization's permissions and licensing; no universal premium-free deployment is promised.

## 3. See the result before installing anything

1. On the repository page, select **Code > Download ZIP** and extract it.
2. Open `assets/example-brief.html` in a browser from the extracted folder.
3. Look for meeting evidence, open issues, historical comparisons and source references.
4. Review the [morning agenda](../templates/morning-plan-ahead.md) and [afternoon agenda](../templates/afternoon-plan-ahead.md).

**Success looks like:** you can explain which morning concerns remain open and which later evidence updates them. All example data is invented.

**If it does not open:** confirm the ZIP was extracted and ask your technical partner to open the HTML with an approved browser. The [preview image](../assets/operations-preview.png) also shows the report design.

## 4. Choose your route

| Your situation | Follow this route |
| --- | --- |
| You are a leader defining the workflow | Complete step 5, then give your technical partner steps 6 through 8. |
| You can run approved Python and upload files | Follow the [portable setup](PORTABLE-SETUP.md), starting with the demo in step 6. |
| You want Microsoft 365 automation | Establish the manual connection first, then follow [Microsoft setup](MICROSOFT-365.md). |
| Your environment restricts software or connectors | Use the Excel dashboard and structured meeting templates. Ask IT for an approved worker before trying the full historical engine. |
| You want an AI agent | Complete the basic data workflow first, then use [Copilot Studio guidance](COPILOT-STUDIO.md). This is an optional route. |

## 5. Leader: define your local workflow

Write down the following with your technical partner. Use roles in shared templates and keep actual names and contacts in your organization's private configuration.

| Decision | What to supply |
| --- | --- |
| Meetings | Names, planned times, timezone, sequence and reporting departments. The four supplied meetings are examples. |
| Report-out structure | Current state, concern, impact on the plan, action, owner and next check. |
| Staffing date | Next business day, the same date or an explicit date; choose the cutover time and holiday handling. |
| Forms information | Questions and response fields that leaders need to see, such as call-outs, checks, add-ons and comments. |
| Evidence review | Who confirms observations and records corrections, follow-up and resolution. |
| Outcomes | What a delay or other concern means locally, how it is measured and who records what happened. |
| Audience | Who needs the charge dashboard, the operations report, or an optional narrative brief. |

**Success looks like:** the morning and afternoon teams agree on one meeting sequence and how an issue is carried forward and closed. Use the [meeting register](../templates/meeting-register.csv) and [outcome register](../templates/outcome-register.csv).

## 6. Technical partner: run the isolated demonstration

Use approved Python 3.11 or newer. Open a terminal in the extracted repository folder and run:

```powershell
python -m hospital_ops demo
```

Open `data/demo/brief.html`. The demo also produces JSON, CSV and an evaluation report. It uses a separate synthetic database. Do not import operational data into it.

**Success looks like:** the generated report opens and contains invented evidence and outcomes.

**If it fails:** check that Python is available and that the terminal is in the extracted repository folder. On some approved Windows installations, use `py -3` in place of `python`. See [troubleshooting](TROUBLESHOOTING.md).

Next, follow [Portable setup, sections 1 and 2](PORTABLE-SETUP.md) to create the private operational configuration and launch the local workbench. Use [Customization](CUSTOMIZATION.md) to enter the leader's choices. Keep the live database on an approved local disk, outside Git and outside synchronized folders.

## 7. Connect one source at a time

| Order | Action and instructions | Check before continuing |
| --- | --- | --- |
| 1 | Import a test VTT using [Portable setup](PORTABLE-SETUP.md). Review the draft and import confirmed observations. | The report shows the correct meeting, time and supporting cue references. Keyword suggestions alone do not become confirmed findings. |
| 2 | Export a test staffing snapshot using [Companion connection](COMPANION.md). Import it into the intelligence layer. | The date is correct and A1:L46 includes later shifts. A Monday snapshot is labeled Monday, even when captured Friday. |
| 3 | Export and import a test Forms response-table snapshot using the same guide. | The source headers and response values are retained. The charge dashboard remains responsible for selecting its latest response. |
| 4 | Import the generated report JSON using the Operations View script described in that guide. | A dedicated Operations View displays meeting, issue and pattern information. Staffing and handoff detail remains in the existing dashboard sheets and the report's HTML/JSON context. |
| 5 | Review an afternoon update using the same issue identifier as the morning concern. | Explicit resolution updates the current issue state; missing information stays unknown. Earlier as-of reports retain their earlier interpretation. |

Use a separate test environment for these checks. Keep operational content and credentials out of the repository.

**If a connection fails:** first compare the source date, table headers and export format with [Data contracts](DATA-CONTRACTS.md). Fix that individual connection before adding a scheduled flow.

## 8. Add automation after the manual checks pass

1. Choose either manual delivery, the approved-folder watcher, or tenant-configured Microsoft automation.
2. Follow [Microsoft setup](MICROSOFT-365.md) for Forms/staffing transfer and optional Teams retrieval. Follow [Portable setup, section 4](PORTABLE-SETUP.md) for the watcher.
3. Set local meeting times, staffing cutover and report publication times. These are independent settings; changing an agenda time does not create or update a Power Automate schedule.
4. Coordinate writes to the shared Excel workbook. Test a new response and a staffing update in your own tenant.
5. Confirm that the latest expected source appears, its date is correct, and failed or missing inputs remain visible for review.

**Success looks like:** a new approved input reaches the intended report without manually rerunning each step, and the responsible person can identify an unsuccessful run. Local and synthetic tests do not establish that a live tenant connection works.

## 9. Add an agent or morning briefing only if useful

An organization can use the report as evidence for an executive or charge nurse brief. [Copilot Studio guidance](COPILOT-STUDIO.md) and the [leadership brief prompt](../prompts/leadership-brief.md) provide starting material.

Configure the audience, trigger time and approved data access locally. A brief should distinguish current confirmed facts, unresolved concerns, historical associations and missing information, with source dates and references. Historical associations require local validation before being presented as predictions.

Scheduled audio, a conversational commute briefing, proactive Teams alerts and additional adapters are optional extensions, not delivered automations in this package. The repository does not learn from another hospital's private history automatically. Each organization retains and evaluates its own evidence.

Return to the [README](../README.md) for the file overview or [Architecture](ARCHITECTURE.md) for implementation boundaries.
