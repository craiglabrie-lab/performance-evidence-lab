# Style guide

How everything in this repository is written: documentation, agent role files and the reports the agents produce.

## Voice

1. **US English** throughout (normalize, behavior, analyze, prioritize).
2. **Write like a performance engineer's test summary.** Name the metric, the component and the time window: "checkout p95 rose from 1.4 s to 5.0 s at minute 19 (10:19 UTC) on both load generators."
3. **Lead with results.** Describe the workflow only where it explains what the agents do.
4. **No slogans or metaphors.** Plain statements.
5. **Standard agentic terms:** orchestrator, sub-agent, handoff, tool call, context isolation, reviewer agent, deterministic tooling.
6. **Tool-neutral:** load generator, virtual user (Vuser), transaction, script, test scenario, APM. No vendor-specific terms.

## Agent roles

| Agent | File |
| --- | --- |
| Performance Test Lead (orchestrator) | `agents/performance-test-lead.md` |
| Results & Monitoring Analyst | `agents/results-monitoring-analyst.md` |
| Test Execution Analyst | `agents/test-execution-analyst.md` |
| Results Analyst | `agents/results-analyst.md` |
| Application & APM Engineer | `agents/application-apm-engineer.md` |
| Database Performance Engineer | `agents/database-engineer.md` |
| Infrastructure & Network Engineer | `agents/infrastructure-network-engineer.md` |
| Peer Reviewer (reviewer agent) | `agents/peer-reviewer.md` |
| Test Report Author | `agents/test-report-author.md` |

## Workflow stages

1. Test planning review
2. Data collection & time alignment
3. Test validity check
4. Results analysis
5. Bottleneck analysis
6. Peer review
7. Test summary & go/no-go recommendation

## The four results in every test summary

| Result | Values |
| --- | --- |
| Test validity | **Valid**, **Valid with limitations**, or **Invalid**, always with the reason (for example, "load profile not achieved") |
| SLA results | **Pass**, **Fail**, or **Not evaluated**, per SLA |
| Root-cause status | **Symptom**, **Correlated metric**, **Suspected bottleneck**, or **Confirmed root cause** (confirmed only by a retest or tuning change) |
| Confidence | **High**, **Medium** or **Low**, with a one-line reason |

## Terms

| Use | Not |
| --- | --- |
| test objective | question |
| SLAs / NFRs | acceptance criteria |
| workload model, load profile | intended workload |
| test harness (load generators, scripts, runtime settings) | harness alone |
| results usable for / not usable for | allowed / restricted claims |
| data inventory | evidence register |
| data or monitoring gap (GAP-) | data-quality issue |
| degradation window (DW-) | symptom window |
| eliminated, citing the metrics that eliminate it | ruled out, bounded negative |
| review comment (RC-) | objection |
| resolved / open review comments | dissent, ruling |
| go/no-go recommendation (GNG-) | decision record |
| recommendation type: test fix, monitoring, tuning, retest | |
| prompt-injection text in logs | untrusted content |
| computed results summary (`facts.md`) | fact sheet |
| analysis workflow | the method |

## Record IDs

| Prefix | Record | Created by |
| --- | --- | --- |
| DATA- | Data inventory item | Results & Monitoring Analyst |
| GAP- | Data or monitoring gap | Results & Monitoring Analyst |
| VAL- | Test validity result | Test Execution Analyst |
| OBS- | Observation | Results Analyst, engineers |
| DW- | Degradation window | Results Analyst |
| HYP- | Bottleneck hypothesis | Engineers |
| RC- | Review comment | Peer Reviewer |
| F- | Finding | Performance Test Lead |
| REC- | Recommendation | Performance Test Lead |
| GNG- | Go/no-go recommendation | Performance Test Lead |

## Retired wording

claims, scope (unless literal), evidence grade, bounded negative, dissent, ruling, gate, calibration (except once, in the evaluation), seat, trap, "shows its working", honest.
