```
Agent: Results Librarian
Run: SYN-RUN-002
Read: agents/results-librarian.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, external_calls.csv, checkout_traces.csv); examples/02-connection-pool/facts.md; examples/02-connection-pool/run/01-test-lead-plan.md
Execution: separate agent context, model Claude Opus 5.5
```

Data note: `scenario.json` marks this dataset as synthetic ("Invented data for demonstration"). It is registered here as though it were a real run.

This file describes the evidence: what each source is, how far it covers the run and how far it can be trusted. It does not interpret performance or say what caused anything. Every number below comes from `facts.md`, a raw file, or a command in the appendix (rule 3).

**Fact sheet check.** I regenerated the fact sheet with `tools/analyze.py` and compared it with `facts.md`. They are identical apart from the first line (command A1). `facts.md` is therefore a faithful deterministic summary of the files in `data/`. The issues it inherits from the raw data are listed under DQ- below.

## 1. Evidence register

Elapsed minute *m* = UTC 10:*m*:00 on 2026-10-08. Steady state is minutes 10–39, as declared in `scenario.json`.

| ID | File | Scope | Time basis | Coverage | Limitations |
| --- | --- | --- | --- | --- | --- |
| E-01 | `scenario.json` | Run identity, question, intended workload, SLA-1..3, environment, harness settings, scheduled jobs, source descriptions | Declares start 2026-10-08T10:00:00Z, 45 min | n/a | Declarations, not measurements. The `run_notes` claim that nothing changed between runs cannot be verified from this run's data (see §3). |
| E-02 | `transactions.csv` | LG1: search, add_to_cart, checkout per minute (count, passed, failed, avg_s, p95_s) | UTC, 60 s windows (`window_seconds` = 60 in all 264 rows) | Minutes 0–43 for each transaction (44/45). Minute 44 has no row (DQ-03) | p95 is per generator, per transaction, per minute. It cannot be averaged across minutes or generators. Transaction failure reasons are not recorded (DQ-10). |
| E-03 | `transactions.csv` | LG2: same fields as E-02 | UTC, 60 s | Minutes 0–43 for each transaction (44/45). Minute 44 has no row (DQ-03) | As E-02 |
| E-04 | `vusers.csv` | LG1 and LG2: scheduled, running and exited_with_error users per minute | UTC | 45/45 per generator | Running equals scheduled in all 90 rows. exited_with_error is 0 throughout, which is inconsistent with `abort_on_error: true` (DQ-04). |
| E-05 | `load_generators.csv` | LG1 and LG2 host: cpu_pct, memory_pct, script_errors, log_level | UTC | 45/45 per generator | The meaning of script_errors is undocumented and it does not match transaction failures (DQ-05). Whether the CPU figure is an average or a sample is undocumented (DQ-07). |
| E-06 | `app_servers.csv` | app1: cpu, heap, gc_pause, active/max threads, db pool active/max, pool wait | UTC | 45/45 | APM metric semantics (point-in-time, mean or max per minute) are undocumented (DQ-07). |
| E-07 | `app_servers.csv` | app2: same fields as E-06 | UTC | 45/45 | As E-06 |
| E-08 | `database.csv` | Database host: cpu, active_sessions, avg_query_ms, lock_wait_ms, top_wait_event | **Server local time, offset -0400 on all 45 rows**, converted to UTC (see §2) | 45/45 after conversion (minutes 0–44, no duplicates) | Exported from the DB host, not APM. Minute-level ordering against APM is not reliable at the onset transition (DQ-06). No query-level, statement-level or lock-holder data (DQ-10). |
| E-09 | `network.csv` | lb1: active_connections, throughput_mbps, retransmit_pct | UTC | 45/45 | Minute 44 active_connections = -1, which is not a valid count (DQ-01). |
| E-10 | `external_calls.csv` | APM view of outbound calls to `payment-sandbox`: calls, avg_ms, p95_ms, errors | UTC | 45/45 | Caller-side view only. There are no sandbox-side metrics (DQ-10). Minute 44 reports latency with 0 calls (DQ-02). p95_ms is per minute and cannot be averaged. |
| E-11 | `checkout_traces.csv` | app1 checkout traces: total, pool_wait, sql, payment_call, db_connection_held (ms) | UTC | 88 traces, 2 per minute, minutes 0–43 | A fixed-schedule sample of about 0.2% of checkouts. It cannot produce percentiles or population values (DQ-08). |
| E-12 | `checkout_traces.csv` | app2 checkout traces: same fields as E-11 | UTC | 44 traces, 1 per minute, minutes 0–43 | As E-11. Half the trace count of app1, always at second :27 (DQ-08). |
| E-13 | `facts.md` | Deterministic summary of E-02..E-12 by `tools/analyze.py` | UTC (DB converted) | As the underlying files | Reproduced exactly (A1). Its min 40–44 summaries include the invalid values in DQ-01 and DQ-02. Its inventory row for traces leaves coverage blank; this register gives it (E-11, E-12). |

