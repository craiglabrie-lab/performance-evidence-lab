```
Agent: Devil's Advocate (Call 2: challenge)
Run: SYN-RUN-002
Read: agents/devils-advocate.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/ (scenario.json, transactions.csv, external_calls.csv, app_servers.csv, load_generators.csv; others via facts.md); examples/02-connection-pool/facts.md; examples/02-connection-pool/run/02-evidence.md, 03-validity.md, 04-performance.md, 05-application.md, 06-database.md, 07-infrastructure.md; my own examples/02-connection-pool/run/08a-independent-read.md
Execution: separate agent context, model Claude Opus 5.5
```

I wrote this after reading the team's files 03–07. I run in a separate context, but on the same model as the rest of the team, so this is a separate pass and not an independent reviewer. New numbers come from commands C1–C3 in the appendix (rule 3). Evidence IDs are the team's.

## Summary for the Test Lead

**Resolve before the report goes out:**

- **CRIT-1.** No file says that payment latency alone accounts for the SLA-1 failure in minutes 19–39. That changes what the recommendations can promise.
- **CRIT-2.** VAL-1 and the application file make a negative claim, "not driven by / not related to our load", which VAL-1's own RC-4 forbids.
- **CRIT-3.** The SLA-2 verdict depends on how the steady state is aggregated, and that reading has not been decided. It needs a recorded decision.

**Recommended, but not blocking:** CRIT-4 to CRIT-9.

**Numbers I checked and found correct:**

- steady-state TPS 93.0 (167,426 / 1,800);
- smallest failing SLA-1 value 4.76 s;
- payment p95 2,723–3,323 ms in minutes 19–39;
- concurrent payment calls 45.9–52.5 in minutes 19–24;
- checkout decomposition residual −0.17 to +0.21 s;
- minute-40 counterfactual 40.0 (40.05);
- LG memory identical on both generators in 45/45 minutes.

I found no number that disagrees with its source.

## Objections

### CRIT-1: SLA-1 would have failed in minutes 19–39 with no pool wait at all. The pool mechanism explains SLA-2 and the slowdown of the other transactions, not SLA-1.

- **Target:**
  - AC-5 (`03-validity.md` §3.3);
  - HYP-APP-1 and OBS-APP-04 (`05-application.md`);
  - the health table in `04-performance.md` §3;
  - by implication, any recommendation that releasing the connection before the payment call fixes the checkout SLA.
