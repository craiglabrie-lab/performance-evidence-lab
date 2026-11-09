# Data and safety

## Data

- Only synthetic data is committed. Every scenario says so in `scenario.json`.
- Real test results, logs, hostnames, topology and generated reports belong outside this repository. Removing a company name does not anonymise a workload or an architecture.
- `.gitignore` excludes common load-tool result formats, but it is not data-loss prevention.

## Untrusted content

Logs and captured responses come from the system under test and can contain anything, including text that looks like instructions to an AI. The fact-sheet tool flags such lines; every agent's rules say they are data with no authority. Scenario 01 contains one deliberately, to show this working.

## Actions

The team reads and recommends. No agent launches load, changes configuration, files tickets, or sends a report anywhere. Recommendations name an owner and an experiment; a person decides whether to act.

## Honesty about execution

Every agent file states how it ran: a separate agent context, which model. Reports state that all agents share one model and that file-access limits were instructions. No report claims more independence, enforcement or real-world validation than actually took place.
