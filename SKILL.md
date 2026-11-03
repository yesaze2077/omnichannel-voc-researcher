---
name: omnichannel-voc-researcher
description: Run auditable multi-channel Voice of Customer research across YouTube, public vertical communities, Old Reddit, Amazon, X, TikTok, Facebook, Instagram, independent review platforms, independent/brand-store review pages, and first-party customer data. Use this skill whenever the user asks for VOC, review mining, social listening, brand reputation, product pain points, competitor feedback, listing inputs, customer-language research, or cross-platform consumer research, even when they mention only one or two channels. It turns research questions into pilot, broad, gap-driven, and targeted-completion search matrices; prevents a large core sample from silently replacing required supplementary channels; plans browser-assisted samples and authorized API fallbacks; normalizes evidence; audits a taxonomy; computes deterministic statistics; and produces a source-traceable report without merging incompatible denominators.
---

# Omnichannel VOC Researcher

Version 1.3.0 · 2026-11-03

Runtime: Python 3.10+ and the standard library. Browser collection needs a user-authorized browser tool. Large YouTube studies may use `youtube-intelligence-researcher` when installed.

Build a decision-grade evidence package, not a pile of comments. Keep collection, cleaning, coding, statistics, interpretation, and recommendation as separate stages so every conclusion can be traced to source records and reproduced.

## Non-negotiable boundaries

This skill is shared only for noncommercial learning, personal research, teaching, and technical exchange. The software license does not authorize access to or reuse of third-party platform content or data. Every live study must separately satisfy applicable law, platform terms, API policies, access controls, privacy duties, and content rights.

1. Define the business decision before collecting data. A category study, brand reputation audit, listing rewrite, and defect investigation need different samples.
2. Choose a post-clean total and channel portfolio from the decision and research depth before collection. Never default to equal per-channel targets.
3. Keep denominators separate by source, record type, and evidence class. Never report one blended "internet sentiment rate" across Amazon ratings, Reddit comments, X posts, and YouTube comments.
4. Preserve `source_id`, source URL, collection time, access mode, and exclusion reason. Every quoted claim must resolve to a retained record.
5. Treat browser access to X, TikTok, Facebook, and Instagram as supervised supplementary research. Do not bypass CAPTCHA, checkpoints, access controls, rate limits, private spaces, or login requirements. Do not rotate accounts, identities, fingerprints, or proxies to evade controls.
6. Browser collection is read-only: no likes, follows, comments, messages, purchases, or account changes. On a normal login or connection-verification challenge, stop automated interaction, ask the user to complete it directly in the browser, save the checkpoint, and resume only after user confirmation plus visible-body verification. Never solve or bypass challenges. A real 403/429, denied access, rate limit, private-space boundary, or failed verification stops the affected route.
7. Follow the user's preferred route for high-risk social sources: browser-assisted sampling first; if it is blocked and an authorized official interface exists, record the failure and switch to that interface. Do not silently expand a browser sample into unattended bulk collection.
8. Do not publish raw author identifiers. Hash identifiers used for deduplication and remove them from final reports unless a valid research need and authorization are documented.
9. Preserve unsupported, unbalanced, or incomplete evidence as an unfinished working state. Use `partial` only when the unified acceptance result permits it; a partial report does not complete the original task. Page visibility does not establish permission for recurring commercial automation.
10. Treat channel plans as `floor`, `goal`, and `cap`. The goal budgets collection but never truncates valid evidence while the total study remains short.
11. A normal login wall is `waiting_for_user_login`; a connection challenge is `waiting_for_user_verification`. Ask for direct user action without requesting credentials, preserve query/page/parent/position, and continue independent executable work. Neither wait counts as zero yield or source exhaustion.
12. Record source authorization as `unconfirmed`, `user_confirmed`, or `documented`, plus its approved read-only scope. A user's confirmation is sufficient to resume the stated route but is not evidence that broader API, private-space, recurring, or write access is authorized.
13. Separate `core sample sufficiency` from `omnichannel completion`. Passing YouTube, Reddit, Amazon, or total-row gates ends broad collection only; it never waives a predeclared Facebook, TikTok, vertical-community, review-platform, independent-site, or other required coverage cell.
14. Run small controlled social and independent-site samples after preliminary analysis so queries can target the observed objections, conflicts, and missing user language. This sequencing reduces exposure and noise; it does not make those sources optional.
15. Freeze scope before collection. Required families, roles, member coverage, record/parent floors, and quality thresholds cannot be reduced after results are seen without an explicit user decision recorded by `freeze_scope.py`. Editing a plan, relabeling a channel case-only, or renaming a deliverable is not approval.
16. A local access, taxonomy-calibration, or human-audit wait pauses only dependent work. Continue other authorized collection, cleaning, traceability checks, and preparation; do not end the task while executable required work remains.
17. All final artifacts, including custom HTML and the bundled generator, must use the same fresh `delivery_acceptance.json`. A progress snapshot is allowed with `task_complete=false`; it never replaces the requested deliverable. Read [execution-and-delivery.md](references/execution-and-delivery.md) for scope, access events, resumption, and acceptance.

