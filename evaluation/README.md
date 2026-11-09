# Evaluation

| File | What it is |
| --- | --- |
| [expected-findings.md](expected-findings.md) | The answer key, written before any agent ran |
| [expected-findings.sha256](expected-findings.sha256) | Its hash, committed before the runs so the key cannot have been edited afterwards |
| [results.md](results.md) | How the team and a single prompt scored, what each cost, and what the comparison does and does not show |

The tests in [`tests/`](../tests/test_analyze.py) check the deterministic tool, not the agents. Agent behaviour is evidenced by the recorded runs in [`examples/`](../examples/README.md).
