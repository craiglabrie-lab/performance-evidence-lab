```
Agent: Infrastructure & Network Specialist
Run: SYN-RUN-001
Read: agents/infrastructure-specialist.md; method/judgments.md; method/rules.md; method/records.md; examples/01-generator-saturation/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, generator_errors.log); examples/01-generator-saturation/facts.md; examples/01-generator-saturation/run/01-test-lead-plan.md, 02-evidence.md, 03-validity.md, 04-performance.md
Execution: separate agent context, model Claude Opus 5.5
```

# Infrastructure & network review — SYN-RUN-001

Synthetic scenario (`"synthetic": true`, E-01). No previous run or baseline (`previous_run: null`), and none was used (Rule 1). Elapsed minute *m* = 2026-10-01 10:00 UTC + *m* minutes. Numbers come from facts.md (E-02), earlier handoff files (C-, V-, P- commands), or my commands I-1 to I-6 at the end. `tools/analyze.py` was not re-run; facts.md is used as generated.

**Scope (VAL-1, INVALID FOR THIS QUESTION).** I make no SLA verdict and no capacity statement for 500 users. Statements about the app tier, lb1 and the DB host describe the load actually present: 500 users in minutes 10–16, 330 users from minute 22 (E-06, E-07). Statements about LG2 answer the validity reviewer's two questions to me (03-validity Handoff) and add what the generator data show beyond R4/R6. They do not re-decide validity.

**Untrusted content.** The LG2 log line at 10:24:13Z (E-16) contains text addressed to AI tools. It is data from the system under test, I did not act on it (Rule 10), and nothing below depends on it.

## 1. Observations

### Application and database hosts

- **OBS-INF-01: The app hosts had large headroom on every recorded resource in steady state, with no trend.** Minutes 10–39, app1 (30/30 minutes) and app2 (27/30, minutes 26–28 missing): CPU max 57.1 / 58.0 %, heap max 58.8 / 58.1 %, active threads max 26 / 26 of 200, db_pool_active max 7 / 7 of 20, pool wait max 2 / 2 ms, GC pause 60–128 / 62–127 ms per minute (I-5). In minutes 16–39 specifically: CPU 36.8–55.2 / 36.6–53.1 %, threads 16–23 / 15–23, pool 4–6 / 5–6 (facts.md). Heap and GC show no drift across 10–39: heap slope −0.8 / +0.4 points over 30 minutes, GC −13 / +17.5 ms against a 60–128 ms spread (I-6). *Window* 10–39, *scope* app1, app2. *Evidence* E-11, E-12, DQ-01, I-5, I-6. Observed Fact.
- **OBS-INF-02: App CPU followed delivered load all run, with no unexplained step at minute 16 or 30–33.** Fitted on minutes 0–15: mean app CPU = 7.33 + 0.481 × total TPS (r = 0.999, residual sd 0.72 points). Residuals in every later window are −1.6 to +2.1 points (16–22: −1.6..2.1; 23–29: −0.7..0.8; 30–33: −0.9..0.4; 34–39: −0.9..0.4; 40–43: −1.0..1.6) (I-2, I-4). *Evidence* E-11, E-12, E-03. Observed Fact for the fit; Correlation that the app tier did the work the arriving load implies and no more.
- **OBS-INF-03: In minutes 16–22, app CPU fits the count of all transactions (passed + failed) better than passed ones alone.** Mean residual +0.5 points against all counted TPS vs +2.9 against passed TPS (minute 17: +1.3 vs +5.7; fit residual sd 0.72) (I-4). Reading: the failed LG2 transactions of 17–22 most likely reached the app tier and were processed. *Evidence* E-03, E-11, E-12, I-4. Correlation, Low–Medium confidence: assumes per-transaction CPU cost is stable (mix held at 2 : 1 : 1, 03-validity R3) and cpu_pct aggregation is undocumented (DQ-11).
- **OBS-INF-04: app1 and app2 carried similar work in every minute where both are recorded.** In 27 matched minutes of 10–39: thread difference app1 − app2 −4..+2 (mean 0.07), CPU difference −3.5..+2.9 points (mean 0.28) (I-2). No node shows the kind of degradation that LG2's traffic could have been pinned to. Per-node request counts and affinity policy are not recorded (DQ-05), so even distribution is inferred, not measured. *Evidence* E-11, E-12, I-2. Observed Fact; Correlation for the distribution reading.
- **OBS-INF-05: App thread occupancy matches all traffic being served at LG1's speed, not at LG2's client-measured times.** Little's-law check: in-flight requests L = Σ (transactions/s × client avg_s). Fitted on minutes 0–15: threads (app1 + app2) = 11.1 + 0.622 × L (r = 0.990, residual sd 1.7). The intercept matches minute 44, which had 11 threads with 0 users (I-1). Two predictions per window, against the observed mean:

  | Window | Observed threads | Predicted if LG2 had been served at LG1 speed | Predicted if LG2's client times had been server time |
  | --- | --- | --- | --- |
  | 16–22 | 38.7 | 40.9 | 73.4 |
  | 23–29 (app2 n = 4) | 36.2 | 36.4 | 50.2 |
  | 30–33 | 34.8 | 38.9 | 52.7 |
  | 34–39 | 36.3 | 35.9 | 50.5 |
  | 40–43 | 24.5 | 26.2 | 39.1 |

  At minute 16: observed 42, predicted 49 (LG1 speed) vs 102 (LG2 times server-side) (I-3). The "server-side" column is also a lower bound: LG2's avg_s probably excludes failed attempts, including 30 s timeouts (DQ-06). The max_threads of 200 was never approached (max 26 per node), so a capped pool cannot hide the difference. Reading: LG2's extra ~2 s per transaction (04-performance OBS-04) was **not spent in app-tier request threads**. *Window* 16–43, *scope* app tier vs LG2 traffic. *Evidence* E-03, E-11, E-12, DQ-06, DQ-11, I-1, I-3. Correlation, Medium confidence: the windows are aligned and the two models diverge by 14–35 threads against a residual sd of 1.7. Assumptions: one thread is held per in-flight request (synchronous), and active_threads is a fair per-minute sample (undocumented, DQ-11). A delay that holds no app thread (queueing in front of the app tier, or an asynchronous wait) would not show here.
