# Attach operational instructions to an approved assistant

The complete canonical prompts and skills remain in `prompts/`, `agents/` and `skills/`. Personalized files supplement them under `organization/prompts/` in the wizard's export. Do not replace the detailed source instructions with a generic “summarize the meeting” prompt.

## Shared behavior

Use `agents/no-python-setup-agent.md` for onboarding. Attach the organization profile, source register, approved field map, `prompts/meeting-extraction.md`, `prompts/leadership-brief.md`, the relevant skill files and the reviewed-record example. For each meeting, use its generated prompt with the configured report-out sequence and exact fields. Treat original documents as reference specifications; current clarified immutable-close rules take precedence over older same-day-overwrite instructions.

Separate five responsibilities:

| Responsibility | Inputs | Output / access |
| --- | --- | --- |
| Discover approved sources | Selected meeting identities, date and scope | Found/pending/missing list and actual retrieval results. Read access only. |
| Extract meeting facts | Numbered VTT cues, supplemental approved evidence, configured fields and prior issues | Draft version-2 record plus review notes. No workbook writes. |
| Review | Draft, source evidence and conflict list | Approved record or corrections. Do not fabricate reviewer approval. |
| Publish | Approved JSON, profile and closing requests | RunReadinessNoPython result and workbook link. Single writer. |
| Brief | Current snapshot, open issues, source coverage, upcoming metrics and optional block lookback | Nine-section written brief; optional spoken draft with written citations. |

## Microsoft 365 / Copilot Studio path

1. Start with a knowledge/instruction-based agent if that is what your organization permits. Attach the instructions and approved sources. This alone does not install update tools.
2. For live actions, an authorized maker configures Copilot Studio tools/agent flows for the responsibilities above. Use strings for JSON arguments and compact primitive response fields.
3. The publish action submits records to the approved queue or requests the existing single writer. Do not add a second direct workbook writer.
4. A briefing action may call RunReadinessNoPython with empty records, empty closing dates and `readOnly: true`. It returns the current snapshot and optional lookback without changing the workbook. Do not invent a successful retrieval when the action is absent.
5. Configure credentials, DLP, connection references and authorized source scope in the tenant, then test. Calendar discovery presents candidate meetings for confirmation. It does not decide that all recurring meetings or all emails should be scanned.

Microsoft documents the distinction between the guided agent-building experience and broader Copilot Studio extensibility: [agent experience](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/copilot-studio-experience).

## ChatGPT path

1. Use an organization-approved ChatGPT workspace. Supply the same profile, prompts, skills and permitted source excerpts/files.
2. Where approved apps provide source access, verify actual scope and available actions. Otherwise upload permitted excerpts manually. Uploading the kit does not grant Microsoft access or install `.md` skills as tools.
3. Generate and review the exact record format. Save the approved JSON in the selected intake location, or pass it manually to the Excel script.
4. For automatic handoff, an approved write-capable tool or integration must place the record in the queue. Do not claim a general ChatGPT upload creates an unattended Power Automate flow.
5. For a brief, supply the script's read-only snapshot response or approved workbook views. Use the complete leadership brief prompt. Scheduling, notifications, audio generation and delivery are optional separately configured capabilities.

App availability and actions depend on the workspace and app: [ChatGPT connected apps](https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt).

## Briefing and operational memory

Retain the nine sections: executive summary; department readiness; staffing/coverage; throughput; safety/quality/infection prevention; supply/equipment/vendor; meetings/time-sensitive items; decisions/asks; follow-up. Read the latest approved context first, preserve source dates and conflicts, and prioritize what changes today's actions. Optional staffing, Forms, SPD/vendor or living-file reports retain their own dates and source references.

Use the executive seven-day tracker as a compact concern index, with dated meeting evidence and the permanent journal available for deeper questions. Block lookback uses a supplied, versioned schedule and explicit surgeon/block keys. Historical recurrence is a reason to verify a concern, not evidence that a delay will occur. No trained prediction model is installed by this kit.
