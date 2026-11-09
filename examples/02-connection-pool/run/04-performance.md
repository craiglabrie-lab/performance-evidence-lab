```
Agent: Performance Analyst
Run: SYN-RUN-002
Read: agents/performance-analyst.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, external_calls.csv, checkout_traces.csv); examples/02-connection-pool/facts.md; examples/02-connection-pool/run/01-test-lead-plan.md; examples/02-connection-pool/run/02-evidence.md; examples/02-connection-pool/run/03-validity.md
Execution: separate agent context, model Claude Opus 5.5
```

Data note: `scenario.json` marks this dataset as synthetic. It is analysed here as though it were a real run.

**Scope.** VAL-1 is VALID WITH LIMITATIONS (`03-validity.md`). Within it I describe the system's behaviour in PERF-A during this run, including minutes 19–39 as behaviour under a caller-side payment-latency excursion at 500 users (AC-5, AC-6). I do not give a capacity verdict (RC-1, RC-2), I do not say the sandbox caused or throttled anything (RC-3, RC-4), and I do not order DB against app-tier signals at one-minute resolution (RC-9, DQ-06). This file measures and describes. It proposes no causes; where a pattern points somewhere, it says where to look.

Evidence IDs (E-, DQ-) are from `02-evidence.md`. Numbers come from `facts.md` (E-13), the earlier run files, or commands P1–P4 in the appendix (rule 3). Percentiles are per generator per minute, summarised as median and maximum, never averaged (rule 5).

## 1. Phases from the data

| Phase | Minutes | How the data marks it | Evidence |
| --- | --- | --- | --- |
| Ramp-up | 0–9 | Running users +25 per generator per minute, 500 reached at minute 9. Response times already at reference level (checkout p95 per minute: LG1 median/max 1.37/1.46 s, LG2 1.42/1.47 s) | E-04, E-13 |
| Stable steady state (reference) | 10–18 | 500 running, TPS 98.7–100.5, all three transactions flat | E-02, E-03, E-04, E-14 |
| Onset | 19 | Step change in checkout response time, errors, payment latency, pool use and threads, all in one minute, on both generators and both nodes | OBS-03, OBS-04 |
| Degradation, escalating | 19–25 | Pool at max from minute 20, pool wait and threads climbing, search and add_to_cart worsening each minute; TPS holds until 23, then falls (97.7 at 24, 92.2 at 25) | OBS-05, OBS-06, OBS-07 |
| Degradation, throughput plateau | 26–39 | TPS 84.2–88.8, response times level, but threads still climbing until they reach the 200 max at 37–39 | OBS-07, OBS-09 |
| Recovery | 40 | All symptoms return to reference level within one minute, in the same minute ramp-down starts (400 users) | OBS-13 |
| Ramp-down | 40–43 (44 has no load) | Users −50 per generator per minute; minute 44 has 0 users and no transaction rows (DQ-03) | E-04 |

The declared steady state (10–39) is therefore two regimes: 9 clean minutes and 21 degraded minutes. The degraded regime had not settled when the steady state ended (threads reached their max at minute 37; VAL-1 §2.7).

## 2. Observations

**OBS-01 — Workload delivered as scheduled.** Running = scheduled on both generators in every minute; 250 + 250 users in minutes 9–39; 0 exits. Ramp-down minutes 40–43; minute 44 has 0 users. *Window:* 0–44, LG1 and LG2. *Evidence:* E-04, E-13, DQ-03. Observed Fact.

**OBS-02 — Reference window, minutes 10–18.** Per-minute p95, median/max (P2):

| Transaction | LG1 | LG2 |
| --- | --- | --- |
| search | 0.99 / 1.06 s | 0.97 / 1.08 s |
| add_to_cart | 0.67 / 0.71 s | 0.66 / 0.72 s |
| checkout | 1.42 / 1.51 s | 1.40 / 1.54 s |

