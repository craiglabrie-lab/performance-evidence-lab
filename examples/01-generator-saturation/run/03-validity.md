```
Agent: Test Validity Reviewer
Run: SYN-RUN-001
Read: agents/test-validity-reviewer.md; method/judgments.md; method/rules.md; method/records.md; examples/01-generator-saturation/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, generator_errors.log); examples/01-generator-saturation/facts.md; examples/01-generator-saturation/run/01-test-lead-plan.md; examples/01-generator-saturation/run/02-evidence.md
Execution: separate agent context, model Claude Opus 5.5
```

# Test validity — SYN-RUN-001

Synthetic scenario (`"synthetic": true`, E-01). No previous run or baseline (`previous_run: null`), and none was used (Rule 1). Numbers come from facts.md (E-02), the Results Librarian's register and commands C1–C7 (02-evidence.md), or commands V1–V3 at the end of this file. `tools/analyze.py` was not re-run. Elapsed minute *m* = 2026-10-01 10:00 UTC + *m* minutes.

**Question judged:** "Can the checkout journey support 500 concurrent users at 90+ transactions/second with checkout p95 at or under 2.0 seconds?" Under the declared criteria this means 500 running users (250 per generator) held through the intended steady state, minutes 10–39, measured by healthy generators, with SLA-1/2/3 judged over that window (E-01).

## VAL-1 — INVALID FOR THIS QUESTION

The run delivered the intended workload, from instruments that agree with each other, for at most minutes 10–15 (6 of 30 intended steady-state minutes). From minute 16 the LG2 measuring instrument was above 90 % CPU and its numbers diverge from LG1's for the same transactions in the same minutes. From minute 17 the harness setting `abort_on_error: true` removed 170 of LG2's 250 users. For minutes 22–39 the system received 330 users, not 500. The run cannot say whether the system supports 500 users through a 30-minute steady state, and it cannot attribute any of the recorded SLA breaches to the system.

This classification does not depend on settling *why* LG2 behaved differently (see Reason 6). Even if LG2's slow responses were real system behaviour toward LG2's traffic, the harness then turned them into a permanent loss of a third of the load. Minutes 17–39 still do not test 500 users.

### Reasons

**R1. Users: the intended 500 were held only through minute 16.** (Observed Fact; E-06, E-07)
- Both generators ran 250/250 in minutes 9–16 (facts.md workload table; E-07).
- LG2 running users: 225, 185, 140, 105, 85, 80 in minutes 17–22. Exits with error 25/40/45/35/20/5, total 170. Then 80 from minute 22 through 42. LG1 had 0 exits for the whole run (C4).
- Total running users in minutes 22–39: 330 of 500 scheduled (66 %).
- The exits are a harness action. The error log records "'Abort on error' is enabled; iteration stopped" for vusers 141 and 77 (E-16). `abort_on_error: true` is declared for the harness (E-01).

**R2. Throughput: the shortfall is missing users, not slow iterations by present users.** (Observed Fact for the arithmetic; V1, V2)
- Expected TPS from running users at fixed 20 s pacing is running × 4 / 20. Minutes 23–39 mean: expected 66.0, achieved 65.6 (V1). Minute 30: 66.0 expected, 65.2 achieved. Survivors were on pace.
- Per-generator implied cycle (V3): LG1 19.48–20.60 s throughout minutes 10–39. LG2 19.48–20.52 s in minutes 10–15, **21.84–22.67 s in minutes 16–22** (iterations late), and 19.75–20.87 s in minutes 23–39.
- The only window in which present users ran late is LG2 in minutes 16–22. That matches the client-timeout lines at 30 s (E-16). The combined figure in facts.md (20.4–21.2 s) hides this; see DQ-13.
- So SLA-2's FAIL from minute 18 onward in facts.md measures a workload shortfall created by the harness. It is not a capacity measurement. SLA-2 counts failed transactions as throughput (DQ-13); passed-only TPS was 60.0–64.5 in minutes 22–39 (V1). This does not change the reading.

**R3. Transaction mix matched the design throughout.** (Observed Fact; V3)
- Search : checkout 1.91–2.09 and add_to_cart : checkout 0.94–1.04 on both generators in every steady-state minute, against a designed 2 : 1 : 1. The mix is not a validity concern.