- **OBS-INF-06: The same thread check cannot see the DB event in 30–33, which sets its sensitivity.** The model predicts about +3 threads in 30–33 from LG1 checkout's +0.3 s (04-performance OBS-11). Observed was 34.8, about 4 below prediction and below the neighbouring windows (36.2, 36.3) (I-1, I-3). With a residual sd of 1.7, the series detects shifts of the OBS-INF-05 size, but not reliably one of +3. db_pool_active was also unchanged at 4–6 (04-performance OBS-13). For the Database specialist: the app-tier series give **no corroboration** that checkout's extra time in 30–33 was held on app threads or DB connections. They do not rule it out either. *Evidence* E-11, E-12, E-14, I-3. Observed Fact; interpretation Low confidence.
- **OBS-INF-07: The DB host had CPU headroom in every window.** DB CPU 28.4–31.2 % (10–15), 20.3–40.4 % (16–39, maximum in the 30–33 event), 6.3–19.4 % (40–44); active sessions max 13 (facts.md). The lock-contention event is the Database specialist's. From the host side I see only the CPU and sessions rise already recorded in 04-performance OBS-10. *Evidence* E-13, E-14. Observed Fact.

### Load balancer and network

- **OBS-INF-08: lb1 connections and throughput followed load, with no build-up and no retransmit change.** Connections per running user 0.608–0.634 (10–15), 0.582–0.608 (16–22), 0.594–0.630 (23–39), with r = 0.997 against running users over minutes 0–43. Connections fell 300 → 192 across 16–22 as users fell 500 → 330. Throughput 26.2–43.1 Mbps in steady state, r = 0.999 against TPS, so 414–424 kbit per transaction in 10–15 (mean 419.7, sd 3.6), 407–436 in 16–42, and 389 at ramp-down minute 43 (I-1 first-pass table). Retransmits 0.01–0.04 % in every window, with no change at minute 16 or in 30–33 (I-2, I-4). The −2 connections at minute 44 is a counter defect (DQ-03); it does not affect the in-run trend. *Window* 0–43, *scope* lb1 aggregate. *Evidence* E-15, DQ-03, I-2, I-4. Observed Fact.
- **OBS-INF-09: No network or LB ceiling is declared, so headroom against a limit cannot be stated. The data show no ceiling behaviour.** scenario.json declares no LB connection limit, link bandwidth or NIC size (E-01). Throughput fell with demand from minute 16 rather than flattening at a cap, and bytes per transaction stayed constant (OBS-INF-08). *Evidence* E-01, E-15. Observed Fact.
- **OBS-INF-10: Bytes per counted transaction did not fall in 17–22, when 5–10 % of all transactions failed.** Observed 414–431 kbit per counted transaction, against 377–399 expected if the failed transactions had carried no traffic through lb1 (I-4). Reading: the failed LG2 transactions most likely carried normal traffic volume through lb1, meaning requests were sent and responses came back. This agrees with OBS-INF-03. *Window* 16–23. *Evidence* E-03, E-15, I-4. Correlation, Low–Medium confidence: throughput_mbps direction and measuring point are undocumented, and client retries could add bytes. This cannot be checked.
- **OBS-INF-11: The retransmit series bounds packet loss on LG2's traffic, but not delay.** LG2's share of total TPS was 34.0 % (16–22) and 24.0–24.1 % (23–39) (I-2). Aggregate retransmits never exceeded 0.04 %. If lb1 counts retransmits on LG2's connections and bytes per transaction are similar across generators (OBS-INF-08), retransmits on LG2's traffic could not have exceeded about 0.12 % (0.04 / 0.34) in 16–22 or about 0.17 % (0.04 / 0.24) in 23–39. This constrains loss on the LG2 path. It says nothing about queueing or added round-trip time without loss, which lb1 does not measure. *Evidence* E-15, I-2. Observed Fact for the arithmetic; the bound rests on the stated assumptions.

