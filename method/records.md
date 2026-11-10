# Records

Agents link their work through short record IDs, so every finding in the test summary can be traced to the data it is based on.

| Prefix | Record | Created by | Example |
| --- | --- | --- | --- |
| DATA- | Data inventory item: a file, or a slice of one | Results & Monitoring Analyst | DATA-04 `load_generators.csv`, LG2, minutes 16–39 |
| GAP- | Data or monitoring gap | Results & Monitoring Analyst | GAP-01 app2 metrics missing for minutes 26–28 |
| VAL- | Test validity result | Test Execution Analyst | VAL-1 Invalid: load profile not achieved |
| OBS- | Observation: a measured result with its time window | Results Analyst, engineers | OBS-03 LG2 checkout p95 5.6 s at minute 16 |
| DW- | Degradation window handed to the engineers | Results Analyst | DW-1 minutes 19–39, all transactions |
| HYP- | Bottleneck hypothesis with root-cause status and confidence | Engineers | HYP-APP-1 DB connection held during the payment call |
| RC- | Review comment | Peer Reviewer | RC-2 database eliminated without query-level metrics |
| F- | Finding | Performance Test Lead | F-1 LG2 saturation distorted the load profile |
| REC- | Recommendation | Performance Test Lead | REC-1 set LG2 logging to standard and retest |
| GNG- | Go/no-go recommendation | Performance Test Lead | GNG-1 no capacity sign-off; retest after harness fix |

## What every finding includes

- **The finding** in one sentence.
- **Time window** (elapsed minutes) and where it applies: load generator, node, transaction.
- **Record IDs** for the data: DATA-, OBS-, GAP-.
- **Root-cause status and confidence**, for anything beyond a measured symptom.
- **Alternatives** considered, and why each was eliminated or kept open.

## Handoff files

Each agent writes one Markdown file into the run folder, numbered in the order the agents ran. Every file starts with this header:

```
Agent: <role>
Run: <run id>
Inputs: <files this agent was given>
Execution: sub-agent with its own context, model <name/version>
```

Every file ends with a **Handoff** section: what the next agent needs to know, and any open questions.
