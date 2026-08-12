#!/usr/bin/env python3
"""Compute deterministic source-aware VOC statistics and evidence candidates."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import flatten_taxonomy, normalize_space, read_json, read_jsonl, write_csv, write_json


def taxonomy_labels(taxonomy: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    l3_to_l2, l2_labels, _ = flatten_taxonomy(taxonomy)
    l3_labels: dict[str, str] = {}
    for level_1 in taxonomy.get("level_1", []):
        for level_2 in level_1.get("level_2", []):
            for level_3 in level_2.get("level_3", []):
                tag_id = normalize_space(level_3.get("id"))
                if tag_id:
                    l3_labels[tag_id] = normalize_space(level_3.get("label")) or tag_id
    return l3_to_l2, l2_labels, l3_labels


def pct(count: int, denominator: int) -> float:
    return round(count / denominator * 100.0, 2) if denominator else 0.0


def numeric(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--taxonomy", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    records = read_jsonl(Path(args.records))
    annotations = read_jsonl(Path(args.annotations))
    taxonomy = read_json(Path(args.taxonomy))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records_by_id = {normalize_space(row.get("source_id")): row for row in records}
    annotations_by_id = {normalize_space(row.get("source_id")): row for row in annotations}
    l3_to_l2, l2_labels, l3_labels = taxonomy_labels(taxonomy)

    source_counts = Counter(normalize_space(row.get("source")) or "unknown" for row in records)
    access_counts = Counter(
        (normalize_space(row.get("source")) or "unknown", normalize_space(row.get("access_mode")) or "unknown")
        for row in records
    )
    sentiment_by_source: Counter[tuple[str, str]] = Counter()
    tag_sentiment: Counter[tuple[str, str]] = Counter()
    tag_record_ids: defaultdict[str, set[str]] = defaultdict(set)
    brand_l2_sentiment: Counter[tuple[str, str, str]] = Counter()
    low_rating_tags: Counter[str] = Counter()
    ownership_counts: Counter[str] = Counter()
    funnel_counts: Counter[str] = Counter()
    severity_counts: Counter[str] = Counter()

    evidence_candidates: list[dict[str, Any]] = []
    severity_rank = {"safety": 5, "high": 4, "medium": 3, "low": 2, "none": 1}
    for source_id, annotation in annotations_by_id.items():
        record = records_by_id.get(source_id)
        if not record:
            continue
        source = normalize_space(record.get("source")) or "unknown"
        brand = normalize_space(record.get("brand")) or "unbranded"
        sentiment = normalize_space(annotation.get("sentiment")) or "unlabeled"
        ownership = normalize_space(annotation.get("ownership_signal")) or "none"
        funnel = normalize_space(annotation.get("funnel_stage")) or "unknown"
        severity = normalize_space(annotation.get("severity")) or "none"
        sentiment_by_source[(source, sentiment)] += 1
        ownership_counts[ownership] += 1
        funnel_counts[funnel] += 1
        severity_counts[severity] += 1
        tags = [normalize_space(tag) for tag in annotation.get("level_3_tags", []) if normalize_space(tag)]
        for tag in set(tags):
            tag_sentiment[(tag, sentiment)] += 1
            tag_record_ids[tag].add(source_id)
            l2_id = l3_to_l2.get(tag, "unknown")
            brand_l2_sentiment[(brand, l2_id, sentiment)] += 1
            rating = numeric(record.get("rating"))
            if rating is not None and rating <= 2:
                low_rating_tags[tag] += 1
        engagement = numeric(record.get("engagement_count")) or 0.0
        evidence_candidates.append(
            {
                "source_id": source_id,
                "source": source,
                "brand": brand,
                "sentiment": sentiment,
                "severity": severity,
                "tags": tags,
                "rating": record.get("rating", ""),
                "source_url": record.get("source_url", ""),
                "evidence_excerpt": annotation.get("evidence_excerpt", ""),
                "engagement_count": record.get("engagement_count", ""),
                "_rank": (severity_rank.get(severity, 0), engagement),
            }
        )

    labeled_count = len(set(records_by_id) & set(annotations_by_id))
    tag_rows: list[dict[str, Any]] = []
    for tag in sorted(tag_record_ids, key=lambda item: (-len(tag_record_ids[item]), item)):
        row: dict[str, Any] = {
            "level_3_id": tag,
            "level_3_label": l3_labels.get(tag, tag),
            "level_2_id": l3_to_l2.get(tag, "unknown"),
            "level_2_label": l2_labels.get(l3_to_l2.get(tag, ""), l3_to_l2.get(tag, "unknown")),
            "record_count": len(tag_record_ids[tag]),
            "pct_of_labeled_records": pct(len(tag_record_ids[tag]), labeled_count),
        }
        for sentiment in ("positive", "neutral", "negative", "mixed"):
            row[sentiment] = tag_sentiment[(tag, sentiment)]
        tag_rows.append(row)

    source_sentiment_rows = [
        {
            "source": source,
            "sentiment": sentiment,
            "count": count,
            "pct_of_source_records": pct(count, source_counts[source]),
        }
        for (source, sentiment), count in sorted(sentiment_by_source.items())
    ]
    brand_rows = [
        {
            "brand": brand,
            "level_2_id": l2_id,
            "level_2_label": l2_labels.get(l2_id, l2_id),
            "sentiment": sentiment,
            "record_tag_count": count,
        }
        for (brand, l2_id, sentiment), count in sorted(brand_l2_sentiment.items())
    ]
    low_rating_rows = [
        {
            "level_3_id": tag,
            "level_3_label": l3_labels.get(tag, tag),
            "low_rating_record_count": count,
        }
        for tag, count in low_rating_tags.most_common()
    ]

    evidence_candidates.sort(key=lambda row: (row["_rank"][0], row["_rank"][1], row["source_id"]), reverse=True)
    for row in evidence_candidates:
        row.pop("_rank", None)

    statistics = {
        "denominators": {
            "included_records": len(records),
            "labeled_records": labeled_count,
            "rating_bearing_records": sum(numeric(row.get("rating")) is not None for row in records),
            "verified_purchase_records": sum(row.get("verified_purchase") is True for row in records),
            "unique_parents": len({(row.get("source"), row.get("parent_id")) for row in records if normalize_space(row.get("parent_id"))}),
            "units": {
                "source_mix": "included record",
                "sentiment": "labeled record",
                "theme_frequency": "labeled record; themes overlap",
                "brand_cross_tab": "record-tag assignment",
            },
        },
        "source_counts": dict(sorted(source_counts.items())),
        "access_mode_counts": [
            {"source": source, "access_mode": mode, "count": count}
            for (source, mode), count in sorted(access_counts.items())
        ],
        "source_sentiment": source_sentiment_rows,
        "tag_frequency": tag_rows,
        "brand_level_2_sentiment": brand_rows,
        "low_rating_tags": low_rating_rows,
        "ownership_counts": dict(sorted(ownership_counts.items())),
        "funnel_counts": dict(sorted(funnel_counts.items())),
        "severity_counts": dict(sorted(severity_counts.items())),
        "evidence_candidates": evidence_candidates[:50],
        "notes": [
            "Theme percentages use labeled records as the denominator and overlap.",
            "Source sentiment uses retained records from each source, not the platform population.",
            "Engagement is a distribution signal and is not used as a demand denominator.",
        ],
    }
    write_json(output_dir / "statistics.json", statistics)
    write_csv(
        output_dir / "tag_frequency.csv",
        tag_rows,
        [
            "level_3_id",
            "level_3_label",
            "level_2_id",
            "level_2_label",
            "record_count",
            "pct_of_labeled_records",
            "positive",
            "neutral",
            "negative",
            "mixed",
        ],
    )
    write_csv(output_dir / "source_sentiment.csv", source_sentiment_rows, ["source", "sentiment", "count", "pct_of_source_records"])
    write_csv(output_dir / "brand_level_2_sentiment.csv", brand_rows, ["brand", "level_2_id", "level_2_label", "sentiment", "record_tag_count"])
    write_csv(output_dir / "low_rating_tags.csv", low_rating_rows, ["level_3_id", "level_3_label", "low_rating_record_count"])
    print(f"records={len(records)} labeled={labeled_count} tags={len(tag_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