TPS 98.7–100.5 per minute; error rate 105 / 53,795 = 0.195%. Payment-sandbox avg 230–258 ms; pool wait 0–2 ms; pool active 6–8 of 20; active threads 22–26 of 200 on each node. *Evidence:* E-14, E-02, E-03, E-06, E-07, E-10, E-13; P2, P3. Observed Fact.

**OBS-03 — Onset is minute 19, for every transaction on both generators.** Taking onset as the first minute whose p95 exceeds that series' maximum in minutes 10–18, onset is minute 19 for all six generator/transaction series (P2). Minute 18 → minute 19, same sources:

| Signal | Minute 18 | Minute 19 | Evidence |
| --- | --- | --- | --- |
| checkout p95 LG1 / LG2 | 1.46 / 1.40 s | 4.96 / 4.93 s | E-02, E-03 |
| search p95 LG1 / LG2 | 1.05 / 0.95 s | 1.59 / 1.58 s | E-02, E-03 |
| add_to_cart p95 LG1 / LG2 | 0.67 / 0.66 s | 1.14 / 1.28 s | E-02, E-03 |
| error rate (all transactions) | 0.18% | 0.59% | E-13 |
| TPS | 100.0 | 98.9 | E-13 |
| payment calls / avg / p95 | 1517 / 258 / 378 ms | 1500 / 2092 / 2957 ms | E-10 |
| pool active app1 / app2 | 7 / 7 | 17 / 17 | E-06, E-07 |
| pool wait app1 / app2 | 0 / 2 ms | 337 / 362 ms | E-06, E-07 |
| active threads app1 / app2 | 26 / 23 | 38 / 39 | E-06, E-07 |
| app CPU app1 / app2 | 54.7 / 53.4% | 52.6 / 54.3% | E-06, E-07 |
| LG CPU LG1 / LG2 | 44.2 / 42.6% | 43.9 / 42.2% | E-05 |

DB active sessions are 9 at minute 19 and 40 at minute 20; per DQ-06 this one-minute difference is not used for ordering. Our load did not rise into the onset (TPS 100.0 → 98.9; checkouts 1517 → 1500). *Window:* 18–19, both generators, both nodes. *Evidence:* as tabled; P1, P3. Observed Fact.

**OBS-04 — Sub-minute onset bracket from the trace sample.** Last normal sampled trace: 10:18:44 (app1; pool wait 0, payment 258 ms, held 313 ms). First degraded: 10:19:10 (app1; pool wait 349, payment 2345, held 2417, total 2899 ms). The first app2 trace of minute 19 (10:19:27) is also degraded (pool wait 410, payment 2413 ms). The first degraded trace already shows both pool wait and a long payment call; the sample cannot order the two. Minute 19's per-minute values (payment avg 2092 ms, checkout p95 ~4.9 s) are already at the level of minutes 20–23, which suggests the change happened at or near the start of minute 19. *Window:* 10:18:44–10:19:27. *Evidence:* E-11, E-12, DQ-08; P4. Observed Fact for the sampled requests; the 26-second bracket is only as fine as a 3-per-minute fixed-schedule sample allows.

**OBS-05 — Breadth: all three transactions degrade, with different shapes.** Per-minute p95 median/max by sub-window (P2):

| Window | checkout LG1 / LG2 | search LG1 / LG2 | add_to_cart LG1 / LG2 |
| --- | --- | --- | --- |
| 10–18 | 1.42/1.51 · 1.40/1.54 | 0.99/1.06 · 0.97/1.08 | 0.67/0.71 · 0.66/0.72 |
| 19–23 | 5.07/5.80 · 5.08/5.74 | 2.26/2.57 · 2.30/2.48 | 1.83/2.18 · 1.75/2.15 |
| 24–25 | 6.28/6.35 · 6.31/6.32 | 3.17/3.22 · 3.19/3.37 | 2.68/2.82 · 2.58/2.88 |
| 26–29 | 7.01/7.64 · 7.25/7.42 | 3.98/4.23 · 4.08/4.31 | 3.34/3.73 · 3.40/3.74 |
| 30–33 | 6.85/7.39 · 7.04/7.33 | 4.39/4.50 · 4.16/4.47 | 3.51/3.56 · 3.76/3.82 |
| 34–36 | 7.20/7.24 · 7.05/7.19 | 4.05/4.48 · 3.93/4.18 | 3.70/3.79 · 3.51/3.74 |
| 37–39 | 6.90/7.17 · 7.31/7.64 | 4.17/4.37 · 3.95/4.12 | 3.35/3.61 · 3.46/3.79 |
| 40–43 | 1.35/1.44 · 1.43/1.54 | 0.99/1.03 · 0.99/1.04 | 0.67/0.71 · 0.67/0.72 |

