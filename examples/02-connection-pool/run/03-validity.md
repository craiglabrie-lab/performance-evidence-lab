```
Agent: Test Validity Reviewer
Run: SYN-RUN-002
Read: agents/test-validity-reviewer.md; method/judgments.md; method/rules.md; method/records.md; examples/02-connection-pool/data/ (scenario.json, transactions.csv, vusers.csv, load_generators.csv, app_servers.csv, database.csv, network.csv, external_calls.csv, checkout_traces.csv); examples/02-connection-pool/facts.md; examples/02-connection-pool/run/01-test-lead-plan.md; examples/02-connection-pool/run/02-evidence.md
Execution: separate agent context, model Claude Opus 5.5
```

Data note: `scenario.json` marks this dataset as synthetic. It is reviewed here as though it were a real run.

This file judges the test, not the system. Evidence IDs (E-, DQ-) are those registered in `02-evidence.md`. Numbers come from `facts.md` (E-13), from `02-evidence.md`, or from the commands in the appendix (rule 3).

## Decision

**VAL-1: VALID WITH LIMITATIONS.**

The harness delivered the intended workload, and the generators were healthy for the whole intended steady state. So the per-criterion results for this run in PERF-A stand. That includes the SLA-1 and SLA-2 failures: they are findings about the system and its payment dependency, not about the harness. The limits are these:

- The run **cannot give a capacity verdict, in either direction**, on whether *our* checkout stack supports 500 users. The degradation began at minute 19 with no change in our load. It coincided with a caller-side latency step on a **shared third-party sandbox** that has undocumented rate limits and no provider-side evidence.
- The clean period is only 9 minutes long (minutes 10–18), against a declared steady state of 30 minutes.
- The SLA-3 result depends on error accounting whose semantics are undocumented (`abort_on_error`, failure definitions).

## 1. The question and what validity must support

Question (E-01): *"Can the checkout journey support 500 concurrent users at 90+ transactions/second with checkout p95 at or under 2.0 seconds?"*

To answer it, the run needs: 500 users actually running at the intended pacing for minutes 10–39; healthy, equivalent generators; harness settings that do not distort load or measurement; a representative environment; and evidence coverage for every steady-state minute. The question also bundles two things the Test Lead asked me to keep apart (`01-test-lead-plan.md` §1):

- **(a) Criterion-level health in this run:** did SLA-1/2/3 hold in PERF-A on 2026-10-08 10:10–10:39 UTC?
- **(b) A capacity verdict:** is 500 users within what our system can carry?

## 2. Checks

### 2.1 Users: PASS

- Running equals scheduled for every generator and every minute, in all 90 rows. exited_with_error is 0 throughout (E-04; `facts.md` workload table; command V1).
- Each generator reached 250 users at minute 9 and held 250 through minute 39: 500 in total for all 30 intended steady-state minutes.
- No user exited early.

### 2.2 Throughput and pacing: shortfall is late iterations, not missing users

Expected throughput is 100 TPS. Implied cycle time = running users ÷ checkouts per second (one checkout per iteration), computed per generator (V1):

| Minutes | TPS (total, `facts.md`) | Implied cycle, LG1 | Implied cycle, LG2 | Running users |
| --- | --- | --- | --- | --- |
| 10–18 | 98.7–100.5 | 19.5–20.4 s | 19.6–20.4 s | 250 + 250 |
| 19–23 | 98.9–101.1 | 19.6–20.5 s | 19.5–20.5 s | 250 + 250 |
| 24–25 | 97.7, 92.2 | 21.0, 21.7 s | 20.2, 22.0 s | 250 + 250 |
| 26–39 | 84.2–88.8 | 22.3–23.8 s | 22.7–24.0 s | 250 + 250 |
| 40–43 (ramp-down) | 19.8–80.9 | 19.7–20.6 s | 19.5–20.3 s | falling, as scheduled |

- Users were present in every minute. Iterations ran late once responses lengthened. Both generators show this to the same degree.
- **Consistency check (model, not a measured fact).** Add the per-minute mean response time of one iteration (2 × search + add_to_cart + checkout, from E-02/E-03 avg_s) to four 3 s think times. This sum crosses the 20 s pacing at about minute 23–24 (V1: 19.4–20.1 s at minute 23, 20.7–20.9 s at minute 24). From minute 26 it tracks the implied cycle within about 0.5 s (minute 30: 23.8 s modelled vs 23.8/24.0 s observed).
- `scenario.json` does not say where think time is applied. So the four-think-times assumption is unverified, but the fit is close.
- **Conclusion:** the SLA-2 failure in minutes 26–39 comes from users who were present but whose responses were slow. Under judgments.md this is **a finding about the system (including its payment dependency), not a harness failure.**

