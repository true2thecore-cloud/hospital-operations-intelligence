# Data contracts, version 1

## Meeting intake sidecar

```json
{
  "id": "2027-01-04-am",
  "kind": "plan_ahead_am",
  "startsAt": "2027-01-04T09:00:00-05:00",
  "sourceLabel": "Morning Plan Ahead",
  "transcriptFile": "2027-01-04-am.vtt"
}
```

Save as `.meeting.json` for the watcher. The VTT must be directly in the same folder. The date portion of `startsAt` is the operating date, so use the site's actual local offset. The `timezone` config controls the watcher's calendar, not reinterpretation of an incorrectly supplied timestamp.

The store assigns transcript receipt time and cue IDs `c1`, `c2`, etc. It retains cue start/end times, speaker text when present, source label and a content hash. Source records are immutable. Changed transcript content requires a new ID, with review of how it relates to the prior source.

## Reviewed record

```json
{
  "id": "2027-01-04-am-review-1",
  "meetingId": "2027-01-04-am",
  "reviewerRole": "Operations reviewer",
  "observations": [
    {
      "signal": "staffing_shortage",
      "state": "active",
      "summary": "Afternoon coverage gap confirmed.",
      "cueIds": ["c1"],
      "issueId": "coverage-2027-01-04",
      "owner": "OR Charge",
      "action": "Confirm the afternoon coverage plan.",
      "due": "2027-01-04 14:00 local"
    }
  ],
  "outcomes": []
}
```

Save as `.review.json`. Allowed states are `active`, `cleared`, `unknown`. A later review uses the same issue ID to update or resolve the issue. An omitted owner/action/due becomes `Not stated`.

Outcome entry: `{ "key": "late_flow_delay", "value": true, "summary": "The defined delay occurred.", "cueIds": ["c2"] }`. Value can be `true`, `false`, or `null`. The outcome should be documented in a later meeting on the same operating date. Cross-day outcome horizons are not implemented in version 0.1.0; the next-day-readiness outcome means a readiness issue identified later that same day, not a next-day measured event.

Receipt time is assigned at import. Optional `reviewedAt` must have an offset, follow the meeting start, and not be later than receipt. `availableAt` is the latest of source receipt, review receipt and review time. Users cannot backdate knowledge by editing a reviewed-at label.

Review IDs are immutable. Identical reimports are skipped. A correction uses a new ID for the same meeting and a full corrected review. The most recent available review supplies that meeting's current interpretation. Omitted signals in a revised review are no longer asserted by that meeting; earlier issue states from other meetings remain unless explicitly cleared.

## Companion snapshots

Staffing: `version`, `sourceSheet`, `staffingDate`, `capturedUtc`, `values[46][12]`, all cell values strings. Handoff: `version`, unique string `headers`, equal-width scalar `rows`, maximum 5,000 rows. The core assigns receipt time. Both have size limits. Source timestamps are never rewritten.

The dashboard presents the newest captured staffing snapshot received by the cutoff. An older capture imported later cannot replace it. Handoff snapshots use receipt order and retain source rows, not a presumed latest-response ordering.

## Report output

`version`, `siteLabel`, `datasetMode`, `configHash`, `date`, `asOfUtc`, `generatedUtc`, `meetings`, `missingMeetings`, `issues`, `warnings`, `snapshots`.

Each issue includes the latest reviewed state and source excerpts. Each warning includes the configured rule, observed historical support and an uncertainty statement. `asOfUtc` controls evidence availability; `generatedUtc` is the time the file was rendered. The Excel script uses `asOfUtc` to reject stale updates.

## Storage and limits

SQLite stores JSON records keyed by record kind and stable ID. Operational and synthetic datasets cannot share a database. The core is single-user; the folder watcher and browser workbench should not write the same database concurrently. Stop one before using the other for writes. Use a normal local filesystem with approved backup. The local workbench is not a multi-user service or a compliant clinical records platform by itself.

VTT text is limited to 2 million characters, local requests to 3 MB, snapshots to approximately 2 million serialized characters, and the Excel view to 500 rows. The HTML brief can show more issues. Archive through an approved process if the dataset outgrows the local baseline.