Useful slices for the analysts. Each is a window of the items above, not a new source:

| ID | Slice | Window |
| --- | --- | --- |
| E-14 | E-02 + E-03 checkout rows, steady state before first SLA failure | minutes 10–18 |
| E-15 | E-02 + E-03 checkout rows, steady state from first SLA failure | minutes 19–39 |
| E-16 | E-06 + E-07 + E-08 + E-10 transition minutes | minutes 18–20 and 39–41 |
| E-17 | E-08 rows with top_wait_event "row lock contention" | minutes 30–33 |

## 2. Time

| Source | Time basis | Normalised in facts.md | Check |
| --- | --- | --- | --- |
| transactions, vusers, load_generators, app_servers, network, external_calls | UTC (`...Z`) | Already UTC | `elapsed_min` agrees with the timestamp in every row of every file (0 mismatches, A2) |
| checkout_traces | UTC, second resolution | Already UTC | `elapsed_min` agrees with the timestamp in all 132 rows (A2) |
| database | Local time, `-0400` on every row | Yes: "converted to UTC using the offset in each timestamp" | 06:00-0400 to 06:44-0400 converts to 10:00Z to 10:44Z = minutes 0–44, 45 unique minutes, no duplicates or gaps (A2) |

**Alignment across sources.** UTC minute buckets line up for all APM, load-tool and LB sources. The conversion of the DB timestamps is correct. However, the DB and APM series do not move together in the same way at the two transitions (A3):

- Onset: at minute 19, app pool active is 17 + 17 = 34 but DB active_sessions is 9. DB sessions reach 40 at minute 20.
- Recovery: at minute 40, app pool active is 7 + 5 = 12 and DB active_sessions is 8. DB drops in the same minute as APM.

A fixed one-minute clock offset would produce a lag at both transitions, and this data shows a lag at only one. Neither source documents whether a value is a point-in-time sample, a mean or a maximum, or which instant inside the minute it represents (DQ-06, DQ-07). **Any claim that a DB signal led or lagged an app-tier signal by one minute should not rest on these two files.**

Other timing facts:
- The trace timestamps fall at seconds :10, :27 and :44 of every minute (A4). Traces give the only sub-minute timing in the dataset.
- The scheduled inventory-sync batch at 10:30 UTC corresponds to elapsed minute 30 (E-01).
- No source documents whether a transaction is bucketed by start or end time. Checkout avg_s reaches 2.91–4.55 s in minutes 19–39 (E-13), so a request near a minute boundary could fall in either minute.

## 3. Coverage

Every entity is present for every steady-state minute (10–39) in every source: 30/30 (A2, A4, `facts.md` inventory). **There are no gaps inside the steady state.**

| Source | Entity | Minutes present | Missing / invalid |
| --- | --- | --- | --- |
| transactions.csv | LG1, LG2 × search / add_to_cart / checkout | 44/45 (0–43) | Minute 44 has no rows. vusers shows 0 scheduled and 0 running at minute 44 (DQ-03). |
| vusers.csv | LG1, LG2 | 45/45 | none |
| load_generators.csv | LG1, LG2 | 45/45 | none |
| app_servers.csv | app1, app2 | 45/45 | none |
| database.csv | host | 45/45 | none |
| network.csv | lb1 | 45/45 | Minute 44 active_connections = -1 (DQ-01) |
| external_calls.csv | payment-sandbox | 45/45 | Minute 44: 0 calls with avg 274 / p95 408 ms (DQ-02) |
| checkout_traces.csv | app1 / app2 | 44/45 (0–43), exactly 3 per minute | Minute 44 has none (0 checkouts) |