### 2.3 Transaction mix: PASS

- Design ratio is search : add_to_cart : checkout = 2 : 1 : 1.
- Achieved ratio by window (V2): search/checkout 1.999, 1.988, 2.000 and 2.033, and add_to_cart/checkout 0.999, 1.000, 0.995 and 0.999, for minutes 0–9, 10–18, 19–39 and 40–43.
- Per-generator per-minute ratios stay between 1.93 and 2.09, and between 0.95 and 1.04 (V1). This is minute-boundary noise.
- The mix held through the degradation.

### 2.4 Generator health: PASS

- LG CPU never exceeds 45.9%, and memory never exceeds 54.0%, on either generator (E-05; `02-evidence.md` A6).
- In steady state, CPU is 42.1–45.9% on both generators in both windows (`facts.md`). It does not rise during minutes 19–39.
- log_level is "standard" on both generators in all 45 minutes (E-05). The SYN-RUN-001 issue (LG2 log level) is therefore not present in this run.
- The two generators behave the same:
  - TPS per generator is 48.9–51.0 in minutes 10–24 and 41.9–44.5 in minutes 26–39 (`facts.md`).
  - Steady-state error rate is LG1 0.465% and LG2 0.469% (`02-evidence.md` A5).
  - Checkout p95 moves together. Both pass in every minute 10–18 and both fail in every minute 19–39 (`facts.md`).
- No generator shows a symptom the other lacks (rule 7). So nothing here points to a generator-specific distortion.

### 2.5 Harness settings: one open defect, bounded

- **abort_on_error = true, yet 871 transactions failed and no user exited** (DQ-04). Whatever the setting does, it did not remove users, so it did not reduce the delivered load (§2.1).
- No evidence that failures ended iterations early. If a failure skipped the rest of an iteration, checkouts would fall short of search/2 in minutes 19–39, where failures run at about 0.6%. The ratio is 2.000 (V2).
- The setting still does not behave as declared. Its semantics are undocumented, so it counts as a test-integrity issue (T-2).
- **Pacing and think time** are declared (fixed 20 s pacing, 3 s think time). Where think time is applied is not declared (§2.2).
- **Client-side timeouts are not declared anywhere.** It is also unknown whether failed requests are included in avg_s and p95_s (DQ-10d). In the worst steady-state window, failures are 0.58–0.60% of each transaction type (V2). Removing or adding that share could move a per-minute p95 only slightly. Every SLA-1 failure is above 2.0 s by at least 2.76 s (lowest failing value 4.76 s, `facts.md`). So this unknown cannot change the SLA-1 outcome.
- **script_errors** (46 in total, only in minutes 19–39, 0–2 per minute) has no definition and does not reconcile with transaction failures (DQ-05). At this size it is not a sign of generator distress. It is unexplained.

### 2.6 Script and data errors vs application errors: cannot be separated

- Failure reasons are not recorded (DQ-10d).
- Before the degradation, failures already run at about 0.2% in every loaded minute, including minute 1 with 100 users: ramp-up 0.197%, minutes 10–18 0.195%, ramp-down 0.199% (`02-evidence.md` A2). A baseline that does not change with load is typical of script or test-data failures, but this run cannot show that.
- In minutes 19–39 the rate rises to about 0.6%, evenly across search, add_to_cart and checkout (0.601%, 0.579%, 0.601%; V2). External calls report 0 errors (E-10).
- The data cannot tell whether the extra failures are client-side timeouts, script failures or server errors.

### 2.7 Steady state: load steady state reached and held; performance regime not stable

- **Load steady state:** reached at minute 9 and held through minute 39. 500 running users and the 2 : 1 : 1 mix are observed in every minute (§2.1, §2.3).
- **Performance regime: three phases, not one steady state:**
  - **Minutes 10–18:** stable. Checkout p95 1.32–1.54 s, TPS 98.7–100.5, error rate 0.17–0.22% (`facts.md`).
  - **Minutes 19–25:** step change at minute 19 (p95 4.96/4.93 s), then responses lengthen and TPS starts to fall.
  - **Minutes 26–39:** TPS levels off at 84.2–88.8, but the app tier is still moving. Active threads rise from 99/106 at minute 26 to 200/200 (the configured max) at minutes 37–39 (V3). The TPS plateau is therefore not an equilibrium, and the run ended before it was clear where it would settle.
