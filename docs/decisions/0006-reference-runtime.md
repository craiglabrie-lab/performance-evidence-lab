# ADR-0006 — Claude Code subagents as the reference runtime

**Decision:** The reference implementation runs each agent as a separate Claude Code subagent, dispatched by the [`/review-run`](../../.claude/commands/review-run.md) command. The recorded demonstration runs used Claude Opus 5.5.

**Why:** Subagents give each role a separate context with no framework to install. The role files are plain Markdown that any other runtime can also use as prompts. Anyone with Claude Code can reproduce a run with one command; anyone without it can read every handoff that a run produced.

**Limits:** File-access limits for each agent are given as instructions, not enforced by a sandbox. All agents share one model. There is no budget enforcement beyond the runtime's own.

**Alternatives considered:** A Python orchestrator calling a model API directly (more control over budgets and access; needs an API key and more code), or an agent framework (more machinery than a demonstration needs).

**Revisit when:** the project needs enforced access control, cost limits, or a mix of models across roles.
