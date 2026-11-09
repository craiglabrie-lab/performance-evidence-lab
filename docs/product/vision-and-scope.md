# Vision and scope

## The problem

A load test produces a lot of evidence: transaction results, virtual-user counts, load-generator health, application, database and network metrics, logs. Reviewing it well takes an experienced engineer, because the important questions are not in any single file:

- Did the test actually produce the load we intended, or did the harness fail?
- Which symptom came first, and on which generator, node or transaction?
- Is the database slow, or is everyone waiting to reach it?
- How sure are we, and what would prove us wrong?

AI can now read all of that evidence in seconds and write a fluent report. Fluent is not the same as right. The typical failure is a confident root cause from a test that never reached its load, or a "probable database issue" that the database's own metrics contradict.

## The idea

Encode the review discipline an experienced performance team uses, and run it as a team of AI agents with distinct seats:

- one agent owns the evidence and its quality;
- one decides whether the test is trustworthy, before anyone diagnoses anything;
- specialists for the application, database and infrastructure each implicate or rule out their own layer with evidence;
- a Devil's Advocate forms its own view first, then challenges the team;
- the Test Lead rules on every objection and owns the decision;
- the arithmetic is done by code, not by the agents.

## Who it is for

| Reader | What they get |
| --- | --- |
| Performance engineers | A review that shows its working: every claim traced to evidence, alternatives considered, a rerun plan |
| Application, database and infrastructure teams | Precise symptom windows and either a hypothesis for their layer or a clear, evidenced "not you" |
| Release and engineering leaders | A five-line summary that says whether the test can be trusted, what failed, and what to do next |

## In scope

- Offline review of one load-test run's exported results.
- Two synthetic demonstration scenarios with recorded runs and a predeclared answer key.
- A deterministic fact-sheet tool and its tests.
- A portable single-prompt version of the method for teams without an agent runtime.

## Out of scope

- Launching load, changing systems, or creating tickets. The team reads evidence and recommends.
- Live integrations with load-testing or APM tools. A future adapter would produce the same fact sheet from real exports.
- Claims about real-world accuracy or time saved. Those need real, authorised data.

## What success looks like

On each scenario the team should reach the expected verdict, find the expected mechanisms, avoid the planted traps, and produce a report a release manager can act on from the first paragraph. The [results](../../evaluation/results.md) record how the recorded runs did against that standard, and how a single well-prompted assistant did on the same data.
