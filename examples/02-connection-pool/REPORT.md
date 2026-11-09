# Performance review report: SYN-RUN-002 (checkout at 500 users, PERF-A)

Run SYN-RUN-002, project SYN-SHOP, environment PERF-A, 2026-10-08 10:00–10:44 UTC. **The data is synthetic** (`scenario.json`: "Invented data for demonstration"). It was reviewed as though it were a real run.

Source of truth for this report: the Test Lead's decision, `run/09-test-lead-decision.md`. Every ID below (E-, DQ-, OBS-, HYP-, CRIT-, AC-, RC-, U-, T-, F-, REC-, DEC-) is the team's own, so each claim can be traced back to its evidence.

## 1. Summary for decision makers

1. **Verdict:** this run cannot tell us whether checkout supports 500 users, either way. In this run, two of the three criteria failed (response time and throughput) and one passed (errors). All three were met for the first 9 minutes, before the payment service's response time rose about 8×.
2. **Validity:** the test is **VALID WITH LIMITATIONS**. It is valid for pass/fail results in this run. It is **not** valid for a capacity verdict at 500 users (VAL-1).
3. **Most important finding:** when payment calls slowed to about 2 s, that delay alone broke the checkout response-time target (F-4, Probable Contributor, High confidence). Our design then spread the delay: each checkout keeps its database connection open during the payment call, so the database connection pools filled. Search, add-to-cart and throughput all suffered (F-6/F-7, Probable Contributor, Medium confidence).
4. **Next action:** ask the payment-sandbox owner for their records (REC-1), add the missing instrumentation (REC-2) and fix the harness and criteria definitions (REC-3). Then rerun with a controlled payment stub, both with and without a fix that releases the connection before the payment call (REC-4, REC-5).
5. **What would change this:** a 30-minute run at a fixed 250 ms payment latency gives a capacity PASS or FAIL (REC-4a). Proof that the extra payment time was spent on our side would make the slowdown our own finding (U-2). No pool saturation at 2.0 s injected latency would refute F-6.

## 2. At a glance

| Judgment | Result | Confidence and limits |
| --- | --- | --- |
| **Test validity** (VAL-1) | VALID WITH LIMITATIONS | Valid for criterion-level health in PERF-A within this run. Not valid for a capacity verdict at 500 users, in either direction (RC-1, RC-2). |
| **Health: SLA-1**, checkout p95 ≤ 2.0 s in each steady-state minute, on each generator | **FAIL** | High. Met in 9/9 minutes 10–18 (1.32–1.54 s). Failed in 21/21 minutes 19–39 (4.76–7.64 s), on both generators. Payment latency alone accounts for the failure (F-4), so it is not attributed to our design. |
| **Health: SLA-2**, throughput ≥ 90 transactions/s in steady state | **FAIL** (per-minute reading, DEC-2) | High for the measurements, Medium for the verdict. Below 90 in all 14 minutes 26–39 (84.2–88.8). The 30-minute mean is **93.0 TPS**, which would pass under a window-mean reading. The criterion owner must decide which reading applies (REC-3). |
| **Health: SLA-3**, error rate ≤ 1% in steady state | **PASS** (as counted by the load tool) | Medium. 0.467% over minutes 10–39; the worst single minute was 0.67%. What counts as a failure is undocumented (DQ-04, DQ-05, DQ-10d). |
| **Health: the question as asked** (capacity at 500 users) | **NOT ASSESSED** | VAL-1 excludes a capacity verdict in both directions (DEC-1). |
| **Grade and confidence of the main finding** | F-4: Probable Contributor, **High**. F-6: Probable Contributor, **Medium**. | Neither is Confirmed Root Cause, because the run made no controlled change. The trigger of the payment-latency rise is ungraded (F-3). |

