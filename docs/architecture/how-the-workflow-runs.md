# How the workflow runs

## Inputs

A test run folder containing `data/scenario.json` (run identity, test objective, workload model, SLAs, environment, load generator settings and the list of data files) and the data files it lists.

## Steps

1. **Computed results summary.** `tools/analyze.py` reads every data file and:
   - converts timestamps to UTC and lists monitoring gaps;
   - calculates the load profile and SLA results per minute;
   - summarizes every metric by time window;
   - flags possible prompt-injection text in logs.

   - builds the transaction summary table, errors by type and the baseline comparison;
   - validates the inputs (required fields and columns, malformed values, elapsed minutes against timestamps, duplicates, missing transaction types, reconciliation with the run-level summary) and lists every problem under "Input checks";
   - calculates a CPU-bound throughput ceiling per tier (Utilization Law), flagged where another resource is saturated;
   - checks whether the baseline comparison is comparable;
   - draws the standard graphs: running Vusers, throughput, checkout p95 and errors over time.

   It writes `facts.md`, `facts.json`, `charts/*.svg`, and the same summary split into section files in `facts/`, so each agent reads only its slice.
2. **Agents.** The runner dispatches each agent to its own Claude Code sub-agent, defined in [`.claude/agents/`](../../.claude/agents/), in this order. Each agent reads its role file, the workflow files and only the inputs listed for its step, and writes one handoff file into `run/`.

| Step | Agent | Inputs | Output |
| --- | --- | --- | --- |
| 1 | Performance Test Lead (analysis plan) | scenario, computed results summary | `01-analysis-plan.md` |
| 2 | Results & Monitoring Analyst | data, summary, plan | `02-data-inventory.md` |
| 3 | Test Execution Analyst | + data inventory | `03-test-execution.md` |
| 4 | Results Analyst | + test validity | `04-results-analysis.md` |
| 5 | Application & APM, Database, Infrastructure & Network engineers (in parallel) | + results analysis | `05`–`07` |
| 6 | Peer Reviewer (initial review; runs alongside steps 3–5) | scenario, summary, data inventory only | `08a-initial-review.md` |
| 7 | Peer Reviewer (peer review) | handoff files 03–07 and its own 08a | `08b-peer-review.md` |
| 8 | Performance Test Lead (go/no-go) | everything | `09-go-no-go.md` |
| 9 | Test Report Author | everything; the go/no-go file is the source of truth | `RUN/TEST-SUMMARY.md` |

3. **Run log.** `RUN/run-log.md` (in a fresh run folder for every run) records the model, the order the agents ran in, which steps ran in parallel, and tokens and time per step.

## Running it

With [Claude Code](https://claude.com/claude-code) in this repository:

```
/review-run examples/01-generator-saturation
```

The command is defined in [`.claude/commands/review-run.md`](../../.claude/commands/review-run.md). To analyze your own results, create a folder with the same layout. Without Claude Code, the agent role files work as prompts in any AI assistant that can read files, or you can use the single-prompt version in [`prompts/`](../../prompts/performance-review-lead.md).

## What is enforced, and how

| Control | How |
| --- | --- |
| Calculations | Done by code; agents cite the computed results summary or show their commands |
| Test validity first | Agent instructions, checked by the Peer Reviewer. Enforced in the Results block by `tools/check_run.py`: an Invalid test reports every SLA as Not evaluated and no Go |
| SLA results | `tools/check_run.py`: a reported result is never stronger than the computed candidate result |
| Handoffs | `tools/check_run.py`: a fresh run folder for every run; a step does not start if a handoff it needs is missing or older than the computed results |
| Tools per agent | Enforced: each sub-agent has a fixed tool list (read, search, Bash, write). No web search or fetch tool and no launching other agents; Bash can still reach the network unless the host blocks it |
| Each agent's file inputs, and keeping the answer key out | Instructions only; not sandboxed. Bash can read any file in the repository. Enforce with host sandboxing and permission rules before using sensitive results |
| Peer Reviewer independence | Its own context, and its initial review is written before it sees the team's findings; it shares the filesystem and the model family with the team |
| Cost and time | Recorded per step; no limits beyond the runtime's own |
