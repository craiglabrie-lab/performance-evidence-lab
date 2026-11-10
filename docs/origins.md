# Origins

Performance Evidence Lab comes from 17 years of performance testing, most recently leading a performance testing team where every test scenario, result set and analysis was reviewed before it reached a release decision.

The first written version of that analysis practice was a single long AI prompt for analyzing load test results ("V2"). It introduced test run isolation, data inventory before analysis, a required load profile check, time normalization, phase-aware correlation, root-cause levels and a final report check. This project keeps those steps and assigns each one to an agent, so every step has an owner and can be checked.

The agent architecture follows a sibling project, [Hive & Seek](https://github.com/craiglabrie-lab/hive-and-seek), which applies the same pattern (specialist agents, a shared data inventory, a reviewer agent and recorded decisions) to job searching.

Product names mentioned in this repository are for context only and do not imply endorsement. No vendor material is included.