Terms used in this report:
- **p95:** the response time that 95% of requests beat. It is judged per minute and per generator, and is never averaged across minutes or generators.
- **TPS:** transactions per second.
- **Connection pool:** the fixed set of database connections each app node can use. There are 20 per node, 40 in total.
- **Grades** (from `method/judgments.md`), weakest to strongest: Observed Fact, Correlation, Probable Contributor, Confirmed Root Cause.

## 3. What happened

The load tool ran 500 virtual users (250 on each of two load generators, LG1 and LG2). Each user repeated search ×2, add_to_cart, checkout at a fixed pace of one iteration every 20 s. Ramp-up was minutes 0–9, the declared steady state minutes 10–39, and ramp-down minutes 40–44.

- **Minutes 10–18: healthy.** TPS was 98.7–100.5. Checkout p95 was 1.32–1.54 s on both generators, and the error rate 0.17–0.22%. Payment calls averaged 230–258 ms as seen by our app. Pool use was 6–8 of 20 connections per node (`facts.md`; OBS-02).
- **Minute 19: a step change with no change in our load.** Checkouts per minute went from 1,517 to 1,500. Average payment latency, measured on our side, went from 258 ms to 2,092 ms. In the same minute:
  - checkout p95 jumped to 4.96 s (LG1) and 4.93 s (LG2);
  - pool wait went from 0/2 ms to 337/362 ms on the two app nodes;
  - errors tripled, from about 0.2% to about 0.6%.

  This happened on both generators and both app nodes (OBS-03).
- **Minutes 19–25: escalation.** Both pools sat at 20/20 from minute 20. Pool wait and app threads kept climbing while payment latency stayed flat. Search and add_to_cart, which never call payment, slowed down gradually (OBS-05, OBS-06).
- **Minutes 26–39: throughput plateau, still moving.** TPS was 84.2–88.8. Iterations ran late (implied cycle 22.3–24.0 s against 20 s pacing) with all 500 users present, so this is a system finding, not a harness problem (VAL-1 §2.2). App threads kept rising until both nodes reached their 200 maximum at minutes 37–39, so the regime had not settled (RC-6).
- **Minutes 30–33: a separate database lock episode** inside the degradation, with no measurable effect on the criteria (F-10).
- **Minute 40: full recovery in one minute,** in the same minute that ramp-down began (400 users):
  - payment avg 263 ms;
  - pool wait 0/2 ms;
  - threads 21/21;
  - checkout p95 1.38/1.36 s.

  What ended the episode cannot be determined (F-15).

Over the 30-minute steady state there were 167,426 transactions (93.0 TPS) and 782 failures (0.467%).

## 4. Findings

All findings are scoped to SYN-RUN-002 in PERF-A, under VAL-1. None is a capacity statement.

