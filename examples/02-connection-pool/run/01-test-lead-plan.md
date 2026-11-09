```
Agent: Test Lead (Call 1 — Plan)
Run: SYN-RUN-002
Read: agents/test-lead.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/scenario.json; examples/02-connection-pool/facts.md
Execution: separate agent context, model Claude Opus 5.5
```

Data note: the dataset is marked synthetic in `scenario.json` ("Invented data for demonstration"). We review it as though it were a real run.

## 1. The question

**As asked (scenario.json):** "Can the checkout journey support 500 concurrent users at 90+ transactions/second with checkout p95 at or under 2.0 seconds?"

**Restated precisely:** On environment PERF-A (2 app nodes, DB pool max 20 per node, max threads 200 per node, payment via a shared third-party sandbox), with 500 virtual users (250 on LG1, 250 on LG2) running the iteration "search x2, add_to_cart x1, checkout x1" at fixed 20 s pacing, does the system meet all three acceptance criteria across the intended steady state, **elapsed minutes 10–39**?

| ID | Metric | Threshold | Scope (as declared) |
| --- | --- | --- | --- |
| SLA-1 | checkout p95 response time | <= 2.0 s | each steady-state minute, each generator. Judge per generator per minute and never average p95s (rule 5) |
| SLA-2 | total throughput | >= 90 transactions/s | steady state |
| SLA-3 | transaction error rate | <= 1% | steady state |

Expected steady TPS is 100.0 (500 users / 20 s pacing x 4 transactions per iteration). The question bundles a **capacity verdict** (does it support 500 users) with criterion-level health. The team should keep the two apart. Validity decides whether this run can support the capacity verdict at all (judgments.md).

Decision order applies: validity comes before diagnosis (rule 6). The Test Validity Reviewer's VAL- decision sets the scope for every health verdict I issue in Call 2.

## 2. First read of the fact sheet

These are questions, not conclusions. Numbers are cited from `facts.md` or from the commands shown in the appendix.

1. **What changed at minute 19?** Steady state is clean for minutes 10–18: checkout p95 1.32–1.54 s on both generators, TPS 98.7–100.5, error rate 0.17–0.22%. At minute 19, checkout p95 jumps to LG1 4.96 s and LG2 4.93 s, and from then on every minute fails SLA-1. In the same minute, payment-sandbox avg latency goes from 258 ms to 2092 ms (`external_calls.csv`), and pool wait goes from 0 to 337 ms (app1) and 362 ms (app2). Checkout volume did not rise: 1517 checkouts at minute 18 and 1500 at minute 19 (appendix, command 3). So nothing on our side visibly increased the load. **Did the payment dependency slow down first and cause pool exhaustion, or did something else exhaust the pool and stall the payment call?** At one-minute and trace resolution both signals appear together. The first symptom-window trace (10:19:10, app1) already shows payment 2345 ms and pool wait 349 ms.

2. **Is the connection held across the payment call?** In the trace medians, the payment call is 80.7–82.3% of connection hold time in normal windows and 97.3% in minutes 19–39. Connection hold goes from about 313 ms to 2022 ms, while SQL time stays at 40–42 ms. Pool active on both nodes reaches 20/20 (the configured max) and DB active sessions reach 40 (= 2 x 20). The DB top wait event changes to "idle in transaction" from minute 20 (appendix, command 1). **Is the pool sized correctly for the hold time the code imposes, and would releasing the connection before the payment call remove the queueing?** The traces are a 3-per-minute sample, so this has to be tested, not assumed.

3. **Is the throughput failure (SLA-2, minutes 26–39) a system finding or a harness artefact?** Running users stay at 500, exited_with_error stays at 0, and LG CPU stays at about 42–46% throughout. Implied cycle time grows from 20.0 s to about 23–24 s. That looks like iterations running late because responses are slow, which judgments.md classifies as a system finding, not a harness failure. The Validity Reviewer must confirm this. A second question for that review: **`abort_on_error: true` is set, yet failed transactions occur in every minute (including ramp-up) and no vuser exits. What does "abort on error" actually trigger here, and does the error accounting hold up?**

