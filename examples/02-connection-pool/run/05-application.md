```
Agent: Application / APM Specialist
Run: SYN-RUN-002
Read: agents/application-specialist.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, external_calls.csv, checkout_traces.csv); examples/02-connection-pool/facts.md; examples/02-connection-pool/run/01-test-lead-plan.md; examples/02-connection-pool/run/02-evidence.md; examples/02-connection-pool/run/03-validity.md; examples/02-connection-pool/run/04-performance.md
Execution: separate agent context, model Claude Opus 5.5
```

Data note: `scenario.json` marks this dataset as synthetic. It is analysed here as though it were a real run.

**Scope.** VAL-1 is VALID WITH LIMITATIONS (`03-validity.md`). I analyse minutes 19–39 as the application tier's behaviour **under a caller-side payment-latency excursion at 500 users** (AC-5, AC-6). I make no capacity claim (RC-1, RC-2). I do not say the sandbox slowed down, throttled us or was driven by our load (RC-3, RC-4); the claim allowed is "caller-side payment latency rose". I do not order DB signals against app-tier signals at one-minute resolution (RC-9, DQ-06).

Evidence IDs (E-, DQ-, OBS-, SW-) are from `02-evidence.md` and `04-performance.md`. Numbers come from `facts.md` (E-13), earlier run files, or commands AP1–AP6 in the appendix (rule 3). Traces (E-11, E-12) are a fixed-schedule 0.2% sample weighted 2:1 toward app1 (DQ-08); I use them for request composition, not population statistics. APM metric semantics (point-in-time, mean or max per minute) are undocumented (DQ-07); every cross-source calculation below states its assumption.

## 1. Answers to the Test Lead's questions (summary)

| Q | Short answer | Where |
| --- | --- | --- |
| A1 Connection held across payment call? | Yes, in **every one of the 132 sampled traces**, in every window. Hold time is payment time plus 34–81 ms; the non-payment part does not change in the degradation. Population-level arithmetic does not fully close (OBS-APP-06). | OBS-APP-02, OBS-APP-06 |
| A2 Does pool demand explain the queueing? | At the unchanged arrival rate, the new hold time needs about 54 connections against 40 available (minute 19–20); before onset about 8. Qualitatively yes. Quantitatively, observed throughput through the pool exceeds what 40 connections at the measured hold time allow, by up to ~30% in minutes 20–24. | OBS-APP-03, OBS-APP-05, OBS-APP-06 |
| A3 Ordering at onset | **Cannot be ordered in time** from this data: same minute, and the first degraded trace shows both. The trace decomposition gives a **direction of mechanism** (payment → hold → pool), not a time order. | OBS-APP-03, HYP-APP-2 |
| A4 Thread growth; is 200 a second limit? | Up to about minute 28 thread growth is consistent with requests queueing for the pool. From minute 29 threads exceed what the clients have in flight, by up to 158 at minutes 37–39. Reaching 200 is **not shown** to add a limit in the three minutes observed. | OBS-APP-07, HYP-APP-3 |
| A5 app1 heap/GC | app1-specific: app2 carries the same queue (pool, threads, pool wait) with no heap or GC change. Starts after onset. No latency effect visible in the sampled traces. | OBS-APP-08, HYP-APP-4 |
| A6 Payment dependency | Caller-side latency is not related to our call volume (same volumes give both regimes, VAL-1 V2). Pool relief at minute 40 follows the payment-latency drop; the 20% load reduction alone would not have relieved the pool. | OBS-APP-09, OBS-APP-10 |
| A7 Failed transactions | The app tier has **no error data**. Nothing in my layer can say what the 29–37 failures per minute were. | OBS-APP-11 |

## 2. Observations

**OBS-APP-01 — Reference state, minutes 10–18.** (E-06, E-07, E-13; AP2, AP3)
- Pool active 13–15 of 40 across both nodes (6–8 of 20 per node). Pool wait 0–2 ms.
- Active threads 43–50 across both nodes (22–26 of 200 per node).
- App CPU 50.7–54.8%, heap 54.0–61.9%, GC pause 65–134 ms on both nodes (E-13).
- Estimated checkout-only connection demand (checkouts/s × (payment avg + 56 ms)) is 7.1–7.9 connections. The pool is therefore about 35% used, with the other ~6 connections plausibly used by search and add_to_cart (an inference, not measured).
- Traces: payment call is 73.2–87.9% of connection hold; hold minus SQL minus payment is 8–24 ms (AP1).

*Window:* 10–18, both nodes. Observed Fact (the demand figure is a calculation under the stated assumption).