| ID | Claim | Evidence | Grade | Confidence | Reason |
| --- | --- | --- | --- | --- | --- |
| F-1 | The intended workload was delivered, and the harness did not distort it. 500/500 users ran in every minute 10–39 with 0 exits, the 2 : 1 : 1 mix held, generator CPU was 42.1–45.9%, and both generators logged at "standard". | E-02–E-05; VAL-1 V1, V2; OBS-01 | Observed Fact | High | Coverage is complete and the two generators agree minute by minute. Load-generator memory is **not** used as evidence: it is derived from the user count (CRIT-7, OBS-INF-11). |
| F-2 | SLA-1 was met in minutes 10–18 (1.32–1.54 s) and failed in 19–39 (4.76–7.64 s), on both generators. The smallest failing margin was 2.76 s. | E-13–E-15; OBS-02, OBS-05; TL-1 | Observed Fact | High | Measured per minute and per generator. |
| F-3 | Payment latency, as seen by our app, stepped up at minute 19 and returned at minute 40. Avg was 230–258 ms in minutes 7–18, 1,809–2,123 ms in 19–39 and 263 ms at 40. p95 was 2,723–3,323 ms in 19–39. Payment errors were 0. The step is **not explained by our per-minute call rate**. Whether it depends on our cumulative volume or concurrency is **unknown**. Where the extra ~1.8 s was spent (provider, network path or our own outbound client) is also unknown. | E-10; VAL-1 V2; OBS-03, OBS-APP-10; TL-1 | Observed Fact for the series; trigger ungraded | High for the series; none for the trigger | Measured on our side only. There is no provider-side or outbound-client data (RC-3, RC-4, U-1, U-2). |
| F-4 | At the payment latency seen in minutes 19–39, **SLA-1 fails on payment latency alone, with or without pool wait.** Payment p95 exceeded 2.0 s by at least 0.72 s in all 21 minutes. Each checkout makes one payment call, synchronously. With pool wait removed, checkout avg would still be 2.42–2.73 s. So releasing the connection cannot make SLA-1 pass at about 2 s of payment latency. | E-10, E-02, E-03, E-11, E-12, DQ-11; `02-evidence.md` A4; 08b C1, C2; TL-1, TL-2 | Probable Contributor | High | The margin of at least 0.72 s is far larger than any bucketing or generator-split error. Synchronous containment rests on a 0.2% trace sample, supported by calls = checkouts in every minute. |
| F-5 | The DB connection is held across the payment call in every sampled checkout, and only the payment part of the hold changes. Hold − SQL − payment is 8–24 ms in all 132 traces. SQL is 25–59 ms in every window. The payment share of the hold is 73–88% normally and 96–98% in 19–39. | E-11, E-12, DQ-08; OBS-APP-02, OBS-DB-06 | Observed Fact for the sampled requests | High for the sample | Extending it to all checkouts is an inference from a fixed-schedule 0.2% sample. |
| F-6 | **Holding connections across the payment call exhausted both DB pools and spread the delay to every transaction.** Evidence for this: pools were at 20/20 in minutes 20–39; DB sessions were pinned at exactly 40, mostly "idle in transaction" (connected and inside an open transaction, but not running SQL); and response-time increases match payment increase plus pool wait (checkout) or pool wait alone (add_to_cart, most of search), with a checkout residual of −0.17 to +0.21 s. Checkout demand was **at or above** the 40-connection cap. The estimate overshoots the cap by up to about 30%, so it is not a measured figure. | E-06–E-08, E-10–E-12; OBS-06, OBS-APP-03 to -06, OBS-DB-05 to -07; TL-2 | Probable Contributor (for the amplification, given the latency rise) | Medium | Independent signals converge. However, the hold pattern rests on a small fixed sample, the pool arithmetic does not close, and metric semantics are undocumented (DQ-07, DQ-08). Not shown: that pool size sets the 84–89 TPS level (RC-6). |
| F-7 | SLA-2's shortfall is late iterations with all users present. Pool amplification is the probable reason they ran late. The implied cycle was 22.3–24.0 s against 20 s pacing. Without pool wait, the model gives 16.0–16.3 s per iteration, under the pacing. | E-04, E-13; VAL-1 V1; 08b C2; TL-2 | Observed Fact (late iterations); Probable Contributor (attribution) | High (late iterations); Medium (attribution) | Inherits F-6, and where think time is applied is unverified (T-5). |
| F-8 | The direction of effect is payment latency → connection hold → pool saturation. The trigger is unknown. The payment span is measured after the connection is acquired, and the pool clears with payment latency at minute 40. The traces cannot order the two signals in time. Per-minute averages fit payment latency reaching full level first (CRIT-8, with the DQ-07 caveat). | OBS-04, OBS-APP-02, -03, -05; 08b C3 | Probable Contributor (direction) | Medium | No outbound-client data. The onset is not resolved in time. |
| F-9 | The database is not implicated in the onset, or in minutes 19–29 and 34–39 (a bounded negative). DB avg query time was 10.1–12.3 ms against a 10.1–12.0 ms reference. DB CPU per TPS was 0.285 and 0.290 against 0.282. Lock wait was 2–8 ms and sampled checkout SQL 25–59 ms. | E-08, E-11, E-12; OBS-DB-03, -04, -06 | Observed Facts from two agreeing sources; a bounded negative, not a cause | High for the measurements; Medium for "not implicated at all" | There is no per-statement or per-session DB data. Search and add_to_cart DB time is visible only through the host-wide mean (DQ-10c). |
| F-10 | Minutes 30–33 were a separate DB episode from a client outside the two app pools, with no measurable effect on the criteria. Row lock contention was the top event, lock wait was 683–800 ms, DB CPU 42.2–44.5%, and there were 46 sessions while both pools were pinned at 20. Sampled checkout SQL was 30–56 ms, and checkout p95 and TPS stayed within the range of neighbouring minutes. The link to the 10:30 UTC inventory-sync batch is an **ungraded hypothesis, Low confidence**. | E-08, E-17, E-06, E-07, E-11–E-13; OBS-10, OBS-DB-08, -09 | Observed Fact (the episode and the non-pool client) | Low (batch link) | There is no record that the batch ran (DQ-10b) and no lock-holder data (DQ-10c). The episode starts 11 minutes after onset, so it cannot explain onset. |
| F-11 | Hosts, the load balancer and the inbound network show no stress and no change at onset (a bounded negative). App CPU was at or below 54.8%, DB CPU at or below 44.5%, and retransmits 0.01–0.04%. Load-balancer connections track users and its throughput tracks TPS. | E-06–E-09; OBS-INF-01 to -08 | Observed Fact (bounded) | High | The **outbound path to the sandbox is not monitored**, and this rule-out does not reach it (HYP-INF-2). |
| F-12 | From minute 27, app1 shows a heap, GC and CPU divergence that app2 does not show under the same queue. app1 heap was 82.3–86.3%, GC 643–863 ms, and CPU 2.6–8.3 points above app2. No latency effect is visible. | E-06, E-07, E-11, E-12; OBS-11, OBS-APP-08, OBS-INF-02 | Correlation | Medium ("node-specific"); Low (any cause) | Starts 8 minutes after onset. JVM configuration is unknown (DQ-10f). |
| F-13 | From minute 29, server threads exceed the client-side count of requests in flight, by about +158 at minutes 37–39. | E-02, E-03, E-06, E-07, E-09; OBS-APP-07, OBS-INF-09 | Observed Fact (arithmetic, assuming comparable sampling) | Low (any explanation) | Unexplained (HYP-APP-3). It shows the 26–39 regime had not settled. |
| F-14 | Failures stepped from 0.195% to about 0.6% at onset and then stayed flat. The rise is spread evenly across all three transactions. Payment errors were 0. abort_on_error is set, yet no user exited. | E-02–E-05, E-10; OBS-08; DQ-04, DQ-05, DQ-10d | Observed Fact | High (counts) | What the failures were is unknown (RC-7). |
| F-15 | Recovery at minute 40 coincided with the first ramp-down step. What ended the episode is indeterminate. A model of whether the 20% load cut alone would have cleared the pool gives 40.05 against a cap of 40, from a model known to overshoot (CRIT-5). | E-10, E-06, E-07, E-02, E-03; OBS-13, OBS-APP-09 | Observed Fact (the coincidence) | High (coincidence); none for its cause | RC-4: the data supports neither "our load drove it" nor "it was independent". |

