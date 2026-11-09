```
Agent: Database Specialist
Run: SYN-RUN-002
Read: agents/database-specialist.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/ (scenario.json, transactions.csv, app_servers.csv, database.csv, checkout_traces.csv; other data files not opened beyond what facts.md summarises); examples/02-connection-pool/facts.md; examples/02-connection-pool/run/01-test-lead-plan.md; examples/02-connection-pool/run/02-evidence.md; examples/02-connection-pool/run/03-validity.md; examples/02-connection-pool/run/04-performance.md
Execution: separate agent context, model Claude Opus 5.5
```

Data note: `scenario.json` marks this dataset as synthetic. It is analysed here as though it were a real run.

**Scope.** VAL-1 is VALID WITH LIMITATIONS (`03-validity.md`). I analyse the database during this run in PERF-A, including minutes 19–39 as system behaviour under a caller-side payment-latency excursion (AC-5, AC-6). I give no capacity verdict (RC-1, RC-2), I do not say the sandbox caused anything (RC-3, RC-4), and I do not order DB signals against app-tier signals at one-minute resolution (RC-9, DQ-06). Evidence IDs (E-, DQ-, OBS-, SW-) are from `02-evidence.md` and `04-performance.md`. New numbers come from commands DB1 and DB2 in the appendix (rule 3).

## Summary

**What the database did not do.** In minutes 19–29 and 34–39 the database did not get slower, did not work harder per transaction, and did not wait on locks. Its CPU, mean query latency and lock wait stayed inside the minutes 10–18 reference range, and DB CPU per transaction/s was unchanged. Sampled checkout SQL time stayed at 25–59 ms in every window. No DB signal moved before onset. What changed is that the database held 40 sessions, exactly the two app pools' maximum, and their top state was "idle in transaction". The connections were held, not working. The database was being waited *for*, not waited *on*.

**Minutes 30–33 are a separate, real DB episode.** There was row lock contention, query latency doubled, DB CPU rose by about 15 points and there were 6 sessions above what the app pools can open. It starts 11 minutes after onset, so it cannot explain onset (rule 8). Sampled checkout SQL, connection hold time, checkout p95 and TPS show no measurable change in those minutes.

**No database tuning is recommended**, because nothing shows the database was the constraint.

## 1. Time alignment (Test Lead D1)

**OBS-DB-01: The UTC conversion is correct. The minute-19 session value cannot be used for ordering.**
- All 45 rows of `database.csv` carry offset -0400. 06:00-0400 to 06:44-0400 converts to 10:00Z to 10:44Z = elapsed minutes 0–44, with no gaps or duplicates (DB1; agrees with `02-evidence.md` §2). All DB minutes below are elapsed minutes on that basis.
- At onset, DB active_sessions is 9 at minute 19, while the app pools sum to 17 + 17 = 34. The DB reaches 40 at minute 20. At recovery, the DB (8) and the pools (7 + 5 = 12) drop in the same minute, 40 (DB1). A fixed clock offset would lag at both transitions, so this is not a clock offset (DQ-06).
- **Candidate explanation (unverified):** the DB export takes a point sample at or near the start of each window, while APM reports a value over the minute. That would fit both transitions:
  - the 10:19:00 DB sample falls before the first degraded trace at 10:19:10, and APM pool active of 17/17 rather than 20/20 at minute 19 suggests a minute that was only partly degraded;
  - the 10:40:00 DB sample would follow a recovery between the last degraded trace (10:39:44) and 10:40:00 (OBS-13).
- Metric semantics are undocumented (DQ-07), so this stays a candidate. It only explains the mismatch; it does not license ordering. **DQ-06 stands: DB and app signals are compared over multi-minute windows only.**

*Window:* 0–44. *Evidence:* E-08, E-06, E-07, E-11, DQ-06, DQ-07; DB1. Observed Fact for the conversion. The sampling explanation is an untested idea, Low confidence: semantics are undocumented.

## 2. Observations

**OBS-DB-02: Reference window, minutes 10–18** (DB1).

| Metric | Range per minute |
| --- | --- |
| DB CPU | 26.8–29.3% (mean 28.1%) |
| active_sessions | 9–10 |
| avg_query_ms | 10.1–12.0 |
| lock_wait_ms | 2–8 |
| top_wait_event | CPU in every minute |
| DB CPU per TPS | 0.277–0.293 (window mean CPU / window TPS = 0.282) |

