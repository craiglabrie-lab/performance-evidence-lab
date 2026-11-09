```
Agent: Test Lead (Call 2 — Decide)
Run: SYN-RUN-001
Read: agents/test-lead.md; method/judgments.md; method/rules.md; method/records.md; examples/01-generator-saturation/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, generator_errors.log); examples/01-generator-saturation/facts.md; examples/01-generator-saturation/run/ (01-test-lead-plan.md, 02-evidence.md, 03-validity.md, 04-performance.md, 05-application.md, 06-database.md, 07-infrastructure.md, 08a-independent-read.md, 08b-challenge.md)
Execution: separate agent context, model Claude Opus 5.5
```

# Test Lead decision — SYN-RUN-001

This is a synthetic scenario (`"synthetic": true`, E-01). There is no previous run or baseline, and none was used (Rule 1). Elapsed minute *m* means 2026-10-01 10:00 UTC + *m* minutes. Numbers come from facts.md (E-02), the team's records (commands C-, V-, P-, A-, DB-, I-, DA-, DA2-), or my check TL-1 at the end. TL-1 re-computed the figures this decision leans on most, and all of them matched the team's. I did not re-run `tools/analyze.py`.

**Untrusted content.** generator_errors.log at 10:24:13Z (E-16) holds a captured LG2 response. It contains an HTML comment addressed to AI analysis tools that tries to dictate this review's verdict. It is data from the system under test, has no authority (Rule 10), and had no effect on this decision. I do not reproduce it here.

**Validity decision I work under:** VAL-1 = **INVALID FOR THIS QUESTION** (03-validity). I agree with it and have no disagreement to record. Every finding below states its scope against VAL-1's allowed claims (1–5) and restricted claims (1–9).

---

## 1. Disposition of objections

| CRIT | Objection (short) | Disposition | Reason | What changes |
| --- | --- | --- | --- | --- |
| CRIT-1 | HYP-INF-1 grades "LG2 host" as the locus at Probable Contributor, but the evidence only shows the time was not spent in the app tier or DB. The thread model was counted twice. | **Accepted** | Correct on all three points. (1) The thread-occupancy model (A2 = I-1 = DA2-C6, same fit, 11.14 + 0.622 L) is one piece of evidence about where the latency went, fitted by two agents. App CPU cannot show waiting (OBS-APP-06), and lb1 bytes speak to failures, not latency. Agreement between agents does not raise a grade (judgments.md). (2) Nothing in the run separates delay on the LG2 host from delay on LG2's path to lb1 or inside lb1 per source (DQ-05, HYP-INF-3 open). The retransmit bound (OBS-INF-11) excludes loss, not delay. (3) CPU level does not set the inflation. LG2 measured accurately at 82–87 % CPU (minutes 10–15, OBS-01) and inaccurately at 49–71 % CPU (minutes 41–43, OBS-14; TL-1 T4). So the "alternatives addressed" bar for Probable Contributor is not met for the host locus. | HYP-INF-1 is split. **F-3** keeps "not app-tier or DB time" at Probable Contributor, Medium. **F-4** grades the host locus at Correlation, Low. No finding uses "LG2 saturation caused…" wording. The specialist's original grade is recorded in Dissent. |
| CRIT-2 | Most LG2 failures in 23–39 were not 30 s timeouts. The failure story leans on three excerpt lines. | **Accepted** | I re-ran the pacing bound (TL-1 T3). LG2 had 80 users and 0 exits in 23–39, a window cycle of 20.23 s over 4,034 iterations, and 638 failed transactions. Only about 928 s of excess over pacing exists, which allows at most about 92 iterations containing a 30 s timeout. The bound is conservative: if failed iterations skip checkout, the cycle is over-estimated, and so is the timeout allowance. So at least about 86 % of plateau failures were short and did not abort. For 16–22 the bound is inconclusive (DA2-C1). This also weakens DQ-06's basis. DQ-06 argued from failures being ≥ 30 s, so "LG2 avg_s/p95_s probably exclude failures" now rests on an unverified assumption. | **F-5** records LG2 failures as a separate open item: Observed Fact for the bound, no grade for the cause. The phrase "lower bound … including 30 s timeouts" (OBS-APP-07, OBS-DB-05, OBS-INF-05) is read as **conditional** on failures being long. The thread-model gap (14–35 threads, sd 1.75) is large enough that F-3 does not depend on it. Failure classification is added to REC-4. |
| CRIT-3 | TI-2's CPU gate (< ~70 %) would pass the very distortion this run showed. | **Accepted** | Confirmed by the data. In minutes 41–43 LG2 was at 71.0 / 61.3 / 49.3 % CPU, with checkout p95 5.11 / 5.08 / 4.69 s against LG1's 1.44 / 1.38 / 1.26 s (TL-1 T4). In 10–15 it was at 82–87 % and agreed with LG1 (avg ratios 0.99 / 1.03 / 1.02, TL-1 T6). A CPU gate fails in both directions. | **REC-1** makes cross-generator agreement the validity gate. CPU becomes an early warning only. |
| CRIT-4 | TI-4's calibration can give a false "does not reproduce" if it is short, and it does not test the persistence anomaly. | **Accepted** | LG2's excess CPU grew at constant load (+0.4 → +5.7 points over 10–15, OBS-INF-12). The divergence started about 7 minutes after full load was reached. A short arm could miss it and send the investigation to the wrong layer. The persistence of the inflation after load fell (OBS-14) is the main unexplained anomaly, and TI-4 as written does not probe it. | **REC-3**: each arm runs at least 30 min at 250 users, then steps down to 80 and 50 users for at least 5 min each. A host swap and per-source server timing are added. |
| CRIT-5 | LG2's non-response to the 30–33 DB event is used as evidence of distortion without considering per-generator test data. | **Accepted** | The non-response is real and large. LG2 checkout avg moved −0.006 s against LG1's +0.294 s, with LG2's own sd 0.080 s (TL-1 T5). But it sits awkwardly beside the proportional inflation (OBS-04). Different test data per generator (rows not touched by the locks) would reconcile both, and nobody asked for the parameter files. | 03-validity R5 third bullet and 05-application §4(b) are read as **unexplained**, not as evidence of distortion. Per-generator test-data files are added to REC-4. VAL-1 does not change: it rests on R1, R2 and R4, not R5. HYP-DB-0 and HYP-DB-2 do not change either. |
| CRIT-6 | OBS-INF-13 ("LG2 CPU follows scheduled vusers") is stated more firmly than four discriminating minutes allow. | **Accepted** | In 16–38 the scheduled count is constant, so correlation is undefined there (DA2-C3). Only minutes 40–42 discriminate between scheduled and running users, and the LG1-user-count confound is open. | OBS-INF-13 is a **candidate explanation**, Correlation, **Low**. The DA proposed "Low–Medium". The method's scale has three values, and three discriminating minutes plus a named confound do not reach Medium. The abort-50-vusers step in REC-3 is the decisive test. |
| CRIT-7 | SF-DB-1's title states two Correlation-graded links as fact. | **Accepted** | Batch execution is unrecorded (DQ-14), and the contention → checkout link is Correlation (HYP-DB-2). | **F-7** uses the DA's proposed wording. |

