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
  "exclusion_reason": ""
}
```

`source_id` must be stable for the same source record. Prefer a platform native ID. Otherwise hash source, URL, publication time, and normalized text. `author_hash` is for private deduplication only and should not appear in the final report.

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