Sessions are 3–5 below the app pool sum (13–14) in these minutes (DB1). The DB and APM count connections differently at low use; the semantics are undocumented (DQ-07).
*Evidence:* E-08, E-06, E-07, E-13. Observed Fact.

**OBS-DB-03: No database signal moves before or at onset.** In minutes 14–19 every DB metric stays inside its 10–18 range: CPU 27.0–29.3%, avg_query 10.4–11.9 ms, lock_wait 2–5 ms, top event CPU (DB1). At minute 19 the DB shows CPU 27.0%, avg_query 11.3 ms, lock_wait 4 ms, top event CPU. Nothing in the DB precedes the minute-19 change. Under OBS-DB-01 the minute-19 row may itself be a pre-onset sample, so it shows only that the DB was normal up to onset, not what it did during onset.
*Window:* 14–19. *Evidence:* E-08, E-16; DB1. Observed Fact, at one-minute resolution.

**OBS-DB-04: In the degraded windows outside 30–33, the database does the same work per transaction at the same speed** (DB1).

| Window | DB CPU % | avg_query_ms | lock_wait_ms | TPS (window) | DB CPU / TPS (window) |
| --- | --- | --- | --- | --- | --- |
| 10–18 (reference) | 26.8–29.3 | 10.1–12.0 | 2–8 | 99.6 | 0.282 |
| 20–29 | 24.5–28.7 | 10.1–12.3 | 3–8 | 93.9 | 0.285 |
| 34–39 | 23.5–25.8 | 10.9–12.1 | 2–8 | 85.6 | 0.290 |

- Per minute, DB CPU per TPS is 0.275–0.303 throughout 20–29 and 34–39, against 0.277–0.293 in the reference window.
- DB CPU **falls** as TPS falls: the 34–39 mean is 24.8%, against 28.1% in the reference window.
- Query latency is flat while checkout p95 rises from about 1.4 s to about 7 s (OBS-05).
- Rising application latency with flat database latency and flat database cost per transaction points away from the database (role file).

*Window:* 10–29, 34–39. *Evidence:* E-08, E-13; DB1. Observed Fact.

**OBS-DB-05: Sessions are pinned at exactly the app pool total, and the top state is "idle in transaction".**
- In every minute of 20–29 and 34–39 (16 minutes), DB active_sessions = 40 = app1 pool active 20 + app2 pool active 20 = 2 × `db_pool_max_per_node` (DB1; E-01).
- "idle in transaction" is the top event in exactly those 16 minutes and in no other minute (`02-evidence.md` A2).
- "Idle in transaction" means a client has opened a transaction on the session, is not running a statement, and has not committed. The session is waiting for the client, not for the database. **The connections are held by the application, open but not working.**
- What the application was doing while it held them is not visible from the DB. The traces show it for sampled checkouts (OBS-DB-06).

*Window:* 20–39. *Evidence:* E-08, E-06, E-07, E-01; DB1. Observed Fact. Interpreting the event name as "client-side wait" depends on the export using the standard meaning of that state; the export does not define it (DQ-07).

**OBS-DB-06: Checkout SQL time does not change. SQL is about 2% of connection hold time in the degraded windows** (DB2).

| Window | Traces | SQL ms, median (range) | Hold ms, median | SQL share of hold (medians) | Checkouts/s | Busy-SQL connections ≈ checkouts/s × SQL median |
| --- | --- | --- | --- | --- | --- | --- |
| 10–18 | 27 | 42 (25–59) | 313 | 13.4% | 24.98 | 1.05 |
| 20–29 | 30 | 37.5 (25–57) | 2027 | 1.9% | 23.47 | 0.88 |
| 30–33 | 12 | 44.5 (30–56) | 1919.5 | 2.3% | 21.40 | 0.95 |
| 34–39 | 18 | 40 (25–57) | 2034.5 | 2.0% | 21.45 | 0.86 |
| 40–43 | 12 | 40.5 (25–57) | 333.5 | 12.1% | 12.43 | 0.50 |

- None of the 63 traces in 19–39 has SQL above the reference maximum of 59 ms. Across the whole run, SQL is 25–59 ms.
- Hold minus payment call is 45.5–60 ms (median) in every window. Connection hold is SQL plus the payment call plus a few tens of ms (see also `02-evidence.md` A4).
- From checkout alone, the database is kept busy executing statements by about one connection's worth of work at any moment, in every window. Meanwhile 40 connections are held in 20–39.