- Only **9 consecutive minutes** (10–18) represent the intended conditions with the payment dependency at its earlier latency.

### 2.8 Environment: the decisive limitation

**Payment dependency (E-01, E-10, DQ-10a).** The payment provider is a "third-party payment sandbox (shared test environment; rate limits undocumented)".

- Caller-side latency stepped from avg 258 ms at minute 18 to 2092 ms at minute 19. It stayed at 1809–2123 ms through minute 39, then returned to 263 ms at minute 40 (V2; `01-test-lead-plan.md` command 1).
- **The step did not follow our traffic.**
  - Our checkout volume did not change at onset: 1517 calls at minute 18, 1500 at minute 19 (V2).
  - At the same volumes the sandbox gave both behaviours. Minutes 7–18 had 1200–1525 calls per minute at 230–258 ms. Minutes 26–39 had 1257–1335 calls per minute at 1809–2123 ms (V2).
  - So a simple per-minute rate threshold on our traffic does not explain the onset.
- **Recovery is ambiguous.** It falls in the first ramp-down minute, at 1195 calls (V2). That could be coincidence, or a load-dependent limit with memory, such as a quota window or hysteresis. The data cannot decide (DQ-10a).
- **The latency is measured on the caller side** (E-10, E-11, E-12). No metric covers the app's outbound HTTP client or the network path to the sandbox. "The sandbox itself slowed down" is therefore not established. What is established is that caller-side payment latency rose.
- Two things argue against an app-side origin at onset, without excluding it:
  - At minute 19 app CPU was 52.6%/54.3%, GC pause 101/130 ms and active threads 38/39 of 200 (V3).
  - app1's heap and GC divergence starts at minute 27, after onset (`01-test-lead-plan.md` command 1).

This is the core reason the capacity verdict is out of scope. The behaviour that coincides with the failure belongs to a shared test double that is not production. Its cause is unknown, and it is not shown to be driven by our load. A FAIL attributed to our system's capacity at 500 users would rest on something the run did not demonstrate. A PASS has only 9 clean minutes behind it.

**Other environment factors:**

- **Scheduled inventory-sync batch at 10:30 UTC (minute 30), inside the steady state** (E-01).
  - It is a confounder for minutes 30–33, where the DB shows row lock contention (E-17).
  - At SLA level those minutes look no different from their neighbours: checkout p95 6.48–7.39 s against 6.65–7.64 s in minutes 26–29 and 6.46–7.31 s in minutes 34–37; TPS 84.2–86.9 against 85.1–88.8 and 85.2–85.8 (`facts.md`).
  - Whether the batch ran is unknown (DQ-10b). It starts after onset, so it cannot explain onset (rule 8).
- **app1 heap/GC divergence from minute 27.** Configuration differences between the nodes are unknown (DQ-10f). It is a system-side observation for the specialists. It does not affect workload delivery, and both generators fail SLA-1 alike.
- **Monitoring coverage:** 30/30 steady-state minutes in every source (`02-evidence.md` §3). Gaps that matter for scope: no sandbox-side data, no outbound HTTP client metrics, no error codes, no application logs, and undocumented metric semantics (DQ-07, DQ-10). DB-vs-app ordering at one-minute resolution is unreliable (DQ-06).
- **DQ-01, DQ-02, DQ-03** fall at minute 44, outside the steady state. They have no effect on scope.
- **SYN-RUN-001** is not used (rule 1). The `run_notes` claim of "no application or database changes" is unverified.

## 3. VAL-1

### 3.1 Classification

**VALID WITH LIMITATIONS**: valid for criterion-level health in PERF-A within this run (question part (a)). Not valid for a capacity verdict on our system at 500 users (question part (b)).

### 3.2 Reasons

1. **Workload delivered as designed** (E-04, E-02, E-03, V1, V2):
   - 500/500 users running in every minute 10–39, 0 exits.
   - Mix at 2.000 : 0.995 : 1 in minutes 19–39 and 1.988 : 1.000 : 1 in minutes 10–18.
