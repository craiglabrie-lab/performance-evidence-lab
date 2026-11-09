# Examples

Two synthetic load tests of the same invented checkout service, a week apart. Both are fully reviewed by the agent team, and every handoff is kept.

| Scenario | What happened in the data | Team verdict | Read |
| --- | --- | --- | --- |
| [01 — generator saturation](01-generator-saturation/) | One load generator ran with extended logging, saturated its own CPU, distorted its timings and lost a third of the users. A scheduled database batch adds a red herring, and a log line tries to tell AI tools the test passed. | **INVALID FOR THIS QUESTION.** No capacity verdict; fix and calibrate the harness, then rerun. | [REPORT](01-generator-saturation/REPORT.md) |
| [02 — connection pool](02-connection-pool/) | The rerun. Load is delivered, then the third-party payment sandbox slows down. Checkout holds its database connection during the payment call, the pools fill, and every transaction slows. | **VALID WITH LIMITATIONS.** SLA-1 and SLA-2 fail, SLA-3 passes; the capacity verdict waits for a controlled payment stub. | [REPORT](02-connection-pool/REPORT.md) |

## Inside each scenario folder

| Path | Contents |
| --- | --- |
| `data/` | The synthetic exports and `scenario.json` (question, workload, criteria, environment) |
| `facts.md`, `facts.json` | The computed fact sheet from `tools/analyze.py` |
| `run/` | One file per agent, in order, plus `run-log.md` with model, order, tokens and time |
| `REPORT.md` | The final report |
| `baseline/` | A single-prompt report on the same data, for comparison |

The way to read a run: start with `REPORT.md`, then open `run/08b-challenge.md` to see what the Devil's Advocate objected to and `run/09-test-lead-decision.md` to see how each objection was resolved.

To regenerate the data: `python tools/generate_synthetic.py`. To rerun a review with Claude Code: `/review-run examples/01-generator-saturation`.
