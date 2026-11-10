# V2 traceability

The analysis workflow started as a single long AI prompt for analyzing load test results, "V2" (*OpenText LRE MCP AI Performance Analysis Prompt V2, Performance Engineer Edition*). This page traces each V2 requirement to where it lives in the current workflow.

## Source

| Field | Value |
| --- | --- |
| File name | OpenText_LRE_MCP_AI_Performance_Analysis_Prompt_V2.docx |
| Size | 44,408 bytes |
| SHA-256 | `f7e771ad7ac681637aea0c5d4755df650b31ef70a6cbcd9d7459105ba714326f` |
| Inspected | 2026-11-08, in full, at the owner's request |
| Storage | Owner-controlled, outside this repository. The document is not committed here. |

V2 was reconstructed from a vendor MCP demonstration workflow and extended with performance engineering controls: test validity, correlation quality, confidence, baseline comparison and actionable recommendations. It applies whether data is retrieved through MCP or supplied manually.

## Requirements

**Status key**
- **Implemented**: built into the workflow, role files or tooling in this repository.
- **Partly implemented**: the difference is stated in the row.
- **Concept**: designed in [docs/concepts/](concepts/README.md), not built.

| ID | V2 requirement | V2 source | Where it lives now | Status |
| --- | --- | --- | --- | --- |
| V2-01 | Exact run isolation; no substitution from other runs; missing current-run data stays visibly missing | Steps 0 and 2 | [Rule 1 and rule 4](../method/rules.md); Results & Monitoring Analyst | Implemented |
| V2-02 | Inventory first, then tiered retrieval and completeness | Step 1 | Stage 2; [Results & Monitoring Analyst](../agents/results-monitoring-analyst.md); data inventory in `tools/analyze.py` | Implemented |
| V2-03 | Validate data integrity; normalize timestamps, time zones, clock skew, sampling and gaps | Step 3 | `tools/analyze.py` (UTC conversion, gap listing); Results & Monitoring Analyst | Implemented (clock skew is checked by the agent, not the tool) |
| V2-04 | Mandatory workload and test harness validity check with three classifications | Step 4; Performance Test Validity Checklist | [Test Execution Analyst](../agents/test-execution-analyst.md): Valid, Valid with limitations, Invalid | Implemented |
| V2-05 | Phase and endurance analysis; no full-run average where phases differ | Step 5; Mandatory Test-Phase Analysis | [Results Analyst](../agents/results-analyst.md); time windows split at onset in `tools/analyze.py`; soak checks by test type | Implemented |
| V2-06 | Consult and correlate all relevant sources; disclose unavailable or partial ones | Step 6 | The three engineers; GAP- records | Implemented |
| V2-07 | Four finding classes plus a separate confidence, with supporting and contradicting evidence | Step 7; Finding Classification Standard | [Root-cause status and confidence](../method/test-summary-results.md); HYP- records list supporting and contradicting metrics | Implemented (classes renamed to Symptom, Correlated metric, Suspected bottleneck, Confirmed root cause) |
| V2-08 | Baseline comparison only against an approved, explicitly supplied run, kept separate | Step 8; Optional Baseline Comparison Rules | `baseline` in `scenario.json`; baseline comparison in `tools/analyze.py`; [rule 1](../method/rules.md); [registry concept](concepts/baseline-and-regression.md) | Implemented (approval tracking is concept) |
| V2-09 | SLA/NFR and business impact; prioritized, owned, testable recommendations; next diagnostic experiment where uncertain | Steps 9 and 10; Recommendation Format | [Performance Test Lead](../agents/performance-test-lead.md) go/no-go; REC- fields; [rule 13](../method/rules.md) | Partly implemented: business impact is not a required field |
| V2-10 | Standalone HTML report in the V2 structure; final validation before delivery | Step 11; Required Report Structure; Final Validation Checklist | [Test Report Author](../agents/test-report-author.md): `TEST-SUMMARY.md` with report checks | Partly implemented: Markdown, not HTML; tester-oriented order with the executive summary first (see differences) |
| V2-11 | Run-specific workspace; original filenames preserved | Steps 0 and 1; Suggested Run Workspace | One folder per test run (`examples/<run>/`) | Partly implemented: synthetic files use standard names; preserving tool export names is part of the [adapter concept](concepts/agent-tool-contracts.md) |
| V2-12 | Data sources and limitations table: availability, coverage, analysis status, impact on confidence | Data Sources / Limitations Table Template | Data inventory and GAP- records ("effect on the analysis") | Implemented |
| V2-13 | Wording follows the finding class ("Observed…", "Correlated with…", "Likely contributed…", "Root cause confirmed…") | Finding Classification Standard | [Style guide](style-guide.md#wording-by-root-cause-status) | Implemented |
| V2-14 | Required evidence sources are inventoried, including controller, load generator, agent and monitoring-host resources | Required Evidence Sources to Inventory | Data inventory; load generator utilization in the Test Execution Analyst role | Partly implemented: the synthetic runs have no controller or monitoring-host data |

## Differences from V2, by design

- **Report order.** V2's report structure has 22 sections, with the executive summary as section 4, after scope, data limitations and validity. The Test Report Author puts the executive summary first, the order release managers and testers expect, and keeps scope, limitations and validity right after it. *Open for the owner to confirm.*
- **Sequencing.** V2's numbered steps put data integrity and time normalization (Step 3) before the validity check (Step 4). Its one-line Execution Flow Summary lists them the other way round. The workflow follows the numbered steps.
- **Platform scope.** V2 assumes .NET and IIS evidence (sections 12, 13 and 17). The workflow is tool-neutral and runtime-neutral. For a given stack, the equivalent runtime evidence is used, or the section is marked not applicable with a reason.
- **Additions that are not in V2:**
  - SLA results kept separate from root-cause status;
  - the multi-agent team with a Peer Reviewer, and the resolution of review comments;
  - deterministic tooling;
  - graphs;
  - a conditional CPU-bound throughput ceiling (Utilization Law);
  - a human release approver for the go/no-go recommendation.
