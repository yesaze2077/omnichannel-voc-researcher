# Rating recovery research contract

Use this profile when the business decision is to recover or protect a marketplace product rating. The displayed rating is an outcome metric, not a VOC label. Research should identify controllable drivers and define a measurement loop; it must not promise a rating change or encourage review manipulation.

## 1. Freeze the baseline before collection

Save a timestamped snapshot with:

- marketplace, listing URL, ASIN, visible parent rating, and visible rating count;
- whether the value is parent-level or child-variation-level and the known variation map;
- visible star histogram and recent review list when available;
- capture method, access state, and whether each field is live, cached, user-observed, or missing;
- current target, hold period, and guardrails.

Do not silently combine a user-observed live rating with a cached rating count. If Amazon does not expose a current field, keep it `pending_live_verification`. Amazon's displayed rating is not a simple arithmetic average, so arithmetic scenarios are sensitivity illustrations only.

## 2. Define the decision and outcome contract

Example decision question: `Which product, setup, listing, and support changes should be prioritized to move the displayed parent rating from 4.2 to at least 4.3 and hold it for 28 days without worsening returns or support contacts?`

Separate:

- leading signals: recurrence of low-star themes, setup success, support recovery, return reasons, and expectation mismatch;
- outcome: displayed parent rating and rating count;
- guardrails: return/refund rate, support-contact rate, repeated-defect share, and policy compliance;
- proof boundary: a post-change time series or controlled rollout is needed to establish improvement. VOC alone ranks hypotheses.

## 3. Keep evidence classes separate

Use these product relations:

- `target_model_direct`: the named model or its confirmed child variation;
- `adjacent_brand_model`: another model from the same brand;
- `category`: the same product category without confirmed model ownership;
- `competitor`: a named competing product;
- `official_context`: manual, help page, listing claim, or brand response;
- `editorial_context`: creator, affiliate, retailer, or editorial material without user ownership evidence.

Only `target_model_direct` can establish a confirmed model-specific issue. Adjacent and category evidence may define search terms, risk hypotheses, or proof requirements; it must not be rewritten as a confirmed target-model defect.

## 4. Stratify rating-bearing evidence

For target-model Amazon and other rating-bearing reviews, preserve:

- rating band: 1, 2, 3, 4, and 5 stars;
- recent window, primary 24-month window, and older durability evidence;
- verified-purchase or claimed ownership signal;
- parent/child variation and platform/workflow when visible;
- review update, seller/brand response, replacement, refund, or successful recovery;
- original rating distribution metadata separately from sampled review text.

Deep default floors are 30 target-model direct records, 20 rating-bearing direct records, 10 low-star direct records, 10 recent direct rating records, and two direct-evidence source types. If the public universe is smaller, preserve attempts and stop only under the two-expansion saturation rule.

Do not build a complaint-only matrix. Keep broad evaluation, four-star friction, five-star success/recovery, and low-star failure searches in the frozen design. Negative/problem queries normally remain below 35% of the matrix.

## 5. Code the rating-driver tree

Every target-model low-star record needs one primary `rating_driver` and may have secondary themes:

1. `product_performance_or_defect` — confirmed output, mechanical, electrical, durability, or reliability failure.
2. `setup_or_workflow_friction` — calibration, connection, driver/app, platform, media, or operating sequence friction.
3. `expectation_or_listing_mismatch` — the product works within its boundary but the buyer expected an unsupported workflow, feature, compatibility, quality level, or included item.
4. `support_or_recovery` — response speed, troubleshooting, replacement, refund, warranty, or successful save.
5. `not_enough_evidence` — the text does not safely support a causal classification.

Never force an ambiguous review into a product-defect bucket. Record user remedy actions separately: restart, reconnect, reinstall, recalibrate, change media, change settings, contact support, replace, return, or abandon.

## 6. Build the search matrix around the driver tree

Core round 1 must include:

- product/model baseline reviews and owner experience;
- recent low-star and return language;
- platform workflows and compatibility;
- setup, calibration, media, print/output quality, reliability, and durability;
- expectation phrases such as `AirPrint`, `driver free`, `no app`, or other category-specific assumptions;
- support, replacement, warranty, and review-update language;
- competitor comparisons and switching.

After cleaning round 1, build round 2 from uncovered driver cells, unresolved source conflicts, missing workflows, and weak direct-model evidence. Then build targeted-completion queries for Facebook, TikTok, Instagram, X, review platforms, independent sites, app stores, and any remaining vertical-community gaps.

## 7. Keep interventions compliant

Allowed intervention lanes:

- product and quality assurance;
- firmware/app/driver and setup flow;
- packaging, quick-start guidance, listing expectation setting, FAQ, and proof;
- customer support triage, troubleshooting, replacement, refund, and follow-up;
- marketplace-native neutral review-request tools when currently permitted.

Do not recommend incentives, selective positive-review requests, review gating, suppression, compensation conditional on review change, or asking a buyer to edit/remove a review. Verify current marketplace policy before implementation.

## 8. Report and measurement contract

The report should lead with:

- current baseline and evidence status;
- the top controllable rating drivers, each with count, denominator, source strata, confidence, and evidence chain;
- a priority matrix of severity, recurrence, controllability, implementation lead time, and proof requirement;
- 0–14 day containment, 15–45 day correction, and 46–90 day validation actions;
- what can be fixed through listing/onboarding versus what requires product or support change;
- required first-party inputs still missing.

Do not calculate “reviews needed to reach 4.3” as a forecast. If useful, show a clearly labelled simple-average sensitivity range and state that Amazon's displayed rating may behave differently. Success is confirmed only after the displayed rating meets the target for the declared hold period while guardrails remain within bounds.

## 9. Preserve scope and delivery gates

Rating-specific floors, windows, direct-source roles, and quality thresholds belong in the frozen scope. A login/connection-verification wait does not allow dropping Amazon, review platforms, or app stores. Follow [execution-and-delivery.md](execution-and-delivery.md) for direct user assistance and resume at the saved checkpoint. Continue independent sources while a route waits. Unknown yield is not saturation.

Both custom and bundled rating reports require fresh unified acceptance with current input hashes. A baseline card or preliminary driver tree may be a snapshot with `task_complete=false`; it does not complete the requested study. These workflow gates do not weaken any rating-recovery evidence, policy, or outcome-proof requirements above.
