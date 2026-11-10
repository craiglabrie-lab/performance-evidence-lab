# Persona review, November 2026

The repository was reviewed from three points of view: a performance engineer, a performance tester, and an AI engineer who has shipped multi-agent systems in production. This page records each point and what happened to it.

**Status key**
- **Implemented**: built and tested in this repository.
- **Concept**: the design will be written up as a concept document, labeled as not yet implemented.
- **Planned**: needs recorded agent runs or real data, and is on the [roadmap](../product/roadmap.md).

## Performance engineer

| # | Feedback | Status | Where |
| --- | --- | --- | --- |
| PE-1 | No baseline or regression comparison. Real analysis compares against the last accepted run or build. | **Implemented**: a baseline run (SYN-RUN-000, build 4.12.0), a `baseline` block in `scenario.json`, and a baseline comparison with a regression threshold in the computed results summary. The baseline is used for comparison, never to fill gaps. Concept doc for multi-run regression tracking to follow. | `examples/00-baseline/`, `tools/analyze.py`, [rules](../../method/rules.md) |
| PE-2 | No test type. Load, stress, soak and spike tests need different checks. | **Implemented**: `test_type` in `scenario.json`, and test-type checks in the Performance Test Lead, Test Execution Analyst, Results Analyst and Application & APM Engineer roles. Only load tests have example data so far. | `agents/` |
| PE-3 | No capacity analysis: throughput curve, service demand, headroom. | **Implemented**: Utilization Law service demand and throughput at 80% CPU per tier and window, plus headroom checks in each engineer's role. | `tools/analyze.py`, `agents/*-engineer.md` |
| PE-4 | Environment parity is missing from test validity. | **Implemented**: `environment_parity` in `scenario.json` (scale, database volume, cache warm-up, external dependencies), checked by the Test Execution Analyst and used to limit production projections. | `agents/test-execution-analyst.md` |
| PE-5 | Only p95 is reported. | **Implemented**: min, average, p90, p95, p99, max and standard deviation per transaction, per load generator and overall. | `transaction_summary.csv`, `facts.md` |
| PE-6 | Errors are not classified. | **Implemented**: failures split into client timeouts, HTTP 5xx and content check failures, per minute and per window, with a new analysis rule. | `transactions.csv`, [rules](../../method/rules.md) |

## Performance tester

| # | Feedback | Status | Where |
| --- | --- | --- | --- |
| PT-1 | Script validity is missing: correlation, test data, content checks. | **Implemented**: script, test data and runtime settings in `scenario.json`; script validity checks in the Test Execution Analyst role. | `agents/test-execution-analyst.md` |
| PT-2 | No execution metadata: build, script versions, test data, runtime settings, changes since the last run. | **Implemented**: shown in the test run overview at the top of every computed results summary. | `facts.md` |
| PT-3 | The test summary does not look like a test summary: no transaction summary table, no graphs. | **Implemented**: transaction summary table and four standard graphs (running Vusers, throughput, checkout p95, errors), and a test summary report structure that includes both. | `charts/`, `agents/test-report-author.md` |
| PT-4 | The computed results summary is hard for a tester to read. | **Implemented**: it now opens with the test run overview, transaction summary, graphs, baseline comparison, errors by type and capacity. The per-minute detail follows. | `facts.md` |

## AI engineer (multi-agent systems in production)

| # | Feedback | Status | Where |
| --- | --- | --- | --- |
| AI-1 | The orchestrator is a prompt: no state machine, checkpoints, retries or resume. | **Concept**: orchestrator design with run state, checkpoints, resume from step N, and a human sign-off step. | Concept document to follow |
| AI-2 | Handoffs are free-form Markdown. | **Concept**: JSON Schema for findings, SLA results, hypotheses and review comments, validated after each step and rendered to Markdown. | Concept document to follow |
| AI-3 | Guardrails are instructions only. | **Implemented in part**: each role is now a Claude Code sub-agent in `.claude/agents/` with an enforced tool list (no web access, no launching other agents). File-level limits are still instructions, and this is stated. | `.claude/agents/`, [how the workflow runs](../architecture/how-the-workflow-runs.md) |
| AI-4 | Cost and context are not engineered: every agent reads everything. | **Concept**: per-agent context slices, model routing (smaller models for routine roles), prompt caching and token budgets per step. | Concept document to follow |
| AI-5 | The case for multiple agents is not shown yet. | **Concept**: tool contracts per engineer (APM, database and load testing tool queries, for example over MCP) that a single context could not hold. | Concept document to follow |
| AI-6 | The evaluation would not convince an AI engineer. | **Concept, then Planned**: evaluation harness with repeated runs, automated scoring from structured output, and a judge on a different model. The answer key and its pre-run hash are already in place. | [evaluation](../../evaluation/README.md) |
| AI-7 | No human approval point or observability. | **Implemented in part**: the go/no-go recommendation is now explicitly for a human release approver, and the test summary report has an approval block. Step-level tracing is part of the orchestrator concept (AI-1). | `agents/performance-test-lead.md`, `agents/test-report-author.md` |

## Role names

The roles were also renamed to match performance testing practice:

| Before | After |
| --- | --- |
| Test Data & Monitoring Analyst | Results & Monitoring Analyst |
| Test Validity Analyst | Test Execution Analyst |
| Performance Analyst | Results Analyst |
| Report Author | Test Report Author |
