# Decision-Aware Sampling Strategy

VOC sampling is an evidence-coverage design, not a probability sample. Choose volume from the decision risk and category heterogeneity, then distribute it across channels. Do not begin with an equal per-channel target.

## Default post-clean evidence tiers

| Research mode | Exploratory | Standard | Deep |
|---|---:|---:|---:|
| Category opportunity | 300 | 900 | 2,000 |
| Brand reputation | 300 | 800 | 1,500 |
| Product improvement | 350 | 800 | 1,500 |
| Listing content | 250 | 600 | 1,000 |
| Rating recovery | 300 | 700 | 1,080 |
| Competitor intelligence | 400 | 1,000 | 2,200 |
| Content strategy | 400 | 1,000 | 2,500 |

These are restartable defaults, not universal statistical power claims. Raise the target when the category has many vehicle models, use scenes, languages, product architectures, or brands. A bounded teaching exercise, pilot, or demonstrably small public universe may use a smaller justified target declared before collection. State the purpose, limits, channel/parent floors, and allowed claims; preserve every channel already promised. Do not force a 350-record product-improvement default onto a small teaching task, or retrospectively lower a target to fit collected rows.

The channel floors below are interpretability defaults for full studies. A bounded teaching contract may predeclare smaller collection floors and parent targets per promised channel, while excluding undersized sources from incidence/cross-channel agreement claims. Keep the channel required for its declared teaching role; do not retroactively relabel it optional or lower its agreed floor.

## Portfolio design

Use the three open, information-rich channels as the core:

- YouTube: relevant videos, transcript-videos, top-level comments, and replies.
- Public vertical forums: owner threads, long-term use, failures, repairs, and workarounds.
- Old Reddit: public original posts and substantive comments across independent threads.

Plan the following completion families from the start when they are relevant to the decision:

- supervised high-risk social: X, TikTok, Facebook, and Instagram;
- third-party review platforms: brand/service trust evidence such as Trustpilot or Sitejabber;
- independent web review sources: specialist sites, retailer/dealer reviews, brand-store verified-review widgets, public Q&A, and comment sections;
- app stores: app-level setup, connectivity, update, and support language when an app is part of the product workflow;
- marketplace and first-party evidence: Amazon reviews and authorized operational exports.

Collect these smaller families after preliminary core analysis so their search terms target the observed objections and unresolved gaps. Their later timing is a precision and risk-control choice, not an optional-source waiver.

Only explicitly optional unavailable allocations may be redistributed toward core sources. Required Amazon, first-party, review, or social coverage stays required until met or an actual user-approved scope revision is frozen. Keep purchased-use evidence separate from category context.

Treat each planned channel value as three different controls:

- `record_floor`: the minimum retained evidence needed for the channel's declared role;
- `record_goal`: the collection budget, not a selection cutoff;
- `record_cap`: the concentration ceiling after any reallocation.

Only channels explicitly declared optional may move to core open sources. A declared Facebook, TikTok, vertical-community, review-platform, or independent-site completion cell cannot be replaced by extra YouTube, Reddit, or Amazon rows. Never discard valid core evidence merely because its planning goal was reached while the total study remains short.

For X, TikTok, Facebook, and Instagram, reserve a small but interpretable sample when enabled:

- target at least `max(30 records, 3% of the post-clean total)` per channel;
- cover at least 10 independent parent posts or content units;
- keep an individual high-risk channel below 6% by default;
- if either floor is missed, label it `case supplement` and exclude it from incidence and cross-channel agreement claims.

For third-party review platforms and independent web review sources, use the same default interpretability floor of 30 retained records and 10 independent parent pages/content units when the public universe supports it. If the universe is smaller, preserve the domain/query attempt ledger and apply the two-expansion saturation rule. Brand-level reviews may support trust/service themes but not model-level performance incidence.

For app stores, use at least 20 retained reviews across both major stores when both are relevant and public. App-level evidence can confirm app workflow themes but does not by itself prove that a named hardware model has the same failure.

For deep rating-recovery work, the 1,080-record default reserves a large core for YouTube, vertical communities, Old Reddit, and Amazon while retaining bounded completion cells for Facebook, TikTok, Instagram, X, review platforms, independent sites, and app stores. Read `rating-recovery.md` before freezing direct-model, low-star, recent-window, and evidence-class floors.

This floor improves interpretability; it does not make personalized search results representative.

## Parent and evidence floors

Control both child-record volume and independent parents. A thousand comments from two viral videos is not a broad sample.

- Deep YouTube: normally at least 120 relevant videos and captions for at least 60% of relevant videos where public tracks are recoverable.
- Deep YouTube collection: normally retrieve at least 3,000 raw top-level/reply comment candidates before relevance filtering, deduplication, parent caps, and quality exclusions. This raw candidate target is separate from the post-clean portfolio total.
- Deep public forums: normally at least 60 independent threads.
- Deep Old Reddit: normally at least 60 independent threads.
- Product improvement: at least 20% verified/claimed owned-use evidence and 10% negative or defect-bearing evidence, unless the universe is smaller and documented.
- Cross-channel agreement: at least three independent sources must each meet their own record and parent floors.

Keep transcript-video, video, comment, reply, forum-post, Reddit-record, review, and first-party-case denominators separate.

## Planning command

```bash
python3 scripts/plan_sample.py \
  --mode product-improvement \
  --depth deep \
  --channels youtube owner_forum reddit amazon x tiktok facebook instagram first_party \
  --output sample_plan.json
```

The portfolio target is post-clean. The plan also emits higher raw candidate targets for API-capable sources, especially YouTube, so bulk retrieval capacity is used without weakening the final evidence standard.

## Stop and append rules

Stop only when both the core-sample gates and every required completion-family gate pass, or when two successive query or parent expansions add less than 5% new relevant records and all shortfalls are documented. Append by missing scene, brand, model, ownership class, sentiment, time period, source type, or required channel family; do not add arbitrary volume to the already dominant segment.

Calculate the rule for every unfinished required source from saved successful measured rounds. Unknown increment counts, verification/login waits, failures, and unattempted sources cannot count as zero-yield expansions. Until eligible saturation is established, a shortfall remains `needs_append` or a source-specific wait. A global low-yield round cannot waive another required channel.

Freeze this plan through [execution-and-delivery.md](execution-and-delivery.md). Required status, floors, parent floors, source roles/members, and quality thresholds are protected; goals and caps remain collection budgets. A `partial` report may be permitted by unified acceptance after valid saturation, but `task_complete` remains false.
