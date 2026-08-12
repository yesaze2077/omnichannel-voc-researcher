#!/usr/bin/env python3
"""Clean normalized VOC records while preserving explicit exclusion evidence."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import normalize_for_match, normalize_space, read_jsonl, write_json, write_jsonl


DEFAULT_PROMOTION_TERMS = (
    "discount code",
    "use code",
    "link in bio",
    "affiliate link",
    "sponsored post",
    "shop now",
    "limited time deal",
)


def term_list(values: list[str]) -> list[str]:
    return [normalize_for_match(value) for value in values if normalize_for_match(value)]


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def rank_record(row: dict[str, Any]) -> tuple[float, str, str]:
    engagement = row.get("engagement_count", "")
    try:
        numeric = float(engagement) if engagement != "" else 0.0
    except (TypeError, ValueError):
        numeric = 0.0
    return (-numeric, normalize_space(row.get("published_at")), normalize_space(row.get("source_id")))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--included", required=True)
    parser.add_argument("--excluded", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--required-term", action="append", default=[])
    parser.add_argument("--reject-term", action="append", default=[])
    parser.add_argument("--promotion-term", action="append", default=[])
    parser.add_argument("--min-chars", type=int, default=8)
    parser.add_argument("--max-per-parent", type=int, default=50)
    args = parser.parse_args()

    records = read_jsonl(Path(args.input))
    required = term_list(args.required_term)
    rejected_terms = term_list(args.reject_term)
    promotion = term_list(args.promotion_term or list(DEFAULT_PROMOTION_TERMS))
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    seen_exact: set[tuple[str, str]] = set()

    for row in records:
        record = dict(row)
        match_text = normalize_for_match(record.get("text"))
        reason = ""
        if len(match_text) < args.min_chars:
            reason = "too_short"
        elif required and not contains_any(match_text, required):
            reason = "missing_required_context"
        elif rejected_terms and contains_any(match_text, rejected_terms):
            reason = "reject_term"
        elif promotion and contains_any(match_text, promotion):
            reason = "pure_promotion_candidate"
        elif (normalize_space(record.get("source")), match_text) in seen_exact:
            reason = "exact_duplicate"

        if reason:
            record["collection_status"] = "excluded"
            record["exclusion_reason"] = reason
            excluded.append(record)
        else:
            seen_exact.add((normalize_space(record.get("source")), match_text))
            record["collection_status"] = "included"
            record["exclusion_reason"] = ""
            included.append(record)

    if args.max_per_parent > 0:
        by_parent: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        uncapped: list[dict[str, Any]] = []
        for record in included:
            parent_id = normalize_space(record.get("parent_id"))
            if parent_id:
                by_parent[(normalize_space(record.get("source")), parent_id)].append(record)
            else:
                uncapped.append(record)

        capped_included = list(uncapped)
        for _, group in sorted(by_parent.items()):
            ordered = sorted(group, key=rank_record)
            capped_included.extend(ordered[: args.max_per_parent])
            for record in ordered[args.max_per_parent :]:
                capped = dict(record)
                capped["collection_status"] = "excluded"
                capped["exclusion_reason"] = "parent_cap"
                excluded.append(capped)
        included = sorted(capped_included, key=lambda row: normalize_space(row.get("source_id")))

    reasons = Counter(normalize_space(row.get("exclusion_reason")) for row in excluded)
    source_before = Counter(normalize_space(row.get("source")) for row in records)
    source_after = Counter(normalize_space(row.get("source")) for row in included)
    summary = {
        "input_records": len(records),
        "included_records": len(included),
        "excluded_records": len(excluded),
        "exclusion_reasons": dict(sorted(reasons.items())),
        "source_counts_before": dict(sorted(source_before.items())),
        "source_counts_after": dict(sorted(source_after.items())),
        "max_per_parent": args.max_per_parent,
        "required_terms": required,
        "reject_terms": rejected_terms,
        "promotion_terms": promotion,
    }
    write_jsonl(Path(args.included), included)
    write_jsonl(Path(args.excluded), excluded)
    write_json(Path(args.summary), summary)
    print(f"included={len(included)} excluded={len(excluded)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
