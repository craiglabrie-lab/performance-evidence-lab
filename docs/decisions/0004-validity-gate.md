# ADR-0004 — Validity is a gate decided before diagnosis

**Decision:** The Test Validity Reviewer decides, before any diagnosis, whether the run can answer the question asked, and lists allowed and restricted claims. Downstream agents work within that scope. The Test Lead cannot overrule the gate, only record disagreement.

**Why:** The most damaging review error is a confident diagnosis from a test that never produced its intended load. Deciding validity first, and in one place, stops the rest of the review from quietly building on a broken run.

**Consequences:** An invalid run still produces a useful report: what went wrong with the test, what can be trusted, and how to fix the rerun. A system that slows down under genuine load does not invalidate a test; that distinction is written into the reviewer's role.

**Revisit when:** a recorded run shows the gate blocking a conclusion that the evidence fully supported.
