```
Agent: Performance Analyst
Run: SYN-RUN-001
Read: agents/performance-analyst.md; method/judgments.md; method/rules.md; method/records.md; examples/01-generator-saturation/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, generator_errors.log); examples/01-generator-saturation/facts.md; examples/01-generator-saturation/run/01-test-lead-plan.md; examples/01-generator-saturation/run/02-evidence.md; examples/01-generator-saturation/run/03-validity.md
Execution: separate agent context, model Claude Opus 5.5
```

# Performance analysis — SYN-RUN-001

Synthetic scenario (`"synthetic": true`, E-01). No previous run or baseline (`previous_run: null`), and none was used (Rule 1). Elapsed minute *m* = 2026-10-01 10:00 UTC + *m* minutes. Numbers come from facts.md (E-02), the evidence register (02-evidence.md, commands C1–C7), the validity record (03-validity.md, V1–V3), or my commands P1–P4 at the end. `tools/analyze.py` was not re-run; facts.md is used as generated.

**Scope I work within (VAL-1, INVALID FOR THIS QUESTION).** Verdict-bearing scope: both generators in minutes 10–15, and LG1 in minutes 10–39 *at the total load actually present* (500 users to minute 16, 330 from minute 22). LG2 in minutes 16–39 is described as a harness symptom, not as system latency. Every SLA verdict for the 500-user steady state is NOT ASSESSED. Values outside the allowed scope are reported as observations only.

**Conventions.** p95 is reported only as per-minute values, summarised as median / max over a window (Rule 5). Never pooled across generators, transactions or minutes. "avg" is the load tool's per-minute avg_s, and window figures for it are ranges or means of per-minute values. LG2 latency in failure-heavy minutes most likely covers passed transactions only (DQ-06). TPS includes failed transactions (DQ-13). Failures cannot be split by type from the CSVs: `transactions.csv` has a single `failed` counter, and `script_errors` is a different, unreconciled counter (DQ-07). The only typed failures are in the 9-line error-log excerpt (E-16, DQ-04).

## 1. Phases, from the data

| Phase | Minutes (data) | Scheduled | What defines it in the data |
| --- | --- | --- | --- |
| Ramp-up | 0–8 (500 running reached at 9) | 0–9 | Running users +50/min total, TPS 10.1 → 89.5, both generators on pace, latency flat on both (facts.md; P1) |
| Full-load steady state | 9–15 | 10–39 | 500 running, TPS 99.0–101.6 (min 10–15), per-generator cycle 19.48–20.52 s, LG1 and LG2 agree per transaction (OBS-01, OBS-02) |
| Degradation, LG2 only | 16–22 | (steady) | LG2 latency ×~4 on all transactions, failures 17.59 %, iterations late, 170 LG2 users exit; LG1 unchanged (OBS-03 – OBS-07) |
| Reduced-load plateau | 23–39 | (steady) | 330 running (LG1 250, LG2 80), total TPS 63.3–66.5, both generators on pace; LG2 latency stays ×~3.3–3.5, failures ~4 % (OBS-08, OBS-09) |
| System event inside plateau | 30–33 | — | DB "row lock contention"; LG1 checkout only rises; reverts at 34 (OBS-10 – OBS-12) |
| Ramp-down | LG1 40–43; LG2 43 only | 40–44 | LG1 250 → 200 → 150 → 100 → 50. LG2 was already at 80, below its scheduled 200, so its count is unchanged until 43 (50). Minute 44: 0 users, no transaction rows (DQ-08) |
| Recovery | — | — | LG1 metrics are at their minute 10–15 levels outside 30–33. LG2 latency and failures **never** return to minute 10–15 levels after minute 16, including at 50 users (OBS-14) |

## 2. Observations

All are Observed Facts unless stated. "Ratio" = LG2 ÷ LG1, both from means of per-minute avg_s for the same transaction in the same minutes (P2).

### Minutes 10–15 (full load, allowed scope)

