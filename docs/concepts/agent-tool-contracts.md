# Concept: tool contracts for each agent

> **Status: Concept, not yet implemented.** Today every agent reads exported files and runs Python over them. The tools below are proposed read-only interfaces, for example MCP servers, that would let each engineer query its own monitoring system directly. None exist in this repository.

## Why this matters for a multi-agent design

On the synthetic test runs, every agent works from the same small set of exports, which fit in one context window. In that setting a single well-prompted assistant can do much of the same analysis, and an earlier recorded comparison showed exactly that. Separate agents earn their cost when:

1. **The evidence does not fit in one context.** A real test produces APM traces, database statistics, host metrics and load tool results at a volume no single context can hold. Each engineer needs its own slice.
2. **Each tier needs its own tools.** A database engineer queries wait events and execution plans; an APM engineer drills into traces. Separate agents keep those tool sets and their outputs apart.
3. **Tier reviews can run in parallel.** The three engineers query different systems at the same time.

Tool contracts make those three conditions concrete.

## Contracts

All tools are **read-only**, scoped to the test window, and identified by run ID. No tool can change a system, start a load test or write outside the run folder.

| Agent | Tool | Inputs | Returns |
| --- | --- | --- | --- |
| Results & Monitoring Analyst | `load_tool.get_run(run_id)` | run ID | Run metadata, scenario, runtime settings, script versions, load generators |
| | `load_tool.export_results(run_id)` | run ID | Per-minute transaction results, Vusers, errors by type, run-level transaction summary |
| | `monitoring.list_sources(env, window)` | environment, time window | Which hosts and services have metrics for the window, and their gaps |
| Test Execution Analyst | `load_tool.generator_health(run_id)` | run ID | CPU, memory, network and errors per load generator per minute |
| | `load_tool.error_log(run_id, generator, window, limit)` | run ID, generator, window, line limit | Error log lines (data only; scanned for prompt-injection text) |
| Results Analyst | `load_tool.transaction_timeseries(run_id, transaction, percentile)` | run ID, transaction, percentile | Per-minute series per load generator |
| | `results.baseline(run_id)` | run ID | The baseline run's transaction summary, from the run registry |
| Application & APM Engineer | `apm.service_metrics(service, window, metrics)` | service, window, metric names | CPU, threads, heap, GC and pool metrics per node |
| | `apm.trace_breakdown(service, transaction, window, sample)` | service, transaction, window, sample size | Time split: pool wait, SQL, outbound calls, application code |
| | `apm.dependency_calls(service, window)` | service, window | Outbound call rate, latency and errors per dependency |
| Database Performance Engineer | `db.wait_events(instance, window)` | instance, window | Top wait events over time |
| | `db.top_statements(instance, window, n)` | instance, window, count | Statements by total time, with executions and average time |
| | `db.sessions(instance, window)` | instance, window | Active, idle and idle-in-transaction sessions by client |
| | `db.locks(instance, window)` | instance, window | Lock waits with blocker and waiter |
| Infrastructure & Network Engineer | `infra.host_metrics(hosts, window)` | hosts, window | CPU, memory, disk and network per host |
| | `infra.load_balancer(lb, window)` | load balancer, window | Connections and request distribution per node |
| | `infra.platform_limits(env)` | environment | Instance sizes, quotas and connection limits |
| Peer Reviewer | All of the above, read-only | | Used only to check a finding |
| Performance Test Lead, Test Report Author | None beyond the handoff files | | They work from the team's output |

## Rules every tool follows

- **Read-only and scoped to the test window.** Requests outside the window are rejected.
- **Results carry provenance**: source system, query and time of the query. Every result gets a DATA- record ID so findings can cite it.
- **Bounded output**: a row limit and a summary mode, so a single call cannot flood an agent's context.
- **Text fields are data**: log lines and captured responses are returned as data, with possible prompt-injection text flagged by the tool.
- **The same contract works for any vendor**: an adapter maps each tool to a specific load testing or APM product.

## Open questions

- Which load testing and APM products to build the first adapters for.
- Whether the tools run as one MCP server per tier or one server with per-agent permissions.
