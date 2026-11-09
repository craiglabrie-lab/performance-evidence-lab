# ADR-0003 — Arithmetic is done by code

**Decision:** A deterministic script, [`tools/analyze.py`](../../tools/analyze.py), produces a fact sheet before any agent runs. Agents state numbers only from the fact sheet, the raw files, or a calculation they ran and showed.

**Why:** Language models are fluent with numbers and unreliable at arithmetic. A review is only as good as its numbers. Code also enforces rules that are easy to forget: time zones are normalised, gaps are listed rather than filled, and percentiles are never averaged.

**Consequences:** The fact sheet is shared by every agent and by the single-prompt baseline, so comparisons isolate the effect of the team rather than of the tooling. The tool is standard-library Python with tests.

**Revisit when:** a new data source needs metrics the tool does not compute.