Volumes (A2, A5):
- Transactions: 212,488 executed across the run. In steady state, 53,795 in minutes 10–18 and 113,631 in minutes 19–39.
- Failures: 871 failed across the run, every one in minutes 0–43.
- Steady-state error rate: (105 + 677) / (53,795 + 113,631) = 0.47%, matching `facts.md`. By generator over minutes 10–39: LG1 0.465%, LG2 0.469%.
- Checkouts: 13,491 in minutes 10–18 (27 traces = 0.200%) and 28,441 in minutes 19–39 (63 traces = 0.222%).

## 4. Meaning of each metric

| Source | Metric | Unit | Per-minute or cumulative | Per entity or combined | Sampled or complete | Combining rules |
| --- | --- | --- | --- | --- | --- | --- |
| E-02/03 | count, passed, failed | requests | per minute | per generator per transaction | complete (load tool) | Additive. count = passed + failed in all 264 rows (A2). |
| E-02/03 | avg_s | seconds | per minute | per generator per transaction | complete | Can be combined across generators only when weighted by count |
| E-02/03 | p95_s | seconds | per minute | per generator per transaction | complete | **Not combinable** across generators, minutes or transactions. Compare per minute, or summarise as median and max (rule 5). SLA-1 is declared per minute per generator. |
| E-04 | scheduled / running / exited_with_error | users | per minute (state) | per generator | n/a | Additive across generators |
| E-05 | cpu_pct, memory_pct | % | per minute | per generator | unstated (DQ-07) | Do not add across hosts |
| E-05 | script_errors | count | per minute | per generator | undocumented meaning (DQ-05) | Not interchangeable with transactions `failed` |
| E-05 | log_level | enum | per minute | per generator | n/a | "standard" for both generators in all 90 rows (A2) |
| E-06/07 | cpu_pct, heap_used_pct | % | per minute | per node | unstated (DQ-07) | Per node only |
| E-06/07 | gc_pause_ms | ms | per minute | per node | unstated: could be total, maximum or a single sample (DQ-07) | Per node only; compare within the series |
| E-06/07 | active_threads, db_pool_active | count | per minute | per node | unstated (DQ-07) | Summing across nodes assumes the same sampling instant |
| E-06/07 | max_threads, db_pool_max | count | config echo | per node | n/a | 200 and 20 on both nodes in every row (A2) |
| E-06/07 | db_pool_wait_ms | ms | per minute | per node | unstated: could be mean, maximum or total (DQ-07) | Do not compare directly with trace pool_wait_ms without stating the assumption |
| E-08 | cpu_pct, active_sessions, avg_query_ms, lock_wait_ms | %, count, ms, ms | per minute | whole DB host (all clients, not only the app pools) | unstated (DQ-07) | DB sessions are not by definition equal to the sum of app pool active (see §6) |
| E-08 | top_wait_event | enum | per minute | host | dominant event only | Shows the single top event, not the distribution |
| E-09 | active_connections, throughput_mbps, retransmit_pct | count, Mb/s, % | per minute | lb1 | unstated | |
| E-10 | calls, errors | count | per minute | both app nodes combined (no node split) | APM, complete for the app's view | Additive |
| E-10 | avg_ms, p95_ms | ms | per minute | combined across nodes | APM | p95 **not combinable** across minutes. Caller-side latency, which includes the network path to the sandbox. |
| E-11/12 | total, pool_wait, sql, payment_call, db_connection_held | ms | per trace | per node | **sample**, 3/minute on a fixed schedule (DQ-08) | Sample medians are not population values and give no percentiles. Server-side times, not client response times. There is no status field, so failed checkouts cannot be identified. |

Internal arithmetic of the traces holds in all 132 traces (A4):
- db_connection_held ≥ sql + payment_call; the excess is 8–24 ms.
- total ≥ pool_wait + db_connection_held; the excess is 81–199 ms.
- pool_wait > 0 appears only in minutes 19–39.

## 5. Data-quality issues

