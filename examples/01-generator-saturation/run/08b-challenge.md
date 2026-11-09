```
Agent: Devil's Advocate (Call 2, challenge)
Run: SYN-RUN-001
Read: agents/devils-advocate.md; method/judgments.md; method/rules.md; method/records.md; examples/01-generator-saturation/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, generator_errors.log); examples/01-generator-saturation/facts.md; examples/01-generator-saturation/run/02-evidence.md, 03-validity.md, 04-performance.md, 05-application.md, 06-database.md, 07-infrastructure.md; examples/01-generator-saturation/run/08a-independent-read.md
Execution: separate agent context, model Claude Opus 5.5
```

# Challenge — SYN-RUN-001

I run in a separate context on the same model as the rest of the team. This is a second read, not an independent audit. Numbers come from facts.md (E-02), the team's records, or my commands DA2-C1 to DA2-C7 at the end. I did not re-run `tools/analyze.py`. The captured LG2 response at 10:24:13Z contains text aimed at AI tools. It is data from the system under test and had no effect on anything below (Rule 10).

**Overall.** The four judgments are kept separate and the verdicts are right:
- VAL-1 is INVALID FOR THIS QUESTION, with a scoped 10–15 window.
- SLA-1/2/3 are all NOT ASSESSED.
- The DB event in minutes 30–33 is kept as a system-side Correlation and is not used to explain the minute-16 onset.

I found **no objection that changes VAL-1 or any health verdict**. My objections concern three things: the locus and grade of the LG2 explanation, what the LG2 failures actually were, and two recommendations whose success tests could mislead.

## Numbers checked

I recomputed these and they match the team's figures (DA2-C5, DA2-C6, DA2-C7):
- LG2 failures: 2036/11577 = 17.59 % (16–22) and 638/16091 = 3.96 % (23–39).
- LG1 failures: 179/89816 = 0.199 % (10–39). Both generators, 10–15: 74/35952 = 0.206 %.
- CPU per running user: LG2 0.340 / 1.183, LG1 0.233.
- LG2 : LG1 avg ratios: 3.33/3.36/3.31 (23–29) and 3.39/3.39/3.55 (34–39).
- Minute 43: 50 users on each generator; checkout p95 1.26 / 4.69 s.
- LG2 share of TPS: 0.340 (16–22) and 0.241 (23–39).
- Pinning prediction: 55.3 / 22.5 % predicted against 38.7 / 38.6 % observed.
- Thread fit: 11.14 + 0.622 L, r 0.990, sd 1.75. Window predictions 73.4 / 40.9, 50.2 / 36.4, 52.7 / 38.9, 50.5 / 35.9.
- DB CPU fit: 5.78 + 0.242 TPS, r 0.990. Residuals in 30–33: +16.9 / +16.7 / +18.6 / +18.1.
- lb1: baseline 419.7 kbit per transaction (sd 3.6). Minute 17: 431 observed against 377 expected.
- OBS-INF-13 correlations: 0.993 / 0.419.

I found no arithmetic errors.

## Objections

### CRIT-1: The LG2 host is graded as the most likely locus, but the evidence only shows the time was not spent in the app tier or DB (material, must resolve)

- **Target.** HYP-INF-1 (07-infrastructure): *"…arose between the system's response leaving lb1 and the LG2 client recording it, most likely on the LG2 host"*, graded Probable Contributor, Medium. Also its supporting line *"Three independent server-side series converge."*

