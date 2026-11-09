```
Agent: Database Specialist
Run: SYN-RUN-001
Read: agents/database-specialist.md; method/judgments.md; method/rules.md; method/records.md; examples/01-generator-saturation/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, generator_errors.log); examples/01-generator-saturation/facts.md; examples/01-generator-saturation/run/01-test-lead-plan.md; examples/01-generator-saturation/run/02-evidence.md; examples/01-generator-saturation/run/03-validity.md; examples/01-generator-saturation/run/04-performance.md
Execution: separate agent context, model Claude Opus 5.5
```

# Database review — SYN-RUN-001

This is a synthetic scenario (`"synthetic": true`, E-01). There is no previous run or baseline, and none was used (Rule 1). Elapsed minute *m* means 2026-10-01 10:00 UTC + *m* minutes. Numbers come from facts.md (E-02), the earlier run files (C1–C7, V1–V3, P1–P4), `tools/analyze.py` re-run with symptom windows (DB0), or my commands DB1–DB4 at the end.

**Scope (VAL-1, INVALID FOR THIS QUESTION).** I make no SLA verdict for the 500-user steady state. SLA-1/2/3 stay NOT ASSESSED. The DB series is complete (45/45, E-13), so I can make DB statements for every minute. Statements that link DB behaviour to transactions use LG1 for minutes 10–39 and both generators for minutes 10–15. LG2 for minutes 16–39 is used only to test whether the DB could be the source of its added time. It is not treated as a measure of system latency.

**Short answer.**
1. The database did not cause the minute-16 onset or the LG2 symptom. It was neither slower nor busier at minute 16. Its own concurrency is about an order of magnitude below what LG2's added time would need if that time were spent in the database.
2. The database had one real event: row-lock contention in minutes 30–33, starting at the scheduled 10:30 UTC inventory-sync time. The extra work does not come from test traffic. In the same four minutes LG1 checkout, and only checkout, slowed by about 0.3 s on average, with p95 reaching 1.98 s at 330 users.
3. I recommend no database tuning. The DB is not the constraint for the main symptom, and the lock contention needs query-level evidence before anyone changes anything.

## 1. Time alignment

- database.csv is in server local time, −0400 on all 45 rows. 06:00−0400 = 10:00Z, and 06:30−0400 = minute 30 = 10:30Z. This was verified in DQ-02 and matches my conversion (DB1).
- **Independent alignment check (DB4).** I correlated DB CPU with total test TPS at lags of −2 to +2 minutes, leaving out minutes 29–34. The correlation peaks at lag 0 (r = 0.983) and falls on both sides (0.931 / 0.939 at ±1, 0.837 / 0.793 at ±2). The DB lock-wait series and LG1 checkout avg_s also peak at lag 0 (0.961, against 0.716 / 0.598 at ±1). So the DB clock lines up with the load-tool clock to within one minute. Sub-minute skew cannot be seen (DQ-02, DQ-12).
- **Caveat on that correlation.** The lock-wait correlation comes almost entirely from one 4-minute block. It tells us the block starts and ends in the same minutes on both signals. It is not a dose-response relationship.

## 2. Observations

All of these are Observed Facts unless stated otherwise.

**OBS-DB-01 — DB load tracks test load linearly, outside minutes 30–33.**
- *Claim:* DB CPU fits 5.78 + 0.242 × TPS, with r = 0.990 over minutes 0–43 excluding 30–33 (n = 40). Residuals stay within ±1.5 points (DB2).
- *Shape:* DB CPU follows the ramp: 8.8 % at minute 0, 28.4–31.2 % at about 100 TPS (minutes 10–15), 20.3–23.3 % at about 65 TPS (minutes 23–29 and 34–39), and 6.3 % at minute 44 (DB0, DB1).
- *Window and scope:* all minutes, DB host.
- *Evidence:* E-13, E-03, DB2.

