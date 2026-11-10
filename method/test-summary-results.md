# The four results in every test summary

Every test summary reports four separate results. Mixing them up is how analysis goes wrong: a root cause reported from a test that never reached its load profile, or an SLA marked Pass for a window with no data.

| Result | Values | Answers |
| --- | --- | --- |
| Test validity | Valid · Valid with limitations · Invalid | Did the test produce the load profile it was designed for, and what are the results usable for? |
| SLA results | Pass · Fail · Not evaluated, per SLA | Did the system meet each SLA, as far as a valid test can show? |
| Root-cause status | Symptom · Correlated metric · Suspected bottleneck · Confirmed root cause | How far has the bottleneck analysis gone? |
| Confidence | High · Medium · Low, with a one-line reason | How sure are we of this specific finding? |

## Test validity

Judge validity against the test objective. The same run can be usable for "these errors occurred under load" and not usable for "the system supports 500 users".

- **Valid**: the achieved load profile, load generator health and monitoring coverage support the test objective.
- **Valid with limitations**: the objective can be answered within stated limits. List what the results are usable for and not usable for.
- **Invalid**: the run cannot answer the test objective. State the reason (for example, "load profile not achieved" or "load generator saturated"). Report the observations that can still be trusted and plan the retest.

Missing data never defaults to Valid. A system that slows down under the planned load does not make the test invalid: if the load generators were healthy and the virtual users were running, a throughput drop caused by slow response times is a result about the system.

## SLA results

An SLA result needs a defined SLA, a time window and data. Use **Not evaluated** when any of them is missing, or when the test validity result does not support it. Missing data is never a Pass.

`tools/analyze.py` computes a **candidate** result for each SLA from the data alone. The reported result can match the candidate or be Not evaluated, never stronger: a candidate Fail is never reported as Pass. When the test is **Invalid**, every SLA result is Not evaluated; the measured breaches are still reported, as observations. `tools/check_run.py` checks these rules in the go/no-go recommendation and the test summary.

## Root-cause status

| Status | What it takes |
| --- | --- |
| Symptom | A measured degradation: a response time, error or throughput change at a known time |
| Correlated metric | A second metric moves with the symptom in the same aligned time window, with monitoring coverage |
| Suspected bottleneck | A plausible mechanism, supported by several metrics, with other tiers eliminated and gaps listed |
| Confirmed root cause | Proven by a retest or tuning change that removes or reproduces the degradation |

Agreement between agents, or a well-argued explanation, never moves a finding up a level. Only new data does.

## Confidence

Confidence applies to one specific finding and comes with a reason: monitoring coverage, time alignment, data quality and the alternatives still open. A high-confidence correlated metric is still a correlated metric.