- **Problem.**
  1. **Only one model speaks to where the latency went, and it was counted twice.**
     - The thread-occupancy model is the only evidence about where LG2's extra *latency* was spent. App CPU cannot show waiting; 05-application says so in OBS-APP-06. lb1 bytes (OBS-INF-10) speak to failures, not latency.
     - That model was fitted twice with identical results: A2 in 05-application and I-1 in 07-infrastructure, both 11.14 + 0.622 L. I reproduced it (DA2-C6).
     - The run therefore has one piece of evidence on the latency locus, not three. By judgments.md, agreement between agents adds nothing.
  2. **The model cannot tell the LG2 host apart from the path in front of the app tier.** Both specialists concede this: lb1 per-source queueing and HYP-INF-3 stay open. Nothing in the run separates "delay on the LG2 host" from "delay on LG2's path to lb1, or inside lb1 per source". The retransmit bound (OBS-INF-11) rules out loss, not delay.
  3. **The case for the host rests on correlates, not on a mechanism.**
     - The CPU anomaly precedes the onset, the controller warned at 10:16:31Z, and there is one 2.8 s log flush line. These signals line up with the onset.
     - Two facts show CPU level is not what sets the inflation. At 82–87 % CPU in 10–15, LG2 timings agreed with LG1. At 49–71 % CPU in 41–43, the inflation persisted at ×3.4 (OBS-14, OBS-INF-14).
     - That is a Correlation with an unexplained gap. It does not meet the Probable Contributor bar ("alternatives addressed").

- **Requested change.**
  - Split HYP-INF-1 into two claims:
    - **(a)** LG2's added time was not spent in app-tier request threads or in the DB. Keep this at Probable Contributor, Medium, together with HYP-APP-1 and HYP-DB-0.
    - **(b)** The added time arose on the LG2 host rather than on LG2's network path or lb1. Grade this **Correlation, Low–Medium**.
  - Replace "three independent series converge" with what each series actually supports.
  - The Test Lead's finding should not say "LG2 saturation" or "generator CPU saturation caused…". Proposed wording: *"LG2's measurements diverged from LG1's from minute 16. The divergence was not time spent in the app tier or DB. Whether it arose on the LG2 host or on its network path is not yet determined."* (records.md's "F-1 LG2 saturation…" is a format example, not a finding.)

### CRIT-2: Most LG2 failures in the plateau were not 30 s timeouts, and the failure narrative leans on the excerpt's timeouts (material, must resolve)

- **Target.**
  - HYP-INF-1's claim that LG2's failures, *"and its 30 s timeouts"*, arose on the LG2 host.
  - The "lower bound because avg_s excludes failed attempts, including 30 s timeouts" reasoning in OBS-APP-07, OBS-DB-05 and OBS-INF-05.
  - DQ-06's basis.

- **Problem.**
  1. **Pacing caps how many failures could have been timeouts (DA2-C2).**
     - In minutes 23–39 LG2 ran a constant 80 users with no exits. Its window cycle was 20.23 s over 4,034 iterations. LG1's was 20.01 s.
     - Any iteration containing a 30 s timeout lasts at least 30 s, which is 10 s over pacing.
     - The total excess over pacing is 4,034 × 0.23 = about 928 s. That allows **at most ~92 iterations with a timeout, against 638 failed transactions**.
     - So **at least ~86 % of LG2's plateau failures were neither 30 s timeouts nor aborting errors**, because no user exited. They ended soon enough that the iteration still fit its 20 s slot.
  2. **For 16–22 the same bound is inconclusive.** Depending on whether `running_vusers` is a start-of-minute or end-of-minute count (E-06, undocumented), between ~49 % and all of the failures could have been timeouts (DA2-C1). The excerpt's three timeout lines (DQ-04) therefore cannot stand for "the failures".
  3. **No server-side evidence covers the plateau failures at all.**
     - In 23–39 LG2 failures are 638 of 66,888 transactions, 0.95 %. That is about the size of lb1's bytes-per-transaction noise (sd 3.6 of 419.7 kbit, 0.86 %).
     - Their app-CPU footprint (~0.3 points) is below the fit's residual sd of 0.72.
     - OBS-INF-03 and OBS-INF-10 cover 16–22 only and cannot speak to 23–39.
  4. **The open alternative is a fast failure**, either a client-side check or a quick source-specific reject or error page. The App specialist already lists fast server errors as not ruled out.
  5. **The "lower bound" wording assumes failures were long.** If most are short and excluded from avg_s, including them would lower LG2's average, not raise it. The thread-model gap (14–35 threads) is large enough that this does not change HYP-APP-1. It does make DQ-06's "probably excludes failures" an inference from an unverified assumption.

