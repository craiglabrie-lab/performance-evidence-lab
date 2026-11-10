---
description: Run the nine-agent performance test results analysis on a test run folder
argument-hint: <test run folder, e.g. examples/01-generator-saturation>
---

Run the Performance Evidence Lab analysis workflow on `$ARGUMENTS`.

The folder must contain `data/scenario.json` and the data files it lists. You are the orchestration runner: you dispatch each agent as its own sub-agent, in order, and do no analysis yourself.

## Setup

1. Run `python3 tools/analyze.py $ARGUMENTS/data --md $ARGUMENTS/facts.md --json $ARGUMENTS/facts.json --charts $ARGUMENTS/charts`.
2. Create `$ARGUMENTS/run/`.

## Dispatch

Each step uses the sub-agent of the same name defined in `.claude/agents/`. Send it this message, filled in:

> Test run folder: `$ARGUMENTS`. Inputs you may read: <inputs>. Write your output to `<output>`. <run note, if any>

| Step | Sub-agent | Inputs (besides its role file, `method/` and the style guide) | Output |
| --- | --- | --- | --- |
| 1 | performance-test-lead (run 1: analysis plan) | data/scenario.json, facts.md | run/01-analysis-plan.md |
| 2 | results-monitoring-analyst | data/*, facts.md, run/01 | run/02-data-inventory.md |
| 3 | test-execution-analyst | data/*, facts.md, charts/*, run/01–02 | run/03-test-execution.md |
| 4 | results-analyst | data/*, facts.md, charts/*, run/01–03 | run/04-results-analysis.md |
| 5 | application-apm-engineer, database-engineer, infrastructure-network-engineer (those the plan assigns; run in parallel) | data/*, facts.md, run/01–04 | run/05-application-apm.md, run/06-database.md, run/07-infrastructure-network.md |
| 6 | peer-reviewer (run 1: initial review) | data/scenario.json, facts.md, run/02 | run/08a-initial-review.md |
| 7 | peer-reviewer (run 2: peer review) | data/*, facts.md, run/03–07, run/08a | run/08b-peer-review.md |
| 8 | performance-test-lead (run 2: go/no-go) | data/*, facts.md, run/* | run/09-go-no-go.md |
| 9 | test-report-author | data/scenario.json, facts.md, charts/*, run/* | TEST-SUMMARY.md |

Step 6 can run at the same time as steps 3–5, because it only needs the data inventory.

If a sub-agent returns its file contents instead of writing the file, save them unchanged to the output path and add a one-line note at the end saying the runner saved it.

## Run log

Write `$ARGUMENTS/run/run-log.md` with:

- the date and model;
- the order the agents ran in, and which steps ran in parallel;
- any engineer the plan left out, and why;
- tokens and time per step, if available;
- a note that each sub-agent's tool list is enforced by Claude Code, but its list of input files is an instruction, not a sandbox.