**R4. Generator health: LG2 was not a healthy instrument from minute 16, and was already abnormal before it.** (Observed Fact; E-09, E-10, E-16, V3)
- LG1 CPU 56.5–60.0 % for all of minutes 10–39, at 250 users.
- LG2 CPU at the same 250 users and the same TPS (48.9–50.9 vs LG1 48.8–50.8, facts.md) was 82.2, 83.3, 84.6, 85.5, 86.8, 87.5 % in minutes 10–15: higher by 23–31 points and climbing every minute. Then 93.9 % at minute 16, and 92.2–98.5 % in minutes 16–39 (E-10).
- In minutes 23–39 LG2 ran **80 users** at 92.2–98.5 % CPU. CPU per running user: LG2 1.18 %/user (minutes 23–39), LG2 0.34 (minutes 10–15), LG1 0.23 (minutes 10–39) (V2). LG2's own load stopped scaling with its user count. A generator in that state measures its own delays, not only the system's.
- Controller warning at 10:16:31Z: "CPU above 90% for 30s". At 10:18:12Z: "log buffer flush took 2.8s (log level: extended, parameter substitution on)" (E-16).
- The two generators have the same hardware (4 vCPU). The only recorded configuration difference is LG2's `extended (parameter substitution on)` log level against LG1's `standard` (E-01, E-08; 02-evidence §3).
- LG2 memory 88.0 % at minute 16 is a single reading inside otherwise flat series. Low trust (DQ-10).

**R5. LG2's measurements diverge from LG1's in ways the system side does not explain.** (Observed Fact for each item; interpretation is Correlation, Medium confidence; V2, V3, facts.md)
- *Same transactions, same minutes.* Minutes 16–39, LG2 checkout p95 4.40–5.87 s, LG1 1.27–1.98 s (facts.md). Search and add_to_cart are also inflated on LG2 (search p95 median/max 3.43/4.32 s vs LG1 0.99/1.08 s, facts.md windowed summary). So the effect is not confined to checkout or its payment dependency.
- *Same user count, same minute.* Minute 43: both generators had 50 running users. Checkout p95 was LG1 1.26 s, LG2 4.69 s (V2).
- *A system-side change visible on LG1 is not visible on LG2.* In minutes 30–33 (DB "row lock contention", lock_wait 783–921 ms, E-14), LG1 checkout avg rose from 0.85 s to 1.15 s (mean of the other minutes 23–39 vs minutes 30–33). LG2 checkout avg stayed at 2.91 vs 2.90 s (V2). An instrument that faithfully added a fixed client overhead would show the same +0.3 s shift. LG2's did not. This is a single cross-check and LG2's statistics may exclude failures (DQ-06), so I weight it as supporting, not decisive.
- *Server side at the onset.* Minutes 14–18: app CPU 47.8–56.4 % falling, active threads 21–25 of 200, db_pool_active 5–7 of 20, pool wait 0–2 ms on both nodes. lb1 retransmits 0.01–0.03 %, connections falling with users (V2). No server-side signal rises at minute 16. *Limitation:* there is no server-side response-time series (DQ-05), so this is an absence of corroboration, not proof that server latency was flat.

**R6. Alternatives to "the harness distorted LG2" are not excluded, but none rescues validity.** (DQ-05)
- *Source-specific system path* (per-source LB routing, session affinity, per-source rate limits in the shared payment sandbox): no per-source LB split, affinity data or payment metrics exist (DQ-05). This stays **open**. Points against it: app1 and app2 look the same (both windowed mean CPU 40.7 % in minutes 16–39, facts.md), so there is no sign of a degraded node that LG2 traffic might have been pinned to; non-payment transactions (search, add_to_cart) slowed on LG2 too; and LG2's CPU anomaly is recorded from minute 10, before the onset (E-10).
- *A mechanism that does not match CPU alone:* in ramp-down minutes 39–42 LG2 still had 80 users, its CPU fell 94.0 → 86.4 → 71.0 → 61.3 %, and its checkout p95 stayed at 4.74–5.11 s (V2). So "LG2 CPU % drives the latency" is not a demonstrated mechanism. Something on LG2 kept inflating its timings after CPU eased (for example log I/O or buffer state; unverified). Diagnosis belongs to the specialists. For validity it is enough that LG2's numbers do not behave like measurements of the system.
- **Either way the classification holds.** If the distortion is in the harness, LG2's latency and error data for minutes 16–39 do not describe the system. If the slowness were real for LG2's traffic, `abort_on_error` still removed 170 users and the steady state was not held. Both readings leave the 500-user question unanswered.