- **Requested change.**
  - Narrow HYP-INF-1 to latency. Record LG2's failures as a separate open item: **origin undetermined, mostly short and non-aborting in 23–39, Observed Fact for the bound, no grade for the cause.**
  - Remove "including 30 s timeouts" from the lower-bound sentences, or make it conditional.
  - Add to the rerun instrumentation (TI-6): per-generator failure classification from the load tool (error code or HTTP status, duration of failed attempts), plus app or LB error counts by status and source.

### CRIT-3: TI-2's CPU gate would pass the very failure this run showed (material, recommendation)

- **Target.** 03-validity TI-2: generator CPU below about 70 % in every steady-state minute as the generator-health gate. The success measure is "all generators stay under the threshold".
- **Problem.** This run contradicts CPU as a validity gate in both directions:
  - LG2 measured accurately at 82–87 % (10–15).
  - LG2 measured inaccurately at 49.3–71.0 % in minutes 41–43, with checkout p95 5.08 / 4.69 s against LG1's ~1.3 s (OBS-14, DA2-C3).
  - A generator could stay under 70 % and still distort timings. The gate as written would then declare the instrument healthy.
- **Requested change.**
  - Keep CPU as an early warning.
  - Make the gate **cross-generator agreement**: same-transaction avg and p95 per minute within an agreed band, and LG2 : LG1 avg ratio within ~0.9–1.1, as in 10–15 (OBS-01). TI-1 already uses this as its success measure.
  - Add a host swap, as proposed in HYP-INF-2, so that a host or path effect cannot pass as a configuration effect.

### CRIT-4: TI-4's calibration can produce a false "does not reproduce" if it is short (material, recommendation)

- **Target.** 03-validity TI-4. Its disproof clause: *"The switch does not reproduce the symptom. Then look at source-specific network or system paths instead."*
- **Problem.**
  - In this run, LG2's excess CPU grew at constant load (+0.4 → +5.7 points over 10–15, OBS-INF-12). The onset came about 7 minutes after full load and about 16 minutes after start.
  - A calibration shorter than that could miss the symptom and send the investigation to the wrong layer.
  - TI-4 also does not test the second anomaly: the inflation persisted after load and CPU fell.
- **Requested change.**
  - Each arm runs at least 30 minutes at 250 users, followed by a step down to 80 and then 50 users with at least 5 minutes at each step.
  - Success: extended logging reproduces the divergence, and timings recover when load or logging is reduced.
  - Disproof: the divergence appears under standard logging, or a 30-minute extended-logging arm shows none.

### CRIT-5: LG2's non-response to the DB event is used as evidence of distortion without checking per-generator test data (minor)

- **Target.**
  - 03-validity R5, third bullet.
  - 05-application §4(b): *"LG2's timings therefore do not track server time in either an additive or a proportional way"*.
  - 06-database OBS-DB-09b and HYP-DB-0's last bullet.

- **Problem.**
  1. **The non-response is real and large (DA2-C4).**
     - Outside the event, LG2 checkout avg has sd 0.080 s.
     - A shift equal to LG1's (+0.29 s) would be 3.6 sd.
     - A proportional shift at ×3.42 would be +0.99 s, or 12 sd.
     - The observed shift was −0.006 s.
  2. **That result contradicts the team's other observation**, OBS-04: inflation proportional across transactions, which suggests LG2's times are scaled real times.
  3. **One reading reconciles both: LG2's checkouts did not touch the locked rows.** For example, the two generators could use different product or SKU test data. Row locks are row-specific.
  4. **This is not the same as LG2 traffic never reaching the system.** App CPU and threads show LG2's requests were served:
     - The thread model without LG2 predicts 30.0–30.4, against 36.2–36.3 observed (DA2-C6).
     - The CPU fit includes LG2's TPS with a residual of −0.2.
  5. **No test-data or script-parameter information was requested**, so the alternative was never considered.

