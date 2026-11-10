# Templates

| Template | Use |
| --- | --- |
| [scenario.json](scenario.json) | Describe a test run so the deterministic tooling and the agents can analyze it. Copy it into `<your-folder>/data/` and fill it in. |
| [go-no-go.md](go-no-go.md) | The structure of the go/no-go recommendation, for analysis done by hand. |
| [recommendation.md](recommendation.md) | One recommendation, with type, owner, success metric and the result that would show the hypothesis is wrong. |

`tools/analyze.py` currently expects the same file layout as the examples: `transactions.csv`, `vusers.csv`, `load_generators.csv`, `app_servers.csv`, `database.csv` and `network.csv`, plus optional logs, outbound calls and APM traces. Real tool exports need a small adapter to that layout.
