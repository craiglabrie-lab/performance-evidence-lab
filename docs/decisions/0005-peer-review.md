# ADR-0005: The Peer Reviewer reviews the data before the team's findings

**Decision:** The Peer Reviewer runs twice. The first run sees only the test run description, the computed results summary and the data inventory, and writes its own initial review. The second run reviews the team's findings and writes review comments. The Performance Test Lead must resolve every review comment.

**Why:** A reviewer who reads the conclusion first tends to check whether it sounds right, not whether it is right. Forming a view from the data first, then comparing it with the team's analysis, is how a good senior engineer avoids anchoring on the first explanation.

**Limits:** All agents run on the same model. The Peer Reviewer has its own context, not its own model, and the test summary says so.

**Revisit when:** a different model is available for the Peer Reviewer and runs can measure whether it finds more.