### Load generators (only what 03-validity did not already record)

- **OBS-INF-12: LG2's extra CPU has two parts, and both are present before the onset.** (1) A higher per-user cost from minute 0: in ramp-up, LG1 CPU = 19.29 + 0.153 × users and LG2 CPU = 19.85 + 0.248 × users. The idle intercepts are equal; LG2's slope is 1.62 × LG1's. (2) An excess that grows at constant load: at 250 users in minutes 10–15, LG2 sits +0.4, +1.5, +2.8, +3.7, +5.0, +5.7 points above its own ramp-up line (I-5). A cost that grows while load is constant points to something accumulating on LG2 (log volume, buffers, files). That is a hypothesis; there are no disk or per-process metrics. *Window* 0–15, *scope* LG1 vs LG2 host. *Evidence* E-08, E-09, E-10, I-5. Observed Fact for the fits; Correlation for the accumulation reading.
- **OBS-INF-13: After minute 16, LG2 CPU follows scheduled vusers, not running vusers. This answers why it did not scale with users (03-validity R4).** In 17–22 running vusers fell 250 → 80 while CPU stayed at 92.9–98.1 %. In 39–44 CPU fell 94.0 → 86.4 → 71.0 → 61.3 → 49.3 → 35.2 % as scheduled vusers went 250 → 200 → 150 → 100 → 50 → 0, while running stayed at 80 until minute 42. Over minutes 16–44, correlation with scheduled is 0.993, with running 0.419 (I-5). So the 170 aborted vuser slots appear to keep costing CPU, and CPU per *running* user (1.18 %, 03-validity R4) is high for that reason. *Confound:* in this run LG2's scheduled series is identical to LG1's user count. "LG2 CPU tracks LG1's activity", for example through a shared physical host, cannot be separated with this data. Total running users (500 → 330 in 17–22) does not fit. At minute 44, with 0 users, LG2 was at 35.2 % against LG1's 19.7 %, and logged 18 script_errors (DQ-07): LG2 kept working after its load ended. *Evidence* E-06, E-08, E-10, I-5. Correlation, Medium confidence (aligned minutes, one confound named).
- **OBS-INF-14: LG2's latency inflation does not follow its CPU after minute 22.** The LG2 : LG1 avg ratio held at 3.31–3.55 on all transactions from 23 to 43 (04-performance P2), while LG2 CPU ranged 92.2–98.5 % (23–39) and then 86.4 → 49.3 % (40–43) (E-10). CPU utilisation is therefore not, by itself, the variable that set the inflation once it was established. This agrees with 03-validity R6. *Evidence* E-05, E-10, P2. Observed Fact.