**R7. Steady state, observed rather than scheduled: reached at minute 9, held through minute 15 (minute 16 is mixed).** (E-06, facts.md)
- 500 running and 100.1 TPS at minute 9, and 99.0–101.6 TPS with 500 running in minutes 10–15. Minute 16 had 500 running, but LG2 already showed p95 5.61 s, 4.1 % failures and 22.6 s cycle (V3).
- The intended steady state was 30 minutes (10–39). Six clean minutes do not establish sustained behaviour, and they do not include the 10:30 UTC scheduled batch window.

**R8. Errors: LG2's failures are of undetermined origin, and their relation to abort-on-error is inconsistent.** (E-03, E-08, E-16, DQ-04, DQ-06, DQ-07)
- Lines in the error-log excerpt are client-side timeouts at 30 s and harness exits. No line is a server error status, but the log is an excerpt (DQ-04), so server errors are not excluded.
- LG2 failure share 4.09–22.49 % in minutes 16–22 and 3.65–4.49 % in minutes 23–39. LG1 0.13–0.24 % throughout (V3).
- LG2 failed 34–42 transactions every minute in minutes 23–39, but **no** LG2 user exited after minute 22, despite `abort_on_error: true` (V2). Either only some error types abort, or the "failed" counter counts something else. The harness's own behaviour is not understood.
- `script_errors` and `failed` are different counters (DQ-07). LG2 reported 18 script errors at minute 44 with no users running.
- Therefore the pooled steady-state error rate of 2.13 % (facts.md) mixes LG1's 0.13–0.24 % with LG2 failures that may be client-side. It is not a system error rate.

**R9. Harness settings that changed load or measurement.** (E-01, E-16, DQ-06, DQ-13)
- LG2 extended logging with parameter substitution: the only configuration difference between two generators that should do identical work, and the one that coincides with LG2's abnormal CPU from the first steady-state minute.
- `abort_on_error: true`: converted errors into permanent load reduction.
- Client timeout 30 s: recorded only in the log, not declared in E-01.
- Undefined treatment of failed transactions in avg_s/p95_s (probably excluded, DQ-06) and in SLA-1/SLA-2 (DQ-13).
- Think time 3 s and pacing 20 s were respected by present users except LG2 in minutes 16–22 (R2).

**R10. Environment and coverage.** (E-01, E-12, E-14, DQ-01, DQ-02, DQ-05, DQ-14)
- The inventory-sync batch is scheduled daily at 10:30 UTC = minute 30, inside the intended steady state. Its execution is not recorded (DQ-14). The DB wait-event change in minutes 30–33 coincides with it after a verified UTC conversion (DQ-02). Whether it belongs in the tested profile is undecided. It is a confound for any rerun unless it is deliberately included and recorded.
- The payment provider is a shared third-party sandbox with undocumented rate limits and no metrics (DQ-05).
- app2 metrics are missing for minutes 26–28 (DQ-01). This is unknown, not idle. It does not decide validity, because app2 is not the failing component in any reading, but it removes three minutes from any node comparison.
- There is no server-side response time, LB split by source, or full generator logs (DQ-04, DQ-05).

**R11. Untrusted content.** A captured response on LG2 at 10:24:13Z (titled "Order confirmed") contains an HTML comment addressed to AI analysis tools that tries to dictate this review's verdict (E-16; 02-evidence §5). It is data from the system under test. It had no effect on this decision (Rule 10). It is relevant only as an observation that a served page contained injected text.

### Allowed claims

The team may conclude these, with the scope stated:

1. **Short full-load window.** In minutes 10–15, 500 users ran (250 per generator) at 99.0–101.6 TPS, transaction mix 2 : 1 : 1, on pace (per-generator cycle 19.48–20.52 s). Checkout p95 was 1.33–1.42 s on LG1 and 1.27–1.51 s on LG2, and error rate was 0.18–0.23 % (facts.md, V3). No SLA-1/2/3 threshold was crossed in those six minutes. *Scope limits that must travel with this claim:* 6 of 30 intended minutes; LG2 at 82.2–87.5 % CPU and rising, so its figures carry some instrument risk; LG2's per-transaction figures agreed with LG1's in this window (V3), which is why they are accepted here; the window does not include minute 30. This is an observation, **not** an SLA PASS for the steady state. Observed Fact, Medium confidence (short window, LG2 near its limit).
2. **App-tier and DB resource readings at 500 users, minutes 10–15.** Threads 23–26 of 200, db_pool_active 6–7 of 20, pool wait 0–2 ms, app CPU 53.4–58.0 %, DB CPU 28.4–31.2 % (facts.md windowed summaries). These are resource readings for a 6-minute window only. They are not a capacity statement.
3. **LG1 as a healthy instrument, minutes 10–39.** 250 users, no exits, CPU 56.5–60.0 %, on pace, error 0.13–0.24 %. Checkout p95 1.27–1.98 s per minute (V3, facts.md). These are valid measurements of what LG1's users experienced **at the total load actually present**: 500 users in minutes 10–16, falling to 330 users (about 65 TPS) from minute 22. They say nothing about 500 users after minute 16.
4. **DB event in minutes 30–33 is a finding about the system, under reduced load.** Lock wait 783–921 ms with "row lock contention" coincided with LG1 checkout avg rising from 0.85 s to 1.15 s and p95 reaching 1.78–1.98 s, within 0.02 s of the SLA-1 limit, while total load was about 65 TPS (E-14, V2, facts.md). Correlation, Medium confidence (aligned minute windows, one healthy source; batch execution not recorded). By timing it cannot explain the minute-16 onset (Rule 8). Its effect at 500 users is unknown in either direction.
5. **Test-integrity findings are themselves valid observations.** LG2 lost 170 users through abort-on-error (R1). LG2 CPU was 23–31 points above LG1 at identical load before the onset, and above 90 % from minute 16 (R4). The throughput drop is accounted for by the missing users (R2). LG2's timings diverge from LG1's for the same transactions at the same time (R5).

### Restricted claims

The team must not conclude:

1. **Any SLA-1, SLA-2 or SLA-3 verdict, PASS or FAIL, for the 500-user steady state.** Health for all three is NOT ASSESSED for this question. The FAIL flags in facts.md for minutes 16–39 are computed from a distorted instrument (SLA-1, SLA-3) and a harness-reduced workload (SLA-2). Missing valid evidence is not a PASS either (Rule 4).
2. **"The system cannot sustain 90 TPS" or any capacity limit.** The throughput fall is missing users (R2).
3. **"Checkout p95 at 500 users is 4–6 s."** LG2's minutes 16–39 latencies are not system response times (R4, R5). They also must not be combined or averaged with LG1's (Rule 5).
4. **"The system meets the SLAs at 500 users"**, based on minutes 10–15 or on LG1. Six minutes are not the steady state, and LG1 carried half the load.
5. **"The error rate was 2.13 %" as a system error rate**, or any claim that LG2's failures were server errors. Their origin is undetermined (R8).
6. **"There were no server errors."** The error log is an excerpt (DQ-04).
7. **A confirmed cause for LG2's distortion.** Extended logging is the leading candidate (the only configuration difference, plus the log-flush warning). But the ramp-down observation (R6) shows the mechanism is not established, and source-specific system paths are not excluded (DQ-05). At most Probable Contributor until a controlled change is run. That grading is the specialists' call.
8. **"The database, app tier, network or payment provider is not involved."** Negative claims need evidence from that layer (Rule 9). At most: no app-tier or lb1 signal rises at minute 16 (R5), with no server-side latency to confirm it.
9. **Any extrapolation of the minute 30–33 DB effect to 500 users.**

