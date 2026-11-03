#!/usr/bin/env python3
"""Compare a planned search matrix with prior query manifests to avoid unchanged reruns."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import normalize_for_match, normalize_space, read_jsonl, utc_now, write_json


def collect_queries(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        if normalize_space(value):
            found.append(normalize_space(value))
    elif isinstance(value, list):
        for item in value:
            found.extend(collect_queries(item))
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in {"query", "keyword"} and isinstance(item, str):
                found.extend(collect_queries(item))
            elif key in {"queries", "keywords", "terms", "runs"}:
                found.extend(collect_queries(item))
    return found


def token_similarity(left: str, right: str) -> float:
    left_tokens = set(normalize_for_match(left).split())
    right_tokens = set(normalize_for_match(right).split())
    union = left_tokens | right_tokens
    return len(left_tokens & right_tokens) / len(union) if union else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--prior", nargs="+", required=True)
    parser.add_argument("--source", default="")
    parser.add_argument("--similarity-threshold", type=float, default=0.80)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    matrix = read_jsonl(Path(args.matrix))
    if args.source:
        matrix = [row for row in matrix if normalize_space(row.get("source")) == args.source]
    prior_queries: list[str] = []
    for filename in args.prior:
        path = Path(filename)
        if path.suffix.lower() in {".jsonl", ".ndjson"}:
            payload: Any = read_jsonl(path)
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
        prior_queries.extend(collect_queries(payload))
    prior_map = {normalize_for_match(query): query for query in prior_queries if normalize_for_match(query)}

    covered: list[dict[str, Any]] = []
    similar: list[dict[str, Any]] = []
    novel: list[dict[str, Any]] = []
    for row in matrix:
        normalized = normalize_for_match(row.get("query"))
        item = {
            "query_id": normalize_space(row.get("query_id")),
            "source": normalize_space(row.get("source")),
            "round": normalize_space(row.get("round")),
            "dimension": normalize_space(row.get("dimension")),
            "query": normalize_space(row.get("query")),
        }
        if normalized in prior_map:
            item["matched_prior_query"] = prior_map[normalized]
            item["similarity"] = 1.0
            covered.append(item)
        else:
            best_query = ""
            best_score = 0.0
            for prior_query in prior_map.values():
                score = token_similarity(item["query"], prior_query)
                if score > best_score:
                    best_query = prior_query
                    best_score = score
            if best_score >= args.similarity_threshold:
                item["matched_prior_query"] = best_query
                item["similarity"] = round(best_score, 3)
                similar.append(item)
            else:
                item["best_prior_query"] = best_query
                item["best_similarity"] = round(best_score, 3)
                novel.append(item)

    result = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "source_filter": args.source,
        "matrix_queries": len(matrix),
        "prior_unique_queries": len(prior_map),
        "covered_exact": len(covered),
        "covered_similar": len(similar),
        "novel_after_similarity": len(novel),
        "similarity_threshold": args.similarity_threshold,
        "covered": covered,
        "similar": similar,
        "novel": novel,
        "interpretation": "Exact matches may be skipped. Similar matches are review candidates, not automatic duplicates. Review query purpose and prior yield before collection.",
    }
    write_json(Path(args.output), result)
    print(f"matrix={len(matrix)} exact={len(covered)} similar={len(similar)} novel={len(novel)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
