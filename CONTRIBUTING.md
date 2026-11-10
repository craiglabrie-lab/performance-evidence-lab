# Contributing

Issues and pull requests are welcome. Follow the [style guide](docs/style-guide.md).

- **New synthetic test runs** are the most useful contribution: a clear test objective, a realistic bottleneck, one or two misleading signals, and an answer key written before any analysis runs.
- **Agent role changes** should explain which recorded behavior they fix. Adding, removing or merging an agent needs an architecture decision record in `docs/decisions/`.
- **Tool changes** need tests. `tools/analyze.py` must keep its rules: never average percentiles, list monitoring gaps instead of filling them, and convert time to UTC.
- **Test data** must be synthetic. Do not commit real results, even with names removed.

Original materials are under the [MIT License](LICENSE).