**OBS-DB-02 — DB latency does not change with load.**
- *Claim:* avg_query_ms is 10.0–12.5 ms (median 11.6) in every minute 0–43 outside 30–33, from 10 TPS to 101.6 TPS. Its correlation with TPS is 0.212 (DB2).
- *By window:* 10–15: 10.4–12.4 ms. 16–22: 10.2–12.3. 23–29: 10.2–12.2. 34–39: 10.0–12.5 (DB0).
- *Evidence:* E-13, DB0, DB2.

**OBS-DB-03 — Nothing in the DB changes at minute 16.**
- *Claim:* Minutes 14–18 show DB CPU 28.4 / 28.9 / 29.9 / 29.0 / 25.5 %, sessions 9, avg query 11.3–12.3 ms, lock wait 2–8 ms, and top wait event "CPU" (DB1).
- *Through minute 29:* lock wait stays at 2–8 ms and avg query at 10.2–12.3 ms. The first DB anomaly of any kind is at minute 30, 14 minutes after the LG2 onset at minute 16 (OBS-03 in 04-performance).
- *Evidence:* E-13, E-14, DB0, DB1.

**OBS-DB-04 — Sessions are far from the pool limits, and no idle wait is recorded.**
- *Claim:* DB active_sessions is 4–13 over the whole run (maximum 13, in minutes 30–33), against an application pool total of 40 (2 nodes × 20, E-01).
- *App pools:* db_pool_active is at most 7 per node and db_pool_wait_ms is 0–2 ms in every row present (DB1).
- *Wait events:* "CPU" is the top wait event in 41 of 45 minutes and "row lock contention" in the other 4. No idle-session wait appears.
- *Conclusion:* there is no sign of connections being held but not working.
- *Evidence:* E-11, E-12, E-13, DB1. app2 is unknown for minutes 26–28 (DQ-01).

**OBS-DB-05 — LG2's added time, if it were spent in the DB, would need far more concurrency than the DB had.**
- *Method:* Little's law, applied to how many requests are in flight at once. In-flight work equals arrival rate × time spent. I took LG2's per-transaction rate × (LG2 avg_s − LG1 avg_s) for the same transaction and minute.
- *Result:* this extra in-flight work is 85.8 at minute 16, 74.3 at 17 and 64.5 at 18, then falls to 26.8 by 22 and holds at about 21.5–22.6 in minutes 23–39 (DB2, section A).
- *What the DB had:* active_sessions 9, 9, 9 at minutes 16–18 and 7 at 22–39. App pool active totals were 9–12, under a hard cap of 40, with pool wait 0–2 ms.
- *Why the estimate is a lower bound:* LG2 avg_s probably leaves out failed attempts, including 30 s timeouts (DQ-06), so the real added time is higher.
- *Window and scope:* minutes 16–39, LG2 against the DB.
- *Evidence:* E-03, E-11–E-13, DB2.
- *Grade:* the arithmetic is an Observed Fact. What it implies is in HYP-DB-0.

**OBS-DB-06 — Minutes 30–33: the DB changes state for exactly four minutes.**
- *During 30–33:* lock_wait_ms 921 / 799 / 783 / 902; top wait event "row lock contention"; active_sessions 13; avg_query_ms 20.3 / 19.9 / 20.9 / 20.7; CPU 38.5 / 38.2 / 40.4 / 40.0 %.
- *Either side:* minutes 29 and 34 show lock wait 6 and 3 ms, sessions 7, avg query 11.6 and 10.0 ms, and CPU 22.8 and 22.1 %. Everything reverts fully at minute 34.
- *Timing:* the start matches the scheduled 10:30 UTC inventory-sync batch (E-01). The batch's execution is not recorded (DQ-14).
- *Evidence:* E-14, DB0, DB1.

