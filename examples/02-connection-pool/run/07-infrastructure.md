```
Agent: Infrastructure & Network Specialist
Run: SYN-RUN-002
Read: agents/infrastructure-specialist.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, external_calls.csv, checkout_traces.csv); examples/02-connection-pool/facts.md; examples/02-connection-pool/run/01-test-lead-plan.md; examples/02-connection-pool/run/02-evidence.md; examples/02-connection-pool/run/03-validity.md; examples/02-connection-pool/run/04-performance.md
Execution: separate agent context, model Claude Opus 5.5
```

Data note: `scenario.json` marks this dataset as synthetic. It is reviewed here as though it were a real run.

**Scope.** VAL-1 is VALID WITH LIMITATIONS (`03-validity.md`). I work inside it: minutes 19–39 are system behaviour under a caller-side payment-latency excursion at 500 users (AC-5, AC-6). I make no capacity claim (RC-1, RC-2), do not say the sandbox throttled or caused anything (RC-3, RC-4), and do not order DB against app-tier signals at one-minute resolution (RC-9, DQ-06). Evidence IDs (E-, DQ-, OBS-, SW-) are from `02-evidence.md` and `04-performance.md`. Every number comes from `facts.md` (E-13), an earlier run file, or commands I1–I4 in the appendix (rule 3).

## Summary

- **Hosts, load balancer and inbound network show no stress and no change at onset, in any minute of the symptom window.** App CPU stays at or below 54.8%, DB CPU at or below 44.5%, LB connections track user count, LB throughput tracks TPS, retransmits stay at 0.01–0.04%. Coverage is 45/45 minutes for every one of these sources (E-13). Within these metrics, infrastructure does not explain the onset at minute 19 or the degradation in 19–39 (HYP-INF-1).
- **That rule-out does not reach the outbound path to the payment sandbox.** No metric covers egress from the app nodes (NAT, proxy, DNS, TLS, internet link). The ~1.8 s rise in caller-side payment latency could include time on that path, and nothing here can exclude it (HYP-INF-2, open).
- **app1 burns extra CPU from minute 27,** in step with its heap/GC divergence (HYP-INF-3, Correlation). It starts 8 minutes after onset and is not a host-capacity problem.
- **Two cross-source consistency findings for the application specialist:** server active threads rise above the client-side in-flight request count from minute 29 and keep climbing while client concurrency is flat (OBS-INF-09); and the implied number of concurrent payment calls in minutes 19–24 (46–52) exceeds the 40 DB connections they are supposed to be made under (OBS-INF-10).
- **One item the Validity Reviewer did not flag:** LG memory_pct is an exact function of user count and identical on both generators in all 45 minutes, so it carries no independent health information (OBS-INF-11).

## 1. Sources and coverage for this view

| Layer | Source | Coverage | What it can show | What it cannot |
| --- | --- | --- | --- | --- |
| App hosts | E-06, E-07 (`app_servers.csv`) | 45/45 per node | CPU %, JVM heap, GC pause, threads, pool | Host memory, disk, NIC, per-core or throttled CPU, instance size. Sampling semantics undocumented (DQ-07) |
| DB host | E-08 (`database.csv`) | 45/45 after UTC conversion | CPU %, sessions, query time, lock wait, top event | Memory, disk I/O, NIC, max_connections. Minute-level ordering vs APM unreliable (DQ-06) |
| LB / inbound network | E-09 (`network.csv`) | lb1 45/45; minute 44 connections = −1 (DQ-01) | Active connections, Mb/s, retransmit % at lb1 | Per-node distribution, LB queueing, LB limits, errors/resets |
| Outbound to sandbox | E-10 (`external_calls.csv`) | 45/45 | Caller-side calls, avg/p95 latency, errors | Where the latency is spent (client pool, connect, TLS, network, provider). No network metrics on this path |
| Generators | E-05 (`load_generators.csv`) | 45/45 per generator | CPU %, memory %, script_errors, log level | NIC, sockets, client timeouts |

