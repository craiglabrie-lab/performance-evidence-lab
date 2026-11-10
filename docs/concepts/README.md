# Concept documents

Each document here describes a design that is **not yet implemented**. Every document opens with a status banner, and every section marked *Implemented* points to the code that already exists. The concepts answer the [persona review](../reviews/2026-11-persona-review.md), mostly the AI engineer's points about running a multi-agent system in production.

| Concept | Answers | Draft artifacts included |
| --- | --- | --- |
| [Handoff schema](handoff-schema.md) | AI-2: handoffs are free-form Markdown | [`schemas/handoff.schema.json`](../../schemas/handoff.schema.json) (draft JSON Schema) and an example handoff |
| [Orchestrator](orchestrator.md) | AI-1, AI-7: no state machine, checkpoints, resume, human sign-off or tracing | [`templates/run-state.example.json`](../../templates/run-state.example.json) |
| [Agent tool contracts](agent-tool-contracts.md) | AI-5: the case for multiple agents | Tool contract table per agent |
| [Cost and model routing](cost-and-model-routing.md) | AI-4: cost and context are not engineered | Token budget table per step |
| [Evaluation harness](evaluation-harness.md) | AI-6: the evaluation would not convince an AI engineer | Scoring rubric mapped to the answer key |
| [Baseline and regression tracking](baseline-and-regression.md) | PE-1: regression comparison across builds | Run registry format |

**Status labels used in these documents**

- **Implemented**: exists in the repository and is tested.
- **Concept**: designed here, not built.
- **Open question**: not decided yet.
