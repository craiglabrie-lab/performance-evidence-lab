---
description: Run the nine-agent performance test results analysis on a test run folder
argument-hint: <test run folder, e.g. examples/01-generator-saturation>
---

Run the Performance Evidence Lab analysis workflow on `$ARGUMENTS`.

The folder must contain `data/scenario.json` and the data files it lists. You are the orchestration runner: you dispatch each agent as its own sub-agent, in order, and do no analysis yourself.

## Setup

1. Run `python3 tools/analyze.py $ARGUMENTS/data --md $ARGUMENTS/facts.md --json $ARGUMENTS/facts.json --charts $ARGUMENTS/charts --sections $ARGUMENTS/facts`. This writes the full computed results summary and the section files in `facts/`, so each agent reads only its slice.
2. Create `$ARGUMENTS/run/`.

## Dispatch

Each step uses the sub-agent of the same name defined in `.claude/agents/`. Send it this message, filled in:

> Test run folder: `$ARGUMENTS`. Inputs you may read: <inputs>. Write your output to `<output>`. <run note, if any>

Each agent gets only the slice it needs (`F/` means `facts/`). Every agent may also open raw files in `data/` to check a specific number.

| Step | Sub-agent | Inputs (besides its role file, `method/` and the style guide) | Output |
| --- | --- | --- | --- |
| 1 | performance-test-lead (run 1: analysis plan) | data/scenario.json, F/overview.md, F/inventory.md | run/01-analysis-plan.md |
| 2 | results-monitoring-analyst | data/scenario.json, F/inventory.md, F/overview.md, data/ (to inventory), run/01 | run/02-data-inventory.md |
| 3 | test-execution-analyst | data/scenario.json, F/overview.md, F/load-profile.md, F/metrics-vusers.md, F/metrics-load_generators.md, data/*.log, run/01–02 | run/03-test-execution.md |
| 4 | results-analyst | F/overview.md, F/load-profile.md, F/metrics-transactions.md, charts/*, run/02–03 | run/04-results-analysis.md |
| 5a | application-apm-engineer | F/overview.md, F/capacity.md, F/metrics-app_servers.md, F/metrics-checkout_traces.md, F/metrics-external_calls.md, run/03–04 | run/05-application-apm.md |
| 5b | database-engineer | F/overview.md, F/capacity.md, F/metrics-database.md, run/03–04 | run/06-database.md |
| 5c | infrastructure-network-engineer | F/overview.md, F/capacity.md, F/metrics-network.md, F/metrics-app_servers.md, run/03–04 | run/07-infrastructure-network.md |
| 6 | peer-reviewer (run 1: initial review) | data/scenario.json, F/overview.md, F/inventory.md, run/02 | run/08a-initial-review.md |
| 7 | peer-reviewer (run 2: peer review) | run/03–07, run/08a, any F/ section needed to check a finding | run/08b-peer-review.md |
| 8 | performance-test-lead (run 2: go/no-go) | run/02–08b, F/overview.md | run/09-go-no-go.md |
| 9 | test-report-author | run/09, run/03–04, F/overview.md, charts/* | TEST-SUMMARY.md |

Run only the engineers the plan assigns; steps 5a–5c run in parallel. If a section file listed above does not exist for this test run (for example, no traces), skip it.

Step 6 can run at the same time as steps 3–5, because it only needs the data inventory.

Sub-agent models are set in `.claude/agents/` (see [ADR-0009](../../docs/decisions/0009-cost-controls.md)). For a first recorded run, start with `examples/02-connection-pool`.

If a sub-agent returns its file contents instead of writing the file, save them unchanged to the output path and add a one-line note at the end saying the runner saved it.

## Run log

Write `$ARGUMENTS/run/run-log.md` with:

- the date and model;
- the order the agents ran in, and which steps ran in parallel;
- any engineer the plan left out, and why;
- tokens, tool calls and time per step, and the model each step used;
- a note that each sub-agent's tool list is enforced by Claude Code, but its list of input files is an instruction, not a sandbox.
