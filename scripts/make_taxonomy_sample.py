#!/usr/bin/env python3
"""Create a deterministic stratified sample and taxonomy-generation prompt."""

from __future__ import annotations

import argparse
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import normalize_space, read_jsonl, write_jsonl, atomic_write_text


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--sample", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--size", type=int, default=150)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--category", default="the study category")
    args = parser.parse_args()

    records = read_jsonl(Path(args.input))
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        key = (
            normalize_space(row.get("source")) or "unknown",
            normalize_space(row.get("brand")) or "unbranded",
            rating_band(row.get("rating")),
        )
        groups[key].append(row)

    rng = random.Random(args.seed)
    for group in groups.values():
        group.sort(key=lambda row: normalize_space(row.get("source_id")))
        rng.shuffle(group)

    target = min(max(args.size, 0), len(records))
    selected: list[dict[str, Any]] = []
    ordered_keys = sorted(groups)
    while len(selected) < target:
        progressed = False
        for key in ordered_keys:
            if groups[key] and len(selected) < target:
                selected.append(groups[key].pop())
                progressed = True
        if not progressed:
            break

    selected.sort(key=lambda row: normalize_space(row.get("source_id")))
    write_jsonl(Path(args.sample), selected)
    minimum_audit = max(50, math.ceil(len(records) * 0.05)) if records else 0
    prompt = f"""# Taxonomy calibration prompt

You are a senior Voice of Customer analyst. Read the attached stratified sample of {len(selected)} records for {args.category}.

Build a three-level taxonomy with these rules:

1. Keep exactly four level-one domains: `people_context`, `functional_value`, `assurance_value`, and `experience_value`.
2. Level two describes a concern area. Level three describes an observable, countable expression.
3. Use stable ASCII IDs and short neutral labels. Do not put sentiment inside theme labels.
4. Give every level-three tag a one-sentence inclusion rule and one boundary example.
5. Output the JSON shape documented in `references/schema.md`.
6. Stop after drafting the taxonomy. Wait for human calibration before annotating the full dataset.

Study notes:

- Full included denominator: {len(records)} records.
- Sample denominator: {len(selected)} records.
- Later annotation audit target: at least {minimum_audit} records.
- Preserve source differences; do not create a blended cross-platform sentiment metric.
"""
    atomic_write_text(Path(args.prompt), prompt)
    print(f"sample={len(selected)} audit_target={minimum_audit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
