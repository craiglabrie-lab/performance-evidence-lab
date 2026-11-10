---
description: Run the nine-agent performance test results analysis on a test run folder
argument-hint: <test run folder, e.g. examples/02-connection-pool>
---

Run the Performance Evidence Lab analysis workflow on `$ARGUMENTS`.

The folder must contain `data/scenario.json` and the data files it lists. You are the orchestration runner: you dispatch each agent as its own sub-agent, in order, and do no analysis yourself.

## Setup

1. Run `python3 tools/analyze.py $ARGUMENTS/data --md $ARGUMENTS/facts.md --json $ARGUMENTS/facts.json --charts $ARGUMENTS/charts --sections $ARGUMENTS/facts`. This writes the full computed results summary and the section files in `facts/`, so each agent reads only its slice. If it exits with an error, stop and report the message.
2. Run `python3 tools/check_run.py init $ARGUMENTS`. It creates a fresh run folder, `$ARGUMENTS/run-<UTC timestamp>/`, and prints its path. Call it `RUN` below. A run folder is never reused, so handoffs from an earlier or interrupted run cannot mix into this one.

## Dispatch

Each step uses the sub-agent of the same name defined in `.claude/agents/`.

**Before each step**, run `python3 tools/check_run.py ready RUN <step>` (use 5 for steps 5a–5c). If it prints `STOP`, do not dispatch that step or any step that depends on it. Record the message in the run log and end the run. The check confirms the handoffs the step needs exist, were written in this run, and, from step 4 on, that `03-test-execution.md` states the test validity result.

Send each sub-agent this message, filled in:

> Test run folder: `$ARGUMENTS`. Run folder: `RUN`. Inputs you may read: <inputs>. Write your output to `<output>`. <run note, if any>

Each agent gets only the slice it needs (`F/` means `$ARGUMENTS/facts/`; `R/` means `RUN/`). Every agent may also open raw files in `data/` to check a specific number. No agent reads `evaluation/` or `tools/generate_synthetic.py`.

| Step | Sub-agent | Inputs (besides its role file, `method/` and the style guide) | Output |
| --- | --- | --- | --- |
| 1 | performance-test-lead (run 1: analysis plan) | data/scenario.json, F/overview.md, F/inventory.md | R/01-analysis-plan.md |
| 2 | results-monitoring-analyst | data/scenario.json, F/inventory.md, F/overview.md, data/ (to inventory), R/01 | R/02-data-inventory.md |
| 3 | test-execution-analyst | data/scenario.json, F/overview.md, F/load-profile.md, F/metrics-vusers.md, F/metrics-load_generators.md, data/*.log, R/01–02 | R/03-test-execution.md |
| 4 | results-analyst | F/overview.md, F/load-profile.md, F/metrics-transactions.md, charts/*, R/02–03 | R/04-results-analysis.md |
| 5a | application-apm-engineer | F/overview.md, F/capacity.md, F/metrics-app_servers.md, F/metrics-checkout_traces.md, F/metrics-external_calls.md, R/03–04 | R/05-application-apm.md |
| 5b | database-engineer | F/overview.md, F/capacity.md, F/metrics-database.md, R/03–04 | R/06-database.md |
| 5c | infrastructure-network-engineer | F/overview.md, F/capacity.md, F/metrics-network.md, F/metrics-app_servers.md, R/03–04 | R/07-infrastructure-network.md |
| 6 | peer-reviewer (run 1: initial review) | data/scenario.json, F/overview.md, F/inventory.md, R/02 | R/08a-initial-review.md |
| 7 | peer-reviewer (run 2: peer review) | R/03–07, R/08a, any F/ section needed to check a finding | R/08b-peer-review.md |
| 8 | performance-test-lead (run 2: go/no-go) | R/02–08b, F/overview.md | R/09-go-no-go.md |
| 9 | test-report-author | R/09, R/03–04, F/overview.md, charts/* | R/TEST-SUMMARY.md |

Run only the engineers the plan assigns; steps 5a–5c run in parallel. If a section file listed above does not exist for this test run (for example, no traces), skip it.

Step 6 can run at the same time as steps 3–5, because it only needs the data inventory. Write its output before step 7 starts, so the initial review is on file before the reviewer sees the team's findings.

**After step 8 and after step 9**, run `python3 tools/check_run.py results RUN RUN/09-go-no-go.md` (then `RUN/TEST-SUMMARY.md`). It checks the Results block: the test validity result matches step 3, every SLA is listed, no SLA result is stronger than the computed candidate result in `facts.json`, and an Invalid test reports every SLA as Not evaluated and no Go. If it prints `STOP`, send the message back to the same agent once to correct its file. If the check still fails, keep the file, record the failure in the run log, and do not present the file as the test summary.

Sub-agent models are set in `.claude/agents/` (see [ADR-0009](../../docs/decisions/0009-cost-controls.md)). For a first recorded run, start with `examples/02-connection-pool`.

If a sub-agent returns its file contents instead of writing the file, save them unchanged to the output path and add a one-line note at the end saying the runner saved it.

## Run log

Write `RUN/run-log.md` with:

- the date and model;
- the order the agents ran in, and which steps ran in parallel;
- any engineer the plan left out, and why;
- every `check_run.py` result, including any STOP and what happened next;
- tokens, tool calls and time per step, and the model each step used;
- a note that each sub-agent's tool list is enforced by Claude Code, but its list of input files, and the rule not to read `evaluation/`, are instructions, not a sandbox.
