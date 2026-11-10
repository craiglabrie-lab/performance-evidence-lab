# ADR-0004: Test validity is checked before bottleneck analysis

**Decision:** Before any bottleneck analysis, the Test Execution Analyst decides whether the run achieved its load profile, and states what the results are usable for and not usable for. All later agents work within that result. The Performance Test Lead cannot override it, only record a disagreement.

**Why:** The most expensive analysis mistake is a confident root cause from a test that never reached its load profile, for example because a load generator was saturated or Vusers dropped out. Deciding validity first, in one place, stops the rest of the analysis from building on a broken test.

**Consequences:** An invalid test still produces a useful test summary: what went wrong with the test, which results can be trusted, and how to fix the retest. A system that slows down under the planned load does not make a test invalid; that distinction is written into the Test Execution Analyst's role.

**Revisit when:** a recorded run shows the validity check blocking a finding that the data fully supported.
