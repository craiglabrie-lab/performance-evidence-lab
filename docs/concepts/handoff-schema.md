# Concept: typed handoffs between agents

> **Status: Concept, not yet implemented.** The draft schema [`schemas/handoff.schema.json`](../../schemas/handoff.schema.json) and the [example handoff](../../schemas/examples/03-test-execution.example.json) exist, and a test validates the example against the schema. No agent produces or consumes JSON handoffs yet; today's handoffs are Markdown.

## Problem

Each agent writes a Markdown file, and the next agent reads that prose and works out what it says. This causes four problems:

- a finding can be lost or reworded between agents;
- the Test Report Author can cite a number that no upstream agent produced;
- scoring a run against the answer key needs a person, or another model, to read every file;
- the orchestrator cannot check that a step produced what the next step needs.

## Design

Each agent writes **two files**:

1. `run/NN-<step>.json`: the structured handoff, validated against `schemas/handoff.schema.json` before the next step starts.
2. `run/NN-<step>.md`: the readable version for people, written from the JSON.

The schema defines one envelope and a set of record types that match the [record IDs](../../method/records.md):

| Record | Required fields |
| --- | --- |
| `data_item` (DATA-) | id, file, scope, time basis, coverage, limitations |
| `gap` (GAP-) | id, source, minutes or scope, effect on analysis |
| `test_validity` (VAL-) | result (Valid / Valid with limitations / Invalid), reason, usable for, not usable for, supporting record IDs |
| `observation` (OBS-) | id, statement, metric, value, unit, window, load generator / node / transaction, source record IDs |
| `sla_result` | SLA ID, result (Pass / Fail / Not evaluated), window, measured values, reason |
| `degradation_window` (DW-) | id, start and end minute, transactions affected, questions for engineers |
| `hypothesis` (HYP-) | id, tier, mechanism, supporting IDs, contradicting IDs, alternatives, root-cause status, confidence and reason, confirming test |
| `elimination` | tier, metrics cited, window covered |
| `review_comment` (RC-) | id, target ID, issue, severity (major / minor), requested change |
| `resolution` | RC ID, outcome (accepted / partly accepted / rejected), reason |
| `finding` (F-) | id, statement, record IDs, root-cause status, confidence and reason |
| `recommendation` (REC-) | id, type (test fix / monitoring / tuning / retest), owner, action, success metric, disproving result, priority |
| `go_no_go` (GNG-) | recommendation, strongest alternative, uncertainty, what would change it, approver (always a person) |

Every record that cites a number includes the record ID it came from, so a validator can check that each number traces back to the computed results summary (`facts.json`) or to a shown calculation.

## Checks the orchestrator would run after each step

1. The JSON validates against the schema.
2. Every ID referenced exists in an upstream handoff or in `facts.json`.
3. Every number tagged as coming from `facts.json` matches it exactly.
4. No SLA result is Pass or Fail when the test validity result marks that SLA "not usable for".
5. No root-cause status is *Confirmed root cause* unless a retest or tuning change is cited.

Checks 3–5 replace parts of the Test Report Author's self-reported report checks with deterministic ones.

## Trade-offs

- Agents spend tokens writing JSON as well as Markdown. Writing JSON first and rendering Markdown with code would remove the duplication.
- A strict schema can force an agent to drop nuance. The `notes` field on every record keeps free text, but no check depends on it.
- The schema becomes a versioned contract: changing it requires updating the agents, the validator and the scoring together.

## Open questions

- Whether to keep the Markdown handoffs at all, or generate them from JSON with code.
- Whether the Peer Reviewer should comment on the JSON records or on the Markdown.
