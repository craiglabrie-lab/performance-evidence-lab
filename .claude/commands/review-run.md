---
description: Run the nine-agent performance test results analysis on a test run folder
argument-hint: <scenario folder, e.g. examples/01-generator-saturation>
---

Run the Performance Evidence Lab analysis workflow on `$ARGUMENTS`.

The folder must contain `data/scenario.json` and the data files it lists. You are the runner: you dispatch each agent as a separate sub-agent, in order, and do no analysis yourself.

## Setup

1. Run `python tools/analyze.py $ARGUMENTS/data --md $ARGUMENTS/facts.md --json $ARGUMENTS/facts.json`.
2. Create `$ARGUMENTS/run/`.

## Dispatch

For each step, launch one general-purpose sub-agent with this prompt, filling in the role file, its inputs and its output file:

> You are one agent in the Performance Evidence Lab analysis workflow. Your role and instructions are in `agents/<role>.md`; read that file first and follow it exactly. Write in US English and follow `docs/style-guide.md`. The test run folder is `$ARGUMENTS`. Read only these files: <inputs>. You may run `python tools/analyze.py` and short Python commands over files in `$ARGUMENTS/data/`; show any command whose result you use. Write your output to `<output file>` and nothing else. Start the file with the header described in `method/records.md`. When you finish, reply with one line saying the file is written. If you are not allowed to write the file, reply with its full contents instead.

| Step | Role file | Inputs (besides its role file, `method/` and the style guide) | Output |
| --- | --- | --- | --- |
| 1 | performance-test-lead.md (run 1: analysis plan) | data/scenario.json, facts.md | run/01-analysis-plan.md |
| 2 | test-data-analyst.md | data/*, facts.md, run/01 | run/02-data-inventory.md |
| 3 | test-validity-analyst.md | data/*, facts.md, run/01–02 | run/03-test-validity.md |
| 4 | performance-analyst.md | data/*, facts.md, run/01–03 | run/04-results-analysis.md |
| 5 | application-apm-engineer.md, database-engineer.md, infrastructure-network-engineer.md (those the plan assigns; run in parallel) | data/*, facts.md, run/01–04 | run/05-application-apm.md, run/06-database.md, run/07-infrastructure-network.md |
| 6 | peer-reviewer.md (run 1: initial review) | data/scenario.json, facts.md, run/02 | run/08a-initial-review.md |
| 7 | peer-reviewer.md (run 2: peer review) | data/*, facts.md, run/03–07, run/08a | run/08b-peer-review.md |
| 8 | performance-test-lead.md (run 2: go/no-go) | data/*, facts.md, run/* | run/09-go-no-go.md |
| 9 | report-author.md | data/scenario.json, facts.md, run/* | TEST-SUMMARY.md |

Step 6 can run at the same time as steps 3–5, because it only needs the data inventory.

If a sub-agent returns its file contents instead of writing the file, save them unchanged to the output path and add a one-line note at the end saying the runner saved it.

## Run log

Write `$ARGUMENTS/run/run-log.md` with the date, model, order the agents ran in, which ran in parallel, any engineer the plan left out and why, tokens and time per step if available, and a note that each agent's file inputs were given as instructions, not enforced by a sandbox.