## 5. What we ruled out, and why

| Ruled out | For what | Evidence | Limit of the rule-out |
| --- | --- | --- | --- |
| A harness or generator problem behind the failures | SLA-1, SLA-2 | 500/500 users and 0 exits; generator CPU ≤ 45.9%; both generators identical in TPS, error rate and SLA-1 outcome (F-1; VAL-1 §2.1–2.4) | Error and timeout semantics are undocumented (DQ-04, DQ-10d) |
| An increase in our load at onset | Onset at minute 19 | Checkouts 1,517 → 1,500 (OBS-03) | Dependence on cumulative volume or concurrency is untested (F-3) |
| Slower database work | Onset and minutes 19–29, 34–39 | Flat query time, flat CPU per TPS, low lock wait, flat checkout SQL (F-9) | No per-statement data. Medium confidence for "not implicated at all" |
| Request-thread exhaustion | Onset and escalation | Threads were 38/39 of 200 at onset; the maximum was reached only at minute 37 (OBS-APP-03, OBS-APP-07) | Thread growth after minute 29 is unexplained (F-13) |
| App CPU or GC | Onset | CPU at its reference level and GC normal on both nodes at onset. app1's change starts at minute 27 on one node only (OBS-APP-03, OBS-APP-08) | app1's divergence remains open (F-12) |
| A node-specific cause | Onset | Both nodes changed in the same minute by the same amount (OBS-APP-03) | none |
| Hosts, load balancer, inbound network | Onset and degradation | No stress and no change at onset (F-11) | The outbound path to the sandbox is unmonitored (HYP-INF-2) |
| The inventory-sync batch or the DB lock episode | Onset | Starts 11 minutes after onset (F-10) | Whether the batch ran is unknown (DQ-10b) |
| "Capacity FAIL: the journey does not support 500 users" | The question as asked | Our load did not change at onset. The SLA-1 failure is accounted for by a latency rise whose cause and location are unknown. All three criteria held for 9 minutes (DEC-1). The Devil's Advocate withdrew this reading in 08b. | It becomes possible if U-2 shows the extra time was on our side |
| "Sandbox blip: discount minutes 19–39 and PASS" | The question as asked | Only 9 clean minutes (RC-2). The design sensitivity (F-6) is real whether or not the sandbox represents production (DEC-1). | none |