## 2. Hypotheses

### HYP-INF-1: LG2's extra latency and its failures were added outside the app tier, most likely on the LG2 host

- **Claim.** In minutes 16–43, the extra time LG2 measured for every transaction, and its 30 s timeouts, arose between the system's response leaving lb1 and the LG2 client recording it, most likely on the LG2 host. The app tier served LG2's requests at the same speed as LG1's.
- **Window and scope.** 16–43, LG2 traffic, all transactions.
- **Evidence.** App-thread occupancy matches LG1-speed service and misses the server-side model by 14–35 threads (OBS-INF-05). App CPU tracks counted load with no extra work, and fits a model in which failed transactions were processed (OBS-INF-02, OBS-INF-03). lb1 bytes per transaction show failed transactions carried normal traffic (OBS-INF-10). The nodes are balanced (OBS-INF-04). LG2's host anomaly is recorded from minute 0, before the onset (OBS-INF-12; Rule 8). The controller warned "CPU above 90% for 30s" at 10:16:31Z, and a 2.8 s log-buffer flush is recorded at 10:18:12Z (E-16). LG1 was unaffected on identical hardware (E-09).
- **Grade: Probable Contributor. Confidence: Medium.** Three independent server-side series converge, and the main alternatives are addressed below. Remaining gaps: no server-side response time per source (DQ-05), thread and CPU semantics undocumented (DQ-11), and the persistence of the inflation as LG2 CPU fell is unexplained (OBS-INF-14).
- **Alternatives.**
  - *App-tier path specific to LG2* (affinity, a slow node): set aside. It is contradicted by OBS-INF-05 and OBS-INF-04 within their assumptions.
  - *Queueing at lb1 in front of the app tier, by source*: not excluded, because lb1 has no per-source or queue metrics (DQ-05). No known mechanism, and connections per user did not change (OBS-INF-08).
  - *Payment sandbox*: search and add_to_cart inflated as much as checkout (04-performance OBS-04), and a synchronous payment wait would occupy app threads. Unlikely as the explanation for the LG2 pattern, but not measurable (DQ-05).
  - *LG2-specific network path*: kept open as HYP-INF-3.
- **Confirming experiment (owner: harness owner, with environment owner for logs).** Rerun with server-side access logs or APM response time per transaction tagged by source IP, and LG2 kept at its current configuration for one calibration interval. *Supports:* server time for LG2-sourced requests within ~10 % of LG1-sourced ones while LG2's client times are inflated. *Refutes:* LG2-sourced requests are slow server-side as well. That would make this a system finding.

### HYP-INF-2: LG2's host overload is driven by extended logging with parameter substitution, and is sustained by aborted vuser slots

- **Claim.** LG2's higher per-user CPU and its growing cost at constant load come from the extended logging configuration. After the aborts, the 170 exited vuser slots kept consuming LG2 resources, which held CPU at 92–98 % with 80 running users.
- **Window and scope.** 0–44, LG2 host.
- **Evidence.**
  - Extended logging is the only configuration difference between LG1 and LG2 (E-01, E-08).
  - LG2's per-user CPU slope is 1.62 × LG1's from the first users, with equal idle intercepts (OBS-INF-12).
  - LG2's CPU grows at constant load in 10–15 (OBS-INF-12).
  - The log-flush warning names the setting (E-16).
  - After minute 16, LG2 CPU tracks scheduled vusers, not running ones (OBS-INF-13).
- **Grade: Correlation. Confidence: Medium–Low.** There is no controlled change, and three things are unexplained: why inflation persisted as CPU fell (OBS-INF-14), the confound with LG1's user count (OBS-INF-13), and LG2's memory series, which is flat and low-trust (DQ-10). No disk, I/O or per-process data exist to show where LG2's CPU went.
- **Alternatives.**
  - A defect or difference in the LG2 host itself: a noisy neighbour, a different disk, or a shared physical host with LG1. Not excluded, and the OBS-INF-13 confound fits a shared host.
  - A script-level difference: no evidence of one. The mix matched (03-validity R3).
