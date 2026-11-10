# Concept: cost, context and model routing

> **Status: Partly implemented** ([ADR-0009](../decisions/0009-cost-controls.md)).
> - **Implemented** (configuration, not yet measured):
>   - context slices (`tools/analyze.py --sections` and per-step inputs in `/review-run`);
>   - model routing for three roles in `.claude/agents/`;
>   - handoff length and tool-call guidance.
> - **Concept**: prompt caching layout, enforced token budgets, and a different model family for the Peer Reviewer.
>
> The measurements below come from the earlier recorded runs, made during development with a previous version of the agents. Those runs are not included in this repository.

## What the earlier runs cost

| | Agent team (per test run) | Single prompt (per test run) |
| --- | --- | --- |
| Agent calls | 11 | 1 |
| Tokens | 1.66 M and 1.77 M | 0.10–0.11 M |
| Tokens per step | 0.09–0.24 M; the largest were the peer review, go/no-go and test summary steps | |
| Wall-clock time, with parallel steps | about 33 minutes | about 2 minutes |

Every step started by reading the full data set and the earlier handoffs, so even the simplest steps used about 0.09 M tokens.

## Design

### 1. Give each agent only its slice of the data (*implemented*)

| Agent | Gets | Does not get |
| --- | --- | --- |
| Results & Monitoring Analyst | All data files (inventory only), `scenario.json` | Earlier handoffs beyond the plan |
| Test Execution Analyst | Vusers, load generator health, error log, transaction summary, `scenario.json`, data inventory | App, database and network metrics |
| Results Analyst | Transactions, transaction summary, baseline comparison, graphs, test validity result | Tier metrics |
| Application & APM Engineer | App server metrics, traces, outbound calls, its degradation windows | Load generator detail |
| Database Performance Engineer | Database metrics, its degradation windows | Load generator and trace detail |
| Infrastructure & Network Engineer | Network and host metrics, capacity table, its degradation windows | Trace detail |
| Peer Reviewer | Everything, but as structured handoffs ([handoff schema](handoff-schema.md)), not full prose | |
| Test Report Author | Go/no-go recommendation, transaction summary, graphs, the records the findings cite | Raw data |

The computed results summary is split into section files in `facts/` (`overview`, `load-profile`, `capacity`, `inventory`, and one `metrics-*` file per data source). [`/review-run`](../../.claude/commands/review-run.md) lists the sections each step receives.

### 2. Route models by the judgment each role needs (*implemented for the smaller-model tier*)

| Tier | Roles | Why |
| --- | --- | --- |
| Large model | Performance Test Lead, Test Execution Analyst, the three engineers | Judgment under uncertainty: validity, bottleneck mechanisms, go/no-go |
| Different large model | Peer Reviewer | A reviewer on a different model is less likely to share the team's blind spots |
| Smaller model | Results & Monitoring Analyst, Results Analyst, Test Report Author | Inventory, description and writing from structured inputs; deterministic checks catch errors |

### 3. Cache what every agent shares (*concept*)

The role preamble, the workflow files and the style guide are the same for every agent. Put them first in each prompt so prompt caching can reuse them.

### 4. Budget every step (*concept; guidance only today*)

| Step | Proposed token budget | On overrun |
| --- | --- | --- |
| Analysis plan | 40 K | Stop and report |
| Data inventory | 80 K | Stop and report |
| Test execution | 80 K | Stop and report |
| Results analysis | 80 K | Stop and report |
| Each engineer | 100 K | Stop and report |
| Peer Reviewer (both runs) | 120 K | Stop and report |
| Go/no-go | 80 K | Stop and report |
| Test summary report | 60 K | Stop and report |
| **Total** | **about 0.8 M** | |

The [orchestrator](orchestrator.md) enforces the budgets and records actual use in the run state.

## Target, to be measured

Reach about half the earlier cost, with the same score against the answer key. The [evaluation harness](evaluation-harness.md) reports both together, so a cheaper configuration is accepted only if it scores as well.

## Open questions

- Which smaller model is good enough for the Results Analyst. That needs measurement, not assumption.
- Whether the Peer Reviewer on a different model finds more, or just finds different things.
