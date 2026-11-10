# Vision and scope

## The problem

A load test produces a lot of data: transaction response times, Vuser counts, load generator health, and application, database and network metrics, plus logs. Analyzing it well takes an experienced performance engineer, because the answers that matter are not in any single file:

- Did the test achieve its load profile, or did the test harness fail?
- Which degradation started first, and on which load generator, node or transaction?
- Is the database slow, or are requests queuing for a database connection?
- How confident is the root cause, and what retest would confirm it?

AI can read all of that data in seconds and write a polished report. A polished report is not the same as a correct one. Typical mistakes are a confident root cause from a test that never reached its load profile, or "probable database contention" that the database's own metrics contradict.

## The approach

Build the analysis practice of an experienced performance team into an agentic workflow:

- the Performance Test Lead orchestrates the analysis and issues the go/no-go recommendation;
- one agent inventories the test data and monitoring, aligns the clocks and lists the gaps;
- one agent checks test validity before any bottleneck analysis;
- application, database and infrastructure engineers each identify their tier as the bottleneck or eliminate it with its own metrics;
- a Peer Reviewer reviews the data first, then the team's findings;
- deterministic tooling does every calculation.

## Audience

| Reader | What they get |
| --- | --- |
| Performance engineers | An analysis that ties every finding to its data, considers the alternatives and ends with a retest plan |
| Application, database and infrastructure teams | Precise degradation windows, and either a bottleneck hypothesis for their tier or a clear elimination backed by metrics |
| Release and engineering leaders | A five-line executive summary: is the test valid, which SLAs failed, and the go/no-go recommendation |

## In scope

- Offline analysis of one test run's exported results.
- Two synthetic test runs with an answer key written in advance.
- Deterministic tooling for the computed results summary, with tests.
- A portable single-prompt version of the workflow for teams without an agent runtime.

## Out of scope

- Running load tests, changing systems or opening tickets. The agents analyze results and recommend.
- Live integration with load testing or APM tools. A future adapter would produce the same computed results summary from real exports.
- Accuracy or time-saved figures for production results. Those need real, authorized data.

## Success

On each test run the agent team should reach the expected test validity result and SLA results, identify the expected bottleneck, eliminate the misleading signals, and produce a test summary a release manager can act on from the executive summary alone. The [evaluation](../../evaluation/README.md) records how recorded runs score against that, and how a single AI assistant scores on the same data.