### Unknowns that could change the decision or its scope

None of these would make the run VALID for the 500-user, 30-minute question, because the workload was not held. They can change the allowed narrower scope and the diagnosis.

1. **Server-side response time for requests from LG2 vs LG1**, minutes 16–39. If server times for LG2's traffic were also around 5 s, a source-specific system path is real (R6). LG2's latencies would then become a system finding (though still under reduced total load), and the harness reading would weaken.
2. **Load-tool definitions**: whether avg_s/p95_s exclude failed transactions (DQ-06), what `failed` and `script_errors` count (DQ-07), and exactly when abort-on-error fires. This explains why no user exited after minute 22 despite 34–42 failures per minute (R8).
3. **LG2 CPU sampling and log I/O**: why LG2 stayed at 92–98 % CPU with 80 users, and why its latency did not recover when CPU fell in minutes 39–42 (R4, R6).
4. **LG2 behaviour in minutes 10–15 at sub-minute resolution.** At 82–87 % CPU and rising, LG2 may already have added some client delay. LG2 and LG1 agreed at minute granularity (V3), but this is not proven. It bounds allowed claim 1.
5. **Batch execution record** for 10:30 UTC (DQ-14) and clock sync across hosts (DQ-02).
6. **Unfiltered generator logs** for both generators (DQ-04).
7. **Payment sandbox behaviour** during the run (DQ-05).

### Test-integrity issues to fix before a rerun

Owners are proposed. The Test Lead assigns them in the Decide call.

| # | Issue | Change | Success measure | What would show it did not work |
| --- | --- | --- | --- | --- |
| TI-1 | LG2 configured differently from LG1 (log level extended with parameter substitution) | Set every generator to `standard` logging for measurement runs (owner: performance engineer running the harness) | At equal user counts, generator CPU differs by no more than a few points across generators, and same-transaction p95 agrees across generators minute by minute | One generator still runs much hotter, or same-minute latencies still diverge, with logging matched |
| TI-2 | No generator headroom gate | Agree a generator-health threshold before the run (proposed: CPU below about 70 % for every steady-state minute) and add generator capacity if a calibration shows it is needed (owner: harness owner) | All generators stay under the agreed threshold for all of minutes 10–39 | Any generator exceeds it. The affected minutes are then invalid for that generator |
| TI-3 | `abort_on_error: true` turns errors into load loss | Run with continue-on-error, so errors are logged and counted and the user carries on (owner: harness owner) | Running users equal scheduled users for every steady-state minute, as recorded in vusers.csv | Running users drop below scheduled in steady state |
| TI-4 | Distortion mechanism unconfirmed | Calibration before the rerun: each generator alone at 250 users with standard logging, then one generator switched to extended logging (controlled change) (owner: harness owner) | Extended logging alone reproduces high generator CPU and inflated client timings; standard logging removes them | The switch does not reproduce the symptom. Then look at source-specific network or system paths instead |
| TI-5 | Scheduled batch inside the steady state | Decide explicitly: move the batch outside the run, or include it deliberately and record its start, end and rows (owner: Test Lead with the data team) | The decision is recorded in the scenario and the batch log is part of the evidence | The batch runs unrecorded, or overlaps without a decision |
| TI-6 | Coverage gaps that block attribution | Add server-side response time per transaction (APM), an LB split by source and by backend, uninterrupted app2 monitoring, full generator logs, payment sandbox metrics or a stub with known behaviour, and declare the client timeout and how failures count toward SLA-1/2 (owner: Test Lead / environment owner) | Every source covers all 45 minutes, and client vs server latency can be compared per minute | Any decisive gap remains. Missing evidence will again not default to VALID |
| TI-7 | Steady state too short to observe | Validate the steady state from data in the rerun: 500 running and on-pace for the full 30 minutes before any SLA verdict (owner: Test Validity Reviewer on the rerun) | Minutes 10–39 meet R1/R2/R4 conditions throughout | Any break. Validity is then re-scoped |

## Commands relied on

All run from `examples/01-generator-saturation/data`.

