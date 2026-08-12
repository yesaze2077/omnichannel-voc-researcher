#!/usr/bin/env python3
"""Normalize CSV/JSON/JSONL source records into the canonical VOC JSONL schema."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import (
    iter_input_rows,
    normalize_space,
    parse_bool,
    parse_float,
    parse_int,
    read_json,
    read_jsonl,
    safe_source_id,
    stable_hash,
    utc_now,
    write_jsonl,
)


ALIASES = {
    "native_id": ["native_id", "comment_id", "review_id", "post_id", "video_id", "id"],
    "parent_id": ["parent_id", "thread_id", "asin", "product_id", "conversation_id", "video_id"],
    "record_type": ["record_type", "type", "content_type"],
    "published_at": ["published_at", "published", "date", "created_at", "timestamp"],
    "text": ["text", "body", "content", "comment", "review", "caption", "title"],
    "source_url": ["source_url", "url", "permalink", "webpage_url", "href"],
    "author": ["author", "username", "user", "profile_name", "reviewer"],
    "brand": ["brand", "brand_name"],
    "product": ["product", "product_name", "title"],
    "vehicle": ["vehicle", "model", "fitment"],
    "rating": ["rating", "stars", "star_rating"],
    "verified_purchase": ["verified_purchase", "verified", "is_verified"],
    "engagement_count": ["engagement_count", "helpful", "likes", "score", "upvotes", "comments_count"],
    "engagement_type": ["engagement_type"],
    "source_type": ["source_type", "account_type", "creator_type"],
    "query": ["query", "keyword", "search_term"],
}

DEFAULT_RECORD_TYPE = {
    "amazon": "review",
    "youtube": "comment",
    "reddit": "comment",
    "x": "post",
    "tiktok": "comment",
    "facebook": "post",
    "instagram": "post",
    "first_party": "customer_record",
}


def parse_field_map(raw: str) -> dict[str, str]:
    if not raw:
        return {}
    candidate = Path(raw)
    value = read_json(candidate) if candidate.exists() else json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("field map must be a JSON object")
    return {str(key): str(column) for key, column in value.items()}


def find_value(row: dict[str, Any], canonical: str, field_map: dict[str, str]) -> Any:
    mapped = field_map.get(canonical)
    if mapped is not None:
        return row.get(mapped, "")
    for alias in ALIASES.get(canonical, [canonical]):
        if alias in row and normalize_space(row.get(alias)) != "":
            return row.get(alias)
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--access-mode", required=True)
    parser.add_argument("--format", choices=["auto", "csv", "json", "jsonl"], default="auto")
    parser.add_argument("--field-map", default="")
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--author-salt", default="local-voc")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    field_map = parse_field_map(args.field_map)
    source = args.source.lower()
    collected_at = utc_now()

    existing = read_jsonl(output_path) if args.append and output_path.exists() else []
    known_ids = {normalize_space(row.get("source_id")) for row in existing}
    normalized: list[dict[str, Any]] = []
    skipped_empty = 0
    duplicate_ids = 0

    for line_number, raw in iter_input_rows(input_path, args.format):
        text = normalize_space(find_value(raw, "text", field_map))
        if not text:
            skipped_empty += 1
            continue
        native_id = normalize_space(find_value(raw, "native_id", field_map))
        source_url = normalize_space(find_value(raw, "source_url", field_map))
        published_at = normalize_space(find_value(raw, "published_at", field_map))
        source_id = safe_source_id(source, native_id, source_url, published_at, text)
        if source_id in known_ids:
            duplicate_ids += 1
            continue

        author = normalize_space(find_value(raw, "author", field_map))
        record = {
            "source_id": source_id,
            "source": source,
            "access_mode": args.access_mode,
            "native_id": native_id,
            "parent_id": normalize_space(find_value(raw, "parent_id", field_map)),
            "record_type": normalize_space(find_value(raw, "record_type", field_map)) or DEFAULT_RECORD_TYPE.get(source, "record"),
            "published_at": published_at,
            "collected_at": collected_at,
            "text": text,
            "source_url": source_url,
            "author_hash": stable_hash(args.author_salt, source, author) if author else "",
            "brand": normalize_space(find_value(raw, "brand", field_map)),
            "product": normalize_space(find_value(raw, "product", field_map)),
            "vehicle": normalize_space(find_value(raw, "vehicle", field_map)),
            "rating": parse_float(find_value(raw, "rating", field_map)),
            "verified_purchase": parse_bool(find_value(raw, "verified_purchase", field_map)),
            "engagement_count": parse_int(find_value(raw, "engagement_count", field_map)),
            "engagement_type": normalize_space(find_value(raw, "engagement_type", field_map)),
            "source_type": normalize_space(find_value(raw, "source_type", field_map)),
            "query": normalize_space(find_value(raw, "query", field_map)),
            "raw_ref": f"{input_path.name}:{line_number}",
            "collection_status": "collected",
            "exclusion_reason": "",
        }
        normalized.append(record)
        known_ids.add(source_id)

    write_jsonl(output_path, existing + normalized)
    print(
        json.dumps(
            {
                "input": str(input_path),
                "output": str(output_path),
                "source": source,
                "added": len(normalized),
                "existing": len(existing),
                "skipped_empty_text": skipped_empty,
                "duplicate_source_ids": duplicate_ids,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