**OBS-APP-02 — The DB connection is held across the payment call in every sampled trace, and only the payment part of the hold changes.** (E-11, E-12; AP1)

| Window | Traces (app1/app2) | Payment share of hold, min–max | Hold − SQL − payment | SQL | Pool wait |
| --- | --- | --- | --- | --- | --- |
| 0–9 | 20 / 10 | 76.1–86.4% | 8–24 ms | 26–58 ms | 0 |
| 10–18 | 18 / 9 | 73.2–87.9% | 8–24 ms | 25–59 ms | 0 |
| 19–23 | 10 / 5 | 95.8–98.3% | 8–23 ms | 25–59 ms | 349–1,018 ms |
| 24–29 | 12 / 6 | 96.1–98.3% | 8–24 ms | 25–57 ms | 924–2,002 ms |
| 30–33 | 8 / 4 | 95.6–97.9% | 9–22 ms | 30–56 ms | 1,361–2,072 ms |
| 34–39 | 12 / 6 | 95.9–98.3% | 8–23 ms | 25–57 ms | 1,240–2,208 ms |
| 40–43 | 8 / 4 | 79.2–87.0% | 8–23 ms | 25–57 ms | 0 |

- Every sampled checkout acquires the connection, runs SQL, and keeps the connection while the payment call runs (hold ≥ SQL + payment in all 132 traces; `02-evidence.md` A4).
- SQL time and the non-payment overhead are unchanged across all windows, including 30–33 (DB lock episode). The rise in hold time from about 0.31 s to about 2.0 s is entirely payment-call time.
- Server-side residual outside the pool and the hold (total − pool wait − hold) is 81–199 ms in every window, so no other server-side wait appears in the sampled checkouts.
- **What the sample cannot show:** whether *every* checkout holds the connection this way (0.2% of checkouts, fixed schedule, app2 only at second :27; DQ-08), and anything about failed checkouts (no status field).

*Window:* 0–43, both nodes. Observed Fact for the sampled requests.

**OBS-APP-03 — Onset, minute 19: hold time jumps with no change in arrival rate, and the new hold time needs more connections than exist.** (E-06, E-07, E-10, E-02, E-03; AP2)

| Signal | Minute 18 | Minute 19 | Minute 20 |
| --- | --- | --- | --- |
| Checkouts per second (load tool) | 25.28 | 25.00 | 25.07 |
| Payment avg (caller-side) | 258 ms | 2,092 ms | 2,093 ms |
| Estimated hold (payment avg + 56 ms) | 0.314 s | 2.148 s | 2.149 s |
| Estimated checkout connection demand | 7.9 | 53.7 | 53.9 |
| Pool active app1 + app2 (max 40) | 14 | 34 | 40 |
| Pool wait app1 / app2 | 0 / 2 ms | 337 / 362 ms | 460 / 437 ms |
| Active threads app1 / app2 | 26 / 23 | 38 / 39 | 49 / 48 |
| App CPU app1 / app2 | 54.7 / 53.4% | 52.6 / 54.3% | 53.3 / 54.6% |
| GC pause app1 / app2 | — | 101 / 130 ms | 94 / 89 ms |

- Both nodes change in the same minute by the same amount. No node-specific pattern (rule 7).
- At minute 19 no app resource is near a limit except the pool: threads are 19–20% of max, CPU is at its reference level, GC is normal.
- The first degraded trace (10:19:10, app1) already shows pool wait 349 ms and payment 2,345 ms (OBS-04). The data cannot place one before the other in time.
- The 56 ms non-payment part of the hold is the median of hold − payment over all 132 traces (range 34–81 ms; AP2).

*Window:* 18–20, both nodes. Observed Fact; the demand row is a calculation assuming every checkout holds a connection for (payment avg + 56 ms).

**OBS-APP-04 — Response-time increases decompose into payment increase plus pool wait.** (E-02, E-03, E-06, E-07, E-10; AP4, AP5)
- **Checkout:** in every minute 19–39, the rise in count-weighted checkout avg over the 10–18 reference (0.855 s) equals the rise in payment avg (over 0.245 s) plus the mean APM pool wait of the two nodes, within −0.17 to +0.21 s. Example, minute 30: +3.54 s = +1.76 s payment + 1.77 s pool wait.
- **add_to_cart:** the rise in avg over reference (0.405 s) equals the mean pool wait within −0.12 to +0.18 s in every minute 19–39.
- **search:** the rise in avg over reference (0.596 s) equals the mean pool wait plus 0.03–0.11 s in 19–25, and plus 0.07–0.34 s in 26–39. Most of the search slowdown is pool wait; a small remainder from minute 26 is unexplained by my data (search runs twice per iteration; whether it acquires more than one connection is unknown).
- These are two independent tools (load-tool client times against APM pool wait and APM outbound latency) agreeing minute by minute. The close fit suggests `db_pool_wait_ms` behaves like a mean wait per acquisition, but that remains an inference (DQ-07).
- Implication: search and add_to_cart, which make no payment call (DQ-11), slowed down because they waited for the same DB connection pool. This answers SW-2's "why do non-payment transactions slow down, and gradually": they track pool wait, which grew gradually (OBS-APP-05).