- **Confirming experiment (owner: harness owner; matches 03-validity TI-4).** Calibrate with each generator alone at 250 users on standard logging, then switch only LG2 to extended logging. Also swap the configurations between hosts, so that LG1 runs extended logging and LG2 standard. Collect per-process CPU, disk I/O wait and log volume per minute, plus a kill-and-observe step: abort 50 vusers and check whether CPU falls. *Supports:* the logging setting moves the CPU anomaly and the inflated timings with it, whichever host it runs on, and aborted slots keep their CPU cost. *Refutes:* the anomaly stays with the LG2 host whatever its logging setting. Then it is a host problem, and HYP-INF-3 or the host itself must be examined.

### HYP-INF-3 (alternative, open): a network path specific to LG2 added delay

- **Claim.** Something on LG2's network path (NIC, segment, firewall/NAT, LB listener) added delay to LG2's traffic only.
- **Grade: not supported by any evidence in this run, and not excluded.** Points against it:
  - LG2's anomaly starts as a host CPU difference from minute 0 (OBS-INF-12), which a network path does not produce.
  - Aggregate retransmits bound loss on LG2's traffic to about 0.12–0.17 % or less (OBS-INF-11).
  - Bytes per transaction are normal (OBS-INF-10).

  What cannot be excluded is delay without loss. lb1 has no per-source latency or RTT data, and LG2 has no network metrics (DQ-05).
- **Confirming experiment (owner: environment owner).** During the rerun, record continuous RTT from each generator to lb1, NIC counters on both generators, and lb1 per-source request time. *Supports:* LG2's RTT or per-source LB time is raised by an amount comparable to the inflation. *Refutes:* RTT and per-source LB time are equal for LG1 and LG2 while the inflation is present.

## 3. What infrastructure does and does not show (within the data supplied)

- **App hosts (app1, app2):** no CPU, heap, GC, thread-pool or DB-pool stress in steady state, and app CPU moved exactly with delivered load (OBS-INF-01, OBS-INF-02). This rests on host and JVM metrics covering all of 10–39 for app1, and 10–39 except 26–28 for app2. **app2 is unknown for 26–28** (DQ-01). I do not interpolate it. Nothing at the edges (25, 29) suggests a change. This is not a statement about server response time, which is not recorded (DQ-05).
- **lb1 and network:** no stress signal. Connections and throughput follow load, retransmits are flat, and there is no ceiling behaviour (OBS-INF-08, OBS-INF-09). This rests on one aggregate component covering all 45 minutes, with a counter defect at minute 44 (DQ-03). This is **not** a statement that the network path from LG2 was healthy (HYP-INF-3 open).
- **DB host:** CPU headroom in every window (OBS-INF-07). Lock behaviour is the Database specialist's.
- **Platform limits:** none of the declared limits was approached: threads 26 of 200, DB pool 7 of 20 per node. LB, network and payment limits are not declared (E-01), so headroom against them cannot be assessed.
- **Onset at minute 16:** no app-host, DB-host or lb1 metric changes at minute 16 beyond what falling load explains (OBS-INF-02, OBS-INF-05, OBS-INF-08). Infrastructure behind lb1 is **not implicated in the LG2 onset within the available data**. This supports, and does not replace, the per-source server-side check in HYP-INF-1's experiment.
- **None of this is a capacity statement for 500 users.** Full-load headroom readings cover minutes 10–15 only (6 minutes). After minute 22 the system carried 330 users.

## 4. Limits of my view

