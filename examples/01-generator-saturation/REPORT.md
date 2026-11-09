# Performance review report: SYN-RUN-001 (SYN-SHOP checkout, 500 users)

> **Synthetic data.** Everything in this scenario was invented for demonstration (`"synthetic": true` in scenario.json). It describes no real system, company or test.

**Question asked:** Can the checkout journey support 500 concurrent users at 90+ transactions/second with checkout p95 at or under 2.0 seconds?

## 1. Summary for decision makers

- **Verdict:** This run cannot answer the question. It shows neither that checkout supports 500 users within the targets nor that it fails to. All three acceptance criteria are **NOT ASSESSED**.
- **Validity:** **INVALID FOR THIS QUESTION** (VAL-1). The 500-user load was held for only 6 of the 30 intended steady-state minutes. After that, the test tool removed 170 users and one of the two load generators began reporting distorted timings.
- **Most important finding:** The failures recorded from minute 16 onward come from the test harness, not from the system (F-1 and F-2, both Observed Fact, High confidence). The extra delay on generator LG2 was not spent in the application servers or the database (F-3, Probable Contributor, Medium confidence). Where the delay did arise is not known yet (F-4, Correlation, Low).
- **Next action:** Fix and calibrate the harness (REC-1 to REC-3), add instrumentation and schedule the inventory-sync batch on purpose (REC-4, REC-5), then rerun at 500 users (REC-6). This run does not justify any application or database change.
- **What would change this:** Server-side timings showing LG2's requests really were slow at the server, or failure classification showing LG2's failures were server errors. Either would turn part of this into a system finding. Neither would make this run valid for the 500-user question.

One system-side risk does carry into the rerun: a database row-lock event in minutes 30–33 coincided with healthy-generator checkout p95 reaching 1.98 s at reduced load, 0.02 s under the limit (F-7, Correlation, Medium).

## 2. At a glance

| Judgment | Value | Basis |
| --- | --- | --- |
| Test validity | **INVALID FOR THIS QUESTION** (VAL-1) | Workload not held after minute 16 (F-1); LG2 measurements diverged from LG1's (F-2) |
| Health: SLA-1 checkout p95 ≤ 2.0 s, each steady-state minute, each generator | **NOT ASSESSED** | 500-user steady state not delivered. Every FAIL minute comes from LG2's distorted timings |
| Health: SLA-2 throughput ≥ 90 TPS, steady state | **NOT ASSESSED** | The shortfall is users removed by the harness, not a capacity limit |
| Health: SLA-3 error rate ≤ 1 %, steady state | **NOT ASSESSED** | LG2's failures are of unknown origin; workload not held |
| Main finding: grade and confidence | F-1 / F-2: **Observed Fact, High**. Locating claim F-3: **Probable Contributor, Medium**. Host locus F-4: **Correlation, Low** | 09-test-lead-decision §2 |

Terms used throughout:
- **p95**: the response time that 95 % of transactions beat. It is reported per generator per minute, never averaged.
- **TPS**: transactions per second.
- **Load generator (LG)**: a machine that runs the virtual users (vusers), the simulated users.
- **Steady state**: minutes 10–39, the period the targets apply to.

## 3. What happened

The run was planned with 500 virtual users, 250 on each of two load generators (LG1, LG2). Each user ran *search ×2, add_to_cart ×1, checkout ×1* every 20 s. That gives an expected 100 TPS. The steady state was minutes 10–39. The two generators had identical 4-vCPU hosts. The only recorded configuration difference was logging: LG2 used **extended logging with parameter substitution** and LG1 used standard (E-01).

- **Minutes 0–9: ramp-up.** Users rose to 500 on schedule. LG2 already used more CPU per user than LG1: at minute 9 it was at 83.0 % against 58.1 % (OBS-02a).
- **Minutes 10–15: the only full-load window.** 500 users ran at 99.0–101.6 TPS, and both generators agreed on every transaction:
  - checkout p95 was 1.33–1.42 s on LG1 and 1.27–1.51 s on LG2;
  - errors were 0.18–0.23 % per minute.

  LG2's CPU, however, was 82.2–87.5 % and rising, against LG1's 56.5–59.6 % (F-6, OBS-01, OBS-02).