- **checkout** steps up by about 3.5 s in one minute (minute 19), then climbs further to about 7 s by minute 27 and stays there.
- **search** and **add_to_cart** rise gradually: modest at minute 19 (search 1.59/1.58 s, add_to_cart 1.14/1.28 s), crossing 2.0 s at minute 21 (search) and minute 23 (add_to_cart), and levelling at about 4 s and 3.5 s from minute 26 (P1, P2).
- Count-weighted avg_s follows the same pattern: search 0.60 s (10–18) → 1.29–1.31 s (19–23) → 2.40–2.58 s (26–39); checkout 0.85–0.86 s → 3.20–3.23 s → 4.15–4.34 s (P2).
- The payment dependency's call count equals the checkout count in every minute (DQ-11). No source shows search or add_to_cart calling it.

*Window:* 10–43, all transactions, both generators. *Evidence:* E-02, E-03, E-14, E-15; P1, P2. Observed Fact. **Where to look:** a slowdown that reaches transactions with no payment call, and grows over minutes rather than stepping, points the specialists at resources shared by all transactions on the app nodes (request threads, DB pool), not only at the checkout code path.

**OBS-06 — Inside the degradation, pool wait and threads keep growing while payment latency does not.** (P3, P4)
- Pool active is 20/20 (the max) on both nodes in every minute 20–39.
- Pool wait (APM, app1 / app2): 337 / 362 ms (19) → 1,103 / 1,137 (24) → 1,438–1,702 (26–29) → 1,645–1,820 (30–33) → 1,598–1,806 (34–39).
- Active threads: 38 / 39 (19) → 99 / 106 (26) → 200 / 200 (37–39).
- Payment avg is flat at 1,809–2,123 ms across 19–39; payment p95 2,723–3,323 ms per minute (E-10).
- Traces show the same split. Median pool wait by window (app1 / app2): 653.5 / 528 ms (19–23), 1,446 / 1,613 (24–29), 1,651 / 1,907.5 (30–33), 1,851 / 1,590 (34–39). Median payment call stays at 1,657–2,318 ms and SQL at 34–45 ms (range 25–59 ms in every window, unchanged from 10–18).
- Trace connection-hold medians follow payment-call medians (e.g. 19–23 app1 2,050 vs payment 2,001 ms), as the Results Librarian's arithmetic check also shows (held − sql − payment = 8–24 ms in all 132 traces, `02-evidence.md` A4).

*Window:* 19–39, app1 and app2. *Evidence:* E-06, E-07, E-10, E-11, E-12, DQ-07, DQ-08; P3, P4. Observed Fact (the trace values describe sampled requests only). APM pool-wait semantics (mean, max or total per minute) are undocumented (DQ-07), so APM and trace pool wait are compared as trends, not as equal quantities.

**OBS-07 — Throughput.** (E-13, P2, P3)
- TPS 98.9–101.1 in minutes 19–23, 97.7 at 24, 92.2 at 25, then 84.2–88.8 in 26–39. The first minute below 90 is 26.
- Per generator: 48.9–51.0 TPS in 10–24, 41.9–44.5 in 26–39; the two generators move together (E-13).
- Implied cycle: 20.0 s at reference; 20.6 s (24), 21.8 s (25), 22.5–23.9 s (26–39). Users remain at 500 (OBS-01), so the shortfall is iterations running late (VAL-1 §2.2).
- Window-level throughput (P2): 99.6 TPS (10–18), 100.0 (19–23), 94.9 (24–25), 87.0 (26–29), 85.7 (30–33), 85.7 (34–36), 85.4 (37–39). Over the whole declared steady state 10–39: 167,426 transactions / 1,800 s = 93.0 TPS.
- LB: active connections 305–314 throughout 19–39; LB throughput 41.2–42.7 Mb/s in 19–24 and 35.2–36.9 Mb/s in 26–39, falling with TPS (E-09).

