# Evaluation

| File | Contents |
| --- | --- |
| [expected-findings.md](expected-findings.md) | The answer key for both synthetic test runs, written before any agent run |
| [expected-findings.sha256](expected-findings.sha256) | The answer key's hash, committed before the runs so the key cannot be changed to match the results |

**Status:** the recorded agent runs, the single-prompt baseline and the scored results are the next stage of the [roadmap](../docs/product/roadmap.md). An earlier version of the agents was run and scored against both test runs; those results are in the repository's git history and will be replaced by runs of the current agents.

Each test run will be analyzed twice, on the same model with the same computed results summary:

1. by the nine-agent workflow;
2. by a single AI assistant asked to analyze the results as an experienced performance engineer, without the workflow or role files.

Both are scored against the answer key for expected findings, misleading signals avoided, root-cause status and SLA results, along with tokens, time and the length of the test summary.

The tests in [`tests/`](../tests/test_analyze.py) cover the deterministic tooling, not the agents.
