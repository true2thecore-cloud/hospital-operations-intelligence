# Source design carried into this release

| Original design material | Reusable destination |
| --- | --- |
| Daily executive brief skill and nine-section output | skills/daily-executive-brief, prompts/leadership-brief.md |
| Daily readiness refresh skill | skills/daily-readiness-refresh, docs/WORKFLOW-SPECIFICATION.md |
| Common and meeting-specific extraction prompts | prompts/meeting-extraction.md and generated local meeting prompts |
| Connection map and action manifest | automation/connection-map.json and automation/action-manifest.json |
| Flow outline and failure handling | automation/flow-outline.json and docs/AUTOMATION-SETUP.md |
| Workbook schema and dated tabs | templates/Daily Operational Readiness.xlsx, scripts/UpdateReadinessWorkbook.ts |
| Validation and troubleshooting | templates/acceptance-checklist.csv and docs/VALIDATION.md |
| Institution-specific workbook and personal identities | Structure adapted; operational contents and personal files excluded |

The original source specifications disagree in places. This release follows the clarified requirements: current executive view; immutable daily master row only at close; seven calendar days of high/medium events including resolved ones; known values retain their dates; no invented add-ons. Source prompts are reference designs, not proof that tenant connectors are installed.