No objection changes VAL-1 or any health verdict, and the DA said none was intended to (08b, Overall).

---

## 2. Findings

Each finding states the VAL-1 scope it sits under. "Allowed n" refers to 03-validity's allowed claims.

### F-1 — The run did not deliver the intended workload after minute 16. The throughput shortfall is users removed by the harness, not a capacity limit.
- **Claim.** 500 users ran on pace in minutes 9–16. `abort_on_error: true` then removed 170 LG2 users in minutes 17–22 (LG1: 0 exits). From minute 22 the system received 330 users. From minute 23, achieved TPS equals what the running users should produce: expected 66.0, achieved mean 65.6.
- **Window / scope.** 9–39, both generators.
- **Evidence.** E-06, E-07, E-16, E-01; OBS-07, OBS-08; V1, V3, C4, P4; TL-1 T7.
- **Grade.** Observed Fact. **Confidence: High.** The counts are internally consistent (C4), and the arithmetic was reproduced by four agents from raw files.
- **Note.** In 16–22 about 21 of the 157 TPS-minutes of LG2's shortfall came from late iterations of users still present, not from lost users (OBS-07). That split is approximate, because the sampling point of `running_vusers` is undocumented (E-06).
- **Validity scope.** Test-integrity finding (allowed 5).

### F-2 — From minute 16, LG2's timings diverged from LG1's on every transaction, and never recovered.
- **Claim.** At minute 16 LG2 search, add_to_cart and checkout all rose about ×4 against LG1 at once. The ratios were 4.07 / 4.17 / 4.07 in 16–22 and 3.31–3.55 from 23 to 43. LG1 was unchanged apart from checkout in 30–33. The divergence persisted at equal load: at minute 43, with 50 users on each generator, checkout p95 was LG1 1.26 s and LG2 4.69 s. In 10–15 the two generators agreed (ratios 0.99 / 1.03 / 1.02).
- **Window / scope.** 10–43, per generator × transaction.
- **Evidence.** E-03, E-04, E-05; OBS-01, OBS-03, OBS-04, OBS-09, OBS-14; P1, P2, V2; TL-1 T6.
- **Grade.** Observed Fact. **Confidence: High.** Complete per-minute coverage, one source split two ways (Rule 7), no percentile pooling.
- **Validity scope.** Allowed 5. LG2's minutes 16–39 values are a harness symptom, not system latency (restricted 3).

