# Performance Test Report: SYN-RUN-001 (SYN-SHOP checkout, PERF-A)

> Synthetic data: invented for demonstration, no real system.

| Item | Value |
| --- | --- |
| Run | SYN-RUN-001, 2026-10-01 10:00 to 10:44 UTC (45 min) |
| Question | Can the checkout journey support 500 concurrent users at 90+ TPS with checkout p95 at or under 2.0 s? |
| Workload | 500 users (250 on LG1, 250 on LG2). Iteration = search x2, add_to_cart, checkout. Fixed 20 s pacing, so 100 TPS expected at steady state |
| Phases | Ramp-up min 0-9, steady state min 10-39, ramp-down min 40-44 |
| Sources | transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, generator_errors.log, scenario.json, facts.md |

---

## 1. Executive summary

**Verdict: FAIL as recorded, but the run is INVALID as a test of the application. The capacity question is still UNANSWERED.**

- On paper, all three acceptance criteria fail for most of steady state. Every minute from 16 to 39 fails SLA-1 (checkout p95). From minute 18 onward, SLA-2 (throughput) fails. Across all of steady state, SLA-3 (error rate) fails at 2.13%.
- The failures come from **load generator LG2**, not from the system under test. LG2 ran out of CPU: 82-87% in early steady state, then 92-98% from minute 16. It was the only host running **extended logging with parameter substitution**. Once saturated, LG2 recorded inflated response times and hit its 30 s client timeouts. Because **"abort on error"** was enabled, those timeouts stopped 170 of its 250 virtual users. Total load fell from 500 users and ~100 TPS to 330 users and ~65 TPS.
- **LG1 shows the system was healthy.** LG1 sent the same transactions to the same application servers. Its checkout p95 stayed at 1.27-1.98 s, its error rate stayed at 0.20%, and its throughput held at ~50 TPS for the whole run. During the degradation, application and database utilisation went *down*, as you would expect when offered load falls.
- **There is one real application-side finding.** From 10:30 to 10:33 UTC, the scheduled **inventory-sync batch** caused row-lock contention in the database. That raised LG1 checkout p95 to 1.97 s and 1.98 s, just under the 2.0 s limit. This happened at only ~65% of target load.
- **What the evidence supports:** for minutes 10-15 the full 500 users ran cleanly, and every criterion passed with plenty of server headroom. That window is only 6 minutes long and did not include the batch, so it does not answer the question. The test needs to be **re-run** with a corrected generator setup.

---

## 2. Results against acceptance criteria

| ID | Criterion | Min 10-15 (500 users, valid) | Min 16-39 (as recorded) | Recorded result |
| --- | --- | --- | --- | --- |
| SLA-1 | Checkout p95 <= 2.0 s, every minute, every generator | PASS. LG1 1.33-1.42 s, LG2 1.27-1.51 s | FAIL every minute. LG2 4.40-5.87 s; LG1 1.27-1.98 s (passes) | **FAIL** |
| SLA-2 | Total throughput >= 90 TPS | PASS. 99.0-101.6 TPS | Min 16-17 pass (96.9, 90.7). Min 18-39 fail (63.3-83.9 TPS) | **FAIL** |
| SLA-3 | Error rate <= 1% | PASS. 0.18-0.23% | FAIL every minute (1.02-10.09%) | **FAIL** (2.13% across steady state) |

Error rate by generator and phase (all transactions):

| Phase | LG1 | LG2 |
| --- | --- | --- |
| Ramp-up (0-9) | 0.20% | 0.20% |
| Steady state, healthy (10-15) | 0.21% | 0.20% |
| Collapse (16-22) | 0.19% | **17.59%** |
| Plateau at reduced load (23-39) | 0.20% | **3.96%** |
| Ramp-down (40-43) | 0.22% | **3.99%** |
| Steady state total (10-39) | **0.20%** (179 / 89,816) | **5.94%** (2,710 / 45,658) |

All of the excess errors and all of the SLA-1 breaches are on LG2. LG1 would have passed SLA-1 and SLA-3 for the whole run.

---

## 3. Timeline