2. **Harness healthy and the two generators equivalent** (E-05, `facts.md`):
   - LG CPU ≤ 45.9%, memory ≤ 54.0%, log_level "standard" on both.
   - Per-generator TPS, error rate (0.465% vs 0.469%) and SLA-1 outcome match minute by minute.
3. **The throughput shortfall is a system finding** (§2.2):
   - Implied cycle rises from about 20 s to 22.3–24.0 s while users are present and generators are not saturated.
   - Iterations ran late because responses were slow, consistent with response-time sums crossing the 20 s pacing.
4. **Evidence coverage complete in steady state** (`02-evidence.md` §3): 30/30 minutes for every source and entity.
5. **The failure coincides with a shared-sandbox latency step not driven by our load** (E-10, V2):
   - Calls were 1517 → 1500 at onset.
   - Latency was 230–258 ms at 1200–1525 calls per minute before onset, and 1809–2123 ms at 1257–1335 calls per minute after.
   - Rate limits are undocumented, and there is no provider-side evidence (DQ-10a).
   - The run therefore cannot attribute the onset to the 500-user load on our system. It also cannot say whether production would see it.
6. **Only 9 clean steady-state minutes** (10–18) out of 30 declared (`facts.md`). That is too short to support a steady-state PASS.
7. **Error accounting is undocumented** (DQ-04, DQ-05, DQ-10d):
   - abort_on_error does not behave as declared.
   - Failure causes are unrecorded, including client timeouts versus server errors.
   - This limits the confidence of SLA-3, not its direction: the worst steady-state minute is 0.67% against a 1% threshold (`facts.md`).

### 3.3 Allowed claims

| # | Claim the team may make | Evidence | Confidence |
| --- | --- | --- | --- |
| AC-1 | The intended workload (500 users, 2 : 1 : 1 mix, fixed 20 s pacing) was delivered for all of minutes 10–39 on both generators, with no early exits | E-04, E-02, E-03, E-05; V1, V2 | High: complete per-minute coverage, both generators agree |
| AC-2 | **SLA-1: FAIL in this run, PERF-A.** Checkout p95 met ≤ 2.0 s in every minute 10–18 on both generators (1.32–1.54 s) and failed in every minute 19–39 on both generators (4.76–7.64 s). Must be stated per minute and per generator, with no run-level p95 (rule 5) | E-14, E-15, `facts.md` | High for the measured outcome |
| AC-3 | **SLA-2: FAIL in this run, PERF-A**, minutes 26–39 (84.2–88.8 TPS). The cause is late iterations from slow responses, not missing users or harness saturation | `facts.md`; E-04, E-05; §2.2 | High that it is not a harness artefact. The four-think-times pacing model is an assumption |
| AC-4 | **SLA-3: PASS in this run, as counted by the load tool.** 0.47% over minutes 10–39 (per-minute max 0.67%), with the stated limitation that failure definitions and abort_on_error semantics are undocumented | `facts.md`, E-02, E-03, DQ-04 | Medium: counts are complete, but what counts as a failure is undocumented |
| AC-5 | In PERF-A, while caller-side payment latency was about 1.8–2.1 s avg, checkout at 500 users did not meet SLA-1, and from minute 26 not SLA-2. While it was about 230–258 ms (minutes 10–18), all three criteria were met. This is an Observed Fact pairing over aligned windows, at most a Correlation. Any mechanism (for example a connection held across the payment call) is for the specialists to grade | E-10, E-14, E-15, `facts.md` | High for the co-occurrence; it does not imply cause |
| AC-6 | The system's behaviour **under a dependency-latency excursion** at 500 users is a legitimate subject for analysis from this run (pool, threads, DB sessions, traces in minutes 19–39) | E-06, E-07, E-08, E-11, E-12 | Scope statement |
| AC-7 | During the run, the generators and harness did not distort the load or the timing measurements in any way the data can detect | E-05; §2.4–2.5 | Medium: generator health is well covered, but timeout and failure semantics are not documented |

### 3.4 Restricted claims