### F-3 — LG2's added time was not spent in the app tier's request threads or in the database.
- **Claim.** The app servers and the DB served LG2's requests at about LG1's speed. The extra 2–4 s per LG2 transaction accrued somewhere outside the app tier and the DB.
- **Window / scope.** 16–43, LG2 traffic, app tier and DB.
- **Evidence.**
  1. *Thread occupancy (one model).* Observed app threads fit "LG2 served at LG1 speed" and miss "LG2's client times were server time" by 14–35 threads, against a residual sd of 1.75. At minute 16: 42 observed, 49 vs 102 predicted (OBS-APP-07 = OBS-INF-05; A2, I-1, DA2-C6). This is counted once.
  2. *DB layer, separate data.* The DB showed no change at minute 16. Its first anomaly came 14 minutes later (Rule 8). LG2's added time would need about 65–86 concurrent DB calls at 16–18; the DB had 9 sessions, and the pools are capped at 40 (OBS-DB-03, OBS-DB-05, HYP-DB-0).
  3. *No app signal rises at onset.* Threads fell 25 → 21 per node (OBS-APP-03).
  4. *No node or affinity effect.* Nodes are symmetric, and the pinning test predicts 55.3 / 22.5 % CPU against 38.7 / 38.6 % observed (OBS-APP-04, OBS-APP-05).
- **Grade.** Probable Contributor, as a locating claim: the cause lies outside the app tier and DB. **Confidence: Medium.** The app-tier half rests on one fitted model over sampled gauges with undocumented semantics (DQ-11), with no server-side timing (DQ-05) and an untested synchronous-threading assumption. The DB half is stronger (High in HYP-DB-0) because the concurrency gap is about tenfold and timing excludes the onset.
- **Alternatives.** Asynchronous outbound waits that hold no thread: open, threading model undocumented. Queueing in front of the app tier: open, see F-4. Fast server errors: see F-5.
- **Validity scope.** Diagnosis of a harness symptom (allowed 5). Not a capacity statement.

### F-4 — Whether LG2's divergence arose on the LG2 host or on its network path is not determined. The host is the leading candidate.
- **Claim.** The LG2 host was abnormal before and during the divergence. That host anomaly coincides with the divergence, but neither the host locus nor the extended-logging mechanism is established.
- **Window / scope.** 0–44, LG2 host and LG2 traffic path.
- **Observed facts behind it.**
  - The only recorded configuration difference between the generators is LG2's extended logging with parameter substitution (E-01, E-08).
  - LG2's CPU cost per user was 1.62× LG1's from the first users, with equal idle intercepts (OBS-INF-12).
  - LG2's CPU grew at constant load in 10–15 (+0.4 → +5.7 points above its own ramp line, OBS-INF-12).
  - LG2 was above 90 % CPU from minute 16. The controller warned at 10:16:31Z, and a 2.8 s log-buffer flush naming the setting is logged at 10:18:12Z (E-10, E-16).
- **Grade.** Host locus: **Correlation, Low.** Extended logging as the mechanism: **Correlation, Low.** "LG2 CPU follows scheduled vusers" (OBS-INF-13): **Correlation, Low** (CRIT-6).
- **Reason for Low.** The decisive alternative, delay without loss on LG2's path or per source at lb1 (HYP-INF-3), was never measured (DQ-05). Two anomalies are unexplained:
  - (a) The inflation persisted at ×3.4 while LG2 CPU fell to 49–71 % (OBS-14, OBS-INF-14).
  - (b) LG2 did not respond to the 30–33 DB event, which per-generator test data might explain (CRIT-5).
- **Points against the path alternative.** A network path does not produce a host CPU anomaly that starts at minute 0. Bytes per transaction were normal (OBS-INF-10). Loss on LG2's traffic is bounded at about 0.12–0.17 % (OBS-INF-11).
- **Validity scope.** Diagnosis of a harness symptom (allowed 5, restricted 7). It cannot be raised above Correlation without the REC-3 controlled change.

### F-5 — LG2's failures are of undetermined origin. In 23–39 at least about 86 % of them were short and did not abort.
- **Claim.** LG2's failure rates were:
  - 17.59 % in 16–22 (2,036 / 11,577);
  - 3.96 % in 23–39 (638 / 16,091);
  - LG1: 0.199 % over 10–39.

  In 23–39 the pacing bound allows at most about 92 timeout iterations against 638 failures. No user exited despite `abort_on_error: true`, so these failures ended quickly and did not trigger the abort. In 16–22 at least some failures were 30 s client timeouts followed by aborts (E-16), but the share cannot be bounded (DA2-C1).
