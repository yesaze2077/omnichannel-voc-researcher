#!/usr/bin/env python3
"""Validate annotation structure, taxonomy membership, and evidence traceability."""

from __future__ import annotations

import argparse
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import (
    REQUIRED_LEVEL_1_IDS,
    flatten_taxonomy,
    normalize_for_match,
    normalize_space,
    read_json,
    read_jsonl,
    write_json,
    write_jsonl,
)


ALLOWED_SENTIMENT = {"positive", "neutral", "negative", "mixed"}
ALLOWED_OWNERSHIP = {
    "verified_purchase",
    "owned_use",
    "claimed_use",
    "purchase_intent",
    "information_seeking",
    "none",
}
ALLOWED_FUNNEL = {
    "awareness",
    "consideration",
    "purchase",
    "installation",
    "ownership",
    "service",
    "repurchase",
    "unknown",
}
ALLOWED_SEVERITY = {"none", "low", "medium", "high", "safety"}


def taxonomy_errors(taxonomy: dict[str, Any]) -> list[str]:
    level_1 = taxonomy.get("level_1", [])
    ids = {normalize_space(item.get("id")) for item in level_1 if isinstance(item, dict)}
    errors: list[str] = []
    missing = REQUIRED_LEVEL_1_IDS - ids
    extra = ids - REQUIRED_LEVEL_1_IDS
    if missing:
        errors.append(f"taxonomy missing level_1 ids: {sorted(missing)}")
    if extra:
        errors.append(f"taxonomy has unsupported level_1 ids: {sorted(extra)}")
    return errors


def rating_band(value: Any) -> str:
    try:
        rating = float(value)
    except (TypeError, ValueError):
        return "unrated"
    if rating <= 2:
        return "low"
    if rating >= 4:
        return "high"
    return "mid"


def make_audit_sample(
    records: list[dict[str, Any]],
    annotations_by_id: dict[str, dict[str, Any]],
    target: int,
    seed: int,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        source_id = normalize_space(record.get("source_id"))
        annotation = annotations_by_id.get(source_id, {})
        key = (
            normalize_space(record.get("source")) or "unknown",
            normalize_space(record.get("brand")) or "unbranded",
            rating_band(record.get("rating")),
            normalize_space(annotation.get("sentiment")) or "unlabeled",
        )
        groups[key].append(record)

    rng = random.Random(seed)
    for group in groups.values():
        group.sort(key=lambda row: normalize_space(row.get("source_id")))
        rng.shuffle(group)

    selected: list[dict[str, Any]] = []
    keys = sorted(groups)
    while len(selected) < target:
        progressed = False
        for key in keys:
            if groups[key] and len(selected) < target:
                record = groups[key].pop()
                source_id = normalize_space(record.get("source_id"))
                safe_record = {k: v for k, v in record.items() if k != "author_hash"}
                selected.append(
                    {
                        "source_id": source_id,
                        "record": safe_record,
                        "annotation": annotations_by_id.get(source_id, {}),
                        "audit": {
                            "fully_correct": "",
                            "sentiment_correct": "",
                            "theme_correct": "",
                            "evidence_correct": "",
                            "notes": "",
                        },
                    }
                )
                progressed = True
        if not progressed:
            break
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--taxonomy", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--audit-sample", required=True)
    parser.add_argument("--audit-pct", type=float, default=5.0)
    parser.add_argument("--audit-min", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    records = read_jsonl(Path(args.records))
    annotations = read_jsonl(Path(args.annotations))
    taxonomy = read_json(Path(args.taxonomy))
    records_by_id = {normalize_space(row.get("source_id")): row for row in records}
    _, _, valid_tags = flatten_taxonomy(taxonomy)

    issues: list[dict[str, str]] = [
        {"source_id": "", "code": "taxonomy", "message": message}
        for message in taxonomy_errors(taxonomy)
    ]
    annotations_by_id: dict[str, dict[str, Any]] = {}
    duplicate_annotations = 0
    traceable = 0
    unknown_tag_counts: Counter[str] = Counter()

    for index, annotation in enumerate(annotations, start=1):
        source_id = normalize_space(annotation.get("source_id"))
        if not source_id:
            issues.append({"source_id": "", "code": "missing_source_id", "message": f"annotation row {index}"})
            continue
        if source_id in annotations_by_id:
            duplicate_annotations += 1
            issues.append({"source_id": source_id, "code": "duplicate_annotation", "message": "duplicate source_id"})
            continue
        annotations_by_id[source_id] = annotation
        record = records_by_id.get(source_id)
        if record is None:
            issues.append({"source_id": source_id, "code": "unknown_source_id", "message": "record not found"})
            continue

        sentiment = normalize_space(annotation.get("sentiment"))
        ownership = normalize_space(annotation.get("ownership_signal"))
        funnel = normalize_space(annotation.get("funnel_stage"))
        severity = normalize_space(annotation.get("severity"))
        tags = annotation.get("level_3_tags", [])
        if not isinstance(tags, list):
            issues.append({"source_id": source_id, "code": "invalid_tags", "message": "level_3_tags must be a list"})
            tags = []
        for tag in tags:
            tag_id = normalize_space(tag)
            if tag_id not in valid_tags:
                unknown_tag_counts[tag_id] += 1
                issues.append({"source_id": source_id, "code": "unknown_tag", "message": tag_id})
        if sentiment not in ALLOWED_SENTIMENT:
            issues.append({"source_id": source_id, "code": "invalid_sentiment", "message": sentiment})
        if ownership not in ALLOWED_OWNERSHIP:
            issues.append({"source_id": source_id, "code": "invalid_ownership", "message": ownership})
        if funnel not in ALLOWED_FUNNEL:
            issues.append({"source_id": source_id, "code": "invalid_funnel", "message": funnel})
        if severity not in ALLOWED_SEVERITY:
            issues.append({"source_id": source_id, "code": "invalid_severity", "message": severity})

        excerpt = normalize_for_match(annotation.get("evidence_excerpt"))
        record_text = normalize_for_match(record.get("text"))
        if not excerpt:
            issues.append({"source_id": source_id, "code": "missing_evidence", "message": "empty evidence excerpt"})
        elif excerpt not in record_text:
            issues.append({"source_id": source_id, "code": "untraceable_evidence", "message": "excerpt not found in record"})
        else:
            traceable += 1

    labeled_known = len(set(annotations_by_id) & set(records_by_id))
    coverage_pct = (labeled_known / len(records) * 100.0) if records else 0.0
    target = min(len(records), max(args.audit_min, math.ceil(len(records) * args.audit_pct / 100.0))) if records else 0
    audit_sample = make_audit_sample(records, annotations_by_id, target, args.seed)
    write_jsonl(Path(args.audit_sample), audit_sample)

    validation = {
        "record_count": len(records),
        "annotation_count": len(annotations),
        "labeled_known_records": labeled_known,
        "annotation_coverage_pct": round(coverage_pct, 2),
        "traceable_evidence_count": traceable,
        "traceable_evidence_pct": round(traceable / labeled_known * 100.0, 2) if labeled_known else 0.0,
        "duplicate_annotations": duplicate_annotations,
        "unknown_tag_counts": dict(sorted(unknown_tag_counts.items())),
        "error_count": len(issues),
        "issues": issues,
        "audit_sample_count": len(audit_sample),
    }
    write_json(Path(args.output), validation)
    print(f"coverage={coverage_pct:.2f}% errors={len(issues)} audit_sample={len(audit_sample)}")
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
