```
Agent: Test Lead (Call 2 — Decide)
Run: SYN-RUN-002
Read: agents/test-lead.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/ (scenario.json and the 8 CSVs, for the checks in TL-1 and TL-2); examples/02-connection-pool/facts.md; examples/02-connection-pool/run/01-test-lead-plan.md, 02-evidence.md, 03-validity.md, 04-performance.md, 05-application.md, 06-database.md, 07-infrastructure.md, 08a-independent-read.md, 08b-challenge.md
Execution: separate agent context, model Claude Opus 5.5
```

Data note: `scenario.json` marks this dataset as synthetic. It is decided here as though it were a real run.

**Scope.** VAL-1 is **VALID WITH LIMITATIONS** (`03-validity.md`). It is valid for criterion-level health in PERF-A within this run. It is not valid for a capacity verdict on our system at 500 users, in either direction (RC-1, RC-2). I do not change VAL-1, and nothing below disagrees with its decision. Where an objection corrects the *wording* of a reason in VAL-1 (CRIT-2, CRIT-7), I record the correction here. The recorded files are evidence and are not edited.

Evidence IDs are the team's (E-, DQ-, OBS-, SW-, HYP-, CRIT-, AC-, RC-, U-, T-). New numbers come from `facts.md`, the earlier run files, or commands TL-1 and TL-2 in the appendix (rule 3). Every checkout p95 is per generator per minute (rule 5).

## Answer to the question

*"Can the checkout journey support 500 concurrent users at 90+ transactions/second with checkout p95 at or under 2.0 seconds?"*

**We cannot conclude it from this run, either way.** What the run does show:

1. **In this run, in PERF-A, the criteria were not met.**
   - SLA-1 FAIL: 21 of 30 steady-state minutes failed, on both generators.
   - SLA-2 FAIL: minutes 26–39 were below 90 TPS, on the per-minute reading recorded in DEC-2.
   - SLA-3 PASS, Medium confidence.
2. **For 9 minutes (10–18), with caller-side payment latency at 230–258 ms, all three criteria were met at 500 users.** Nine minutes is too short to call the steady state sustained.
3. **From minute 19, caller-side payment latency was about 2 s.** At that latency:
   - **SLA-1 fails on payment latency alone** (F-4). It would have failed with zero pool wait, whatever our design.
   - **Holding the DB connection across the payment call adds pool exhaustion** (F-6, Probable Contributor, Medium). That spreads the delay to search and add_to_cart, which never call payment, and leads to the loss of throughput (SLA-2).

The conditional design finding leads this report. At 500 users, a payment latency of about 2 s takes down throughput and every transaction, not only checkout. That holds whether or not the sandbox represents production. What stays open is the trigger: why caller-side payment latency rose, and whether our own traffic or our own outbound path played a part.

## 1. Disposition of objections