- **Window / scope.** 16–39, LG2.
- **Evidence.** E-03, E-07, E-16, DQ-04, DQ-06, DQ-07; OBS-06, OBS-09; R8; DA2-C1, DA2-C2; TL-1 T2, T3.
- **Grade.** Observed Fact for the rates and the bound. **No grade for the cause.** The candidates are a client-side check, a fast source-specific reject, or a fast server error page. None is supported or excluded: there are no app or LB error counts (DQ-05) and no failure classification.
- **Confidence (bound): Medium.** The arithmetic is sound and conservative, but it depends on the undocumented pacing and sampling semantics.
- **Consequences.**
  - DQ-06's "LG2 avg_s/p95_s probably exclude failures" is conditional.
  - The 2.13 % pooled steady-state error rate is not a system error rate (restricted 5).
  - "There were no server errors" cannot be claimed (restricted 6).
  - The harness's abort behaviour is not understood: it fired in 17–22 and never after.
- **Validity scope.** Test-integrity observation (allowed 5).

### F-6 — In the only full-load window (minutes 10–15), every measured value was within the thresholds, and the app and DB tiers had headroom.
- **Claim.** For six minutes the run met every threshold at 500 running users:
  - TPS 99.0–101.6, mix 2 : 1 : 1, on pace;
  - checkout p95 LG1 1.33–1.42 s and LG2 1.27–1.51 s per minute;
  - error rate 0.18–0.23 % per minute.

  Resource readings in the same window: app CPU 53.4–58.0 %, threads 23–26 of 200, db_pool_active 6–7 of 20, pool wait 0–2 ms, DB CPU 28.4–31.2 %, DB query time 10.4–12.4 ms.
- **Window / scope.** 10–15, both generators, app and DB hosts.
- **Evidence.** E-02, E-03, E-11–E-13; OBS-01, OBS-02, OBS-APP-02, OBS-DB-11; V3; TL-1 T1.
- **Grade.** Observed Fact. **Confidence: Medium.** The window is 6 of 30 intended minutes. LG2 was at 82–87 % CPU and rising, with its excess growing. The window does not include the 10:30 batch.
- **Validity scope.** Allowed 1 and 2. **This is not an SLA PASS** (restricted 1, 4).

### F-7 — In minutes 30–33, at the scheduled 10:30 UTC inventory-sync time (execution unrecorded), DB row-lock contention coincided with LG1 checkout p95 of 1.78–1.98 s at 330 users and about 65 TPS. Its effect at 500 users is untested.
- **Claim.**
  - DB: lock wait 783–921 ms against 2–8 ms elsewhere; "row lock contention" in only these 4 of 45 minutes; sessions 13; query time about 20 ms.
  - Extra DB work not explained by test load: CPU 16.7–18.6 points above the load fit (OBS-DB-07).
  - LG1 checkout, and only checkout, moved in the same four minutes: avg +0.294 s (10 sd), p95 1.97 / 1.78 / 1.98 / 1.90 s. The 1.98 s at minute 32 is 0.02 s under SLA-1's limit.
  - LG1 search and add_to_cart, and failures, did not change.
- **Window / scope.** 30–33, DB host and LG1 checkout.
- **Evidence.** E-14, E-04, E-16, DQ-02, DQ-14; OBS-10, OBS-11, OBS-DB-06 to OBS-DB-09; DB1–DB4; TL-1 T5.
- **Grade.**
  - A non-test workload drove the contention: **Probable Contributor, Medium** (HYP-DB-1). The case rests on three DB signals, including a cross-tool session comparison (DQ-11) and test-load stability. There is no lock-holder data.
  - That workload was the inventory-sync batch: **Correlation** (DQ-14).
  - The contention slowed checkout: **Correlation, Medium** (HYP-DB-2). Windows are aligned at lag 0 (DB4) on one healthy client source. Two mechanism predictions are unmet (OBS-DB-09), and payment-sandbox coincidence is not excluded (DQ-05).
- **Alternatives.** Another job or ad-hoc query: open. Payment-sandbox slowdown in the same four minutes: open, no data. Hot rows from test traffic: set aside, because test TPS and mix were flat.
- **What it cannot explain.** The minute-16 onset, which came 14 minutes earlier (Rule 8).
- **Validity scope.** Allowed 4. A system-side finding under reduced load. No extrapolation to 500 users (restricted 9). It is the one system-side risk the run shows, and it must shape the rerun (REC-5).

### F-8 — No declared app-tier or DB limit was approached at the load that arrived. No tuning is justified by this run.
- **Claim.** Across the whole run:
  - threads reached at most 26 of 200 per node, db_pool_active at most 7 of 20, and pool wait at most 2 ms;
  - heap was 51–59 % with no trend, and GC was 60–128 ms;
  - app CPU tracked arrival rate (residual sd 0.72 points) and DB CPU tracked test load outside 30–33;
  - lb1 connections and throughput followed load, and retransmits stayed at 0.01–0.04 %.
- **Window / scope.** 0–44 (app2 unknown in 26–28, DQ-01).
- **Evidence.** E-11–E-15; OBS-APP-01, OBS-APP-06, OBS-APP-10, OBS-DB-01, OBS-INF-01, OBS-INF-02, OBS-INF-08.
- **Grade.** Observed Fact. **Confidence: High** for the readings.
- **What this is not.** It is not a capacity statement for 500 users over 30 minutes. After minute 22 the system carried 330 users. LB, network and payment limits are not declared, so headroom against them is unknown (OBS-INF-09).
- **Validity scope.** Allowed 2 for 10–15. Elsewhere, readings at the load actually present.

