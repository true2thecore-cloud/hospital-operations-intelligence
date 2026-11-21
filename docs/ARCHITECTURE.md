# Architecture and boundaries

| Layer | Implementation | Boundary |
| --- | --- | --- |
| Intake | VTT parser, Graph adapter, folder watcher | Does not discover all meetings or acquire tenant credentials automatically. |
| Review | Keyword mentions plus JSON review with cue evidence | No automatic semantic confirmation. Optional Copilot drafting is separately configured. |
| Memory | Immutable SQLite source/review/snapshot records | Single-user local baseline, not a hospital-wide hosted database. |
| Sequencing | Actual meeting start and evidence-availability timestamps | Planned agenda order is configurable; transcripts are not rearranged to fit an assumed sequence. |
| Follow-through | Stable issue IDs with active/cleared/unknown states | No implicit closure, assignment changes or autonomous escalation. |
| Patterns | Configured signal combinations and earlier-day comparisons | Exploratory associations; no trained model or calibrated probability. |
| Evaluation | Walk-forward checkpoint scoring | Depends on explicit outcomes and reliable receipt times. |
| Presentation | Escaped HTML, safe CSV, JSON, dedicated Excel sheet | Snapshots, not instantaneous live staffing. |
| Microsoft bridge | Approved folder synchronization and Office Script | Worker availability, cloud sync and tenant configuration determine latency. |

The portable core runs without an AI dependency. Users can manually review observations or use an approved model to draft the same schema. No hidden external API calls occur in the report pipeline.

For a future enterprise deployment, IT can move storage to an approved transactional database, expose authenticated scoped endpoints, add a work queue, centralize credentials, implement tenant authorization and retention, and monitor pipeline health. Preserve the timestamp/evidence contracts and tests during that migration. Those deployment components are not supplied as a claimed ready-to-import cloud solution here.

## Repository layout

```text
hospital_ops/   Parser, store, comparisons, reports, CLI, local workbench, adapters
config/         Site and rule configuration
templates/      Editable agendas, registers and review examples
examples/       Synthetic transcript only
agents/         Configurable operational agent instructions
skills/         Reusable workflow instructions
prompts/        Extraction and audience-specific briefing prompts
scripts/        Excel Operations View import
docs/           Setup, integration, contracts, learning and troubleshooting
tests/          Core behavior and chronology checks
assets/         Synthetic report preview
```
