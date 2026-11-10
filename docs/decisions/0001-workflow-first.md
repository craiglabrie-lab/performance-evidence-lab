# ADR-0001: The analysis workflow is the product

**Decision:** Performance Evidence Lab is first a workflow for analyzing performance test results. The nine-agent team is its reference implementation.

**Why:** The lasting value is the analysis practice: check test validity before bottleneck analysis, keep SLA results separate from root-cause status, calculate with tools, and tie every finding to its data. A performance engineer, a single AI assistant or an agent team can all follow it. Tying it to one framework or vendor would make it harder to reuse.

**Consequences:** The workflow is documented in [method/](../../method/README.md) so an engineer can follow it by hand. Agent role files reference the workflow instead of repeating it.

**Revisit when:** a second implementation, such as another agent runtime or a manual checklist, shows parts of the workflow that only make sense for agents.