**OBS-DB-07 — The extra DB work in 30–33 is not explained by test load.**
- *Test load was steady:* total TPS was 64.9–66.5, the same as minutes 29 and 34 (65.6–66.4). LG1 checkout rate was 12.34/s, against 12.54/s in the rest of 23–39 (DB1, DB3).
- *CPU above prediction:* DB CPU was 16.7–18.6 points above the load fit from OBS-DB-01. Elsewhere the residuals are within ±1.5 (DB2).
- *Sessions above app pool use:* DB sessions were 13, while the app pools' active connections summed to 9–11. That is 2–4 more DB sessions than app pool connections. These are the only minutes in the run where that happens. Everywhere else, sessions are 0–5 *below* the pool sum (DB1).
- *Caveat:* the sessions comparison mixes two tools with undocumented sampling (DQ-11, DQ-02), so I treat it as supporting evidence only.
- *Evidence:* E-11–E-14, DB1, DB2.

**OBS-DB-08 — In minutes 30–33, LG1 checkout moves and nothing else does.**
- *LG1 checkout:* avg_s mean 1.145 s, against 0.851 s in the rest of 23–39. That is +0.29 s, or +35 %. Per-minute p95 had median 1.935 and max 1.98 s, against median 1.43 and max 1.53 s (DB3; minutes 30–33 are the only LG1 minutes that trip the onset rule, P1).
- *Other LG1 transactions:* search (avg 0.593 against 0.601) and add_to_cart (0.395 against 0.402) do not move. LG1 checkout failures stay at 0.20 %, against 0.22 %.
- *Error log:* one excerpt line at 10:31:02Z reports LG1 vuser 12 checkout at 3.4 s (E-16, DQ-04).
- *Window and scope:* 30–33, LG1, at 330 total users and about 65 TPS.
- *Evidence:* E-04, E-16, DB3, P1.

**OBS-DB-09 — Two signals the lock-wait mechanism predicts do not appear.**
- *(a) No rise in held app connections or threads.* If checkouts were waiting on row locks while holding a pooled connection, the extra time would show as extra held connections. At 12.34 LG1 checkouts/s × 0.29 s, that is about 3.6 extra in-flight checkouts. Instead, app1 db_pool_active was 4–5 in 30–33, against 4–6 in 23–29 and 34–39. app2 was 5–6 against 5–6. Active threads were 16–19, against 16–20 (DB3). Pool wait stayed at 0–2 ms.
- *(b) No shift in LG2 checkout.* LG2 checkout avg_s was 2.900 s in 30–33, against 2.906 s in the rest of 23–39, and LG2 p95 median was 4.69 against 4.74 (DB3; also V2, OBS-12).
- *Caveats:* the app gauges are per-minute samples with undocumented semantics (DQ-11). LG2 is a distorted instrument in this window (VAL-1).
- *Evidence:* E-11, E-12, E-05, DB3.

**OBS-DB-10 — The DB is quiet when LG1 p95 is slightly raised in minutes 23–29 (SW-5).**
- *Claim:* in 23–29, LG1 checkout p95 median was 1.49 s, and the DB showed lock wait 2–7 ms, avg query 10.2–12.2 ms, sessions 7, CPU on the load fit, and wait event "CPU" (DB0, DB1, DB2).
- *Conclusion:* the DB shows no counterpart to that small rise.
- *Evidence:* E-13, DB0–DB2.

**OBS-DB-11 — DB resource readings at full load, minutes 10–15 only.**
- *Readings:* CPU 28.4–31.2 %, sessions 9–10, avg query 10.4–12.4 ms, lock wait 2–8 ms, wait event "CPU" (DB0).
- *Limits:* this covers six minutes at 500 users and contains no batch window. It is a resource reading, not a capacity statement (allowed claim 2, 03-validity).
- *Evidence:* E-13, DB0.

## 3. Hypotheses and negative claims

### HYP-DB-0 — The database is not implicated in the minute-16 onset or in LG2's inflated timings (minutes 16–43)

