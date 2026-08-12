---
name: omnichannel-voc-researcher
description: Run auditable multi-channel Voice of Customer research across YouTube, Reddit, Amazon, X, TikTok, Facebook, Instagram, and first-party customer data. Use this skill whenever the user asks for VOC, review mining, social listening, brand reputation, product pain points, competitor feedback, listing inputs, customer-language research, or cross-platform consumer research, even when they mention only one or two channels. It plans browser-assisted samples and authorized API fallbacks, normalizes evidence, builds and audits a taxonomy, computes deterministic statistics, applies quality gates, and produces a source-traceable report without merging incompatible denominators.
compatibility: Python 3.10+ using the standard library. Browser collection requires an available user-authorized browser tool. YouTube large-sample research can delegate to youtube-intelligence-researcher when installed.
---

# Omnichannel VOC Researcher

Build a decision-grade evidence package, not a pile of comments. Keep collection, cleaning, coding, statistics, interpretation, and recommendation as separate stages so every conclusion can be traced to source records and reproduced.

## Non-negotiable boundaries

This skill is shared only for noncommercial learning, personal research, teaching, and technical exchange. The software license does not authorize access to or reuse of third-party platform content or data. Every live study must separately satisfy applicable law, platform terms, API policies, access controls, privacy duties, and content rights.

1. Define the business decision before collecting data. A category study, brand reputation audit, listing rewrite, and defect investigation need different samples.
2. Choose a post-clean total and channel portfolio from the decision and research depth before collection. Never default to equal per-channel targets.
3. Keep denominators separate by source, record type, and evidence class. Never report one blended "internet sentiment rate" across Amazon ratings, Reddit comments, X posts, and YouTube comments.
4. Preserve `source_id`, source URL, collection time, access mode, and exclusion reason. Every quoted claim must resolve to a retained record.
5. Treat browser access to X, TikTok, Facebook, and Instagram as supervised supplementary research. Do not bypass CAPTCHA, checkpoints, access controls, rate limits, private spaces, or login requirements. Do not rotate accounts, identities, fingerprints, or proxies to evade controls.
6. Browser collection is read-only: no likes, follows, comments, messages, purchases, or account changes. Stop on CAPTCHA, re-authentication, checkpoint, 403, 429, explicit access limits, or repeated empty/error pages.
7. Follow the user's preferred route for high-risk social sources: browser-assisted sampling first; if it is blocked and an authorized official interface exists, record the failure and switch to that interface. Do not silently expand a browser sample into unattended bulk collection.
8. Do not publish raw author identifiers. Hash identifiers used for deduplication and remove them from final reports unless a valid research need and authorization are documented.
9. Label unsupported or unbalanced studies `partial`. Page visibility and successful collection do not establish permission for recurring commercial automation.

## Choose the research mode

| Mode | Decision supported | Primary evidence |
|---|---|---|
| `category-opportunity` | What unmet need is worth solving? | scenes, workarounds, alternatives, severity |
| `brand-reputation` | What drives trust, complaints, and repurchase? | owned-use evidence, service, durability, comparisons |
| `product-improvement` | What should product and QA fix first? | defects, fitment, safety, recurrence, low ratings |
| `listing-content` | What should a listing prove and explain? | objections, terminology, fitment, proof needs, FAQs |
| `competitor-intel` | Where do competitors win or fail? | brand-by-theme evidence with matched contexts |
| `content-strategy` | What content helps users decide or succeed? | questions, misconceptions, installation and use scenes |

## Workflow

### 1. Create the study contract

Read `references/sampling-strategy.md`. Write the decision question, research mode/depth, market, category definition, brands/products, time window, exclusions, target channels, post-clean total, per-source record and parent floors, report audience, quality thresholds, and stop conditions before collection.

Initialize a restartable workspace:

```bash
python3 scripts/init_study.py \
  --study "utv cab fan voc" \
  --category "UTV and ATV cab cooling fans" \
  --market "United States" \
  --decision "Prioritize product and listing improvements" \
  --channels youtube reddit amazon x tiktok first_party \
  --mode product-improvement \
  --depth deep \
  --output-root work
```

Do not set final thresholds after seeing results. Read `references/reporting-and-quality.md` before finalizing the contract.

### 2. Plan evidence by channel

Read `references/source-playbooks.md` and create a source plan. Use channels for the evidence they are good at instead of trying to collect the same volume everywhere.

- Make YouTube, public vertical forums, and Old Reddit the core evidence pool for deep public-web studies. Control both retained records and independent videos/threads.
- For YouTube, use the official Data API first for public search, metadata, top-level comments, and replies within quota. Delegate to `youtube-intelligence-researcher`, then recover public captions in its separate restartable transcript stage and normalize the outputs here.
- Keep YouTube raw candidate goals separate from retained VOC goals. For a default deep study, plan at least 3,000 raw comment/reply candidates across at least 120 relevant videos, then clean and cap them into the declared post-clean allocation.
- Do not claim that an API key can download arbitrary public captions. The official caption download endpoint requires permission to edit the video; public transcript recovery remains a separate mechanism.
- Use bounded, restartable collection from standard public forum pages and Old Reddit pages. Preserve query, page, thread, and failure manifests.
- For X, use supervised browser sampling first; when blocked or when an authorized structured retrieval is approved, use the official API and record credit usage.
- For each enabled high-risk social channel, target at least 30 retained records and 10 independent parents, normally 3-6% of the total. Below either floor, use examples only and exclude the channel from agreement claims.
- Treat Facebook and Instagram as experimental public-content supplements unless an authorized first-party API covers the requested data.
- Import customer support, returns, product reviews, surveys, and site search as first-party evidence with their own denominators.

Store collection manifests and failure states even when a channel returns zero records.

### 3. Normalize all records

Use the canonical schema in `references/schema.md`. Convert CSV, JSON, JSONL, or platform exports without carrying raw author names into the normalized layer:

```bash
python3 scripts/normalize_records.py \
  --input raw/amazon_reviews.csv \
  --output normalized/records.jsonl \
  --source amazon \
  --access-mode browser_assisted \
  --append
```

Use `--field-map` when source columns do not match common aliases. Never overwrite raw evidence.

### 4. Clean, deduplicate, and cap concentration

```bash
python3 scripts/clean_records.py \
  --input normalized/records.jsonl \
  --included analysis/records_included.jsonl \
  --excluded analysis/records_excluded.jsonl \
  --summary analysis/cleaning_summary.json \
  --max-per-parent 50
```

Exclude off-topic, exact duplicate, too-short, and pure promotional records with explicit reasons. A viral thread cap limits statistical dominance; it does not delete the raw thread. Keep pre-clean, post-clean, and post-cap counts distinct.

### 5. Build and calibrate the taxonomy

Read `references/taxonomy-and-coding.md`. Create a stratified sample, normally 150 records:

```bash
python3 scripts/make_taxonomy_sample.py \
  --input analysis/records_included.jsonl \
  --sample analysis/taxonomy_sample.jsonl \
  --prompt analysis/taxonomy_prompt.md \
  --size 150
```

Keep four stable level-one value domains:

- People and context
- Functional value
- Assurance value
- Experience value

Generate level-two and level-three labels from the sample, then stop for human calibration. Keep sentiment, ownership, funnel stage, severity, brand, product, and vehicle as separate dimensions rather than hiding them inside theme names.

### 6. Annotate and audit

Apply the calibrated taxonomy to included records. Each annotation needs `source_id`, sentiment, level-three tags, ownership signal, funnel stage, severity, and an evidence excerpt copied from that record.

Validate before statistics:

```bash
python3 scripts/validate_annotations.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --taxonomy analysis/taxonomy.json \
  --output analysis/annotation_validation.json \
  --audit-sample analysis/annotation_audit_sample.jsonl
```