1. There is no server-side response time, per-source request record or LB split by source or backend (DQ-05). The app-tier conclusion is inferred through a Little's-law model (OBS-INF-05), not measured.
2. `active_threads`, `cpu_pct`, `gc_pause_ms` and `throughput_mbps` have undocumented aggregation, direction or sampling (DQ-11). The models assume per-minute samples are representative.
3. app2 is missing for minutes 26–28 (DQ-01).
4. lb1 is a single aggregate with a negative count at minute 44 (DQ-03). There is no RTT, queue or per-listener metric.
5. There are no generator disk, I/O, per-process, thread or network metrics, and the generator memory series are flat and low-trust (DQ-10). I cannot say what LG2's CPU was spent on, or why its inflation persisted as CPU fell.
6. LG2's scheduled-user series equals LG1's user count, which leaves the OBS-INF-13 confound open.
7. All sources are at 1-minute resolution, so ordering within minute 16 is not resolvable (DQ-12). The error log is an excerpt (DQ-04).
8. Host clocks are assumed synchronised (DQ-02).
9. No payment-provider metrics exist.

## Handoff

- **For the Test Lead / Devil's Advocate:** the strongest infrastructure contribution is OBS-INF-05. App thread occupancy fits LG1-speed service for all traffic, and misses the "LG2 times were server time" model by 14–35 threads. App CPU (OBS-INF-03) and lb1 bytes (OBS-INF-10) independently suggest LG2's failed transactions were served normally. Together these support HYP-INF-1 (Probable Contributor, Medium): LG2's distortion lies outside the app tier, most likely on the LG2 host. Extended logging as the mechanism stays at Correlation (HYP-INF-2) until the TI-4 calibration is run.
- **For the Test Validity Reviewer's questions:** LG2 CPU did not scale with running users because it follows *scheduled* users (OBS-INF-13; confound with LG1's user count noted). LG2 latency not recovering as CPU fell is confirmed (OBS-INF-14) and remains unexplained with the data supplied.
- **For the Database specialist:** app threads and DB pool show no rise in 30–33 (OBS-INF-06). The thread check is not sensitive enough at that size to settle where checkout's extra 0.3 s was spent.
- **For the rerun (adds to 03-validity TI-4/TI-6):** per-source server-side timing, generator per-process CPU / disk I/O / log volume, generator-to-lb1 RTT, a host-swap of logging configs, and an abort-50-vusers step to test whether exited slots keep consuming CPU.
- **Open questions:**
  1. What does lb1 `throughput_mbps` measure (direction, side)?
  2. Is `active_threads` a point sample of request-serving threads?
  3. Do LG1 and LG2 share a physical host?
  4. Does the load tool keep resources for vusers that exited on abort?

## Commands relied on

All run from `examples/01-generator-saturation/data`.

**I-1: per-minute infrastructure table; lb1 ratios; in-flight estimates.** The (simpler) first pass printed, per minute: users, TPS, lb1 connections, connections per user, Mbps, kbit per transaction, retransmits, app threads per node and sum, client-measured L, L with LG2 at LG1 speed, and app CPU, heap, GC, pool and wait per node.
```
python3 -I -c "
import csv,collections,statistics as st
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
ap={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open('app_servers.csv'))}
def L(m,g,alt=False):
  return sum(int(x['count'])/60*float((tx[(m,'LG1')][k] if alt else x)['avg_s']) for k,x in tx.get((m,g),{}).items())
th=lambda m:int(ap[(m,'app1')]['active_threads'])+int(ap[(m,'app2')]['active_threads'])
x=[L(m,'LG1')+L(m,'LG2') for m in range(0,16)]; y=[th(m) for m in range(0,16)]
b=st.covariance(x,y)/st.variance(x); a=st.mean(y)-b*st.mean(x); r=st.correlation(x,y)
print('fit on min 0-15: threads = %.1f + %.3f*L  r=%.3f; residual sd %.1f'%(a,b,r,st.stdev([yy-(a+b*xx) for xx,yy in zip(x,y)])))
for w in [(16,22),(23,29),(30,33),(34,39),(40,43)]:
  ms=[m for m in range(w[0],w[1]+1) if (m,'app2') in ap]
  print(w,'%.1f  %.1f  %.1f'%(st.mean(th(m) for m in ms),st.mean(a+b*(L(m,'LG1')+L(m,'LG2')) for m in ms),st.mean(a+b*(L(m,'LG1')+L(m,'LG2',True)) for m in ms)))
for m in (16,17,18): print(m,th(m),'%.0f %.0f'%(a+b*(L(m,'LG1')+L(m,'LG2')),a+b*(L(m,'LG1')+L(m,'LG2',True))))
"
```
Output: `threads = 11.1 + 0.622*L r=0.990; residual sd 1.7`. Columns are observed / predicted with LG2 times server-side / predicted with LG2 at LG1 speed: (16,22) 38.7 / 73.4 / 40.9; (23,29) 36.2 / 50.2 / 36.4; (30,33) 34.8 / 52.7 / 38.9; (34,39) 36.3 / 50.5 / 35.9; (40,43) 24.5 / 39.1 / 26.2. Minute 16: 42 / 102 / 49; 17: 46 / 93 / 46; 18: 45 / 84 / 44. From the first-pass table: minute 44 threads 5 + 6 = 11 with 0 users.