- **Claim:** The DB did not slow down or become constrained at minute 16. LG2's added time in minutes 16–39 was not spent in the database.
- **Evidence:**
  - *Timing (Rule 8):* the DB was unchanged at minute 16, and its first anomaly came 14 minutes later (OBS-DB-03).
  - *Latency:* DB latency was flat across load and windows (OBS-DB-02).
  - *Load:* DB load tracked test load, not the symptom. CPU fell with the lost users (OBS-DB-01).
  - *Sessions and pools:* sessions stayed well below pool limits with no idle wait and pool waits of 0–2 ms (OBS-DB-04).
  - *Concurrency:* LG2's added time would need at least 65–86 concurrent DB calls in minutes 16–18, and about 22 in minutes 23–39. The DB had 7–9 sessions, and the app pools cannot exceed 40 (OBS-DB-05).
  - *Shared DB:* the DB serves both app nodes, and LG1 showed no change at minute 16 (04-performance OBS-03).
  - *Minutes 30–33:* when the DB *did* degrade, LG2 timings did not move (OBS-DB-09b). That is the opposite of what a DB-bound LG2 symptom would show.
- **Grade:** Observed Fact for each DB measurement. The exclusion is an inference from DB-layer evidence (Rule 9), not from missing data.
- **Confidence:** High that the DB was not slower or busier at the onset. The series is complete, the time alignment is checked (DB4), and several independent DB metrics agree.
  - High that LG2's added time was not *DB* time. The concurrency gap is about tenfold, and the 40-connection cap makes it impossible.
  - One assumption carries the second claim: all application DB access goes through the recorded pools. No other path is documented.
- **Alternatives considered:**
  - *LG2-specific test data hitting a slow query or hot rows.* Set aside. That would show up as extra sessions or held pool connections (OBS-DB-05) and as lock waits (2–8 ms in 16–29). Neither appears.
  - *DB contention at sub-minute scale that the per-minute series hide.* Cannot be excluded at sub-minute scale. But it could not produce a ×3–4 inflation lasting 28 minutes on every LG2 transaction while the per-minute averages stay flat.
- **What would change this:** query-level or server-side traces showing LG2-sourced requests waiting in the DB.

### HYP-DB-1 — A non-test workload, most likely the inventory-sync batch, caused the row-lock contention in minutes 30–33

- **Claim:** In minutes 30–33 a workload outside the test traffic ran on the DB and produced the row-lock contention. Its start time matches the inventory-sync batch scheduled for 10:30 UTC.
- **Window:** minutes 30–33 (10:30–10:33 UTC). **Scope:** DB host.
- **Evidence:**
  - *Timing:* the contention starts in the minute of the schedule, with alignment checked to within one minute (OBS-DB-06, DB4, DQ-02).
  - *Extra work:* DB CPU was about 17–19 points above what the steady test load predicts (OBS-DB-07).
  - *Extra sessions:* DB sessions exceeded app pool connections only in these minutes (OBS-DB-07).
  - *Steady test traffic:* test TPS and mix were unchanged, so the extra work did not come from the test (DB1, DB3).
- **Grade:**
  - *A non-test workload caused the contention:* **Probable Contributor.** The mechanism is plausible: a bulk writer takes row locks. Three independent DB signals converge, and test-load change is ruled out. The gap is that there is no lock-holder or statement data (DQ-05f).
  - *That workload was the inventory-sync batch:* **Correlation**. The only link is the schedule. Execution is not recorded (DQ-14).
- **Confidence:** Medium. The DB signals agree and alignment is verified. But there is no job log or blocking-session record, and the sessions comparison crosses two tools (DQ-11).
- **Alternatives:**
  - *Another unscheduled job, ad-hoc query or DB maintenance task.* Not excluded, because no job or activity log exists. Kept open.
  - *A hot-row pattern in the test traffic.* Set aside. Test TPS, mix and checkout rate were flat, and the extra CPU and sessions exceed what the test load explains.
  - *Clock skew making a coincidence look aligned.* Set aside to within one minute (DB4).
- **Confirming experiment:** see REC-DB-1. Record the batch's start and end and the DB's blocking-session and lock-holder detail. Success means the blocking sessions in the contention window belong to the batch's DB user, and contention starts and ends with the batch log. The hypothesis is disproved if contention appears without the batch, or the batch runs without contention.

### HYP-DB-2 — The row-lock contention slowed checkout in minutes 30–33