*Window:* 19–39, all transactions, both generators, both nodes. Correlation (two independent sources, aligned per-minute windows, complete coverage).

**OBS-APP-05 — Escalation then plateau: pool wait grows while demand exceeds the pool, and levels once throughput falls.** (E-06, E-07, E-13; AP2)
- Minutes 20–24: arrival rate still 24.3–25.2 checkouts/s; estimated checkout connection demand 47.2–53.9 against 40. Pool wait rises 0.45 → 1.12 s; threads 49/48 → 81/83.
- Minute 25: TPS 92.2, demand 44.7, pool wait 1.33/1.38 s.
- Minutes 26–39: checkouts 20.95–22.25/s; demand 40.5–47.0; pool wait levels at 1.44–1.82 s; TPS 84.2–88.8.
- This is the pattern of a closed-loop workload behind a saturated pool: the queue grows until iterations run late enough (VAL-1 §2.2) that the arrival rate falls to about what the pool can serve, and then the wait stops growing. Payment avg is flat (1,809–2,123 ms) throughout, so the growth of pool wait in 19–25 is not driven by payment latency increasing.

*Window:* 19–39. Observed Fact for the series; the "closed-loop" reading is an interpretation used in HYP-APP-1.

**OBS-APP-06 — The pool arithmetic does not close exactly.** (E-06, E-07, E-10; AP6)
- Mean concurrent payment calls, by Little's Law (calls × avg_ms / 60 s): 5.7–6.5 in 10–18; 52.3 at 19; **45.9–52.5 in 20–24**; 43.4 at 25; **39.3–45.8 in 26–39**; 5.2 at 40.
- If every payment call ran while holding a DB connection, the pool would need at least that many connections on average. It has 40, and reports 40/40 from minute 20.
- So in minutes 20–24, roughly 6–12 more payment calls were in flight on average than the pool could cover, and checkouts completed at ~1,500/min against an estimated pool-limited ceiling of 1,117–1,242/min (40 / hold). In 26–39 the overshoot is up to about 15–18%.
- Possible reasons, none testable here: (a) not every checkout holds the connection across the payment call (the trace sample is 63/63 in 19–39 but is 0.2% and fixed-schedule); (b) `calls`/`avg_ms` and `db_pool_active` are bucketed or sampled differently (DQ-07, DQ-11); (c) `db_pool_active` is capped at, or sampled below, the true in-use count.
- **Consequence:** the pool can be said to be saturated (Observed Fact: 20/20 on both nodes), and the payment-dominated hold time accounts for that saturation qualitatively. It cannot be said that pool size quantitatively sets the 84–89 TPS level.

*Window:* 19–39. Observed Fact (calculation shown); it limits HYP-APP-1.