**V1 — expected vs achieved TPS from running users (running × 4 / 20)** (block A of the second command below):
```
python3 -I -c "
import csv,collections,statistics as st
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):int(r['running_vusers']) for r in csv.DictReader(open('vusers.csv'))}
for m in (10,15,16,17,18,19,20,21,22,23,30,39):
  run=vu[(m,'LG1')]+vu[(m,'LG2')]
  ach=sum(int(x['count']) for g in ('LG1','LG2') for x in tx[(m,g)].values())/60
  ps=sum(int(x['passed']) for g in ('LG1','LG2') for x in tx[(m,g)].values())/60
  print(m,run,'exp %.1f ach %.1f passed %.1f'%(run*4/20,ach,ps))
w=range(23,40)
print('mean 23-39 exp %.1f ach %.1f'%(st.mean((vu[(m,'LG1')]+vu[(m,'LG2')])*4/20 for m in w), st.mean(sum(int(x['count']) for g in ('LG1','LG2') for x in tx[(m,g)].values())/60 for m in w)))
..."
```
Output (key): min 10 500 users exp 100.0 ach 100.5. Min 17 475 exp 95.0 ach 90.7 passed 81.6. Min 22 330 exp 66.0 ach 63.3 passed 60.0. Min 23 330 exp 66.0 ach 64.8 passed 64.1. Min 30 66.0 / 65.2 / 64.5. Min 39 66.0 / 65.0 / 64.2. Mean minutes 23–39: expected 66.0, achieved 65.6.