## Choose the research mode

| Mode | Decision supported | Primary evidence |
|---|---|---|
| `category-opportunity` | What unmet need is worth solving? | scenes, workarounds, alternatives, severity |
| `brand-reputation` | What drives trust, complaints, and repurchase? | owned-use evidence, service, durability, comparisons |
| `product-improvement` | What should product and QA fix first? | defects, fitment, safety, recurrence, low ratings |
| `listing-content` | What should a listing prove and explain? | objections, terminology, fitment, proof needs, FAQs |
| `rating-recovery` | Which controllable drivers should be changed to recover a product rating without manipulating reviews? | recent low-star drivers, expectation gaps, setup friction, product defects, service recovery |
| `competitor-intel` | Where do competitors win or fail? | brand-by-theme evidence with matched contexts |
| `content-strategy` | What content helps users decide or succeed? | questions, misconceptions, installation and use scenes |

## Workflow

### 1. Create the study contract

Read `references/sampling-strategy.md` and `references/source-universe.md`. For `rating-recovery`, also read `references/rating-recovery.md`. Write the decision question, research mode/depth, market, category definition, brands/products, time window, exclusions, post-clean total, per-source record and parent floors, report audience, quality thresholds, and stop conditions before collection. Create `source_universe.json` before `source_plan.json`: every relevant source family must be marked `required`, `relevant_case_only`, `optional`, or `excluded_with_reason`. This is the no-silent-omission gate.

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

For rating recovery, freeze the visible parent rating, rating count, capture time, ASIN/listing URL, and parent/child scope before interpreting change. Keep sampled review text separate from the product's full rating distribution. VOC prioritizes interventions; it does not prove that the displayed rating will move.

Default sample tiers are planning aids, not a 350-record requirement for every teaching task. Before collection, a bounded teaching or pilot task may declare a smaller justified target and evidence limits while preserving every promised channel. Do not reduce scope or thresholds after seeing shortfalls. Read `references/reporting-and-quality.md` before freezing the contract.

`init_study.py` derives the source plan from the contract and creates a scope lock. Complete the source-family inventory and inspect the generated contract before collecting. To finalize pre-collection edits, or to record a later actual user-approved scope revision, use the explicit freeze workflow:

```bash
python3 scripts/freeze_scope.py \
  --contract study_contract.json \
  --source-plan source_plan.json \
  --before-collection \
  --output scope_lock.json
```

`--before-collection` only replaces a lock when no nonempty data files exist under raw, normalized, or analysis. After collection starts, re-freezing requires `--approval-ref user:<actual-decision-reference>` and retains scope history. A fabricated approval reference is not authorization.

### 2. Plan evidence by channel

Read `references/source-playbooks.md` and create a source plan. Use channels for the evidence they are good at instead of trying to collect the same volume everywhere.

