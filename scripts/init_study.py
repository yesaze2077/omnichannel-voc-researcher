#!/usr/bin/env python3
"""Create a restartable omnichannel VOC study workspace."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

from common import utc_now, write_json
from plan_sample import MODES, build_plan, normalize_channels


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:60] or "voc-study"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--market", required=True)
    parser.add_argument("--decision", required=True)
    parser.add_argument("--channels", nargs="+", required=True)
    parser.add_argument("--output-root", default="work")
    parser.add_argument("--timestamp", default="")
    parser.add_argument("--mode", choices=MODES, default="product-improvement")
    parser.add_argument("--depth", choices=("exploratory", "standard", "deep"), default="standard")
    parser.add_argument("--target-total", type=int, default=0, help="Optional post-clean total override.")
    parser.add_argument("--target-per-channel", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()

    timestamp = args.timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    study_dir = Path(args.output_root) / f"{slugify(args.study)}_{timestamp}"
    for relative in (
        "raw",
        "manifests",
        "normalized",
        "analysis/statistics",
        "reports",
        "logs",
    ):
        (study_dir / relative).mkdir(parents=True, exist_ok=True)

    channels = normalize_channels(args.channels)
    sample_plan = build_plan(args.mode, args.depth, channels, args.target_total)
    source_targets = {row["source"]: row for row in sample_plan["allocation"]}
    if args.target_per_channel:
        for row in sample_plan["allocation"]:
            row["target_included_records"] = args.target_per_channel
        sample_plan["target_included_records"] = args.target_per_channel * len(channels)
        sample_plan["legacy_equal_channel_override"] = True
    contract = {
        "schema_version": "2.0",
        "status": "draft",
        "study": args.study,
        "category": args.category,
        "market": args.market,
        "decision_question": args.decision,
        "created_at": utc_now(),
        "channels": channels,
        "research_mode": args.mode,
        "research_depth": args.depth,
        "sample_plan": sample_plan,
        "time_window": {"start": "", "end": "", "older_durability_evidence": "separate"},
        "scope": {"brands": [], "products": [], "vehicles": [], "exclusions": []},
        "collection_policy": {
            "api_first_sources": [source for source in channels if source == "youtube"],
            "open_web_main_sources": [source for source in channels if source in {"reddit", "owner_forum"}],
            "supervised_browser_sources": [
                source for source in channels if source in {"amazon", "x", "tiktok", "facebook", "instagram"}
            ],
            "supervised": True,
            "read_only": True,
            "high_risk_social_record_cap": max(
                [30, *[
                    row["target_included_records"]
                    for row in sample_plan["allocation"]
                    if row["source"] in {"x", "tiktok", "facebook", "instagram"}
                ]]
            ),
            "default_comments_per_parent": 10,
            "stop_signals": ["captcha", "checkpoint", "reauth", "403", "429", "access_limit"],
            "no_bypass": True,
        },
        "quality_thresholds": {
            "min_included_records": sample_plan["target_included_records"],
            "min_sources": sample_plan["minimum_distinct_sources"],
            "max_single_source_pct": 70.0,
            "min_annotation_coverage_pct": 95.0,
            "max_missing_url_pct": 5.0,
            "max_parent_share_pct": 20.0,
            "min_audit_accuracy_pct": 90.0,
        },
        "report": {"audience": "", "language": "user_requested", "required_decisions": []},
        "stop_condition": "Quality gate passes or valid planned sources are exhausted and status is partial.",
    }

    source_plan = {
        "study": args.study,
        "created_at": utc_now(),
        "sources": [
            {
                "source": source,
                "role": source_targets[source]["role"],
                "target_records": source_targets[source]["target_included_records"],
                "min_distinct_parents": source_targets[source]["min_distinct_parents"],
                "access_order": source_targets[source]["access_order"],
                "status": "planned",
                "records_collected": 0,
                "failure_reason": "",
            }
            for source in channels
        ],
    }

    write_json(study_dir / "study_contract.json", contract)
    write_json(study_dir / "source_plan.json", source_plan)
    write_json(study_dir / "manifests" / "collection_manifest.json", {"attempts": []})
    print(study_dir.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