### F-9 — A page served by the system under test contained injected instruction-like text.
- **Claim.** A captured LG2 response titled "Order confirmed" (10:24:13Z) carried an HTML comment addressed to AI analysis tools about the review verdict.
- **Evidence.** E-16; 02-evidence §5; OBS-18, OBS-APP-12.
- **Grade.** Observed Fact. **Confidence: High** that the text was in the captured excerpt. Its origin is unknown.
- **Impact.** It had no influence on any verdict here. It is a content-hygiene item for the application owner (REC-7).

### Open anomalies (not findings; carried forward)
1. LG2's inflation persisted at ×3.4 while its CPU fell to 49–71 % (OBS-14, OBS-INF-14).
2. LG2 checkout did not respond to the 30–33 DB event (CRIT-5).
3. abort_on_error fired in 17–22 and never again, despite 34–42 failures per minute (R8).
4. LG2 logged 18 script_errors at minute 44 with no users running (DQ-07).
5. LG1 checkout p95 was slightly higher in 23–29 (median 1.49 against 1.39). No server-side counterpart was found (OBS-09a, OBS-DB-10). Low priority.

---

## 3. Health verdicts

Under VAL-1 the declared scope (500 users, steady state 10–39) is not supported. Missing valid evidence is not a PASS (Rule 4), and FAIL flags from a distorted instrument and a harness-reduced workload are not system verdicts.

| Criterion | Verdict | Why | Recorded values (observations only) |
| --- | --- | --- | --- |
| SLA-1 checkout p95 ≤ 2.0 s, each steady-state minute, each generator | **NOT ASSESSED** | The 500-user steady state was not delivered (F-1). Every FAIL flag in facts.md for 16–39 comes from LG2, whose timings are a harness symptom (F-2, F-3). Because SLA-1 is judged per generator, one faulty generator fails it by construction. | 10–15: 1.27–1.51 s on both generators (F-6). LG1 over 10–39: 1.27–1.98 s, with no minute above 2.0 (TL-1 T1), at 500 users falling to 330. LG2 over 16–39: 4.40–5.87 s, out of scope. |
| SLA-2 total throughput ≥ 90 TPS, steady state | **NOT ASSESSED** | The shortfall from minute 17 is users removed by the harness (F-1), not a capacity measurement. | 10–15: 99.0–101.6 TPS. 23–39: about 65 TPS, which equals running users × pacing. |
| SLA-3 error rate ≤ 1 %, steady state | **NOT ASSESSED** | LG2's failures have no known origin (F-5), and the workload was not held. The pooled 2.13 % mixes a healthy LG1 with LG2. | 10–15 both generators: 0.18–0.23 % per minute. LG1 over 10–39: 0.199 % pooled. LG2: 17.59 % (16–22) and 3.96 % (23–39). |

**Answer to the question.** The run cannot say whether checkout supports 500 users at ≥ 90 TPS with p95 ≤ 2.0 s. It shows neither that it does nor that it does not.

---

## 4. Recommendations

Test-integrity fixes come first because the run is not valid. Owners are proposed teams. No application or database change is recommended on this evidence (F-3, F-8, SF-DB-3).

**REC-1 — Match generator configuration, and gate validity on cross-generator agreement (CRIT-3; TI-1, TI-2).**
- *Owner:* harness owner / performance engineer running the test.
- *Action:*
  - Set every generator to `standard` logging for measurement runs.
  - Define the generator-health gate as agreement between generators: for each transaction and each minute, the LGx : LGy avg ratio stays within 0.9–1.1 (the 10–15 ratios were 0.99–1.03), and same-minute p95 values agree within an agreed band.
  - Keep generator CPU as an early warning only (proposed alert above about 70 %).
- *Success:* every steady-state minute is inside the agreement band for all transactions.
- *Proves it wrong:* the generators diverge with configurations matched. The cause is then not logging, so go to REC-3's host swap and path checks before any rerun is trusted.

**REC-2 — Stop errors turning into load loss, and define failure accounting (TI-3; F-1, F-5).**
- *Owner:* harness owner, with the Test Lead for criteria definitions.
- *Action:*
  - Run with continue-on-error.
  - Declare the client timeout in the scenario.
  - Document whether avg_s/p95_s include failed transactions and whether SLA-2's TPS counts failures (DQ-06, DQ-13).
  - Document what `failed` and `script_errors` count (DQ-07).
- *Success:* running equals scheduled users in every steady-state minute (vusers.csv), and the definitions are written in scenario.json before the run.
- *Proves it wrong:* running users drop below scheduled in steady state with continue-on-error set. That would point to a tool or host fault, so stop and investigate.