No source covers: app↔DB network, app→sandbox network, DNS, firewall/NAT/proxy, host memory outside the JVM, storage I/O. Steady-state coverage of every source above is 30/30 minutes (`02-evidence.md` §3).

## 2. Observations

**OBS-INF-01 — App host CPU has headroom in every window and does not move at onset.** (I2)

| Window | app1 CPU min / median / max | app2 CPU min / median / max |
| --- | --- | --- |
| 10–18 | 51.4 / 52.7 / 54.8% | 50.7 / 52.6 / 54.2% |
| 19–26 | 47.5 / 52.45 / 53.3% | 49.4 / 52.9 / 54.6% |
| 27–39 | 50.5 / 52.1 / 54.7% | 44.6 / 47.1 / 49.1% |

Minute 18 → 19: app1 54.7 → 52.6%, app2 53.4 → 54.3% (E-06, E-07). The highest value in the run is 54.8% (app1, minute 10). App CPU rises in proportion to load during ramp-up (12.8/12.2% at 50 users to 53.4/52.1% at 500 users, minutes 0–9) and falls with it during ramp-down (43.7/44.5% at minute 40 to 18.4/16.3% at minute 43), so the metric is live and load-responsive. *Window:* 0–44, both nodes. *Evidence:* E-06, E-07, E-13; I2. Observed Fact. *Caveat:* instance size, core count and any container CPU quota are not declared, so "headroom" means headroom against 100% of the reported metric, not against a known platform quota (DQ-07, §4).

**OBS-INF-02 — App CPU per transaction is flat until minute 26, then rises, and the rise is on app1 only.** (I2)
- Sum of node CPU % divided by TPS: 1.036–1.089 in 10–18; 1.042–1.091 in 19–26; 1.122–1.197 in 27–39.
- app1 − app2 CPU: −2.6 to +2.2 points in 10–18; −2.1 to +1.8 in 19–26; **+2.6 to +8.3 in 27–39**.
- In 27–39 app2 CPU (44.6–49.1%) has fallen with throughput (TPS 84.2–87.2), while app1 stays at 50.5–54.7%, its reference level.
- The same minutes are when app1 heap is 82.3–86.3% and GC pause 643–863 ms (OBS-11, SW-5); app1 GC in 19–26 is 71–111 ms.
- Threads and pool are matched across nodes in these minutes (threads within 5 of each other per minute; pool 20/20 on both) (I2; OBS-11).

*Window:* 10–39, app1 vs app2. *Evidence:* E-06, E-07, E-13; I2. Observed Fact.

**OBS-INF-03 — DB host CPU has headroom and does not move at onset.** (I2)
- 10–18: 26.8–29.3%. 19–39 excluding 30–33: 23.5–28.7%. 30–33: 42.2–44.5% (with "row lock contention", lock_wait 683–800 ms, sessions 46; OBS-10, SW-4).
- Minute 18 → 19: 29.3 → 27.0%. Under DQ-06 I use only the multi-minute statement: DB CPU in 19–29 (24.5–28.7%) is no higher than in 10–18.
- DB sessions in 30–33 are 46 against an app pool sum of 40, so 6 sessions came from a client other than the two app pools in those minutes (`02-evidence.md` §6). Who that client was is unknown (DQ-10b).

*Window:* 10–39, DB host. *Evidence:* E-08, E-17; I2. Observed Fact (host-level only; no memory or I/O metrics).

