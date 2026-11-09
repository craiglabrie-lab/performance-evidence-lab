# Glossary

| Term | Meaning |
| --- | --- |
| Abort on error | A load-tool setting that stops a virtual user's iteration (or the user) when an error occurs. Lost users reduce the load actually applied. |
| Acceptance criteria | The thresholds the test is judged against, for example checkout p95 ≤ 2.0 s. Identified as SLA-1, SLA-2… |
| Connection pool | A fixed set of database connections an application node shares. When all are in use, requests wait. |
| Evidence grade | How far the evidence goes toward a cause: Observed Fact, Correlation, Probable Contributor, Confirmed Root Cause. |
| Fact sheet | `facts.md`, produced by `tools/analyze.py`: the computed numbers every agent works from. |
| Implied cycle time | Running users ÷ iterations per second (Little's Law). With fixed pacing it should equal the pacing interval; a larger value means iterations are running late. |
| Load generator | A machine that runs virtual users. If it runs out of CPU, it delays its own requests and measurements. |
| p95 | The response time 95% of requests were faster than. Percentiles cannot be averaged. |
| Pacing | How often each virtual user starts an iteration. Fixed pacing of 20 s means one iteration every 20 s per user. |
| Steady state | The part of the test where the intended load is held constant. Must be confirmed from data, not assumed from the schedule. |
| Symptom window | A time range the Performance Analyst hands to specialists, for example minutes 19–39. |
| TPS | Transactions per second. |
| Validity | Whether the run can answer the question asked: VALID, VALID WITH LIMITATIONS, or INVALID FOR THIS QUESTION. |
| Virtual user (Vuser) | A simulated user running the test script. |
