# Glossary

| Term | Meaning |
| --- | --- |
| Abort on error | A runtime setting that stops a Vuser's iteration, or the Vuser itself, when an error occurs. Vusers lost this way reduce the load actually applied. |
| Computed results summary | `facts.md` and `facts.json`, produced by `tools/analyze.py`: the calculated numbers every agent works from. |
| Connection pool | A fixed set of database connections shared by an application node. When every connection is in use, requests wait. |
| Degradation window | A time range the Performance Analyst hands to the engineers, for example minutes 19–39. |
| Go/no-go recommendation | The Performance Test Lead's recommendation on whether the results support release, with the retest or tuning plan. |
| Implied cycle time | Running Vusers ÷ iterations per second (Little's Law). With fixed pacing it should equal the pacing interval. A larger value means iterations are running late. |
| Load generator | A machine that runs Vusers. A saturated load generator adds its own delay to response times and can drop Vusers. |
| Load profile | The number of Vusers, ramp-up, steady state and ramp-down a test is designed to apply. |
| p95 | The response time that 95% of requests were faster than. Percentiles cannot be averaged. |
| Pacing | How often each Vuser starts an iteration. Fixed pacing of 20 s means one iteration every 20 s per Vuser. |
| Root-cause status | How far the bottleneck analysis has gone: symptom, correlated metric, suspected bottleneck, or confirmed root cause. |
| SLA | Service level agreement: a measurable target the test is judged against, such as checkout p95 ≤ 2.0 s. |
| Steady state | The part of the test where the planned load is held constant. Confirmed from the data, not assumed from the schedule. |
| Test validity | Whether the test run can answer its test objective: Valid, Valid with limitations, or Invalid. |
| TPS | Transactions per second. |
| Vuser | Virtual user: a simulated user running the test script. |
| Workload model | The planned transaction mix, pacing, think time and Vuser count. |
