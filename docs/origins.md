# Origins

Performance Evidence Lab comes from 17 years of performance testing, including hiring, training and leading a performance test team of nearly 20 performance testers.

The first written version of that analysis practice was a single long AI prompt for analyzing load test results ("V2"). It introduced test run isolation, data inventory before analysis, a required load profile check, time normalization, phase-aware correlation, root-cause levels and a final report check. This project keeps those steps and assigns each one to an agent, so every step has an owner and can be checked. The original V2 document was inspected in full on 2026-11-08, and [V2 traceability](v2-traceability.md) maps each of its 14 requirements to the current workflow.

The agent architecture follows a sibling project, [Hive & Seek](https://github.com/craiglabrie-lab/hive-and-seek), which applies the same pattern (specialist agents, a shared data inventory, a reviewer agent and recorded decisions) to job searching.

Product names mentioned in this repository are for context only and do not imply endorsement. No vendor material is included.
