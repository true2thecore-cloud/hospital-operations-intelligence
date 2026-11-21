# Configure retrieval, refresh and optional brief delivery

These are tenant build instructions and local worker commands, not an importable cloud solution. Preserve the stage boundaries so each action has a bounded context, explicit input/output and visible failure status.

## A. Confirm connections

Use the [source register](../templates/source-register.csv) and [connection map](../automation/connection-map.json). Verify the selected account can access each approved calendar series, Outlook folder, Teams artifact, OneDrive/SharePoint location and workbook. Confirm local connector/DLP rules and credential ownership with IT. Do not treat an access preference as successful authentication.

Start with manual VTT and workbook publication when permissions are restricted. Excel/Office Scripts entitlement and AI/Graph/custom connector licensing vary by route. [Microsoft Office Scripts integration](https://learn.microsoft.com/en-us/office/dev/scripts/develop/power-automate-integration) and [Copilot Studio licensing](https://learn.microsoft.com/en-us/microsoft-copilot-studio/billing-licensing) describe platform requirements.

## B. Transcript delivery flow

1. Create a flow for the selected meeting series, using its scheduled end plus the configured delay, initially 60 minutes. Preserve meeting occurrence ID, actual start/end and timezone. A changed meeting time must update the scheduled action.
2. Retrieve the permitted transcript through the existing Graph adapter or approved tenant action. For non-owned meetings, use an authorized shared VTT or permitted artifact route. Recording-to-text conversion is a separately approved service.
3. If unavailable, use bounded retries. Keep pending, denied, missing and not-held distinct. Do not silently replace a transcript with unrelated chat.
4. If email delivery is enabled, send to the configured recipient with meeting name, operating date, occurrence identity and transcript availability in the subject/body. Attach the VTT or provide its approved file reference. A missing transcript produces a status message, not a fabricated attachment.
5. The intake flow watches only the configured sender/folder/subject pattern, validates attachment type, and deduplicates on meeting/source identity. Transcript emails may be in Inbox or Sent Items; configure the relevant folders explicitly. Use an approved full MIME parser or connector attachment action, not fragile HTML scraping.

Microsoft permissions and tenant controls determine availability. See [list transcripts](https://learn.microsoft.com/en-us/graph/api/onlinemeeting-list-transcripts?view=graph-rest-1.0) and [get transcript](https://learn.microsoft.com/en-us/graph/api/calltranscript-get?view=graph-rest-1.0). These actions have not been exercised in the user's tenant by this repository build.

## C. Draft, review and import

1. Supply the meeting-specific generated prompt, common extraction instructions, configured field definitions and numbered evidence to the approved agent/prompt action.
2. Process one meeting occurrence at a time. Split long sources into identified cue ranges if necessary, then consolidate with duplicate/conflict checks before review. Do not lose context such as negation or later corrections at chunk boundaries.
3. Put draft JSON in `Drafts`. A reviewer checks values, source locators, dates, issue continuity and severity. Move only confirmed version-2 records into `Reviewed` using the `.readiness.json` suffix.
4. Run the readiness watcher on an approved worker. It imports reviewed records, publishes a workbook payload and attempts closing checks. Inspect `readiness-status.json` for failures and waiting sources.

Supplemental SPD/vendor emails, overnight supervisor reports, maintained files or Forms handoffs follow the same evidence contract. The organization chooses the source. If no process exists, offer a simple report template; do not claim missing operational facts were collected.

## D. Publish and close

1. Store the blank readiness workbook, or a new empty workbook for a customized field schema, at the approved authoritative location.
2. In Excel Automate, create **Update Readiness Workbook** using `scripts/UpdateReadinessWorkbook.ts`.
3. Create a Power Automate flow triggered by creation/modification of `Published/readiness.json`. Ignore status files and temporary files.
4. Get file content and pass its JSON text as `payloadJson` to **Excel Online (Business) > Run script** for that exact workbook. Decode a base64 content envelope only if the connector returns one.
5. Coordinate one writer for this workbook across all flows. Confirm a sample import updates only readiness-owned sheets. The script rejects unrelated sheets, schema changes, stale payloads and changes to frozen daily rows.
6. Read the script result. Only report completion after successful publication. For a failed run, retry once after re-reading workbook metadata. If it fails again, stop automatic retries and send an error notification only where enabled.
7. At close, the worker requires the local closing time, all expected meeting records and elapsed processing windows. It freezes a daily record once, then the next payload appends it. Never change that row to absorb late information.

Office Scripts called by Power Automate cannot make external API calls; retrieval belongs in connector actions or the approved worker. [Microsoft external-call limitations](https://learn.microsoft.com/en-us/office/dev/scripts/develop/external-calls).

Excel multi-sheet writes are not transactional. A connection interruption can leave partial publication. Run history and save status must remain visible; rerunning the same payload is safe for append rows and refreshes current views. Preserve versioned backups in the authoritative storage system. A downloaded copy is a snapshot, not automatically synchronized.

## E. Optional confirmation and morning brief

Ask whether this is wanted. Configure audience, recipient/channel, local time and source cutoff. Read current readiness JSON, applicable staffing, reviewed overnight updates and relevant dated block lookbacks. Use the full leadership briefing prompt. Leave unreported add-ons out of the narrative. Do not convert historical coincidence into a predicted delay.

For a commute brief, optionally configure an approved speech service or voice-capable agent. Keep a written companion with evidence references. Audio synthesis, push delivery and conversational hosting are not supplied by the local Python engine. Separate the transcript, refresh and briefing actions so one failure does not imply all stages succeeded.

## F. Optional custom API route

The [Swagger scaffold](../automation/custom-connector.swagger2.json) defines retrieval/publication contracts only. It uses a placeholder host and requires an authenticated, governed service implementing those operations. Do not import it as if it deploys endpoints. Prefer standard approved flow actions where sufficient. The local loopback workbench is not an enterprise API.
