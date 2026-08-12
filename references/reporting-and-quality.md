# Reporting and Quality

## Denominator ledger

Always disclose:

- discovered records;
- successfully collected records;
- records excluded by each reason;
- records retained before and after parent caps;
- labeled records;
- audited records;
- records by source and access mode;
- rating-bearing and verified-purchase subsets;
- unique parent posts, videos, products, and brands where available.

Do not compare raw counts as incidence when collection depth differs by channel.

## Default quality gates

Tune thresholds in the study contract before collection. Defaults are conservative starting points, not universal truth.

| Gate | Default |
|---|---:|
| Included records | at least 50 |
| Distinct sources | at least 2 |
| Largest source share | no more than 70% |
| Annotation coverage | at least 95% |
| Missing source URL | no more than 5% |
| Annotation structural errors | 0 |
| Human audit | required |
| Fully correct audit records | at least 90% |
| Largest parent contribution | no more than 20% after cap |

Large category studies need higher gates and source-balance rules. Small brand-reputation pilots may remain `partial` while still producing useful hypotheses.

## Status

- `pass`: all predeclared critical gates pass and no unresolved safety, compliance, or traceability veto remains.
- `partial`: useful evidence exists, but one or more coverage, balance, audit, or access gates miss.
- `blocked`: the requested evidence cannot be accessed safely, required inputs are absent, or structural validation prevents analysis.

## Evidence weighting

Never hide evidence classes inside one score. Present at least:

- verified purchase or first-party purchased-use evidence;
- claimed owned use;
- creator/reviewer demonstration;
- purchase intent and information seeking;
- promotion, official content, and distribution signals.

Use weights only for prioritization after showing unweighted counts and documenting the weight rationale. Do not call a weighted score a market rate.

## Report structure

1. Decision and confidence.
2. Recommended actions, owners, proof requirements, and stop conditions when known.
3. Data scope and denominator ledger.
4. Source-specific positive themes and pain points.
5. Brand/product/vehicle comparisons within matched contexts.
6. Anomaly and safety signals.
7. People, scenes, jobs, workarounds, and funnel evidence.
8. Evidence chain with `source_id`, short excerpt, and URL.
9. Method, exclusions, missingness, access limitations, and quality-gate result.

## Decision safeguards

- Views, likes, comments, and shares are distribution signals, not purchase demand.
- Search ranking is not a representative sample.
- First-page Amazon reviews are not the complete review population.
- A social post question is not owned-use evidence.
- A visible product claim is not independent proof.
- Cross-source agreement raises confidence only when the underlying evidence classes and contexts are meaningfully independent.
- Cross-source disagreement is a finding. Show it instead of averaging it away.

## Feedback loop

After a product, listing, content, or service change, compare the relevant business outcome with the VOC hypotheses. Record which labels predicted returns, service contacts, conversion objections, or repeat purchase, and retire labels that produce no actionable distinction. This is model calibration, not proof that the original VOC caused the outcome.