*Window:* 10–39. Observed Fact.

**OBS-08 — Errors step up at onset and then stay flat.** (P2)
- By window: 0.195% (10–18), 0.583% (19–23), 0.588% (24–25), 0.613% (26–29), 0.603% (30–33), 0.584% (34–36), 0.605% (37–39), 0.199% (40–43).
- Per transaction in each degraded sub-window, both generators: 0.49–0.73%. All three transactions are affected about equally.
- Per minute: 0.54–0.67% in 19–39; maximum 0.67% at minute 27 (E-13).
- The rate rises in the same minute as response times (19) and does not keep growing as pool wait and threads grow (OBS-06).
- **Failure type cannot be separated.** The load tool records no reason (DQ-10d). Client timeouts are not declared. Payment-sandbox errors are 0 in every minute (E-10). LG script_errors are 0–2 per minute, only in 19–39, and do not reconcile with transaction failures (DQ-05).

*Window:* 10–43, all transactions, both generators. *Evidence:* E-02, E-03, E-05, E-10, E-13. Observed Fact.

**OBS-09 — The 26–39 plateau: response times level, threads still rising.** Checkout p95 per minute is 6.46–7.64 s on both generators across 26–39 with no trend; search 3.68–4.50 s. Threads rise from 99/106 to 200/200 over the same minutes. When threads reach 200 (37–39), checkout p95 median/max is LG1 6.90/7.17, LG2 7.31/7.64, compared with 7.20/7.24 and 7.05/7.19 in 34–36; TPS 85.2–85.8. No step at SLA level is visible when the thread max is reached, but there are only three minutes at the max before ramp-down. *Window:* 26–39. *Evidence:* E-02, E-03, E-06, E-07, E-13; P1–P3. Observed Fact.

**OBS-10 — Minutes 30–33: DB lock episode inside the degradation.** (P3)
- DB: top_wait_event "row lock contention"; lock_wait 683–800 ms (2–8 ms in every other minute of 19–39); DB CPU 42.2–44.5% (23.5–28.7% elsewhere in 19–39); avg_query 19.2–20.2 ms (10.1–12.3 ms elsewhere); sessions 46 (40 elsewhere in 20–39).
- Client and app side in the same minutes, compared with neighbours:

| Signal | 26–29 | 30–33 | 34–36/39 |
| --- | --- | --- | --- |
| checkout p95 median LG1 / LG2 | 7.01 / 7.25 s | 6.85 / 7.04 s | 7.20 / 7.05 s (34–36) |
| TPS per minute | 85.1–88.8 | 84.2–86.9 | 85.4–85.8 (34–36) |
| APM pool wait, both nodes | 1,438–1,702 ms | 1,645–1,820 ms | 1,598–1,806 ms (34–39) |
| trace SQL time | 25–57 ms | 30–56 ms | 25–57 ms (34–39) |

- There is no visible SLA-level difference in 30–33. Whether the inventory-sync batch ran is unknown (DQ-10b), and the episode starts 11 minutes after onset (rule 8).

*Window:* 26–39, DB host and both nodes. *Evidence:* E-08, E-17, E-06, E-07, E-11, E-12, E-13. Observed Fact.