- **OBS-01 — Both generators measured the same latency for every transaction.** Checkout p95 median/max: LG1 1.39 / 1.42 s, LG2 1.40 / 1.51 s. Search: LG1 1.01 / 1.05, LG2 0.98 / 1.04. Add_to_cart: LG1 0.65 / 0.70, LG2 0.66 / 0.67. LG2 : LG1 avg ratio 0.99 (search), 1.03 (add_to_cart), 1.02 (checkout). *Window* 10–15, *scope* both generators, all transactions. *Evidence* E-04, E-05, P1, P2.
- **OBS-02 — Full workload was delivered and on pace, with a low error rate.** 500 running, total TPS 99.0–101.6 (per generator 48.8–50.8 and 48.9–50.9), per-generator cycle LG1 19.71–20.46 s, LG2 19.48–20.52 s. Failure share per minute 0.18–0.23 % (facts.md); pooled over the window 74 / 35,952 = 0.206 % (P1). App CPU 53.4–58.0 %, threads 23–26 of 200, db_pool_active 6–7 of 20, pool wait 0–2 ms, DB CPU 28.4–31.2 %, lock wait 2–8 ms, lb1 retransmits 0.02–0.04 % (P3). *Evidence* E-02, E-03, E-06, E-11–E-15, P1, P3.
- **OBS-02a — Instrument note (from validity, restated for the windows).** LG2 CPU 82.2 → 87.5 % and rising every minute in 10–15, against LG1 56.5–59.6 % at the same users and TPS. The gap opens during ramp-up: at 25 users LG1 23.2 / LG2 26.9 %, at 125 users 39.0 / 49.7 %, at 250 users (min 9) 58.1 / 83.0 % (P3). Latency on LG2 does not differ from LG1 at minute resolution until minute 16. *Evidence* E-09, E-10, P3.

### Minutes 16–22 (onset and user loss)

- **OBS-03 — Onset is minute 16, on LG2 only, on all three transactions at once.** Using "first minute above 1.2 × the minute 10–15 maximum" for p95 and avg_s, and "first minute above 2 × the minute 10–15 maximum" for failure share: LG2 search, add_to_cart and checkout all trip at minute 16 on all three measures, and stay tripped for all 28 minutes 16–43. LG1 trips on nothing in minutes 16–29 or 34–43. Minute 16 values on LG2: checkout p95 5.61 s, search 4.14, add_to_cart 2.91; failures 27 / 62 / 23. *Window* 16, *scope* per generator × transaction. *Evidence* E-03, P1. Minute-16 ordering against LG2 CPU (93.9 %) cannot be resolved below one minute (DQ-12).
- **OBS-04 — The inflation is proportional across transactions, not a fixed added amount.** LG2 : LG1 avg ratio in 16–22: search 4.07, add_to_cart 4.17, checkout 4.07. The absolute differences differ by transaction (1.86 / 1.27 / 2.61 s). *Window* 16–22. *Evidence* P2. (Pattern only; no cause proposed.)
- **OBS-05 — LG2 p95 per minute in 16–22.** Checkout 5.28–5.87 s (median 5.67), search median/max 4.14 / 4.32, add_to_cart 2.81 / 2.91. LG1 in the same minutes: checkout median/max 1.42 / 1.46, search 0.98 / 1.08, add_to_cart 0.66 / 0.71. *Evidence* E-04, E-05, P1. LG2 values probably exclude failed attempts (DQ-06).
- **OBS-06 — LG2 failures in 16–22: 2,036 / 11,577 = 17.59 % pooled** (search 17.39 %, add_to_cart 17.83 %, checkout 17.74 %), per minute 4.09–22.49 % (V3). LG1 in the same window 39 / 21,057 = 0.19 %. Typed evidence exists only in the excerpt: three 30 s client timeouts (checkout ×2, search ×1) and two abort-on-error exits, all LG2, 10:16:31–10:21:03Z; no server-error status line (excerpt only, DQ-04). LG2 `script_errors` 0 at 16, then 143–252 per minute in 17–22 (E-10). *Evidence* E-03, E-08, E-16, P1.
- **OBS-07 — Throughput loss in 16–22 is mostly lost users, partly late iterations.** Against 250 LG2 users at 20 s pacing (50 TPS), LG2's summed shortfall over 16–22 is 157.1 TPS-minutes: 136.0 from fewer running users, 21.1 from present users running late (P4). The late part is largest at minutes 16–17 (4.4, 4.5 TPS) and shrinks to 1.8 by minute 22. LG2 per-generator cycle 21.84–22.67 s in 16–22 (V3); LG1 19.48–20.58 s. Running users LG2 250 → 225 → 185 → 140 → 105 → 85 → 80 (E-07). *Caveat:* whether running_vusers is point-in-time or end-of-minute is undocumented (E-06), so the split is approximate at minute granularity.