| CRIT | Disposition | Reason | What changes |
| --- | --- | --- | --- |
| CRIT-1: SLA-1 fails on payment latency alone; the pool mechanism explains SLA-2 and the collateral slowdown, not SLA-1 | **Accepted** | Checked (TL-1): payment p95 was 2,723–3,323 ms in all 21 minutes from 19 to 39. There is one payment call per checkout (DQ-11), and the call is synchronous inside the checkout in 132/132 traces (`02-evidence.md` A4). So at least about 5% of checkouts spent more than 2.7 s in the payment call alone, every minute. Bucketing (DQ-07) and the generator split cannot close a margin of 0.7 s or more. The zero-pool-wait projection reproduces (TL-2): checkout avg 2.42–2.73 s, iteration 16.02–16.33 s, which is under the 20 s pacing. | New F-4. F-6 and F-7 are scoped to SLA-2 and collateral slowdown. REC-5 does not promise SLA-1. REC-4 measures the payment-latency budget for SLA-1. REC-6 gives the budget, timeout and circuit-breaker decision an owner. |
| CRIT-2: "not driven by / not related to our load" is an unsupported negative claim | **Accepted** | What the evidence shows is narrower: latency does not follow our **per-minute call rate**. The same rates gave both regimes (VAL-1 V2). A cumulative quota, a concurrency limit or hysteresis are untested. Recovery fell in the first ramp-down minute. RC-4 already forbids a direction. | F-3 uses the phrase "not explained by our per-minute call rate; dependence on cumulative volume or concurrency is unknown (RC-4, U-1)". This replaces the quoted wording in VAL-1 §2.8 and §3.2 reason 5, and in `05-application.md` A6 and OBS-APP-10. VAL-1's decision does not rest on that phrase. A load-dependent trigger would still leave the capacity question unanswered: it would turn into a question about production provider limits (U-1). So VAL-1 is unaffected. |
| CRIT-3: the SLA-2 verdict depends on an undecided aggregation | **Accepted** | It is the only verdict that flips on a reading. | DEC-2 records the reading. SLA-2 is reported as FAIL with the 93.0 TPS mean beside it. REC-3 asks the criterion owner to declare the aggregation. |
| CRIT-4: "demand ≈ 54 vs 40" is not a measurement | **Accepted** | The same inputs give 45.9–52.5 concurrent payment calls in minutes 19–24 against at most 40 connections (OBS-APP-06, OBS-INF-10, OBS-DB-07). Something in the inputs overstates, or not every checkout holds the connection. | F-6 says demand is "at or above the 40-connection cap; the estimate overshoots". The REC-4 prediction band is labelled model-derived and widened. The falsifier is kept. HYP-APP-1 stays at Medium. |
| CRIT-5: the minute-40 counterfactual is on a knife-edge | **Accepted** | 19.92 × 2.011 = 40.05 against a cap of 40, from a model known to overshoot by up to about 30%. | F-16 records the counterfactual as indeterminate. The observed fact stands: payment latency and the pool returned to reference in the same minute. |
| CRIT-6: HYP-DB-3 graded Correlation without a second measured signal | **Accepted** | The 10:30 schedule is a declaration, not a measurement (DQ-10b). judgments.md requires two measured signals. | F-10: the non-pool client and the lock episode are Observed Facts. The link to the batch is ungraded, Low confidence. |
| CRIT-7: VAL-1 cites LG memory as health evidence | **Accepted** (no change to VAL-1) | LG memory_pct is identical on both generators in 45/45 minutes and is a fixed function of user count (OBS-INF-11; 08b C3). | F-1 drops memory as evidence. VAL-1 reason 2 still holds on users, mix, CPU and generator symmetry. I cannot change VAL-1 and do not need to. |
| CRIT-8: "cannot be ordered in time" is slightly too weak | **Accepted, no grade change** | Payment avg at minute 19 (2,092 ms) equals minute 20 (2,093 ms), so it is not diluted. Pool active 17/17, pool wait 337/362 ms and threads 38/39 at minute 19 are all below their minute-20 values. Together these fit latency at full level first, with the queue still building. This depends on undocumented sampling and bucketing (DQ-07) and comes from one APM source. | F-8 adds this as an Observed Fact with the DQ-07 caveat. HYP-APP-2 stays Probable Contributor, Medium. |
| CRIT-9: no experiment for a load-dependent trigger | **Partly accepted** | The gap is real, and if REC-1 yields nothing, nothing else is planned. Two conditions apply, though. (a) A test of 40 minutes or more at about 25 calls/s against a **shared** sandbox affects other tenants, so it needs the sandbox owner's agreement. (b) We cannot see other tenants' traffic, so a negative result is weak evidence. | REC-7 adds the experiment as a fallback after REC-1. It needs owner consent, and it states that a null result does not exclude a provider-side limit. |

## 2. Findings

Each finding sits under VAL-1 (VALID WITH LIMITATIONS) and the allowed claim named. None of them is a capacity statement (RC-1, RC-2).

**F-1. The intended workload was delivered and the harness did not distort it.**
- **Detail:** 500/500 users ran in every minute 10–39 with 0 exits. The 2 : 1 : 1 mix held (2.000 : 0.995 : 1 in 19–39). LG CPU was 42.1–45.9%. log_level was "standard" on both generators. The two generators match minute by minute on TPS, error rate and SLA-1 outcome.
- **Not used as evidence:** LG memory (CRIT-7).
- **Evidence:** E-04, E-05, E-02, E-03; VAL-1 V1, V2; OBS-01.
- **Grade:** Observed Fact.
- **Confidence:** High. Coverage is complete and the two generators agree.
- **Scope:** AC-1, AC-7.

**F-2. SLA-1 met in minutes 10–18 and failed in 19–39, on both generators.**
- **Detail:** checkout p95 was 1.32–1.54 s per minute per generator in 10–18. It was 4.76–7.64 s in every minute 19–39. The smallest failing margin is 2.76 s.
- **Evidence:** E-14, E-15, E-13; OBS-02, OBS-05; TL-1.
- **Grade:** Observed Fact.
- **Confidence:** High.
- **Scope:** AC-2.

**F-3. Caller-side payment latency stepped up at minute 19, held for 21 minutes and returned at minute 40.**
- **Detail:**
  - Avg was 230–258 ms in minutes 7–18, 1,809–2,123 ms in 19–39, and 263 ms at 40. p95 was 2,723–3,323 ms per minute in 19–39. Errors were 0 throughout.
  - The step is **not explained by our per-minute call rate**: 1,517 calls at minute 18 and 1,500 at minute 19, and the same rates produced both regimes.
  - **Whether it depends on our cumulative volume or concurrency is unknown** (RC-4, U-1; CRIT-2).
  - Where the extra ~1.8 s was spent is unknown: provider, network path or our own outbound client (U-2, HYP-INF-2).
- **Evidence:** E-10; VAL-1 V2; OBS-03, OBS-APP-10; TL-1.
- **Grade:** Observed Fact for the series. The trigger is ungraded.
- **Confidence:** High for the series. None is assigned for the trigger.
- **Scope:** AC-5. RC-3 and RC-4 apply.