*Window:* 10–43, sampled checkouts. *Evidence:* E-11, E-12, E-02, E-03, DQ-08; DB2. Observed Fact for the sampled requests. The concurrency figure is a Little's Law estimate: it assumes the sample median represents the population (DQ-08), and it covers checkout statements only.

**OBS-DB-07: Pool-demand cross-check (Test Lead A2, DB side).** Checkouts/s × median sampled hold time (DB2):
- **10–18:** 7.8 connections, against a pool sum of 13–14 and DB sessions of 9–10. Other transactions also use connections.
- **20–29:** 47.6. **30–33:** 41.1. **34–39:** 43.6. All against a hard cap of 40.

Demand from checkout alone is at or above the combined pool maximum, which fits a pool pinned at 20/20 with requests queueing for it. A 40-connection pool cannot sustain more than 40 concurrent holds, so the 3–19% excess is not physical. It shows the limits of the inputs: a deterministic 3-per-minute sample (DQ-08), undocumented bucketing (DQ-07), and an assumed even split across nodes. The estimate supports "demand at or above the cap", not a precise figure. The detailed per-node calculation is the application specialist's (A2).
*Window:* 10–39. *Evidence:* E-02, E-03, E-06, E-07, E-11, E-12; DB2. This is a calculation, not a measurement. Medium confidence for "at or above the cap".

**OBS-DB-08: Minutes 30–33 are a database episode with exact edges** (DB1).

| Metric | 26–29 | 30–33 | 34–39 |
| --- | --- | --- | --- |
| top_wait_event | idle in transaction | row lock contention | idle in transaction |
| lock_wait_ms | 3–8 | 683–800 (800, 781, 683, 734) | 2–8 |
| avg_query_ms | 10.3–12.3 | 19.2–20.2 | 10.9–12.1 |
| DB CPU % | 24.5–25.0 | 42.2–44.5 | 23.5–25.8 |
| DB CPU / TPS (per minute) | 0.281–0.294 | 0.496–0.512 | 0.275–0.303 |
| active_sessions | 40 | 46 | 40 |

- Both app pools are at their configured max of 20 in all of 30–33 (DB1). So **the 6 sessions above 40 cannot come from those two pools.** Some other client connected to the database.
- DB CPU rises by about 15–20 points while TPS is flat or falling (84.2–86.9). The extra work is not driven by the checkout load.
- Under DQ-06, the edges are known to the minute only.
- The inventory-sync batch is scheduled for 10:30 UTC = minute 30 (E-01). Whether it ran is unknown (DQ-10b).

*Window:* 26–39. *Evidence:* E-08, E-17, E-06, E-07, E-13, E-01; DB1. Observed Fact.

**OBS-DB-09: The lock episode has no measurable effect on checkout.**

| Signal | 26–29 | 30–33 | 34–37 / 34–39 | Source |
| --- | --- | --- | --- | --- |
| Trace SQL ms, median (range) | 40.5 (25–54) | 44.5 (30–56) | 34.5 (25–56), 34–37 | DB2 |
| Trace connection hold ms, median | 2199 | 1919.5 | 1990.5, 34–37 | DB2 |
| Trace pool wait ms, median | 1593.5 | 1759.5 | 1847.5, 34–37 | DB2 |
| APM pool wait, both nodes | 1,438–1,702 | 1,645–1,820 | 1,598–1,806, 34–39 | OBS-06 |
| Checkout p95 median LG1 / LG2 | 7.01 / 7.25 s | 6.85 / 7.04 s | 7.20 / 7.05 s, 34–36 | OBS-10 |
| TPS per minute | 85.1–88.8 | 84.2–86.9 | 85.2–85.8, 34–39 | E-13 |

- All 12 sampled checkouts in 30–33 have SQL of 30–56 ms, inside the 25–59 ms range seen in every other window. Each trace is listed in DB2.
- A checkout statement held up by lock waits of the size the DB reports (683–800 ms) would show in sql_ms.
- With 12 traces, an effect on 22% or more of checkouts would have had at least a 95% chance of showing in at least one trace if the sample were random (DB2). The sample is deterministic (seconds :10/:27/:44; DQ-08), so this is a guide, not a bound.
- APM pool wait in 30–33 is slightly above 26–29 and level with 34–39. Pool wait was still rising through 19–29 (OBS-06), so the difference cannot be attributed to the episode.
- **Effect size against the criteria:** checkout p95 (SLA-1) and TPS (SLA-2) in 30–33 are within the range of the neighbouring windows, and both were already failing. No measurable effect on any criterion.