### Minutes 23–39 (reduced-load plateau)

- **OBS-08 — From minute 23, throughput equals what the running users should produce.** 330 running; expected 66.0 TPS, achieved mean 65.6 (V1); per-minute total 63.3–66.5 (facts.md). LG2 cycle 19.75–20.87 s, LG1 19.48–20.60 s. LG1 TPS 49.1–50.8, LG2 15.5–16.1. No user exits after minute 22. *Evidence* E-06, V1, V3, P1.
- **OBS-09 — LG2 stays inflated at a lower, stable ratio; LG2 failures drop but stay ~20× LG1's.** LG2 : LG1 avg ratio 3.31–3.36 (23–29) and 3.39–3.55 (34–39) for all three transactions. LG2 checkout p95 median/max 4.74 / 5.19, search 3.31 / 3.64, add_to_cart 2.25 / 2.38. LG2 failures 638 / 16,091 = 3.96 % (34–42 per minute, V2); LG1 102 / 50,797 = 0.20 %. LG2 script_errors 8–23 per minute. LG2 CPU 92.2–98.5 % with 80 users. The step from ×~4.1 to ×~3.3 and from ~21 % to ~4 % failures happens between minutes 22 and 23, the same minute exits stop (P1, P2). *Evidence* E-05, E-07, E-10, P1, P2.
- **OBS-09a — LG1 checkout p95 sits slightly higher in 23–29 than in 10–15 and 34–39, without any avg change.** p95 median 1.49 (23–29) vs 1.39 (10–15) and 1.38 (34–39); max 1.53 at minute 23. LG1 checkout avg 0.83–0.89 s in 23–29, same range as 10–15 (0.81–0.86). Below the 1.2× onset rule; DB lock wait 2–7 ms in 23–29 (P3). Small, no server-side counterpart found; reported for completeness. *Evidence* P1, P3.

### Minutes 30–33 (DB event)

- **OBS-10 — DB changes state for exactly four minutes.** Lock wait 921 / 799 / 783 / 902 ms (2–8 ms on either side), top wait event "row lock contention" (only these 4 of 45 rows), sessions 13 (7 on either side), avg query 19.9–20.9 ms (10.0–12.5 on either side), CPU 38.2–40.4 % (21.0–23.0 on either side). Reverts fully at minute 34. *Evidence* E-14, P3. Coincides with the 10:30 UTC inventory-sync schedule; execution not recorded (DQ-14, DQ-02).
- **OBS-11 — On LG1, only checkout moves, in the same four minutes.** LG1 checkout p95 1.97 / 1.78 / 1.98 / 1.90 s (median 1.94, max 1.98 — 0.02 s under the SLA-1 threshold); avg 1.16 / 1.12 / 1.19 / 1.11 s vs 0.81–0.89 in every other minute 10–43. LG1 search (p95 median/max 0.99 / 1.02) and add_to_cart (0.66 / 0.73) do not change. LG1 failures unchanged (0.20 %). One excerpt line at 10:31:02Z: LG1 vuser 12 checkout 3.4 s. Total load in this window: 330 users, ~65 TPS. *Window* 30–33, *scope* LG1 checkout. *Evidence* E-04, E-14, E-16, P1. Grade for the DB ↔ LG1-checkout link: **Correlation, Medium confidence** — aligned minute windows, start and end match on both signals, one healthy client source; batch execution unrecorded and clock sync unverifiable (DQ-02).
- **OBS-12 — On LG2, the same event is not visible.** LG2 checkout avg 2.90 s in 30–33 vs 2.88 (23–29) and 2.94 (34–39); p95 median 4.69 vs 4.67 and 4.93. LG2 : LG1 checkout ratio dips to 2.53 only because LG1 rose. *Evidence* P1, P2, V2.
- **OBS-13 — No app-tier or lb1 change in 30–33.** App CPU 37.0–39.5 %, threads 16–19, db_pool_active 4–6 of 20, pool wait 0–2 ms on both nodes (app2 present 30–33); lb1 retransmits 0.01–0.04 %. *Evidence* E-11, E-12, E-15, P3. No server-side response time exists to show where the added checkout time was spent (DQ-05).