- **Claim:** The lock contention added about 0.29 s to LG1 checkout avg (+35 %) and raised LG1 checkout p95 to 1.78–1.98 s for four minutes. Search and add_to_cart were not affected.
- **Window:** minutes 30–33. **Scope:** LG1 checkout, at 330 users and about 65 TPS.
- **Evidence:**
  - Start and end match exactly, with lag 0 the best alignment (OBS-DB-06, OBS-DB-08, DB4).
  - Only checkout moves, which is consistent with checkout touching rows the batch locks (OBS-DB-08). This is an assumption: there is no query or table data.
  - The app tier shows no other change in this window (04-performance OBS-13).
- **Grade:** **Correlation.** It is not raised to Probable Contributor, because two predictions of the mechanism are not met and are not yet explained (OBS-DB-09):
  - (a) Held app pool connections and threads do not rise by the roughly 3–4 the added checkout time implies.
  - (b) LG2 checkout shows no shift.
  - Both have candidate explanations: (a) sampled gauges with undocumented semantics (DQ-11); (b) LG2 measurement distortion (VAL-1). Neither has been tested.
- **Confidence:** Medium. The windows are aligned and the signal comes from a healthy client source, LG1. Against that: the mechanism has unmet predictions, there is no server-side checkout timing (DQ-05), and there is no query-level data.
- **Alternatives:**
  - *A coincident slowdown in another checkout dependency, such as the payment sandbox, in the same four minutes.* Cannot be excluded, because there are no payment metrics (DQ-05). It would need an unlikely exact coincidence with the DB window.
  - *Checkout waits on locks without holding a pooled connection* (for example, a separate connection path for inventory reservation). Unknown. This is a question for Application.
- **Effect size against the criterion:**
  - At 330 users, LG1 checkout p95 peaked at 1.98 s (minute 32). That is 0.02 s under the SLA-1 threshold of 2.0 s.
  - The rise in p95 median was +0.5 s over four minutes (DB3). No transaction failures were added (0.20 % against 0.22 %).
  - What this does at 500 users is **unknown**. Contention usually grows with concurrent writers, but this run gives no basis for a number, and extrapolation is restricted (03-validity, restricted claim 9).
  - In the only 500-user window (minutes 10–15) checkout p95 was 1.27–1.51 s. That window did not contain the batch.
- **Confirming experiment:** REC-DB-1. This needs server-side checkout time and DB lock-wait detail per statement in a run where the batch runs at a recorded time. The claim is disproved if checkout server-side time does not rise during the recorded batch-driven contention, or if it rises equally without it.

## 4. Secondary findings

- **SF-DB-1 — A scheduled DB workload overlaps the checkout steady state and brings LG1 checkout p95 to within 0.02 s of SLA-1 at two-thirds load** (HYP-DB-1, HYP-DB-2). This is the one system-side risk the valid scope shows. It is a risk to be tested at 500 users, not a FAIL.
- **SF-DB-2 — DB headroom at full load in minutes 10–15 (six minutes only).**
  - CPU was 28.4–31.2 % at about 100 TPS.
  - Sessions were 9–10, against a pool total of 40.
  - Query latency was flat at 10–12 ms (OBS-DB-11).
  - No DB constraint was observed at 500 users in that window. This is not a capacity statement.
- **SF-DB-3 — No DB tuning is recommended.** No DB evidence shows the DB constraining the main symptom (HYP-DB-0). For the lock contention, the next step is evidence (REC-DB-1), not changes to indexes, isolation levels or batch SQL.

## 5. Recommendation on the batch for the rerun (Test Lead question)

**REC-DB-1 (proposed; the Test Lead assigns it).**