*Window:* 26–39. *Evidence:* E-11, E-12, E-02, E-03, E-06, E-07, E-13, DQ-08; DB2. Observed Fact for the sampled requests and the per-minute values.

**OBS-DB-10: The database returns to its reference state with the app tier.** At minute 40 (400 users): sessions 8, top event CPU, avg_query 11.3 ms, lock_wait 4 ms, CPU 24.1% (DB1). In minutes 40–43, avg_query is 10.3–11.3 ms. The DB shows no residual state after recovery.
*Window:* 39–43. *Evidence:* E-08, E-16; DB1. Observed Fact.

## 3. Hypotheses

**HYP-DB-1: The database is not implicated in the onset or in the degradation of minutes 19–29 and 34–39.**
- **Claim:** neither database load, database latency nor database lock waits caused or added to the checkout slowdown outside 30–33.
- **Evidence (positive, not absence):**
  - No DB signal moves before or at onset (OBS-DB-03).
  - DB query latency is flat (10.1–12.3 ms against 10.1–12.0 ms reference) while checkout p95 rises about fivefold (OBS-DB-04, OBS-05).
  - DB CPU per transaction/s is unchanged (0.285 and 0.290 against 0.282), and DB CPU falls as throughput falls (OBS-DB-04).
  - Lock wait stays at 2–8 ms (OBS-DB-04).
  - Sampled checkout SQL stays at 25–59 ms (OBS-DB-06).
  - Sessions sit at exactly the pool total in a client-wait state (OBS-DB-05).
- **Grade:** this is a negative claim, so the cause grades do not apply directly. The supporting statements are Observed Facts from two independent sources (DB host export and APM traces) that agree.
- **Confidence:** High that DB latency, CPU per transaction and lock waits did not rise in these windows: coverage is complete for 30/30 minutes and two sources agree. Medium that the database is not implicated at all, because:
  - avg_query_ms is a host-wide mean, and the dataset has no per-statement or per-session data (DQ-10c). A slow subset could hide in the mean, although checkout's own SQL is directly shown flat.
  - search and add_to_cart have no traces, so their DB time is seen only through that host-wide mean.
  - Metric semantics are undocumented (DQ-07).
- **Alternatives considered:**
  - *DB slower under load:* set aside, since latency and cost per transaction are flat.
  - *DB lock waits from onset:* set aside, since lock wait is 2–8 ms outside 30–33.
  - *DB CPU saturation:* set aside, since CPU stays at or below 29.3% outside 30–33.
  - *A DB event at onset hidden by the one-minute lag:* not excluded at sub-minute resolution. However, the DB looks the same in 20–29 as in 10–18 on every metric except sessions, so any such event left no trace in latency, CPU or locks.
- **Confirming experiment:** EXP-DB-1 below.

**HYP-DB-2: The two app pools fill because connections are held idle inside open transactions across a non-database wait. Sampled traces show that wait to be the payment call.**
- **Claim:** pool exhaustion, and the pool wait that is part of checkout response time in 19–39, comes from connection hold time, not database execution time.
- **Mechanism:**
  - A checkout opens a transaction, runs about 40 ms of SQL and keeps the connection while the payment call runs.
  - Hold time rises from about 313 ms to about 2,000 ms.
  - Checkout demand reaches or exceeds the 40-connection cap.
  - The DB sees 40 sessions mostly idle in transaction.
- **Evidence:**
  - Sessions equal the pool total and the top state is "idle in transaction" (OBS-DB-05).
  - SQL is about 2% of hold time in the degraded windows (OBS-DB-06).
  - Hold minus payment call is about 50 ms in every window (OBS-DB-06; `02-evidence.md` A4).
  - Little's Law demand is at or above the cap (OBS-DB-07).
  - Trace median pool wait is 1,198.5–1,847.5 ms in 20–39 (DB2), against a total of about 3.6 s (`facts.md`).
