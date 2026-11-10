# ADR-0009: Cost controls for agent runs

**Decision:** Before the next recorded run, apply four controls:

1. **Context slices.** `tools/analyze.py --sections` splits the computed results summary into section files. Each sub-agent receives only the sections its role needs, listed per step in [`/review-run`](../../.claude/commands/review-run.md).
2. **Model routing.** The Results & Monitoring Analyst, Results Analyst and Test Report Author run on a smaller model (`model: sonnet` in `.claude/agents/`). The Performance Test Lead, Test Execution Analyst, the three engineers and the Peer Reviewer keep the session model.
3. **Lean instructions.** Each sub-agent works from its sections, opens raw data only to check a specific number, aims for 10 tool calls or fewer, and keeps its handoff to about 150 lines.
4. **One test run first.** Record test run 02, measure it, then decide on test run 01.

**Why:** The earlier recorded runs used about 1.7 million tokens per test run, against about 0.1 million for a single prompt. Every step started by reading the full data set and every earlier handoff, and each tool call re-sent the whole context. See [cost and model routing](../concepts/cost-and-model-routing.md).

**Expected effect:** roughly 0.5–0.9 million tokens for test run 02. This is an estimate, to be replaced by the measured figure in the run log.

**Risks:** A smaller model could miss details in the inventory or the transaction summary. The Peer Reviewer and the answer key scoring should catch this, and the routing will be revisited if they do. The Peer Reviewer still uses the same model family as the team.

**Revisit when:** the first recorded run under these controls is scored.