- **Problem.** This is a missing conclusion, and it makes the current story stronger than it should be in one place and weaker in another.
  - **Observed Fact.** Caller-side payment p95 was 2,723–3,323 ms in every minute from 19 to 39 (C1; E-10). That is above 2.0 s in all 21 minutes.
  - **Link to checkout.** There is one payment call per checkout (DQ-11). In all 132 sampled traces the checkout contains its payment call synchronously: total ≥ pool wait + hold ≥ payment (02-evidence A4). So in every one of those minutes at least about 5% of checkouts spent more than 2.7 s in the payment call alone. Checkout p95 therefore exceeds 2.0 s even if pool wait is zero.
  - **Caveats.** Minute bucketing between the two tools (DQ-07) and an assumed even split across generators. Neither can close a gap of 0.7 s or more.
  - **Projection for checkout average.** I removed pool wait and kept the observed payment latency (C2). Projected checkout avg is 2.42–2.73 s per minute. HYP-APP-1 experiment 2 predicts the same (~2.6 s), but no file draws the consequence for SLA-1.
  - **Projection for throughput.** The same projection puts the iteration time (VAL-1's four-think-times model) at 16.0–16.3 s, below the 20 s pacing. If HYP-APP-1 holds, users would not have run late and TPS would have stayed near 100. **So SLA-2's failure is what the pool amplification adds.** This is a model under two assumptions (where think time falls, and HYP-APP-1 itself), so it is no stronger than Probable Contributor.
  - **Consequences.**
    1. The SLA-1 outcome in minutes 19–39 is set by dependency latency, whatever the design. That is the strongest support for VAL-1's decision to defer the capacity verdict, and it should be stated as such.
    2. The design finding (HYP-APP-1) concerns SLA-2, search, add_to_cart, and how far the damage spreads. It does not concern meeting SLA-1 under a 2 s dependency.
    3. A fix that releases the connection would not make SLA-1 pass at 2 s payment latency. SLA-1 can be met only if payment latency stays within a budget that nobody has declared.
- **Severity: material.** It changes how the findings are framed and what the recommendations can claim.
- **Requested change.**
  - In the findings, split the 19–39 failures:
    - SLA-1: payment latency alone exceeds the criterion. Observed Fact for payment p95; High confidence for "SLA-1 fails at zero pool wait".
    - SLA-2, plus search and add_to_cart: pool amplification (HYP-APP-1, Probable Contributor, Medium).
  - In the recommendations:
    - Do not present connection release as the SLA-1 fix.
    - Have the stub experiment (T-1 / HYP-APP-1) report SLA-1 at each latency step, with and without the fix, so the experiment measures the payment-latency budget that SLA-1 can tolerate.
    - Name an owner for declaring a payment timeout or latency budget. Nothing in 03–07 addresses timeouts or a circuit breaker.

### CRIT-2: "Not driven by our load" is a negative claim that the evidence does not support, and RC-4 forbids it

- **Target:**
  - `03-validity.md` §2.8, "**The step did not follow our traffic.**";
  - §3.2 reason 5, "a shared-sandbox latency step not driven by our load";
  - `05-application.md` §1 A6, "Caller-side latency is not related to our call volume";
  - OBS-APP-10, "Latency is not a function of our call volume".
- **Problem.** What the evidence shows is narrower: the latency is not a function of our **per-minute call rate**. The same rates gave both regimes (VAL-1 V2). Several load-dependent mechanisms are still untested, and none can be excluded without sandbox-side data (DQ-10a, rule 9):
  - a cumulative quota or burst window: 21,752 calls by minute 18 (08a DA-2);
  - a concurrency limit;
  - hysteresis.
  - Recovery at minute 40 is the first ramp-down minute, which a load-dependent explanation predicts and an independent incident does not.
  - VAL-1's own RC-4 says, correctly, that "the data supports neither direction". The text quoted above takes a direction.
- **Severity: material.** The claim is a conclusion about the trigger. It would set the report against an external dependency on evidence that does not reach.
- **Requested change.** Replace each quoted phrase with "not explained by our per-minute call rate; whether it depends on our cumulative volume or concurrency is unknown (RC-4, U-1)". VAL-1 itself does not change.

### CRIT-3: The SLA-2 verdict depends on an aggregation reading that has not been decided

- **Target:** SLA-2 FAIL (AC-3; `04-performance.md` §3; `facts.md`).
- **Problem.** `scenario.json` scopes SLA-2 as "steady state" and does not say how to aggregate.
  - Read per minute, it fails in minutes 26–39 (14 consecutive minutes, 84.2–88.8 TPS).
  - Read as a 30-minute mean, it gives 93.0 TPS and passes (C2 confirms 167,426 / 1,800 = 93.01).
  - The analyst raised this; no one has decided it. It is the only verdict that flips on a reading.
- **My view.** FAIL is the right reading for a throughput criterion meant to show the load is **sustained**:
  - the mean mixes three regimes;
  - the last 14 minutes all fail;
  - the regime was still moving at minute 39 (threads still rising; RC-6).
  - A mean that passes only because the first 16 minutes were healthy is not evidence of sustained throughput.
- **Severity: material until decided.** It flips a health verdict.
- **Requested change.**
  - Record a DEC on the reading.
  - Report SLA-2 as FAIL (per-minute reading, minutes 26–39) and give the 93.0 TPS mean beside it.
  - Ask the criterion owner to state the aggregation for the rerun.

### CRIT-4: The pool-demand arithmetic does not close, so "demand ≈ 54 vs 40" should not be stated as a figure

- **Target:**
  - OBS-APP-03 (estimated demand 53.7–53.9);
  - §1 A2 ("about 54 connections against 40");
  - HYP-APP-1 ("demand exceeded the 40 available connections");
  - the prediction in HYP-APP-1 experiment 1 that the pool reaches 20/20 at 1.3–1.6 s.
- **Problem.**
  - OBS-APP-06, OBS-INF-10 and OBS-DB-07 all show that the same inputs imply 45.9–52.5 concurrent payment calls in minutes 19–24 (C1), with at most 40 connections to make them under. That is not physically possible if every call holds a connection.
  - So the estimate overstates true occupancy by up to about 30%, or not every checkout holds the connection. Either way, "54 vs 40" is not a measurement.
  - The DB file states this correctly ("at or above the cap"). The application file states it correctly in OBS-APP-06 but not in its summary or in HYP-APP-1.
  - The experiment-1 prediction band comes from the same model, so it inherits the error.
  - **I made the same mistake in 08a.** DA-2 gave 22.8 connections per node against 20 without noting that this cannot be physical. On this point the team's Medium confidence is right and my Medium-High was not.
- **Severity: minor.** The grade (Probable Contributor, Medium) already allows for it. The wording does not.
- **Requested change.**
  - State demand as "at or above the 40-connection cap (estimate overshoots; OBS-APP-06)".
  - Widen the experiment-1 prediction, or label it as model-derived. Keep the falsifier ("pool below max at 2.0 s").
  - Keep HYP-APP-1 at Medium. Do not raise it.

### CRIT-5: The minute-40 counterfactual sits on a knife-edge and uses a model shown to overshoot

- **Target:** OBS-APP-09 and §1 A6, "the 20% load reduction alone would not have relieved the pool".
- **Problem.**
  - The calculation gives 19.92 × 2.011 = 40.05 against a cap of 40 (C2).
  - The same model overstates occupancy by up to 30% (CRIT-4). So true demand at that rate and hold time could be well below 40, and the pool might have cleared from the load reduction alone.
  - The observed fact, that payment latency and the pool returned to reference in the same minute, stands without the counterfactual.
- **Severity: minor.** It does not change HYP-APP-1 or VAL-1. It does lean on the recovery question, which RC-4 leaves open.
- **Requested change.** Restate it as "indeterminate: at the cap within the model's known error". Drop "would not have relieved the pool".

### CRIT-6: The batch attribution (HYP-DB-3) is graded Correlation without a second measured signal

- **Target:** HYP-DB-3, "Grade: Correlation: timing plus session count".
- **Problem.**
  - judgments.md requires two independent **signals** moving together. The 10:30 schedule is a declaration in `scenario.json`, not a measurement. Nothing in the run shows the batch ran (DQ-10b).
  - What is measured is the following, all Observed Fact:
    - 6 sessions above a pool total pinned at its maximum, so a non-pool client was present;
    - row lock contention;
    - higher DB CPU and query time;
    - all with edges at minutes 30 and 33.
  - Linking those to the batch is a timing coincidence with a schedule.
- **Severity: minor.** No verdict or recommendation depends on it, and EXP-DB-3 already tests it.
- **Requested change.** Grade the non-pool client and the lock episode as Observed Fact. Record "consistent with the inventory-sync batch" as an ungraded hypothesis with Low confidence.

### CRIT-7: VAL-1 cites LG memory as generator-health evidence, but that metric is not a measurement

- **Target:** `03-validity.md` §2.4 and §3.2 reason 2, "memory ≤ 54.0%".
- **Problem.** OBS-INF-11 shows LG memory_pct is identical on both generators in all 45 minutes and is a fixed function of user count. I confirmed the 45/45 identity (C3). It carries no independent health information.
- **Severity: minor.** VAL-1 does not change. Users, mix, CPU and per-generator symmetry carry the decision.
- **Requested change.** Drop memory from VAL-1's reasons, or footnote it with OBS-INF-11. The same applies to my own 08a §2, which cited it.

### CRIT-8: "Cannot be ordered in time" at onset is slightly too weak

- **Target:** OBS-APP-03, HYP-APP-2 ("time order cannot be established"), 05 §1 A3.
- **Problem.** The minute-level series give weak ordering evidence that the team did not use (C3):
  - Payment avg at minute 19 is 2,092 ms, the same as minute 20 (2,093 ms). If latency had risen partway through minute 19, a per-call average for that minute would be diluted toward 258 ms. It is not diluted, so the latency was high from about the start of minute 19.
  - In the same minute, pool active was 17/17, pool wait 337/362 ms and threads 38/39. All three are below their minute-20 values (20/20, 460/437 ms, 49/48).
  - That fits latency at full level first, with the pool queue still building. `04-performance.md` OBS-04 comes close to this ("at or near the start of minute 19") without drawing the inference.
  - **Limits.** It depends on undocumented semantics (DQ-07): pool_active could be a point sample. It comes from one APM source, not two.
- **Severity: minor.** It supports HYP-APP-2's direction but is not new causal evidence. **No grade change requested.**
- **Requested change.** Record it as an Observed Fact with the DQ-07 caveat, and say "the traces cannot order them; the per-minute averages are consistent with payment latency first". Do not raise HYP-APP-2.

### CRIT-9: There is no experiment for the load-dependent explanation of the trigger

- **Target:** VAL-1 U-1/T-1; `05-application.md` HYP-APP-2 experiment; `07-infrastructure.md` HYP-INF-2.
- **Problem.**
  - The proposed tests cover where the payment time is spent: the outbound client, network phases and the stub.
  - **For HYP-B in 08a** (a sandbox limit that depends on our load), the only route is U-1, a records request to a sandbox owner who may have nothing.
  - If no records exist, the team has no planned way to settle whether production providers could impose the same limit.
- **Severity: minor.** It is a gap in the recommendations and does not affect any conclusion.
- **Requested change.** Add a fallback with owner, measure and falsifier, run against the real sandbox, outside the capacity test:
  - hold 500 users at a fixed call rate for longer than 40 minutes;
  - then step the call rate down and back up during any episode.
  - **Supports a load-dependent limit:** latency tracks the steps, or onset recurs at a similar cumulative call count.
  - **Refutes it:** latency episodes do not follow call rate or cumulative volume.

## Where the team differs from my independent read, and who I now think is right

| Point | My 08a | Team | Now |
| --- | --- | --- | --- |
| Answer to the question as asked | "No, the journey did not meet the criteria at 500 users" | SLA-1 and SLA-2 FAIL in this run; capacity verdict NOT ASSESSED (VAL-1 RC-1/RC-2; 04 §3) | **The team is right.** CRIT-1 shows that SLA-1 in minutes 19–39 fails on dependency latency alone, so the run cannot say whether *our* stack meets SLA-1 at 500 users under representative dependency latency. My "No" overreached. My second qualifier still stands, made more precise: the design cannot absorb about 2 s of dependency latency **without losing SLA-2 and slowing transactions that never call payment**. The report should lead with that conditional finding, not leave it behind "NOT ASSESSED". |
| Confidence for the pool mechanism | Probable Contributor, Medium-High | Probable Contributor, Medium | **The team is right** (CRIT-4). I missed that the demand arithmetic does not close. |
| LG memory as generator health | Cited | VAL-1 cited it; infrastructure showed it is derived | **The infrastructure specialist is right** (CRIT-7). |
| Server threads above client in-flight from minute 29 | Not seen | Found (OBS-APP-07, OBS-INF-09) | **The team is right to report it** as unexplained (HYP-APP-3, Low). |
| Non-pool DB client in minutes 30–33 | Not drawn out | 6 sessions above the pinned pool total (OBS-DB-08) | **The team's observation stands**, graded as in CRIT-6. |
| Direction payment → pool | Well supported by trace structure | HYP-APP-2, Probable Contributor, Medium; not ordered in time | Agree with the grade. CRIT-8 adds weak minute-level support. |
| Recovery at ramp-down | Called the best clue between HYP-A and HYP-B | Kept open (RC-4, OBS-13) | Agree, except for the wording in CRIT-2 and CRIT-5. |

## What the team got right and should keep

- **VAL-1 is VALID WITH LIMITATIONS,** and the TPS shortfall is treated as a system finding, not a harness failure. The supporting checks: users present, generators healthy, implied cycle time rising, and the response-time model crossing the 20 s pacing.
- **Percentiles are handled correctly.** SLA-1 is stated per minute and per generator throughout, with no run-level or cross-generator p95, and the failing margin is used to bound the failed-request unknown.
- **The pool mechanism is graded Probable Contributor, not Confirmed.** It rests on converging evidence:
  - the hold spans the payment call in all 132 traces;
  - the minute-by-minute decomposition of client response times into payment increase plus pool wait comes from two independent tools (OBS-APP-04, which I re-ran: C2);
  - "idle in transaction" sessions sit at exactly 40;
  - SQL time is flat.
  The overshoot (OBS-APP-06) is disclosed instead of hidden.
- **The batch and app1 heap/GC are set aside for onset on timing (rule 8) and split-by-source (rule 7),** and both are kept as separate observations with their own experiments.
- **The database rule-out is built on positive DB evidence,** with its scope stated: host-wide mean, no per-statement data, Medium for "not implicated at all". No DB tuning is recommended.
- **The infrastructure rule-out stops at the inbound path** and names the unmonitored outbound path as the main gap.
- **No one recommends "increase the pool size".** The experiments name an owner, a change, a measure and a refuting result.
- **Data-quality items are carried through every file,** including DQ-06 (no one-minute DB/app ordering), DQ-08 (trace sample) and DQ-10 (unknown, not absent).

## Handoff

**For the Test Lead**

- **Must resolve before the report goes out:**
  - CRIT-1: split SLA-1 (dependency latency alone) from SLA-2 and the collateral slowdown (pool amplification), and make sure the recommendations do not imply that the fix meets SLA-1.
  - CRIT-2: remove "not driven by / not related to our load".
  - CRIT-3: record a DEC on how SLA-2 is aggregated.
- **Recommended:** CRIT-4 to CRIT-9. None of them changes VAL-1 or a verdict.
- **Suggested wording for the answer to the question as asked:**
  - The run does not demonstrate that the journey supports 500 users: only 9 clean minutes, and a capacity verdict is not assessed.
  - It does show that at 500 users a caller-side payment latency of about 2 s breaks SLA-1 by itself.
  - Through connections held across the payment call, the same latency also takes down throughput (SLA-2) and every other transaction (Probable Contributor, Medium).

**Open questions:**
- The payment-latency budget that SLA-1 can tolerate (to be measured in the stub experiment).
- Whether payment-sandbox latency depends on our cumulative volume or concurrency (CRIT-9).

## Appendix: commands run

All commands were run from `examples/02-connection-pool/data` with `python3 -I -c`.

**C1. Checkout p95 against payment p95, and concurrent payment calls against pool, minutes 17–41**
```python
T={(m,gen,txn): row from transactions.csv}; X={m: row from external_calls.csv}; A={(m,node): row from app_servers.csv}
for m in 17..41: print checkout p95 LG1/LG2, payment avg/p95/calls, checkout count,
                       min(p95 LG1,LG2) - payment p95, calls*avg_ms/60000, app1+app2 db_pool_active
print min/max payment p95 and avg over 19..39
```
Output:
- Payment p95 in minutes 19–39: 2,723–3,323 ms. Payment avg: 1,809–2,123 ms.
- Checkout p95 minus payment p95 (lower of the two generators): 1.83–4.46 s in minutes 19–39.
- Concurrent payment calls: 52.3, 52.5, 47.2, 52.0, 50.0, 45.9 in minutes 19–24, against pool sums of 34, then 40.
- Calls equal checkouts in every minute shown.

**C2. Projection without pool wait; decomposition residual; steady-state TPS; minute-40 counterfactual**
```python
ref (10..18, count-weighted): search 0.596, add_to_cart 0.405, checkout 0.855 s; payment avg 0.245 s
for m in 19..39:
  dp   = payment_avg(m) - 0.245
  proj_checkout = 0.855 + dp                      # checkout avg with zero pool wait
  proj_iter     = 2*0.596 + 0.405 + 0.855 + dp + 12   # VAL-1 four-think-times model
  resid = (weighted checkout avg(m) - 0.855) - dp - mean(app1,app2 db_pool_wait_ms)/1000
steady total = sum of counts, minutes 10..39, all txns; TPS = total/1800
counterfactual = 1195/60 * 2.011
```
Output:
- Projected checkout avg: 2.42–2.73 s. Projected iteration time: 16.02–16.33 s.
- Residual: −0.17 to +0.21 s, matching OBS-APP-04.
- Steady state: 167,426 transactions, 93.01 TPS.
- Minute-40 counterfactual: 19.92 checkouts/s × 2.011 s = 40.05.

**C3. LG memory identity and app-tier values at onset**
```python
count minutes where LG1 memory_pct == LG2 memory_pct
for m in 15..21: payment avg; app1/app2 db_pool_active, db_pool_wait_ms, active_threads
```
Output:
- LG memory is identical in 45 of 45 minutes.
- Values at onset:

  | Minute | Payment avg | Pool active (app1/app2) | Pool wait | Threads |
  | --- | --- | --- | --- | --- |
  | 18 | 258 ms | 7/7 | 0/2 ms | 26/23 |
  | 19 | 2,092 ms | 17/17 | 337/362 ms | 38/39 |
  | 20 | 2,093 ms | 20/20 | 460/437 ms | 49/48 |
  | 21 | 1,876 ms | 20/20 | 661/708 ms | 58/54 |