- **Grade:** Probable Contributor, for pool queueing in 20–39. The mechanism is plausible, several sources converge, and the alternatives in HYP-DB-1 are addressed. There is no controlled change, so it is not Confirmed.
- **Confidence:** Medium. The traces are a deterministic sample of 3 per minute (DQ-08). There are no per-session DB data to show directly that the idle sessions are the checkout transactions. Whether search and add_to_cart hold transactions the same way is unknown.
- **Gaps and limits:**
  - This explains why the pool filled. It does not explain why payment latency rose at minute 19. That is outside the database and outside what this run can decide (RC-3, RC-4).
  - The data cannot say whether payment latency or pool exhaustion came first (OBS-04).
  - The application specialist owns the code-path claim; this file gives the database evidence for it.
- **Alternatives considered:**
  - *Connection leak:* set aside for now. Sessions return to 8 within one minute at recovery (OBS-DB-10), and the pool returns to 7/5, which a leak would not do.
  - *Long-running SQL holding connections:* set aside, since SQL is 25–59 ms.
- **Confirming experiment:** EXP-DB-2 below.

**HYP-DB-3: The minutes 30–33 lock episode comes from a database client other than the two app pools, consistent with the inventory-sync batch.**
- **Evidence:**
  - 6 sessions above a pool total that is at its configured max (OBS-DB-08).
  - DB CPU rises about 15–20 points with no rise in TPS (OBS-DB-08).
  - The start matches the 10:30 UTC schedule to the minute (E-01).
  - Sampled checkout SQL is unaffected, which suggests the lock waits fell mainly on statements other than sampled checkout SQL (OBS-DB-09).
- **Grade:** Correlation: timing plus session count.
- **Confidence:** Low. There is no batch log (DQ-10b) and no lock holder or waiter identity (DQ-10c). Another application component or maintenance job with its own connections is not excluded (DQ-10f). Who blocked whom is unknown.
- **Alternatives:**
  - *(a) The batch's sessions waited on each other or on rows the batch itself touched.*
  - *(b) The batch waited on rows locked by checkout transactions that stayed open about 2 s while idle in transaction.* This is possible only if checkout writes or locks rows before the payment call, which is unknown. If true, the long hold in HYP-DB-2 would also lengthen any batch that touches checkout's rows.
  - *(c) Some checkout statements did wait but fell outside the sample.* This is bounded only loosely (OBS-DB-09).
- **Confirming experiment:** EXP-DB-3 below.

## 4. Secondary findings

1. **The lock episode is real but has no measurable effect on checkout in this run** (OBS-DB-08, OBS-DB-09).
   - In 30–33, DB query latency roughly doubled, lock waits reached 683–800 ms and DB CPU reached 42.2–44.5%.
   - Effect on SLA-1 and SLA-2 is not measurable: p95 and TPS stay within their neighbours' range, and both criteria were already failing.
   - It cannot explain onset, which came 11 minutes earlier (rule 8).
   - In a run without the payment excursion it might matter more. This run cannot say.
   - It is also the only time in the run the database did meaningfully more work.
2. **Long open transactions.** For about 20 minutes, 40 sessions sat mostly idle in transaction (OBS-DB-05), with each checkout transaction open for about 2 s instead of about 0.3 s (OBS-DB-06).
   - Open transactions keep any row locks they have taken and hold back cleanup of old row versions for their duration.
   - This run shows no harm from that beyond pool occupancy: lock wait is 2–8 ms and query latency is flat outside 30–33.
   - It is a design property worth knowing for the batch interaction in HYP-DB-3(b).
3. **The database host did not approach saturation in any minute.** Peak DB CPU is 44.5% (minute 32). Outside 30–33 the peak is 29.3% (DB1). This is an observation about this run, not a capacity statement (RC-2).

## 5. What database evidence is missing (Test Lead D4)

Each item is unknown, not absent (rule 4):
- Per-statement or per-query statistics: which statements ran, how often and how long. This leaves search and add_to_cart DB time visible only through the host-wide mean (DQ-10c).
- Per-session state over time: state, transaction start time, client application or address. This would show directly that the 40 sessions are the app pools and how long each transaction stayed open (DQ-10c).
- Lock holder and waiter identity for 30–33 (DQ-10c).
- Inventory-sync batch log: whether it ran, start, end, tables and session count (DQ-10b).
- Sampling semantics of every `database.csv` metric: point or mean, which instant, and what active_sessions and top_wait_event count (DQ-07). This would resolve DQ-06.
- DB throughput (statements or transactions per second) from the DB side. CPU per TPS is used here as a proxy.