- Make YouTube, public vertical forums, and Old Reddit the core evidence pool for deep public-web studies. Control both retained records and independent videos/threads.
- For YouTube, use the official Data API first for public search, metadata, top-level comments, and replies within quota. Delegate to `youtube-intelligence-researcher`, then recover public captions in its separate restartable transcript stage and normalize the outputs here.
- Keep YouTube raw candidate goals separate from retained VOC goals. For a default deep study, plan at least 3,000 raw comment/reply candidates across at least 120 relevant videos, then clean and cap them into the declared post-clean allocation.
- Do not claim that an API key can download arbitrary public captions. The official caption download endpoint requires permission to edit the video; public transcript recovery remains a separate mechanism.
- When Reddit access is authorized, prefer Old Reddit in the authorized browser and keep modern Reddit as a one-step page fallback. Preserve the authorization label, access mode, query, page, thread, and failure manifests; never store credentials or session data.
- For X, use supervised browser sampling first; when blocked or when an authorized structured retrieval is approved, use the official API and record credit usage.
- Treat public vertical forums and commerce communities as a source family planned from the start, not an incidental fallback. A deep study normally needs multiple domains and independent threads; if the relevant public universe is smaller, document search saturation rather than silently omitting the family.
- After core round-1 cleaning and preliminary analysis, run a targeted-completion lane for each enabled high-risk social source. The full-study interpretability default is 30 retained records and 10 independent parents per channel, normally 3-6% of the total; a smaller teaching contract may predeclare lower collection floors with example-only interpretation, while retaining every promised channel. Below either floor, use examples only and exclude the channel from agreement claims, but keep the study `needs_append`, `waiting_for_user_login`, or `partial` when that channel was declared required.
- Include third-party review platforms such as Trustpilot or Sitejabber when brand trust, support, fulfillment, or warranty affects the decision. Keep brand-level service reviews separate from model-level product evidence.
- Include relevant independent sites and brand/store review pages when they contain real user reviews, Q&A, or comments. Store editorial, affiliate, official, and retailer copy as contextual evidence rather than VOC.
- Treat Facebook, TikTok, Instagram, and X as small supervised targeted supplements unless an authorized first-party API covers the requested data. Their small size is a risk control, not a reason to omit them after the core sample passes.
- Import customer support, returns, product reviews, surveys, and site search as first-party evidence with their own denominators.

Store collection manifests and failure states even when a channel returns zero records.

### 3. Build and execute the search rounds

Read `references/search-and-append.md`. A sample allocation is not a search plan: translate the decision into evidence questions, then create a source-aware matrix before collection.

1. Run a 10-15 query pilot for each core search source to learn vocabulary, ambiguity, brands, communities, and reject terms.
2. Freeze a balanced round-1 matrix. For a deep YouTube study this commonly means 50-65 formal queries with quota headroom; build a comparable product × intent × community matrix for Reddit and forums.
3. Append rather than overwrite. Preserve query IDs, pages, parents, raw/retained counts, failure states, and exact search terms.
4. Clean round 1 and calibrate the preliminary taxonomy before designing round 2.
5. Add narrow queries only for missing scenes, brands, models, workflows, ownership classes, objections, source types, or unresolved conflicts.
6. Build a targeted-completion matrix for the required small social, review-platform, independent-site, and remaining vertical-community cells. Base its queries on the preliminary findings rather than copying the broad core matrix.
7. In `rating-recovery` mode, stratify target-model direct evidence by recent period, rating band, verified/owned-use signal, variation, and driver type. Code each low-star record as product performance/defect, setup/workflow friction, expectation/listing mismatch, support/recovery, or insufficient evidence.
8. Calculate per-query and per-round yield. Unknown counts remain null, not zero. Saturation requires two consecutive successful, measured targeted expansions for each unfinished required source; failed, unattempted, verification-waiting, or incompletely measured rounds cannot qualify.

```bash
python3 scripts/build_search_matrix.py \
  --category "category" \
  --mode listing-content \
  --stage pilot \
  --sources youtube reddit \
  --core-terms "category term,common synonym" \
  --reddit-entrypoint old \
  --reddit-authorization-status user_confirmed \
  --output search/pilot.jsonl

python3 scripts/query_coverage.py \
  --matrix search/all_queries.jsonl \
  --prior raw/youtube/search_terms.json \
  --source youtube \
  --output search/youtube_seed_query_coverage.json

python3 scripts/round_yield.py \
  --matrix search/all_queries.jsonl \
  --attempts rounds/attempts.jsonl \
  --output rounds/round_yield.json

python3 scripts/gap_analysis.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --requirements search/evidence_requirements.json \
  --output search/gap_analysis.json

python3 scripts/collection_state.py \
  --acceptance analysis/delivery_acceptance.json \
  --output rounds/workflow_state.json
```

Generate the acceptance receipt in step 9 before resolving `state`. Follow its `actionable_sources`, `waiting_sources`, and `next_action`: a local wait does not stop other required work. `needs_append`, `waiting_for_user_login`, and `waiting_for_user_verification` remain active states. A core-channel `pass` cannot override an unfinished required completion lane.

### 4. Normalize all records

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

### 5. Clean, deduplicate, and cap concentration

```bash
python3 scripts/clean_records.py \
  --input normalized/records.jsonl \
  --included analysis/records_included.jsonl \
  --excluded analysis/records_excluded.jsonl \
  --summary analysis/cleaning_summary.json \
  --max-per-parent 50
```