**F-4. At the payment latency observed in 19–39, SLA-1 fails on payment latency alone, with or without pool wait. (CRIT-1)**
- **Detail:**
  - Payment p95 exceeded 2.0 s by at least 0.72 s in all 21 minutes (TL-1).
  - Each checkout makes one payment call (DQ-11), and the call sits synchronously inside the checkout in 132/132 traces.
  - With pool wait removed and observed payment latency kept, checkout avg would still be 2.42–2.73 s (TL-2).
- **Consequences:**
  - The SLA-1 failure in this run does not by itself implicate our design.
  - Releasing the connection before the payment call cannot make SLA-1 pass at about 2 s of payment latency.
  - It is the strongest single reason the capacity verdict must wait for a controlled dependency (VAL-1 T-1).
- **Evidence:** E-10, E-02, E-03, E-11, E-12, DQ-11; `02-evidence.md` A4; 08b C1, C2; TL-1, TL-2.
- **Grade:** Probable Contributor. The mechanism is shown structurally but not by a controlled change. It is a counterfactual on the population, resting on a 0.2% trace sample for synchronous containment.
- **Confidence:** High. The margin of ≥ 0.72 s is far larger than any bucketing or generator-split error, and calls = checkouts in every minute supports containment beyond the sample.
- **Alternatives:**
  - Some checkouts make the payment call asynchronously. No trace shows this, and it would not change the p95 argument unless more than 95% did.
- **Scope:** AC-5.

**F-5. The DB connection is held across the payment call in every sampled checkout, and only the payment part of the hold changes.**
- **Detail:**
  - In all 132 traces, hold minus SQL minus payment is 8–24 ms.
  - SQL is 25–59 ms in every window, including 30–33.
  - The payment share of the hold is 73–88% in normal windows and 96–98% in 19–39.
- **Evidence:** E-11, E-12, DQ-08; OBS-APP-02, OBS-DB-06.
- **Grade:** Observed Fact for the sampled requests.
- **Confidence:** High for the sample. Extending it to all checkouts is an inference from a fixed-schedule 0.2% sample.
- **Scope:** AC-6.

**F-6. Holding connections across the payment call exhausted both DB pools and spread the delay to every transaction. (HYP-APP-1 with HYP-DB-2)**
- **Mechanism:**
  - Pool at 20/20 on both nodes, minutes 20–39 (Observed Fact).
  - DB sessions pinned at exactly 40, top state "idle in transaction", in 20–29 and 34–39 (Observed Fact, multi-minute windows).
  - Checkout demand **at or above the 40-connection cap**. The Little's Law estimate overshoots the cap by up to about 30% in 20–24, so it is not a measured figure (CRIT-4; OBS-APP-06).
  - Client response-time increases match payment increase plus pool wait (checkout) and pool wait alone (add_to_cart, most of search), minute by minute, across two independent tools. The residual is −0.17 to +0.21 s for checkout (OBS-APP-04; TL-2).
- **Not shown:** that pool size quantitatively sets the 84–89 TPS level (RC-6).
- **Evidence:** E-06, E-07, E-08, E-10, E-11, E-12; OBS-06, OBS-APP-03 to -06, OBS-DB-05 to -07.
- **Grade:** Probable Contributor for the amplification, given the payment-latency rise.
- **Confidence:** Medium. Several independent signals converge, but the hold pattern rests on a small fixed sample, the pool arithmetic does not close, and metric semantics are undocumented (DQ-07, DQ-08).
- **Alternatives set aside:**
  - Slower DB work: SQL flat, DB latency and CPU per TPS flat (F-9).
  - Thread exhaustion: 38/39 of 200 at onset.
  - App CPU or GC: unchanged at onset.
  - Our load rising: it did not.
- **Alternative kept open:** not every checkout holds its connection across the call. That would explain the overshoot, and it is tested in REC-2 and REC-4.
- **Scope:** AC-6.

**F-7. SLA-2's shortfall is late iterations with all users present. Pool amplification is the probable reason the iterations ran late.**
- **Detail:**
  - Implied cycle was 22.3–24.0 s in 26–39 against 20 s pacing, with 500 users running. This is a system finding, not a harness one (VAL-1 §2.2). Observed Fact, High.
  - Without pool wait, the four-think-time model gives 16.0–16.3 s per iteration, under the pacing (TL-2). So the pool amplification, not payment latency alone, probably cost SLA-2.
- **Evidence:** E-04, E-13; VAL-1 V1; 08b C2; TL-2.
- **Grade:** Probable Contributor for the attribution.
- **Confidence:** Medium. It inherits F-6 and the unverified assumption about where think time is applied (T-5).
- **Scope:** AC-3, AC-6. RC-6 applies.

**F-8. The direction of effect is payment latency → connection hold → pool saturation. The trigger is unknown. (HYP-APP-2)**
- **Detail:**
  - The payment span is measured after the connection is acquired.
  - Only the payment part of the hold changes.
  - Pool wait grows in 19–25 while payment latency is flat.
  - The pool clears with payment latency at minute 40.
  - The traces cannot order the two signals within 10:18:44–10:19:10. The per-minute averages fit payment latency at full level first: minute-19 avg is undiluted, and pool, wait and threads are still below their minute-20 values (CRIT-8, with the DQ-07 caveat).