**OBS-INF-04 — LB active connections track user count, not request concurrency, and do not move at onset.** (I1, I4)
- Active connections / running users = 0.61–0.63 in every minute 2–43, through ramp-up, steady state, degradation and ramp-down (e.g. 309 at 500 users in minute 9, 249 at 400 in minute 40, 61 at 100 in minute 43).
- Steady state: 307–312 in 10–18 and 305–314 in 19–39. Minute 18 → 19: 312 → 308.
- Over the same period the client-side in-flight request count (Little's Law from the load tool: Σ count × avg_s / 60) rises from 59.9–62.8 (10–18) to 141.1 at minute 19 and 240.7–248.7 in 27–39 (I1). The LB connection count does not follow it.
- So this metric reflects persistent client connections per user. It shows no connection build-up at the LB, but it also cannot show request queueing at or behind the LB.
- No per-node split exists, so LB distribution across app1/app2 cannot be checked directly. Indirectly, the nodes were evenly loaded in 10–26: CPU within ±2.6 points, threads within 7, pool active within 1 (I2).
- Minute 44 value −1 is invalid and treated as unknown (DQ-01).

*Window:* 0–43, lb1. *Evidence:* E-09, E-04, E-02, E-03, E-06, E-07, DQ-01; I1, I4. Observed Fact. The in-flight figure is a model and depends on whether avg_s includes failed requests (DQ-10d) and on bucketing (DQ-07).

**OBS-INF-05 — LB throughput moves with transactions; nothing unexplained on the wire.** (I1)
- Mb/s per TPS: 0.413–0.428 in 10–18; 0.408–0.431 in 19–39; 0.389–0.452 in ramp-up and ramp-down minutes 1–9 and 40–43, where low counts make the ratio noisier.
- LB throughput falls from 41.2–42.7 Mb/s (19–24) to 35.2–36.9 Mb/s (26–39) exactly as TPS falls (OBS-07). Bytes per transaction did not change at onset or in 30–33 (0.408–0.431).
- Highest value in the run: 43.0 Mb/s (minute 15). No bandwidth limit for lb1 or the network is declared in `scenario.json`, so a comparison against a known limit is not possible.

*Window:* 0–43, lb1. *Evidence:* E-09, E-13; I1. Observed Fact.

**OBS-INF-06 — Retransmits are low and flat in every window.** Retransmit 0.02–0.04% in 10–18 and 0.01–0.04% in 19–39; 0.02 → 0.03% at minute 18 → 19; 0.01–0.04% over the whole run (E-13; I1). No error or reset counters exist. *Window:* 0–44, lb1. *Evidence:* E-09. Observed Fact.

**OBS-INF-07 — The app→DB path shows no slowdown in the sampled requests.** Trace SQL time is 25–59 ms in every window, including 19–39 and 30–33 (`facts.md` trace summaries; OBS-06, OBS-10). SQL time includes the app↔DB network round trip, so a network delay on that path would appear there; none does. DB avg_query_ms is 10.1–12.3 ms outside 30–33 (E-08). *Window:* 0–43. *Evidence:* E-11, E-12, E-08, DQ-08. Observed Fact for the sampled requests only (3 per minute, fixed schedule).

**OBS-INF-08 — At both transitions, infrastructure metrics follow load, not the symptom.** (I1, I2)

| Signal | Minute 18 | Minute 19 | Minute 39 | Minute 40 |
| --- | --- | --- | --- | --- |
| Running users | 500 | 500 | 500 | 400 |
| LB connections | 312 | 308 | 308 | 249 |
| LB Mb/s | 41.4 | 41.2 | 35.8 | 33.6 |
| Retransmit % | 0.02 | 0.03 | 0.02 | 0.01 |
| app1 / app2 CPU % | 54.7 / 53.4 | 52.6 / 54.3 | 51.4 / 45.4 | 43.7 / 44.5 |
| DB CPU % | 29.3 | 27.0 | 23.5 | 24.1 |
| LG1 / LG2 CPU % | 44.2 / 42.6 | 43.9 / 42.2 | 45.9 / 45.9 | 39.3 / 37.3 |
| Payment avg ms (for reference) | 258 | 2092 | 1955 | 263 |

At onset, payment latency rises about 8× while no host, LB or network metric changes beyond its normal minute-to-minute spread. At recovery the infrastructure metrics fall by about the same fraction as users (−20%), which is what load alone predicts. *Window:* 18–19, 39–40. *Evidence:* E-04, E-05, E-06, E-07, E-08, E-09, E-10. Observed Fact.

**OBS-INF-09 — Server threads outgrow the client-side request count from minute 29.** (I1) *(Consistency finding for the application specialist.)*
- Active threads (app1 + app2) vs client-side in-flight requests (load tool, Little's Law): 45–50 vs 59.9–62.8 in 10–18 (ratio about 0.75–0.8); 77 vs 141.1 at minute 19; 243 vs 248.4 at 28; **255 vs 241.6 at 29; 400 vs 241.4–246.6 in 37–39**.
- From minute 27 the client-side in-flight count is flat (240.7–248.7) while threads climb from 220 to 400, about 18 per minute across both nodes.
- At 37–39 the 400 active threads also exceed lb1's 306–310 active connections (E-09).
- If each active thread serves one live inbound request, neither of those can happen. Either some threads are doing work no client is still waiting for (for example after a client-side timeout or abandoned request), or `active_threads` counts something else (a per-minute maximum, or non-request threads; DQ-07), or the LB multiplexes requests over connections.

*Window:* 19–39, both nodes. *Evidence:* E-02, E-03, E-06, E-07, E-09, DQ-07, DQ-10d; I1. Observed Fact for the arithmetic; the cause is not established. This is an app-tier question; I raise it because the load does not explain it.

**OBS-INF-10 — In minutes 19–24, the implied concurrent payment calls exceed the 40 pool connections they are made under.** (I3) *(Platform-limit consistency finding for the application specialist.)*
- Concurrent payment calls ≈ calls/60 × avg latency (E-10). Minutes 10–18: 5.7–6.5 (pool active sum 13–15). Minutes 19–24: **45.9–52.5**. Minutes 25–39: 39.3–45.8.
- The declared pool is 20 per node, 40 in total (E-01). Pool active is 20/20 on both nodes from minute 20 (OBS-06), DB sessions are 40 (E-08), and every one of the 132 traces holds its DB connection across the payment call (`02-evidence.md` A4: held ≥ sql + payment in all traces).
- On those facts, concurrent payment calls cannot exceed 40. In 19–24 the estimate is 15–31% above it; in 25–39 it settles at roughly 40.
- Possible reasons: some checkouts call the payment service without holding a connection (the trace sample is 3/min and fixed-schedule, DQ-08); APM calls and avg_ms are bucketed differently or describe different populations (DQ-07, DQ-11); or pool active is a sample that understates occupancy. The data cannot choose between them.

*Window:* 10–39. *Evidence:* E-01, E-06, E-07, E-08, E-10, E-11, E-12, DQ-07, DQ-08, DQ-11; I3. Observed Fact for the arithmetic. It matters for any pool-demand calculation (Test Lead A2).

**OBS-INF-11 — Generators: CPU healthy; memory_pct is not an independent measurement.** (I2, I4)
- LG CPU 42.1–45.9% on both generators in 10–39, unchanged between 10–18 and 19–39 (as VAL-1 §2.4).
- LG memory_pct is **identical on LG1 and LG2 in all 45 minutes**, and takes exactly one value per user count: 38.0% at 0 users per generator, +1.6 points per 25 users, 54.0% at 250 (I4). It is flat at 54.0% through 9–39 while client-side in-flight requests quadruple (OBS-INF-04).
- That pattern fits a value derived from the user count (or a replicated export), not a per-host measurement. It is far from any limit either way, but "LG memory ≤ 54%" should not be counted as independent evidence of generator memory health. This does not change VAL-1: CPU, users, mix and per-generator symmetry carry that decision.

*Window:* 0–44, LG1 and LG2. *Evidence:* E-05, E-04; I2, I4. Observed Fact.

**OBS-INF-12 — Declared platform limits and whether they were reached.** (E-01; OBS-12)

| Limit | Declared | Reached? | Evidence |
| --- | --- | --- | --- |
| DB pool per node | 20 (40 total) | Yes, 20/20 both nodes, minutes 20–39 | E-06, E-07 |
| Request threads per node | 200 | Yes, 200/200 both nodes, minutes 37–39 | E-06, E-07 |
| LG size | 4 vCPU each | No; CPU ≤ 45.9% | E-05 |
| Payment sandbox rate limits | "undocumented" | Unknown | E-01, DQ-10a |
| App/DB instance size, CPU quota, host memory | Not declared | Unknown | — |
| LB connection limit, bandwidth | Not declared | Unknown; observed max 314 connections, 43.0 Mb/s | E-09 |
| DB max_connections | Not declared | Unknown; observed max 46 sessions | E-08 |

The only limits shown to be reached are application configuration limits, not host or network capacity. *Evidence:* as tabled. Observed Fact.

## 3. Hypotheses

**HYP-INF-1 — Hosts, the load balancer and the inbound network do not explain the onset or the degradation, within the metrics supplied.**
- **Claim:** across 19–39, app host CPU, DB host CPU, lb1 connections, lb1 throughput and retransmits show no saturation and no change the load does not explain; at onset (18 → 19) none of them moves while payment latency rises 8×.
- **Window and scope:** minutes 10–39 with transitions 18–19 and 39–40; app1, app2, DB host, lb1.
- **Evidence:** OBS-INF-01, -03, -04, -05, -06, -07, -08; E-06, E-07, E-08, E-09 (all 30/30 steady-state minutes).
- **Grade:** Observed Fact for "these metrics show no stress and no onset change". It is a bounded negative, not a cause.
- **Confidence:** High for the bounded statement — complete per-minute coverage of the symptom window, live metrics that track load in ramp-up and ramp-down, and an 8× symptom against flat infrastructure signals.
- **What it does not cover:** host memory outside the JVM, disk I/O, NIC-level errors, per-core or quota-throttled CPU, LB queueing or per-node balance, the app→sandbox network path (HYP-INF-2). It does not say "the infrastructure is fine".
- **Alternatives:** (a) CPU throttling under a container quota would show as latency with moderate reported CPU — no quota is declared and no throttling metric exists, so this is unexcluded but unsupported; (b) LB queueing would not show in a connection count that tracks users (OBS-INF-04) — but client-side latency for search and add_to_cart rises gradually with pool wait and threads (OBS-05, OBS-06), which is an app-tier pattern, not an LB one.

**HYP-INF-2 — Part of the caller-side payment latency rise is spent on the outbound network path to the sandbox (egress, NAT/proxy, DNS, TLS).**
- **Claim (kept open as an alternative, not proposed as likely):** the ~1.8 s step in E-10 is measured from the caller and includes the network path, which no source monitors.
- **Window and scope:** onset minute 19 through 39; both nodes (E-10 has no node split).
- **Evidence for:** none. **Evidence against:** inbound network is clean (OBS-INF-05, -06) and the app→DB path is clean (OBS-INF-07), but those are different paths. Payment errors are 0 in every minute (E-10), which says nothing about delay.
- **Grade:** no grade reached — no signal covers this path. **Confidence:** Low, because the path is unmonitored, not because evidence points against it.
- **Why it matters:** it is part of VAL-1 U-2. If the extra time is on our side of the boundary (outbound client pool, egress, DNS), the onset is an environment or system finding, not a sandbox event.
- **Confirming experiment (rule 12):** owner: platform/network owner with the APM owner. Change: in the rerun, record per-call timing phases for the payment call (DNS, TCP connect, TLS handshake, time to first byte) on both nodes, egress/NAT/proxy connection and error counters, and run a lightweight synthetic probe from each app node to the sandbox and to a control endpoint every 10 s. Success measure: phase timings and probe latency explain the caller-side latency to within a stated tolerance. Refuting result: if a latency step appears with connect/TLS/DNS phases unchanged and only time-to-first-byte rising, and the control-endpoint probe stays flat, the network path is ruled out and the time is in the sandbox (or the app's own client queue, if connection-acquire time rises).

**HYP-INF-3 — app1 spends extra CPU in 27–39 on garbage collection linked to its heap growth.**
- **Claim:** the +2.6 to +8.3 point app1−app2 CPU gap in 27–39 moves with app1's heap (82.3–86.3%) and GC pause (643–863 ms), not with load or request distribution.
- **Window and scope:** minutes 27–39, app1 vs app2.
- **Evidence:** OBS-INF-02, OBS-11; E-06, E-07.
- **Grade:** Correlation — CPU and heap/GC change together in the same aligned minutes, both from APM (E-06). **Confidence:** Medium — the alignment is exact and the threads/pool on both nodes match, but GC metric semantics are undocumented (DQ-07) and there are no GC logs or JVM settings (DQ-10f).
- **Alternatives:** (a) app1 received more requests (LB imbalance) — set aside as primary because threads (within 5 per minute) and pool (20/20) match, and the CPU gap appears in the same minute as the heap step (27) rather than gradually; not excluded because there is no LB per-node data. (b) A host-level difference between nodes (instance size, co-tenant) — not supported, as the nodes match within ±2.6 points in 10–26.
- **Relation to the symptom:** starts 8 minutes after onset, so it cannot explain onset (rule 8); OBS-11 shows no SLA-level difference by node. It is a separate node-level question (SW-5). Even at its peak, app1 CPU is ≤ 54.7%, so it is not a host capacity issue.
- **Confirming experiment:** owner: APM/platform owner. Compare app1 and app2 JVM and host configuration (heap size, GC algorithm, instance type) and collect GC logs in the rerun. Success: a configuration difference or GC log that accounts for app1's heap/GC and CPU delta. Refuting result: identical configuration and GC logs showing app2 behaving the same once its own queue reaches app1's level — then the effect is load-driven, not node-specific.

## 4. Limits of my view

- **Outbound path to the sandbox is unmonitored** (no egress, NAT, proxy, DNS or TLS metrics; E-10 is caller-side only). This is the most important gap: it is where the dominant symptom sits, and it is why HYP-INF-1 stops at the inbound network.
- **No host metrics beyond CPU** on app nodes (only JVM heap) or the DB host: no host memory, swap, disk I/O, NIC errors, or CPU steal/throttling.
- **No platform sizing:** app and DB instance sizes, core counts, CPU quotas, LB connection limits, bandwidth limits and DB max_connections are not declared. "Headroom" is against 100% of the reported metric only.
- **LB:** one aggregate component (lb1), no per-node split, no queue depth, no 5xx/reset counters. The connection metric tracks users, so it cannot show request queueing (OBS-INF-04).
- **Metric semantics** (point-in-time, mean or max per minute) are undocumented for every host and network metric (DQ-07). OBS-INF-09 and OBS-INF-10 depend on that.
- **Sandbox side:** no tenancy, throttling or incident data (DQ-10a). I found no environment-side evidence of another tenant or of throttling; that is a gap, not a finding of "no throttling" (Test Lead I4).
- **LG memory** is not an independent measurement (OBS-INF-11).

## Handoff

- **To the Test Lead.**
  - Infrastructure answer to I2 and I3: hosts, lb1 and the inbound network show no stress and no onset change across the whole symptom window (HYP-INF-1, High, bounded). App CPU is 44.6–54.8% throughout 10–39; the tier is not CPU-bound in the reported metric.
  - Answer to I4: no environment-side evidence of throttling or other tenants exists in this dataset; it is a gap (DQ-10a).
  - Answer to I1: generator CPU healthy and log level "standard" on both, as VAL-1 found; script_errors remain undefined (DQ-05). LG memory is not independent evidence (OBS-INF-11).
  - The rule-out must not be reported as "infrastructure is fine": the outbound payment path is unmonitored (HYP-INF-2). Add its instrumentation to T-4.
- **To the Application specialist.**
  - OBS-INF-10: in 19–24 the implied concurrent payment calls (46–52) exceed the 40 pool connections; any pool-demand calculation (A2) has to reconcile this.
  - OBS-INF-09: from minute 29 active threads exceed client-side in-flight requests and lb1 connections, and keep rising while client concurrency is flat. Worth checking for work that continues after the client has gone, before reading the 200-thread max as pure queueing (A4).
  - OBS-INF-02 / HYP-INF-3: app1's extra CPU from minute 27 moves with its GC; relevant to A5.
- **To the Database specialist.** DB host CPU (≤ 29.3% outside 30–33, 42.2–44.5% in 30–33) and trace SQL time (25–59 ms throughout) show no host or app→DB network stress (OBS-INF-03, -07). The 6 extra sessions in 30–33 come from a non-pool client.
- **To the Test Validity Reviewer.** OBS-INF-11 (LG memory derived from user count) does not change VAL-1 but should not be cited as generator memory evidence.
- **Open questions:** instance sizes and CPU quotas for app and DB hosts; LB per-node metrics and limits; what `active_threads` counts and how it is sampled; egress path and outbound HTTP client configuration for the payment call.

## Appendix: commands run

Scripts are in `/tmp/inf/`, outside `data/`, run with `python3 -I` and the data folder as an argument: `python3 -I /tmp/inf/iN.py /home/claude/performance-evidence-lab/examples/02-connection-pool/data`.

**I1. LB connections, throughput per TPS, client in-flight estimate, threads and pool per minute (minutes 0–44)**
```python
import csv,sys
D=sys.argv[1]
N={int(r['elapsed_min']):r for r in csv.DictReader(open(D+'/network.csv'))}
A={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open(D+'/app_servers.csv'))}
V={}
for r in csv.DictReader(open(D+'/vusers.csv')):
    V.setdefault(int(r['elapsed_min']),0); V[int(r['elapsed_min'])]+=int(r['running_vusers'])
T={}
for r in csv.DictReader(open(D+'/transactions.csv')):
    m=int(r['elapsed_min']); T.setdefault(m,[0,0.0]); T[m][0]+=int(r['count']); T[m][1]+=int(r['count'])*float(r['avg_s'])
for m in range(0,45):
    n=N[m]; c=int(n['active_connections']); mb=float(n['throughput_mbps'])
    tps=T[m][0]/60 if m in T else 0
    infl=T[m][1]/60 if m in T else 0          # Little's Law: completions/s x mean response s
    th=int(A[(m,'app1')]['active_threads'])+int(A[(m,'app2')]['active_threads'])
    pl=int(A[(m,'app1')]['db_pool_active'])+int(A[(m,'app2')]['db_pool_active'])
    print(m,V[m],c,round(c/V[m],3) if V[m] else '-',mb,round(tps,1),round(mb/tps,3) if tps else '-',round(infl,1),th,pl,n['retransmit_pct'])
```
Key outputs: LB connections 307–312 (10–18), 305–314 (19–39); Mb/s per TPS 0.413–0.428 (10–18), 0.408–0.431 (19–39); client in-flight 59.9–62.8 (10–18), 141.1 (19), 240.7–248.7 (27–39); threads sum 45–50 (10–18), 77 (19), 243 (28), 255 (29), 400 (37–39); retransmit 0.01–0.04% all minutes; minute 44 connections −1.

**I2. Host resources per minute and per window (app, DB, LG)**
```python
import csv,sys,statistics as st
from datetime import datetime,timezone
D=sys.argv[1]
A={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open(D+'/app_servers.csv'))}
L={(int(r['elapsed_min']),r['generator']):r for r in csv.DictReader(open(D+'/load_generators.csv'))}
s=datetime(2026,10,8,10,tzinfo=timezone.utc); B={}
for r in csv.DictReader(open(D+'/database.csv')):
    B[int((datetime.strptime(r['window_start_local'],'%Y-%m-%dT%H:%M:%S%z')-s).total_seconds()//60)]=r
T={}
for r in csv.DictReader(open(D+'/transactions.csv')):
    m=int(r['elapsed_min']); T[m]=T.get(m,0)+int(r['count'])
# per minute: app1/app2 cpu, heap, gc, threads; cpu1-cpu2; (cpu1+cpu2)/tps; DB cpu, sessions, query, lock, event; LG cpu, mem, script_errors
# per window (10,18),(19,26),(27,39),(19,39): min/median/max of app1, app2, DB CPU; min/max of cpu1-cpu2 and (cpu1+cpu2)/tps; LG mem and cpu
```
Key outputs: app1 CPU 51.4/52.7/54.8 (10–18), 47.5/52.45/53.3 (19–26), 50.5/52.1/54.7 (27–39); app2 50.7/52.6/54.2, 49.4/52.9/54.6, 44.6/47.1/49.1. app1−app2: −2.6..+2.2, −2.1..+1.8, +2.6..+8.3. CPU sum/TPS: 1.036–1.089, 1.042–1.091, 1.122–1.197. DB CPU 26.8–29.3 (10–18), 23.5–28.7 (19–39 excl. 30–33), 42.2–44.5 (30–33). LG CPU 42.1–45.9 (10–39); LG memory 54.0 throughout 9–39. Transition values as in OBS-INF-08.

**I3. Concurrent payment calls vs pool occupancy (minutes 8–43)**
```python
import csv,sys
D=sys.argv[1]
X={int(r['elapsed_min']):r for r in csv.DictReader(open(D+'/external_calls.csv'))}
A={(int(r['elapsed_min']),r['node']):r for r in csv.DictReader(open(D+'/app_servers.csv'))}
C={}
for r in csv.DictReader(open(D+'/transactions.csv')):
    if r['transaction']=='checkout': m=int(r['elapsed_min']); C[m]=C.get(m,0)+int(r['count'])
for m in range(8,44):
    x=X[m]; cc=int(x['calls'])/60*int(x['avg_ms'])/1000
    pl=int(A[(m,'app1')]['db_pool_active'])+int(A[(m,'app2')]['db_pool_active'])
    print(m,x['calls'],C.get(m),x['avg_ms'],x['p95_ms'],x['errors'],round(cc,1),pl)
```
Key outputs: concurrent payment calls 5.7–6.5 in 10–18 (pool sum 13–15); 52.3, 52.5, 47.2, 52.0, 50.0, 45.9 in 19–24 (pool sum 34, then 40); 39.3–45.8 in 25–39 (pool sum 40); 1.2–5.2 in 40–43. Payment calls equal checkouts in every minute; errors 0.

**I4. LG memory identity and LB connection-to-user ratio**
```bash
cd /home/claude/performance-evidence-lab/examples/02-connection-pool/data && python3 -I -c "
import csv
L={}
for r in csv.DictReader(open('load_generators.csv')): L.setdefault(int(r['elapsed_min']),{})[r['generator']]=r
V={}
for r in csv.DictReader(open('vusers.csv')): V.setdefault(int(r['elapsed_min']),{})[r['generator']]=int(r['running_vusers'])
same=sum(L[m]['LG1']['memory_pct']==L[m]['LG2']['memory_pct'] for m in L); print('mem identical minutes',same,'of',len(L))
print('distinct (users_per_LG, mem):',sorted({(V[m]['LG1'],L[m]['LG1']['memory_pct']) for m in L}))
N={int(r['elapsed_min']):int(r['active_connections']) for r in csv.DictReader(open('network.csv'))}
rs=[N[m]/(V[m]['LG1']+V[m]['LG2']) for m in range(2,44)]; print(round(min(rs),3),round(max(rs),3))
"
```
Output: memory identical in 45 of 45 minutes; one memory value per user count — (0, 38.0), (25, 39.6), (50, 41.2), … (225, 52.4), (250, 54.0); LB connections / running users 0.61–0.63 over minutes 2–43.
