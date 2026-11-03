#!/usr/bin/env python3
"""Build a balanced, source-aware VOC search matrix for pilot and append rounds."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

from common import normalize_for_match, normalize_space, read_jsonl, stable_hash, utc_now, write_json, write_jsonl


NEGATIVE_DIMENSIONS = {"pain_failure", "troubleshooting", "rating_risk"}
STAGE_TO_ROUND = {
    "pilot": "pilot",
    "formal": "round_1",
    "round_2": "round_2",
    "supplement": "supplement",
    "targeted_completion": "round_3_targeted_completion",
}
REDDIT_ENTRYPOINTS = {
    "old": "https://old.reddit.com",
    "modern": "https://www.reddit.com",
}


def reddit_access_fields(entrypoint: str, authorization_status: str) -> dict[str, str]:
    """Return an auditable Reddit browser-access contract for a matrix row."""
    fallback = "modern" if entrypoint == "old" else "old"
    authorization_prefix = "authorized_browser" if authorization_status != "unconfirmed" else "public_page"
    return {
        "access_mode": f"{authorization_prefix}_{entrypoint}_reddit",
        "preferred_entrypoint": REDDIT_ENTRYPOINTS[entrypoint],
        "fallback_entrypoint": REDDIT_ENTRYPOINTS[fallback],
        "authorization_status": authorization_status,
    }


def terms(value: str) -> list[str]:
    result: list[str] = []
    for item in value.split(","):
        cleaned = normalize_space(item)
        if cleaned and cleaned.lower() not in {existing.lower() for existing in result}:
            result.append(cleaned)
    return result


def add_candidate(
    rows: list[dict[str, Any]],
    query: str,
    dimension: str,
    purpose: str,
    priority: int = 2,
) -> None:
    cleaned = normalize_space(query)
    if cleaned:
        rows.append({
            "query": cleaned,
            "dimension": dimension,
            "purpose": purpose,
            "priority": priority,
        })


def candidate_queries(
    core_terms: list[str],
    brands: list[str],
    scenes: list[str],
    problems: list[str],
    workflows: list[str],
    gap_terms: list[str],
    stage: str,
    mode: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for core in core_terms:
        for modifier, purpose in (
            ("review", "Baseline product/category evaluation"),
            ("honest review", "Independent purchase evaluation"),
            ("worth it", "Value and purchase objection"),
            ("before you buy", "Pre-purchase concerns"),
        ):
            add_candidate(rows, f"{core} {modifier}", "baseline_evaluation", purpose, 1)
        for modifier, purpose in (
            ("setup", "Initial setup"),
            ("how to use", "Use workflow"),
            ("installation", "Installation effort"),
            ("compatibility", "Compatibility boundary"),
        ):
            add_candidate(rows, f"{core} {modifier}", "setup_compatibility", purpose, 1)
        for modifier, purpose in (
            ("long term review", "Long-term ownership"),
            ("after 6 months", "Durability evidence"),
            ("owner review", "Claimed ownership"),
            ("warranty support", "Service experience"),
        ):
            add_candidate(rows, f"{core} {modifier}", "ownership_service", purpose, 2)
        for modifier, purpose in (
            ("problems", "Broad failure discovery"),
            ("not working", "Failure and remedy"),
            ("common issues", "Recurring issues"),
        ):
            add_candidate(rows, f"{core} {modifier}", "pain_failure", purpose, 2)
        for modifier, purpose in (
            ("troubleshooting", "Troubleshooting language"),
            ("how to fix", "User remedy"),
        ):
            add_candidate(rows, f"{core} {modifier}", "troubleshooting", purpose, 2)
        for scene in scenes:
            add_candidate(rows, f"{core} for {scene}", "scene_job", f"Use scene: {scene}", 1)
            add_candidate(rows, f"using {core} for {scene}", "scene_job", f"Observed workflow: {scene}", 2)
        for workflow in workflows:
            add_candidate(rows, f"{core} {workflow} setup", "workflow_platform", f"Workflow: {workflow}", 1)
            add_candidate(rows, f"{core} {workflow} compatibility", "workflow_platform", f"Compatibility: {workflow}", 2)
        for problem in problems:
            add_candidate(rows, f"{core} {problem}", "pain_failure", f"Problem: {problem}", 1)
            add_candidate(rows, f"{core} {problem} fix", "troubleshooting", f"Remedy: {problem}", 2)
        for brand in brands:
            core_has_known_brand = any(known.lower() in core.lower() for known in brands)
            same_brand = brand.lower() in core.lower()
            if not core_has_known_brand:
                add_candidate(rows, f"{brand} {core} review", "brand_model", f"Brand evidence: {brand}", 1)
                add_candidate(rows, f"{brand} {core} problems", "pain_failure", f"Brand problem evidence: {brand}", 2)
                add_candidate(rows, f"{brand} {core} long term review", "ownership_service", f"Brand durability: {brand}", 2)
            elif same_brand:
                add_candidate(rows, f"{core} review", "brand_model", f"Target brand/model evidence: {brand}", 1)
                add_candidate(rows, f"{core} problems", "pain_failure", f"Target brand/model problem evidence: {brand}", 2)
                add_candidate(rows, f"{core} long term review", "ownership_service", f"Target brand/model durability: {brand}", 2)
            if not same_brand:
                add_candidate(rows, f"{core} vs {brand}", "comparison_switching", f"Alternative comparison: {brand}", 1)

        if mode == "rating-recovery":
            for modifier, purpose in (
                ("1 star review", "Low-rating driver"),
                ("2 star review", "Low-rating driver"),
                ("returned", "Return-triggering experience"),
                ("review update", "Post-purchase rating change"),
            ):
                add_candidate(rows, f"{core} {modifier}", "rating_risk", purpose, 1)
            for modifier, purpose in (
                ("support fixed", "Successful service recovery"),
                ("replacement experience", "Replacement and recovery"),
                ("setup mistake", "Setup-caused dissatisfaction"),
                ("not what I expected", "Expectation mismatch"),
            ):
                dimension = "support_recovery" if modifier in {"support fixed", "replacement experience"} else "expectation_mismatch"
                add_candidate(rows, f"{core} {modifier}", dimension, purpose, 1)

    for gap in gap_terms:
        for core in core_terms:
            add_candidate(rows, f"{core} {gap}", "gap_append", f"Evidence gap: {gap}", 1)
            add_candidate(rows, f"{core} {gap} review", "gap_append", f"Gap evaluation: {gap}", 2)
            add_candidate(rows, f"{core} {gap} problems", "gap_append", f"Gap failure evidence: {gap}", 2)

    if stage in {"round_2", "supplement", "targeted_completion"}:
        return [row for row in rows if row["dimension"] == "gap_append"]
    return rows


def select_balanced(candidates: list[dict[str, Any]], count: int, negative_cap: float) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for row in candidates:
        key = normalize_for_match(row["query"])
        if key not in unique or row["priority"] < unique[key]["priority"]:
            unique[key] = row

    groups: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for row in sorted(unique.values(), key=lambda item: (item["priority"], item["query"].lower())):
        groups[row["dimension"]].append(row)
    dimension_order = [
        "baseline_evaluation",
        "setup_compatibility",
        "scene_job",
        "workflow_platform",
        "brand_model",
        "comparison_switching",
        "ownership_service",
        "pain_failure",
        "troubleshooting",
        "rating_risk",
        "expectation_mismatch",
        "support_recovery",
        "gap_append",
    ]
    active = [dimension for dimension in dimension_order if groups[dimension]]
    selected: list[dict[str, Any]] = []
    negative = 0
    while active and len(selected) < count:
        progressed = False
        for dimension in list(active):
            if len(selected) >= count:
                break
            if not groups[dimension]:
                active.remove(dimension)
                continue
            row = groups[dimension].popleft()
            is_negative = dimension in NEGATIVE_DIMENSIONS
            projected_negative = negative + int(is_negative)
            projected_total = len(selected) + 1
            if is_negative and projected_negative / projected_total > negative_cap:
                if groups[dimension]:
                    groups[dimension].append(row)
                else:
                    active.remove(dimension)
                continue
            selected.append(row)
            negative = projected_negative
            progressed = True
        if not progressed:
            break
    return selected


def enforce_target_floor(
    selected: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    target_terms: list[str],
    floor: int,
    negative_cap: float,
) -> list[dict[str, Any]]:
    """Replace non-target rows so a named target is not diluted by category queries."""
    normalized_targets = [normalize_for_match(term) for term in target_terms if normalize_for_match(term)]
    if not normalized_targets or floor <= 0:
        return selected

    def is_target(row: dict[str, Any]) -> bool:
        query = normalize_for_match(row["query"])
        return any(term in query for term in normalized_targets)

    result = list(selected)
    selected_keys = {normalize_for_match(row["query"]) for row in result}
    target_count = sum(is_target(row) for row in result)
    if target_count >= floor:
        return result
    target_candidate_map: dict[str, dict[str, Any]] = {}
    for row in sorted(candidates, key=lambda item: (item["priority"], item["dimension"], item["query"].lower())):
        key = normalize_for_match(row["query"])
        if is_target(row) and key not in selected_keys and key not in target_candidate_map:
            target_candidate_map[key] = row
    target_candidates = list(target_candidate_map.values())
    for candidate in target_candidates:
        if target_count >= floor:
            break
        replacement_index = next((
            index for index in range(len(result) - 1, -1, -1)
            if not is_target(result[index])
            and ((result[index]["dimension"] in NEGATIVE_DIMENSIONS) == (candidate["dimension"] in NEGATIVE_DIMENSIONS))
        ), None)
        if replacement_index is None:
            replacement_index = next((index for index in range(len(result) - 1, -1, -1) if not is_target(result[index])), None)
        if replacement_index is None:
            break
        trial = list(result)
        trial[replacement_index] = candidate
        negative_share = sum(row["dimension"] in NEGATIVE_DIMENSIONS for row in trial) / len(trial)
        if negative_share > negative_cap:
            continue
        result = trial
        selected_keys = {normalize_for_match(row["query"]) for row in result}
        target_count = sum(is_target(row) for row in result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", required=True)
    parser.add_argument("--mode", default="listing-content")
    parser.add_argument("--stage", choices=tuple(STAGE_TO_ROUND), required=True)
    parser.add_argument("--sources", nargs="+", required=True)
    parser.add_argument("--core-terms", required=True, help="Comma-separated category/product synonyms.")
    parser.add_argument("--target-terms", default="", help="Comma-separated named target models that need a minimum query share.")
    parser.add_argument("--target-query-floor", type=int, default=0, help="Minimum target-model queries per source after balancing.")
    parser.add_argument("--brands", default="")
    parser.add_argument("--scenes", default="")
    parser.add_argument("--problems", default="")
    parser.add_argument("--workflows", default="")
    parser.add_argument("--gap-terms", default="")
    parser.add_argument("--communities", default="", help="Comma-separated Reddit/forum scopes.")
    parser.add_argument("--required-context-terms", default="")
    parser.add_argument("--reject-context-terms", default="")
    parser.add_argument("--queries-per-source", type=int, default=0)
    parser.add_argument("--negative-query-cap-pct", type=float, default=35.0)
    parser.add_argument(
        "--reddit-entrypoint",
        choices=tuple(REDDIT_ENTRYPOINTS),
        default="old",
        help="Preferred Reddit browser surface. Old Reddit is the default lightweight surface.",
    )
    parser.add_argument(
        "--reddit-authorization-status",
        choices=("unconfirmed", "user_confirmed", "documented"),
        default="unconfirmed",
        help="Audit label only; never place credentials or authorization documents in the matrix.",
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--append", action="store_true", help="Append new query IDs without overwriting prior rounds.")
    args = parser.parse_args()

    core = terms(args.core_terms)
    if not core:
        raise SystemExit("--core-terms must contain at least one term")
    gaps = terms(args.gap_terms)
    if args.stage in {"round_2", "supplement", "targeted_completion"} and not gaps:
        raise SystemExit("--gap-terms is required for round_2, supplement, and targeted_completion matrices")
    query_count = args.queries_per_source or {
        "pilot": 12,
        "formal": 60,
        "round_2": 15,
        "supplement": 10,
        "targeted_completion": 10,
    }[args.stage]
    candidates = candidate_queries(
        core,
        terms(args.brands),
        terms(args.scenes),
        terms(args.problems),
        terms(args.workflows),
        gaps,
        args.stage,
        args.mode,
    )
    scopes = terms(args.communities) or [""]
    required = terms(args.required_context_terms) or core
    rejected = terms(args.reject_context_terms)
    output_rows: list[dict[str, Any]] = []
    for source in args.sources:
        selected = select_balanced(candidates, query_count, args.negative_query_cap_pct / 100.0)
        selected = enforce_target_floor(
            selected,
            candidates,
            terms(args.target_terms),
            min(args.target_query_floor, query_count),
            args.negative_query_cap_pct / 100.0,
        )
        for index, row in enumerate(selected):
            scope = scopes[index % len(scopes)] if source in {"reddit", "owner_forum", "review_site", "independent_web", "app_store"} else ""
            access_fields: dict[str, str] = {
                "access_mode": "official_api" if source == "youtube" else "public_page" if source in {"owner_forum", "review_site", "independent_web", "app_store"} else "browser_assisted",
            }
            if source == "reddit":
                access_fields = reddit_access_fields(args.reddit_entrypoint, args.reddit_authorization_status)
            output_rows.append({
                "query_id": f"q_{stable_hash(source, STAGE_TO_ROUND[args.stage], scope, row['query'])}",
                "source": source,
                "round": STAGE_TO_ROUND[args.stage],
                "dimension": row["dimension"],
                "query": row["query"],
                "scope": scope,
                "purpose": row["purpose"],
                "priority": row["priority"],
                "required_context_terms": required,
                "reject_context_terms": rejected,
                "planned_parent_target": 5 if args.stage == "pilot" else 10,
                "max_results": 10 if source == "youtube" else 20 if source in {"reddit", "owner_forum", "review_site", "independent_web", "app_store"} else 5,
                **access_fields,
                "status": "planned",
            })

    output_path = Path(args.output)
    prior_rows = read_jsonl(output_path) if args.append and output_path.exists() else []
    combined: dict[str, dict[str, Any]] = {
        normalize_space(row.get("query_id")): row
        for row in prior_rows
        if normalize_space(row.get("query_id"))
    }
    for row in output_rows:
        combined[row["query_id"]] = row
    all_rows = list(combined.values())
    write_jsonl(output_path, all_rows)
    dimension_counts = Counter(row["dimension"] for row in output_rows)
    negative = sum(row["dimension"] in NEGATIVE_DIMENSIONS for row in output_rows)
    summary = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "category": args.category,
        "mode": args.mode,
        "stage": args.stage,
        "round": STAGE_TO_ROUND[args.stage],
        "sources": args.sources,
        "queries": len(output_rows),
        "matrix_queries_after_append": len(all_rows),
        "append": bool(args.append),
        "queries_per_source": dict(Counter(row["source"] for row in output_rows)),
        "dimension_counts": dict(sorted(dimension_counts.items())),
        "negative_query_share_pct": round(negative / len(output_rows) * 100.0, 2) if output_rows else 0.0,
        "negative_query_cap_pct": args.negative_query_cap_pct,
        "target_terms": terms(args.target_terms),
        "target_query_floor": min(args.target_query_floor, query_count),
        "target_query_counts": {
            source: sum(
                any(normalize_for_match(term) in normalize_for_match(row["query"]) for term in terms(args.target_terms))
                for row in output_rows if row["source"] == source
            )
            for source in args.sources
        },
        "required_context_terms": required,
        "reject_context_terms": rejected,
        "reddit_entrypoint": args.reddit_entrypoint if "reddit" in args.sources else None,
        "reddit_authorization_status": args.reddit_authorization_status if "reddit" in args.sources else None,
    }
    summary_path = Path(args.summary) if args.summary else output_path.with_suffix(".summary.json")
    write_json(summary_path, summary)
    print(f"queries={len(output_rows)} output={output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