- **Not shown:** why caller-side latency rose, or where the time was spent (U-2).
- **Evidence:** OBS-04, OBS-APP-02, -03, -05; 08b C3.
- **Grade:** Probable Contributor for the direction.
- **Confidence:** Medium. There is no outbound-client data, and the onset is not resolved in time.
- **Scope:** AC-5, AC-6.

**F-9. The database is not implicated in the onset or in minutes 19–29 and 34–39 (bounded negative). (HYP-DB-1)**
- **Detail:** In those minutes:
  - DB avg query time was 10.1–12.3 ms against a reference of 10.1–12.0 ms.
  - DB CPU per TPS was 0.285 and 0.290 against 0.282.
  - Lock wait was 2–8 ms.
  - Sampled checkout SQL was 25–59 ms.
  - Sessions sat at the pool total in a client-wait state.
- **Evidence:** E-08, E-11, E-12; OBS-DB-03, -04, -06.
- **Grade:** Observed Facts from two independent sources that agree. This is a bounded negative, not a cause.
- **Confidence:**
  - High for the measurements.
  - Medium for "not implicated at all". There is no per-statement or per-session data, and search and add_to_cart DB time is visible only through the host mean (DQ-10c).
- **No database tuning is recommended.**

**F-10. Minutes 30–33 were a separate DB episode from a non-pool client, with no measurable effect on the criteria.**
- **Observed Facts:**
  - "row lock contention" was the top event.
  - lock_wait was 683–800 ms and avg_query 19.2–20.2 ms.
  - DB CPU was 42.2–44.5%.
  - There were 46 sessions while both pools were pinned at 20. So 6 sessions came from another client.
  - Sampled checkout SQL was 30–56 ms. Checkout p95 and TPS stayed within the range of the neighbouring windows.
- **Timing:** the episode starts 11 minutes after onset, so it cannot explain onset (rule 8).
- **Link to the inventory-sync batch (10:30 UTC):** an **ungraded hypothesis**, Low confidence. There is no record that the batch ran (DQ-10b) and no lock-holder data (DQ-10c) (CRIT-6).
- **Open possibility:** about 2 s of open checkout transactions could lengthen any concurrent writer (HYP-DB-3(b)). Whether checkout locks rows before the payment call is unknown.
- **Evidence:** E-08, E-17, E-06, E-07, E-11, E-12, E-13; OBS-10, OBS-DB-08, -09.

**F-11. Hosts, the load balancer and the inbound network show no stress and no change at onset (bounded negative). (HYP-INF-1)**
- **Detail:**
  - App CPU was at or below 54.8% and DB CPU at or below 44.5%.
  - LB connections track users, and Mb/s tracks TPS.
  - Retransmits were 0.01–0.04%.
  - Both transitions follow load, not the symptom.
- **Gaps:** the outbound path to the sandbox (egress, NAT/proxy, DNS, TLS) is **not monitored**, and this rule-out does not reach it (HYP-INF-2). Platform sizing and quotas are not declared.
- **Evidence:** E-06 to E-09; OBS-INF-01 to -08.
- **Grade:** Observed Fact for the bounded statement.
- **Confidence:** High.

**F-12. From minute 27, app1 shows a heap, GC and CPU divergence that app2 does not show under the same queue.**
- **Detail:**
  - app1 heap was 82.3–86.3% and GC 643–863 ms.
  - app1 CPU was +2.6 to +8.3 points above app2.
  - app2 heap was 54.1–61.6% with the same pool, threads and pool wait.
- **Effect:** it starts 8 minutes after onset, and no latency effect is visible in sampled traces.
- **Evidence:** E-06, E-07, E-11, E-12; OBS-11, OBS-APP-08, OBS-INF-02.
- **Grade:** Correlation (HYP-APP-4, HYP-INF-3).
- **Confidence:** Medium for "node-specific". Low for any cause, because JVM configuration is unknown (DQ-10f).

**F-13. From minute 29, server threads exceed the client-side in-flight request count, reaching about +158 at 37–39.**
- **Detail:** this is not explained by client-visible work. Within three minutes at 200/200 there is no visible latency step.
- **Evidence:** E-02, E-03, E-06, E-07, E-09; OBS-APP-07, OBS-INF-09.
- **Grade:** Observed Fact for the arithmetic. It assumes comparable sampling (DQ-07).
- **Confidence:** Low for any explanation (HYP-APP-3).
- **Why it matters:** it means the 26–39 regime had not settled (RC-6).

**F-14. Failures stepped from 0.195% to about 0.6% at onset and then stayed flat. Their type is unknown.**
- **Detail:**
  - The rise is spread evenly across search, add_to_cart and checkout. Payment errors were 0.
  - abort_on_error is set, yet no user exited.
  - script_errors does not reconcile with transaction failures.