**OBS-APP-07 — Threads: consistent with pool queueing until about minute 28, then growing beyond what clients have in flight.** (E-02, E-03, E-06, E-07; AP3)
- Client in-flight requests (Little's Law: Σ count × avg_s / 60 over all transactions, both generators) against app threads (app1 + app2):

| Minutes | Client in-flight | App threads | Threads − client in-flight |
| --- | --- | --- | --- |
| 10–18 | 59.9–62.8 | 44–50 | −17.5 to −10.8 |
| 19–24 | 141.1–215.0 | 77–164 | −64.1 to −47.5 |
| 25–28 | 221.5–248.4 | 192–243 | −29.5 to −5.4 |
| 29–33 | 241.6–248.7 | 255–331 | +13.4 to +86.0 |
| 34–36 | 240.7–242.4 | 354–385 | +111.6 to +143.0 |
| 37–39 | 241.4–246.6 | 400 | +153.4 to +158.6 |
| 40 | 50.2 | 42 | −8.2 |

- In the reference window the app holds fewer threads than the clients have in flight (the difference is network and LB time). Through minute 28 that remains true.
- From minute 29, client in-flight is flat at about 241–249 but threads keep rising by about 5–25 per minute (both nodes combined) until both nodes reach 200 at minute 37.
- Under one-thread-per-request, the server cannot hold more request threads than the clients have requests outstanding. The excess (up to ~158 threads) is not explained by client-visible work. Failed requests cannot account for it: 29–37 failures per minute would each have to keep a thread for about five minutes.
- At 37–39 (both nodes at 200) client in-flight (241.4–246.6), checkout avg and p95 (OBS-09) show no step. Within these three minutes the thread limit is not shown to add latency.
- All threads clear within minute 40 (21/21), the same minute payment latency and pool wait return to reference.

*Window:* 10–40, both nodes. Observed Fact (calculation shown); assumes `active_threads` counts request-serving threads at a comparable instant to the client averages (DQ-07), and that `avg_s` includes all requests (unknown, DQ-10d).

**OBS-APP-08 — app1 heap/GC step at minute 27; app2 unchanged under the same queue.** (E-06, E-07, E-11, E-12; AP1, AP4)
- app1: heap 82.3–86.3%, GC 643–863 ms in every minute 27–39, after 54.4–61.6% and 71–111 ms in 19–26. The level is flat over 27–39, not climbing. At minute 40 heap is 59.6% and GC 79 ms.
- app2 over 27–39: heap 54.1–61.6%, GC 81–127 ms.
- In the same minutes the two nodes carry the same load state: pool 20/20 on both, pool wait within about 150 ms, threads within 5 (OBS-11, AP2).
- app1 CPU is 2.6–8.3 points higher than app2 in every minute 27–39 (50.5–54.7% vs 44.6–49.4%), against −2.1 to +1.8 points in 19–26 (AP4). This is consistent with extra GC work on app1 but is not proven to be GC.
- Sampled traces show no latency effect: residual outside pool and hold is median 131 ms on app1 vs 125 ms on app2 in 27–39 (139.5 vs 164 ms in 10–18). Total trace time by node is similar (OBS-11). Client-side response times cannot be split by node.

*Window:* 19–40, app1 vs app2. Observed Fact.

**OBS-APP-09 — Recovery at minute 40 follows the payment latency, not the load reduction alone.** (E-02, E-03, E-06, E-07, E-10; AP2)
- Minute 40: checkout rate 19.92/s (−20% from minute 39), payment avg 263 ms, pool active 7/5, pool wait 0/2 ms, threads 21/21.
- Counterfactual calculation: at 19.92 checkouts/s with minute 39's hold (2.011 s), checkout connection demand would be 40.0, i.e. the pool would still be saturated. The pool cleared because the hold time fell back to ~0.32 s.
- Whether the payment latency fell *because* our load fell is outside what the data can show (RC-4).

*Window:* 39–40. Observed Fact plus a stated counterfactual calculation.

**OBS-APP-10 — Outbound payment dependency as seen by the app tier.** (E-10; VAL-1 V2)
- 0 errors in every minute. Calls equal checkouts in every minute (DQ-11).
- Caller-side avg 230–258 ms at 1,200–1,525 calls/min (7–18); 1,809–2,123 ms at 1,257–1,511 calls/min (19–39); 248–275 ms at 296–1,195 calls/min (40–43). Latency is not a function of our call volume.
- From minute 20 the number of concurrent payment calls from our side is bounded by the DB pool (each call runs under a held connection, OBS-APP-02), roughly 40, against about 6 at reference (OBS-APP-06). If the provider is sensitive to concurrency rather than rate, our concurrency did rise sharply — but only *after* the latency rose, so it cannot explain the onset (rule 8).
- **Gap (U-2):** there are no outbound HTTP-client metrics (connection pool, connect/TLS time, DNS, queueing). The data cannot say whether the extra ~1.8 s is spent in the network path, in the provider, or in our own outbound client.

*Window:* 7–43. Observed Fact.

**OBS-APP-11 — No application-tier error evidence.** (E-06, E-07, E-10, E-11, E-12)
- Transaction failures are 29–37 per minute in 19–39 (AP4), against about 0.2% earlier (OBS-08).
- The app tier provides no error counts, status codes, pool-acquisition timeouts or logs (DQ-10d, DQ-10e). Traces have no status field. Payment errors are 0.
- The largest sampled pool wait is 2,208 ms (AP1); whether the pool has an acquisition timeout, and whether any failures are pool timeouts, is unknown.

*Window:* 19–39. Observed Fact (of absence of data, not absence of errors; rule 4).

## 3. Hypotheses

### HYP-APP-1 — Connection held across the payment call turns payment latency into DB-pool exhaustion, which spreads the delay to every transaction and, through late iterations, to throughput

- **Claim, split as required:**
  - *Resource exhausted:* the DB connection pool, 20/20 on both nodes from minute 20 to 39, with pool wait 0.34–1.82 s. **Observed Fact.**
  - *Why it was exhausted:* each checkout holds its connection for the duration of the payment call, so when caller-side payment latency rose ~8×, hold time rose from ~0.31 s to ~2.0 s at an unchanged arrival rate, and demand exceeded the 40 available connections. **Probable Contributor.**
  - *Spread:* the pool queue added its wait to search and add_to_cart, which share the pool, and to checkout on top of its own payment delay; the closed-loop workload then ran late, which cut TPS. **Probable Contributor.**
- **Window and scope:** minutes 19–39, both nodes, all transactions.
- **Supporting evidence:**
  - OBS-APP-02: connection held across the payment call in all 132 sampled traces; hold increase is entirely payment time; SQL unchanged.
  - OBS-APP-03: hold time jumps with no change in arrival rate; demand ~54 vs 40 connections; pool is the only app resource at a limit.
  - OBS-APP-04: client response-time increases equal payment increase + pool wait (checkout) and pool wait (add_to_cart, most of search), minute by minute, across two independent tools.
  - OBS-APP-05: pool wait grows while demand exceeds the pool, and levels as TPS falls.
  - OBS-APP-09: the pool clears when hold time falls; the load reduction alone would not have cleared it.
  - Both nodes show the same pattern at the same time (rule 7).
  - DB top wait event "idle in transaction" in 20–29 and 34–39 (`02-evidence.md` §6) fits sessions that sit open while the app does something else. I leave its interpretation to the Database specialist.
- **Contradicting evidence and gaps:**
  - OBS-APP-06: population arithmetic overshoots the 40-connection limit by up to ~30% in 20–24. Either not every checkout holds the connection across the call, or the metrics are not commensurable. This prevents a quantitative claim that pool size sets the throughput level (RC-6 stands).
  - The holding pattern is shown on a 0.2% deterministic sample (DQ-08).
  - Pool and thread metric semantics are undocumented (DQ-07).
  - No controlled change exists in this run, so Confirmed Root Cause is out of reach.
- **Alternatives considered:**
  - *Slower DB work lengthened the hold:* set aside for the hold-time increase. Sampled SQL 25–59 ms in every window and hold − SQL − payment 8–24 ms throughout (OBS-APP-02). The Database specialist owns the wider DB view.
  - *Request-thread exhaustion:* set aside for onset and escalation. Threads 38/39 of 200 at onset, max reached only at 37 (OBS-APP-03, OBS-APP-07).
  - *App CPU or GC:* set aside for onset. CPU at its reference level, GC normal on both nodes at onset; app1's GC starts at 27 and affects one node only (OBS-APP-03, OBS-APP-08; rule 8).
  - *Increase in our load:* set aside. Checkouts 1,517 → 1,500 at onset (OBS-03).
  - *Pool exhausted first and that slowed the payment call:* not supported. The payment span is measured after the connection is acquired, so pool wait is not inside it; no app resource that could slow outbound calls was saturated at minute 19. Not excluded if an unmeasured outbound client limit exists (U-2; HYP-APP-2).
- **Grade:** Probable Contributor (for the amplification mechanism, given the payment-latency rise).
- **Confidence:** Medium. Several independent per-minute signals fit the mechanism closely and every alternative tested against app-tier data fails, but the hold pattern rests on a small fixed sample and the pool arithmetic overshoots (OBS-APP-06).
- **Experiment to confirm or refute** (owner: application team, with the Test Lead for scheduling; depends on VAL-1 T-1 stub):
  1. At 500 users with the current build, inject fixed payment latency with a stub at 250 ms, 1.0 s, 1.5 s and 2.0 s (10 minutes each). **Prediction:** pool reaches 20/20 between about 1.3 s and 1.6 s of payment latency (from OBS-APP-01 and OBS-APP-03: 34–40 connections available to checkout at 25/s), and search/add_to_cart avg rise by about the pool wait. **Refuted if** the pool stays below max at 2.0 s, or search/add_to_cart slow down with no pool wait.
  2. Same steps with a build that releases the DB connection (commits) before the payment call and re-acquires it afterwards if needed. **Prediction:** at 2.0 s payment, pool active stays near reference (well below 20), pool wait ~0, search and add_to_cart at reference, checkout avg ≈ reference + payment increase (~2.6 s), TPS ≈ 100. **Refuted if** the pool still saturates or non-payment transactions still slow.
  3. Instrument per-request connection hold and a sampled-per-request "held during outbound call" flag, so OBS-APP-06 can be resolved: the fraction of checkouts holding across the call should be ~100% if the hypothesis holds as stated.

### HYP-APP-2 — The trigger of the episode is the rise in caller-side payment latency; the pool, threads and other transactions are downstream of it

- **Claim:** the direction of effect at onset is payment latency → connection hold → pool saturation → waits elsewhere. This claim says nothing about *why* caller-side latency rose or where those ~1.8 s were spent.
- **Window:** minutes 18–20 (SW-1).
- **Supporting evidence:** OBS-APP-02 (only the payment part of hold changes); OBS-APP-03 (no app resource near a limit at onset; load unchanged); OBS-APP-05 (payment latency flat while pool wait grows, so the pool does not feed back into payment time); OBS-APP-09 (pool clears with payment latency, not with load).
- **Contradicting evidence and gaps:** time order cannot be established: both signals change in the same minute and the first degraded trace shows both (OBS-04). Where the payment time is spent is unmeasured (U-2): an app-internal outbound cause (HTTP client pool, DNS, TLS, connection reuse) is unlikely given unchanged load and unsaturated resources, but not excluded.
- **Alternatives:** reverse direction (pool first) — no mechanism in the data (HYP-APP-1 alternatives). App-internal outbound limit — would need a change in demand or service time at minute 19 to saturate; demand did not change; cannot be excluded without outbound client metrics.
- **Grade:** Probable Contributor for the direction of effect.
- **Confidence:** Medium. The decomposition is clear, but the onset is not resolvable in time and the outbound path is unobserved.
- **Experiment** (owner: APM/platform owner with the Test Lead): add outbound HTTP-client metrics (pool in use / max, wait, connect and TLS time) and run VAL-1 T-1. **Refuted if** caller-side latency exceeds the stub's served latency, or the outbound client shows queueing at onset (that would make the latency our own).

### HYP-APP-3 — Threads beyond client in-flight work from minute 29 are an unexplained second effect tied to the payment episode

- **Claim:** from minute 29, threads grow by about 5–25 per minute (both nodes combined) beyond the requests clients have in flight, reaching +158 at 37–39, and clear in the same minute payment latency recovers (OBS-APP-07).
- **Candidate mechanisms (none supported above the others):** (a) metric semantics — `active_threads` may be a per-minute maximum or include non-request threads (DQ-07); (b) work not visible to the client, such as asynchronous or background threads per checkout waiting on the payment provider; (c) server work continuing after the client has given up. Candidate (c) is weak: at 29–37 failures per minute each abandoned request would have to keep a thread for about five minutes, while sampled server-side checkouts take ~4 s.
- **Grade:** Observed Fact for the divergence; no mechanism graded.
- **Confidence:** Low for any explanation: the metric definition is unknown and no thread-level data exists.
- **Why it matters:** if the growth is real, the thread pool would become a second limit had the steady state continued; the run shows no effect in the three minutes at 200 (OBS-APP-07, OBS-09).
- **Experiment** (owner: APM/platform owner): document `active_threads` semantics; in the rerun take thread dumps every minute during any degradation and classify threads by state and stack (pool acquisition, outbound HTTP, other). **Refuted (as a real excess)** if dumps show request threads ≈ client in-flight.

### HYP-APP-4 — app1's heap/GC change is node-specific, not a general consequence of the queue

- **Claim:** the same queue on app2 produced no heap or GC change (OBS-APP-08), so queued work alone is not sufficient to cause it. Some app1-specific factor (smaller heap or different GC settings, or node-specific state) is involved.
- **Contradicting evidence and gaps:** app1 vs app2 JVM configuration is unknown (DQ-10f); the heap returned to normal at minute 40, so the extra occupancy was released when the queue cleared, which fits "queue-held objects on a node with less headroom" as well as "different GC behaviour". A monotonic leak is less likely: the level is flat over 27–39 and clears at 40.
- **Effect on the symptom:** none visible. Starts 8 minutes after onset (rule 8); sampled trace residuals and totals similar on both nodes; pool wait and threads match across nodes.
- **Grade:** Correlation (node comparison over aligned, covered windows).
- **Confidence:** Medium for "node-specific"; Low for any specific cause.
- **Experiment** (owner: platform owner): compare JVM arguments, heap size and GC configuration of app1 and app2; enable GC logs in the rerun. **Refuted** if the configurations are identical and app2 shows the same change under the same queue depth in a rerun.

## 4. Ruled out (application tier)

| Ruled out | Scope | Evidence | Confidence |
| --- | --- | --- | --- |
| App CPU saturation as a cause of onset or of the degradation | 19–39, both nodes | CPU 52.6/54.3% at onset, ≤ 54.8% throughout, below reference in 26–39 on app2 (OBS-APP-03, E-13, OBS-12) | High |
| Request-thread exhaustion as the cause of onset or escalation | 19–36 | Threads 38/39 of 200 at onset; max reached only at 37 (OBS-APP-03, OBS-APP-07) | High |
| GC pauses as the cause of onset | 18–26 | GC 71–130 ms on both nodes, as in reference; app1 change starts at 27 (OBS-APP-08) | High |
| A node-specific cause of onset | 18–20 | Both nodes change in the same minute by the same amount (OBS-APP-03) | High |
| Longer SQL in checkout as the source of the longer connection hold | 0–43, sampled checkouts | SQL 25–59 ms and hold − SQL − payment 8–24 ms in every window (OBS-APP-02). Applies to sampled checkout SQL only; the DB layer itself is for the Database specialist | Medium (sample) |
| An increase in our request rate at onset | 18–19 | Checkouts 25.28 → 25.00/s (OBS-APP-03) | High |

**Not ruled out:** an app-internal origin of the payment latency (outbound client, DNS, TLS, connection reuse) — no outbound-client data (U-2). Zero payment errors is not evidence of no throttling (rule 9, RC-3).

## 5. Questions for other specialists

- **Database specialist:**
  - Does the DB evidence agree that checkout SQL did not slow (trace SQL 25–59 ms throughout)?
  - Does "idle in transaction" in 20–29 and 34–39 (`02-evidence.md` §6) correspond to sessions held open in a transaction across the payment call? If so it corroborates HYP-APP-1 from an independent source, over multi-minute windows (DQ-06).
  - In 30–33, DB sessions are 46 against a pool sum of 40: are the 6 extra sessions from another client (for example the batch)? Neither pool wait nor sampled checkout SQL changes in those minutes (OBS-10, OBS-APP-02), and search's small unexplained remainder (OBS-APP-04) is not specific to 30–33.
- **Infrastructure specialist:**
  - app1 vs app2 JVM/heap/GC configuration (HYP-APP-4).
  - Any host or network evidence on the egress path to the payment sandbox (DNS, TLS, NAT, proxy) for 10:19–10:40 UTC (HYP-APP-2, U-2).
  - Is `active_threads` request threads only, and is it a sample, mean or maximum per minute (HYP-APP-3, DQ-07)?
- **APM/platform owner (via Test Lead):** semantics of `db_pool_active`, `db_pool_wait_ms` and `active_threads`; whether the pool has an acquisition timeout; whether outbound HTTP-client metrics and app error counts exist for this run (OBS-APP-06, OBS-APP-11).

## Handoff

- **Main application-tier result:** the DB connection pool is the exhausted resource (Observed Fact). Its exhaustion, and the slowdown of search and add_to_cart, are accounted for by connections held across the payment call while caller-side payment latency was ~2 s (HYP-APP-1, Probable Contributor, Medium). Checkout's increase equals payment increase plus pool wait, and the other transactions' increase equals pool wait, minute by minute (OBS-APP-04).
- **Direction, not time order:** the data supports payment latency → hold → pool, not the reverse (HYP-APP-2, Probable Contributor, Medium), but cannot order them in time, and cannot say where the payment time was spent (U-2). Nothing here licenses "the sandbox caused it" (RC-3).
- **Limits the next agents must carry:** the pool arithmetic overshoots by up to ~30% in 20–24 (OBS-APP-06), so pool size cannot be presented as the quantitative throughput ceiling (RC-6). Thread growth from minute 29 exceeds client in-flight work and is unexplained (HYP-APP-3).
- **Secondary:** app1 heap/GC from minute 27 is node-specific, after onset, with no visible latency effect (HYP-APP-4). Not a contributor to onset (rule 8).
- **For the Test Lead:** the most useful rerun is the stub latency-injection test with and without releasing the connection before the payment call (HYP-APP-1 experiment), plus outbound-client and thread instrumentation (HYP-APP-2, HYP-APP-3). That is the controlled change that could move HYP-APP-1 toward Confirmed Root Cause.
- **Open:** OBS-APP-06 reconciliation; HYP-APP-3 explanation; failure types (OBS-APP-11); questions in §5.

## Appendix: commands run

Scripts are in `/tmp/app/`, outside `data/`, run with `python3 -I` and the data folder as argument (`/home/claude/performance-evidence-lab/examples/02-connection-pool/data`). AP6 was run from inside `data/` with `python3 -I -c`.

**AP1. Trace composition by window and node** (`/tmp/app/a1.py`)
```python
R=list(csv.DictReader(open(D+'/checkout_traces.csv')))
W=[(0,9),(10,18),(19,23),(24,29),(30,33),(34,39),(40,43)]
for a,b in W:
  for n in ('app1','app2','both'):
    s=[traces in window (and node)]
    share=[100*payment_call_ms/db_connection_held_ms]; ov=[held-sql-payment]
    res=[total-pool_wait-held]; sq=[sql]; pw=[pool_wait]
    print(a,b,n,len(s),min/max share, min/max ov, median/min/max res, min/max sql, min/max pw)
for (a,b) in [(10,18),(19,26),(27,39)], node: median/min/max of res
```
Key outputs: the table in OBS-APP-02. Residual (total − pool wait − hold) median app1/app2: 139.5/164 (10–18), 156.5/112.5 (19–26), 131/125 (27–39). Max sampled pool wait 2,208 ms (app1, 34–39).

**AP2. Pool demand per minute** (`/tmp/app/a2.py`)
```python
nonpay=[held-payment for all traces]; NP=median(nonpay)        # 56 ms (range 34-81)
for m in 8..43:
  c = checkout count LG1+LG2; pay = external_calls avg_ms; hold=(pay+NP)/1000
  demand = c/60*hold; pool = app1+app2 db_pool_active; cap = 40/hold*60
  print m, c/60, pay, hold, demand, pool, cap, c, pool wait a1/a2, threads a1/a2
```
Key outputs: demand 6.8–7.9 (8–18); 53.7 (19); 47.2–53.9 (20–24); 44.7 (25); 40.5–47.0 (26–39); 6.4 (40). Cap 1,117–1,242 checkouts/min in 20–24 against observed 1,456–1,511. Minute 40: 19.92 checkouts/s; 19.92 × 2.011 s (minute 39 hold) = 40.0.

**AP3. Client in-flight vs app threads** (`/tmp/app/a3.py`)
```python
for m in 8..43:
  L = sum(count*avg_s for both generators, all transactions)/60
  th = app1+app2 active_threads
  print m, TPS, L, th, th-L, search/add_to_cart avg minus reference, pool wait, checkout avg
```
Key outputs: the table in OBS-APP-07.

**AP4. Checkout decomposition and node comparison** (`/tmp/app/a4.py`)
```python
ref checkout avg = count-weighted avg_s over 10-18, both generators   # 0.855 s
ref payment avg  = mean external_calls avg_ms over 10-18               # 0.245 s
for m in 19..40:
  dC = weighted checkout avg(m) - ref; dP = payment avg(m) - ref; pw = mean(app1,app2 pool wait)/1000
  print m, dC, dP, pw, dP+pw, dC-dP-pw, heap a1/a2, gc a1/a2, cpu a1/a2, failed per minute
```
Key outputs: dC − dP − pw between −0.17 and +0.21 s in every minute 19–39; app1 heap 82.3–86.3% and GC 643–863 ms in 27–39; app1 − app2 CPU +2.6 to +8.3 points in 27–39, −2.1 to +1.8 in 19–26; failures 29–37 per minute in 19–39.

**AP5. search and add_to_cart increase vs pool wait**
```bash
cd .../data && python3 -I -c "
w(ms,t) = count-weighted avg_s over minutes ms, both generators
for t in (search, add_to_cart): r0=w(10..18,t); for m in 19..39: w([m],t)-r0-mean(pool wait a1,a2)/1000"
```
Output: search reference 0.596 s, remainder +0.03 to +0.34 s (+0.03 to +0.11 in 19–25); add_to_cart reference 0.405 s, remainder −0.12 to +0.18 s.

**AP6. Payment-call concurrency vs pool**
```bash
cd .../data && python3 -I -c "
conc(m)=calls*avg_ms/60000; pool=app1+app2 db_pool_active
for windows (10,18),(19,19),(20,24),(25,25),(26,39),(40,40): print min/max conc, min/max pool"
```
Output: 5.7–6.5 / 13–15 (10–18); 52.3 / 34 (19); 45.9–52.5 / 40 (20–24); 43.4 / 40 (25); 39.3–45.8 / 40 (26–39); 5.2 / 12 (40).
