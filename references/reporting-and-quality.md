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

Large category studies need higher gates and source-balance rules. A small teaching or pilot task may set a smaller justified sample target before collection and preserve all promised channels. The 50-record quality default and larger mode defaults are not universal task minima. Source roles, record/parent floors, and quality thresholds are frozen; do not reduce them after observing shortfalls. Human audit counts must be actual and cannot exceed the available records.

## Status

- `pass`: all predeclared critical gates pass and no unresolved safety, compliance, or traceability veto remains.
- `partial`: a limited report may be allowed only after unified acceptance confirms eligible saturation for all unfinished required sources and a valid audit. Useful but merely unfinished evidence stays in a working state; missing audit or access waits cannot be called saturation.
- `blocked`: the requested evidence cannot be accessed safely, required inputs are absent, or structural validation prevents analysis.

Report core-sample readiness and omnichannel completion separately. A report may say the core evidence is analytically usable while the overall workflow remains `needs_append` or `waiting_for_user_login`. Do not display a final all-channel `PASS` until every required vertical-community, social, review-platform, independent-site, marketplace, and first-party coverage cell has passed. A permitted saturation-limited partial report displays the shortfalls and `task_complete=false`, never a global PASS.

## Unified delivery acceptance

Use [execution-and-delivery.md](execution-and-delivery.md) for `delivery_acceptance.py`, scope lock, access checkpoints, and renderer commands. The quality gate alone does not authorize delivery. Acceptance reconciles locked scope with the current plan, record/parent coverage, human audit, access waits, and source-specific measured rounds. It exposes `task_complete`, `final_report_allowed`, `snapshot_allowed`, and the next executable action.

Bind and recheck input hashes for all built-in and custom report paths. Recompute acceptance when any bound input changes; an old receipt cannot validate new data. `generate_report.py` and `validate_report.py` both require `--acceptance`. A hand-written HTML report is subject to the same gate.

A progress snapshot may show current evidence, missing sources, and next actions with `task_complete=false`; a taxonomy draft, collection CSV, or renamed “pilot report” cannot stand in for the requested final result. While a source, calibration, or audit is waiting, continue independent executable work. Only full acceptance marks the task complete.

## Evidence weighting

Never hide evidence classes inside one score. Present at least:

- verified purchase or first-party purchased-use evidence;
- claimed owned use;
- creator/reviewer demonstration;
- purchase intent and information seeking;
- promotion, official content, and distribution signals.

Use weights only for prioritization after showing unweighted counts and documenting the weight rationale. Do not call a weighted score a market rate.

## Rating-recovery gates

When `research_mode` is `rating-recovery`, also require:

- a timestamped baseline with listing URL/ASIN, displayed rating, rating count, and parent/child scope;
- the predeclared target-model direct, rating-bearing, low-star, recent-window, and direct-source floors;
- a valid `rating_driver` for at least 90% of target-model low-star evidence;
- target-model, adjacent-model, category, competitor, official, and editorial evidence kept separate;
- the full product rating distribution kept separate from sampled review-text distribution;
- a current policy check before recommending any review-request workflow;
- a post-change measurement plan with rating hold period and return/support guardrails.

A rating-recovery quality-gate pass means the evidence package can support prioritization. It does not mean the displayed rating has recovered.

## Report structure

1. Decision and confidence.
2. Recommended actions, owners, proof requirements, and stop conditions when known.
3. Data scope and denominator ledger.
4. Channel-family completion ledger: planned floor/goal/cap, retained records, independent parents, authorization/access state, and whether the source can enter cross-channel agreement.
5. Source-specific positive themes and pain points.
6. Brand/product/vehicle comparisons within matched contexts.
7. Anomaly and safety signals.
8. People, scenes, jobs, workarounds, and funnel evidence.
9. Evidence chain with `source_id`, short excerpt, and URL.
10. Method, exclusions, missingness, access limitations, and quality-gate result.

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