### Ramp-down and recovery

- **OBS-14 — LG2 timings do not recover when its load or CPU falls.** LG2 at 80 users in 40–42 and 50 users at 43: checkout p95 4.74 / 5.11 / 5.08 / 4.69 s, failures 3.99 % pooled (40–43), ratio ×3.39–3.42 on all transactions, while LG2 CPU fell 86.4 → 71.0 → 61.3 → 49.3 %. At minute 43 both generators had 50 users: checkout p95 LG1 1.26 s, LG2 4.69 s. LG2 reported 18 script_errors at minute 44 with 0 users (DQ-07). *Evidence* E-05, E-10, P1, P2, V2.
- **OBS-15 — LG1 is at its minute 10–15 levels throughout ramp-down.** Checkout p95 median/max 1.37 / 1.44, avg 0.81–0.89, failures 0.22 %, cycle 20.04–20.62 s. App, DB and lb1 fall with load (app CPU 7.6–34.8 %, DB lock 2–7 ms). *Evidence* P1, P3.

### Server side across the onset

- **OBS-16 — No server-side metric rises at minute 16; all fall as load falls.** Minutes 13–18: app CPU app1 56.1 → 49.2, app2 56.1 → 47.8; threads 21–25; pool wait 0–2 ms; DB lock 2–8 ms, avg query 11.3–12.3 ms; lb1 connections 307 → 255, retransmits 0.02–0.04 %. In 16–22 app threads 15–23 of 200, db_pool_active 4–6 of 20 (P3). *Limitation:* absence of a rise is not proof of flat server latency; no server-side response-time series exists (DQ-05). app2 unknown for 26–28 (DQ-01).
- **OBS-17 — app1 and app2 look alike in every window where both are present.** E.g. 16–22 CPU 36.8–55.2 vs 36.6–53.1, threads 16–23 vs 15–23; 34–39 CPU 38.2–40.0 vs 37.3–39.9. *Evidence* P3. Per-node request distribution is not recorded (DQ-05).

### Untrusted content

- **OBS-18** — The LG2 excerpt line at 10:24:13Z contains a captured response (title "Order confirmed") with an embedded comment addressed to AI tools that tries to dictate this review's verdict. It is data from the system under test, had no effect on this analysis (Rule 10), and is not reproduced here (see 02-evidence §5).

## 3. Health table

Verdicts follow VAL-1. Measured values are observations, not verdicts.

