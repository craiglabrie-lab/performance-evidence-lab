# Records

Agents connect their work through short IDs. Any reader can follow a conclusion back to the measurement it rests on.

| Prefix | Record | Created by | Example |
| --- | --- | --- | --- |
| E- | Evidence item: a file, or a specific slice of one | Results Librarian | E-04 `load_generators.csv`, LG2, minutes 16–39 |
| DQ- | Data-quality issue | Results Librarian | DQ-01 app2 metrics missing for minutes 26–28 |
| VAL- | Validity decision | Test Validity Reviewer | VAL-1 INVALID FOR THIS QUESTION |
| OBS- | Observation: a measured statement with a window | Performance Analyst, specialists | OBS-03 LG2 checkout p95 5.6 s at minute 16 |
| SW- | Symptom window handed to specialists | Performance Analyst | SW-1 minutes 16–39 |
| HYP- | Hypothesis: a proposed mechanism with grade and confidence | Specialists | HYP-APP-1 connection held across payment call |
| CRIT- | Objection | Devil's Advocate | CRIT-2 database ruled out without query-level evidence |
| F- | Finding: an accepted conclusion | Test Lead | F-1 LG2 saturation distorted the workload |
| REC- | Recommendation | Test Lead | REC-1 set LG2 log level to standard and rerun |
| DEC- | Decision record | Test Lead | DEC-1 defer the capacity verdict |

## What each claim carries

- **Claim** in one sentence.
- **Window** (elapsed minutes) and scope (generator, node, transaction).
- **Evidence** as E-, OBS- or DQ- IDs.
- **Grade and confidence**, for anything beyond an Observed Fact.
- **Alternatives** considered, and why they were kept or set aside.

## Handoff files

Each agent writes one Markdown file into the run folder, numbered in the order they ran. Every file starts with a header block:

```
Agent: <role>
Run: <run id>
Read: <files this agent was given>
Execution: separate agent context, model <name/version>
```

and ends with a **Handoff** section: what the next agent needs to know, and any open questions.
