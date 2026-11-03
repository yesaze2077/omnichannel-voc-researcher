# Search Matrix and Append Protocol

Use this protocol for every public-web study large enough to require more than a few hand-picked records. A channel allocation describes evidence volume; it does not replace search planning.

## 1. Translate the decision into evidence questions

Before writing queries, list the decisions the evidence must support. For listing-content work, normally cover:

- who the product is for and which workflows matter;
- the five leading purchase objections;
- setup, compatibility, and boundary conditions;
- failures, workarounds, maintenance, durability, and support;
- alternatives, switching reasons, and competitor comparisons;
- proof needed before a claim can enter the listing.
- brand/service trust and warranty language from third-party review platforms;
- model-specific user Q&A/reviews from independent or brand-store pages;
- targeted social-language checks for the preliminary top objections.

Keep direct-target, adjacent-model, competitor, and category questions separate.

## 2. Build a pilot matrix

Start each core search source with 10-15 high-recall queries. Include category synonyms, baseline reviews, setup, scenes, ownership, comparisons, and a limited problem sample. Use the pilot to learn:

- user vocabulary and unexpected synonyms;
- relevant brands, models, workflows, communities, and content formats;
- ambiguity and reject terms;
- which queries produce independent parents rather than repeated content;
- likely comment/reply and transcript yield.

Do not call a source exhausted after a pilot.

```bash
python3 scripts/build_search_matrix.py \
  --category "4x6 thermal shipping label printers" \
  --mode listing-content \
  --stage pilot \
  --sources youtube reddit \
  --core-terms "4x6 thermal label printer,bluetooth shipping label printer" \
  --brands "Brand A,Brand B" \
  --scenes "Etsy shipping,Shopify fulfillment" \
  --problems "label calibration,bluetooth connection" \
  --workflows "iPhone,Android,Mac,Windows" \
  --reject-context-terms "mini label maker,receipt printer" \
  --reddit-entrypoint old \
  --reddit-authorization-status user_confirmed \
  --output search/pilot.jsonl
```

## 3. Freeze and run round 1

Use pilot evidence to build the formal matrix. A large YouTube study commonly uses 50-65 formal queries while leaving quota headroom. Reddit and forum matrices should cross product terms with communities, workflows, problems, ownership, comparisons, and support. Avoid rerunning unchanged queries.

Each matrix row contains:

- `query_id`, `source`, `round`, `dimension`, `query`, and optional `scope`;
- purpose, priority, required/reject context terms;
- parent target, result cap, access mode, authorization status, preferred/fallback entrypoint, and status.

When authorization is confirmed after a matrix already exists, update the access contract without changing query IDs:

```bash
python3 scripts/configure_reddit_access.py \
  --matrix search/all_queries.jsonl \
  --entrypoint old \
  --authorization-status user_confirmed \
  --summary search/reddit_access_summary.json
```

Keep negative/problem queries below the declared cap, normally 35%, so the matrix does not manufacture a complaint-heavy sample.

When a prior study exists, compare exact normalized terms before running the matrix:

```bash
python3 scripts/query_coverage.py \
  --matrix search/all_queries.jsonl \
  --prior raw/youtube/search_terms.json \
  --source youtube \
  --output search/youtube_seed_query_coverage.json
```

Exact matches can be skipped. Similar but non-identical queries still need a semantic review; do not assume string difference means new evidence.

## 4. Record query and round yield

Collection attempts are JSONL rows keyed by `query_id`. Record at least:

```json
{
  "query_id": "q_example",
  "source": "reddit",
  "round": "round_2",
  "is_expansion": true,
  "discovered_parents": 12,
  "new_parents": 8,
  "raw_records": 54,
  "relevant_records": 31,
  "new_relevant_records": 27,
  "retained_records": 24,
  "duplicate_records": 4,
  "access_mode": "authorized_browser_old_reddit",
  "page_url": "https://old.reddit.com/...",
  "status": "complete"
}
```

Calculate yield deterministically:

```bash
python3 scripts/round_yield.py \
  --matrix search/all_queries.jsonl \
  --attempts rounds/attempts.jsonl \
  --output rounds/round_yield.json
```

The incremental percentage is new relevant evidence divided by the relevant evidence accumulated before that round. Preserve missing or unknown counts as null; do not fill them with zero or infer new evidence from a total row count. Unknown denominators or increments remain ineligible for saturation. Record collection/access failure explicitly. A blocked or unattempted source is not a successful measured expansion.