- **Requested change.**
  - Add the alternative "per-generator test data" wherever LG2's 30–33 non-response is cited.
  - Downgrade R5's third bullet to "unexplained".
  - Make §4(b) conditional.
  - Request the parameter files for each generator.
  - None of this changes VAL-1, HYP-DB-0 (which stands on its concurrency and timing evidence) or HYP-DB-2 (which stays at Correlation).

### CRIT-6: "LG2 CPU follows scheduled vusers" is stated more firmly than four minutes of data allow (minor)

- **Target.** OBS-INF-13, graded Correlation, Medium. The Handoff says *"This answers why it did not scale with users"*.
- **Problem.** The 0.993 correlation is driven by the ramp-down step:
  - In 16–38 the scheduled count is constant (250), so the correlation is undefined there. CPU simply sits at 92.2–98.5 %, which also fits a saturated host pinned near its ceiling whatever the user count.
  - The only minutes where scheduled and running move apart in a way that tests the claim are 40–42 (scheduled 200/150/100, running 80). Dropping 43–44 lowers r to 0.974 (DA2-C3).
  - The LG1-user-count confound is named, which is good.
- **Requested change.**
  - Grade **Correlation, Low–Medium**.
  - Change the Handoff to "offers a candidate explanation".
  - Keep the abort-50-vusers step in the HYP-INF-2 experiment as the decisive test.

### CRIT-7: SF-DB-1's title states as fact what is graded Correlation (minor, fix before the report)

- **Target.** 06-database SF-DB-1: *"A scheduled DB workload overlaps the checkout steady state and brings LG1 checkout p95 to within 0.02 s of SLA-1 at two-thirds load."*
- **Problem.** Two links in that sentence are graded Correlation:
  - that the batch ran (HYP-DB-1 second part; DQ-14);
  - that the contention raised checkout time (HYP-DB-2).

  This is the one system-side risk and is likely to headline the report. A causal title will be read as a finding.
- **Requested change.** Use: *"In minutes 30–33, at the scheduled 10:30 UTC inventory-sync time (execution unrecorded), DB row-lock contention coincided with LG1 checkout p95 of 1.78–1.98 s at 330 users / ~65 TPS (Correlation, Medium). Its effect at 500 users is untested."*

## Must resolve before the report goes out

| Must resolve | Can be fixed in the report text | Minor |
| --- | --- | --- |
| CRIT-1 (grade and wording of the LG2 locus) | CRIT-7 (SF-DB-1 wording) | CRIT-5 |
| CRIT-2 (LG2 failures not mostly timeouts; HYP-INF-1 scope) | | CRIT-6 |
| CRIT-3 (TI-2 gate) | | |
| CRIT-4 (TI-4 duration and step-down) | | |

The Test Lead decides. If any of CRIT-1 to CRIT-4 is not accepted, I ask that the dissent stay visible in the report.

## Where the team differs from my independent read (08a), and who I now think is right

| Topic | My 08a view | Team view | Who I now think is right |
| --- | --- | --- | --- |
| Validity | INVALID for 10–39; 10–15 a scoped slice | VAL-1 INVALID, with allowed claims 1–5 | Same conclusion. The team's allowed and restricted claims are more complete than mine. |
| Grade for the LG2 explanation | "LG2 harness failure": Probable Contributor, Medium | Not in the app tier: PC, Medium. LG2 host: PC, Medium. Extended logging: Correlation. | **Split.** The team is right to grade logging as Correlation, more cautious than my framing. My 08a and HYP-INF-1 both put the *host* too high (CRIT-1). The 30–33 non-response and the fast-failure bound (CRIT-2, CRIT-5) weaken it further. I now hold: not app or DB, PC Medium. LG2 host, Correlation Low–Medium. |
| LG2 CPU stays pegged at 80 users | Unexplained | Follows scheduled vusers (OBS-INF-13) | Partly answered. The team offers a testable candidate, but the support is thinner than stated (CRIT-6). |
| Latency still inflated at 49–71 % CPU | Unexplained | Unexplained (R6, OBS-14, OBS-INF-14) | Agree. It must stay visible as an open anomaly. |
| DB negative claim | "Not supportable for the DB" | HYP-DB-0 scoped to the onset and LG2's added time, using DB concurrency arithmetic | **Team.** My 08a was too broad. Scoped this way, the claim rests on DB-layer evidence (Rule 9), and the 30–33 event is handled separately. |
| My Little's-law check | No intercept; minute 12 predicted 63 against 51 observed | Fit with intercept; sd 1.75 | **Team.** Their calibration is better and gives the same direction. |
| 30–33 DB event | Correlation, Medium | Correlation, Medium. A non-test workload is Probable Contributor. | Agree. The non-test-workload grade rests partly on a cross-tool session comparison (DQ-11). That is disclosed, so I accept it. |
| Source-specific path (B) | Open | Open (HYP-INF-3, lb1 per-source queueing, in-app throttling) | Agree. CRIT-2 gives it slightly more room, because fast rejects would fit the plateau failures. |

