# Four judgments that stay separate

A performance review answers four different questions. Mixing them is the most common way a report goes wrong: a confident root cause from a test that never reached its load, or a "PASS" for a period with no data.

| Judgment | Values | Answers |
| --- | --- | --- |
| Test validity | VALID · VALID WITH LIMITATIONS · INVALID FOR THIS QUESTION | Can this run answer the question we asked? |
| Performance health | PASS · FAIL · NOT ASSESSED, per acceptance criterion | Did the system meet its criteria, within the scope the run supports? |
| Evidence grade | Observed Fact · Correlation · Probable Contributor · Confirmed Root Cause | How far does the evidence go toward a cause? |
| Confidence | High · Medium · Low, with a one-line reason | How sure are we of this specific claim? |

## Test validity

Judge validity for the question asked, not for the run in general. The same run can support "these errors occurred" and fail to support "the system handles 500 users".

- **VALID** — the achieved workload, harness health and evidence coverage support the question.
- **VALID WITH LIMITATIONS** — the question can be answered within a stated scope. List what is allowed and what is not.
- **INVALID FOR THIS QUESTION** — the run cannot answer it. Report trustworthy observations and test-integrity findings, and plan the rerun.

Missing decisive evidence never defaults to VALID. A system that slows down under load is not a harness failure: if the generators were healthy and the users were running, a throughput drop caused by slow responses is a finding about the system.

## Performance health

Health needs a declared criterion, a scope and evidence. Use NOT ASSESSED when any of them is missing, or when validity does not support the scope. Missing data is never PASS.

## Evidence grade

| Grade | What it takes |
| --- | --- |
| Observed Fact | A measurement or record you can point to exactly |
| Correlation | Two independent signals move together in aligned, covered windows |
| Probable Contributor | A plausible mechanism, supported by converging evidence; alternatives addressed and gaps disclosed |
| Confirmed Root Cause | The mechanism is demonstrated: a controlled change reproduces or removes the symptom, or equivalent causal evidence |

Agreement between agents, a stronger model or a well-written argument never raises a grade. Only new evidence does.

## Confidence

Confidence applies to one precise claim and comes with a reason based on source reliability, coverage, alignment and remaining alternatives. It is not a probability. A high-confidence correlation is still a correlation.