**Not ruled out:**
- an app-internal origin of the payment latency (outbound client, DNS, TLS);
- a provider-side limit that depends on our load;
- throttling (zero payment errors is not evidence that there was none).

## 6. Recommendations

In priority order. Evidence and test-integrity items come before system changes. **Not recommended:**
- **Increasing the DB pool size as the fix.** It raises concurrent payment calls, DB sessions and thread use, and threads already reached 200/200.
- **Database tuning** (F-9).

| # | Owner | Action | Success measure | Result that would prove it wrong |
| --- | --- | --- | --- | --- |
| REC-1 | Test Lead with the payment-sandbox owner | Request provider-side latency, rate-limit hits, throttling, tenancy and incident records for 2026-10-08 10:15–10:45 UTC (U-1) | Records received covering 10:19–10:40 UTC | Provider-side latency stayed near about 250 ms while our side saw about 2 s. The extra time would then be on our side (U-2), and the onset becomes a system finding. |
| REC-2 | APM/platform owner with the DBA | Add instrumentation:<br>• outbound payment-call phases (outbound pool wait, DNS, connect, TLS, time to first byte) and egress/proxy counters<br>• a per-request "connection held during outbound call" flag and hold duration<br>• random, node-balanced trace sampling<br>• per-statement DB statistics, and 10 s session snapshots with transaction age and client identity<br>• thread dumps every minute during any degradation<br>• documented metric semantics<br>• a run ID in every export | Each item is present in the rerun's evidence register, with its semantics documented | The rerun still raises DQ-06, DQ-07 or DQ-08-type issues for these signals |
| REC-3 | Harness owner (abort_on_error, failure reasons); test designer (think-time placement); checkout product owner (SLA-2 aggregation) | Document abort_on_error and set it to the intended behaviour. Record a reason code per failure, and declare client timeouts. Declare where think time is applied. State whether SLA-2 is judged per minute or as a window mean. | Exits, transaction failures and script_errors reconcile, and every failure has a reason. The scenario file states think-time placement and SLA-2 aggregation. | Failures without reasons, or exits that do not match the setting |
| REC-4 | Test Lead with the environment owner. The application team and DBA analyse the results. | Replace the shared sandbox with a service-virtualisation stub (a test double with a fixed, declared latency). Then run:<br>**(a)** a 30-minute steady state at a fixed 250 ms;<br>**(b)** stepped injection of ≥ 10 minutes each at 250 ms, 1.0 s, 1.5 s and 2.0 s.<br>At every step, report SLA-1 per minute and per generator, SLA-2, pool active and wait, threads, search and add_to_cart avg, and DB session state. Keep inventory-sync out of the window. | Stub logs confirm the latency served, and caller-side latency stays within a declared tolerance of it. (a) gives an unambiguous SLA-1/2/3 result. (b) gives the payment-latency budget at which SLA-1 first fails. Model-derived prediction (wide): the pool saturates between about 1.0 s and 2.0 s. | **HYP-APP-1 wrong:** the pool stays below its maximum at 2.0 s, or search and add_to_cart slow down with no pool wait. **Latency is our own (U-2):** caller-side latency exceeds what the stub served. |
| REC-5 | Application team | Build that commits and releases the DB connection before the payment call and re-acquires it afterwards only if needed. Repeat the REC-4(b) steps. | At 2.0 s injected latency:<br>• pool well below 20 per node, pool wait about 0;<br>• idle-in-transaction sessions near reference;<br>• search and add_to_cart at their 10–18 levels;<br>• TPS ≥ 90;<br>• checkout avg about reference plus injected latency.<br>SLA-1 is **not** expected to pass at 2.0 s (F-4). | The pool still saturates, or non-payment transactions still slow down, with the fix in place |
| REC-6 | Checkout product owner with the payment-integration architect | Using REC-4(b), set the payment-latency budget that keeps checkout p95 ≤ 2.0 s. Define a client timeout and a circuit breaker or fallback for the payment call. Decide whether SLA-1 should be conditional on dependency latency. | Budget, timeout and breaker are documented. In a REC-4 step above the timeout, checkout fails fast and the other transactions are unaffected. | Above the budget, pool wait or non-payment latency still rises, or checkout waits past the timeout |
| REC-7 (secondary; fallback) | Test Lead with the sandbox owner. Not part of the capacity test. | Only if REC-1 yields no records, and only with the sandbox owner's consent: hold about 25 calls/s against the real sandbox for more than 40 minutes. During any episode, step the rate down and back up, and log cumulative and concurrent calls. | Shows whether latency follows rate, concurrency, or cumulative count (onset recurring near about 21,750 calls) | Episodes do not follow rate, concurrency or cumulative volume. **Limit:** we cannot see other tenants, so a null result does not exclude a provider-side limit. |
| REC-8 (secondary) | Data team with the DBA | Schedule capacity tests away from 10:30 UTC. Separately, run the batch in a declared window during a fixed-latency stub test, capturing the batch log and lock holder/waiter snapshots. | The extra sessions and lock waits belong to the batch, and checkout SQL and p95 stay within the no-batch range | Lock waiters include checkout statements, or checkout SQL or p95 rises. Or the contention appears without the batch. |
| REC-9 (secondary) | Platform owner | Compare app1 and app2 JVM arguments, heap size, GC algorithm and instance type. Enable GC logs in the rerun. | A configuration difference or GC log accounts for app1's delta | Configurations are identical, and app2 shows the same change at the same queue depth |

