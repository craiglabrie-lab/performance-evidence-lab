# Performance Test Report — SYN-RUN-002 (SYN-SHOP checkout, PERF-A)

> Synthetic data for demonstration. No real system, company or test.

| Item | Value |
| --- | --- |
| Run | SYN-RUN-002 (rerun of SYN-RUN-001 after the LG2 log level was set to standard; no application or DB changes) |
| Date / window | 2026-10-08, 10:00–10:44 UTC (45 min) |
| Workload | 500 Vusers (250 per generator), ramp-up min 0–9, steady state min 10–39, ramp-down min 40–44 |
| Iteration | search x2, add_to_cart x1, checkout x1; fixed pacing 20 s; think time 3 s; expected 100 TPS |
| Environment | 2 app nodes (200 threads, DB pool 20 per node), 1 DB, lb1, third-party payment **sandbox** (shared, rate limits undocumented) |
| Question | Can checkout support 500 concurrent users at 90+ TPS with checkout p95 at or under 2.0 s? |

---

## 1. Verdict

**FAIL. The objective was not met.** The run does not show that checkout can sustain 500 users at the target service level.

| Criterion | Threshold | Result | Detail |
| --- | --- | --- | --- |
| SLA-1 checkout p95, each steady-state minute, each generator | <= 2.0 s | **FAIL** (21 of 30 minutes) | Passed min 10–18 (1.32–1.54 s). Failed every minute from min 19 to 39 (4.76–7.64 s, both generators). |
| SLA-2 total throughput, steady state | >= 90 TPS | **FAIL** (14 of 30 minutes) | ~100 TPS in min 10–24, then fell to 84–89 TPS from min 26 to 39. |
| SLA-3 transaction error rate, steady state | <= 1% | PASS | 0.47% overall. About 0.2% in min 10–18 and about 0.6% from min 19. |

For the first 9 steady-state minutes (min 10–18) the system met every criterion with room to spare: checkout p95 about 1.4 s, about 100 TPS, about 0.2% errors, app CPU about 53%, DB pool 7 of 20, DB CPU about 28%. At **10:19 UTC (min 19)** it degraded suddenly, while the load was unchanged. It stayed degraded until ramp-down and was getting worse when steady state ended.

---

## 2. What happened (timeline)

| Min (UTC) | Event | Evidence |
| --- | --- | --- |
| 0–9 | Clean ramp to 500 users. | TPS tracked the schedule linearly (9.9 to 99.3). Implied cycle about 20 s, which matches the pacing. |
| 10–18 | Healthy steady state. | Checkout p95 1.32–1.54 s. Payment-sandbox avg about 245 ms (p95 about 330–385 ms). Pool active 6–8 of 20 with 0–2 ms wait. |
| **19** | **Payment sandbox latency jumps about 8x in one minute** | Avg 258 ms to 2,092 ms, p95 378 ms to 2,957 ms. Call volume unchanged (1,517 to 1,500 per minute). Zero payment errors. |
| 19 | DB pool saturates on both nodes right away | Pool active 17 of 20, then 20 of 20 from min 20. Pool wait 337/362 ms (app1/app2), rising to about 1.7–1.8 s. |
| 20 | DB sessions jump 9 to 40 (= 2 nodes x 20), and the top wait event changes from `CPU` to **`idle in transaction`** | database.csv, timestamps 06:20-0400 = 10:20 UTC. |
| 19–39 | Every transaction slows, including those that never call payment | search avg 0.6 s to 2.5 s; add_to_cart 0.4 s to 2.1 s; checkout 0.85 s to 4.3 s. |
| 19–39 | App threads pile up and grow without levelling off | active_threads 38 to 200 (= max_threads) on **both** nodes by min 37. |
| 24–26 | Iterations overrun the 20 s pacing, so throughput drops | Implied cycle 20.6 s, then 21.8 s, then 22.5 s (later 23–24 s). TPS falls below 90 at min 26. |
| 27–39 | app1 only: heap 83–86% and GC pause 650–860 ms per minute | app2 stays at about 55–61% heap and about 100 ms GC. |
| 30–33 | inventory-sync batch (scheduled 10:30 UTC) causes row-lock contention in the DB | lock_wait 683–800 ms, DB CPU about 43%, avg query 19–20 ms, sessions 46. |
| 40 | Ramp-down starts. **Everything recovers within the same minute.** | Payment avg 263 ms, pool 7 of 20 with 0 wait, threads 21, checkout p95 1.35–1.54 s. |

---

## 3. Root cause analysis

### 3.1 Trigger: payment-sandbox latency stepped from ~250 ms to ~2 s