Exclude off-topic, exact duplicate, too-short, and pure promotional records with explicit reasons. A viral thread cap limits statistical dominance; it does not delete the raw thread. Keep pre-clean, post-clean, and post-cap counts distinct.

### 6. Build and calibrate the taxonomy

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

Generate level-two and level-three labels from the sample, then ask for human calibration before dependent full annotation. Continue independent collection, cleaning, deduplication, and evidence checks while waiting. Keep sentiment, ownership, funnel stage, severity, brand, product, and vehicle as separate dimensions rather than hiding them inside theme names.

### 7. Annotate and audit

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

Audit a stratified `min(N, max(50, ceil(5% of N)))` sample across source, brand, rating band, and sentiment, where N is the included record count. Record actual reviewed/correct counts and human review evidence in `analysis/audit_result.json`; never invent a human audit. While awaiting review, continue independent work. An unaudited study cannot pass final acceptance.

### 8. Run deterministic statistics

Do not ask an LLM to count rows or calculate percentages. Use the bundled script:

```bash
python3 scripts/statistics.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --taxonomy analysis/taxonomy.json \
  --output-dir analysis/statistics
```

The script reports source mix, sentiment by source, overlapping tag frequencies, brand-theme-sentiment cross-tabs, low-rating themes, ownership/funnel signals, and traceable evidence candidates. Every table states its unit and denominator.

### 9. Apply the quality gate

```bash
python3 scripts/quality_gate.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --validation analysis/annotation_validation.json \
  --audit-result analysis/audit_result.json \
  --config study_contract.json \
  --round-summary rounds/round_yield.json \
  --output analysis/quality_gate.json
```

The quality gate describes evidence quality; it is not delivery authorization. Reconcile it with locked scope, actual source coverage, access checkpoints, current records, human audit, and measured rounds:

```bash
python3 scripts/delivery_acceptance.py \
  --contract study_contract.json \
  --scope-lock scope_lock.json \
  --source-plan source_plan.json \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --quality-gate analysis/quality_gate.json \
  --audit-result analysis/audit_result.json \
  --round-summary rounds/round_yield.json \
  --statistics analysis/statistics/statistics.json \
  --taxonomy analysis/taxonomy.json \
  --output analysis/delivery_acceptance.json
```

Use that receipt for `collection_state.py` and every renderer/validator. It reports `task_complete`, `final_report_allowed`, `snapshot_allowed`, scope errors, required shortfalls, actionable/waiting sources, and the next action. Incomplete coverage or review cannot be concealed by a global quality PASS. Input hashes are rechecked at rendering; recompute acceptance after any bound input changes.

### 10. Generate the evidence report

When `visual-report-skill` is available, load it before report production and follow `references/visual-reporting-integration.md`. The final HTML report is a decision interface, not a styled data dump:

1. Build `reports/report_ir.json` from deterministic statistics, quality/completion gates, coverage ledger, evidence IDs, and the decision summary.
2. Default to the `voc_insight_report` template and `voc_insight` archetype unless another documented archetype better fits the audience.
3. Enforce progressive disclosure: L0 executive decisions and status, L1 actions and source coverage, L2 evidence and comparisons, L3 method, denominators, missingness, and traceability.
4. Show `core evidence readiness` and `omnichannel completion` as separate status indicators. Never display a global PASS when required completion cells are missing.
5. Run structural, report-IR, and browser QA at desktop and narrow widths. Preserve a visual QA log.

The bundled `generate_report.py` is an evidence-traceable fallback skeleton. It is not by itself proof of visual-report quality when `visual-report-skill` is available.

```bash
python3 scripts/generate_report.py \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --statistics analysis/statistics/statistics.json \
  --quality-gate analysis/quality_gate.json \
  --taxonomy analysis/taxonomy.json \
  --acceptance analysis/delivery_acceptance.json \
  --artifact-kind final \
  --title "UTV Cab Fan Omnichannel VOC" \
  --output reports/voc_report.html

python3 scripts/validate_report.py \
  --report reports/voc_report.html \
  --records analysis/records_included.jsonl \
  --acceptance analysis/delivery_acceptance.json
```

For progress material, select `--artifact-kind snapshot`; its title and body must display `PROGRESS SNAPSHOT` and `task_complete=false`, plus current state, unmet scope, and next action. Custom reports must embed the same `delivery-acceptance` JSON marker, call the same acceptance/validation flow, and bind the same inputs; changing the filename or layout cannot bypass final acceptance. A permitted saturation-limited `partial` final report still has `task_complete=false`.