| # | The team must not claim | Why |
| --- | --- | --- |
| RC-1 | "The system **cannot** support 500 users" or "500 users exceeds capacity" | Our load did not change at onset (minute 19; checkouts 1517 → 1500). The coincident change is in a shared sandbox that is not production, and its cause is unknown (E-10, DQ-10a). The run does not show that load caused the degradation |
| RC-2 | "The system **can** support 500 users" or a steady-state PASS | Only 9 clean minutes (10–18) against a declared 30. SLA-1 failed for 21 of 30 minutes |
| RC-3 | "The payment sandbox slowed down / throttled us / caused the failure" as an established fact or root cause | Latency is caller-side only. There are no sandbox-side metrics and no outbound HTTP client metrics. Zero errors in E-10 is not evidence of no throttling (DQ-10a, rule 9). The claim allowed is "caller-side payment latency rose" |
| RC-4 | "The sandbox slowdown was / was not caused by our load" | The same call volumes gave both latency regimes. Recovery coincides with the start of ramp-down. The data supports neither direction (V2) |
| RC-5 | Any run-level or cross-generator checkout p95, or an averaged payment p95 | Rule 5; E-02, E-03, E-10 limitations |
| RC-6 | The 84–89 TPS level of minutes 26–39 as a stable or sustainable capacity figure | App threads were still rising to the 200 max at minutes 37–39 (V3). The regime had not settled when the steady state ended |
| RC-7 | Any statement about what the failed transactions were (timeouts, script/data, server errors), or that the 0.2% baseline failure rate is "application errors" | Failure reasons are not recorded (DQ-10d). abort_on_error and script_errors are undocumented (DQ-04, DQ-05) |
| RC-8 | "The inventory-sync batch did / did not affect the result" beyond the SLA-level observation that minutes 30–33 look like their neighbours | Whether the batch ran is unknown (DQ-10b). The DB has no query or lock-holder data (DQ-10c) |
| RC-9 | Any one-minute lead or lag between DB and app-tier signals | DQ-06 |
| RC-10 | Any comparison with or carry-over from SYN-RUN-001, including "the LG2 fix worked" beyond "both generators ran at standard log level in this run" | Rule 1; no SYN-RUN-001 data in this run |

### 3.5 Unknowns that could change the decision

| # | Unknown | What it would change |
| --- | --- | --- |
| U-1 | Sandbox-side records for 10:19–10:40 UTC: latency, throttling, rate-limit hits, other tenants, incidents (DQ-10a) | **External incident or other tenant:** minutes 19–39 become a dependency-degradation episode. The capacity question stays unanswered and needs a rerun. **Throttling triggered by our traffic** (for example a cumulative quota): the question becomes whether the production provider has comparable limits at production volumes, and the run says nothing about production limits |
| U-2 | Outbound HTTP client and connection metrics for the payment call inside the app | **The caller-side latency was produced inside our app** (for example outbound connection-pool queueing): the onset is a system finding under our own load. That would move part (b) toward **VALID** with a capacity FAIL. **Pure sandbox time:** RC-1 stands |
| U-3 | What abort_on_error does in this tool; client timeout values; whether failed requests are included in avg_s/p95_s | **Failures are hidden or truncated in some way:** SLA-3 confidence drops, and the response-time series would need re-examination. It cannot reverse SLA-1 (smallest failing margin 2.76 s) |
| U-4 | Error codes and messages for the 871 failures | Would separate script/data failures from application errors (RC-7), and would tell whether the 0.6% in minutes 19–39 includes client timeouts |
| U-5 | Whether inventory-sync ran, and against which tables | Would let the team scope minutes 30–33 cleanly (RC-8) |
| U-6 | app1 vs app2 configuration (JVM, heap, GC) | **A configuration difference exists:** the environment was asymmetric. Not workload-affecting, but relevant to the rerun environment |

### 3.6 Test-integrity issues to fix before a rerun

Each item names an owner, the change, how success is measured and what would show it has failed (rule 12).

- **T-1. Control the payment dependency.**
  - **Owner:** Test Lead with the environment owner.
  - **Change:** for the capacity question, replace the shared sandbox with a service-virtualisation stub at a fixed, declared latency (for example 250 ms, matching minutes 10–18).
  - **Separate test:** run a stepped latency-injection test (for example 250 ms → 1 s → 2 s at 500 users) to measure how much dependency latency the system tolerates.
  - **Success:** caller-side payment avg stays within a declared tolerance of the stub setting in every steady-state minute, and the stub's own logs confirm the latency it served.
  - **Failure sign:** caller-side latency rises above the stub's served latency. That would show the latency is produced inside our app, so U-2 would resolve toward a system finding.
