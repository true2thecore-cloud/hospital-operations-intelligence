# What learning means in this release

The system accumulates reviewed evidence and later outcomes. It does not fine-tune an AI model or claim causality. Its current early-warning method is a transparent, configurable historical comparison.

## Example

At the reviewed morning checkpoint, staffing coverage and receiving-bed constraints are both active. A rule asks whether comparable earlier days later had a defined flow delay. The brief reports the number of matched days, the number with the outcome, the broader observed baseline and missing outcomes. A small denominator produces an insufficient-history message.

The synthetic example contains **8 events among 11 matched earlier days**. These numbers are invented to test the workflow. They are not evidence of real predictive performance or a recommended hospital threshold.

## Preventing future-information leakage

- Meeting start, transcript receipt and review availability are separate timestamps.
- An observation becomes available only after its source and review are received.
- A checkpoint uses the first available confirmed review of the configured meeting type.
- A warning requires the combination at that checkpoint and still-active signals in the current reviewed state. A combination first raised in the afternoon is not compared as a morning pattern; configure an afternoon checkpoint rule for that use case.
- Earlier as-of reports exclude later reviews, revisions and outcomes.
- Historical comparisons use earlier dates only, within the lookback window.
- The outcome must be documented in a meeting that starts after the checkpoint.
- Unknown, absent or unreviewed outcomes are excluded from event-rate denominators and counted separately.
- Backfilled historical transcripts are not pretended to have been available prospectively. Their actual receipt time governs availability.

A same-day outcome reported before the prediction checkpoint cannot validate that prediction. A late review made after the outcome meeting may make that day ineligible. This is deliberate.

## Collect a useful outcome register

Agree on the outcome definition before collection, such as a documented delay exceeding a locally selected duration. For every eligible day, explicitly record true, false or unknown in a later reviewed meeting. Record no-event days as carefully as event days. Avoid outcome data that exists only when someone reports a problem.

Track interventions too. If leaders acted on a warning and prevented an issue, a simple event/no-event comparison cannot establish whether the warning was wrong or the intervention worked. Capture that distinction for subsequent analysis.

## Evaluate prospectively

```powershell
python -m hospital_ops --config config/site.local.json evaluate --out data/evaluation.json
```

The evaluator walks forward by checkpoint, builds each historical comparison from information available at that time, and then scores against outcomes documented later. It reports true/false positives and negatives, precision and recall where denominators exist, unknown outcomes, and days lacking enough prior history. It does not silently score missing outcomes as false.

Review coverage, sample size, false alarms, missed events, changing practices, weekday mix, service mix and data freshness before considering operational use. Thresholds and rules selected after inspecting a test period must be assessed on a new period. The current engine is a baseline for that process, not an independently validated prediction model.

Forecasts support leader review. This repository does not perform autonomous staffing assignments, patient triage, individual employee scoring or clinical treatment decisions.