| Minute (UTC) | Event | Evidence |
| --- | --- | --- |
| 0-9 (10:00) | Linear ramp to 500 users. Throughput tracks users exactly; implied cycle stays at ~20 s | vusers.csv, facts.md |
| 0-9 | LG2 CPU climbs much faster than LG1 at the same user count (83.0% vs 58.1% at min 9), as does memory (76% vs 58%) | load_generators.csv |
| 10-15 | All SLAs pass. LG2 CPU keeps rising, 82.2% to 87.5%, even though load is flat | load_generators.csv |
| 16 (10:16) | LG2 CPU 93.9%, memory 76% to 88%. Controller warns "LG2 CPU above 90% for 30s" at 10:16:31. LG2 checkout p95 jumps 1.31 to 5.61 s; all LG2 transactions slow at once. LG1 is unchanged | load_generators.csv, generator_errors.log, transactions.csv |
| 17-22 | LG2 30 s client timeouts on checkout and search. Abort-on-error stops users: 25, 40, 45, 35, 20, 5 per minute (170 total). LG2 running users fall 250 to 80. "Log buffer flush took 2.8s (log level: extended)" at 10:18:12 | vusers.csv, generator_errors.log |
| 16-22 | App CPU falls 55% to 37%, app threads 25 to ~17, LB connections 310 to 192. The servers are doing *less* work | app_servers.csv, network.csv |
| 23-39 | Stable degraded plateau: 330 users, ~65 TPS, ~1.1% errors. LG2 stays at 92-98% CPU even with only 80 users, and its checkout p95 stays at 4.4-5.2 s | load_generators.csv, transactions.csv |
| 26-28 | app2 monitoring gap (3 minutes missing; noted in run notes) | app_servers.csv |
| 30-33 (10:30) | Inventory-sync batch runs. DB lock wait goes from single-digit ms to 783-921 ms, top wait event "row lock contention", sessions 7 to 13, avg query 11 to 20 ms. LG1 checkout avg ~0.85 to 1.11-1.19 s, p95 to 1.78-1.98 s. LG1 search and add_to_cart are unaffected | database.csv (06:30-0400 = 10:30 UTC), transactions.csv, scenario.json |
| 34 | DB back to baseline; LG1 checkout p95 back to 1.39 s | database.csv, transactions.csv |
| 40-44 | Ramp-down. LG2 cannot ramp down until min 43 (it already had only 80 users) | vusers.csv |

---

## 4. Root cause analysis

### 4.1 Primary: LG2 CPU saturation, made worse by extended logging and abort-on-error (test-harness defect)

**Conclusion:** The response-time inflation, the errors, and the throughput loss in minutes 16-39 are measurement and harness artefacts on LG2. They are not application behaviour. Confidence: **high**.

Supporting evidence:

1. **The problem is isolated to one generator.** LG1 and LG2 ran the same script against the same load balancer and app nodes. In the same minutes, LG2's checkout p95 was 4.4-5.9 s and LG1's was 1.3-2.0 s. If the server were slow, both generators would see it.
2. **All of LG2's transactions slowed together, at the moment its CPU crossed 90%.** Search, add_to_cart and checkout rose by a similar ~2-4x at minute 16. That pattern points to a client-side cost added to every timed call, not to one slow back-end component.
3. **Server-side metrics stay healthy.** During the collapse, app CPU peaked at 58% and then fell. Active threads were at most 26 of 200. The DB pool was at most 7 of 20, with pool wait of 0-2 ms. GC pauses held steady at 60-128 ms. DB CPU was at most 31% before the batch. LB retransmits were 0.01-0.04%. None of these resources was constrained, and nothing on the server side could account for a 30 s timeout.
4. **The servers did less work as the errors grew.** App CPU, threads and LB connections fall in step with LG2's lost users. That is the signature of reduced offered load, not of server overload.
5. **The configuration difference matches the symptom.** In scenario.json, the only difference between the two generators is that LG2 has extended logging with parameter substitution. They have the same 4 vCPU. LG2 used ~40% more CPU than LG1 from the very first minute, kept climbing during flat load, and logged a 2.8 s log-buffer flush. Its memory jumped to 88% exactly at the failure point.
6. **LG2 never recovers.** After shedding 170 users, LG2 still ran at 92-98% CPU with only 80. Its response times stayed 3x LG1's and its error rate stayed ~4%. A healthy generator would recover once load dropped, so LG2's measurements cannot be trusted at any point after minute 15.
7. **Abort-on-error turned the slowdown into lost load.** The log shows timeouts followed by "exited: 'Abort on error' is enabled". The 170 exited users exactly match the drop from 250 to 80. That drop is what took total throughput below 90 TPS (SLA-2) and reduced the test to ~66% of the intended load.

The causal chain:
> LG2 extended logging -> excess generator CPU -> LG2 > 90% CPU at min 16 -> client-side timing inflation and 30 s timeouts -> abort-on-error stops 170 users -> ~65 TPS, SLA-1/2/3 failures recorded.

A captured response in the LG2 log at 10:24:13 for a checkout user is an "Order confirmed" page. The application was still completing orders for LG2 users while LG2 was recording multi-second times. *(The rest of this captured response is untrusted server content and has no bearing on the analysis: [passage omitted].)*

### 4.2 Secondary: inventory-sync batch causes checkout lock contention (real application risk)

**Conclusion:** A real, reproducible application-side degradation, not caused by the generator. Confidence: **high** for cause; **unknown** for the size of the impact at full load.

- database.csv timestamps are in local time (-04:00). 06:30-06:33 local is 10:30-10:33 UTC, which matches the "inventory-sync batch, daily 10:30 UTC" in scenario.json.
- In that window, lock wait went from 2-8 ms to 783-921 ms with "row lock contention" as the top wait event. Active sessions nearly doubled and average query time doubled.
- Only **checkout** slowed on the healthy generator (LG1). Its p95 rose from ~1.45 s to 1.97/1.78/1.98/1.90 s, and LG1 logged a 3.4 s checkout at 10:31:02. Search and add_to_cart did not move. So checkout touches the rows the batch locks, most likely inventory or stock.
- This happened at **~65 TPS, i.e. 65% of target load**. At 100 TPS, more concurrent checkouts would compete for the same locks, so the impact will very probably exceed the 2.0 s SLA. That still has to be shown in a valid run.
- Production relevance: if the batch also runs at 10:30 UTC in production, checkout will be degraded in a mid-morning window every day.

