# Roadmap

| Stage | Outcome | Status |
| --- | --- | --- |
| Workflow and agents | Analysis workflow, nine agent role files and Claude Code sub-agents, deterministic tooling with tests, style guide | Done |
| Tester and engineer views | Transaction summary, p90/p95/p99, errors by type, standard graphs, baseline comparison, Utilization Law headroom, execution metadata | Done |
| Concept documents | Handoff schema, agent tool contracts, orchestrator design (checkpoints, resume, human sign-off), cost and model routing, evaluation harness, baseline and regression design. Each labeled as a concept, in [docs/concepts/](../concepts/README.md) | Done |
| Recorded example runs | Both synthetic test runs analyzed by the agent team, every handoff recorded, scored against the answer key, and compared with a single-prompt baseline | Next |
| Repeatability | Several runs per test run, to measure how much the findings vary | Planned |
| Harder test runs | No single clear bottleneck, conflicting metrics, a valid run that passes every SLA, a monitoring gap on the tier that is the bottleneck | Planned |
| Coded orchestrator and typed handoffs | Build the [orchestrator](../concepts/orchestrator.md) and [handoff schema](../concepts/handoff-schema.md) concepts | Planned |
| Evaluation harness | Build the [evaluation harness](../concepts/evaluation-harness.md): repeated runs, automated scoring, a judge on a different model | Planned |
| Real result exports | Adapters that convert load testing tool exports and APM data into the same computed results summary | Planned |
| Model mix and cost | Smaller models for routine agents and a different model for the Peer Reviewer, with quality measured against cost | Planned |
| Independent evaluation | Authorized, anonymized real results analyzed and scored by an experienced performance engineer | Needs data access |

Every statement about how well the workflow performs is backed by recorded runs.