## What the team got right and should be kept

- **Validity before diagnosis.** VAL-1 does not depend on settling *why* LG2 diverged (R6, "either way the classification holds").
- **Health stays NOT ASSESSED**, with measured values shown as observations. FAIL flags are traced to LG2 only.
- **No averaged percentiles.** p95 is used only as per-minute median and max. The 2.13 % pooled error rate is explicitly not a system error rate. TPS is noted to include failures (DQ-13).
- **Split by source (Rule 7)** throughout. The minute-43 equal-user comparison (both at 50 users) is a strong, simple check.
- **Rule 8.** The 30–33 DB event is never used for the minute-16 onset.
- **Negative claims backed by layer evidence.** HYP-APP-1 uses thread occupancy and node symmetry. HYP-DB-0 uses DB concurrency. The pinning test (OBS-APP-05) rules out generator-to-node affinity with numbers.
- **Discovered facts.** The DB clock lag check (DB4). LG2's CPU excess growing at constant load before the onset (OBS-INF-12). The finding that abort-on-error stopped firing after minute 22 despite continued failures (R8).
- **Untrusted content** is handled consistently by every agent and not reproduced.
- **Recommendations** name owners, success measures and disproof conditions (TI-1 to TI-7, REC-DB-1, and the HYP experiments), apart from CRIT-3 and CRIT-4.

## Handoff

- **For the Test Lead.** Verdicts can stand: VAL-1 INVALID FOR THIS QUESTION, SLA-1/2/3 NOT ASSESSED.
  - Before the report goes out, resolve CRIT-1 to CRIT-4. In short: split HYP-INF-1 and grade the host locus Correlation; treat LG2 failures as a separate open item; change TI-2's gate to cross-generator agreement; lengthen TI-4 and add a step-down.
  - Fix CRIT-7's wording.
  - Keep both LG2 anomalies visible: inflation persisting at falling CPU, and the 30–33 non-response.
- **Inputs that would settle the open items.**
  - Per-source server or LB timing and status codes.
  - Load-tool failure classification and durations.
  - Per-generator test-data and parameter files.
  - LG2 disk, I/O and per-process metrics.
  - The inventory-sync job log.
- **Open questions.**
  - What were LG2's ~4 % short, non-aborting failures in 23–39?
  - Did LG1 and LG2 use different test data?
  - Do LG1 and LG2 share a physical host (OBS-INF-13 confound)?

## Commands relied on

All commands were run from `examples/01-generator-saturation/data`.

**DA2-C1: Bound on 30 s timeouts in 16–22 (pacing, both readings of `running_vusers`)**
```
python3 -I -c "
import csv,collections
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('vusers.csv'))}
T=('search','add_to_cart','checkout')
tot_to=0; tot_f=0
for m in range(16,23):
  rp=int(vu[(m-1,'LG2')]['running_vusers']); rn=int(vu[(m,'LG2')]['running_vusers'])
  N=int(tx[(m,'LG2')]['checkout']['count'])
  Cn=60*rn/N; Cx=60*max(rp,rn)/N; mx=N*max(0,Cx-20)/10
  f=sum(int(tx[(m,'LG2')][t]['failed']) for t in T); tot_to+=mx; tot_f+=f
  print(m,N,rn,max(rp,rn),'%.1f %.1f'%(Cn,Cx),round(mx),f)
print('16-22 max timeouts %.0f of %d'%(tot_to,tot_f))
"
```