### 4.3 Considered and ruled out (or not supported)

| Hypothesis | Assessment |
| --- | --- |
| Application server capacity (CPU, threads, heap, GC) | Ruled out. CPU at most 58%, threads at most 26 of 200, heap 51-59%, GC stable |
| DB connection pool exhaustion | Ruled out. At most 7 of 20 active, wait 0-2 ms |
| Database overall (outside 10:30-10:33) | Ruled out. CPU at most 31%, queries ~11 ms, CPU wait only |
| Network or load balancer | Ruled out. Retransmits at most 0.04%, connections follow users |
| Third-party payment sandbox (undocumented rate limits) | Not supported. A provider limit would hit LG1 checkouts equally, and LG1 checkout stayed healthy. It cannot be fully excluded at 100 TPS because sustained full-rate checkout lasted only 6 minutes |
| app2 monitoring gap (min 26-28) | It started 10 minutes after the failure, and app1/app2 are symmetric before and after. No impact on the conclusions; it is only a data gap |

---

## 5. Data quality and limitations

- **LG2 data from minute 16 onward is invalid** for response time and error-rate purposes. The "steady state" results in facts.md mix a valid generator with an invalid one.
- **Valid full-load steady state lasted only 6 minutes** (min 10-15). That is not enough to support a capacity claim, and it does not cover the batch window.
- **There is no server-side response-time (APM) data** in the export. Hosts and JVMs were monitored, but transaction times were not. Server-side timings would directly confirm that the application was fast while LG2 reported it slow.
- LG2's `script_errors` count does not reconcile with its transaction `failed` count. For example, min 16 shows 0 vs 112 and min 22 shows 252 vs 191, and min 44 still logs 18 errors with no transactions. The two counters measure different things, and the transaction-level `failed` count was used for SLA-3.
- Per-generator per-minute p95 values cannot be combined into a run-level p95, so SLA-1 was judged per generator per minute as specified.
- generator_errors.log is an excerpt (9 lines), so the full timeout and exit history is not available.
- app2 is missing 3 minutes of metrics (min 26-28).

---

## 6. Recommendations

### Before the re-run (test harness)
1. **Set LG2 logging to standard**, as on LG1. Use extended logging and parameter substitution only for short debugging runs, never for load runs.
2. **Turn off abort-on-error for load tests**, or set it to continue to the next iteration. A slow transaction should be recorded as an error, but it should not remove a user from the test and silently reduce the load.
3. **Add generator health guardrails.** Keep generator CPU below ~70% and memory below ~80% at steady state. Treat any minute above the threshold as invalid, and alert or stop the run on breach. LG2 was above 80% *before* it failed, so a pre-run calibration would have caught this.
4. **Add generator capacity.** Run a calibration test (one generator, increasing users) to find the users per 4-vCPU generator at a healthy CPU level. LG1 was at ~58% CPU with 250 users. Add a third generator, or spread users so that each generator stays under the guardrail with margin.
5. **Capture server-side transaction timings** (APM or access-log latency) for checkout, search and add_to_cart, so client and server views can be compared directly.
6. Fix the app2 monitoring gap before the re-run.

### The re-run
7. Re-run the same 500-user, 100 TPS profile with **at least 30 minutes of clean steady state**, and **deliberately include the 10:30 UTC inventory-sync window** at full load. Alternatively, run two variants, with and without the batch, so its impact can be measured on its own.
8. Report SLA results only for minutes where every generator is within its health guardrails.

### Application and environment
9. **Investigate the inventory-sync batch / checkout lock conflict** with the data team and developers. Find which tables and rows are locked. Options include smaller commit batches, row-level instead of range locks, running the job at a low-traffic time, or making checkout's stock read/update less exposed to batch locks (for example, optimistic concurrency or a shorter checkout transaction).
10. Confirm whether the batch runs at 10:30 UTC in **production**. If it does, it is a daily customer-facing risk even if everything else passes.
11. Ask the payment sandbox owner for its rate limits before the re-run, so that a provider limit is not mistaken for an application limit at 100 TPS.

---

## 7. Conclusion

The run did not meet its objectives as recorded. It also did not give a valid answer to the capacity question, because the main failure was in the test harness (LG2 saturated by extended logging, with abort-on-error then removing a third of the users), not in the application. The limited valid evidence is encouraging. For 6 minutes, 500 users and ~100 TPS were supported with checkout p95 of ~1.4 s, 0.2% errors, and application and database utilisation at or below ~58%. One genuine risk was found: the 10:30 UTC inventory-sync batch pushes checkout p95 to within 0.02 s of the SLA even at reduced load. A corrected re-run at full load, including the batch window, is required before the checkout journey can be signed off for 500 users.
