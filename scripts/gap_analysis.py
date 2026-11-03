#!/usr/bin/env python3
"""Turn preliminary VOC coverage requirements into deterministic round-2 gap terms."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import normalize_space, read_json, read_jsonl, utc_now, write_json


def values(value: Any) -> set[str]:
    if isinstance(value, list):
        return {normalize_space(item).lower() for item in value if normalize_space(item)}
    text = normalize_space(value)
    return {text.lower()} if text else set()


def matches(record: dict[str, Any], annotation: dict[str, Any], cell: dict[str, Any]) -> bool:
    dimensions = {
        "sources": values(record.get("source")),
        "record_types": values(record.get("record_type")),
        "brands": values(record.get("brand")),
        "products": values(record.get("product")),
        "product_relations": values(record.get("product_relation")),
        "ownership_signals": values(annotation.get("ownership_signal")),
        "sentiments": values(annotation.get("sentiment")),
        "funnel_stages": values(annotation.get("funnel_stage")),
        "tags": values(annotation.get("level_3_tags")),
    }
    for key, actual in dimensions.items():
        expected = values(cell.get(key))
        if expected and not actual.intersection(expected):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = read_jsonl(Path(args.records))
    annotations = {
        normalize_space(row.get("source_id")): row
        for row in read_jsonl(Path(args.annotations))
        if normalize_space(row.get("source_id"))
    }
    requirements = read_json(Path(args.requirements))
    cells = requirements.get("evidence_cells", []) if isinstance(requirements, dict) else []
    if not isinstance(cells, list) or not cells:
        raise SystemExit("requirements must contain a non-empty evidence_cells list")

    results: list[dict[str, Any]] = []
    gap_terms: list[str] = []
    for index, cell in enumerate(cells, start=1):
        if not isinstance(cell, dict):
            continue
        matched = [
            row for row in records
            if matches(row, annotations.get(normalize_space(row.get("source_id")), {}), cell)
        ]
        record_count = len(matched)
        parent_count = len({
            (normalize_space(row.get("source")), normalize_space(row.get("parent_id")))
            for row in matched if normalize_space(row.get("parent_id"))
        })
        source_count = len({normalize_space(row.get("source")) for row in matched if normalize_space(row.get("source"))})
        min_records = int(cell.get("min_records", 0) or 0)
        min_parents = int(cell.get("min_parents", 0) or 0)
        min_sources = int(cell.get("min_sources", 0) or 0)
        passed = record_count >= min_records and parent_count >= min_parents and source_count >= min_sources
        search_term = normalize_space(cell.get("search_term"))
        if not passed and search_term and search_term.lower() not in {term.lower() for term in gap_terms}:
            gap_terms.append(search_term)
        results.append({
            "cell_id": normalize_space(cell.get("id")) or f"cell_{index}",
            "label": normalize_space(cell.get("label")) or normalize_space(cell.get("id")) or f"Cell {index}",
            "search_term": search_term,
            "actual": {"records": record_count, "parents": parent_count, "sources": source_count},
            "minimum": {"records": min_records, "parents": min_parents, "sources": min_sources},
            "passed": passed,
            "record_deficit": max(0, min_records - record_count),
            "parent_deficit": max(0, min_parents - parent_count),
            "source_deficit": max(0, min_sources - source_count),
        })

    result = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "records_evaluated": len(records),
        "annotations_available": len(annotations),
        "cells": results,
        "failed_cells": [row["cell_id"] for row in results if not row["passed"]],
        "gap_terms": gap_terms,
        "round_2_required": any(not row["passed"] for row in results),
        "next_command_hint": (
            "Pass the comma-separated gap_terms to build_search_matrix.py --stage round_2."
            if gap_terms else "No declared evidence-cell gap remains."
        ),
    }
    write_json(Path(args.output), result)
    print(f"cells={len(results)} failed={len(result['failed_cells'])} gap_terms={len(gap_terms)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