- **Owner:** Test Lead, with the data team, which owns the batch (E-01). The DBA or environment owner provides DB instrumentation.
- **Decision first.** The batch is daily at 10:30 UTC. If production checkout peaks overlap 10:30 UTC, the batch is part of the real production profile, and leaving it out would overstate capacity. If production does not overlap, the batch is a confound. Either way the choice must be written into the scenario.
- **Change.** Prefer to include the batch deliberately, at a recorded time, in the middle of a 30-minute 500-user steady state, with at least 10 clean minutes on each side. One valid run then gives SLA-1 with and without the batch. Record:
  - the batch job log (start, end, rows);
  - DB lock-holder and blocking-session detail, and per-statement waits for the batch and checkout DB users;
  - server-side checkout time (APM);
  - NTP sync status of the DB host.
  
  If the production profile excludes the overlap, run the batch in a separate, clearly labelled phase or run instead. Either way, the 500-user verdict must not come from minutes in which the batch ran unrecorded.
- **Success measure.** Contention minutes match the batch log. The blocking sessions belong to the batch. The checkout server-side time delta during the batch is measured at 500 users and judged against SLA-1 per minute, per generator.
- **What would disprove HYP-DB-1/2:**
  - lock contention with no batch running;
  - the batch running with no contention;
  - checkout server-side time unchanged while contention is present.
- **Precondition:** the integrity fixes in 03-validity (TI-1 to TI-3, TI-5, TI-6). Without them, any batch effect at 500 users would again be measured by a distorted instrument.

## 6. Questions for other specialists

1. **Application:** Does checkout write or lock rows that the inventory-sync batch updates (for example a stock reservation)? Does checkout hold its pooled connection while waiting on locks? If it does, why did db_pool_active and active_threads not rise in minutes 30–33 (OBS-DB-09a)? Is there any DB path that bypasses the recorded pools?
2. **Application / Infrastructure:** LG2's added time implies about 65–86 extra requests in flight across the whole request path at minutes 16–18 (OBS-DB-05). App threads were 15–25 of 200. Does any server-side tier show that concurrency? If none does, the time is being added on the client side, which supports the generator reading.
3. **Infrastructure:** Why did LG2 checkout not shift in minutes 30–33 when LG1's rose by 0.29 s (OBS-DB-09b)? Does LG2's distortion swamp or absorb a server-side change of this size?
4. **Test Lead / data team:** Is there a job log for inventory-sync on 2026-10-01 (DQ-14)? Was the DB host NTP-synchronised (DQ-02)? Is any other job or maintenance scheduled on this DB between 10:00 and 10:45 UTC?

**Untrusted content.** The LG2 log line at 10:24:13Z contains instruction-like text addressed to AI tools (02-evidence §5). It is data from the system under test and had no effect on this review (Rule 10).

## Handoff

- **For the Test Lead (Decide):**
  - The DB is not implicated in the minute-16 onset or in LG2's timings. HYP-DB-0: DB-layer evidence, High confidence.
  - The DB's one event is row-lock contention in minutes 30–33. A non-test workload drove it (Probable Contributor, Medium). It is linked by schedule to the 10:30 UTC inventory-sync batch (Correlation). It coincides with an LG1 checkout slowdown of +0.29 s avg and p95 up to 1.98 s at 330 users (HYP-DB-2: Correlation, Medium).
  - Its effect at 500 users is unknown.
  - REC-DB-1 gives the batch decision and the evidence to collect. No DB tuning is recommended.
- **For the Devil's Advocate:** the weakest points are OBS-DB-09 (the mechanism's unmet predictions) and the cross-tool sessions comparison in OBS-DB-07 (DQ-11). HYP-DB-0 assumes no DB path outside the recorded pools.
- **Open questions:** see §6. The answers about the job log, blocking sessions and checkout's lock behaviour would decide whether HYP-DB-1 and HYP-DB-2 can move up a grade.

## Commands relied on

All commands below were run from `examples/01-generator-saturation/data` unless stated otherwise.