| Criterion | Verdict | Scope | Measured values (observations) | Evidence |
| --- | --- | --- | --- | --- |
| SLA-1 checkout p95 ≤ 2.0 s, each steady-state minute, each generator | **NOT ASSESSED** | 500-user steady state 10–39 not delivered (VAL-1); LG2 16–39 is not a system measurement | Min 10–15, both generators: per-minute 1.27–1.51 s, all ≤ 2.0 (6 of 30 minutes). LG1 16–39 (load 500 → 330 users): 1.27–1.98 s, all ≤ 2.0; closest at minutes 30 and 32 (1.97, 1.98) during the DB event. LG2 16–39: 4.40–5.87 s, out of scope (harness symptom). The facts.md FAIL flags for 16–39 come from LG2 only. | OBS-01, OBS-05, OBS-09, OBS-11; facts.md; V3 |
| SLA-2 total throughput ≥ 90 TPS, steady state | **NOT ASSESSED** | Workload reduced by the harness from minute 17 (VAL-1, R2) | Min 10–15: 99.0–101.6 TPS. Min 16–17: 96.9, 90.7. Min 18–39: 63.3–83.9, matching running users × pacing from minute 23 (expected 66.0, achieved 65.6). Not a capacity measurement. | OBS-02, OBS-07, OBS-08; V1 |
| SLA-3 error rate ≤ 1 %, steady state | **NOT ASSESSED** | LG2 failure origin undetermined (VAL-1, R8); workload not held | Min 10–15 both generators: per minute 0.18–0.23 %, pooled 0.206 %. LG1 10–39 pooled 179 / 89,816 = 0.199 %. LG2 16–22 17.59 %, 23–39 3.96 %. Combined pooled 10–39 2.13 % (facts.md) mixes these and is not a system error rate. | OBS-02, OBS-06, OBS-09; facts.md; P1 |

What the run does **not** show: that the system meets any criterion at 500 users over 30 minutes, or that it fails any. Six clean minutes and a half-load generator are not a steady-state PASS (Rule 4).

## 4. Symptom windows for the specialists

| ID | Window | Scope | What is observed | Questions to investigate | Who |
| --- | --- | --- | --- | --- | --- |
| SW-0 | 0–15 | LG2 vs LG1 host | LG2 CPU grows faster than LG1 from the first users (26.9 vs 23.2 % at 25 users; 83.0 vs 58.1 % at 250) with identical TPS, mix and latency (OBS-02a) | What on LG2 costs more CPU per user from minute 0? Does its per-user cost match the extended-logging difference? | Infrastructure |
| SW-1 | 16 (single minute) | LG2, all transactions | Simultaneous onset of latency ×~4, failures, late iterations and CPU > 90 % (OBS-03, OBS-07); LG1 and server side unchanged (OBS-16) | What changed on LG2 at minute 16? Is there any sub-minute record (generator logs, controller events) that orders CPU, log flush and timeouts? Is there any server-side record of LG2-sourced requests being slow? | Infrastructure (lead), Application |
| SW-2 | 16–22 | LG2 | Failures 17.59 %, 30 s client timeouts, 170 exits, script_errors 143–252/min (OBS-06, OBS-07) | What are LG2's failures by type? Why did exits stop at minute 22 while failures continued at 34–42/min (R8)? Did any LG2 request receive a server error? | Infrastructure, Application |
| SW-3 | 23–43 | LG2 | Stable ×3.3–3.5 inflation on all transactions, ~4 % failures, at 80 then 50 users, CPU 92–98 % then falling to 49 % without latency recovery (OBS-09, OBS-14) | Why does LG2 inflation persist when its CPU falls (OBS-14)? Why is the inflation proportional across transactions (OBS-04)? Is any source-specific path (LB, affinity, payment sandbox) involved — no per-source data exists (DQ-05)? | Infrastructure (lead), Application |
| SW-4 | 30–33 | DB; LG1 checkout | Row-lock contention, lock wait 783–921 ms, sessions 13, query 20 ms; LG1 checkout avg +~0.3 s and p95 to 1.98 s; LG1 search/add_to_cart unchanged; app tier unchanged (OBS-10 – OBS-13) | What held the row locks? Was it the 10:30 UTC inventory-sync batch? Why only checkout (which tables/rows does checkout touch that search/add_to_cart do not)? What would this do at 500 users? | Database (lead), Application |
| SW-5 | 23–29 | LG1 checkout | p95 median 1.49 vs 1.39 baseline, avg unchanged (OBS-09a) | Low priority. Is there any server-side signal in these minutes? Likely within run-to-run variation; check only if SW-4 work exposes something. | Database / Application (optional) |

## 5. Handoff

