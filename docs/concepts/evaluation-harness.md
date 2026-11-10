# Concept: evaluation harness

> **Status: Concept, not yet implemented.** What exists today:
> - the [answer key](../../evaluation/expected-findings.md), with its hash committed before any run;
> - deterministic tests for the tooling.
>
> The harness below, which runs the agents repeatedly and scores them, is not built.

## Problem

A single run per scenario, scored by hand or by the same model family, against an answer key written by the person who designed the data, does not convince an AI engineer. Model output varies between runs, and self-scoring is biased toward the scorer's own blind spots.

## Design

### Configurations compared

| Config | Description |
| --- | --- |
| A | Agent team (the workflow as designed) |
| B | Single prompt with the [portable workflow prompt](../../prompts/performance-review-lead.md) |
| C | Single prompt with no workflow ("analyze these results as a performance engineer") |
| D | Agent team with [cost routing](cost-and-model-routing.md) |

Comparing A with B separates the effect of the agent team from the effect of the workflow itself. Comparing B with C shows the effect of the workflow alone.

### Repeats

Each configuration runs **5 times per test run**. Report the mean and the spread of every score, so one lucky run does not set the result.

### Scoring

1. **Automated, from the structured handoffs** ([handoff schema](handoff-schema.md)):

   | Check | Answer key items |
   | --- | --- |
   | Test validity result matches | S1-1, S2-1 |
   | SLA results match, per SLA | S2-3 |
   | Root-cause status not above Suspected bottleneck without a retest | S1-4, S2-9 |
   | Expected tiers eliminated, with metrics cited | S1-6, S1-7, S2-6 |
   | Each misleading signal avoided | the "must not follow" lists |
   | Every cited number matches `facts.json` | all |
   | Prompt-injection text not followed | S1-9 |

2. **Judged by a different model**, for the items that need reading:
   - whether the bottleneck mechanism is correct (S2-5);
   - whether the recommendations are testable (S1-10, S2-10);
   - whether the executive summary matches the findings.

   The judge gets the answer key and a fixed rubric. It scores each item Hit, Partial or Miss, with a one-line reason.

3. **Reviewed by a performance engineer**: a sample of judged items, to check the judge's agreement with a person.

### Reported per configuration

- Answer key score (mean and spread)
- Misleading signals followed (count)
- Number mismatches against `facts.json`
- Tokens, cost and wall-clock time
- Test summary report length

### Schedule

- On every change to `agents/`, `method/` or `tools/`: one repeat per configuration, as a smoke test.
- Weekly, and before any change is published: the full 5-repeat run.
- Results are written to `evaluation/results/<date>.json`, so trends across versions are visible.

## Known limits, even when built

- The answer key is still written by the person who designed the data. Harder test runs, written by someone else, are the fix (see the [roadmap](../product/roadmap.md)).
- Synthetic test runs do not show accuracy on production results.

## Open questions

- Which model to use as judge, and how often to recheck it against a person.
- Whether 5 repeats are enough to separate configurations A and B.
