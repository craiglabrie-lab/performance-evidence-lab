# ADR-0001 — The method is the product

**Decision:** Performance Evidence Lab is first a review methodology for load-test results. The nine-agent team is its reference implementation.

**Why:** The lasting value is the discipline: validity before diagnosis, evidence grades kept apart from confidence, numbers from tools, claims traceable to evidence. That discipline works whether a person, one assistant or a team of agents applies it. Tying it to one framework or vendor would make it harder to reuse.

**Consequences:** The method is written in [method/](../../method/README.md) so a person can apply it by hand. Agent role files reference the method instead of restating it.

**Revisit when:** a second implementation (another runtime, or a manual review checklist) shows parts of the method that only make sense for agents.