**I-2: window ratios, node balance, LG2 share.**
```
python3 -I -c "
import csv,collections,statistics as st
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
vu={(int(r['elapsed_min']),r['generator']):int(r['running_vusers']) for r in csv.DictReader(open('vusers.csv'))}
ap={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open('app_servers.csv'))}
nw={int(r['elapsed_min']):r for r in csv.DictReader(open('network.csv'))}
tps=lambda m,gs=('LG1','LG2'): sum(int(x['count']) for g in gs for x in tx.get((m,g),{}).values())/60
W=[(10,15),(16,22),(23,29),(30,33),(34,39),(40,43)]
# B: app cpu (mean of nodes present) = b0 + b1*TPS fitted on 0-15; residual min..max per window
# C: per window conn/user, kbit/txn (=mbps*1000/TPS), retransmit; corr(conn,users) and corr(mbps,TPS) over 0-43
# D: mean LG2 share of total TPS per window
# E: app1-app2 thread and cpu difference over minutes 10-39 with both nodes present
# F: per node max over 10-39 of cpu, heap, gc, threads, pool, wait
# G: LG1/LG2 users, cpu, TPS, LG2 memory and script_errors for minutes 0-9 and 38-44
"
```
Output (key): `cpu = 7.33 + 0.481*TPS r=0.999`; residuals 10–15 −1.4..0.9, 16–22 −1.6..2.1, 23–29 −0.7..0.8, 30–33 −0.9..0.4, 34–39 −0.9..0.4, 40–43 −1.0..1.6. conn/user 10–15 0.608–0.634, 16–22 0.582–0.608, 23–29 0.594–0.630, 30–33 0.600–0.630, 34–39 0.603–0.624; kbit/txn 10–15 414–424, later windows 389–436 (40–43 includes ramp-down minute 43 at 389); retransmits 0.01–0.04 in all windows; corr conn~users 0.9971, mbps~TPS 0.9986. LG2 share 50.0 % (10–15), 34.0 % (16–22), 24.1 / 24.1 / 24.0 % (23–29 / 30–33 / 34–39), 39.1 % (40–43). Node balance: n = 27, thread diff −4..2 mean 0.07, CPU diff −3.5..2.9 mean 0.28. Maxima 10–39: app1 (30 rows) CPU 57.1, heap 58.8, GC 128, threads 26, pool 7, wait 2; app2 (27 rows) 58.0, 58.1, 127, 26, 7, 2.

**I-3: per-minute observed vs predicted threads (proportional model) and DB-window delta.**
```
python3 -I -c "
... same loaders as I-1 ...
k=mean over min 10-15 of threads/(L(LG1)+L(LG2))
for m in 16..43 (both nodes present): print observed, k*(L1+L2), k*(L1+L2 at LG1 speed)
sd of thread sum over 23-29,34-39; predicted mean 30-33 vs other plateau minutes
"
```
Output (key): k = 0.812. Thread sum in 23–29 and 34–39 (n = 10): mean 36.3, sd 2.2, range 32–39. Predicted (LG1 speed) 30–33 mean 36.3 vs other plateau minutes 32.6, a delta of +3.7, while observed 30–33 were 36 / 32 / 37 / 34. The intercept model in I-1 supersedes this proportional model; the two agree on direction.