## 7. Limitations and open questions

**Limitations of this run:**
- Only 9 clean steady-state minutes (10–18), against 30 declared.
- The payment dependency is a shared third-party sandbox with undocumented rate limits and no provider-side data (DQ-10a).
- Payment latency is measured only on our side, and the outbound path is unmonitored (U-2, HYP-INF-2).
- Checkout traces are a fixed-schedule ~0.2% sample, weighted 2:1 toward app1 (DQ-08).
- APM and DB metric semantics are undocumented (DQ-07). DB-versus-app ordering at one-minute resolution is unreliable (DQ-06).
- Failure reasons, abort_on_error behaviour and client timeouts are undocumented (DQ-04, DQ-05, DQ-10d).
- Nothing from the previous run, SYN-RUN-001, was used. The `run_notes` claim of "no application or database changes" is unverified.

**Open questions:**
- U-1, U-2: what triggered the payment-latency rise, and whether any of the ~1.8 s was spent on our side.
- Whether the latency depends on our cumulative volume or concurrency (CRIT-9).
- Whether every checkout holds its connection across the call, given that the pool arithmetic overshoots (OBS-APP-06).
- Why threads outgrew client work (F-13).
- What the failures were (F-14).
- Whether inventory-sync ran.
- How app1 is configured.
- What `active_threads` measures.
- Whether 500 users can sustain 30 minutes under normal dependency latency.