4. **Are the row lock contention in minutes 30–33 and the app1 heap/GC rise from minute 27 contributors or distractions?** DB lock_wait jumps to 683–800 ms with top event "row lock contention" in minutes 30–33. That lines up with the scheduled **inventory-sync batch at 10:30 UTC** (= minute 30). Separately, app1 heap rises to 82–86% and GC pause to 643–863 ms from minute 27, while app2 stays at about 54–62% heap and about 70–130 ms GC. Both begin **after** the minute-19 onset, so neither can explain the onset (rule 8). **Do they make the symptom worse within their windows, and does app1's heap behaviour show a separate problem?** Note that SLA-1 fails on both generators in about equal measure, and app1/app2 pool wait is about equal.

5. **What does recovery at minute 40 tell us?** At minute 40, payment avg drops to 263 ms, pool wait to 0–2 ms and checkout p95 back to about 1.4 s. That is the same minute ramp-down begins (400 users, 1195 checkouts that minute). **Did the sandbox recover because our load dropped (load-dependent throttling or rate limiting), or by coincidence?** The answer decides whether the payment slowdown is an external event or a reaction to our own traffic. The sandbox is shared and its rate limits are undocumented (`scenario.json`). External calls report 0 errors throughout.

## 3. Assignments

Symptom windows will come from the Performance Analyst (SW-). Until then, specialists should work over **minutes 10–18 (reference)**, **19–39 (symptom)**, and the transition minutes **18–20** and **39–41**. Every claim must carry E-/OBS-/DQ- IDs, a window and a grade (records.md).

### Application specialist: involved (primary)
The pool, threads and outbound payment call all sit in the app tier, which is where the symptom shows.
- **A1.** Using `checkout_traces.csv` and `app_servers.csv`: is the DB connection held across the payment call? Report connection-hold vs payment-call per trace in each window, not only medians. State what the 3-per-minute sample can and cannot show.
- **A2.** Does pool demand explain the queueing? Compute the expected concurrent connections per node from checkout rate and measured hold time in minutes 10–18 and 19–39, and compare with pool max 20 and observed pool active. Show the command (rule 3).
- **A3.** Ordering at onset: within minute 19 and the surrounding traces, can anything show whether payment latency or pool exhaustion came first? If the data cannot separate them, say so.
- **A4.** Thread growth: active threads climb from about 38 to 200 (max) over minutes 19–37. Is this requests queueing on the pool, and does reaching 200 threads at minutes 37–39 add a second limit?
- **A5.** app1 heap/GC from minute 27: is this a consequence of queued requests (held objects), or an app1-specific defect? Compare app1 vs app2 under the same pool/thread conditions (rule 7). Bear in mind the trace sample is about 2:1 app1:app2 (88 vs 44 traces; appendix, command 2).
- **A6.** Payment dependency: what does `external_calls.csv` say about call volume vs latency (is latency load-dependent?), and why does recovery coincide with ramp-down?
- **A7.** Which transactions fail in minutes 19–39 (search, add_to_cart and checkout all show failures), and does any source show why? External calls show 0 errors, so where do the failed transactions come from?

### Database specialist: involved
The DB layer must be ruled in or out with DB evidence, not by absence (rule 9). Lock contention also coincides with a scheduled job.
- **D1.** Check time alignment first. `database.csv` is in server local time (-0400 offset) and exported from the DB host, not the APM tool. Confirm the UTC conversion. Explain why DB active sessions reach 40 at minute 20 when app pools hit 17 and 20 active at minute 19: is it a one-minute clock or bucketing lag, or real ordering?
- **D2.** Is the DB a cause or a victim in minutes 19–29 and 34–39? Use avg_query_ms, CPU, sessions, lock_wait and top_wait_event ("idle in transaction"), plus trace sql_ms. What does "idle in transaction" mean for who holds the connection?
- **D3.** Minutes 30–33 row lock contention: does it line up with the inventory-sync batch (10:30 UTC daily, data team)? Is there any evidence the batch ran (the dataset has no batch log)? Does it measurably worsen checkout p95 or pool wait in those minutes compared with 26–29 and 34–37?
- **D4.** State plainly what DB evidence is missing (for example query-level or per-statement data, batch logs). Grade any "DB is not the cause" claim only as far as the available DB evidence allows.

