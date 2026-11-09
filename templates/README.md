# Templates

| Template | Use |
| --- | --- |
| [scenario.json](scenario.json) | Describe a run so the fact-sheet tool and the agents can review it. Copy into `<your-folder>/data/` and fill in. |
| [decision-record.md](decision-record.md) | The shape of the Test Lead's decision, for reviews done by hand. |
| [recommendation.md](recommendation.md) | One recommendation, with owner, success measure and the result that would prove it wrong. |

The fact-sheet tool currently expects the same file layout as the examples: `transactions.csv`, `vusers.csv`, `load_generators.csv`, `app_servers.csv`, `database.csv`, `network.csv`, plus optional logs, external calls and traces. Real exports need a small adapter into that layout.
