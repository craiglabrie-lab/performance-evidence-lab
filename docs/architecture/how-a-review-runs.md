# How a review runs

## Inputs

A scenario folder with `data/scenario.json` (run identity, question, intended workload, acceptance criteria, environment, harness settings, list of sources) and the data files it lists.

## Steps

1. **Fact sheet.** `tools/analyze.py` reads every source, normalises time to UTC, lists gaps, computes workload and acceptance results per minute, summarises every metric by window, and flags instruction-like text in logs. Output: `facts.md` and `facts.json`.
2. **Agents.** The runner dispatches each agent as a separate subagent, in the order below. Each agent reads its role file, the method, and only the files listed for its step, and writes one file into `run/`.

| Step | Agent | Reads | Writes |
| --- | --- | --- | --- |
| 1 | Test Lead (plan) | scenario, fact sheet | `01-test-lead-plan.md` |
| 2 | Results Librarian | data, fact sheet, plan | `02-evidence.md` |
| 3 | Test Validity Reviewer | + evidence register | `03-validity.md` |
| 4 | Performance Analyst | + validity | `04-performance.md` |
| 5 | Application, Database, Infrastructure specialists (in parallel) | + performance | `05`–`07` |
| 6 | Devil's Advocate (independent read; runs alongside 3–5) | scenario, fact sheet, evidence register only | `08a-independent-read.md` |
| 7 | Devil's Advocate (challenge) | team's files 03–07 and its own 08a | `08b-challenge.md` |
| 8 | Test Lead (decide) | everything | `09-test-lead-decision.md` |
| 9 | Report Writer | everything; the decision is the source of truth | `REPORT.md` |

3. **Record.** `run/run-log.md` lists the model, order, parallelism, token use and time for each step.

## Running it yourself

With [Claude Code](https://claude.com/claude-code) in this repository:

```
/review-run examples/01-generator-saturation
```

The command is defined in [`.claude/commands/review-run.md`](../../.claude/commands/review-run.md). To review your own results, create a folder with the same layout. Without Claude Code, the role files work as prompts in any assistant that can read files, or use the single-prompt version in [`prompts/`](../../prompts/performance-review-lead.md).

## What is and is not enforced

| Control | How |
| --- | --- |
| Numbers | Computed by code; agents told to cite the fact sheet or show their commands |
| Validity gate | Enforced by role instructions and checked by the Devil's Advocate and the Report Writer's quality checks |
| File access per agent | Instruction only, not sandboxed |
| Independence of the challenge | Separate context and evidence-first ordering; same model |
| Cost and time | Recorded per step; not capped beyond the runtime's own limits |
