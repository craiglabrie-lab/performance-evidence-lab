---
description: Run the nine-agent performance review on a results folder
argument-hint: <scenario folder, e.g. examples/01-generator-saturation>
---

Run the Performance Evidence Lab review on `$ARGUMENTS`.

The folder must contain `data/scenario.json` and the data files it lists. You are the runner: you dispatch each agent as a separate subagent, in order, and do no analysis yourself.

## Setup

1. Run `python tools/analyze.py $ARGUMENTS/data --md $ARGUMENTS/facts.md --json $ARGUMENTS/facts.json`.
2. Create `$ARGUMENTS/run/`.

## Dispatch

For each step, launch one general-purpose subagent with this prompt, filling in the role file, the files it may read and its output file:

> You are one agent in the Performance Evidence Lab review team. Your role and instructions are in `agents/<role>.md`; read that file first and follow it exactly. The scenario folder is `$ARGUMENTS`. Read only these files: <list>. You may run `python tools/analyze.py` and short Python commands over files in `$ARGUMENTS/data/` to compute numbers; show any command whose result you rely on. Write your output to `<output file>` and nothing else. Start the file with the header block described in `method/records.md`. When you finish, reply with one line saying the file is written.

| Step | Role file | Reads (besides its role file and `method/`) | Writes |
| --- | --- | --- | --- |
| 1 | test-lead.md (call 1: Plan) | data/scenario.json, facts.md | run/01-test-lead-plan.md |
| 2 | results-librarian.md | data/*, facts.md, run/01 | run/02-evidence.md |
| 3 | test-validity-reviewer.md | data/*, facts.md, run/01–02 | run/03-validity.md |
| 4 | performance-analyst.md | data/*, facts.md, run/01–03 | run/04-performance.md |
| 5 | application-specialist.md, database-specialist.md, infrastructure-specialist.md (only those the plan assigns; run them in parallel) | data/*, facts.md, run/01–04 | run/05-application.md, run/06-database.md, run/07-infrastructure.md |
| 6 | devils-advocate.md (call 1: Independent read) | data/scenario.json, facts.md, run/02 | run/08a-independent-read.md |
| 7 | devils-advocate.md (call 2: Challenge) | data/*, facts.md, run/03–07, run/08a | run/08b-challenge.md |
| 8 | test-lead.md (call 2: Decide) | data/*, facts.md, run/* | run/09-test-lead-decision.md |
| 9 | report-writer.md | data/scenario.json, facts.md, run/* | REPORT.md |

Step 6 may run at the same time as steps 3–5, because it depends only on the evidence register.

## Record

Write `$ARGUMENTS/run/run-log.md` with: date, model, the order agents ran, which ran in parallel, which specialists the plan skipped and why, and the fact that file-access limits were given as instructions, not enforced by a sandbox.
