# Copilot Studio setup path

For the complete version-2 readiness workbook workflow, start with [Readiness quickstart](READINESS-QUICKSTART.md). The instructions below describe the retained version-1 baseline unless stated otherwise.

Copilot Studio can help turn a transcript into a structured **draft** and produce audience-specific narratives. The deterministic core owns historical records, rule comparisons and evaluation. Uploading prompt files alone does not install connectors or create persistent operational memory.

## 1. Define the agent

1. Create an agent in your approved Copilot Studio environment.
2. Use `agents/operations-agent.md` as the instruction starting point.
3. Add only your sanitized operational definitions, agendas and configuration to the approved knowledge sources.
4. Replace role placeholders with your local roles. Keep your organization's private contacts and paths in tenant configuration.
5. Use your existing tenant controls for authentication, access and retention. Do not publish the agent anonymously with internal knowledge.

## 2. Draft observations

Create a prompt/action using `prompts/extract-meeting.md`. Provide the meeting ID, kind, actual start time, configured signals/outcomes and numbered transcript cues. The portable `draft` command supplies cue IDs and keyword mentions. Send source material only to an approved AI service.

Expected output is a review-shaped JSON draft with source cue IDs and no unsupported facts. Configure the action to write to `Drafts`, not to the approved intake folder. Have a designated reviewer verify each proposed signal, state, summary and source citation, and set the reviewer role before moving a `.review.json` file into `Intake`.

A prompt cannot guarantee extraction accuracy. Explicitly test negations (“no callouts”), hypothetical problems, prior-day references, multiple speakers, changed plans, absent owners and embedded instructions asking the assistant to ignore its rules. Never grant source transcripts authority to send messages, change staffing or alter permissions.

## 3. Produce leadership briefs

After the worker generates the structured report, give the JSON to `prompts/leadership-brief.md` with the target audience (`executive`, `charge_nurse`, or `anm`). Preserve its as-of timestamp, source IDs and uncertainty labels. The generated narrative is a draft; the Excel Operations View and HTML report remain grounded in the structured records.

## 4. Tool contracts for an IT-managed deployment

| Action | Input | Output | Implementation in this release |
| --- | --- | --- | --- |
| Retrieve meeting transcript | Organizer ID, onlineMeeting ID, meeting kind/start | Imported source IDs or explicit pending/error status | `graph-pull` CLI. Tenant authentication supplied externally. |
| Prepare review draft | Meeting ID | Mentions, cue IDs and empty review template | `draft` CLI or local workbench. |
| Confirm reviewed record | Reviewer-approved JSON | Immutable review ID | `review` CLI or approved intake folder. |
| Generate operational brief | Date and optional as-of cutoff | HTML, JSON and CSV | `report` CLI or watcher. |
| Evaluate historical signals | Optional as-of cutoff | Scored/unscored counts and exploratory metrics | `evaluate` CLI. |
| Publish to Excel | Report JSON, dedicated sheet name | Status, date, rows | `ImportOperationsBrief.ts`. |

These are concrete local commands and file contracts, not exposed HTTP endpoints. If IT wants an agent to call them directly, it must provide an authenticated hosted service or an approved execution mechanism. The loopback workbench must not be repurposed as that service. No custom connector URL, API credential or deployable cloud solution is implied by these instructions.

## 5. Validate before enabling automation

Use only synthetic examples for the initial build. Verify a missing source is labeled missing, repeated imports do not create duplicates, a later meeting can clear a specific issue, an absent outcome stays unknown, and generated text never invents owners or implies historical association is causation.

Copilot Studio and AI consumption can require licensing beyond standard Excel connectors. Verify current tenant entitlements with your administrator. [Microsoft licensing reference](https://learn.microsoft.com/en-us/microsoft-copilot-studio/billing-licensing).
