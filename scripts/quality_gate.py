#!/usr/bin/env python3
"""Apply source balance, traceability, annotation, and audit gates."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any

from common import normalize_space, read_json, read_jsonl, write_json


from workflow_contract import valid_voc, digest


DEFAULTS = {
    "min_included_records": 50,
    "min_sources": 2,
    "max_single_source_pct": 70.0,
    "min_annotation_coverage_pct": 95.0,
    "max_missing_url_pct": 5.0,
    "max_parent_share_pct": 20.0,
    "min_audit_accuracy_pct": 90.0,
}


def load_thresholds(path: str) -> dict[str, Any]:
    thresholds = dict(DEFAULTS)
    if not path:
        return thresholds
    payload = read_json(Path(path))
    if isinstance(payload.get("quality_thresholds"), dict):
        payload = payload["quality_thresholds"]
    for key in DEFAULTS:
        if key in payload:
            thresholds[key] = payload[key]
    return thresholds


def load_sample_plan(path: str) -> dict[str, Any]:
    if not path:
        return {}
    payload = read_json(Path(path))
    if isinstance(payload, dict) and isinstance(payload.get("allocation"), list):
        return payload
    plan = payload.get("sample_plan", {}) if isinstance(payload, dict) else {}
    return plan if isinstance(plan, dict) else {}


def gate(name: str, actual: Any, operator: str, threshold: Any, passed: bool, critical: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "actual": actual,
        "operator": operator,
        "threshold": threshold,
        "passed": passed,
        "critical": critical,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--validation", required=True)
    parser.add_argument("--audit-result", default="")
    parser.add_argument("--config", default="")
    parser.add_argument("--round-summary", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    all_records = read_jsonl(Path(args.records))
    records = [row for row in all_records if valid_voc(row)]
    annotations = read_jsonl(Path(args.annotations))
    validation = read_json(Path(args.validation))
    config_payload = read_json(Path(args.config)) if args.config else {}
    thresholds = load_thresholds(args.config)
    sample_plan = load_sample_plan(args.config)
    round_summary = read_json(Path(args.round_summary)) if args.round_summary and Path(args.round_summary).exists() else {}
    sources = Counter(normalize_space(row.get("source")) or "unknown" for row in records)
    total = len(records)
    largest_source_pct = max((count / total * 100.0 for count in sources.values()), default=0.0)
    missing_url_pct = sum(not normalize_space(row.get("source_url")) for row in records) / total * 100.0 if total else 100.0

    parent_counts = Counter(
        (normalize_space(row.get("source")), normalize_space(row.get("parent_id")))
        for row in records
        if normalize_space(row.get("parent_id"))
    )
    largest_parent_pct = max((count / total * 100.0 for count in parent_counts.values()), default=0.0)
    coverage_pct = float(validation.get("annotation_coverage_pct", 0.0))
    validation_errors = int(validation.get("error_count", 0))
    validation_fresh = validation.get("input_digests",{}).get("records")==digest(all_records) and validation.get("input_digests",{}).get("annotations")==digest(annotations)

    audit_path = Path(args.audit_result) if args.audit_result else None
    audit = read_json(audit_path) if audit_path and audit_path.exists() else {}
    reviewed = int(audit.get("reviewed", 0) or 0)
    fully_correct = int(audit.get("fully_correct", 0) or 0)
    audit_accuracy = fully_correct / reviewed * 100.0 if reviewed else 0.0
    audit_target = min(total, max(50, math.ceil(total * 0.05))) if total else 0

    gates = [
        gate("annotation_validation_inputs_current", validation_fresh, "==", True, validation_fresh),
        gate("included_records", total, ">=", thresholds["min_included_records"], total >= thresholds["min_included_records"]),
        gate("distinct_sources", len(sources), ">=", thresholds["min_sources"], len(sources) >= thresholds["min_sources"]),
        gate("largest_source_pct", round(largest_source_pct, 2), "<=", thresholds["max_single_source_pct"], largest_source_pct <= thresholds["max_single_source_pct"]),
        gate("annotation_coverage_pct", round(coverage_pct, 2), ">=", thresholds["min_annotation_coverage_pct"], coverage_pct >= thresholds["min_annotation_coverage_pct"]),
        gate("missing_source_url_pct", round(missing_url_pct, 2), "<=", thresholds["max_missing_url_pct"], missing_url_pct <= thresholds["max_missing_url_pct"]),
        gate("annotation_validation_errors", validation_errors, "==", 0, validation_errors == 0),
        gate("audit_records_reviewed", reviewed, ">=", audit_target, reviewed >= audit_target),
        gate("audit_accuracy_pct", round(audit_accuracy, 2), ">=", thresholds["min_audit_accuracy_pct"], audit_accuracy >= thresholds["min_audit_accuracy_pct"]),
        gate("largest_parent_share_pct", round(largest_parent_pct, 2), "<=", thresholds["max_parent_share_pct"], largest_parent_pct <= thresholds["max_parent_share_pct"]),
    ]

    research_mode = normalize_space(config_payload.get("research_mode"))
    rating_recovery = config_payload.get("rating_recovery", {}) if isinstance(config_payload, dict) else {}
    if research_mode == "rating-recovery":
        profile = sample_plan.get("rating_recovery_profile", {})
        strata = rating_recovery.get("evidence_strata", profile.get("evidence_strata", {}))
        baseline = rating_recovery.get("baseline_snapshot", {})
        required_baseline_fields = profile.get("baseline_snapshot_required_fields", [
            "captured_at", "listing_url", "asin", "displayed_rating", "rating_count", "parent_child_scope"
        ])
        missing_baseline_fields = [
            field for field in required_baseline_fields
            if baseline.get(field) in (None, "", [], {})
        ]
        gates.append(gate(
            "rating_baseline_snapshot_complete",
            len(missing_baseline_fields),
            "==",
            0,
            not missing_baseline_fields,
        ))

        direct_relations = {"target_model_direct", "target_direct", "direct_target"}
        direct_records = [
            row for row in records
            if normalize_space(row.get("product_relation")).lower() in direct_relations
        ]
        rating_bearing = [row for row in direct_records if isinstance(row.get("rating"), (int, float))]
        low_star = [row for row in rating_bearing if float(row["rating"]) <= 3.0]
        recent_buckets = {"recent_90d", "recent_180d", "current_period"}
        recent_rating = [
            row for row in rating_bearing
            if normalize_space(row.get("time_bucket")).lower() in recent_buckets
        ]
        direct_sources = {
            normalize_space(row.get("source")) for row in direct_records if normalize_space(row.get("source"))
        }
        rating_counts = {
            "target_model_direct_records": len(direct_records),
            "target_model_rating_bearing_records": len(rating_bearing),
            "target_model_low_star_records": len(low_star),
            "recent_target_rating_records": len(recent_rating),
            "direct_evidence_sources": len(direct_sources),
        }
        for field, actual in rating_counts.items():
            threshold = int(strata.get(field, 0) or 0)
            if threshold:
                gates.append(gate(f"rating_{field}", actual, ">=", threshold, actual >= threshold))

        annotations_by_id = {
            normalize_space(row.get("source_id")): row
            for row in annotations
            if normalize_space(row.get("source_id"))
        }
        allowed_drivers = set(rating_recovery.get("rating_driver_types", profile.get("rating_driver_types", [])))
        coded_low_star = 0
        for row in low_star:
            annotation = annotations_by_id.get(normalize_space(row.get("source_id")), {})
            driver = normalize_space(annotation.get("rating_driver"))
            if driver in allowed_drivers:
                coded_low_star += 1
        driver_coverage_pct = coded_low_star / len(low_star) * 100.0 if low_star else 0.0
        gates.append(gate(
            "rating_low_star_driver_coverage_pct",
            round(driver_coverage_pct, 2),
            ">=",
            90.0,
            driver_coverage_pct >= 90.0,
        ))

    source_parent_counts = Counter()
    for source, parent_id in parent_counts:
        if parent_id:
            source_parent_counts[source] += 1
    for allocation in sample_plan.get("allocation", []):
        source = normalize_space(allocation.get("source"))
        if not source:
            continue
        legacy_target = int(allocation.get("target_included_records", 0) or 0)
        record_floor = int(allocation.get("record_floor", legacy_target) or 0)
        record_goal = int(allocation.get("record_goal", legacy_target) or 0)
        record_cap = int(allocation.get("record_cap", 0) or 0)
        required_source = bool(allocation.get("required_for_completion", allocation.get("required", True)))
        parent_target = int(allocation.get("min_distinct_parents", 0) or 0)
        source_members = [
            normalize_space(member)
            for member in allocation.get("source_members", [source])
            if normalize_space(member)
        ] or [source]
        source_record_count = sum(sources[member] for member in source_members)
        source_parent_count = sum(source_parent_counts[member] for member in source_members)
        if record_floor:
            gates.append(gate(
                f"source_{source}_record_floor",
                source_record_count,
                ">=",
                record_floor,
                source_record_count >= record_floor,
                critical=required_source,
            ))
        if record_goal:
            gates.append(gate(
                f"source_{source}_record_goal",
                source_record_count,
                ">=",
                record_goal,
                source_record_count >= record_goal,
                critical=False,
            ))
        if record_cap:
            gates.append(gate(
                f"source_{source}_record_cap",
                source_record_count,
                "<=",
                record_cap,
                source_record_count <= record_cap,
            ))
        if parent_target:
            gates.append(gate(
                f"source_{source}_distinct_parents",
                source_parent_count,
                ">=",
                parent_target,
                source_parent_count >= parent_target,
                critical=required_source,
            ))

    unknown_query_ids = round_summary.get("unknown_attempt_query_ids", []) if isinstance(round_summary, dict) else []
    if args.round_summary:
        gates.append(gate(
            "round_attempt_query_ids_valid",
            len(unknown_query_ids),
            "==",
            0,
            len(unknown_query_ids) == 0,
        ))

    policy_warnings: list[str] = []
    browser_counts = Counter(
        normalize_space(row.get("source"))
        for row in records
        if normalize_space(row.get("access_mode")) == "browser_assisted"
    )
    for source, count in sorted(browser_counts.items()):
        if source in {"x", "tiktok", "facebook", "instagram"} and count > 30:
            policy_warnings.append(
                f"{source} has {count} browser-assisted records; review the study contract and platform authorization before reuse or scale."
            )

    failed = [item for item in gates if item["critical"] and not item["passed"]]
    waiting_sources = round_summary.get("waiting_for_user_login_sources", []) if isinstance(round_summary, dict) else []
    saturation_stop_allowed = bool(round_summary.get("saturation_stop_allowed")) if isinstance(round_summary, dict) else False
    coverage_prefixes = (
        "included_records",
        "distinct_sources",
        "largest_source_pct",
        "source_",
    )
    coverage_failed = any(item["name"].startswith(coverage_prefixes) for item in failed)
    if total == 0 or not annotations:
        status = "blocked"
    elif failed:
        status = "needs_append" if coverage_failed and not saturation_stop_allowed else "partial"
    else:
        status = "pass"

    result = {
        "status": status,
        "input_digests": {"records":digest(all_records),"annotations":digest(annotations),"contract":digest(config_payload),"audit_result":digest(audit),"round_summary":digest(round_summary)},
        "thresholds": thresholds,
        "gates": gates,
        "failed_gate_names": [item["name"] for item in failed],
        "source_counts": dict(sorted(sources.items())),
        "excluded_context_or_discovery_records": len(all_records)-len(records),
        "delivery_acceptance_required": True,
        "policy_warnings": policy_warnings,
        "process": {
            "round_summary_supplied": bool(args.round_summary),
            "waiting_for_user_login_sources": waiting_sources,
            "consecutive_low_yield_expansions": round_summary.get("consecutive_low_yield_expansions", 0) if isinstance(round_summary, dict) else 0,
            "saturation_stop_allowed": saturation_stop_allowed,
        },
        "rating_recovery": {
            "enabled": research_mode == "rating-recovery",
            "baseline_missing_fields": missing_baseline_fields if research_mode == "rating-recovery" else [],
            "evidence_counts": rating_counts if research_mode == "rating-recovery" else {},
            "low_star_driver_coverage_pct": round(driver_coverage_pct, 2) if research_mode == "rating-recovery" else None,
        },
        "notes": [
            "Pass means the declared evidence package met structural gates; it is not platform-population representativeness.",
            "Needs_append means coverage gates miss and the two-expansion saturation rule has not been met; collection should continue.",
            "Partial findings may support hypotheses and targeted follow-up, not category-wide incidence claims.",
        ],
    }
    write_json(Path(args.output), result)
    print(f"status={status} failed={len(failed)}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