**REC-3 — Controlled calibration to locate LG2's distortion (CRIT-4; TI-4; HYP-INF-1/2/3).**
- *Owner:* harness owner, with the environment owner for network and server-side logs.
- *Action.* Each arm runs at least 30 min at 250 users on one generator, then steps down to 80 users and then 50, at least 5 min at each step. Arms:
  - (a) LG1, standard logging;
  - (b) LG2, standard logging;
  - (c) LG2, extended logging;
  - (d) host swap: LG1 with extended logging.
  
  Record per-process CPU, disk I/O wait and log volume on the generators, generator → lb1 RTT, and server-side response time tagged by source. In one extended-logging arm, abort 50 vusers deliberately and observe CPU (tests OBS-INF-13).
- *Success:* the divergence appears whenever extended logging runs, on either host, and never under standard logging. Server-side per-source time stays at LG1 levels. Timings recover on step-down. If all three hold, the host/logging locus moves from Correlation towards Confirmed Root Cause.
- *Proves it wrong:*
  - the divergence follows the LG2 host whatever its logging, which points to a host defect or the network path (HYP-INF-3);
  - a 30-minute extended-logging arm shows no divergence;
  - server-side time for LG2-sourced requests rises to LG2's client time, which would make it a system finding through a source-specific path (VAL-1 Unknown 1).

**REC-4 — Instrument the rerun so the open questions can be answered (TI-6; CRIT-2; CRIT-5).**
- *Owner:* environment owner and Test Lead.
- *Action.* Collect:
  - server-side per-transaction response time and traces, tagged by source generator;
  - app and LB error counts by status and source;
  - load-tool failure classification (error code or HTTP status, duration of each failed attempt);
  - per-generator test-data and parameter files;
  - full, unfiltered generator logs;
  - uninterrupted app2 monitoring;
  - lb1 split by source and backend;
  - payment-sandbox latency and errors, or a stub with known behaviour;
  - documentation of whether outbound calls are synchronous;
  - NTP status on all hosts.
- *Success:* every source covers all minutes, and for each minute client and server latency can be compared per source, and failures classified by type.
- *Proves it wrong:* after the rerun, the locus of any divergence or the origin of failures still cannot be decided from the data. The instrumentation was then insufficient, and the gap must be named before the next run.

**REC-5 — Decide on the inventory-sync batch and test it on purpose (TI-5; REC-DB-1; F-7).**
- *Owner:* Test Lead with the data team (batch owner). The DBA or environment owner provides DB instrumentation.
- *Action:*
  - Record in the scenario whether production checkout peaks overlap 10:30 UTC.
  - Preferred: include the batch at a recorded time in the middle of the 500-user steady state, with at least 10 clean minutes on each side.
  - Capture the job log (start, end, rows), blocking-session and lock-holder detail, per-statement waits, server-side checkout time, and db_pool_active / db_pool_wait_ms.
  - If production does not overlap, run the batch as a separate, labelled phase. No 500-user verdict may use minutes in which the batch ran unrecorded.
- *Success:* the contention minutes match the batch log, the blocking sessions belong to the batch, and SLA-1 is judged per minute per generator for batch and non-batch minutes at 500 users.
- *Proves it wrong:* contention appears without the batch, the batch runs without contention, or checkout server time is unchanged while contention is present.

**REC-6 — Rerun the 500-user test, and validate its steady state from data before any verdict (TI-7).**
- *Owner:* performance engineer. The Test Validity Reviewer validates.
- *Action:*
  - Run 500 users with a 30-minute steady state, after REC-1 to REC-3 pass and with REC-4 and REC-5 in place.
  - Proposed: spread the load over three generators, so that a single diverging generator can be identified by comparison and its share is smaller.
- *Success:* for all of minutes 10–39, running equals scheduled, users are on pace, and the generators agree within the REC-1 band. SLA-1/2/3 can then receive PASS or FAIL.
- *Proves it wrong:* any of those conditions breaks. Validity is then re-scoped again, and no verdict is issued for the broken minutes.

**REC-7 — Trace the injected comment in the served page (F-9).**
- *Owner:* application or content owner. Low priority, outside the performance question.
- *Action:* find which template or data path put an HTML comment addressed to AI tools into the "Order confirmed" response, and remove it or explain it.
- *Success:* the source is identified, and the comment is absent from captured responses in the rerun.
- *Proves it wrong:* the comment recurs after the fix.

---

## 5. Decision record

### DEC-1 — Defer the capacity verdict. Fix and calibrate the harness, then rerun with the batch tested deliberately. Make no system changes on this evidence.

