# Results: the team against a single prompt

Both scenarios were reviewed twice on 2026-11-09, on the same model (Claude Opus 5.5) and with the same inputs (the data folder and the computed fact sheet):

- **Team:** the nine-agent review, following [the method](../method/README.md).
- **Single prompt:** one agent told to act as an experienced performance engineer and write a report with verdict, root cause and recommendations. It was not given the method or the role files.

Both were scored against the [expected findings](expected-findings.md), which were written before either ran. The file's SHA-256 (`1ed6eab8…5bda`) was committed before the runs, in [`expected-findings.sha256`](expected-findings.sha256). Scoring was done by the project's assistant, not by an independent reviewer.

## Headline

**Both approaches found almost everything, and neither fell into a trap.** On these two clear-cut scenarios, a single strong model with a good fact sheet is a serious reviewer. The team did not find more of the answer key. Where it differed was in **how far its claims went**: it kept the four judgments apart, graded causes conservatively, surfaced ambiguities the single prompt glossed over, and left a traceable record of every step. It cost about **16 times as many tokens**.

That is a narrower result than "multi-agent beats single prompt", and it is the honest one.

## Scenario 01 — generator saturation

| Expected finding | Team | Single prompt |
| --- | --- | --- |
| S1-1 Invalid for the 500-user question | ✅ INVALID FOR THIS QUESTION; all criteria NOT ASSESSED | ✅ "INVALID as a test of the application", but headline verdict "FAIL as recorded" |
| S1-2 Problem is on LG2 only | ✅ F-2 | ✅ |
| S1-3 LG2 CPU asymmetry | ✅ | ✅ |
| S1-4 Extended logging is the probable contributor | ◐ Named as the only configuration difference and leading candidate, but graded **Correlation, Low** | ✅ Stated as the cause, "confidence high", in a causal chain |
| S1-5 Abort-on-error removed users | ✅ F-1 | ✅ |
| S1-6 Application tier healthy | ✅ F-3, F-8 | ✅ |
| S1-7 Batch lock spike is not the cause | ✅ F-7, graded Correlation | ✅, but called a "real, reproducible" degradation with "high" confidence in its cause |
| S1-8 app2 monitoring gap disclosed | ✅ | ✅ |
| S1-9 Injected instruction treated as data | ✅ F-9 | ✅ |
| S1-10 Fix logging, generator headroom, abort setting, rerun | ✅ plus a calibration experiment to prove the cause | ✅ |
| Traps avoided | 5 / 5 | 5 / 5 |

**Where the team was more cautious than the answer key.** It refused to call extended logging more than a correlation, for two reasons it stated: the network path from LG2 was never measured, and LG2's timings stayed inflated after its CPU fell to 49–71% during ramp-down. The second point is a genuine inconsistency in the synthetic data (the generator holds LG2's timing inflation constant while its CPU falls). The team caught a flaw in the scenario; the single prompt did not. Whether "Correlation, Low" is too cautious is a fair debate, and the team's report says what experiment would settle it.

## Scenario 02 — connection pool

| Expected finding | Team | Single prompt |
| --- | --- | --- |
| S2-1 Valid (or valid with limitations); throughput drop is a system symptom | ✅ VALID WITH LIMITATIONS | ✅ Generators ruled out; no formal validity call |
| S2-2 Payment sandbox is a limitation | ✅ Capacity verdict withheld because of it | ✅ Recommends a stub |
| S2-3 SLA-1 FAIL, SLA-2 FAIL, SLA-3 PASS | ✅, and flagged that SLA-2 **passes** (93.0 TPS) if read as a window mean | ✅ |
| S2-4 Pools saturate | ✅ | ✅ |
| S2-5 Connection held during the payment call | ✅ F-5, F-6 | ✅ |
| S2-6 Database not slow | ✅ F-9, as a bounded negative | ✅ |
| S2-7 app1 GC rise is secondary | ✅ | ✅ |
| S2-8 Batch lock spike minor | ✅, batch link left ungraded | ✅ |
| S2-9 Probable Contributor, not Confirmed | ✅ | ◐ No grade; called "the real application defect", high confidence |
| S2-10 Release the connection, timeout or breaker, stub, not a bigger pool | ✅ | ✅ |
| Traps avoided | 5 / 5 | 5 / 5 |

**Beyond the answer key.** Both noticed that payment latency alone breaks the checkout target, so fixing the connection handling would not make SLA-1 pass on its own. The answer key had missed this. Only the team flagged that SLA-2's verdict depends on an undeclared reading of the criterion, that "not driven by our load" was an unsupported negative claim, and that the load-generator memory metric is a formula of the user count rather than a measurement (another flaw in the synthetic data).

## Cost

| | Team (scenario 01) | Team (scenario 02) | Single prompt (each) |
| --- | --- | --- | --- |
| Agent calls | 11 | 11 | 1 |
| Tokens | 1.66 M | 1.77 M (+0.16 M aborted) | 0.10–0.11 M |
| Agent time, summed | 44 min | 44 min | 2 min |
| Wall-clock, with parallel steps | about 33 min | about 33 min | 2 min |
| Handoff and report text | about 2,700 lines | about 3,100 lines | about 130–150 lines |

## What this does and does not show

**Shows**
- The method works end to end as a team, with real handoffs, real objections and a decision that responds to them. Every objection in both runs was ruled on and most changed a finding.
- The deterministic fact sheet carries much of the load. Both approaches used it, and neither made an arithmetic error that changed a conclusion.
- The team's distinctive value is **calibration and auditability**: separate validity and health verdicts, graded claims, visible dissent, and a record a reviewer can check line by line.

**Does not show**
- That the team finds causes a single prompt would miss. On these scenarios it did not.
- Real-world accuracy. The scenarios are synthetic and were designed by the same author as the role checklists.
- Repeatability. Each approach ran once per scenario.
- That the extra cost is worth it in general. That depends on the stakes of the decision and on harder cases.

## Next experiments

1. Harder scenarios: no clear cause, conflicting signals, a valid run that passes, missing monitoring for the guilty layer.
2. Several runs of each approach per scenario, to measure variation.
3. A middle option: the single prompt given the method and the portable prompt, to separate the effect of the method from the effect of the team.
4. Cheaper models for routine seats (Librarian, Report Writer) and a different model for the Devil's Advocate.
5. Fix the two synthetic-data flaws the team found, and record the change.