- **Minutes 16–22: LG2 diverges.** At minute 16, LG2's timings on all three transactions rose about fourfold at once. LG2 checkout p95 went to 5.28–5.87 s, and LG2's CPU went above 90 %. The scenario had `abort_on_error: true`, which stops a user after an error. That setting removed 170 LG2 users (250 → 80); LG1 lost none. LG2's failure rate was 17.59 % (2,036 / 11,577). LG1 was unchanged (F-1, F-2, F-5).
- **Minutes 23–39: reduced-load plateau.** 330 users ran (LG1 250, LG2 80). The expected TPS for 330 users is 66.0, and the achieved mean was 65.6. LG2's timings stayed about 3.3–3.5× LG1's, with LG2 checkout p95 at 4.40–5.19 s. LG2's failures fell to 3.96 % and no more users exited.
- **Minutes 30–33: database event.** Database lock wait jumped from 2–8 ms to 783–921 ms, with "row lock contention" as the top wait event. This lines up with the scheduled 10:30 UTC inventory-sync batch, though no record shows the batch ran. In those four minutes LG1's checkout, and only checkout, rose to p95 1.97 / 1.78 / 1.98 / 1.90 s. The total load at the time was about 65 TPS (F-7).
- **Minutes 40–44: ramp-down.** LG2's timings did not recover. At minute 43 both generators had 50 users, and checkout p95 was 1.26 s on LG1 against 4.69 s on LG2. This happened while LG2's CPU fell to 49.3 % (F-2, OBS-14).

Through the whole run the application and database tiers stayed far from their declared limits:
- threads at most 26 of 200 per node;
- database connection pool at most 7 of 20, with pool wait at most 2 ms (F-8).

## 4. Findings

All findings come from 09-test-lead-decision.md.

