# ADR-0002: Nine agents, modeled on a performance test team

**Decision:** The workflow uses nine agents: Performance Test Lead (orchestrator), Test Data & Monitoring Analyst, Test Validity Analyst, Performance Analyst, Application & APM Engineer, Database Performance Engineer, Infrastructure & Network Engineer, Peer Reviewer and Report Author.

**Why:** These are the people a performance team brings into a results analysis. Each agent has one responsibility and can be held to it. Separate application, database and infrastructure engineers mean each tier is either identified as the bottleneck or eliminated with its own metrics, instead of a general "probably the database".

**Alternatives considered:**
- *One AI assistant with the whole workflow in one prompt.* Simpler and cheaper. It is the baseline the agent team is compared against.
- *Fewer, broader roles.* An earlier design had a single cross-tier diagnostic role. It was dropped because it hid which tiers had actually been analyzed.

**Consequences:** More agent calls and more tokens than a single prompt. The Performance Test Lead decides which engineers each test run needs.

**Revisit when:** recorded runs show an agent that never changes the outcome, or a recurring gap that no agent covers.
