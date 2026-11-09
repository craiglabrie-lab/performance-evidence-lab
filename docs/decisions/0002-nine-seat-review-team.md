# ADR-0002 — Nine agents, modelled on a real review team

**Decision:** The team has nine fixed seats: Test Lead, Results Librarian, Test Validity Reviewer, Performance Analyst, Application / APM Specialist, Database Specialist, Infrastructure & Network Specialist, Devil's Advocate and Report Writer.

**Why:** These mirror the people a performance team actually brings into a results review. Each seat owns one question and can be held to it. Separate application, database and infrastructure specialists mean each layer is either implicated or ruled out with its own evidence, which is how real reviews avoid "it's probably the database".

**Alternatives considered:**
- *One assistant with the whole method in one prompt.* Simpler and cheaper; it is the baseline every run is compared against.
- *Fewer, broader roles* (an earlier design had one "cross-stack" diagnostic role). Rejected: it hid which layers had actually been examined.

**Consequences:** More calls and more tokens than a single prompt. The Test Lead decides which specialists a given review needs.

**Revisit when:** recorded runs show a seat that never changes the outcome, or a recurring gap no seat covers.
