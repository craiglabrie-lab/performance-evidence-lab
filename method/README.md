# Analysis workflow

The steps an experienced performance team follows when it analyzes load test results. The agents run this workflow, and a performance engineer can follow it by hand.

## Seven stages

| Stage | What gets answered | Agent | Output |
| --- | --- | --- | --- |
| 1. Test planning review | What is the test objective, which SLAs apply, and which tiers need a bottleneck review? | Performance Test Lead | Analysis plan |
| 2. Data collection & time alignment | Do we have the right run, complete monitoring and aligned clocks? | Test Data & Monitoring Analyst | Data inventory and gap list |
| 3. Test validity check | Did the test achieve its load profile with healthy load generators? What are the results usable for? | Test Validity Analyst | Test validity result |
| 4. Results analysis | What happened, when did degradation start, and did each SLA pass? | Performance Analyst | Observations, SLA results, degradation windows |
| 5. Bottleneck analysis | Which tier is the bottleneck, and which tiers are eliminated? | Application & APM, Database, Infrastructure & Network engineers | Bottleneck hypotheses |
| 6. Peer review | Which findings go further than the data supports? | Peer Reviewer | Review comments |
| 7. Test summary & go/no-go | What do we conclude, and what is the retest or tuning plan? | Performance Test Lead, then Report Author | Go/no-go recommendation and test summary |

The test validity check comes before results analysis. If the test did not achieve its load profile, the rest of the workflow still runs, but it reports what the run is usable for, explains what went wrong with the test, and plans the retest. It never issues a capacity result the test cannot support.

## Read next

- [Test summary results](test-summary-results.md): test validity, SLA results, root-cause status and confidence.
- [Analysis rules](rules.md): the twelve rules every agent follows.
- [Records](records.md): the IDs that link each finding to its data.