**OBS-11 — app1 heap and GC diverge from minute 27; app2 does not.** (P3)
- app1 heap is 82.3–86.3% and GC pause 643–863 ms in every minute 27–39; in 19–26 they were 54.4–61.6% and 71–111 ms.
- app2 over 27–39: heap 54.1–61.6%, GC 81–127 ms.
- Over the same minutes, app1 and app2 pool active (20/20), pool wait (within about 150 ms of each other each minute) and threads (within 5 of each other each minute) match.
- Trace totals by node are similar: 34–39 median 3,932 ms on app1 vs 3,615 ms on app2, on a 2:1 sample (DQ-08).
- Generator results cannot be split by node, so no client-side response time per node exists.
- The divergence starts 8 minutes after onset.

*Window:* 19–39, app1 vs app2. *Evidence:* E-06, E-07, E-11, E-12. Observed Fact.

**OBS-12 — No saturated host resource is visible.** (E-05, E-06, E-07, E-08, P3)
- App CPU is 52.6/54.3% at onset. In 26–39 it is 47.5–54.7% on app1 and 44.6–49.4% on app2, below reference.
- DB CPU stays at or below 28.7% outside 30–33.
- LG CPU stays at or below 45.9% and memory at or below 54.0%.
- LB retransmits are 0.01–0.04%.

The configured limits that are reached are the DB pool (20/20, from minute 20) and request threads (200/200, minutes 37–39). *Window:* 0–43. Observed Fact.

**OBS-13 — Recovery is complete within minute 40, the first ramp-down minute.** (P1, P3, P4)
- Minute 40, with 400 users:
  - Checkout p95 1.38 / 1.36 s; search 0.94 / 0.99 s; add_to_cart 0.65 / 0.65 s; error rate 0.19%.
  - Payment avg 263 ms, p95 373 ms.
  - Pool wait 0 / 2 ms; pool active 7 / 5; threads 21 / 21, down from 200 / 200 at minute 39.
  - DB sessions 8; app1 heap 59.6%, GC 79 ms.
- Traces bracket the change between 10:39:44 (app1, pool wait 1,839, payment 2,271 ms) and 10:40:10 (app1, pool wait 0, payment 251 ms).
- Minutes 40–43 match the 10–18 reference (checkout p95 median/max LG1 1.35/1.44, LG2 1.43/1.54 s), with no residual symptom on any source.
- Recovery coincides with the first reduction in load, so the data cannot say whether load reduction or something independent ended the episode (RC-4). All post-recovery measurements are at 400 users or fewer, so they say nothing about 500 users after recovery.

*Window:* 39–43. *Evidence:* E-02, E-03, E-04, E-06, E-07, E-08, E-10, E-11, E-12, E-16. Observed Fact.

## 3. Health table

Scope for every row: SYN-RUN-002 in PERF-A, declared steady state minutes 10–39, under VAL-1 VALID WITH LIMITATIONS.

| Criterion | Verdict | Measured | Scope and limits | Evidence |
| --- | --- | --- | --- | --- |
| SLA-1 checkout p95 ≤ 2.0 s, each steady-state minute, each generator | **FAIL** | Met in 9/9 minutes 10–18 on both generators (1.32–1.54 s). Failed in 21/21 minutes 19–39 on both generators (4.76–7.64 s; LG1 median/max 6.65/7.64, LG2 6.85/7.64). Smallest failing margin 2.76 s | Per minute, per generator; no run-level p95 (rule 5). Failed-request inclusion in p95 is unknown (DQ-10d), but it cannot change the outcome at these margins (VAL-1 §2.5). Confidence High | E-14, E-15, E-13; OBS-02, OBS-05 |
| SLA-2 total throughput ≥ 90 TPS, steady state | **FAIL** | Per minute: ≥ 90 in 10–25 (92.2–101.1), < 90 in all 14 minutes 26–39 (84.2–88.8). Whole-window mean over 10–39: 93.0 TPS | The verdict reads "steady state" as sustained throughput in each steady-state minute, as `facts.md` and VAL-1 (AC-3) do. The criterion does not state its aggregation. As a 30-minute mean it would be 93.0 ≥ 90, so the **Test Lead should confirm the reading**. The shortfall is late iterations with all 500 users present, not a harness artefact (VAL-1 §2.2). The 84–89 TPS level is not a stable capacity figure (RC-6). Confidence High for the per-minute measurements; the verdict depends on the stated reading | E-13, E-04, E-05; OBS-07 |
| SLA-3 error rate ≤ 1%, steady state | **PASS** (as counted by the load tool) | 782 / 167,426 = 0.467% over 10–39; per-minute max 0.67% (minute 27); 0.195% in 10–18, 0.58–0.61% per sub-window in 19–39 | What counts as a failure, abort_on_error behaviour and client timeouts are undocumented (DQ-04, DQ-10d). Confidence Medium | E-02, E-03, E-13; OBS-08 |
| Question as asked: support 500 users at ≥ 90 TPS with checkout p95 ≤ 2.0 s (capacity) | **NOT ASSESSED** | See SLA-1..3 above as observations | VAL-1 excludes a capacity verdict in either direction (RC-1, RC-2): onset came without any change in our load and coincided with a caller-side latency rise on a shared sandbox (OBS-03), and only 9 clean minutes exist | VAL-1 §3.2, §3.4 |

