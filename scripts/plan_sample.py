#!/usr/bin/env python3
"""Plan a decision-aware omnichannel VOC sample portfolio."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from common import utc_now, write_json


MODES = (
    "category-opportunity",
    "brand-reputation",
    "product-improvement",
    "listing-content",
    "rating-recovery",
    "competitor-intel",
    "content-strategy",
)

DEPTH_TOTALS = {
    "category-opportunity": {"exploratory": 300, "standard": 900, "deep": 2000},
    "brand-reputation": {"exploratory": 300, "standard": 800, "deep": 1500},
    "product-improvement": {"exploratory": 350, "standard": 800, "deep": 1500},
    "listing-content": {"exploratory": 250, "standard": 600, "deep": 1000},
    "rating-recovery": {"exploratory": 300, "standard": 700, "deep": 1080},
    "competitor-intel": {"exploratory": 400, "standard": 1000, "deep": 2200},
    "content-strategy": {"exploratory": 400, "standard": 1000, "deep": 2500},
}

MODE_WEIGHTS = {
    "category-opportunity": {"youtube": 40, "owner_forum": 25, "reddit": 20, "amazon": 5, "review_site": 3, "independent_web": 3, "first_party": 5},
    "brand-reputation": {"youtube": 25, "owner_forum": 20, "reddit": 20, "amazon": 17, "review_site": 10, "independent_web": 5, "first_party": 13},
    "product-improvement": {"youtube": 35, "owner_forum": 25, "reddit": 20, "amazon": 10, "review_site": 4, "independent_web": 4, "first_party": 5},
    "listing-content": {"youtube": 35, "owner_forum": 20, "reddit": 15, "amazon": 15, "review_site": 5, "independent_web": 5, "first_party": 10},
    "rating-recovery": {"youtube": 36.3, "owner_forum": 20.7, "reddit": 15.5, "amazon": 15.5, "review_site": 3, "independent_web": 3, "app_store": 2, "first_party": 10},
    "competitor-intel": {"youtube": 38, "owner_forum": 25, "reddit": 20, "amazon": 10, "review_site": 4, "independent_web": 4, "first_party": 2},
    "content-strategy": {"youtube": 50, "owner_forum": 20, "reddit": 15, "amazon": 5, "review_site": 3, "independent_web": 3, "first_party": 5},
}

RISKY_SOCIAL = {"x", "tiktok", "facebook", "instagram"}
CORE_OPEN = {"youtube", "owner_forum", "reddit"}
TARGETED_COMPLETION = RISKY_SOCIAL | {"review_site", "independent_web", "app_store"}
ALIASES = {
    "reddit_old": "reddit",
    "old_reddit": "reddit",
    "vertical_forum": "owner_forum",
    "open_forum": "owner_forum",
    "vertical_community": "owner_forum",
    "trustpilot": "review_site",
    "sitejabber": "review_site",
    "third_party_review": "review_site",
    "independent_site": "independent_web",
    "brand_store_review": "independent_web",
    "appstore": "app_store",
    "app_review": "app_store",
    "ins": "instagram",
    "ig": "instagram",
}


def normalize_channels(channels: list[str]) -> list[str]:
    result = []
    for raw in channels:
        channel = ALIASES.get(raw.lower().strip(), raw.lower().strip())
        if channel and channel not in result:
            result.append(channel)
    return result


def distribute(total: int, weighted_sources: list[tuple[str, float]]) -> dict[str, int]:
    if not weighted_sources:
        return {}
    weight_sum = sum(weight for _, weight in weighted_sources)
    exact = [(source, total * weight / weight_sum) for source, weight in weighted_sources]
    allocated = {source: math.floor(value) for source, value in exact}
    remaining = total - sum(allocated.values())
    for source, _ in sorted(exact, key=lambda item: (item[1] - math.floor(item[1]), item[0]), reverse=True)[:remaining]:
        allocated[source] += 1
    return allocated


def minimum_parents(source: str, records: int, depth: str) -> int:
    floors = {
        "youtube": {"exploratory": 25, "standard": 60, "deep": 120},
        "owner_forum": {"exploratory": 15, "standard": 30, "deep": 60},
        "reddit": {"exploratory": 15, "standard": 30, "deep": 60},
        "amazon": {"exploratory": 8, "standard": 15, "deep": 25},
        "review_site": {"exploratory": 5, "standard": 8, "deep": 10},
        "independent_web": {"exploratory": 5, "standard": 8, "deep": 10},
        "app_store": {"exploratory": 2, "standard": 2, "deep": 2},
        "first_party": {"exploratory": 20, "standard": 50, "deep": 100},
    }
    if source == "app_store":
        return min(records, 2)
    if source in TARGETED_COMPLETION:
        return min(records, 10)
    floor = floors.get(source, {"exploratory": 10, "standard": 20, "deep": 40})[depth]
    divisor = 12 if source in CORE_OPEN else 15
    return min(records, max(floor, math.ceil(records / divisor)))


def record_floor(source: str, goal: int, total: int, depth: str) -> int:
    """Return an interpretability floor without turning the planning goal into a cap."""
    if source == "app_store":
        return min(goal, max(20, math.ceil(total * 0.02)))
    if source in TARGETED_COMPLETION:
        return min(goal, max(30, math.ceil(total * 0.03)))
    base = {
        "youtube": {"exploratory": 75, "standard": 180, "deep": 300},
        "owner_forum": {"exploratory": 40, "standard": 90, "deep": 150},
        "reddit": {"exploratory": 50, "standard": 120, "deep": 200},
        "amazon": {"exploratory": 20, "standard": 40, "deep": 60},
        "first_party": {"exploratory": 20, "standard": 50, "deep": 80},
    }.get(source, {"exploratory": 20, "standard": 40, "deep": 60})[depth]
    return min(goal, max(base, math.ceil(goal * 0.60)))


def record_cap(source: str, goal: int, total: int) -> int:
    """Limit concentration while leaving room to reallocate optional-source shortfalls."""
    if source in RISKY_SOCIAL:
        return max(goal, math.ceil(total * 0.06))
    if source in {"review_site", "independent_web", "app_store"}:
        return max(goal, math.ceil(total * 0.10))
    if source in CORE_OPEN:
        return max(goal, math.floor(total * 0.70))
    return max(goal, math.ceil(total * 0.25))


def access_order(source: str) -> list[str]:
    if source == "youtube":
        return ["official_api_search_metadata_comments", "public_caption_recovery"]
    if source == "reddit":
        return ["old_reddit_public_pages", "authorized_official_api_if_available"]
    if source == "owner_forum":
        return ["public_forum_pages"]
    if source == "review_site":
        return ["public_review_pages", "authorized_export_if_available"]
    if source == "independent_web":
        return ["public_brand_or_store_review_pages", "public_product_q_and_a"]
    if source == "app_store":
        return ["public_app_store_review_pages", "authorized_export_if_available"]
    if source == "x":
        return ["supervised_browser", "authorized_official_api_if_blocked"]
    if source in {"tiktok", "facebook", "instagram", "amazon"}:
        return ["supervised_browser"]
    if source == "first_party":
        return ["authorized_import"]
    return ["public_or_authorized_source"]


def build_plan(mode: str, depth: str, channels: list[str], target_total: int = 0) -> dict:
    channels = normalize_channels(channels)
    if not channels:
        raise ValueError("at least one channel is required")
    if not (set(channels) - RISKY_SOCIAL):
        raise ValueError("a study cannot rely only on high-risk social browser samples")

    requested_total = target_total or DEPTH_TOTALS[mode][depth]
    risky = [source for source in channels if source in RISKY_SOCIAL]
    # Preserve a useful floor without allowing risky browser sources to dominate.
    total = max(requested_total, math.ceil(len(risky) * 30 / 0.15)) if risky else requested_total
    risky_floor = max(30, math.ceil(total * 0.03)) if risky else 0
    risky_reserved = risky_floor * len(risky)
    if risky_reserved > math.floor(total * 0.15):
        total = math.ceil(risky_reserved / 0.15)

    non_risky = [source for source in channels if source not in RISKY_SOCIAL]
    weights = MODE_WEIGHTS[mode]
    weighted = [(source, weights.get(source, 5)) for source in non_risky]
    allocations = distribute(total - risky_reserved, weighted)
    for source in risky:
        allocations[source] = risky_floor

    rows = []
    for source in channels:
        records = allocations[source]
        parent_floor = minimum_parents(source, records, depth)
        role = "core" if source in CORE_OPEN else ("targeted_supplement" if source in TARGETED_COMPLETION else "supplement")
        row = {
            "source": source,
            "role": role,
            "required": source in CORE_OPEN,
            "required_for_completion": True,
            "record_floor": record_floor(source, records, total, depth),
            "record_goal": records,
            "record_cap": record_cap(source, records, total),
            "target_included_records": records,
            "target_share_pct": round(records / total * 100, 2),
            "min_distinct_parents": parent_floor,
            "access_order": access_order(source),
            "status": "planned",
        }
        if source in RISKY_SOCIAL:
            row.update({
                "max_planned_share_pct": 6.0,
                "interpretability_floor": {
                    "min_records": risky_floor,
                    "min_distinct_parents": 10,
                    "rule": "Below either floor, label as case supplement and exclude from cross-channel agreement claims.",
                },
            })
        if source == "youtube":
            transcript_target = max(15, math.ceil(parent_floor * 0.65))
            raw_comment_floor = {"exploratory": 500, "standard": 1500, "deep": 3000}[depth]
            raw_comment_multiplier = {"exploratory": 2, "standard": 3, "deep": 5}[depth]
            row.update({
                "target_raw_video_candidates": math.ceil(parent_floor * 1.5),
                "target_raw_comment_candidates": max(raw_comment_floor, records * raw_comment_multiplier),
                "collection_cap_comments_per_video": 100,
                "target_relevant_videos": parent_floor,
                "target_transcript_videos": transcript_target,
                "min_transcript_video_pct": 60.0,
                "comment_collection": "Use commentThreads.list for top-level comments and comments.list for missing replies; preserve pagination and disabled-comment statuses.",
                "caption_collection": "Official caption download is not available for arbitrary public videos; recover public tracks in a separate restartable stage after relevance filtering.",
            })
        rows.append(row)

    min_sources = min(len(channels), {"exploratory": 3, "standard": 4, "deep": 5}[depth])
    plan = {
        "schema_version": "2.0",
        "created_at": utc_now(),
        "mode": mode,
        "depth": depth,
        "target_included_records": total,
        "target_is_post_clean": True,
        "requested_target_total": requested_total,
        "minimum_distinct_sources": min_sources,
        "allocation": rows,
        "allocation_semantics": {
            "floor": "Minimum retained evidence needed for this source to satisfy its declared role.",
            "goal": "Planning target used to budget collection; it is not a selection cutoff.",
            "cap": "Maximum retained contribution after reallocation and concentration control.",
            "reallocation": "Only sources explicitly marked optional may be reallocated. Core-source sufficiency never waives a required completion-family floor.",
        },
        "round_strategy": [
            {
                "stage": "pilot",
                "purpose": "Learn user vocabulary, ambiguity, brands, scenes, and reject terms with 10-15 high-recall queries per core search source.",
            },
            {
                "stage": "round_1",
                "purpose": "Run the frozen broad matrix and collect the first evidence tranche.",
            },
            {
                "stage": "preliminary_analysis",
                "purpose": "Clean the first tranche, calibrate a stratified taxonomy sample, and identify evidence gaps.",
            },
            {
                "stage": "round_2",
                "purpose": "Append narrow queries for missing scenes, brands, models, objections, ownership classes, and source types.",
            },
            {
                "stage": "supplement",
                "purpose": "Use Amazon, app stores, and other lower-risk supplements to test the preliminary conclusions and purchase objections.",
            },
            {
                "stage": "targeted_completion",
                "purpose": "Run bounded, evidence-gap-driven sampling across Facebook, TikTok, Instagram, X, review platforms, independent/store review pages, app stores, and any other required completion family.",
            },
        ],
        "cross_source_evidence_floors": {
            "owned_or_verified_use_records": max(50, math.ceil(total * 0.20)),
            "independent_parent_units": max(25, sum(row["min_distinct_parents"] for row in rows)),
            "negative_or_defect_records_for_product_improvement": max(50, math.ceil(total * 0.10)) if mode in {"product-improvement", "rating-recovery"} else 0,
        },
        "stopping_rule": "Stop only after core evidence gates and every required source-family completion gate pass. If gates miss, complete targeted append rounds and stop partial only after two successive query/parent expansions each add less than 5% new relevant records, with all shortfalls documented.",
        "login_rule": "A normal login wall or expired session becomes waiting_for_user_login. Ask the user to log in directly; never request credentials. CAPTCHA, checkpoint, 403, 429, or an explicit access limit stops that route.",
        "interpretation_rules": [
            "Record targets are evidence-coverage goals, not a probability sample or population representativeness claim.",
            "Raw candidate targets are collection goals before relevance filtering, deduplication, parent caps, and quality exclusions; they are not added to the post-clean total.",
            "YouTube comments, transcript-videos, forum posts, Reddit records, reviews, and first-party cases keep separate denominators.",
            "Cross-channel agreement requires at least three independent sources that each meet their record and parent floors.",
            "A high-risk social source below its interpretability floor contributes examples only, not incidence or consensus.",
            "Meeting YouTube, Reddit, Amazon, or any other core goal does not waive Facebook, TikTok, Instagram, X, vertical-community, review-platform, independent-web, or app-store cells declared required for completion.",
        ],
    }
    if mode == "rating-recovery":
        plan["rating_recovery_profile"] = {
            "objective": "Identify controllable causes of low ratings and prioritize product, onboarding, listing, and support changes without promising a rating outcome.",
            "baseline_snapshot_required_fields": [
                "captured_at",
                "listing_url",
                "asin",
                "displayed_rating",
                "rating_count",
                "parent_child_scope",
            ],
            "evidence_strata": {
                "target_model_direct_records": 30,
                "target_model_rating_bearing_records": 20,
                "target_model_low_star_records": 10,
                "recent_target_rating_records": 10,
                "direct_evidence_sources": 2,
            },
            "rating_driver_types": [
                "product_performance_or_defect",
                "setup_or_workflow_friction",
                "expectation_or_listing_mismatch",
                "support_or_recovery",
                "not_enough_evidence",
            ],
            "required_separations": [
                "target_model_direct_vs_adjacent_model_vs_category_vs_competitor",
                "parent_rating_vs_child_variation_evidence",
                "recent_window_vs_older_durability_evidence",
                "rating_distribution_vs_sampled_review_text",
                "Amazon_displayed_rating_vs_simple_arithmetic_sensitivity",
            ],
            "proof_boundary": "VOC can prioritize interventions. Only post-change rating, review, return, and support data can establish whether the displayed rating recovered.",
        }
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--depth", choices=("exploratory", "standard", "deep"), default="standard")
    parser.add_argument("--channels", nargs="+", required=True)
    parser.add_argument("--target-total", type=int, default=0, help="Optional post-clean total override.")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    plan = build_plan(args.mode, args.depth, args.channels, args.target_total)
    write_json(Path(args.output), plan)
    print(json.dumps({
        "output": str(Path(args.output).resolve()),
        "mode": args.mode,
        "depth": args.depth,
        "target_included_records": plan["target_included_records"],
        "allocation": {row["source"]: row["target_included_records"] for row in plan["allocation"]},
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