Audit a stratified `max(50 records, 5%)` sample across source, brand, rating band, and sentiment. Record reviewed and correct counts in `analysis/audit_result.json`. An unaudited study cannot pass the final gate.

### 7. Run deterministic statistics

Do not ask an LLM to count rows or calculate percentages. Use the bundled script:

```bash
python3 scripts/statistics.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --taxonomy analysis/taxonomy.json \
  --output-dir analysis/statistics
```

The script reports source mix, sentiment by source, overlapping tag frequencies, brand-theme-sentiment cross-tabs, low-rating themes, ownership/funnel signals, and traceable evidence candidates. Every table states its unit and denominator.

### 8. Apply the quality gate

```bash
python3 scripts/quality_gate.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --validation analysis/annotation_validation.json \
  --audit-result analysis/audit_result.json \
  --output analysis/quality_gate.json
```

Use `pass`, `partial`, or `blocked`. Source imbalance, missing URLs, low annotation coverage, failed traceability, and missing audit evidence must remain visible. Never turn a large row count into a quality claim.

### 9. Generate the evidence report

```bash
python3 scripts/generate_report.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --statistics analysis/statistics/statistics.json \
  --quality-gate analysis/quality_gate.json \
  --taxonomy analysis/taxonomy.json \
  --title "UTV Cab Fan Omnichannel VOC" \
  --output reports/voc_report.html

python3 scripts/validate_report.py \
  --report reports/voc_report.html \
  --records analysis/records_included.jsonl
```

Lead with the decision, actions, confidence, and veto conditions. Then show source-specific findings, positive themes, pain points, anomaly signals, behavioral segments, evidence chains, methods, missingness, and limitations. Quote briefly and link to the original source.

## Output contract

Deliver:

1. Study contract and source plan.
2. Raw-data manifest and channel failure log.
3. Normalized, included, and excluded record files.
4. Calibrated taxonomy, annotation file, validation, and audit sample/result.
5. Deterministic statistics with denominators.
6. Quality-gate result.
7. Source-traceable HTML report and a concise decision summary.

Never deliver raw secrets, cookies, access tokens, private group content, unredacted author identifiers, or claims that exceed the quality gate.

For any public or shared package, include the repository's `NOTICE.md`: technical visibility is not permission for automation or commercial reuse, and no software license grants rights to third-party content, trademarks, personal data, or datasets.

## Failure handling

| Symptom | Action |
|---|---|
| CAPTCHA, checkpoint, re-login, 403, or 429 | Stop that browser route, preserve the manifest, and use an authorized fallback if available |
| Search returns empty or unstable pages | Try one standard visible navigation path; then record `blocked` or `empty`, not repeated URL guessing |
| Official API unavailable | Keep the channel as a small supervised browser sample or mark it unavailable; do not bypass controls |
| One viral post dominates | Apply the predeclared parent cap and report both original and capped counts |
| Promotional or off-topic noise | Exclude with a reason and review a sample of exclusions |
| Tags drift across batches | Freeze a taxonomy version, validate unknown tags, and recalibrate deliberately |
| AI label errors | Expand the stratified audit, correct the coding guide, and rerun annotations before statistics |
| Cross-channel findings conflict | Report the conflict by source and evidence class; do not average it away |
| Quality gate misses | Mark the study `partial`, state the missing evidence, and recommend the smallest useful append |

## Resource map

- `references/source-playbooks.md`: platform roles, browser/API order, limits, and stop rules.
- `references/sampling-strategy.md`: decision-depth sample tiers, channel allocation, parent floors, and append rules.
- `references/schema.md`: canonical record, annotation, taxonomy, and audit formats.
- `references/taxonomy-and-coding.md`: value hierarchy, coding rules, and audit method.
- `references/reporting-and-quality.md`: denominators, gates, report structure, and decision safeguards.
