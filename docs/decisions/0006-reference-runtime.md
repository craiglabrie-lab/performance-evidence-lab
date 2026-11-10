# ADR-0006: Claude Code sub-agents as the reference runtime

**Decision:** The reference implementation defines each agent as a Claude Code sub-agent in [`.claude/agents/`](../../.claude/agents/), with its own context and a fixed tool list, dispatched in order by the [`/review-run`](../../.claude/commands/review-run.md) command.

**Why:** Sub-agents give each role context isolation with no framework to install. The role files are plain Markdown that any other agent runtime can use as prompts. Anyone with Claude Code can rerun an analysis with one command, and anyone without it can read every handoff file a run produced.

**Limits:** Tool lists are enforced, but each agent's file inputs are instructions, not a sandbox. The orchestrator is itself a prompt, not code, so it has no checkpoints or resume yet (see the orchestrator design concept on the roadmap). All agents share one model. There are no cost limits beyond the runtime's own.

**Alternatives considered:** a Python orchestrator calling a model API directly (more control over cost and access, but it needs an API key and more code), or an agent framework (more machinery than this project needs).

**Revisit when:** the project needs enforced access control, cost limits, or different models for different agents.
