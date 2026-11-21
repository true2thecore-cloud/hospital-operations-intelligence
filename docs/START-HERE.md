# Start here

This kit preserves the operating sequence while letting your organization choose its meetings, departments, sources, field definitions, workbook location and optional automation.

## 1. See the finished structure

Download and extract the repository. Open the [synthetic workbook](../assets/Readiness%20Synthetic%20Example.xlsx) or [preview](../assets/readiness-preview.png). Inspect Executive Snapshot, Master Table, Hand-Off Review, Source Audit Log, Issue History and dated meeting sheets. The example is invented; it is not your live data.

## 2. Choose your role

| You are | Begin with |
| --- | --- |
| A leader defining the workflow | [Organization questions](ONBOARDING.md). Decide what each meeting must report and which sources are approved. |
| A technical partner implementing it | [Readiness quickstart](READINESS-QUICKSTART.md). Run the demo, configure the site, import a reviewed meeting and verify the workbook. |
| A Microsoft 365 builder | Complete the manual test, then follow [Automation setup](AUTOMATION-SETUP.md). |
| Restricted from running software | Use the blank workbook and meeting templates manually; ask IT for an approved worker before promising automatic refresh. |
| Already using the charge dashboard | Keep its working staffing/Forms flows and use [Companion connection](COMPANION.md). |

## 3. Know what changes and what stays fixed

Customize names, times, weekdays, local source locations, departments, field definitions and recipients. Preserve these record rules:

- Executive Snapshot refreshes validated known information with dates.
- Only HIGH/MEDIUM events appear in its rolling seven-calendar-day tracker. Resolved events remain until their original event date ages out.
- Master Table appends one permanent row per closed day and never refreshes that row.
- Meeting evidence and corrections remain traceable; older unresolved concerns remain in handoff/history.
- Closing occurs after the configured time and final transcript-processing window, with expected meetings accounted for.
- Unreported add-ons and missing facts are not invented.

## 4. Configure and verify one complete day

Use the questionnaire or an edited profile to generate meeting-specific extraction prompts. Review the mapping before granting tenant access. Import approved evidence, verify a metric and concern, publish the workbook, close the date, and rerun to confirm no duplicate daily row. Follow [the acceptance checklist](VALIDATION.md).

## 5. Add only the automation you want

Transcript email delivery, scheduled refresh, confirmation messages, morning briefings and audio are separate choices. Working local commands and the Office Script are supplied. Microsoft connections require tenant setup. Audio hosting and department-to-department agent sharing are optional extensions, not installed services.

The detailed [workflow specification](WORKFLOW-SPECIFICATION.md), [briefing prompt](../prompts/leadership-brief.md), [source mapping](SOURCE-TRACEABILITY.md) and [automation guide](AUTOMATION-SETUP.md) explain the complete chain. The repository does not grant permissions or silently create agents when uploaded.