- **Evidence:** E-02 to E-05, E-10; OBS-08; DQ-04, DQ-05, DQ-10d.
- **Grade:** Observed Fact.
- **Confidence:** High for the counts. Failure semantics are undocumented.

**F-15. Recovery at minute 40 coincided with the first ramp-down step. What ended the episode is indeterminate.**
- **Detail:**
  - At minute 40, payment avg was 263 ms, pool wait 0/2 ms, threads 21/21, and checkout p95 1.38/1.36 s.
  - The counterfactual that the 20% load cut alone would not have cleared the pool is **indeterminate**. It gives 40.05 against 40 from a model that overshoots (CRIT-5).
  - Whether payment latency fell because our load fell is unknown (RC-4).
- **Evidence:** E-10, E-06, E-07, E-02, E-03; OBS-13, OBS-APP-09.
- **Grade:** Observed Fact for the coincidence.
- **Confidence:** High for the coincidence. None is assigned for its cause.

## 3. Health verdicts

Scope for every row: SYN-RUN-002, PERF-A, declared steady state minutes 10–39, under VAL-1 VALID WITH LIMITATIONS.

| Criterion | Verdict | Measured | Confidence and limits |
| --- | --- | --- | --- |
| SLA-1 checkout p95 ≤ 2.0 s, each steady-state minute, each generator | **FAIL** | Met in 9/9 minutes 10–18 on both generators (1.32–1.54 s). Failed in 21/21 minutes 19–39 on both generators (4.76–7.64 s). No run-level p95 is given (rule 5). | High. Whether failed requests are included in p95 is unknown, but that cannot reverse a 2.76 s margin. The failure is accounted for by caller-side payment latency alone (F-4). It is not attributed to our design. |
| SLA-2 total throughput ≥ 90 TPS, steady state | **FAIL** (per-minute reading, DEC-2) | ≥ 90 in minutes 10–25. Below 90 in all 14 minutes 26–39 (84.2–88.8). Shown beside it: the 30-minute mean is 93.0 TPS (167,426 / 1,800; TL-1). | High for the measurements. Medium for the verdict, because it depends on the reading in DEC-2. It is a system finding, not a harness artefact (F-7). The 84–89 TPS level is not a capacity figure (RC-6). |
| SLA-3 error rate ≤ 1%, steady state | **PASS** (as counted by the load tool) | 0.467% over minutes 10–39. The per-minute maximum is 0.67% (minute 27), so it passes under either reading. The rate tripled inside the episode (0.195% → about 0.6%). | Medium. abort_on_error, failure definitions and client timeouts are undocumented (DQ-04, DQ-05, DQ-10d). |
| Question as asked (capacity at 500 users) | **NOT ASSESSED** | See DEC-1 | VAL-1 excludes it in both directions (RC-1, RC-2) |

## 4. Recommendations

Ordered by priority. The run is not invalid, but the capacity question can only be answered once the dependency is controlled and the evidence gaps are closed. So evidence and test-integrity items come before system changes. **Not recommended:** increasing the DB pool size as the fix. It raises concurrent payment calls, DB sessions and thread use, and threads already reached 200/200. Database tuning is also not recommended (F-9).

**REC-1. Ask for sandbox-side records for the episode (U-1).**
- **Owner:** Test Lead, with the payment-sandbox owner.
- **Action:** request provider-side latency, rate-limit hits, throttling, tenancy and incident records for 2026-10-08 10:15–10:45 UTC.
- **Success measure:** records are received that cover 10:19–10:40 UTC.
- **What would prove the working view wrong:** provider-side latency stayed near reference (about 250 ms) while our caller-side latency was about 2 s. The extra time would then be on our side of the boundary (U-2), and the onset becomes a system finding.

**REC-2. Close the evidence gaps before the rerun (VAL-1 T-4; HYP-APP-1 exp. 3; HYP-INF-2; HYP-APP-3; `06-database.md` §5).**
- **Owner:** APM/platform owner, with the DBA.
- **Action:** add the following:
  - timing phases for the outbound payment call (outbound pool wait, DNS, connect, TLS, time to first byte) on both nodes, plus egress/proxy counters;
  - a per-request "connection held during outbound call" flag and the hold duration;
  - random, node-balanced trace sampling;
  - DB per-statement statistics and 10-second session snapshots with transaction age and client identity;
  - minute-by-minute thread dumps during any degradation;
  - documented semantics (point, mean or max) for every APM and DB metric;
  - a run ID in every export.
- **Success measure:** each item is present in the rerun's evidence register with its semantics documented.
- **What would prove it insufficient:** the rerun's Results Librarian still has to raise DQ-06, DQ-07 or DQ-08-type issues for these signals.

**REC-3. Fix the harness and criteria definitions (T-2, T-5, DEC-2).**
- **Owners:**
  - harness owner: abort_on_error and failure reasons;
  - test designer: where think time applies;
  - criterion owner (checkout product owner): how SLA-2 is aggregated.
- **Action:**
  - document abort_on_error and set it to the intended behaviour;
  - record a reason code per failure and declare client timeouts;
  - declare where think time is applied;
  - state whether SLA-2 is judged per minute or as a window mean.