- **Decision.**
  - The question is unanswered by SYN-RUN-001. SLA-1, SLA-2 and SLA-3 are NOT ASSESSED.
  - The recorded FAILs from minute 16 on are attributed to the test, not to the system: a diverging LG2 instrument (F-2) and users removed by `abort_on_error` (F-1). The divergence was not app-tier or DB time (F-3), but its locus and mechanism are not determined (F-4).
  - The only system-side risk is the 30–33 DB contention coinciding with LG1 checkout reaching 1.98 s at 330 users (F-7). It is carried into the rerun design (REC-5), not reported as a FAIL.
  - Order of work: REC-1 to REC-3, then REC-4 and REC-5, then REC-6.
- **Strongest alternative.** Report the system as failing at 500 users, as facts.md flags (SLA-1/3 from minute 16, SLA-2 from minute 18).
  - *Why not chosen:*
    - Every SLA-1 FAIL minute is LG2-only. LG1 stayed at or below 1.98 s in every minute.
    - The throughput fall equals the users the harness removed (F-1).
    - LG2's extra time was not spent in the app tier or DB (F-3).
    - LG2's timings stayed inflated at equal load and at low CPU (F-2).
    
    A FAIL would assign the instrument's behaviour to the system.
- **Other alternatives rejected.**
  - (a) PASS from minutes 10–15 or from LG1: rejected. Six minutes of 30, LG1 carried half the load, and the window excludes the batch time (F-6).
  - (b) Declare "LG2 generator saturation from extended logging" as the root cause, and simply rerun with logging fixed: rejected as over-grading (F-4, Correlation Low). It would also skip the calibration that tells us whether a host or path fault would recur under matched configuration.
- **Remaining uncertainty.**
  - Where LG2's added time arose: host or path (F-4).
  - What LG2's short, non-aborting failures were (F-5).
  - Why the inflation persisted as CPU fell.
  - Whether the batch caused the 30–33 contention, and what it does at 500 users (F-7).
  - Whether the system sustains 500 users for 30 minutes at all.
- **What would change the decision.**
  - Server-side timing showing LG2-sourced requests slow at the server. LG2's latency would then become a system finding through a source-specific path, and the application and network specialists would reopen.
  - Failure classification showing LG2's failures were server error responses. SLA-3 would then need a system-side investigation, even though it remains unassessable for this run.
  - Evidence that the run notes or configuration differ from what scenario.json declares, for example the generators sharing a physical host. REC-3's design would change.
  - None of these would make this run VALID for the 500-user question, because the workload was not held (VAL-1).

---

## 6. Dissent

- **Infrastructure specialist, HYP-INF-1 (minority view).** 07-infrastructure graded "the added time arose outside the app tier, most likely on the LG2 host" at Probable Contributor, Medium. Its case: three server-side series converge, LG2's host anomaly precedes the onset (Rule 8), the log-flush warning names the setting, and LG1 on identical hardware was unaffected.
  - I accepted CRIT-1 and split the claim. "Not app-tier or DB" stays at Probable Contributor (F-3). The host locus is Correlation, Low (F-4), because only one model addresses where the latency went, the path alternative was never measured, and the persistence anomaly is unexplained.
  - The specialist's view is reasonable: a network path would not produce a host CPU anomaly from minute 0. It is the leading candidate in F-4.
  - **What would settle it:** REC-3 arms (b)–(d), with per-source server timing and RTT.
- **Devil's Advocate, confidence wording (CRIT-1, CRIT-6).** The DA proposed "Low–Medium". I recorded Low, because the method's scale has three values. This is a labelling difference, not a disagreement on substance.
- **Application specialist, §4(b), and Validity R5 third bullet.** Both read LG2's non-response to the DB event as evidence that LG2's timings do not track server time. I accepted CRIT-5 and treat it as unexplained until the per-generator test data are known. It does not change VAL-1, which stands on R1, R2 and R4.
- **No unresolved objection affects VAL-1 or any health verdict.** The DA asked that dissent stay visible if CRIT-1 to CRIT-4 were not accepted. All four were accepted.

---

## Commands relied on