**Unresolved dissent and points not fully settled** (from `09-test-lead-decision.md` §6):
1. **SLA-2 aggregation (CRIT-3, DEC-2).** The Test Lead chose the per-minute reading (FAIL). The contrast in `scenario.json` is a fair argument for a window mean (93.0 TPS, PASS): SLA-1 is scoped "each steady-state minute", while SLA-2 says only "steady state". Only the criterion owner can settle this. If a window mean is declared, SLA-2 becomes PASS for this run, and the report must still state that every minute from 26 to 39 was below 90.
2. **CRIT-9, partly accepted.** The Devil's Advocate asked for a load-dependence test against the real sandbox. It was made conditional on REC-1 and on the owner's consent. If the owner refuses and has no records, the question stays open with no planned way to close it.
3. **Does every checkout hold its connection?** The application, database and infrastructure specialists all flag a demand overshoot of up to about 30%. "Not every checkout holds the connection" and "the metrics are not commensurable" are both still possible. This caps F-6 at Medium.
4. **Direction payment → pool (CRIT-8).** The Devil's Advocate's independent read (08a) called it "well supported". The application specialist and the Test Lead keep it at Probable Contributor, Medium, because the outbound path is unobserved. The minute-level support from CRIT-8 is recorded but does not raise the grade.
5. **Recovery at ramp-down (F-15).** The Devil's Advocate rates this as the best clue for telling an external incident from a load-dependent limit. The team keeps it open. It remains the single most informative unexplained coincidence in the run.
6. **Thread growth beyond client work (F-13).** Unexplained. The candidate causes (metric semantics, server work after client abandonment, background threads) remain open.

## 8. How this review was produced

**Execution mode.**
- Each agent ran in a **separate Claude Code subagent context**, on model **Claude Opus 5.5**. The agents were dispatched in the order of the numbered files.
- The three specialists (05, 06, 07) ran **in parallel**.
- The Devil's Advocate's first call (08a) ran **in parallel with steps 3–5**: validity, performance analysis and the specialists. It therefore had not seen the team's analysis.
- All agents run on the same model. So the Devil's Advocate is a separate pass, not an independent reviewer (08a, 08b).
- **File-access limits were instructions given to each agent, not a sandbox.** Each file's header lists what that agent was told it read.
- **The data is synthetic.**

| Step | Agent | File produced |
| --- | --- | --- |
| 1 | Test Lead (Call 1: plan) | `run/01-test-lead-plan.md` |
| 2 | Results Librarian | `run/02-evidence.md` |
| 3 | Test Validity Reviewer | `run/03-validity.md` |
| 4 | Performance Analyst | `run/04-performance.md` |
| 5 | Application / APM Specialist (in parallel) | `run/05-application.md` |
| 5 | Database Specialist (in parallel) | `run/06-database.md` |
| 5 | Infrastructure & Network Specialist (in parallel) | `run/07-infrastructure.md` |
| 3–5 (in parallel) | Devil's Advocate (Call 1: independent read) | `run/08a-independent-read.md` |
| 6 | Devil's Advocate (Call 2: challenge) | `run/08b-challenge.md` |
| 7 | Test Lead (Call 2: decide) | `run/09-test-lead-decision.md` |
| 8 | Report Writer | `REPORT.md` (this file) |