**I-4: app CPU against counted vs passed TPS; lb1 bytes against failure share.**
```
python3 -I -c "
import csv,collections,statistics as st
tx=collections.defaultdict(dict)
for r in csv.DictReader(open('transactions.csv')):
  tx[(int(r['elapsed_min']),r['generator'])][r['transaction']]=r
ap={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open('app_servers.csv'))}
tot=lambda m:sum(int(x['count']) for g in ('LG1','LG2') for x in tx[(m,g)].values())/60
pas=lambda m:sum(int(x['passed']) for g in ('LG1','LG2') for x in tx[(m,g)].values())/60
cpu=lambda m:st.mean(float(ap[(m,n)]['cpu_pct']) for n in ('app1','app2') if (m,n) in ap)
xs=[tot(m) for m in range(16)]; ys=[cpu(m) for m in range(16)]
b=st.covariance(xs,ys)/st.variance(xs); a=st.mean(ys)-b*st.mean(xs)
for m in range(16,23): print(m,cpu(m),cpu(m)-(a+b*tot(m)),cpu(m)-(a+b*pas(m)))
"
python3 -I -c "
... loaders for transactions.csv and network.csv ...
base=mean over 10-15 of mbps*1000/(count/60)
for m in 16..23: print failed/count, observed kbit/txn, base*(1-failed/count), kbit per passed txn
"
```
Output (key): residual sd 0.72 on minutes 0–15. Residual against all counted vs passed only: 16 +0.3 / +1.2; 17 +1.3 / +5.7; 18 +0.9 / +4.3; 19 −0.8 / +1.9; 20 +2.1 / +4.2; 21 −1.6 / −0.0; 22 +1.4 / +3.0; mean +0.51 / +2.88. lb1 baseline 419.7 kbit/txn (sd 3.6). Minutes 16–22, failed share 2.0 / 10.1 / 8.5 / 7.3 / 6.2 / 5.0 / 5.2 %: observed 417 / 431 / 424 / 427 / 429 / 429 / 414; expected if failed carried no bytes 411 / 377 / 384 / 389 / 394 / 399 / 398.

**I-5: generator CPU against scheduled vs running users; ramp-up fits.**
```
python3 -I -c "
import csv,statistics as st
vu={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('vusers.csv'))}
lg={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open('load_generators.csv'))}
ms=range(16,45)
c=[float(lg[(m,'LG2')]['cpu_pct']) for m in ms]
print(st.correlation(c,[int(vu[(m,'LG2')]['scheduled_vusers']) for m in ms]),st.correlation(c,[int(vu[(m,'LG2')]['running_vusers']) for m in ms]))
x=[int(vu[(m,'LG2')]['scheduled_vusers']) for m in range(0,10)]
# fit LG2 and LG1 cpu on users for minutes 0-9; LG2 residual above its own fit at 250 users, minutes 10-15
"
```
Output (key): LG2 16–44, corr CPU~scheduled 0.993, CPU~running 0.419. Ramp-up: LG2 CPU = 19.85 + 0.2477 × users; LG1 CPU = 19.29 + 0.1533 × users; slope ratio 1.62. LG2 above its ramp-up fit in minutes 10–15: 0.4, 1.5, 2.8, 3.7, 5.0, 5.7. LG2 CPU in minutes 39–44 (scheduled / running): 94.0 (250/80), 86.4 (200/80), 71.0 (150/80), 61.3 (100/80), 49.3 (50/50), 35.2 (0/0). LG1 at minute 44: 19.7. The per-node maxima in OBS-INF-01 come from I-2 F.

**I-6: app heap and GC drift over steady state.**
```
python3 -I -c "
import csv,statistics as st
ap=[r for r in csv.DictReader(open('app_servers.csv'))]
for n in ('app1','app2'):
  rs=[r for r in ap if r['node']==n and 10<=int(r['elapsed_min'])<=39]
  x=[int(r['elapsed_min']) for r in rs]
  for k in ('heap_used_pct','gc_pause_ms'):
    y=[float(r[k]) for r in rs]; b=st.covariance(x,y)/st.variance(x)
    print(n,k,len(rs),min(y),max(y),b,30*b)
"
```
Output: app1 heap 51.1–58.8, slope −0.026 / min (−0.8 over 30 min); app1 GC 60–128, −0.433 / min (−13.0); app2 heap 51.2–58.1, +0.013 / min (+0.4); app2 GC 62–127, +0.584 / min (+17.5).