- The slowdown at min 19 came from the outbound payment call. Sampled checkout traces show the payment call going from a median of 253 ms (min 10–18) to 1,970 ms (min 19–39). Over the same period SQL time stayed flat (median 42 ms before, 41 ms after), and DB avg query time stayed at about 10–12 ms apart from the batch window.
- **The step was not caused by our load increasing.** The payment call rate was about 25 per second for the 10 minutes before min 19 with normal latency, and it did not change at min 19. The shape (an abrupt step to a flat plateau of about 1.8–2.1 s with zero errors) looks like throttling, or an event in the shared sandbox, more than gradual saturation.
- **This alone is enough to fail SLA-1.** At min 19, pool wait was still only about 350 ms, yet checkout p95 was already 4.9 s. A dependency whose own p95 is about 3 s cannot sit inside a 2.0 s checkout p95 budget. Even an unlimited connection pool would not have saved SLA-1 in this window.
- The cause on the sandbox side cannot be determined from this data. Latency recovered at min 40, when the call rate fell to about 20 per second. That could mean a rate threshold near 20–21 per second once some burst allowance runs out. But latency did *not* recover in min 26–39 at about 21–22 per second, and a single recovery that coincides with ramp-down is not proof. The sandbox is shared, and its rate limits are not documented.

### 3.2 Amplifier (the real application defect): a DB connection is held open across the payment call

The checkout code path takes a DB connection and keeps a transaction open while it waits for the payment provider.