Output (key):
- Cycle using the end-of-minute count: 21.8–22.7 s.
- Cycle using the start-of-minute count: 22.6–29.7 s.
- With the start-of-minute count, at most 1,678 of 2,036 failures (82 %) could have been timeouts. Per minute this ranges from 40 % to over 100 %, so the bound is inconclusive.
- Per-transaction failure share in 16–22: 17.39 / 17.83 / 17.74 %.

**DA2-C2: Bound on 30 s timeouts in 23–39 (constant users, no exits)**
```
python3 -I -c "
import csv,collections
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('vusers.csv'))}
T=('search','add_to_cart','checkout')
for g in ('LG1','LG2'):
  ms=range(23,40)
  U=sum(int(vu[(m,g)]['running_vusers']) for m in ms)*60
  N=sum(int(tx[(m,g)]['checkout']['count']) for m in ms)
  f=sum(int(tx[(m,g)][t]['failed']) for m in ms for t in T)
  C=U/N
  print(g,set(vu[(m,g)]['running_vusers'] for m in ms),sum(int(vu[(m,g)]['exited_with_error']) for m in ms),'%.2f'%C,N,f,'%.0f'%(N*max(0,C-20)/10))
"
```

Output:

| Generator | Users (23–39) | Exits | Window cycle | Iterations | Failed transactions | Max timeout iterations |
| --- | --- | --- | --- | --- | --- | --- |
| LG1 | 250 | 0 | 20.01 s | 12,742 | 102 | 16 |
| LG2 | 80 | 0 | 20.23 s | 4,034 | 638 | 92 (≤ 14 % of failures) |

**DA2-C3: LG2 CPU against scheduled and running vusers, robustness**
```
python3 -I -c "
import csv,statistics as st
vu={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('vusers.csv'))}
lg={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('load_generators.csv'))}
c=lambda m:float(lg[(m,'LG2')]['cpu_pct']); s=lambda m:int(vu[(m,'LG2')]['scheduled_vusers']); r=lambda m:int(vu[(m,'LG2')]['running_vusers'])
for a,b in ((16,44),(16,42),(16,38),(23,44)):
  ms=range(a,b+1)
  # st.correlation raises when one series is constant; reported as nan
  ...
for m in range(16,45): print(m,s(m),r(m),c(m),lg[(m,'LG1')]['cpu_pct'])
"
```

Output: correlation with scheduled / running vusers by window:

| Window | Scheduled | Running |
| --- | --- | --- |
| 16–44 | 0.993 | 0.419 |
| 16–42 | 0.974 | 0.152 |
| 16–38 | undefined (scheduled constant at 250) | 0.103 |
| 23–44 | 0.994 | 0.823 |

LG2 CPU in 16–39 was 92.2–98.5. In 40–44 (scheduled / running users): 86.4 (200/80), 71.0 (150/80), 61.3 (100/80), 49.3 (50/50), 35.2 (0/0).

**DA2-C4: Size of the 30–33 shift per generator and transaction against its own noise**
```
python3 -I -c "
import csv,collections,statistics as st
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
ev=range(30,34); nb=[m for m in range(23,40) if m not in ev]
for g in ('LG1','LG2'):
  for t in ('search','add_to_cart','checkout'):
    a=[float(tx[(m,g)][t]['avg_s']) for m in nb]; b=[float(tx[(m,g)][t]['avg_s']) for m in ev]
    print(g,t,'%.3f sd %.3f | %.3f | shift %.3f = %.1f sd'%(st.mean(a),st.stdev(a),st.mean(b),st.mean(b)-st.mean(a),(st.mean(b)-st.mean(a))/st.stdev(a)))
r=st.mean(float(tx[(m,'LG2')]['checkout']['avg_s'])/float(tx[(m,'LG1')]['checkout']['avg_s']) for m in nb)
print('ratio %.2f, proportional prediction +%.2f s'%(r,r*0.29))
"
```