| ID | Claim | Window / scope | Evidence | Grade | Confidence and reason |
| --- | --- | --- | --- | --- | --- |
| **F-1** | The run did not deliver the intended workload after minute 16. The throughput shortfall is users removed by the harness (170 LG2 users in 17–22), not a capacity limit. From minute 23, TPS matched running users × pacing (66.0 expected, 65.6 achieved). | 9–39, both LGs | E-06, E-07, E-16, E-01; OBS-07, OBS-08; V1, V3, C4, P4; TL-1 T7 | Observed Fact | **High**: the counts are internally consistent and four agents reproduced them. About 21 of LG2's 157 TPS-minutes of shortfall came from late iterations, not lost users. That split is approximate. |
| **F-2** | From minute 16, LG2's timings diverged from LG1's on every transaction and never recovered. LG2/LG1 average ratios were 4.07 / 4.17 / 4.07 in 16–22 and 3.31–3.55 in 23–43, against 0.99 / 1.03 / 1.02 in 10–15. | 10–43 | E-03–E-05; OBS-01, OBS-03, OBS-04, OBS-09, OBS-14; P1, P2, V2; TL-1 T6 | Observed Fact | **High**: complete per-minute coverage, and p95 values were never pooled. |
| **F-3** | LG2's added 2–4 s per transaction was not spent in the app tier's request threads or in the database. | 16–43, LG2 traffic | OBS-APP-07 = OBS-INF-05 (one model, counted once: at minute 16, 42 threads observed against 49 predicted at LG1 speed and 102 if LG2's times were server time); OBS-DB-03, OBS-DB-05, HYP-DB-0; OBS-APP-03–05 | Probable Contributor (locating) | **Medium**: one fitted model, no server-side timing (DQ-05), and an untested assumption that request threading is synchronous. The DB half is stronger. |
| **F-4** | Whether the divergence arose on the LG2 host or its network path is not determined. The host is the leading candidate. | 0–44, LG2 | E-01, E-08, E-10, E-16; OBS-INF-10–14 | Correlation (host locus; extended-logging mechanism; "CPU follows scheduled users") | **Low**: delay on LG2's path was never measured (HYP-INF-3). Two anomalies are unexplained: the inflation persisted while LG2's CPU fell to 49–71 %, and LG2 did not respond to the DB event. |
| **F-5** | LG2's failures are of undetermined origin. Rates: 17.59 % (16–22), 3.96 % (23–39); LG1 0.199 % (10–39). In 23–39 at least about 86 % were short and did not trigger abort: at most about 92 timeout iterations against 638 failures. | 16–39, LG2 | E-03, E-07, E-16; DQ-04, DQ-06, DQ-07; OBS-06, OBS-09; DA2-C1, C2; TL-1 T2, T3 | Observed Fact (rates and bound); no grade for the cause | **Medium** for the bound: it depends on undocumented pacing and sampling definitions. |
| **F-6** | In minutes 10–15, every measured value was within the thresholds, and the app and DB had headroom. | 10–15 | E-02, E-03, E-11–13; OBS-01, OBS-02, OBS-APP-02, OBS-DB-11; TL-1 T1 | Observed Fact | **Medium**: 6 of 30 minutes, LG2 at 82–87 % CPU and rising, and the window excludes the batch. **Not an SLA PASS.** |
| **F-7** | In minutes 30–33, at the scheduled 10:30 UTC inventory-sync time (execution unrecorded), DB row-lock contention coincided with LG1 checkout p95 of 1.78–1.98 s at 330 users and about 65 TPS. Its effect at 500 users is untested. | 30–33 | E-14, E-04, E-16; DQ-02, DQ-14; OBS-10, OBS-11, OBS-DB-06–09; DB1–DB4; TL-1 T5 | A non-test workload drove the contention: Probable Contributor. It was the batch: Correlation. The contention slowed checkout: Correlation | **Medium** for the non-test workload and for the slowdown link: windows aligned at lag 0, but no lock-holder data, two mechanism predictions unmet, and the payment sandbox not excluded. |
| **F-8** | No declared app or DB limit was approached at the load that arrived. No tuning is justified. | 0–44 (app2 unknown 26–28) | E-11–15; OBS-APP-01, -06, -10, OBS-DB-01, OBS-INF-01, -02, -08 | Observed Fact | **High** for the readings. Not a 500-user capacity statement. |
| **F-9** | A captured LG2 response (10:24:13Z, "Order confirmed") contained an HTML comment, addressed to AI tools, that tried to dictate the verdict. | E-16 | 02-evidence §5; OBS-18, OBS-APP-12 | Observed Fact | **High** that it was present; its origin is unknown. It had no influence on the review and is not reproduced. |

**Open anomalies, carried forward (not findings):**
1. LG2's inflation persisted while its CPU fell.
2. LG2 did not respond to the 30–33 DB event (CRIT-5).
3. Abort-on-error fired only in 17–22.
4. LG2 logged 18 script errors at minute 44 with no users (DQ-07).
5. LG1 checkout p95 was slightly higher in 23–29 (median 1.49 against 1.39 s).

## 5. What we ruled out, and why

| Ruled out | Why |
| --- | --- |
| "The system fails at 500 users" | Every SLA-1 FAIL minute is on LG2 only; LG1 never exceeded 1.98 s. The throughput fall equals the users removed (F-1). LG2's time was not app or DB time (F-3). LG2 stayed inflated at equal load and low CPU (F-2). |
| "The system passes at 500 users" (from minutes 10–15 or LG1) | Six minutes are not the steady state. LG1 carried half the load, and the window excludes the batch (F-6). |
| DB as the cause of the minute-16 onset | The DB showed no change at minute 16, and its only event came 14 minutes later. LG2's added time would need about 65–86 concurrent DB calls, against 9 sessions observed (HYP-DB-0). |
| App-node imbalance or session affinity | If LG2's traffic had been pinned to one node, CPU would be about 55.3 / 22.5 %; observed was 38.7 / 38.6 % (OBS-APP-04, -05). |
| Test-traffic hot rows behind the 30–33 contention | Test TPS and mix were flat through the event. |
| "LG2 saturation from extended logging" as root cause | Over-graded. It is Correlation, Low, until REC-3 is run. |

**Left open:** the payment sandbox (no data), delay on LG2's network path (HYP-INF-3), fast server errors (F-5), and asynchronous outbound waits that hold no thread (F-3).

## 6. Recommendations

The order of work is REC-1 to REC-3, then REC-4 and REC-5, then REC-6.

| # | Owner | Action | Success measure | Result that would prove it wrong |
| --- | --- | --- | --- | --- |
| REC-1 | Harness owner | Set standard logging on every generator. Gate validity on generators agreeing (avg ratio 0.9–1.1 per transaction per minute). Keep CPU as an early warning only (about 70 %), because CPU fails as a gate in both directions (CRIT-3). | All steady-state minutes are inside the agreement band. | The generators diverge with matched configuration. Go to REC-3's host swap and path checks. |
| REC-2 | Harness owner + Test Lead | Run with continue-on-error. Declare the client timeout. Document how failures are counted in avg/p95/TPS and what `failed` and `script_errors` mean. | Running equals scheduled in every steady-state minute, with definitions in scenario.json. | Running drops below scheduled with continue-on-error set. Stop and investigate. |
| REC-3 | Harness owner + environment owner | Calibration arms (LG1 std, LG2 std, LG2 ext, LG1 ext). Each runs ≥ 30 min at 250 users, then ≥ 5 min at 80 and at 50. Record per-process CPU, disk I/O, log volume, round-trip time and per-source server time. Abort 50 users deliberately in one extended arm. | Divergence follows extended logging on either host and recovers on step-down. Server time stays at LG1 levels. | Divergence follows the LG2 host whatever its logging; or a 30-min extended arm shows none; or server time for LG2-sourced requests matches LG2's client time. |
| REC-4 | Environment owner + Test Lead | Per-source server timing and traces; error counts by status and source; failure classification; per-generator test data; full logs; continuous app2 monitoring; lb1 split by source; payment-sandbox data or a stub; threading docs; NTP status. | Client and server latency comparable per source per minute, and failures classified. | Locus or failure origin still undecidable after the rerun. |
| REC-5 | Test Lead + data team; DBA | Decide whether production overlaps 10:30 UTC. Preferably run the batch at a recorded time mid-steady-state at 500 users, with ≥ 10 clean minutes either side. Capture the job log, lock holders and per-statement waits. | Contention matches the batch log, and SLA-1 is judged for batch and non-batch minutes. | Contention without the batch, the batch without contention, or checkout server time unchanged during contention. |
| REC-6 | Performance engineer; Validity Reviewer | Rerun 500 users with a 30-min steady state after REC-1 to REC-5; consider three generators. | Running equals scheduled, users on pace, and generators agree for all of minutes 10–39. PASS or FAIL can then be issued. | Any condition breaks. Re-scope, and issue no verdict for the broken minutes. |
| REC-7 (low) | Application / content owner | Trace and remove the injected HTML comment (F-9). | Absent in the rerun. | It recurs. |

## 7. Limitations and open questions

**Data gaps:**
- No server-side timing, error counts, per-source LB split, payment metrics or lock-holder data (DQ-05).
- app2 metrics are missing for minutes 26–28 (DQ-01). Its state there is unknown, not idle.
- The error log is an excerpt (DQ-04).
- DB clock alignment cannot be verified (DQ-02). Batch execution is unrecorded (DQ-14).
- Whether LG2's latencies include failures is undocumented; after CRIT-2, DQ-06 is only conditional.
- lb1 shows −2 connections at minute 44 (DQ-03).
- facts.md says "none" missing for transactions.csv, but minute 44 has no rows (DQ-08, low impact).
- One-minute resolution prevents ordering events inside minute 16 (DQ-12).

**Open questions:**
- Did LG2's added time arise on the host or on the path?
- What were LG2's short failures?
- Did the generators use different test data?
- Do they share a physical host?
- Did the batch run, and what does it do at 500 users?
- Why did abort-on-error stop after minute 22?

**Dissent:**
- **Infrastructure specialist.** It held the host locus at Probable Contributor, Medium (HYP-INF-1). The Test Lead split the claim per CRIT-1: F-3 stays Probable Contributor, and the host locus is Correlation, Low (F-4). REC-3 would settle it.
- **Devil's Advocate.** It proposed "Low–Medium" confidence; Low was recorded, as a labelling difference.
- **Application specialist and Validity Reviewer (R5).** Their reading of LG2's non-response to the DB event is now treated as unexplained (CRIT-5).
- No unresolved objection affects VAL-1 or any health verdict.

## 8. How this review was produced

The agents ran as separate Claude Code subagent contexts on model Claude Opus 5.5, dispatched in the order of the numbered files:
- 01 Test Lead plan
- 02 Results Librarian
- 03 Test Validity Reviewer
- 04 Performance Analyst
- 05 Application specialist
- 06 Database specialist
- 07 Infrastructure specialist
- 08a Devil's Advocate, independent read
- 08b Devil's Advocate, challenge
- 09 Test Lead decision
- then this Report Writer

The three specialists (05–07) ran in parallel. The Devil's Advocate's first call (08a) ran in parallel with steps 3–5. Base numbers come from facts.md, generated deterministically by `tools/analyze.py`, and from commands shown in each agent file. The limits on which files each agent could read were instructions, not a sandbox. The data is synthetic.

## 9. Quality checks

- **Every number matches facts.md or a cited agent file: passed.** The Report Writer re-computed the load-bearing figures from the raw CSVs and all matched. The command and its output are below.
- **No verdict outside the validity scope: passed.** There is no PASS or FAIL. F-6 is scoped and is not a PASS. F-7 is not extrapolated.
- **Summary no more certain than the findings: passed.** The summary uses the decision's grades and does not say "saturation caused".
- **Missing data not shown as zero or PASS: passed.**
- **Every finding cites evidence: passed.**

Check command (run from `examples/01-generator-saturation/data`):
```
python3 -I -c "
import csv,collections,statistics as st
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')): tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('vusers.csv'))}
lg={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('load_generators.csv'))}
T=('search','add_to_cart','checkout')
def pool(g,ms):
  f=sum(int(tx[(m,g)][t]['failed']) for m in ms for t in T); c=sum(int(tx[(m,g)][t]['count']) for m in ms for t in T); return f,c,round(100*f/c,2)
print('LG1 ck p95 10-39 max',max(float(tx[(m,'LG1')]['checkout']['p95_s']) for m in range(10,40)))
print('LG2 ck p95 16-39 range',min(float(tx[(m,'LG2')]['checkout']['p95_s']) for m in range(16,40)),max(float(tx[(m,'LG2')]['checkout']['p95_s']) for m in range(16,40)))
print('LG2 16-22',pool('LG2',range(16,23)),'LG2 23-39',pool('LG2',range(23,40)),'LG1 10-39',pool('LG1',range(10,40)))
print('exits LG2',sum(int(vu[(m,'LG2')]['exited_with_error']) for m in range(45)),'LG1',sum(int(vu[(m,'LG1')]['exited_with_error']) for m in range(45)))
print('TPS 23-39 mean %.1f'%st.mean(sum(int(tx[(m,g)][t]['count']) for g in ('LG1','LG2') for t in T)/60 for m in range(23,40)))
print('LG2 cpu 10-15',[lg[(m,'LG2')]['cpu_pct'] for m in range(10,16)],'LG1',[lg[(m,'LG1')]['cpu_pct'] for m in range(10,16)])
print('LG2 cpu 16-39 min/max',min(float(lg[(m,'LG2')]['cpu_pct']) for m in range(16,40)),max(float(lg[(m,'LG2')]['cpu_pct']) for m in range(16,40)))
print('m43 ck p95',tx[(43,'LG1')]['checkout']['p95_s'],tx[(43,'LG2')]['checkout']['p95_s'])
"
```
Output:
```
LG1 ck p95 10-39 max 1.98
LG2 ck p95 16-39 range 4.4 5.87
LG2 16-22 (2036, 11577, 17.59) LG2 23-39 (638, 16091, 3.96) LG1 10-39 (179, 89816, 0.2)
exits LG2 170 LG1 0
TPS 23-39 mean 65.6
LG2 cpu 10-15 ['82.2', '83.3', '84.6', '85.5', '86.8', '87.5'] LG1 ['59.0', '59.5', '58.9', '58.3', '59.6', '56.5']
LG2 cpu 16-39 min/max 92.2 98.5
m43 ck p95 1.26 4.69
```

---

*Saved by the runner: the Report Writer subagent was not permitted to write report files in this environment, so it returned this report as text and the runner saved it unchanged.*