Keep source-level yield and success eligibility. Two low-yield rounds on an easy source cannot satisfy saturation for a different unfinished required channel; aggregate yield cannot hide that channel’s missing attempts or login/verification wait.

## 5. Preliminary analysis and round 2

After round 1, clean the evidence and calibrate a stratified taxonomy sample. Build the next matrix only from visible gaps such as:

- missing scene, workflow, brand, model, or time period;
- weak owned-use or negative/defect evidence;
- an unresolved contradiction across sources;
- a major purchase objection without product-specific proof;
- excessive official, affiliate, or single-parent concentration.

Use `--stage round_2 --gap-terms "..."` and append the results. Do not add arbitrary volume to an already dominant segment.

For repeatable studies, declare required evidence cells and compute the gaps instead of eyeballing them:

```bash
python3 scripts/gap_analysis.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --requirements search/evidence_requirements.json \
  --output search/gap_analysis.json
```

Each evidence cell can require minimum records, independent parents, and sources, filtered by source, record type, brand, product, product relation, ownership signal, sentiment, funnel stage, or taxonomy tags. Feed the failed cells' `gap_terms` into the round-2 matrix.

## 6. Targeted omnichannel completion

After the broad core sources have been cleaned and the preliminary taxonomy is stable, create a separate `targeted_completion` matrix for every required small channel family:

- Facebook, TikTok, Instagram, and X: combine the target product/category with the preliminary objections, scenes, workflows, comparisons, and recovery actions. Keep creator/seller/affiliate content separate from user comments.
- Public vertical communities: target missing platforms, merchant workflows, long-term threads, and specialist terminology across multiple domains.
- Third-party review platforms: target brand trust, support, fulfillment, warranty, returns, and product/model names.
- Independent sites and brand/store reviews: target the named model, competitor products, Q&A, verified-review widgets, and niche workflows; reject editorial/affiliate copy from VOC counts.
- App stores: target the relevant app name plus connection, permissions, platform, update, template, and support gaps; keep app-level evidence separate from named-hardware evidence.

This matrix is narrow by design. It should test, qualify, or extend preliminary findings rather than replay the entire broad matrix. Completing the main YouTube/Reddit/Amazon quotas does not close these required coverage cells.

```bash
python3 scripts/build_search_matrix.py \
  --category "4x6 thermal shipping label printers" \
  --mode listing-content \
  --stage targeted_completion \
  --sources owner_forum tiktok facebook review_site independent_web \
  --core-terms "MUNBYN RW403B,bluetooth shipping label printer" \
  --gap-terms "AirPrint confusion,app login,4x6 PDF workflow,label calibration,small text clarity,support warranty" \
  --communities "community.shopify.com,community.ebay.com,sellercentral.amazon.com,trustpilot.com,munbyn.com" \
  --output search/targeted_completion.jsonl
```

## 7. Login and access states

A normal login wall becomes `waiting_for_user_login`; a connection-verification challenge becomes `waiting_for_user_verification`. Stop automated interaction and ask the user to complete the displayed action directly. Save query ID, URL, parent, position, and last retained source ID using `source_access.py`; see [execution-and-delivery.md](execution-and-delivery.md). Never request credentials or solve/bypass a challenge.

User confirmation and a visible readable body are both required before `resume_confirmed`. Resume the saved page and append/deduplicate. If verification fails, or the route returns real 403/429, access denial, rate limit, or a private/member-only boundary, stop that restricted route and use only an authorized fallback.

Continue other executable required sources and independent preparation while the route waits. Pending taxonomy calibration or audit blocks only its dependent operations. Keep the same required source, floors, and parent target; do not rewrite the source plan to call it a case supplement.

## 8. Stop rule

Complete collection when core gates and every locked required completion-family gate pass. Otherwise continue executable targeted expansions. A saturation-limited report is eligible only when each unfinished required source has two consecutive successful measured expansions below 5%, with all shortfalls documented and audit valid. Missing/unknown counts, failed requests, unattempted queries, and user waits never qualify.

Run `delivery_acceptance.py` and then `collection_state.py --acceptance analysis/delivery_acceptance.json --output rounds/workflow_state.json`. Follow executable work before waiting. Final rendering requires `final_report_allowed`; snapshots remain available when `snapshot_allowed`, but must display `task_complete=false` and cannot substitute for the original task. A permitted `partial` report also retains `task_complete=false`.

Required sources and thresholds are frozen before collection. Only a real user decision recorded with `freeze_scope.py` can revise them; editing a plan or renaming the study does not change scope.