## 4. Symptom windows

| ID | Window | Scope | What it shows | Questions for the specialists | Reference window |
| --- | --- | --- | --- | --- | --- |
| **SW-1** | Minutes 18–20; trace bracket 10:18:44–10:19:27 | Both nodes, all transactions, payment dependency | The onset: every symptom changes in one minute with no change in load (OBS-03, OBS-04) | Can anything in the app tier order payment latency against pool exhaustion at onset? Is there any app-side signal (outbound HTTP client, connection setup to the sandbox) that shows where the extra ~1.8 s of caller-side payment time is spent (VAL-1 U-2)? If the data cannot answer, say so. | 10–18 |
| **SW-2** | Minutes 19–25 | Both nodes; search, add_to_cart, checkout | Escalation: pool at max from 20, pool wait and threads climbing, search and add_to_cart worsening each minute while payment latency is flat (OBS-05, OBS-06) | Why do transactions with no payment call slow down, and gradually rather than in a step? What do the thread and pool series say about where requests are waiting? Does the measured connection-hold time, with the checkout rate, account for the pool at 20/20 (Test Lead A2)? | 10–18 |
| **SW-3** | Minutes 26–39, with 37–39 (threads at 200) as a sub-window | Both nodes, both generators | Throughput below 90 TPS; response times level while threads still climb to the max (OBS-07, OBS-09) | Is the plateau an equilibrium or still moving? Does reaching 200 threads add a second limit? Why does pool wait level at about 1.6–1.8 s while threads keep rising? | 19–25 and 10–18 |
| **SW-4** | Minutes 30–33 | DB host; both nodes | Row lock contention, DB CPU and query time up, sessions 46; no SLA-level change visible (OBS-10) | What held the locks, and did it touch checkout data? Did inventory-sync run (DQ-10b)? Does anything below SLA level change in these minutes? Report as an overlay on the degradation, not part of onset (rule 8). | 26–29 and 34–37 |
| **SW-5** | Minutes 27–39 | app1 vs app2 | app1 heap 82–86% and GC 643–863 ms; app2 unchanged; pool, threads and trace times match across nodes (OBS-11) | Is this app1-specific (configuration, JVM) or a consequence of queued work on app1? Does it change app1's request handling in any measurable way? Starts after onset. | app1 19–26; app2 27–39 |
| **SW-6** | Minutes 39–41; trace bracket 10:39:44–10:40:10 | All sources | Full recovery in one minute, coinciding with the first ramp-down step (OBS-13) | Does anything show whether recovery followed the drop in our load or happened independently? How did 200 queued threads clear within one minute? | 10–18 |
| **SW-7** | Minutes 19–39 | All transactions, both generators | Failures step from 0.2% to about 0.6% at onset, then stay flat, spread evenly across transactions (OBS-08) | Which failures are client timeouts, server errors or script/data failures (DQ-10d, VAL-1 U-4)? Why does the rate not grow as waits grow? | 10–18 (0.195% baseline) |