Output (checkout avg_s, 30–33 against the other minutes of 23–39):

| Generator | Other minutes (mean, sd) | Minutes 30–33 | Shift |
| --- | --- | --- | --- |
| LG1 | 0.851 s, sd 0.029 | 1.145 s | +0.294 s (10.0 sd) |
| LG2 | 2.906 s, sd 0.080 | 2.900 s | −0.006 s (−0.1 sd) |

The LG2 : LG1 ratio outside the event was 3.42, so the proportional model predicts +0.99 s for LG2. LG1 and LG2 search and add_to_cart: |shift| ≤ 0.6 sd.

**DA2-C5: Sample of team figures (failure pools, CPU per user, p95 ranges, minute 43, ratios, LG2 share, pinning)**
```
python3 -I -c "
... loaders for transactions, vusers, load_generators, app_servers ...
pool(g,ms) = failed/count summed over transactions and minutes
cpu/user = mean of cpu_pct/running_vusers per minute
pinning: 7.33+0.481*2*mean generator TPS over 23-39 minutes with app2 present
"
```

Output:
- Failure pools: (2036, 11577, 17.59 %), (638, 16091, 3.96 %), (179, 89816, 0.199 %), (102, 50797, 0.201 %). 10–15 both generators: 74 / 35952 = 0.206 %.
- CPU per user: 0.340 / 1.183 / 0.233.
- Checkout p95, 16–39: LG2 4.40–5.87, LG1 1.27–1.98.
- Minute 43: 50 / 50 users, p95 1.26 / 4.69.
- Ratios: 23–29 [3.33, 3.36, 3.31]; 34–39 [3.39, 3.39, 3.55].
- LG2 share: 0.340 / 0.241.
- Pinning: 49.9 / 15.8 TPS → 55.3 / 22.5 % predicted, 38.7 / 38.6 % observed (n = 14).

**DA2-C6: Thread-occupancy model re-run, adding an "LG2 never reached the app" prediction; DB CPU fit**
```
python3 -I -c "
... loaders ...
LA = sum rate*own avg_s; LB = sum rate*LG1 avg_s; L1 = LG1 terms only
fit threads(app1+app2) on LA over minutes 0-15 with both nodes; print window means obs / A / B / LG1-only
DB: fit cpu_pct on total TPS over 0-43 excluding 30-33; residuals 30-33
"
```

Output: fit 11.14 + 0.622 L, r 0.990, sd 1.75. The maximum |LA − LB| over the calibration minutes is 1.47.

| Window | Observed | A (LG2 times are server time) | B (LG2 served at LG1 speed) | LG1 only |
| --- | --- | --- | --- | --- |
| 16–22 | 38.7 | 73.4 | 40.9 | 30.3 |
| 23–29 | 36.2 | 50.2 | 36.4 | 30.4 |
| 30–33 | 34.8 | 52.7 | 38.9 | 32.2 |
| 34–39 | 36.3 | 50.5 | 35.9 | 30.0 |

DB fit: 5.78 + 0.242 TPS, r 0.990. Residuals in 30–33: 16.9, 16.7, 18.6, 18.1.

**DA2-C7: lb1 bytes per transaction against failure share**
```
python3 -I -c "
... per-minute total count and failed from transactions.csv; network.csv ...
k(m)=throughput_mbps*1000/(count/60); base=mean k over 10-15
for m in 16..23: fail share, observed k, base*(1-fail share); range of k over 23-39
"
```

Output:
- Baseline 419.7 kbit per transaction, sd 3.6.

| Minute | Failure share | Observed kbit | Expected if failures carried no bytes |
| --- | --- | --- | --- |
| 16 | 2.0 % | 417 | 411 |
| 17 | 10.1 % | 431 | 377 |
| 18 | 8.5 % | 424 | 384 |
| 22 | 5.2 % | 414 | 398 |

- Range over 23–39: 407–434.
