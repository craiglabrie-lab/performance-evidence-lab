# Analysis workflow

The steps an experienced performance team follows when it analyzes load test results. The agents run this workflow, and a performance engineer can follow it by hand.

## Seven stages

| Stage | What gets answered | Agent | Output |
| --- | --- | --- | --- |
| 1. Test planning review | What is the test objective, which SLAs apply, and which tiers need a bottleneck review? | Performance Test Lead | Analysis plan |
| 2. Data collection & time alignment | Do we have the right run, its execution metadata, complete monitoring, aligned clocks and a baseline run? | Results & Monitoring Analyst | Data inventory and gap list |
| 3. Test validity check | Did the test achieve its load profile, with healthy load generators, valid scripts and a representative environment? What are the results usable for? | Test Execution Analyst | Test validity result |
| 4. Results analysis | What happened, when did degradation start, did each SLA pass, and what regressed against the baseline? | Results Analyst | Observations, SLA results, degradation windows |
| 5. Bottleneck analysis | Which tier is the bottleneck, which tiers are eliminated, and how much headroom does each have? | Application & APM, Database, Infrastructure & Network engineers | Bottleneck hypotheses |
| 6. Peer review | Which findings go further than the data supports? | Peer Reviewer | Review comments |
| 7. Test summary & go/no-go | What do we conclude, and what is the retest or tuning plan? | Performance Test Lead, then Test Report Author | Go/no-go recommendation and test summary |

The test validity check comes before results analysis. If the test did not achieve its load profile, the rest of the workflow still runs, but it reports what the run is usable for, explains what went wrong with the test, and plans the retest. It never issues a capacity result the test cannot support.

## Read next

- [Test summary results](test-summary-results.md): test validity, SLA results, root-cause status and confidence.
- [Analysis rules](rules.md): the thirteen rules every agent follows.
- [Records](records.md): the IDs that link each finding to its data.
