# Concept: baseline and regression tracking across builds

> **Status: Partly implemented.**
> - **Implemented**:
>   - comparison of one test run against one baseline run, named in `scenario.json`;
>   - per-transaction p90, p95 and p99 change, error rate and throughput;
>   - a regression threshold;
>   - tests for all of the above.
>
>   See [`tools/analyze.py`](../../tools/analyze.py) and [test run 00](../../examples/00-baseline/).
> - **Concept**: the run registry, baseline selection rules and statistical comparison below.

## Problem

A single named baseline works for one comparison. Across releases, a performance team needs answers to three questions:

- Which run is the current baseline, and who accepted it?
- Is a change real or noise?
- Is response time drifting across builds, even when each single comparison passes?

## Design

### Run registry

`registry/runs.json` lists every analyzed test run:

```json
{
  "run_id": "SYN-RUN-000",
  "build": "4.12.0",
  "test_type": "load",
  "workload_model": "checkout-500",
  "environment": "PERF-A",
  "test_validity": "Valid",
  "go_no_go": "Go",
  "accepted_as_baseline": {"by": "<release approver>", "date": "2026-09-24"},
  "transaction_summary": "examples/00-baseline/data/transaction_summary.csv"
}
```

### Baseline selection rules

1. Same test type, workload model and environment.
2. The test validity result is Valid, and a person accepted the run as a baseline.
3. The most recent run that meets 1 and 2, unless the test run names a specific baseline.
4. A test run that is Invalid can never become a baseline. Its comparison is reported as an observation only. Test run 01 is the example: every transaction looks slower than the baseline, but the test is invalid, so there is no regression verdict.

### Comparison

| Measure | Method |
| --- | --- |
| Percentile change | p90, p95 and p99 per transaction, against a threshold per transaction (*implemented, single threshold*) |
| Is it real? | Compare the distributions of per-minute values in the two steady states (for example with a Mann–Whitney U test), not just two numbers |
| Throughput and errors | Steady-state TPS and error % by type (*implemented for TPS and total error %*) |
| Drift | p95 per transaction across the last N accepted runs, to flag slow growth that no single comparison exceeds |

### Who uses it

- The **Results Analyst** reports regressions and whether the test validity result supports them.
- The **Performance Test Lead** includes unexplained regressions in the go/no-go recommendation.
- The **Test Report Author** adds a trend graph per transaction across builds.

## Open questions

- Thresholds per transaction, or one per SLA.
- How long accepted runs stay in the registry before they stop being useful baselines (for example, after an environment change).
