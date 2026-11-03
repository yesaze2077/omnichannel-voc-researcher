# Canonical Schemas

## Normalized record

Store records as UTF-8 JSONL. Required fields are `source_id`, `source`, `access_mode`, `record_type`, `text`, `source_url`, and `collected_at`. Empty values remain empty strings; do not invent them.

```json
{
  "source_id": "amazon_4a1d3f6d71c2b450",
  "source": "amazon",
  "access_mode": "browser_assisted",
  "native_id": "R123",
  "parent_id": "B0EXAMPLE",
  "record_type": "review",
  "published_at": "2026-07-01",
  "collected_at": "2026-08-12T08:30:00Z",
  "text": "The fan moves air but the bracket needed modification.",
  "source_url": "https://example.invalid/review/R123",
  "author_hash": "d73a2f0911d42e1c",
  "brand": "ExampleBrand",
  "product": "Dual cab fan",
  "vehicle": "Polaris RZR",
  "rating": 3.0,
  "verified_purchase": true,
  "engagement_count": 4,
  "engagement_type": "helpful_votes",
  "source_type": "customer",
  "query": "utv cab fan",
  "raw_ref": "amazon_reviews.csv:2",
  "collection_status": "collected",
  "exclusion_reason": "",
  "query_id": "q_example",
  "round": "pilot",
  "dimension": "workflow_platform",
  "scope": "EtsySellers",
  "authorization_status": "user_confirmed",
  "product_relation": "category",
  "evidence_type": "user_comment",
  "time_bucket": "last_24_months",
  "selection_mode": "frozen_matrix"
}
```

`source_id` must be stable for the same source record. Prefer a platform native ID. Otherwise hash source, URL, publication time, and normalized text. `author_hash` is for private deduplication only and should not appear in the final report.

The normalizer passes through only a safe whitelist of collection-context fields, including `query_id`, `round`, `dimension`, `scope`, authorization status, source relation/evidence class, time bucket, selection mode, subreddit, parent URL, visible comment context, country/language, and variant labels. It never automatically copies credentials, cookies, tokens, raw author names, or arbitrary source fields. A bridge may supply a stable `source_id` and original `collected_at`; both are preserved.

## Taxonomy

Use stable ASCII IDs and human-readable labels. Four level-one IDs are fixed; level-two and level-three nodes are study-specific.

```json
{
  "version": "1.0",
  "category": "UTV cab cooling fans",
  "level_1": [
    {
      "id": "people_context",
      "label": "People and context",
      "level_2": [
        {
          "id": "use_scene",
          "label": "Use scene",
          "level_3": [
            {
              "id": "trail_stop",
              "label": "Trail stop",
              "definition": "Cooling need while stopped or moving slowly on a trail."
            }
          ]
        }
      ]
    }
  ]
}
```

The four required level-one IDs are:

- `people_context`
- `functional_value`
- `assurance_value`
- `experience_value`

## Annotation

Annotations are one JSONL object per retained record:

```json
{
  "source_id": "amazon_4a1d3f6d71c2b450",
  "sentiment": "negative",
  "level_3_tags": ["fitment", "airflow"],
  "ownership_signal": "owned_use",
  "funnel_stage": "ownership",
  "severity": "medium",
  "evidence_excerpt": "the bracket needed modification",
  "coder": "model-and-human-audit",
  "taxonomy_version": "1.0"
}
```

Allowed dimensions:

- `sentiment`: `positive`, `neutral`, `negative`, `mixed`
- `ownership_signal`: `verified_purchase`, `owned_use`, `claimed_use`, `purchase_intent`, `information_seeking`, `none`
- `funnel_stage`: `awareness`, `consideration`, `purchase`, `installation`, `ownership`, `service`, `repurchase`, `unknown`
- `severity`: `none`, `low`, `medium`, `high`, `safety`

Theme labels overlap. One record may receive multiple level-three tags, so theme percentages do not sum to 100%.

## Audit result

After reviewing the generated audit sample, save:

```json
{
  "audit_type": "human",
  "reviewed": 50,
  "fully_correct": 46,
  "sentiment_correct": 48,
  "theme_correct": 47,
  "evidence_correct": 50,
  "notes": "Corrected fitment versus installation guidance."
}
```

The quality gate uses `fully_correct / reviewed`. Keep dimension-level counts for diagnosis.

## Collection manifest

Every source attempt, including failures, needs a manifest entry:

```json
{
  "source": "facebook",
  "access_mode": "browser_assisted",
  "query": "utv cab fan",
  "started_at": "2026-08-12T08:00:00Z",
  "finished_at": "2026-08-12T08:05:00Z",
  "records_collected": 0,
  "status": "blocked",
  "failure_reason": "standard post search returned Not Found",
  "fallback": "none",
  "notes": "Stopped after two standard paths; no bypass attempted."
}
```

A normal login wall uses a pause state instead of a failure:

```json
{
  "source": "amazon",
  "access_mode": "browser_assisted",
  "query": "label printer calibration reviews",
  "status": "waiting_for_user_login",
  "failure_reason": "",
  "user_action_required": "Sign in directly in the authorized browser, then confirm that collection may resume.",
  "notes": "No credential was requested or handled."
}
```

Query-round attempts use `query_id`, `source`, `round`, discovered/new parent counts, raw/relevant/new-relevant/retained record counts, duplicates, and status. Calculate saturation from saved attempts rather than narrative notes. See `references/search-and-append.md`.

## Frozen scope and access checkpoints

The source plan is derived from the study contract and checked against `scope_lock.json`. The lock protects required status, source roles/members, record and independent-parent floors, and quality thresholds. Budget goals/caps are not permissions to drop required coverage. Use `freeze_scope.py` and retain history; do not hand-edit the lock or invent user-approval references. See [execution-and-delivery.md](execution-and-delivery.md).

Source access events use unique `event_id` values and preserve the available checkpoint: page URL, browser reference, query ID, parent ID, position, and last retained source ID. Supported event names are:

- `verification_required` — automation paused for direct user completion;
- `login_required` — user sign-in needed;
- `resume_confirmed` — actual user-action reference plus visible-body evidence reference both supplied;
- `verification_failed` — assistance did not restore readable content;
- `access_denied` — real denial/rate/access restriction stops the route.

A verification observation is not an empty result. Keep unknown record/yield counts null rather than zero, and do not include credentials or raw account details in event evidence. A resume event retains the saved query/page/position and does not reset the required source allocation.

## Delivery acceptance receipt

Generate `analysis/delivery_acceptance.json` with `delivery_acceptance.py`; do not synthesize or edit it to grant delivery. It binds current input paths and SHA values and reports:

- `task_complete`, `final_report_allowed`, `snapshot_allowed`;
- `scope_valid`, `scope_errors`;
- `channel_coverage`, `required_shortfalls`;
- `actionable_sources`, `waiting_sources`;
- `state`, `next_action`.

All renderers and validators consume this receipt and verify current inputs. A snapshot must visibly show `PROGRESS SNAPSHOT` and `task_complete=false`; an eligible saturation-limited final report remains `partial` with `task_complete=false`. No artifact, title, or legacy quality PASS may independently change these values. Custom HTML must embed the same `delivery-acceptance` JSON marker used by the bundled renderer and pass `validate_report.py --acceptance ...`.

A `--traceability-only` check can inspect legacy evidence-ID links, but is not delivery acceptance and cannot authorize a final report.
