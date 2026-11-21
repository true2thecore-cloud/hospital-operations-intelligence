# Customize for your hospital

Copy `config/site.example.json` to `config/site.local.json`. Keep personal configuration outside Git.

| Setting | What to change |
| --- | --- |
| `siteLabel` | Hospital or service label shown in reports. |
| `leaderRole` | The role supported by the assistant, not a named individual. |
| `timezone` | IANA timezone for the folder watcher, such as `America/New_York`. |
| `meetings` | Keys, labels, planned times and report-out order. Actual meeting timestamps determine historical order. |
| `signals` | Explicit operational concerns and keywords that help reviewers find mentions. |
| `outcomes` | What happened later, with a locally agreed measurable definition. |
| `rules` | Combinations of confirmed signals and the later outcome to examine. |
| `historyDays` | Lookback window. Default 90 calendar days. |
| `minimumHistory` | Minimum matched, known-outcome days before historical watch wording. Default 8 is a demonstration threshold, not statistical validation. |
| `watchRate` | Observed event-rate threshold for historical watch wording. Default 0.6 is configurable, not a calibrated probability. |

## Add another department

For example, add ED, care management, transport, ICU, bed management or environmental services to the relevant meeting's `reportOrder`. Define signals that department can explicitly confirm, add local outcome definitions, then update the agenda. Departments are configuration, not hard-coded hospital names.

For each report-out, use the same six fields: current state, concern, impact on the plan, action, owner, next check. Configure actual local escalation contacts privately. Use role placeholders in reusable templates.

## Signal and issue semantics

A signal is a reviewed summary state for one operational dimension at a meeting: `active`, `cleared`, or `unknown`. Use one aggregate state per signal in each review. If multiple sub-issues need independent tracking, give them separate signal keys or maintain an aggregate active state until all sub-issues clear.

An `issueId` is the stable follow-through identifier. Reuse it when the afternoon meeting updates a morning concern. Use a new ID for a genuinely separate issue. Owner, action and due time remain `Not stated` unless explicitly documented. Absence from a later meeting does not close an issue.

## Review corrections and configuration changes

To correct a meeting interpretation, create a new review ID for the same meeting and include the complete revised observations/outcomes. The most recently available revision replaces that meeting's interpretation for current reports. Historical as-of reports still use what was available then.

Changing a rule or outcome definition changes the analysis. Reports include a configuration hash. Keep versioned configuration copies with evaluation results, and collect a new validation period after substantive changes. Do not mix different outcome definitions into one comparison without an explicit migration and review.

## Audience-specific reports

The HTML brief presents sequence, patterns, open issues, evidence and staffing context. Use `prompts/leadership-brief.md` to draft a short executive or charge nurse narrative from the structured report. Retain source IDs and uncertainty labels. Generated narratives are drafts for the designated leader.