- **Success measure:** exited_with_error, transaction failures and script_errors reconcile, and every failure has a reason. The scenario file states the think-time placement and the SLA-2 aggregation.
- **What would prove it wrong:** failures without reasons, or exits that do not match the setting.

**REC-4. Run a controlled dependency test at 500 users: capacity baseline plus stepped latency injection (VAL-1 T-1; HYP-APP-1 exp. 1; EXP-DB-1, EXP-DB-2).**
- **Owner:** Test Lead with the environment owner. The application team and DBA analyse the results.
- **Action:**
  - Replace the shared sandbox with a service-virtualisation stub.
  - **(a) Capacity baseline:** 30-minute steady state at a fixed 250 ms. This answers the capacity question under declared dependency latency.
  - **(b) Stepped injection:** at least 10 minutes each at 250 ms, 1.0 s, 1.5 s and 2.0 s.
  - At every step, report SLA-1 per minute per generator, SLA-2, pool active and wait, threads, search and add_to_cart avg, and DB session state.
  - Keep inventory-sync out of the window (REC-8).
- **Success measure:**
  - the stub's own logs confirm the latency it served, and caller-side latency stays within a declared tolerance of it;
  - (a) gives an unambiguous SLA-1/2/3 result over 30 minutes;
  - (b) gives the payment-latency budget at which SLA-1 first fails (CRIT-1).
- **Predictions (model-derived, so wide; CRIT-4):** the pool saturates somewhere between about 1.0 s and 2.0 s injected latency, and search and add_to_cart avg rise by about the pool wait.
- **What would prove HYP-APP-1 wrong:**
  - the pool stays below its maximum at 2.0 s;
  - or search and add_to_cart slow down with no pool wait.
- **What would make the latency our own (U-2):** caller-side latency exceeds what the stub served.

**REC-5. Test a build that releases the DB connection before the payment call (HYP-APP-1 exp. 2; EXP-DB-2 follow-on). Run it inside REC-4(b).**
- **Owner:** application team.
- **Action:** commit and release the connection before the outbound payment call, and re-acquire it afterwards only if needed. Repeat the REC-4(b) steps.
- **Success measure:** at 2.0 s injected latency:
  - pool active stays near reference (well below 20 per node) and pool wait is about 0;
  - DB idle-in-transaction sessions stay near reference;
  - search and add_to_cart are at their 10–18 levels;
  - TPS is ≥ 90 (SLA-2 PASS);
  - checkout avg is about reference plus the injected latency.
- **Not expected:** SLA-1 is **not** expected to pass at 2.0 s (F-4). This change contains the damage; it does not fix checkout latency.
- **What would prove it wrong:** the pool still saturates, or non-payment transactions still slow down, with the fix in place.

**REC-6. Declare a payment-latency budget and the failure behaviour of the checkout's payment call (CRIT-1).**
- **Owner:** checkout product owner with the payment-integration architect.
- **Action:**
  - Using REC-4(b), set the payment-latency budget that keeps checkout p95 within 2.0 s.
  - Define a client timeout and a circuit-breaker or fallback for the payment call.
  - Decide whether SLA-1 should be stated conditionally on dependency latency.
- **Success measure:** the budget, timeout and breaker are documented. In a REC-4 step above the timeout, checkout fails fast at the timeout and the other transactions are unaffected.
- **What would prove it wrong:** with the breaker in place, a step above the budget still raises pool wait or non-payment latency, or checkout waits past the timeout.

**REC-7. Fallback test of whether the sandbox latency depends on our load (CRIT-9, partly accepted). Run it only if REC-1 yields no records, and only with the sandbox owner's agreement.**
- **Owner:** Test Lead with the sandbox owner. This is not part of the capacity test.
- **Action:** hold about 25 calls/s against the real sandbox for more than 40 minutes. During any latency episode, step the call rate down and back up. Log cumulative calls and concurrent calls (REC-2 instrumentation).
- **Supports a load-dependent limit:** latency follows the rate or concurrency steps, or onset recurs at a similar cumulative count (about 21,750 calls by minute 18; 08a DA-2).
- **Refuting result:** episodes do not follow rate, concurrency or cumulative volume.
- **Limit:** we cannot see other tenants' traffic, so a null result does not exclude a provider-side limit.

**REC-8. Keep inventory-sync out of the steady state, and test its interaction deliberately (T-3; EXP-DB-3).**
- **Owner:** data team with the DBA.
- **Action:** schedule capacity tests away from 10:30 UTC. Separately, run the batch in a declared window during a fixed-latency stub test at 500 users, with the batch log and lock holder/waiter snapshots captured.
- **Success measure:** the extra sessions and lock waits belong to the batch, and checkout SQL and p95 in the batch window stay within the no-batch range.
- **What would prove it wrong:**
  - lock waiters include checkout statements, or checkout SQL or p95 rises: the batch does affect checkout;
  - or the contention appears without the batch: the source is something else.