- **Look first at SW-1 / SW-3 (Infrastructure).** Every SLA-relevant anomaly in steady state is on LG2, starts at minute 16 on all three transactions at once, is proportional across transactions, and persists at low user count and falling CPU. Nothing on app, DB or lb1 rises at the onset. Where to look: LG2's own host and harness behaviour, and any per-source path that could treat LG2 traffic differently. I propose no cause.
- **SW-4 (Database) is the one system-side event the valid scope shows.** It affects LG1 checkout only, starts and ends with the DB lock-wait change, and brings checkout p95 to 1.98 s at ~65 TPS — 0.02 s under SLA-1 at 66 % of the intended load. Its effect at 500 users is unknown.
- **Throughput:** the drop is accounted for by lost users from minute 23 (OBS-08). In 16–22, about 21 of 157 TPS-minutes of LG2's shortfall came from late iterations of present users (OBS-07).
- **Health:** SLA-1/2/3 all NOT ASSESSED for the question. The only clean full-load window is minutes 10–15, where every measured value was within thresholds.
- **Open questions:** load-tool definition of `failed` vs `script_errors` and whether p95 excludes failures (DQ-06, DQ-07); why abort-on-error stopped firing after minute 22; server-side latency by source; batch execution record for 10:30 UTC; unfiltered generator logs.

## Commands relied on

All run from `examples/01-generator-saturation/data`.

**P1 — per-minute listing and window summaries per generator × transaction; pooled failure rates; onset rule**
```
python3 -I -c "
import csv,collections,statistics as st
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):int(r['running_vusers']) for r in csv.DictReader(open('vusers.csv'))}
W=[(10,15),(16,22),(23,29),(30,33),(34,39),(23,39),(40,43)]
T=('search','add_to_cart','checkout')
for a,b in W:
  ms=range(a,b+1)
  for g in ('LG1','LG2'):
    for t in T:
      p=[float(tx[(m,g)][t]['p95_s']) for m in ms]; av=[float(tx[(m,g)][t]['avg_s']) for m in ms]
      c=sum(int(tx[(m,g)][t]['count']) for m in ms); f=sum(int(tx[(m,g)][t]['failed']) for m in ms)
      print('%d-%d %s %-11s p95 med %.2f max %.2f | avg %.2f-%.2f | fail %.2f%% (%d/%d)'%(a,b,g,t,st.median(p),max(p),min(av),max(av),100*f/c,f,c))
for a,b in [(10,15),(16,22),(23,39),(40,43)]:
  ms=range(a,b+1)
  for g in ('LG1','LG2'):
    tps=[sum(int(x['count']) for x in tx[(m,g)].values())/60 for m in ms]
    cyc=[vu[(m,g)]/(int(tx[(m,g)]['checkout']['count'])/60) for m in ms]
    c=sum(int(x['count']) for m in ms for x in tx[(m,g)].values()); f=sum(int(x['failed']) for m in ms for x in tx[(m,g)].values())
    print(a,b,g,'tps %.1f-%.1f fail %.2f%% (%d/%d) cycle %.2f-%.2f'%(min(tps),max(tps),100*f/c,f,c,min(cyc),max(cyc)))
# pooled 10-15 both generators; LG1 10-39
# onset: first minute 16-43 with p95_s or avg_s > 1.2 x max(10-15), or failed/count > 2 x max(10-15)
"
```
(The per-minute listing used the same inputs, printing running/exited users, generator CPU and script_errors, and count/failed/avg_s/p95_s per transaction for every generator and minute 0–44.)
Key output: as quoted in OBS-01 – OBS-15. 10–15 pooled 74/35952 = 0.206 %. LG1 10–39 pooled 179/89816 = 0.199 %. LG2 16–22 2036/11577 = 17.59 %; 23–39 638/16091 = 3.96 %; LG1 23–39 102/50797 = 0.20 %. Onset: LG2 all transactions first minute 16 on p95, avg and failure share, 28 minutes each; LG1 checkout p95 and avg first 30, minutes [30, 31, 32, 33] only; LG1 search and add_to_cart none.