- **Payment time makes up most of the connection hold time:** 81% when healthy (253 of 313 ms) and **97%** when degraded (1,970 of 2,022 ms) (trace medians).
- **The DB confirms it:** from min 20, 40 sessions (every pooled connection on both nodes) sit in `idle in transaction`. They hold a transaction open but do no DB work. DB CPU stays at about 25–28%.
- **The pool arithmetic (Little's law):** each node handles about 12.5 checkouts per second.
  - Healthy: 12.5/s x 0.31 s ≈ 4 connections for checkout. That fits the observed 7 of 20 once search and add_to_cart are added.
  - Degraded: 12.5/s x 2.0 s ≈ **25 connections for checkout alone, against a pool of 20**. Saturation was unavoidable.
  - When saturated, 2 x 20 connections divided by about 2.0 s of hold time caps checkout at about 20 per second. That is about where it settled (about 21 per second in min 26–39, which fits within the sampling error of 3 traces per minute).
- **The slowdown spreads to every transaction:** search and add_to_cart never call the payment provider, yet they slowed by about 1.7–1.9 s each. That matches the pool wait, so they are queuing behind checkout for the same connections.
- **The queue never stabilised:** active threads climbed steadily from 38 to the 200-thread maximum on both nodes, while median pool wait in checkout traces rose from 737 ms (min 19–24) to 1,836 ms (min 34–39). Had steady state run longer, thread exhaustion would most likely have turned into rejected requests or timeouts, and SLA-3 would have failed too.

**Result:** a slowdown in one external dependency, limited to checkout, became a slowdown across the whole application, because a scarce shared resource (the DB connection) is held for the full duration of a remote call.

### 3.3 Why throughput fell (SLA-2): a side effect, not a separate bottleneck

The test uses closed-loop fixed pacing: each user starts a new iteration every 20 s. Once an iteration (4 responses plus think time) takes longer than 20 s, the next one starts late and the offered load drops. The implied cycle time follows the response times closely:

- Healthy: 2 x 0.6 + 0.4 + 0.85 ≈ 2.5 s of response time per iteration, comfortably inside 20 s.
- From min 24–25, response times total about 8.8 s or more. The implied cycle exceeds 20 s and TPS starts to fall. That fits a 3 s think time after each of the 4 steps (an inference; the script was not reviewed).

The throughput failure is therefore a **direct consequence of the slow responses**. Note one more thing: because the load tool slowed down along with the system, the application received *less* load than intended during the failure. With open-arrival traffic, as in production where customers keep arriving, queues and errors would have been worse than this test shows.

### 3.4 Causes ruled out or ranked secondary

| Candidate | Assessment | Evidence |
| --- | --- | --- |
| Load generators | **Ruled out** | CPU ≤ 46%, memory flat at 54%, both generators behave the same (TPS, p95, errors). No Vusers exited. The LG2 issue from RUN-001 is not present. |
| Network / LB | **Ruled out** | About 309 connections steady, retransmits 0.01–0.04%. Throughput in Mbps dropped only in line with TPS. |
| DB capacity / SQL | **Ruled out as cause** | SQL time flat (about 40 ms). Query avg about 11 ms outside the batch. CPU ≤ 30% outside the batch. |
| App CPU | **Ruled out** | About 45–55% throughout. CPU did not rise when latency did, which points to waiting rather than working. |
| inventory-sync batch (10:30 UTC) | **Present but not causal; still contaminates the run** | It started 11 minutes after degradation began. Checkout p95 and trace SQL time show no visible change in min 30–33. It does add row-lock waits up to 800 ms, so it must not overlap future runs. |
| app1 heap/GC (min 27–39) | **Secondary; investigate** | It started 8 minutes after the problem began, affected only app1, and cleared at ramp-down, so it is not a leak. Trace totals were about the same on app1 and app2 (mean 3.63 s vs 3.56 s), so its effect on response time was small. The asymmetry between nodes is unexplained, and 86% heap leaves little headroom. |

---

## 4. Recommendations

### Priority 1: fix the application design (needed whatever the sandbox outcome)
1. **Release the DB connection before calling the payment provider.** Split checkout into two short transactions: (a) persist the order as `PENDING` and commit, (b) call payment with no connection held, (c) take a connection again to record the result. Alternatively, make the payment step asynchronous (outbox or queue). Expected effect: connection hold drops from about 2 s to about 50–60 ms whatever the provider's latency, and search and add_to_cart stop depending on payment health.
2. **Bound the payment call.** Set a client timeout well inside the checkout SLA budget, add a circuit breaker, and use a dedicated bulkhead (a separate thread or connection limit) for payment calls. A slow provider should then fail or slow down checkout only, not the whole site.
3. **Fail fast on pool acquisition.** Set a connection acquisition timeout far below the current about 1.8 s waits, so threads are not consumed until they reach the 200 maximum.
4. **Do not use a bigger pool as the fix.** At 2 s hold time the target rate needs ≥ 25 connections per node for checkout alone, plus headroom. That moves 50+ idle-in-transaction sessions onto the DB and still leaves SLA-1 failing because of payment latency. At most it is a short-term mitigation.

### Priority 2: make the test environment fit to answer the question
5. **Raise the payment-sandbox behaviour with its owner.** Was there throttling, a rate limit, or an incident between 10:19 and 10:40 UTC on 2026-10-08? Get the documented rate limits. Check whether SYN-RUN-001 shows the same step at a similar point; if it does, a load-related throttle becomes much more likely.
6. **Replace the shared sandbox with a service-virtualised payment stub** for capacity runs, configured to production-like latency (the healthy profile here is about 250 ms avg, about 380 ms p95). Then run a separate **fault-injection test** with the stub at about 2 s latency to prove the fix in recommendation 1 keeps search and add_to_cart unaffected.
7. **Keep the inventory-sync batch (10:30 UTC daily) out of the test window**, or schedule runs around it, and record the decision.

### Priority 3: measurement and harness hygiene
8. **Check the `abort_on_error: true` setting.** Roughly 15–19 transactions failed per minute per generator, yet no Vuser exited. Either these errors do not count for abort, or the setting is not applied.
9. **Capture error types** (timeouts or HTTP codes) by transaction. The data shows that failures roughly tripled (from about 14 to about 31 per minute), but not why. The payment dependency reported zero errors, so the failures are probably timeouts inside the app tier.
10. **Add a pacing-miss / iteration-duration metric**, or use an arrival-rate (open) workload, so a throughput shortfall caused by slow responses is visible directly.
11. **Profile the app1 heap under backlog** (heap histogram during the degraded window) to explain the asymmetry between nodes.
12. **Fix the LB metric export.** active_connections = **-1** at min 44 is an invalid value (it looks like a sentinel or counter reset).

### Re-test exit criteria
- Rerun 500 users with a **full 30-minute steady state** after recommendation 1 is in place, using a payment stub (or a sandbox with confirmed limits) and with no batch overlap. Pass requires SLA-1 to SLA-3 in every minute.
- Run a fault-injection test with payment at about 2 s. Expected outcome: search and add_to_cart p95 stay about the same as in healthy minutes (about 1.0 s and 0.7 s), DB pool usage stays well under 20 per node, and threads do not grow.

---

## 5. Confidence and limitations

- **High confidence:** what happened in what order, that pool exhaustion amplified the problem, and that holding the connection across the payment call is the mechanism. Four independent sources agree: transactions, app pool and thread metrics, DB wait events, and traces.
- **Medium confidence:** the throughput mechanism. It assumes 3 s think time after each step, inferred from implied cycle times; the script was not reviewed.
- **Low confidence / open:** *why* the payment sandbox slowed down (throttle or shared-environment event). The data cannot separate the two.
- Traces are a sample (3 per minute). Medians are robust, but the tails are not well represented.
- p95 values are per generator per minute and were not averaged. No run-level p95 is reported.
- DB metrics come from the DB host in local time (UTC-4) and were converted to UTC. The DB session step shows up 1 minute after the app pool step, which is within the sampling resolution (the app pool was 17 of 20 at min 19, so the onset was partway through that minute).
- SYN-RUN-001 data was not available, so no comparison between runs was made.