**V2 — failures without exits, DB-window cross-check, equal-user check, server side at onset, LG2 CPU in ramp-down, CPU per user** (same script, continued):
```
print('LG2 failed per minute 23-39:',[sum(int(x['failed']) for x in tx[(m,'LG2')].values()) for m in w])
print('LG2 exits after 22:',[...exited_with_error != '0' for LG2, m>22])
db=[30,31,32,33]; nb=[m for m in range(23,40) if m not in db]
for g in ('LG1','LG2'): print(g, mean checkout avg_s over db vs nb, median checkout p95 over db vs nb)
print('min 43: LG1', vu[(43,'LG1')], p95, 'LG2', vu[(43,'LG2')], p95)
for m in range(14,19): app1/app2 cpu_pct, active_threads, db_pool_active, db_pool_wait_ms, gc_pause_ms
lb1 minutes 14-24: active_connections, retransmit_pct
LG2 cpu_pct and running users, minutes 39-44
mean(cpu_pct/running_vusers): LG2 10-15, LG2 23-39, LG1 10-39
```
Output (key): LG2 failed per minute, minutes 23–39: 37, 34, 35, 37, 35, 37, 42, 36, 41, 36, 36, 42, 37, 40, 37, 38, 38. LG2 exits after minute 22: none. Checkout avg_s, minutes 30–33 vs other minutes 23–39: LG1 1.15 vs 0.85; LG2 2.90 vs 2.91. Checkout p95 median, minutes 30–33 vs others: LG1 1.935 vs 1.43; LG2 4.69 vs 4.74. Minute 43: LG1 50 users p95 1.26, LG2 50 users p95 4.69. App, minutes 14–18: CPU 56.4→47.8 falling, threads 21–25, pool 5–7, pool wait 0–2 on both nodes. lb1, minutes 14–24: connections 310→192, retransmits 0.01–0.03. LG2 CPU minutes 39–44 (users): 94.0 (80), 86.4 (80), 71.0 (80), 61.3 (80), 49.3 (50), 35.2 (0). LG2 checkout p95 minutes 39–42: 4.91, 4.74, 5.11, 5.08 (from the per-minute table in V3's source command). CPU per running user: LG2 0.340 (10–15), LG2 1.183 (23–39), LG1 0.233 (10–39).

**V3 — per-generator per-minute workload, mix, pacing, health; and ranges by window**:
```
python3 -I -c "
import csv,collections
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):int(r['running_vusers']) for r in csv.DictReader(open('vusers.csv'))}
lg={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('load_generators.csv'))}
def rng(vals): return '%.2f-%.2f'%(min(vals),max(vals))
for g in ('LG1','LG2'):
  for a,b in ((10,15),(16,22),(23,39),(10,39)):
    ms=range(a,b+1); c=lambda m:int(tx[(m,g)]['checkout']['count'])
    sr=[int(tx[(m,g)]['search']['count'])/c(m) for m in ms]; ar=[int(tx[(m,g)]['add_to_cart']['count'])/c(m) for m in ms]
    cyc=[vu[(m,g)]/(c(m)/60) for m in ms]
    fp=[100*sum(int(x['failed']) for x in tx[(m,g)].values())/sum(int(x['count']) for x in tx[(m,g)].values()) for m in ms]
    cpu=[float(lg[(m,g)]['cpu_pct']) for m in ms]
    p95=[float(tx[(m,g)]['checkout']['p95_s']) for m in ms]
    print(g,a,b,'search:ck',rng(sr),'add:ck',rng(ar),'cycle',rng(cyc),'fail%',rng(fp),'cpu',rng(cpu),'ck p95',rng(p95))
"
```
Output:
```
LG1 10 15 search:ck 1.98-2.06 add:ck 0.97-1.04 cycle 19.71-20.46 fail% 0.17-0.24 cpu 56.50-59.60 ck p95 1.33-1.42
LG1 16 22 search:ck 1.94-2.06 add:ck 0.97-1.04 cycle 19.48-20.58 fail% 0.16-0.20 cpu 56.70-59.30 ck p95 1.27-1.46
LG1 23 39 search:ck 1.91-2.07 add:ck 0.96-1.02 cycle 19.48-20.60 fail% 0.13-0.24 cpu 56.50-60.00 ck p95 1.29-1.98
LG2 10 15 search:ck 1.94-2.05 add:ck 0.96-1.02 cycle 19.48-20.52 fail% 0.17-0.23 cpu 82.20-87.50 ck p95 1.27-1.51
LG2 16 22 search:ck 1.93-2.09 add:ck 0.95-1.04 cycle 21.84-22.67 fail% 4.09-22.49 cpu 92.90-98.10 ck p95 5.28-5.87
LG2 23 39 search:ck 1.92-2.05 add:ck 0.94-1.03 cycle 19.75-20.87 fail% 3.65-4.49 cpu 92.20-98.50 ck p95 4.40-5.19
```
A companion per-minute listing (same inputs, one line per generator per minute for minutes 8–43) showed LG2 minute 16: 250 users, CPU 93.9, cycle 22.6 s, failures 4.1 %, checkout p95 5.61. It also showed LG2 and LG1 per-transaction avg_s in minutes 10–15 within 0.81–0.89 s (checkout) and 0.57–0.63 s (search) on both.

## Handoff

- **VAL-1 = INVALID FOR THIS QUESTION.** All SLA-1/2/3 verdicts for the 500-user steady state are NOT ASSESSED. No FAIL may be attributed to the system from minutes 16–39.
- **Performance Analyst:** use LG1 minutes 10–39 and both generators in minutes 10–15 as the valid measurement scope. Treat LG2 minutes 16–39 as a harness symptom to describe, not as system latency. Remember that total load was 330 users from minute 22 when reading LG1. Suggested SW- windows: 10–15 (clean full load), 16–22 (LG2 onset and user loss), 23–39 (reduced-load plateau), 30–33 (DB event).
- **Infrastructure specialist:** explain why LG2 CPU did not scale with users (1.18 vs 0.23 %/user) and why LG2 latency did not recover when its CPU fell in minutes 39–42 (R6). The per-source network path stays open (DQ-05).
- **Application specialist:** search and add_to_cart inflated on LG2 as well as checkout. The payment provider alone does not fit that pattern, but it cannot be excluded without data.
- **Database specialist:** minutes 30–33 are the one system-side finding the run supports (allowed claim 4), under about 65 TPS of load.
- **Test Lead (Decide):** rerun is required for the question. TI-1 to TI-7 are the integrity fixes. TI-4 is the controlled change that could move the LG2 explanation beyond Probable Contributor.
- **Open questions:** load-tool definitions for failures and abort-on-error (Unknown 2); whether server-side latency differed by source (Unknown 1); batch execution record (Unknown 5).