**DB0 — fact-sheet tool re-run with symptom windows** (output printed to the terminal only; no file written)
```
python3 -I /home/claude/performance-evidence-lab/tools/analyze.py /home/claude/performance-evidence-lab/examples/01-generator-saturation/data --windows 10-15 16-22 23-29 30-33 34-39 | grep -A30 "### database.csv"
```
Output (database.csv, min/mean/max):
- 10–15: CPU 28.4/29.72/31.2, sessions 9/9.33/10, avg_query 10.4/11.53/12.4, lock 2/5.5/8.
- 16–22: CPU 21.4/25.07/29.9, sessions 7/8.14/9, avg_query 10.2/11.41/12.3, lock 2/5.0/8.
- 23–29: CPU 20.3/21.4/22.9, sessions 7/7/7, avg_query 10.2/11.16/12.2, lock 2/4.86/7.
- 30–33: CPU 38.2/39.27/40.4, sessions 13/13/13, avg_query 19.9/20.45/20.9, lock 783/851.25/921.
- 34–39: CPU 20.6/22.18/23.3, sessions 7/7/7, avg_query 10.0/11.57/12.5, lock 2/5.33/8.

**DB1 — per-minute DB (UTC), total TPS, DB CPU/TPS, sessions against app pool sum, LG1 latency**
```
python3 -I -c "
import csv,collections,statistics as st
from datetime import datetime,timezone
t0=datetime(2026,10,1,10,tzinfo=timezone.utc)
db={}
for r in csv.DictReader(open('database.csv')):
  t=datetime.strptime(r['window_start_local'],'%Y-%m-%dT%H:%M:%S%z'); db[int((t-t0).total_seconds()//60)]=r
ap={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open('app_servers.csv'))}
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
tps=lambda m: sum(int(x['count']) for g in ('LG1','LG2') for x in tx[(m,g)].values())/60 if (m,'LG1') in tx else 0
for m in range(45):
  d=db[m]; a1=ap.get((m,'app1')); a2=ap.get((m,'app2'))
  p1=int(a1['db_pool_active']) if a1 else None; p2=int(a2['db_pool_active']) if a2 else None
  ps=p1+p2 if p1 is not None and p2 is not None else None
  T=tps(m); l1=tx.get((m,'LG1'),{})
  print(m,'%.1f'%T,d['cpu_pct'],'%.3f'%(float(d['cpu_pct'])/T) if T else '-',d['active_sessions'],p1,p2,ps,(int(d['active_sessions'])-ps) if ps is not None else '-',a1['db_pool_wait_ms'] if a1 else '-',a2['db_pool_wait_ms'] if a2 else 'MISSING',d['avg_query_ms'],d['lock_wait_ms'],d['top_wait_event'],l1.get('checkout',{}).get('avg_s'),l1.get('checkout',{}).get('p95_s'),l1.get('search',{}).get('avg_s'))
"
```
Key output:
- Sessions minus app pool sum: −1 to −5 in every minute where both nodes are present, except minute 44 (0) and minutes 30–33 (+3, +3, +2, +4).
- Pool wait 0–2 ms on every row.
- app2 missing at minutes 26–28.
- Minutes 14–18: DB CPU 28.4, 28.9, 29.9, 29.0, 25.5; sessions 9; avg query 11.3–12.3; lock 2–8; event CPU.
- Minutes 30–33: TPS 65.2 / 64.9 / 66.1 / 66.5, DB CPU/TPS 0.589–0.611, against 0.309–0.353 in 23–29 and 34–39.
- LG1 checkout p95 1.97 / 1.78 / 1.98 / 1.90.