**REC-9. Compare the app1 and app2 configuration (HYP-APP-4, HYP-INF-3).**
- **Owner:** platform owner.
- **Action:** compare JVM arguments, heap size, GC algorithm and instance type, and enable GC logs in the rerun.
- **Success measure:** a configuration difference or GC log accounts for app1's heap, GC and CPU delta.
- **What would prove node-specificity wrong:** the configurations are identical, and app2 shows the same change at the same queue depth.

## 5. Decision records

### DEC-1: Report criterion-level verdicts for this run and defer the capacity verdict

- **Decision:**
  - For SYN-RUN-002 in PERF-A: SLA-1 FAIL, SLA-2 FAIL, SLA-3 PASS (Medium).
  - The capacity question at 500 users is **NOT ASSESSED**.
  - The report leads with the conditional design finding: at 500 users, about 2 s of caller-side payment latency (i) breaks SLA-1 by itself (F-4, High), and (ii) through connections held across the payment call, also takes down throughput and every other transaction (F-6, F-7; Probable Contributor, Medium).
  - Next step: REC-1 to REC-4 before any capacity statement.
- **Strongest alternative:** **capacity FAIL, "the journey does not support 500 users"** (`08a-independent-read.md` §1).
- **Why not chosen:**
  - Our per-minute load did not change at onset.
  - The SLA-1 failure is accounted for by a dependency latency rise whose cause and location are unknown (F-3, F-4).
  - Under the earlier latency, all three criteria held for the 9 minutes observed.
  - A FAIL would attribute to our stack's capacity something the run did not show. The Devil's Advocate withdrew this answer in 08b.
- **Opposite alternative, also rejected:** "sandbox blip; discount minutes 19–39 and PASS". There are only 9 clean minutes (RC-2), and the design sensitivity (F-6) is a real finding whatever the sandbox's representativeness.
- **Remaining uncertainty:**
  - what triggered the latency rise, and whether any of the ~1.8 s is spent on our side (U-1, U-2);
  - whether it depends on our cumulative volume or concurrency;
  - whether every checkout holds its connection across the call, given that the pool arithmetic overshoots (F-6);
  - why threads outgrow client work (F-13);
  - what the failures were (F-14);
  - whether 500 users sustain 30 minutes under normal dependency latency.
- **One further possibility, not graded:** once latency rose, our concurrent payment calls rose from about 6 to about 40–52 (OBS-APP-06). A concurrency-sensitive provider could therefore *sustain* an episode that something else started. Under rule 8 this cannot explain onset, because concurrency rose only after latency did.
- **What would change the decision:**
  - **REC-1 or REC-2 shows the extra time was on our side** (provider latency normal, or outbound pool/DNS/TLS time rising): the onset becomes a system finding under our own load. Part (b) moves toward VALID, and a capacity FAIL could be issued (U-2). That would be for a new VAL- decision, not for me.
  - **REC-4(a) passes all three criteria for 30 minutes at a declared 250 ms:** capacity PASS under that dependency condition. **If it fails:** capacity FAIL.
  - **REC-4(b) shows no pool saturation at 2.0 s:** F-6 is refuted, and the explanation of SLA-2 and the collateral slowdown has to be reopened.

### DEC-2: SLA-2 is judged per steady-state minute (sustained throughput)

- **Decision:** SLA-2 is FAIL for minutes 26–39 (14 consecutive minutes at 84.2–88.8 TPS). The 30-minute mean of 93.0 TPS is reported beside it. The same per-minute reading applied to SLA-3 still gives PASS (maximum 0.67%), so the two "steady state" criteria are read consistently.
- **Reasons:**
  - A throughput criterion exists to show the load is **sustained**.
  - The mean blends three regimes and passes only because minutes 10–25 were healthy. Minutes 10–25 averaged 99.2 TPS and minutes 26–39 averaged 86.0 TPS (TL-1).
  - The regime was still moving at minute 39 (F-13).
  - This matches the reading in `facts.md`, VAL-1 AC-3 and `04-performance.md`.
- **Strongest alternative:** a window mean (93.0 TPS, PASS). Its best argument is in `scenario.json` itself: SLA-1 is scoped "each steady-state minute", while SLA-2 says only "steady state". That difference in wording could mean a window aggregate was intended.
- **Why not chosen:** the wording is ambiguous, not explicit. A reading that hides 14 consecutive failing minutes would overstate health, and that is the more harmful error.
- **Remaining uncertainty:** the criterion owner's intent.
- **What would change it:** if the owner declares a window mean (REC-3), SLA-2 becomes PASS for this run at 93.0 TPS. The report must then still state that every minute from 26 to 39 was below 90.

## 6. Dissent

Objections and points not fully resolved, stated fairly:

1. **How SLA-2 is aggregated (CRIT-3, DEC-2).** I decided the per-minute reading. The contrast between how SLA-1 and SLA-2 are scoped in `scenario.json` is a fair argument for a window mean. Only the criterion owner can settle it.
2. **CRIT-9, partly accepted.** The Devil's Advocate asked for a load-dependence test against the real sandbox. I made it conditional on REC-1 and on the sandbox owner's consent, and noted that a null result is weak. If the owner refuses and has no records, the load-dependence question about the trigger stays open with no planned route to close it.
3. **Whether every checkout holds its connection (OBS-APP-06, CRIT-4).** The application, database and infrastructure specialists all flag that the occupancy arithmetic overshoots by up to about 30%. "Not every checkout holds the connection" and "the metrics are not commensurable" are both live. This caps F-6 at Medium until REC-2 and REC-4 report.
4. **The payment → pool direction (CRIT-8).** The Devil's Advocate's 08a called the direction "well supported". The application specialist and I keep it at Probable Contributor, Medium, because the outbound path is unobserved (U-2). The minute-level support CRIT-8 adds is recorded but does not raise the grade (judgments.md: only new evidence raises a grade).
5. **Recovery at ramp-down (F-15).** The Devil's Advocate rates this as the best clue between an external incident and a load-dependent limit. The team keeps it open. No one's reading is shown wrong. It remains the single most informative unexplained coincidence in the run.
6. **Thread growth beyond client work (F-13).** It is unexplained. Candidate causes (metric semantics, server work after client abandonment, background threads) remain open.

## Handoff

- **For the report:**
  - Lead with DEC-1's conditional finding.
  - Verdicts: SLA-1 FAIL, SLA-2 FAIL (per-minute reading, 93.0 TPS mean shown), SLA-3 PASS (Medium), capacity NOT ASSESSED.
  - Every checkout p95 per minute per generator. Never say "the sandbox caused/throttled" or "not driven by our load" (CRIT-2).
- **Next actions, in order:** REC-1, REC-2 and REC-3 (evidence and harness), then REC-4 with REC-5 (controlled test), then REC-6 (budget and timeout). REC-7 to REC-9 are secondary.
- **Do not recommend:** increasing the pool size, or database tuning.
- **Open questions:**
  - U-1 and U-2: trigger and location of the payment time;
  - the SLA-2 aggregation intent;
  - abort_on_error semantics and failure types;
  - whether inventory-sync ran;
  - app1 configuration;
  - `active_threads` semantics.
- **Not used:** nothing from SYN-RUN-001. No run-level p95. No one-minute DB-vs-app ordering.

## Appendix: commands run

Both were run from `examples/02-connection-pool/data` with `python3 -I -c`.

**TL-1. SLA ranges, payment p95, steady-state totals and per-minute SLA-2 and SLA-3**
```python
import csv
X={int(r['elapsed_min']):r for r in csv.DictReader(open('external_calls.csv'))}
T={}
for r in csv.DictReader(open('transactions.csv')):
    T[(int(r['elapsed_min']),r['generator'],r['transaction'])]=r
p95=[int(X[m]['p95_ms']) for m in range(19,40)]
print('payment p95 19-39 min/max',min(p95),max(p95),'all>2000',all(v>2000 for v in p95))
print('payment avg 18,19,20,40',[X[m]['avg_ms'] for m in (18,19,20,40)])
ck=[float(T[(m,g,'checkout')]['p95_s']) for m in range(19,40) for g in ('LG1','LG2')]
ck0=[float(T[(m,g,'checkout')]['p95_s']) for m in range(10,19) for g in ('LG1','LG2')]
tot=sum(int(T[k]['count']) for k in T if 10<=k[0]<=39); f=sum(int(T[k]['failed']) for k in T if 10<=k[0]<=39)
# per minute 10..39: TPS = count/60, error % = failed/count; list minutes < 90 TPS; max error %; mean TPS 10-25 and 26-39
```
Output:
- Payment p95 in minutes 19–39: 2,723–3,323 ms; all above 2,000. Payment avg at minutes 18, 19, 20 and 40: 258, 2,092, 2,093 and 263 ms.
- Checkout p95 per generator per minute: 4.76–7.64 s in 19–39; 1.32–1.54 s in 10–18.
- Steady state: 167,426 transactions, 93.01 TPS, 0.467% errors.
- Minutes below 90 TPS: 26–39. Per-minute maximum error rate: 0.67%. Mean of per-minute TPS: 99.2 in 10–25, 86.0 in 26–39.

**TL-2. Zero-pool-wait projection and checkout decomposition (re-run of 08b C2)**
```python
# ref (10..18, count-weighted avg_s, both generators): search, add_to_cart, checkout; payment ref = mean avg_ms 10..18
for m in 19..39:
    dp  = payment_avg(m) - ref_payment
    proj_checkout = ref_checkout + dp
    proj_iter     = 2*ref_search + ref_add + ref_checkout + dp + 12      # four 3 s think times (VAL-1 model)
    resid = (weighted checkout avg(m) - ref_checkout) - dp - mean(app1,app2 db_pool_wait_ms)/1000
```
Output:
- Reference values: search 0.596 s, add_to_cart 0.405 s, checkout 0.855 s, payment 0.245 s.
- Projected checkout avg with zero pool wait: 2.42–2.73 s.
- Projected iteration time: 16.02–16.33 s.
- Decomposition residual: −0.17 to +0.21 s.