- **T-2. Document and fix error handling in the harness.**
  - **Owner:** harness owner.
  - **Change:** document what abort_on_error does. Set it to the intended behaviour (for a capacity test usually: log the failure, end the iteration, keep the user). Record an error code or message per failure, and declare client timeouts.
  - **Success:** vusers.exited_with_error, transaction failures and script_errors reconcile, and every failure has a reason.
  - **Failure sign:** failures without a reason, or exits that do not match the setting.
- **T-3. Keep scheduled jobs out of the steady state, or record them.**
  - **Owner:** data team with the Test Lead.
  - **Change:** schedule the test away from inventory-sync at 10:30 UTC. If it must overlap, capture the batch start and end log.
  - **Success:** no unexplained "row lock contention" episodes in the steady state, or a batch log that brackets them.
- **T-4. Add the missing instrumentation.**
  - **Owner:** APM/platform owner.
  - **Change:** add outbound HTTP client pool metrics for the payment call, and document whether each APM and DB metric is point-in-time, mean or max (DQ-07). Make trace sampling random and balanced across nodes (DQ-08). Export a run ID with every file (DQ-09).
  - **Success:** each of these is present and documented in the rerun's evidence register.
- **T-5. Declare where think time is applied** in the scenario definition, so that the pacing model in §2.2 can be checked rather than assumed. **Owner:** test designer.
- **T-6. Keep the steady state long enough to settle.**
  - **Owner:** Test Lead.
  - **Change:** if a degradation occurs in the rerun, the 30-minute steady state should show whether threads and pool reach an equilibrium. In this run threads were still climbing at minute 37 (V3).
  - **Change:** consider extending the steady state if the regime is still moving at its end.

## Handoff

- **To the Performance Analyst and specialists.** Scope is VAL-1 VALID WITH LIMITATIONS.
  - You may analyse minutes 19–39 as **system behaviour under a caller-side payment-latency excursion at 500 users** (AC-5, AC-6).
  - Do not frame any finding as a capacity limit of our system at 500 users (RC-1, RC-2), and do not assert that the sandbox caused or throttled anything (RC-3, RC-4).
  - The most valuable open evidence question for scope is U-2: whether any app-side signal can show that payment latency arose inside our app at onset. If the data cannot show it, say so.
- **To the Test Lead (Call 2).**
  - **Health verdicts you may issue for this run in PERF-A:** SLA-1 FAIL (minutes 19–39, both generators, per-minute statement), SLA-2 FAIL (minutes 26–39), SLA-3 PASS with Medium confidence and the error-accounting limitation.
  - **Capacity verdict:** defer it, with no PASS and no FAIL, pending U-1/U-2 and a rerun under T-1.
  - **SLA-2:** it is not a harness artefact. Answer to your question 3: it is a system-side finding.
  - **abort_on_error (your question (d)):** the data shows it removed no users and did not cut iterations short (mix 2.000 : 0.995 : 1 in minutes 19–39). What it actually does remains unknown (T-2).
- **To the Devil's Advocate.** Points worth challenging:
  - Whether the payment dependency counts as "the system" for the question as asked. I treated it as part of the checkout journey for SLA verdicts (AC-2, AC-3) but not for the capacity verdict (RC-1).
  - The four-think-times pacing model in §2.2. It is an assumption that is consistent with the data; it has not been verified.
- **Open questions:** U-1 to U-6.

## Appendix: commands run

Scripts are in `/tmp/val/`, outside `data/`. They were run with `python3 -I` against `examples/02-connection-pool/data`.

**V1. Per-generator users, mix, pacing and generator health by minute (minutes 8–43)** (`/tmp/val/v1.py`)

```python
T[(m,g)][txn] = row  from transactions.csv;  V[(m,g)] from vusers.csv;  L[(m,g)] from load_generators.csv
for m in 8..43, g in LG1,LG2:
  s,a,c = counts of search, add_to_cart, checkout
  ips = c/60 ; cycle = running_vusers/ips
  resp = 2*avg_s(search) + avg_s(add_to_cart) + avg_s(checkout) ; model = resp + 4*3
  print sched, running, exited, s, a, c, s/c, a/c, ips, cycle, resp, model, failed, lg cpu, script_errors
```