## Handoff

- **Look first at SW-1 and SW-2 (application specialist).**
  - The onset is a single-minute, all-source change at minute 19 with flat load (OBS-03).
  - What follows is not one step. Payment latency is flat at ~2 s from minute 19, but pool wait, threads and non-checkout response times keep growing for 6–18 minutes (OBS-05, OBS-06).
  - That divergence, and the slowdown of search and add_to_cart, which have no payment call, are the most specific patterns in the data. They point at what all transactions share on the app nodes (request threads, DB pool, connection hold time; Test Lead A1–A4).
  - Trace SQL time is unchanged throughout (25–59 ms), and connection hold follows payment-call time.
- **Then SW-3** for the throughput plateau and the thread max, and **SW-7** for the failure mix, which needs data the run does not have (DQ-10d).
- **SW-4 and SW-5 are secondary.** Both start well after onset (minutes 30 and 27) and show no SLA-level difference from their neighbours (OBS-10, OBS-11). They may still matter as separate problems, but they cannot explain onset (rule 8).
- **Database specialist:** use multi-minute windows only (DQ-06). DB sessions equal the pool sum (40) in 20–29 and 34–39, with "idle in transaction" as the top event (`02-evidence.md` §6).
- **Infrastructure specialist:** OBS-12 gives the host-resource picture. No host resource is saturated; the limits reached are configured pool and thread maxima.
- **Test Lead:** confirm the reading of SLA-2's "steady state" scope (per minute vs whole-window mean, 93.0 TPS). Health verdicts as in §3; capacity NOT ASSESSED, per VAL-1.
- **Not done here:** no cause is proposed, no run-level p95 is given, and no data from SYN-RUN-001 is used.

## Appendix: commands run

Scripts are in `/tmp/pa/`, outside `data/`, run with `python3 -I` and the data folder passed as an argument: `python3 -I /tmp/pa/pN.py /home/claude/performance-evidence-lab/examples/02-connection-pool/data`.

**P1. Per-minute p95 and checkout avg per transaction and generator, failures per transaction (minutes 8–43)**
```python
import csv,sys
D=sys.argv[1]
T={}
for r in csv.DictReader(open(D+'/transactions.csv')):
    T[(int(r['elapsed_min']),r['generator'],r['transaction'])]=r
for m in range(8,44):
    row=[]
    for t in ('search','add_to_cart','checkout'):
        row.append('%s/%s'%(T[(m,'LG1',t)]['p95_s'],T[(m,'LG2',t)]['p95_s']))
    row.append('%s/%s'%(T[(m,'LG1','checkout')]['avg_s'],T[(m,'LG2','checkout')]['avg_s']))
    f=[sum(int(T[(m,g,t)]['failed']) for g in ('LG1','LG2')) for t in ('search','add_to_cart','checkout')]
    print(m,'|',' | '.join(row),'|',f)
```
Key outputs: minute 18 → 19 checkout p95 1.46/1.40 → 4.96/4.93, search 1.05/0.95 → 1.59/1.58, add_to_cart 0.67/0.66 → 1.14/1.28; minute 39 → 40 checkout 7.17/6.85 → 1.38/1.36. Failures per minute (search/add/checkout, both generators) 5–7 / 2–4 / 2–4 in 10–18 and 14–19 / 6–9 / 7–10 in 19–39.

