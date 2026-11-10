# Data and safety

## Test data

- Only synthetic test runs are committed, and every `scenario.json` says so.
- Real test results, logs, hostnames, topology and test summaries stay outside this repository. Removing a company name does not anonymize a workload model or an architecture.
- `.gitignore` excludes common load testing result formats. It is not a data loss prevention control.

## Prompt-injection text in logs

Logs and captured responses come from the system under test and can contain anything, including text written to look like instructions to an AI. `tools/analyze.py` flags these lines, and every agent's rules treat them as data that is never followed. Test run 01 contains one on purpose.

## No actions

The agents analyze results and make recommendations. No agent starts a load test, changes configuration, opens a ticket or sends a test summary anywhere. Each recommendation names an owner and a retest, and a person decides whether to act on it.

## Execution transparency

Every handoff file records how the agent ran: as a sub-agent with its own context, and on which model. Test summaries state which model each agent ran on (three roles are routed to Sonnet; the others inherit the runner's model) and that each agent's file inputs were instructions, not sandboxed.