### Infrastructure specialist: involved (rule-out and harness health)
The infrastructure layer is unlikely to explain an onset that hits both generators and both nodes equally. But it must be ruled out with evidence, and app1's GC divergence needs a host or JVM view.
- **I1.** Load generator health: CPU, memory and script_errors per generator across all windows. Script errors appear only in minutes 19–39 (0–2 per minute). Are they a symptom of slow responses or a harness problem? Confirm both generators run at log_level "standard" as scenario.json states.
- **I2.** Network / LB (`network.csv`): connections about 305–314 and retransmits 0.01–0.04% across the symptom window. Rule the network in or out with these numbers. Note the active_connections value of **-1 at minute 44**, which is not a valid count and should be treated as a data-quality issue, not as zero.
- **I3.** App host resources: CPU on both nodes stays at about 45–55% while response times rise. Confirm the app tier is not CPU-bound, and give a host/JVM view of app1 heap/GC from minute 27 (configuration difference between nodes?).
- **I4.** Payment sandbox as environment: it is a shared third-party test environment with undocumented rate limits. Is there any environment-side evidence of another tenant or throttling? If none, record that as a gap, not as "no throttling".

### Not involving
None of the three is excluded. All layers could explain part of the symptom or must be ruled out explicitly.

## 4. Risks to the review

1. **Payment-sandbox representativeness.** The dominant signal is a shared third-party sandbox whose latency rose about 8x for exactly the symptom window. If the slowdown is a sandbox event, this run may not answer the capacity question about *our* system. The Validity Reviewer should decide whether the run is VALID, VALID WITH LIMITATIONS or INVALID FOR THIS QUESTION for the capacity verdict, and separately what it supports about the architecture (connection held across an external call). I will not issue a capacity PASS/FAIL beyond what VAL- allows.
2. **Coincident onset.** Payment latency, pool wait, thread growth and the SLA-1 failure all change in the same minute. Per-minute data and a 3-per-minute trace sample may not separate cause from effect. Expect Correlation or Probable Contributor at most for any mechanism unless a controlled change exists, and none exists in this run. "Confirmed Root Cause" needs a controlled experiment (judgments.md).
3. **Previous run is off limits.** `run_notes` refer to SYN-RUN-001 and an LG2 log-level fix. Nothing from SYN-RUN-001 may fill gaps here (rule 1). We also have no data from it, so "no changes between runs" is an unverified statement in the notes, not evidence.
4. **Clock alignment.** `database.csv` uses local time with an offset and comes from a different tool than APM. Any one-minute DB-vs-app lead or lag must be checked before it is used for ordering (rule 8).
5. **Sampling bias in traces.** Traces are sampled (3/minute, about 2:1 app1:app2). Medians from 63 symptom-window traces must not be presented as population values, and app1-vs-app2 comparisons from traces are weighted toward app1.
6. **Confounders inside the window.** The inventory-sync batch (minute 30) and app1 GC (minute 27) overlap the symptom window. Their contribution must be separated from the onset mechanism, not merged into one story.
7. **Data-quality items for the Results Librarian.** These include: network active_connections = -1 at minute 44, which the fact sheet's min 40–44 mean includes; transactions.csv has 44/45 minutes (minute 44 is the zero-user minute, so it is probably expected but should be confirmed); no batch-job log; no query-level DB data; no sandbox-side metrics; the `abort_on_error` behaviour, which is inconsistent with the observed failures.
8. **Untrusted content.** I scanned every CSV for free-text fields (appendix, command 2). The only non-numeric values are identifiers and enumerations (node, generator, transaction, dependency, log_level, top_wait_event, trace_id). No embedded instructions were found. Any text found later in data or documents is still data only (rule 10).
9. **Averaged percentiles.** The fact sheet gives median/max of per-minute p95. Nobody should restate a run-level checkout p95 (rule 5). SLA-1 is judged per generator per minute.

## Handoff