**P2. Sub-window p95 median/max, weighted avg, error rates, TPS; onset per series**
```python
import csv,sys,statistics as st
D=sys.argv[1]
T={}
for r in csv.DictReader(open(D+'/transactions.csv')):
    T[(int(r['elapsed_min']),r['generator'],r['transaction'])]=r
W=[(10,18),(19,23),(24,25),(26,29),(30,33),(34,36),(37,39),(40,43)]
for a,b in W:
    ms=range(a,b+1)
    for t in ('search','add_to_cart','checkout'):
        for g in ('LG1','LG2'):
            p=[float(T[(m,g,t)]['p95_s']) for m in ms]
            c=sum(int(T[(m,g,t)]['count']) for m in ms); f=sum(int(T[(m,g,t)]['failed']) for m in ms)
            w=sum(int(T[(m,g,t)]['count'])*float(T[(m,g,t)]['avg_s']) for m in ms)/c
            print(a,b,g,t,st.median(p),max(p),min(p),round(w,2),f,c,100*f/c)
    # window totals: failed/count, per-minute TPS min/max, count/(60*minutes)
# steady state 10-39: failed, count, %, count/1800 ; max per-minute error %
# onset: first minute in 10-39 with p95 > max p95 of 10-18, and first minute with p95 > 2.0, per txn/gen
```
(The elided lines are the window and steady-state totals and the onset loop, computed from the same `T` dictionary as shown in the printed labels.)

Key outputs: the window tables in OBS-02, OBS-05, OBS-07 and OBS-08. Steady state 10–39: 782 / 167,426 = 0.467%, 93.0 TPS; max per-minute error 0.67% at minute 27. Onset (first minute above the 10–18 max) = 19 for all six series; first minute above 2.0 s: checkout 19, search 21, add_to_cart 23, on both generators.

**P3. Per-minute cross-source table, minutes 16–44**
```python
import csv,sys
from datetime import datetime,timezone
D=sys.argv[1]
A={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open(D+'/app_servers.csv'))}
X={int(r['elapsed_min']):r for r in csv.DictReader(open(D+'/external_calls.csv'))}
N={int(r['elapsed_min']):r for r in csv.DictReader(open(D+'/network.csv'))}
L={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open(D+'/load_generators.csv'))}
s=datetime(2026,10,8,10,tzinfo=timezone.utc); B={}
for r in csv.DictReader(open(D+'/database.csv')):
    B[int((datetime.strptime(r['window_start_local'],'%Y-%m-%dT%H:%M:%S%z')-s).total_seconds()//60)]=r
for m in range(16,45):
    # prints payment calls/avg/p95/errors; app1/app2 threads, pool active, pool wait, heap, gc, cpu;
    # DB sessions, cpu, avg_query, lock_wait, top_wait_event; LB connections, Mb/s; LG cpu and script_errors
```
Key outputs: the per-minute values in OBS-03, OBS-06, OBS-07, OBS-09 to OBS-13 (for example threads 99/106 at 26 and 200/200 at 37–39; app1 heap 82.3–86.3% and GC 643–863 ms in 27–39; DB lock_wait 800/781/683/734 ms in 30–33; LB 35.2–36.9 Mb/s in 26–39).

**P4. Traces at transitions and per-window per-node medians and ranges**
```python
import csv,sys,statistics as st
D=sys.argv[1]
R=list(csv.DictReader(open(D+'/checkout_traces.csv')))
for r in R:
    if int(r['elapsed_min']) in (17,18,19,20,21,38,39,40,41):
        print(r['timestamp_utc'][11:],r['node'],r['total_ms'],r['pool_wait_ms'],r['sql_ms'],r['payment_call_ms'],r['db_connection_held_ms'])
W=[(10,18),(19,23),(24,29),(30,33),(34,39),(40,43)]
for a,b in W:
    for n in ('app1','app2'):
        s=[r for r in R if a<=int(r['elapsed_min'])<=b and r['node']==n]
        f=lambda k:(st.median(int(r[k]) for r in s),min(int(r[k]) for r in s),max(int(r[k]) for r in s))
        print(a,b,n,len(s),f('total_ms'),f('pool_wait_ms'),f('payment_call_ms'),f('db_connection_held_ms'),f('sql_ms'))
```
Key outputs: the transition traces in OBS-04 and OBS-13; per-window medians in OBS-06 (pool wait app1/app2 653.5/528 in 19–23, 1,446/1,613 in 24–29, 1,651/1,907.5 in 30–33, 1,851/1,590 in 34–39; SQL 25–59 ms in every window).