## 6. Experiments (rule 12)

These are proposals for the Test Lead's recommendations. None is a database tuning change.

- **EXP-DB-1 (tests HYP-DB-1).**
  - **Owner:** DBA with the Test Lead.
  - **Change:** none to the database. In the rerun under T-1 (stubbed payment, stepped latency 250 ms → 1 s → 2 s at 500 users), capture per-statement statistics and 10-second session-state snapshots.
  - **Success measure:** DB avg query time and DB CPU per transaction/s stay within the 10–18 reference range (10.1–12.0 ms; about 0.28) at every latency step.
  - **Proves it wrong:** DB latency or DB cost per transaction rises with injected latency at constant user load, or any statement's mean time rises materially between steps.
- **EXP-DB-2 (tests HYP-DB-2).**
  - **Owner:** DBA with the application specialist.
  - **Change:** same rerun, with session snapshots that include transaction start time and client identity.
  - **Success measure:** at the 1 s and 2 s steps, sessions in "idle in transaction" rise to the pool total. Those sessions belong to the app pools, and their transaction ages track the injected payment latency, while SQL time stays at about 25–59 ms.
  - **Proves it wrong:** sessions are mostly active (executing) or waiting on locks, or pool exhaustion appears without idle-in-transaction sessions.
  - **Follow-on:** if the application team changes the code to release or commit the connection before the payment call, the same test should show sessions stay near the reference level (about 9–14) at every latency step.
- **EXP-DB-3 (tests HYP-DB-3).**
  - **Owner:** data team with the DBA.
  - **Change:** run inventory-sync deliberately in a declared window during a controlled test (fixed-latency stub, 500 users), with the batch log and lock holder/waiter snapshots captured. Keep it out of the capacity test's steady state otherwise (T-3).
  - **Success measure:** the extra sessions and the lock waits belong to the batch, and checkout SQL time and p95 in the batch window stay within the no-batch window's range.
  - **Proves it wrong:**
    - Lock waiters include checkout statements, or checkout p95 or SQL time rises in the batch window. The batch then does affect checkout.
    - Or the row lock contention appears without the batch. HYP-DB-3 is then wrong about the source.

## 7. Questions for other specialists

- **Application (A1, A2):**
  - Does checkout open its DB transaction before the payment call, and does it write or lock any rows before the call? This decides HYP-DB-3(b).
  - Do search and add_to_cart take connections from the same pool, and do they hold transactions open? That would explain their slowdown (OBS-05) as pool queueing rather than DB time.
- **Application / platform:** does any application component other than the two app pools connect to this database, such as a second pool, a scheduler or an admin tool? That bears on the 6 extra sessions in 30–33.
- **Infrastructure / APM owner:** what are the sampling semantics of `database.csv`? Is each value a point at window start, a mean or a max? Confirming point-at-start would resolve DQ-06 (OBS-DB-01).
- **Data team (via Test Lead):** did inventory-sync run on 2026-10-08? When did it start and end, and which tables and how many sessions did it use?

## Handoff

- **Database verdict for this run:** not implicated in onset or in minutes 19–29 and 34–39 (HYP-DB-1). This rests on database evidence: latency, CPU per transaction, lock wait and checkout SQL time all stay at reference levels. Confidence is High for those measurements and Medium for "not implicated at all", because there is no per-statement or per-session data.
- **For the application specialist:** the database supports HYP-DB-2 (Probable Contributor, Medium). Sessions are pinned at exactly 40 = 2 × 20 and idle in transaction. SQL is about 2% of hold time. Demand from checkout alone is at or above the cap. The question of what drives the hold, and the ordering at onset, stays with you and with VAL-1's U-2.
- **For the Test Lead:**
  - Minutes 30–33 are a real DB episode with a non-app-pool source (HYP-DB-3, Correlation, Low). There is no measurable effect on checkout or on SLA-1 and SLA-2 (OBS-DB-09), and it cannot explain onset.
  - Do not recommend database tuning.
  - Recommend EXP-DB-1 to EXP-DB-3 alongside T-1 and T-3, and the DB instrumentation in §5 as part of T-4.