Lead with the decision, actions, confidence, and veto conditions. Then show source-specific findings, positive themes, pain points, anomaly signals, behavioral segments, evidence chains, methods, missingness, and limitations. Quote briefly and link to the original source.

## Output contract

Deliver:

1. Study contract, scope lock/history, source-access authorization manifest/checkpoints, and floor/goal/cap source plan.
2. Search matrices, targeted-completion matrix, round-yield summary, workflow state, raw-data manifest, and channel failure log.
3. Normalized, included, and excluded record files.
4. Calibrated taxonomy, annotation file, validation, and audit sample/result.
5. Deterministic statistics with denominators.
6. Quality-gate result and fresh unified delivery-acceptance receipt.
7. Source-traceable visual HTML report, `reports/report_ir.json`, visual QA log, and a concise decision summary.

Never deliver raw secrets, cookies, access tokens, private group content, unredacted author identifiers, or claims that exceed the quality gate.

For any public or shared package, include the repository's `NOTICE.md`: technical visibility is not permission for automation or commercial reuse, and no software license grants rights to third-party content, trademarks, personal data, or datasets.

## Failure handling

| Symptom | Action |
|---|---|
| Normal login wall or expired session | Save checkpoint, set `waiting_for_user_login`, ask the user to sign in directly, verify readable content after confirmation, and resume the same bounded route; continue independent work |
| Authorized Old Reddit page is missing or incomplete | Record the Old Reddit attempt, try the equivalent normal Reddit page once, and preserve distinct access modes; do not loop through URL variants |
| Connection verification or CAPTCHA/checkpoint challenge | Stop automated interaction; ask the user to complete it directly, save `verification_required`, and resume only after confirmed user action plus visible-body verification; never solve or bypass it |
| Real 403/429, denied access, failed verification, or explicit rate limit | Stop the restricted route, preserve the reason and checkpoint; use only an authorized fallback and continue other executable work |
| Search returns empty or unstable pages | Try one standard visible navigation path; then record `blocked` or `empty`, not repeated URL guessing |
| Official API unavailable | Keep the channel as a small supervised browser sample or mark it unavailable; do not bypass controls |
| One viral post dominates | Apply the predeclared parent cap and report both original and capped counts |
| Promotional or off-topic noise | Exclude with a reason and review a sample of exclusions |
| Tags drift across batches | Freeze a taxonomy version, validate unknown tags, and recalibrate deliberately |
| AI label errors | Expand the stratified audit, correct the coding guide, and rerun annotations before statistics |
| Cross-channel findings conflict | Report the conflict by source and evidence class; do not average it away |
| Quality gate misses before saturation | Set `needs_append` and run the smallest gap-driven append; do not issue a final report |
| Core channels pass but required social/forum/review-site cells remain empty | Keep `needs_append` or `waiting_for_user_login`; broad sample volume cannot be reallocated over a required coverage family |
| Two successful measured targeted expansions each add less than 5% per unfinished required source | Let unified acceptance decide whether a limited `partial` report is allowed; unknown/failed/waiting rounds do not qualify, and `task_complete` remains false |
| Human calibration or audit is pending | Pause dependent annotation or final acceptance only; continue independent collection and checks |
| A custom report or old receipt appears to pass | Recompute unified acceptance; reject scope drift, stale hashes, and unsupported completion claims |

## Resource map

- `references/source-playbooks.md`: platform roles, browser/API order, limits, and stop rules.
- `references/sampling-strategy.md`: decision-depth sample tiers, channel allocation, parent floors, and append rules.
- `references/search-and-append.md`: pilot/formal/gap matrices, round manifests, yield calculation, login waits, and saturation.
- `references/schema.md`: canonical record, annotation, taxonomy, and audit formats.
- `references/taxonomy-and-coding.md`: value hierarchy, coding rules, and audit method.
- `references/reporting-and-quality.md`: denominators, gates, report structure, and decision safeguards.
- `references/source-universe.md`: required source-family inventory, evidence roles, access classification, and no-silent-omission rules.
- `references/visual-reporting-integration.md`: Report IR, visual template, progressive disclosure, status, traceability, and responsive QA contract.
- `references/rating-recovery.md`: baseline freeze, rating-driver taxonomy, sampling strata, compliant intervention boundary, and measurement contract.

- `references/execution-and-delivery.md`: scope freeze/revision, user-assisted access checkpoints and resumption, independent progress, and unified artifact acceptance.