Key outputs:
- **Users:** scheduled = running = 250 per generator in minutes 9–39, exited 0.
- **Implied cycle, LG1 / LG2:**
  - Minutes 10–18: 19.5–20.4 s / 19.6–20.4 s.
  - Minutes 19–23: 19.6–20.5 s / 19.5–20.5 s.
  - Minutes 24–25: 21.0, 21.7 s / 20.2, 22.0 s.
  - Minutes 26–39: 22.3–23.8 s / 22.7–24.0 s.
  - Minutes 40–43: 19.7–20.6 s / 19.5–20.3 s.
- **Model (response sum + 12 s):**
  - Minutes 10–18: 14.37–14.52 s. Minute 19: 17.71/17.66 s.
  - Minute 23: 20.06/19.88 s. Minute 24: 20.91/20.73 s.
  - Minute 26: 22.54/22.49 s against cycle 22.3/22.7 s.
  - Minute 30: 23.83/23.82 s against cycle 23.8/24.0 s.
- **Mix:** per-generator per-minute s/c 1.93–2.09, a/c 0.95–1.04.
- **Generators:** LG CPU 42.1–45.9% in minutes 10–39. script_errors 0–2 only in minutes 19–39.

**V2. Window mix, failure rate by transaction, payment latency against call volume** (`/tmp/val/v2.py`)

```python
aggregate counts and failed per transaction over windows 0-9, 10-18, 19-39, 40-43
print search/checkout, add_to_cart/checkout, failed% per transaction
print external_calls rows for selected minutes; ranges of calls and avg_ms for minutes 26-39;
rows in minutes 0-18 with calls >= 1195 and their max avg_ms
```

Output:

| Window | search/checkout | add_to_cart/checkout | Failed %: search / add_to_cart / checkout |
| --- | --- | --- | --- |
| 0–9 | 1.9992 | 0.9993 | 0.206 / 0.170 / 0.206 |
| 10–18 | 1.9877 | 0.9998 | 0.194 / 0.215 / 0.178 |
| 19–39 | 2.0000 | 0.9953 | 0.601 / 0.579 / 0.601 |
| 40–43 | 2.0325 | 0.9993 | 0.198 / 0.201 / 0.201 |

Payment-sandbox, calls / avg_ms by minute:

| Minutes | Calls / avg_ms |
| --- | --- |
| 7–9 | 7: 1200 / 230; 8: 1352 / 245; 9: 1475 / 244 |
| 17–20 | 17: 1473 / 249; 18: 1517 / 258; 19: 1500 / 2092; 20: 1504 / 2093 |
| 26, 30, 39 | 26: 1335 / 1963; 30: 1257 / 2007; 39: 1269 / 1955 |
| 40–43 | 40: 1195 / 263; 41: 881 / 275; 42: 612 / 271; 43: 296 / 248 |

- Minutes 26–39: calls 1257–1335, avg_ms 1809–2123.
- Minutes 0–18 with calls ≥ 1195: max avg_ms 258.
- Errors: 0 in every minute.

**V3. App node state at transition minutes**

```bash
cd examples/02-connection-pool/data && python3 -I -c "
import csv
for r in csv.DictReader(open('app_servers.csv')):
    m=int(r['elapsed_min'])
    if m in (18,19,20,25,26,36,37,39,40): print(m,r['node'],'cpu',r['cpu_pct'],'thr',r['active_threads'],'pool',r['db_pool_active'],'wait',r['db_pool_wait_ms'],'gc',r['gc_pause_ms'],'heap',r['heap_used_pct'])
"
```

Key outputs (app1 / app2):

| Minute | CPU % | Threads | Pool active | Pool wait (ms) | GC (ms) | Heap % |
| --- | --- | --- | --- | --- | --- | --- |
| 18 | 54.7 / 53.4 | 26 / 23 | 7 / 7 | 0 / 2 | — | — |
| 19 | 52.6 / 54.3 | 38 / 39 | 17 / 17 | 337 / 362 | 101 / 130 | — |
| 26 | — | 99 / 106 | — | — | — | — |
| 36 | — | 191 / 194 | — | — | — | — |
| 37 | — | 200 / 200 | — | — | 747 / 86 | 84.2 / 56.2 |
| 39 | — | 200 / 200 | — | — | — | — |
| 40 | — | 21 / 21 | 7 / 5 | 0 / 2 | — | — |

A dash means the value is not used in this file.
