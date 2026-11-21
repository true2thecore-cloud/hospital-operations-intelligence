# Full readiness workflow

This specification preserves the original surgical operations workflow while replacing personal names, hospital units, paths and recipients with configuration. It supplements the version-1 portable engine rather than silently changing that engine's contracts.

## The six stages

1. **Configure:** ask which organization, departments, meeting series, recurring days, timezone, information needs, workbook name/location and optional deliveries apply. Confirm scope before discovery. A scheduled meeting is not proof that a transcript exists.
2. **Retrieve:** obtain approved VTT transcripts, then permitted supplemental chat, email, living files, staffing and Forms snapshots. Default transcript check is 60 minutes after scheduled end, configurable. Retain actual meeting times and source identity. For a non-owned meeting, use authorized shared transcript/file access; a recording alone still requires an approved transcription process.
3. **Extract and review:** use each meeting's generated field template. Preserve units, operating date, observation time, source reference and cue/record locator. Missing is not zero. Regex can assist extraction but cannot guarantee semantic correctness. AI drafts require review. Unknown severity is not promoted into the high/medium tracker.
4. **Refresh:** publish current validated metrics and seven-day high/medium events on Executive Snapshot. Keep known values with their original dates when later meetings omit them. Planned next-day volume must not replace today's volume. Carry unresolved issues in Hand-Off Review independently of the seven-day display.
5. **Close:** after the configured local closing time and every expected meeting's processing window, append one permanent Master Table row. Expected meetings must have a reviewed processed, unavailable or not-held record. Pending sources block closure. An operator can explicitly record unavailable after investigation, never silently turn a timeout into a successful extraction.
6. **Brief and compare:** use current snapshot, upcoming operating-date observations, unresolved issues, applicable staffing and authorized supplemental updates. Consult matching dated block sessions when useful. Preserve uncertainty; association does not establish causation or a validated forecast.

## Record rules

| View | Rule |
| --- | --- |
| Executive Snapshot | Refresh from validated evidence. High/medium events include resolved ones for event date through event date + 6 days. On day 8 they leave this view only. |
| Master Table | Exactly one immutable row per closed local date. Never refreshed. Late evidence goes to dated records and current views. |
| Dated meeting sheets | One sheet per meeting occurrence, updated for a reviewed correction. The source/review revisions remain immutable in the database and audit/history sheets. |
| Issue History | Append every reviewed issue revision with record identity, event date, status and evidence. |
| Hand-Off Review | Current unresolved issues, including those older than seven days. Explicit resolution required. |
| Source Audit Log | Append source status for each reviewed revision. Distinguish missing, pending, denied and not applicable. |
| Audit Details | Generated reading view for long cell text. Continuation parts preserve the full text and identify the source sheet, cell and field. Refreshing this view never changes the original historical values. |

The closed daily summary includes concerns raised or updated that day, including resolved concerns, plus unresolved carry-forward. Resolution before closing does not erase an event from that day's permanent summary.

If closing is missed because the worker was stopped, an explicit later close uses evidence available at that actual close time and records that time. It never pretends to have closed earlier. Repeat close returns the original record. Changes to the field schema require an explicit new workbook/schema migration; the Excel publisher refuses to reinterpret an existing Master Table's columns.

## Configurable data contract

Use [readiness profile](../config/readiness.example.json), [reviewed meeting example](../templates/reviewed-meeting.example.json), [field map](../templates/meeting-field-map.csv) and [source register](../templates/source-register.csv).

Each metric has a configured key/type/unit, value, observedAt, appliesToDate and evidence. Each issue has stable issueId, immutable eventDate, severity, state, summary, owner, action, due and evidence. Optional surgeonKey and blockKey support historical retrieval. Approved records identify reviewerRole. Evidence references point to locally retained VTT cues or approved email/file records; the package does not claim to verify external content merely because a reviewer supplied a reference.

Store source content privately. Do not put employee identities, patient identifiers or tenant locations in public examples. Department reporting can use aggregate counts without patient-level identity.

## Existing staffing connection

The companion remains responsible for assignments, hours and the charge dashboard. Its A1:L46 staffing export includes later shifts; Friday next-business-day becomes Monday. Import snapshots using the existing bridge. A reviewer maps relevant validated facts into readiness records, preserving source date and reference. A snapshot is context, not an automatic staffing risk or inferred acuity calculation.

## Monthly block lookback

Use [dated block schedule](../templates/block-schedule.example.json). Export or transcribe the organization's grid into explicit dated sessions with stable local surgeon/block keys and non-overlapping effective versions. `lookback` finds the surgeon's previous dated session and the same weekday ordinal/block in the prior calendar month. It returns source-linked issues only where explicitly associated. It does not infer surgeon identity from names or claim no problems when records are absent. If the prior month has no corresponding fifth weekday, no match is returned.

## Optional department federation

Department managers may maintain their own Forms questions, staffing models and source locations. As a later extension, publish authorized aggregate updates with department, operating date, observation time, definitions, issue ID, state, owner, source reference and access scope. Shared agents should query those permitted records, not inherit unrestricted access to another department's inbox. The local engine is single-writer; a shared enterprise store, permissions, service endpoints and agent-to-agent transport are not deployed by this package.