**P2 — LG2 : LG1 ratio and difference of mean per-minute avg_s, by window**
```
for a,b in [(10,15),(16,22),(23,29),(30,33),(34,39),(40,43)]:
  ms=range(a,b+1)
  for t in ('search','add_to_cart','checkout'):
    l1=st.mean(float(tx[(m,'LG1')][t]['avg_s']) for m in ms); l2=st.mean(float(tx[(m,'LG2')][t]['avg_s']) for m in ms)
    print('%d-%d %-11s LG1 %.2f LG2 %.2f ratio %.2f diff %.2f'%(a,b,t,l1,l2,l2/l1,l2-l1))
```
Output: 10–15 ratios 0.99 / 1.03 / 1.02 (search / add_to_cart / checkout). 16–22 4.07 / 4.17 / 4.07 (diff 1.86 / 1.27 / 2.61 s). 23–29 3.33 / 3.36 / 3.31. 30–33 3.44 / 3.46 / 2.53 (LG1 checkout 1.15). 34–39 3.39 / 3.39 / 3.55. 40–43 3.39 / 3.39 / 3.42.

**P3 — server side and generators by window (min–max), DB converted to UTC minutes**
```
python3 -I -c "
import csv
from datetime import datetime,timezone
ap={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open('app_servers.csv'))}
nw={int(r['elapsed_min']):r for r in csv.DictReader(open('network.csv'))}
t0=datetime(2026,10,1,10,tzinfo=timezone.utc); db={}
for r in csv.DictReader(open('database.csv')):
  t=datetime.strptime(r['window_start_local'],'%Y-%m-%dT%H:%M:%S%z'); db[int((t-t0).total_seconds()//60)]=r
lg={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('load_generators.csv'))}
# for windows 10-15,16-22,23-29,30-33,34-39,40-44: min-max of app cpu/heap/gc/threads/pool/wait per node (present rows only),
# db cpu/sessions/avg_query/lock_wait/top_wait_event, lb1 connections/mbps/retransmit, generator cpu/mem/script_errors;
# per-minute 13-18 app/db/lb1; per-minute 28-35 db; per-minute 0-9 generator CPU
"
```
Key output: 10–15 app CPU 53.4–58.0, threads 23–26, pool 6–7, wait 0–2; DB lock 2–8; lb1 retx 0.02–0.04. 16–22 app threads 15–23, pool 4–6; DB lock 2–8. 23–29 app2 n=4 (26–28 missing). 30–33 DB CPU 38.2–40.4, sessions 13, query 19.9–20.9, lock 783–921, "row lock contention"; app CPU 37.0–39.5, wait 0–2. 34–39 DB lock 2–8, sessions 7. Minutes 13–18 app CPU 56.1 → 49.2 / 47.8, lb1 connections 307 → 255. DB minutes 28–29 and 34–35 lock 3–8, sessions 7. Generator CPU ramp-up, LG1 / LG2: 23.2/26.9 (0), 39.0/49.7 (4), 58.1/83.0 (9).

**P4 — LG2 throughput shortfall split into lost users and late iterations**
```
python3 -I -c "
import csv,collections
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):int(r['running_vusers']) for r in csv.DictReader(open('vusers.csv'))}
S=[0,0,0]
for m in range(15,25):
  u=vu[(m,'LG2')]; e=u*4/20; a=sum(int(x['count']) for x in tx[(m,'LG2')].values())/60
  print(m,u,'%.1f %.1f | %.1f %.1f %.1f'%(e,a,50-a,50-e,e-a))
  if 16<=m<=22: S[0]+=50-a;S[1]+=50-e;S[2]+=e-a
print('sum 16-22 shortfall %.1f users %.1f pace %.1f'%tuple(S))
"
```
Output: minute 16 users 250, expected 50.0, achieved 45.6 (pace 4.4); 17: 225, 45.0, 40.5 (users 5.0, pace 4.5); 22: 80, 16.0, 14.2 (users 34.0, pace 1.8); 23: 80, 16.0, 15.6 (pace 0.4). Sum 16–22: shortfall 157.1, users 136.0, pace 21.1 TPS-minutes.
