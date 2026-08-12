# Decision-Aware Sampling Strategy

VOC sampling is an evidence-coverage design, not a probability sample. Choose volume from the decision risk and category heterogeneity, then distribute it across channels. Do not begin with an equal per-channel target.

## Default post-clean evidence tiers

| Research mode | Exploratory | Standard | Deep |
|---|---:|---:|---:|
| Category opportunity | 300 | 900 | 2,000 |
| Brand reputation | 300 | 800 | 1,500 |
| Product improvement | 350 | 800 | 1,500 |
| Listing content | 250 | 600 | 1,000 |
| Competitor intelligence | 400 | 1,000 | 2,200 |
| Content strategy | 400 | 1,000 | 2,500 |

These are restartable defaults, not universal statistical power claims. Raise the target when the category has many vehicle models, use scenes, languages, product architectures, or brands. Lower it only when the universe is demonstrably small and record the reason before collection.

## Portfolio design

Use the three open, information-rich channels as the core:

- YouTube: relevant videos, transcript-videos, top-level comments, and replies.
- Public vertical forums: owner threads, long-term use, failures, repairs, and workarounds.
- Old Reddit: public original posts and substantive comments across independent threads.

Redistribute unavailable Amazon or first-party allocations toward those core sources. Keep Amazon reviews and authorized first-party records as high-value supplements, especially for product-improvement, listing, and brand-reputation decisions.

For X, TikTok, Facebook, and Instagram, reserve a small but interpretable sample when enabled:

- target at least `max(30 records, 3% of the post-clean total)` per channel;
- cover at least 10 independent parent posts or content units;
- keep an individual high-risk channel below 6% by default;
- if either floor is missed, label it `case supplement` and exclude it from incidence and cross-channel agreement claims.

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

Stop only when allocation and quality gates pass, or when two successive query or parent expansions add less than 5% new relevant records and all shortfalls are documented. Append by missing scene, brand, model, ownership class, sentiment, time period, or source type; do not add arbitrary volume to the already dominant segment.