**DB2 — Little's law on LG2's added time; DB CPU against TPS fit; DB latency ranges**
```
python3 -I -c "
...same loading as DB1...
T=('search','add_to_cart','checkout')
for m in list(range(14,24))+[30,39]:
  ex=sum(int(tx[(m,'LG2')][t]['count'])/60*(float(tx[(m,'LG2')][t]['avg_s'])-float(tx[(m,'LG1')][t]['avg_s'])) for t in T)
  ... print m, LG2 tps, ex, db sessions, app pool sum
ms=[m for m in range(44) if m not in (30,31,32,33)]
x=[tps(m) for m in ms]; y=[float(db[m]['cpu_pct']) for m in ms]
# least-squares fit y=a0+b*x, st.correlation(x,y); residuals for 29-34 and range outside 30-33
# avg_query and lock_wait ranges outside 30-33; corr(tps, avg_query); per-window ranges and wait events
"
```
Output:
- *Little's law:* extra in-flight from LG2's added time: minute 14: 1.5; 15: 0.1; 16: 85.8; 17: 74.3; 18: 64.5; 19: 48.3; 20: 37.3; 21: 28.3; 22: 26.8; 23: 22.5; 30: 21.5; 39: 22.6. Against DB sessions 9, 9, 9, 9, 9, 8, 8, 7, 7, 7, 13, 7, and pool sums 14, 13, 12, 11, 10, 11, 11, 9, 9, 10, 10, 10.
- *Fit:* cpu = 5.78 + 0.242 × TPS, r = 0.990, n = 40.
- *Residuals:* 30: +16.9; 31: +16.7; 32: +18.6; 33: +18.1; 29: +0.9; 34: +0.4. Outside 30–33: −1.5 to +1.5.
- *Latency outside 30–33:* avg_query 10.0–12.5 (median 11.6), lock 2–8, corr(TPS, avg_query) = 0.212. Wait event "CPU" in every window except 30–33.

**DB3 — effect size by window, per generator and transaction; app pools and threads around the DB event**
```
python3 -I -c "
...loading as DB1...
W={'23-29':range(23,30),'30-33':range(30,34),'34-39':range(34,40),'23-39 excl 30-33':[m for m in range(23,40) if m not in range(30,34)]}
for g in ('LG1','LG2'):
  for t in ('search','add_to_cart','checkout'):
    for k,w in W.items():
      av=[float(tx[(m,g)][t]['avg_s']) for m in w]; p=[float(tx[(m,g)][t]['p95_s']) for m in w]
      f=sum(int(tx[(m,g)][t]['failed']) for m in w); c=sum(int(tx[(m,g)][t]['count']) for m in w)
      print(g,t,k,'avg mean %.3f p95 med %.3f max %.2f fail %.2f%% ck/s %.2f'%(st.mean(av),st.median(p),max(p),100*f/c,c/60/len(w)))
# per-minute 26-37: app1/app2 db_pool_active, active_threads, db_pool_wait_ms, cpu_pct
"
```
Key output (p95 values are median/max of per-minute values, never pooled):
- *LG1 checkout:* 30–33 avg 1.145, p95 1.935 / 1.98, fail 0.20 %, 12.34/s. The rest of 23–39: avg 0.851, p95 1.43 / 1.53, fail 0.22 %, 12.54/s. 23–29: p95 median 1.49.
- *LG1 search:* avg 0.593 against 0.601. *LG1 add_to_cart:* 0.395 against 0.402.
- *LG2 checkout:* 30–33 avg 2.900, p95 4.69 / 4.90. Rest of 23–39: 2.906, 4.74 / 5.19.
- *app1 db_pool_active:* 30–33 [5, 5, 5, 4], against 4–6 elsewhere in 23–39. *app2:* 5–6 against 5–6. *Threads:* 16–19 against 16–20. *Pool wait:* 0–2.

**DB4 — time-alignment lag check**
```
python3 -I -c "
...loading as DB1...
ex=set(range(29,35))
for lag in (-2,-1,0,1,2):
  ms=[m for m in range(2,42) if m not in ex and m+lag not in ex]
  print(lag, st.correlation([tps[m] for m in ms],[float(db[m+lag]['cpu_pct']) for m in ms]))
for lag in (-1,0,1):
  ms=[m for m in range(20,43) if 0<=m+lag<44]
  print(lag, st.correlation([float(db[m]['lock_wait_ms']) for m in ms],[LG1 checkout avg_s at m+lag for m in ms]))
"
```
Output:
- *DB CPU against TPS:* lag −2: 0.837; −1: 0.931; 0: 0.983; +1: 0.939; +2: 0.793.
- *DB lock wait against LG1 checkout avg:* lag −1: 0.716; 0: 0.961; +1: 0.598.
