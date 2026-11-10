# ADR-0003: Calculations are done by deterministic tooling

**Decision:** [`tools/analyze.py`](../../tools/analyze.py) produces a computed results summary before any agent runs. Agents use numbers only from that summary, the raw data files, or a calculation they ran and showed.

**Why:** Language models write fluently about numbers and are unreliable at arithmetic. An analysis is only as good as its numbers. Code also enforces rules that are easy to forget: convert time zones to UTC, list monitoring gaps instead of filling them, and never average percentiles.

**Consequences:** Every agent and the single-prompt baseline work from the same computed results summary, so a comparison measures the agent workflow, not the tooling. The tool uses only the Python standard library and has tests.

**Revisit when:** a new data source needs metrics the tool does not calculate.
