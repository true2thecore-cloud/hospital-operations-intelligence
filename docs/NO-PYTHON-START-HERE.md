# Start here: no-Python development preview

This branch adds a working Excel processing path and an offline setup wizard. It keeps the original Python path, operational prompts, Markdown files, skills and templates. It is not a production release or a one-click Microsoft installer.

## 1. Open the guide

Download this branch as a ZIP and extract it. Open **setup/index.html** in Edge or Chrome. Open the downloaded file, not GitHub's source-code view. No server, Python, Node installation or AI API key is needed to use the wizard.

Complete its eight steps. Choose meetings, names, days, report-out sequence, questions, metrics, sources, closing rules and optional briefing preferences. The page runs offline and does not connect to accounts. Save your profile to resume later. The downloaded kit includes all canonical operational MD/skill files and separate personalized prompts under `organization/prompts/`.

Download generates every meeting prompt whether or not you click Preview first. Each prompt includes an empty draft record with that meeting's key, placeholders for the actual occurrence and an unreviewed role. The separate synthetic example and preview pictures are fixed demonstrations, not your customized output. Read `CONNECTION-SETUP-NOTES.md` and `organization/setup-checks.json` in the exported kit for unfinished setup choices.

On Sources, a SharePoint/OneDrive Meetings folder belongs in the raw transcript folder field. Email folders are names such as `Inbox; Sent Items`, not a mailbox address or a Yahoo/Outlook browser URL. The flow connects the mailbox separately and selects each actual folder. A workbook folder link can describe the destination, but the flow must select the actual `.xlsx` file. Blank meeting questions or report-out order are allowed for a draft and listed for completion before live use.

## 2. Start an isolated Excel pilot

1. Create a **new blank .xlsx workbook** in your approved OneDrive for Business or SharePoint location. Use a synthetic profile with `datasetMode: "synthetic"`. Keep the existing operational workbook unchanged.
2. In Excel, open **Automate → New Script**. Replace the sample code with the complete contents of `scripts/RunReadinessNoPython.ts`. Save it as **RunReadinessNoPython**.
3. Run it with the parameters below. The generated `organization/readiness-profile.json` supplies `profileJson`. Use the wizard's synthetic example or a reviewed JSON array for intake.

| Script parameter | What to enter |
| --- | --- |
| `profileJson` | Complete organization profile JSON, with synthetic mode for the pilot. |
| `reviewedRecordsJson` | Array of reviewed version-2 records, or `[]` to refresh without new records. |
| `reportDate` | `YYYY-MM-DD`, or blank for today's date in the profile timezone. |
| `closeDatesJson` | Dates to try closing, such as `["2027-01-22"]`; use actual pilot dates, not this future example. `[]` means do not close. |
| `blockScheduleJson` | Optional complete version-1 block schedule JSON, or blank. |
| `readOnly` | `true` validates and returns a preview without writing; `false` commits and refreshes. |

4. Start with `readOnly: true`. A valid response says `validated_only`. This is validation, not a saved workbook.
5. Run the same inputs with `readOnly: false`. A successful response says `updated`. Confirm the Executive Snapshot, dated meeting sheets, Source Audit Log, Hand-Off Review and Issue History appear. Master Table receives a row only when a requested day passes closing checks.
6. Repeat the same run. It must add zero new records and no duplicate historical rows. Check the formatting again.

The hidden `_Readiness Journal` is the runtime's permanent record store. Do not delete or manually edit it. Workbook access controls still apply; hiding a sheet does not secure its contents. Use one writer for this workbook.

## 3. Use your assistant for extraction

Open your organization's approved Copilot or ChatGPT environment. Supply the generated meeting prompt, matching approved transcript or excerpts, prior issue IDs and the record example. The assistant drafts a structured record. A person verifies the facts, evidence locators, operating date, issue matches and severity, then replaces `REPLACE_WITH_ROLE` with the reviewer's role.

The Excel script accepts reviewed facts, not raw audio or VTT. It does not invent a transcript parser or run an AI model. Draft records fail intake until reviewed. Missing values stay unknown. Instructions found inside an email or transcript are source content, never permission to alter the workflow.

Reviewer placeholders are rejected in every mode. Example, sample, synthetic and test reviewer labels are accepted only in isolated synthetic mode and rejected for operational intake. The role field is an attestation, not an authenticated approval system. A person or configured approval step must control admission to the Reviewed Records folder. Existing committed history is not rewritten by this check.

The `.md` skills are reusable instructions. They are not automatically installed Microsoft tools. Follow [agent setup](NO-PYTHON-AGENTS.md) to attach instructions and configure actual actions.

## 4. Connect automatic updates

Use [the prepared action sequence](NO-PYTHON-AUTOMATION.md). The single recurring worker reads approved record files and calls the same Excel script. Separate intake actions may gather raw transcripts, but must not write the workbook concurrently. You select the accounts, folders, workbook and saved script in Power Automate.

The local kit does not include an import-tested Power Platform solution ZIP. The action maps are complete implementation recipes with parameters and expressions. A maker must create and test the flow in the destination environment. A future tenant-authored solution export can reduce these clicks further.

## 5. Accept before operational use

Run [the acceptance checklist](NO-PYTHON-ACCEPTANCE.md). Confirm both correctness and access in the actual tenant. A green flow step alone is not proof of the intended workbook contents. If accepted, create a separate fresh workbook with `datasetMode: "operational"` and the reviewed organization profile.

Do not run the new engine against a populated Python-generated workbook. Both paths preserve the same business rules, but their journal/serialization formats differ. Keep the original archive and use an explicit migration if combined history is required.

## What works and what remains local

| Capability | Included | Target-environment work |
| --- | --- | --- |
| Offline wizard and personalized prompts | Runnable browser page | Choose organization settings. |
| Intake, daily close, history and snapshots | Complete Office Script and shared TypeScript engine | Save the script and verify it in Excel. |
| Formatting and long-text details | Existing publisher reused in the generated script | Visual acceptance in tenant Excel. |
| Automatic workbook refresh | Exact recurring-worker action map | Create flow, authenticate connections, test concurrency/retries. |
| Transcript retrieval | Source search sequence and fallback routes | Grant access and configure retrieval for selected meetings. |
| Extraction and executive briefing | Full operational prompts and skills | Approved assistant and review process. |
| Spoken or scheduled briefing | Optional instructions and delivery contract | Configure and test the delivery service; disabled by default. |

Office Scripts and Power Automate availability depend on the account, organization policy and licensing. The standard Excel connector alone does not establish entitlement for every optional AI or Graph action. See [Microsoft's integration guidance](https://learn.microsoft.com/en-us/office/dev/scripts/develop/power-automate-integration) and [Excel connector limits](https://learn.microsoft.com/en-us/connectors/excelonlinebusiness/).