The fact sheet `facts.md` was generated deterministically by `tools/analyze.py`, with no model involved. The Results Librarian reproduced it exactly (02-evidence A1).

**Report Writer inputs.** The role file; `method/judgments.md`; `method/records.md`; `data/scenario.json`; `facts.md`; and every file in `run/`. One check command was run over `data/`, from `examples/02-connection-pool/data`:

```bash
python3 -I -c "
import csv
T={}
for r in csv.DictReader(open('transactions.csv')): T[(int(r['elapsed_min']),r['generator'],r['transaction'])]=r
X={int(r['elapsed_min']):r for r in csv.DictReader(open('external_calls.csv'))}
tot=sum(int(T[k]['count']) for k in T if 10<=k[0]<=39); f=sum(int(T[k]['failed']) for k in T if 10<=k[0]<=39)
print('steady total',tot,'TPS',round(tot/1800,2),'err%',round(100*f/tot,3),'failed',f)
tps={m:sum(int(T[(m,g,t)]['count']) for g in ('LG1','LG2') for t in ('search','add_to_cart','checkout'))/60 for m in range(10,40)}
print('minutes <90',[m for m in tps if tps[m]<90])
ck=lambda a,b:[float(T[(m,g,'checkout')]['p95_s']) for m in range(a,b+1) for g in ('LG1','LG2')]
print('checkout p95 10-18',min(ck(10,18)),max(ck(10,18)),'19-39',min(ck(19,39)),max(ck(19,39)))
p=[int(X[m]['p95_ms']) for m in range(19,40)]; a=[int(X[m]['avg_ms']) for m in range(19,40)]
print('payment p95 19-39',min(p),max(p),'avg',min(a),max(a),'avg 18/19/40',X[18]['avg_ms'],X[19]['avg_ms'],X[40]['avg_ms'])
print('mean TPS 10-25',round(sum(tps[m] for m in range(10,26))/16,1),'26-39',round(sum(tps[m] for m in range(26,40))/14,1))
"
```

Output:
```
steady total 167426 TPS 93.01 err% 0.467 failed 782
minutes <90 [26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]
checkout p95 10-18 1.32 1.54 19-39 4.76 7.64
payment p95 19-39 2723 3323 avg 1809 2123 avg 18/19/40 258 2092 263
mean TPS 10-25 99.2 26-39 86.0
```

## 9. Quality checks

| Check | Result | How it was checked |
| --- | --- | --- |
| Every number matches `facts.md` or a cited agent file | **Pass**, with the scope stated | The headline numbers (steady-state total, TPS, error rate, minutes below 90 TPS, checkout p95 ranges, payment avg and p95 ranges) were recomputed from raw data by the command in §8, and all match. All other numbers were copied from `facts.md` or from the agent file cited beside them, and were not recomputed by the Report Writer. |
| No verdict outside the validity scope | **Pass** | The only verdicts are per-criterion for this run in PERF-A. Capacity is NOT ASSESSED. The report contains no "cannot/can support 500 users" (RC-1, RC-2), no "the sandbox caused or throttled" (RC-3), and no "driven / not driven by our load" (RC-4, CRIT-2). |
| The summary is no more certain than the findings | **Pass** | The summary uses the same grades and confidence as F-4 (Probable Contributor, High) and F-6/F-7 (Probable Contributor, Medium). It states that the capacity question is unanswered, and it marks SLA-2 as dependent on a reading. |
| Missing data is not shown as zero or PASS | **Pass** | Zero payment errors is not treated as "no throttling". The minute-44 values (DQ-01, DQ-02) are not used. The unmonitored outbound path, the missing batch log, failure reasons and DB statement data are stated as unknown. SLA-3 PASS carries its error-accounting limitation. |
| Every finding cites evidence | **Pass** | F-1 to F-15 each list E-/OBS-/DQ- IDs or appendix commands (§4). |

---

*Saved by the runner: the Report Writer subagent was not permitted to write report files in this environment, so it returned this report as text and the runner saved it unchanged.*