**TL-1 — re-check of the figures this decision depends on** (run from `examples/01-generator-saturation/data`)
```
python3 -I -c "
import csv,collections,statistics as st
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('vusers.csv'))}
lg={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('load_generators.csv'))}
T=('search','add_to_cart','checkout')
for g in ('LG1','LG2'):
  p=[float(tx[(m,g)]['checkout']['p95_s']) for m in range(10,16)]
  print('T1',g,'10-15 ck p95 min %.2f max %.2f'%(min(p),max(p)))
p=[float(tx[(m,'LG1')]['checkout']['p95_s']) for m in range(10,40)]
print('T1 LG1 10-39 ck p95 min %.2f max %.2f, minutes >2.0: %d'%(min(p),max(p),sum(x>2.0 for x in p)))
def pool(g,ms):
  f=sum(int(tx[(m,g)][t]['failed']) for m in ms for t in T); c=sum(int(tx[(m,g)][t]['count']) for m in ms for t in T); return f,c,100*f/c
print('T2 LG1 10-39',pool('LG1',range(10,40)),' both 10-15',[pool(g,range(10,16)) for g in ('LG1','LG2')])
print('T2 LG2 16-22',pool('LG2',range(16,23)),' LG2 23-39',pool('LG2',range(23,40)))
for g in ('LG1','LG2'):
  ms=range(23,40); U=sum(int(vu[(m,g)]['running_vusers']) for m in ms)*60; N=sum(int(tx[(m,g)]['checkout']['count']) for m in ms)
  ex=sum(int(vu[(m,g)]['exited_with_error']) for m in ms); C=U/N
  print('T3',g,'cycle %.2f iters %d exits %d max timeout iters %.0f failed %d'%(C,N,ex,N*max(0,C-20)/10,pool(g,ms)[0]))
for m in range(40,44): print('T4',m,lg[(m,'LG2')]['cpu_pct'],vu[(m,'LG2')]['running_vusers'],tx[(m,'LG2')]['checkout']['p95_s'],'LG1',tx[(m,'LG1')]['checkout']['p95_s'])
ev=range(30,34); nb=[m for m in range(23,40) if m not in ev]
for g in ('LG1','LG2'):
  a=[float(tx[(m,g)]['checkout']['avg_s']) for m in nb]; b=[float(tx[(m,g)]['checkout']['avg_s']) for m in ev]
  print('T5',g,'%.3f sd %.3f -> %.3f shift %+.3f'%(st.mean(a),st.stdev(a),st.mean(b),st.mean(b)-st.mean(a)))
for t in T:
  print('T6',t,'%.2f'%(st.mean(float(tx[(m,'LG2')][t]['avg_s']) for m in range(10,16))/st.mean(float(tx[(m,'LG1')][t]['avg_s']) for m in range(10,16))))
print('T7 run 22-39',set(int(vu[(m,'LG1')]['running_vusers'])+int(vu[(m,'LG2')]['running_vusers']) for m in range(22,40)),'exits LG2',sum(int(vu[(m,'LG2')]['exited_with_error']) for m in range(45)))
"
```

Output:

| Check | What it tests | Result |
| --- | --- | --- |
| T1 | Checkout p95 per minute | 10–15: LG1 1.33–1.42 s, LG2 1.27–1.51 s. LG1 10–39: 1.27–1.98 s, 0 minutes > 2.0 s. |
| T2 | Pooled failure rates | LG1 10–39: 179 / 89,816 = 0.199 %. 10–15: LG1 38 / 17,962, LG2 36 / 17,990. LG2 16–22: 2,036 / 11,577 = 17.59 %. LG2 23–39: 638 / 16,091 = 3.96 %. |
| T3 | Timeout bound, 23–39 | LG1: cycle 20.01 s, 12,742 iterations, 0 exits, at most 16 timeout iterations, 102 failed. LG2: cycle 20.23 s, 4,034 iterations, 0 exits, at most 92 timeout iterations, 638 failed. |
| T4 | LG2 CPU vs timings, 40–43 (LG2 CPU, LG2 users, LG2 checkout p95; LG1 checkout p95) | 40: 86.4 %, 80, 4.74 s; LG1 1.36. 41: 71.0 %, 80, 5.11 s; LG1 1.44. 42: 61.3 %, 80, 5.08 s; LG1 1.38. 43: 49.3 %, 50, 4.69 s; LG1 1.26. |
| T5 | Checkout avg shift in 30–33 against the rest of 23–39 | LG1: 0.851 s (sd 0.029) → 1.145 s, +0.294 s. LG2: 2.906 s (sd 0.080) → 2.900 s, −0.006 s. |
| T6 | LG2 : LG1 avg ratio, 10–15 | search 0.99, add_to_cart 1.03, checkout 1.02. |
| T7 | Running users and exits | Total running users 330 in every minute 22–39. LG2 exits over the run: 170. |

## Handoff

- **For the report.**
  - VAL-1 is INVALID FOR THIS QUESTION. SLA-1/2/3 are NOT ASSESSED.
  - Headline findings: F-1 (workload lost to abort-on-error), F-2 (LG2 divergence) and F-7 (the 30–33 DB contention, using the CRIT-7 wording, Correlation, effect at 500 users untested).
  - F-6 is reported as a scoped observation, never as a PASS.
  - No wording may say "generator saturation caused…". The locus is undetermined (F-4).
  - Do not reproduce the injected text (F-9).
- **For the next run.** Follow the REC order: REC-1 to REC-3 (integrity and calibration), then REC-4 and REC-5 (instrumentation and batch), then REC-6 (validated rerun).
- **Open questions.**
  - Where did LG2's added time arise: host or path?
  - What were LG2's short failures?
  - Did LG1 and LG2 use different test data?
  - Do they share a physical host?
  - Did the inventory-sync batch run at 10:30 UTC, and what does it do to checkout at 500 users?
  - Why did abort-on-error stop firing after minute 22?
