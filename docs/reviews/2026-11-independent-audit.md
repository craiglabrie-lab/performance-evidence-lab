# Independent technical audit: findings and status

An external technical and architectural audit reviewed commit `164f09a`. It reproduced each defect on temporary copies of the synthetic test runs. This file records each finding, what changed, and the test that locks the fix in.

The audit judged the agent workflow from its definitions only. Agent behavior, token cost and comparative accuracy were not measured; the recorded, scored run is still the next stage.

## Confirmed defects

| ID | Severity | Finding | Status | Regression tests (`tests/test_analyze.py`) |
| --- | --- | --- | --- | --- |
| PEL-01 | High | A window response-time SLA trusted the run-level summary even when it contradicted the per-minute data or had a conflicting duplicate row, and could Pass | **Fixed.** The summary is validated on load: counts, accounting, response-time order, the steady-state window, and duplicates (conflicting rows are not used). A window percentile is used only when the summary reconciles with complete per-minute rows for that transaction. | `test_window_response_time_rejects_*`, `test_window_response_time_uses_reconciled_summary_without_minute_percentiles` |
| PEL-02 | High | A baseline or current run missing an entire load generator could still qualify for regression verdicts | **Fixed.** The baseline is loaded with the same validation as the current run. Both runs must have every expected load generator, scheduled Vusers equal to the planned total, running equal to scheduled, every declared transaction, and a summary that reconciles. | `test_baseline_missing_a_generator_is_not_comparable`, `test_current_run_missing_a_generator_is_not_comparable` |
| PEL-03 | High | Impossible transaction statistics (negative p95, counts that do not add up) were eligible for Pass | **Fixed.** Rows where passed + failed ≠ count, or failure types do not add up to failed, are treated as missing. Negative, out-of-order, or zero-sample response times are blanked. | `test_impossible_transaction_statistics_never_pass`, `test_invalid_rows_are_reported_and_never_pass` |
| PEL-04 | High | Unsupported SLA scopes (per-generator throughput), unit mismatches and duplicate SLA IDs could produce a Pass for a different requirement | **Fixed.** Each SLA is checked against a type, evaluation, unit and statistic matrix. Anything outside it, and any duplicated ID, is Not evaluated with the reason. Units are never converted. | `test_unsupported_sla_scope_is_not_evaluated`, `test_unit_mismatch_is_not_evaluated`, `test_duplicate_sla_ids_are_not_evaluated` |
| PEL-05 | High | Scenario-controlled paths could read files outside the run folder and write a graph outside the graphs folder | **Fixed.** Source files must be plain names that resolve inside the run folder (links included). The baseline must be inside an allowed root (`--baseline-root`). Graph file names are sanitized and checked for containment. | `test_source_paths_cannot_leave_the_run_folder`, `test_graph_names_cannot_leave_the_graphs_folder`, `test_baseline_outside_the_allowed_root_is_not_read` |
| PEL-06 | Medium | The baseline regression check rounded before comparing: 10.04% read as 10.0% and was not flagged | **Fixed.** The threshold is checked at full precision; rounding is for display only. | `test_regression_threshold_uses_unrounded_change` (exactly 10%, just above, just below) |
| PEL-07 | Medium | Zero CPU, an empty monitoring file, a malformed row or a missing baseline file crashed the analysis | **Fixed.** A zero-CPU ceiling is reported as undefined. Malformed rows are reported and treated as missing. An unloadable baseline is reported as not available. The CLI exits with a clear message instead of a stack trace. | `test_data_problems_are_reported_not_crashes`, `test_cli_reports_input_errors_with_exit_status` |
| PEL-08 | Medium | The response-time graph was not valid XML (an unescaped `<=` in the threshold label), and an unsupported SLA statistic crashed graph generation | **Fixed.** All graph text is escaped. Only SLAs the tool can evaluate are drawn as threshold lines. A graph that cannot be drawn is skipped and reported. | `test_every_standard_graph_is_valid_xml`, `test_unsupported_sla_statistic_does_not_break_graphs` |

## Design risks

| Risk | Status |
| --- | --- |
| Test validity and release gating depend on prompts | **Partly addressed.** SLA results from the tool are now labeled candidate results. `tools/check_run.py` checks the Results block in the go/no-go recommendation and the test summary. The test validity result must match the Test Execution Analyst's, no SLA result can be stronger than the computed candidate, and an Invalid test reports every SLA as Not evaluated and no Go. Tests: `tests/test_check_run.py`. |
| An interrupted run can mix evidence | **Addressed.** Every run gets a fresh `run-<UTC timestamp>/` folder, and a step does not start if a handoff it needs is missing, empty or older than the computed results. |
| Sample duration is implicit | **Addressed.** Only 60-second buckets are accepted; other `window_seconds` values are reported and treated as missing, never rescaled. |
| CPU and throughput averaged over different minutes | **Addressed.** The CPU-bound ceiling now pairs CPU and throughput by minute and reports how many minutes it used. |
| Evidence and answer-key isolation are procedural | **Open.** All agents have Bash, so file limits and the rule not to read `evaluation/` are instructions. The README and architecture docs now say so. Runtime sandboxing and permission rules are needed before sensitive results are used. |
| README wording overstated the evidence | **Fixed.** "Prevents" is now "is designed to catch", and model routing is stated accurately (three roles on Sonnet, the rest inherit the runner's model). |

## Not adopted yet

- **Three runs of each approach on three cases.** This is the right design for a full evaluation, but too costly for the next stage. The next stage is one scored run of test run 02 against two single-prompt comparisons. Repeated runs and a blind case written by a second engineer follow once the cost of one run is known.
- **Validation against real load tool exports.** This needs adapters for each export format, confirmed against the tool's own counts and percentiles. It is on the [roadmap](../product/roadmap.md).