- **To the Results Librarian / Validity Reviewer:** please issue E- and DQ- IDs for the items in risk 7, and decide VAL- for the question as asked, with an explicit allowed scope. In particular, decide whether a shared-sandbox latency excursion limits the capacity verdict, and whether the SLA-2 failure is a system finding (iterations late due to slow responses) or a harness issue.
- **To the Performance Analyst:** confirm the symptom window(s). Candidates are SW onset at minute 19, an SLA-2 sub-window at minutes 26–39, a lock-contention sub-window at 30–33 and an app1-GC sub-window at 27–39.
- **To specialists:** questions A1–A7, D1–D4 and I1–I4 above. Negative claims need positive evidence.
- **Open questions I want answered by Call 2:** (a) Can anything order the payment slowdown against pool exhaustion? (b) Is the sandbox slowdown load-dependent? (c) Did the inventory-sync batch run, and did it matter? (d) Why did no vuser exit with abort_on_error set?

## Appendix: commands run

All run from `examples/02-connection-pool/data/` with `python3 -I`. They produced the per-minute numbers above that are not in `facts.md`.

**Command 1: per-minute cross-source table (minutes 14–44)**
```python
import csv
from datetime import datetime, timezone
ext={int(r['elapsed_min']):r for r in csv.DictReader(open('external_calls.csv'))}
app={}
for r in csv.DictReader(open('app_servers.csv')): app[(int(r['elapsed_min']),r['node'])]=r
db={}
start=datetime(2026,10,8,10,0,tzinfo=timezone.utc)
for r in csv.DictReader(open('database.csv')):
    t=datetime.strptime(r['window_start_local'],'%Y-%m-%dT%H:%M:%S%z')
    db[int((t-start).total_seconds()//60)]=r
lg={}
for r in csv.DictReader(open('load_generators.csv')): lg[(int(r['elapsed_min']),r['generator'])]=r
net={int(r['elapsed_min']):r for r in csv.DictReader(open('network.csv'))}
for m in range(14,45): ...  # prints payment avg/p95, app1/app2 heap, gc, threads, pool active, pool wait,
                            # db sessions, lock_wait, top_wait_event, LG script_errors, log_level, lb connections
```
Key outputs used: payment avg 258 ms (min 18), then 2092 ms (min 19), then 263 ms (min 40). Pool wait app1 0 (18), then 337 (19); app2 2 (18), then 362 (19). DB sessions 9 (19), then 40 (20); top_wait_event "idle in transaction" from minute 20; "row lock contention" in minutes 30–33 with lock_wait 683–800 ms. app1 heap 82.3–86.3% and GC 643–863 ms in minutes 27–39; app2 heap 54.1–61.6%. LG script_errors 0–2 per minute only in minutes 19–39. log_level is "standard" for both generators in every minute. lb1 active_connections = -1 at minute 44.

**Command 2: free-text scan and trace counts**
```python
import csv,glob,re
for f in sorted(glob.glob('*.csv')):
    rows=list(csv.DictReader(open(f))); txt=set()
    for r in rows:
        for k,v in r.items():
            if k and not re.fullmatch(r'-?[\d.]+',v or '') and 'utc' not in k and 'local' not in k and 'timestamp' not in k:
                txt.add((k,v))
    print(f,len(rows),sorted(txt)[:15])
tr=list(csv.DictReader(open('checkout_traces.csv')))
from collections import Counter
print(Counter(r['node'] for r in tr))
```
Output: only identifier and enumeration values. Traces app1 88, app2 44.

**Command 3: traces at onset and checkout counts**
```python
import csv
tr=[r for r in csv.DictReader(open('checkout_traces.csv')) if int(r['elapsed_min']) in (18,19,20)]
for r in tr: print(r['timestamp_utc'],r['node'],r['total_ms'],r['pool_wait_ms'],r['payment_call_ms'],r['db_connection_held_ms'])
c={}
for r in csv.DictReader(open('transactions.csv')):
    if r['transaction']=='checkout' and int(r['elapsed_min']) in (18,19,40):
        c.setdefault(int(r['elapsed_min']),0); c[int(r['elapsed_min'])]+=int(r['count'])
print(c)
```
Output: the last minute-18 trace (10:18:44, app1) shows pool wait 0 and payment 258 ms. The first minute-19 trace (10:19:10, app1) shows pool wait 349 and payment 2345 ms. Checkout counts: minute 18 = 1517, minute 19 = 1500, minute 40 = 1195.