- **For the Devil's Advocate:** the weakest points are:
  - avg_query_ms is a host-wide mean, and only checkout has direct SQL timing.
  - The OBS-DB-09 "no effect" rests on 12 deterministic traces and per-minute p95 values.
  - The OBS-DB-07 Little's Law figures exceed 40, which shows the limits of the sampled inputs.
- **Not done:** no one-minute DB-vs-app ordering, no run-level p95, no capacity statement, nothing from SYN-RUN-001.

## Appendix: commands run

Scripts are in `/tmp/db/`, outside `data/`, run with `python3 -I` and the data folder as an argument.

**DB1. DB per-minute table against pool sum and TPS; window summaries** (`python3 -I /tmp/db/d1.py <data>`)
```python
import csv,sys,statistics as st
from datetime import datetime,timezone
D=sys.argv[1]
s=datetime(2026,10,8,10,tzinfo=timezone.utc)
B={}
for r in csv.DictReader(open(D+'/database.csv')):
    t=datetime.strptime(r['window_start_local'],'%Y-%m-%dT%H:%M:%S%z')
    B[int((t-s).total_seconds()//60)]=r
print('offsets',set(r['window_start_local'][-5:] for r in B.values()),'minutes',min(B),max(B),len(B))
A={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open(D+'/app_servers.csv'))}
T={}
for r in csv.DictReader(open(D+'/transactions.csv')):
    m=int(r['elapsed_min']); T[m]=T.get(m,0)+int(r['count'])
for m in range(14,45):
    b=B[m]; p1=int(A[(m,'app1')]['db_pool_active']); p2=int(A[(m,'app2')]['db_pool_active'])
    tps=T.get(m,0)/60
    print(m,b['cpu_pct'],b['active_sessions'],b['avg_query_ms'],b['lock_wait_ms'],b['top_wait_event'],'|',p1,p2,p1+p2,
          int(b['active_sessions'])-(p1+p2),'|',round(tps,1),round(float(b['cpu_pct'])/tps,3) if tps else '-')
W=[(10,18),(19,19),(20,29),(30,33),(34,39),(40,43)]
for a,c in W:
    ms=range(a,c+1); f=lambda k:[float(B[m][k]) for m in ms]
    tps=sum(T[m] for m in ms)/(60*len(ms)); cpu=f('cpu_pct')
    print('W',a,c,'cpu',min(cpu),max(cpu),round(st.mean(cpu),1),'sess',min(f('active_sessions')),max(f('active_sessions')),
          'q',min(f('avg_query_ms')),max(f('avg_query_ms')),'lock',min(f('lock_wait_ms')),max(f('lock_wait_ms')),
          'TPS',round(tps,1),'meanCPU/TPS',round(st.mean(cpu)/tps,3),'events',set(B[m]['top_wait_event'] for m in ms))
```
Key outputs:
- Offsets {'-0400'}, minutes 0–44, 45 rows.
- Per minute, minutes 14–18: sessions 9–10, pool sum 13–14, CPU/TPS 0.277–0.293.
- Minute 19: CPU 27.0, sessions 9, q 11.3, lock 4, CPU event; pool 17 + 17 = 34.
- Minutes 20–29 and 34–39: sessions 40, pool 20 + 20 = 40, diff 0, CPU/TPS 0.275–0.303.
- Minutes 30–33: sessions 46, diff +6, lock 800/781/683/734, q 20.2/19.2/19.2/20.1, CPU 42.5/44.0/44.5/42.2, CPU/TPS 0.496–0.512.
- Minute 40: sessions 8, pool 7 + 5.
- Windows:

| Window | CPU min–max (mean) | Sessions | avg_query | lock_wait | TPS | CPU/TPS |
| --- | --- | --- | --- | --- | --- | --- |
| 10–18 | 26.8–29.3 (28.1) | 9–10 | 10.1–12.0 | 2–8 | 99.6 | 0.282 |
| 20–29 | 24.5–28.7 (26.8) | 40 | 10.1–12.3 | 3–8 | 93.9 | 0.285 |
| 30–33 | 42.2–44.5 (43.3) | 46 | 19.2–20.2 | 683–800 | 85.7 | 0.505 |
| 34–39 | 23.5–25.8 (24.8) | 40 | 10.9–12.1 | 2–8 | 85.6 | 0.290 |
| 40–43 | 10.8–24.1 (17.6) | 5–8 | 10.3–11.3 | 4–8 | 50.1 | 0.352 |