| ID | Issue | Evidence | Impact on what can be concluded |
| --- | --- | --- | --- |
| DQ-01 | lb1 active_connections = **-1** at minute 44, with throughput 0.0 | E-09; A2 | The value is invalid: treat it as unknown, not zero. The `facts.md` min 40–44 network summary (min -1.0, mean 124.0) includes it. No effect on minutes 0–43 or on the steady state. |
| DQ-02 | payment-sandbox at minute 44 reports **0 calls** with avg_ms 274 and p95_ms 408 | E-10; A2 | Latency figures with no calls behind them are not measurements. The `facts.md` min 40–44 external_calls avg/p95 summary (avg max 275, p95 max 428) includes this row. Exclude minute 44 from any ramp-down latency statement. No effect on the steady state. |
| DQ-03 | transactions.csv and checkout_traces.csv have **no rows for minute 44**. `scenario.json` declares ramp-down as 40–44 | E-02, E-03, E-04, E-11, E-12 | vusers shows 0 scheduled and 0 running at minute 44, so the absence matches no load being applied, not a collection gap. Ramp-down with load is effectively minutes 40–43. Outside the steady state, so no effect on SLA scope. |
| DQ-04 | `abort_on_error: true`, yet **871 transactions failed** (in minutes 1–43, including ramp-up) and **exited_with_error is 0** in every row; running = scheduled in all 90 rows | E-01, E-02, E-03, E-04; A2 | What "abort on error" does in this harness is undocumented. Unknown: whether a failure ends the iteration, the user, or nothing, and whether failed iterations are retried. This limits how far the error accounting (SLA-3) and the "all 500 users ran" claim can be trusted. The Validity Reviewer must resolve or bound it. |
| DQ-05 | LG script_errors total **46** (LG1 24, LG2 22), all in minutes 19–39, while transactions failed total 871, with failures in every loaded minute from 1 to 43 | E-05, E-02, E-03; A2 | The meaning of script_errors is undocumented and it does not reconcile with transaction failures. Do not use either as a proxy for the other. Neither can show by itself whether failures came from the harness or the system. |
| DQ-06 | DB vs APM minute alignment is asymmetric: DB lags the app pools by one minute at onset (19 → 20) but not at recovery (40) | E-06, E-07, E-08; A3 | The UTC conversion is correct, but one-minute ordering between DB and app-tier signals cannot be relied on (rule 8). DB vs APM comparisons are safe only over windows of several minutes. |
| DQ-07 | Sampling semantics are undocumented for host, APM and DB metrics (point-in-time, mean or max per minute): pool active, pool wait, threads, gc_pause, heap, CPU, DB sessions, lock wait. Transaction bucketing rule (start or end time) is also undocumented. | E-05..E-10 | Trends within one series are comparable. Arithmetic across sources (for example pool sum vs DB sessions, or Little's Law estimates using pool_wait_ms) depends on an assumption that must be stated each time it is used. |
| DQ-08 | Trace sampling is deterministic, not random: seconds :10/:27/:44 every minute, node order app1, app2, app1 every minute (88 app1, 44 app2), about 0.2% of checkouts. There is no success/failure field. | E-11, E-12; A4, A5 | Traces show per-request composition for the sampled requests only. They cannot give percentiles, population medians or failure-path behaviour. Node comparisons are weighted 2:1 toward app1, and app2 is only ever observed at second :27. Trace total_ms is server-side and not comparable with load-tool response times. |
| DQ-09 | No data file carries a run ID. Run identity rests on timestamps (2026-10-08 10:00–10:44 UTC) matching `scenario.json` | E-01..E-12; A2 | All files are internally consistent with SYN-RUN-002's declared start and duration, and no file contradicts it. Membership cannot be checked against an independent identifier. Low impact. |
| DQ-10 | **Evidence not in the dataset:** (a) payment-sandbox provider-side metrics, rate limits, tenancy or throttling records; (b) any log showing whether the inventory-sync batch ran; (c) query-level or per-statement DB data, and lock holder/waiter identity; (d) error codes or messages for failed transactions; (e) application logs; (f) GC logs, JVM settings or a config comparison for app1 vs app2; (g) any SYN-RUN-001 data | E-01 (source list); `data/` contents (A5) | Each of these is **unknown, not absent** (rules 4, 9). For example: "no throttling" cannot be claimed from E-10's 0 errors, "the batch ran" cannot be claimed from the schedule, and "the DB is not the cause" cannot be claimed beyond what E-08's host-level metrics show. SYN-RUN-001 must not be used to fill anything (rule 1). |
| DQ-11 | payment-sandbox calls equal checkout count **exactly in every minute 0–43**, including failed checkouts, and including minutes where checkout avg_s is 3–4.5 s and requests could straddle minute boundaries | E-10, E-02, E-03; A2 | This is consistent with one payment call per checkout attempt. The bucketing rules of the two tools are undocumented, so it is unclear whether these are two independent counts. Treat the match as a fact about the export, not as independent corroboration between tools. |

## 6. Configuration and context facts

From E-01 unless noted otherwise. These are reported as facts; others will judge their effect.

**Environment and harness**

- Environment PERF-A, project SYN-SHOP, tool "generic load tool export". Run SYN-RUN-002, start 2026-10-08T10:00:00Z, 45 min.
- 2 app nodes. `db_pool_max_per_node` 20 and `max_threads_per_node` 200. The data echoes both values on both nodes in every row (E-06, E-07). The combined pool max across nodes is 40.
- Payment provider: "third-party payment sandbox (shared test environment; rate limits undocumented)". It appears in E-10 as the single dependency `payment-sandbox`.

**Workload**

- Intended: 250 users each on LG1 and LG2 (500 in total).
- Ramp-up minutes 0–9, steady state 10–39, ramp-down 40–44.
- Iteration "search x2, add_to_cart x1, checkout x1". Fixed pacing of one iteration every 20 s per user, think time 3 s. Expected steady TPS 100.0.
- Achieved schedule (E-04): +25 users per generator per minute, reaching 250 per generator at minute 9 and holding through minute 39. Then −50 per generator per minute, reaching 0 at minute 44.

**Generators**

- LG1 and LG2 are identical in declared config (4 vCPU, log_level "standard").
- Observed log_level is "standard" on both generators in all 45 minutes (E-05), so there is no difference between generators in this setting.
- LG CPU never exceeds 45.9% and memory never exceeds 54.0% on either generator (A6).

**Nodes**

- app1 and app2 have identical declared limits. No other per-node configuration is provided (DQ-10f).

**Acceptance criteria**

- SLA-1: checkout p95 ≤ 2.0 s, each steady-state minute, each generator.
- SLA-2: total throughput ≥ 90 TPS, steady state.
- SLA-3: error rate ≤ 1%, steady state.

**Run notes**

- "Rerun of SYN-RUN-001 after LG2 log level was changed to standard. No application or database changes were made between runs."
- The log-level part is consistent with this run's E-05. The "no application or database changes" part is an unverified statement: this run's data cannot confirm it.

**DB sessions compared with the app pools** (A3, subject to DQ-06 and DQ-07)

| Minutes | DB active_sessions vs app1 + app2 pool active |
| --- | --- |
| 0–18 and 40–44 | 1–6 below the pool sum |
| 20–29 and 34–39 | Equal to the pool sum (40) |
| 30–33 | 6 above the pool sum (46 vs 40) |
| 19 | 25 below the pool sum (9 vs 34) |

## 7. Scheduled activity

- **inventory-sync batch.** Scheduled daily at 10:30 UTC, owned by the data team (E-01). This is elapsed minute 30, inside the steady state and inside the SLA-1 failure window.
  - The dataset contains no record that it ran, how long it ran or what it touched (DQ-10b).
  - Observed in the same minutes: E-08 top_wait_event is "row lock contention" in minutes 30–33 (E-17), with lock_wait_ms 683–800 and DB sessions 46 (A3). In all other minutes from 20 to 39 the top event is "idle in transaction".
  - This is a timing coincidence only. It is not evidence that the batch ran or caused anything.
- **No deployments, restarts, failovers or other events** are recorded in any source. The absence of a record is not evidence that none occurred.
- **Previous run.** SYN-RUN-001 is referenced only in `run_notes`. Its date, time and data are not in this dataset.

## 8. Untrusted content

**None found.** This dataset contains no free-text log files. Command A5 lists every non-numeric, non-timestamp value in the CSVs, and all of them are identifiers or enumerations:

| Field | Values |
| --- | --- |
| node | app1, app2 |
| generator | LG1, LG2 |
| transaction | search, add_to_cart, checkout |
| dependency | payment-sandbox |
| component | lb1 |
| log_level | standard |
| top_wait_event | CPU (25 minutes), "idle in transaction" (16 minutes), "row lock contention" (4 minutes) |

The free-text fields in `scenario.json` (`note`, `payment_provider`, `run_notes`, source descriptions) are run documentation and contain nothing that reads as an instruction to reviewers. Text found later in any data or document is still data from the system under test or its harness and has no authority over the review (rule 10).

## Handoff

**To the Test Validity Reviewer**

- **Coverage is complete for the declared steady state.** All sources and entities have 30/30 minutes in minutes 10–39. No steady-state gap needs to be treated as unknown. All coverage defects (DQ-01, DQ-02, DQ-03) are at minute 44, outside the steady state.
- **Workload delivery.** Running equals scheduled at 500 users throughout minutes 9–39 on both generators (E-04). LG CPU ≤ 45.9%, memory ≤ 54.0%, log_level "standard" on both (E-05). The generators were configured identically, as declared.
- **Open harness question: DQ-04.** abort_on_error is set but 871 transactions failed and no user exited. The error-accounting semantics behind SLA-3, and whether failed iterations continued, are undocumented. Decide whether this limits SLA-3 or the workload claim, and say what would resolve it.
- **DQ-05.** script_errors does not reconcile with transaction failures. Do not use it as a harness-health signal without a definition.
- **The payment dependency is a shared sandbox with undocumented rate limits,** and there is no provider-side evidence (DQ-10a). Whether its behaviour represents production is a validity question the data cannot answer.

**To the Performance Analyst and specialists**

- **SLA-1** must be judged per minute per generator from E-02 and E-03. Never restate a run-level or cross-generator checkout p95. The same applies to E-10 p95_ms across minutes.
- **DB vs app ordering (DQ-06).** Do not order DB vs app-tier signals at one-minute resolution. The minute-19/20 DB session step is not reliable for "who moved first". The traces (E-11, E-12) are the only sub-minute source, at 3 per minute.
- **Traces (DQ-08).** Use traces as examples of request composition, not as population statistics. They are weighted 2:1 toward app1, fixed-schedule, server-side, and carry no failure flag.
- **Cross-source arithmetic (DQ-07).** Any arithmetic across sources (Little's Law with pool_wait_ms, pool sum vs DB sessions) must state its sampling assumption.
- **Ramp-down figures.** Exclude minute 44 from network and payment-latency statements (DQ-01, DQ-02).
- **Negative claims need positive evidence (rule 9; DQ-10).** In particular:
  - "No sandbox throttling" cannot rest on E-10's 0 errors.
  - "The batch ran" or "the batch caused the lock contention" cannot rest on the schedule plus E-17.
  - "The DB is not the cause" can go only as far as E-08's host-level metrics.
  - app1 vs app2 configuration differences are unknown, not absent.
- **Previous run.** Nothing from SYN-RUN-001 may be used.

**Open questions (need data owners)**

1. What does `abort_on_error` do in this tool, and what does `script_errors` count? (harness owner)
2. Did inventory-sync run on 2026-10-08, when, and against which tables? (data team)
3. Are there sandbox-side records for 10:19–10:40 UTC: latency, rate limiting, other tenants? (payment sandbox owner)
4. What is the sampling semantics of each APM and DB metric, and are app1 and app2 configured identically (JVM, heap, GC)? (APM / platform owner)

## Appendix: commands run

All scripts are kept in `/tmp/lib/` (outside `data/`) and run with `python3 -I` against `examples/02-connection-pool/data`. Outputs quoted above come from these runs.

**A1. Fact sheet reproduction**
```bash
cd /home/claude/performance-evidence-lab
python3 tools/analyze.py examples/02-connection-pool/data --md /tmp/facts_check.md
diff <(tail -n +2 /tmp/facts_check.md) <(tail -n +2 examples/02-connection-pool/facts.md) && echo IDENTICAL
```
Output: `IDENTICAL`.

**A2. Timestamps, coverage, consistency and error accounting** (`check1.py`, `check2.py`)
```python
# check1.py: elapsed_min vs timestamp per file; DB offset conversion
start=datetime(2026,10,8,10,0,tzinfo=timezone.utc)
for each UTC file: e=int((ts(r[tcol])-start).total_seconds()//60); count e!=int(r['elapsed_min'])
database: offsets Counter; em=[int((ts(local)-start).total_seconds()//60)]; unique/dups; non-CPU top_wait_event by minute
# check2.py
coverage per (generator,transaction); window_seconds values; count!=passed+failed; duplicate keys
vusers running!=scheduled; exited_with_error total; LG log_level counts; script_errors by minute and total
failed/count per window 0-9, 10-18, 19-39, 40-44, all
app max_threads / db_pool_max values; pool_active>max; threads>max; minutes at pool max / thread max
network negative or zero values; external_calls zero-call rows; payment calls vs checkout count per minute
```
Key outputs:
- 0 elapsed-minute mismatches in all files.
- DB: offset -0400 on 45 rows, maps to minutes 0–44, no duplicates. "idle in transaction" in minutes 20–29 and 34–39; "row lock contention" in minutes 30–33.
- Transactions: minute 44 missing for all 6 generator/transaction series. count = passed + failed in every row.
- vusers: running = scheduled in every row; exited_with_error total 0. log_level "standard" in 45/45 rows for each generator.
- script_errors: LG1 24, LG2 22, only in minutes 19–39.
- Failed/count by window:

  | Window | Failed / count | Error % |
  | --- | --- | --- |
  | 0–9 | 65 / 33,031 | 0.197 |
  | 10–18 | 105 / 53,795 | 0.195 |
  | 19–39 | 677 / 113,631 | 0.596 |
  | 40–44 | 24 / 12,031 | 0.199 |
  | all | 871 / 212,488 | 0.41 |

- Pool at max (20) on both nodes in minutes 20–39. Threads at max (200) on both nodes in minutes 37–39.
- network: minute 44 active_connections -1, throughput 0.0.
- external_calls: minute 44 calls 0, avg 274, p95 408. Payment calls equal checkout count in every minute 0–43 (difference 0).

**A3. Cross-source minute table and DB/pool alignment** (`check3.py`)
```python
db keyed by converted elapsed minute; for minutes 16-22, 25-34, 37-44 print app1/app2 pool active, pool wait,
threads, heap, gc; pool sum; DB sessions, cpu, avg_query, lock_wait, top event; payment avg/p95
diff = db_sessions[m] - (app1_pool[m] + app2_pool[m])  for m in 0..44
lag  = db_sessions[m+1] - (app1_pool[m] + app2_pool[m]) for m in 0..43
```
Key outputs:
- Minute 19: pool 17 + 17 = 34, DB sessions 9. Minute 20: pool 40, DB 40.
- Minute 40: pool 7 + 5 = 12, DB 8.
- Same-minute diff: −1 to −6 in minutes 0–18 and 40–44; −25 at minute 19; 0 in minutes 20–29 and 34–39; +6 in minutes 30–33.
- Lagged diff: −32 at minute 39 → 40, so a fixed one-minute lag does not fit the recovery transition.
- Minutes 30–33: lock_wait 800, 781, 683, 734 ms.

**A4. Trace sampling and arithmetic** (`check4.py`)
```python
traces per minute; missing minutes; node split overall and per window; per-minute node order pattern;
second-of-minute values; trace_id pattern T<mm><i>;
count(held < sql+payment); range of total-pool_wait-held; range of held-sql-payment; minutes with pool_wait>0
```
Output:
- Coverage and sampling:
  - Exactly 3 traces in each of 44 minutes; minute 44 missing.
  - app1 88, app2 44. Per window: 20/10, 18/9, 42/21, 8/4.
  - Node order (app1, app2, app1) in all 44 minutes. Seconds :10, :27, :44 in all 44 minutes.
  - IDs follow T<minute><index>.
- Arithmetic:
  - held < sql + payment: 0 traces.
  - total − pool_wait − held: 81 to 199 ms.
  - held − sql − payment: 8 to 24 ms.
  - pool_wait > 0 only in minutes 19–39.

**A5. Free-text scan, file list, sampling fraction, per-generator error rate** (`check5.py`)
```python
for each CSV: collect (column,value) pairs that are neither numeric nor ISO timestamps (trace_id excluded)
list data/ files and scenario.json source list
checkouts and traces in 10-18 and 19-39; failed/count per generator for 10-18, 19-39, 10-39
```
Output:
- Free-text values: only those listed in §8.
- data/ contains `scenario.json` plus the 8 CSVs listed as sources, and nothing else.
- Checkouts and trace fraction: 13,491 in minutes 10–18 (0.200%) and 28,441 in minutes 19–39 (0.222%).
- Error rate by generator:

  | Generator | 10–18 | 19–39 | 10–39 |
  | --- | --- | --- | --- |
  | LG1 | 0.195% | 0.592% | 0.465% |
  | LG2 | 0.196% | 0.600% | 0.469% |

**A6. Range sanity checks**
```bash
cd examples/02-connection-pool/data && python3 -I -c "...p95<avg in transactions and external_calls; LG cpu/mem max; LB retransmit range..."
```
Output:
- p95 < avg: none in either file.
- LG CPU max 45.9%, memory max 54.0%.
- LB retransmit 0.01–0.04%.