**DB2. Trace SQL, hold and pool wait by window; Little's Law estimates; lock-window traces** (`python3 -I /tmp/db/d2.py <data>`)
```python
import csv,sys,statistics as st
D=sys.argv[1]
R=list(csv.DictReader(open(D+'/checkout_traces.csv')))
C={}
for r in csv.DictReader(open(D+'/transactions.csv')):
    if r['transaction']=='checkout':
        m=int(r['elapsed_min']); C[m]=C.get(m,0)+int(r['count'])
W=[(10,18),(19,19),(20,29),(26,29),(30,33),(34,37),(34,39),(40,43)]
for a,b in W:
    s=[r for r in R if a<=int(r['elapsed_min'])<=b]
    g=lambda k:[int(r[k]) for r in s]
    sql=g('sql_ms'); held=g('db_connection_held_ms'); pay=g('payment_call_ms'); pw=g('pool_wait_ms')
    nonpay=[h-p for h,p in zip(held,pay)]
    cps=sum(C[m] for m in range(a,b+1))/(60*(b-a+1))
    print('W',a,b,'n',len(s),'sql',st.median(sql),min(sql),max(sql),'held med',st.median(held),
          'held-pay med/max',st.median(nonpay),max(nonpay),'poolwait med',st.median(pw),'checkout/s',round(cps,2),
          'LL conns',round(cps*st.median(held)/1000,1),'busy-SQL conns',round(cps*st.median(sql)/1000,2),
          'SQL share %',round(100*st.median(sql)/st.median(held),1))
ref=max(int(r['sql_ms']) for r in R if 10<=int(r['elapsed_min'])<=18)
print('ref sql max',ref,'traces 19-39 above',sum(1 for r in R if 19<=int(r['elapsed_min'])<=39 and int(r['sql_ms'])>ref))
for r in R:
    if int(r['elapsed_min']) in (29,30,31,32,33,34):
        print(r['timestamp_utc'][11:],r['node'],r['sql_ms'],r['db_connection_held_ms'],r['payment_call_ms'],r['pool_wait_ms'],r['total_ms'])
n=sum(1 for r in R if 30<=int(r['elapsed_min'])<=33)
print('n 30-33',n,'f at which P(miss all)=0.05:',round(1-0.05**(1/n),3))
```
Key outputs:

| Window | n | SQL med (min–max) | Held med | Held − pay med | Pool wait med | Checkouts/s | LL conns | Busy-SQL conns | SQL share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10–18 | 27 | 42 (25–59) | 313 | 57 | 0 | 24.98 | 7.8 | 1.05 | 13.4% |
| 19 | 3 | 40 (31–59) | 2417 | 53 | 359 | 25.00 | 60.4 | 1.00 | 1.7% |
| 20–29 | 30 | 37.5 (25–57) | 2027 | 54.5 | 1198.5 | 23.47 | 47.6 | 0.88 | 1.9% |
| 26–29 | 12 | 40.5 (25–54) | 2199 | 56.5 | 1593.5 | 21.88 | 48.1 | 0.89 | 1.8% |
| 30–33 | 12 | 44.5 (30–56) | 1919.5 | 56.5 | 1759.5 | 21.40 | 41.1 | 0.95 | 2.3% |
| 34–37 | 12 | 34.5 (25–56) | 1990.5 | 45.5 | 1847.5 | 21.56 | 42.9 | 0.74 | 1.7% |
| 34–39 | 18 | 40 (25–57) | 2034.5 | 51 | 1835.5 | 21.45 | 43.6 | 0.86 | 2.0% |
| 40–43 | 12 | 40.5 (25–57) | 333.5 | 60 | 0 | 12.43 | 4.1 | 0.50 | 12.1% |

- Reference SQL max is 59 ms; 0 of the traces in 19–39 exceed it. All-run SQL is 25–59 ms.
- Traces in minutes 30–33 (time, node, SQL ms):
  - 10:30:10 app1 43; 10:30:27 app2 34; 10:30:44 app1 33
  - 10:31:10 app1 46; 10:31:27 app2 45; 10:31:44 app1 52
  - 10:32:10 app1 35; 10:32:27 app2 30; 10:32:44 app1 44
  - 10:33:10 app1 56; 10:33:27 app2 50; 10:33:44 app1 52
- n(30–33) = 12. The affected fraction at which a random sample would miss every affected checkout with 5% probability is 0.221.
