#!/usr/bin/env python3
"""Apply source balance, traceability, annotation, and audit gates."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any

from common import normalize_space, read_json, read_jsonl, write_json


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
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = read_jsonl(Path(args.records))
    annotations = read_jsonl(Path(args.annotations))
    validation = read_json(Path(args.validation))
    thresholds = load_thresholds(args.config)
    sample_plan = load_sample_plan(args.config)
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

    audit_path = Path(args.audit_result) if args.audit_result else None
    audit = read_json(audit_path) if audit_path and audit_path.exists() else {}
    reviewed = int(audit.get("reviewed", 0) or 0)
    fully_correct = int(audit.get("fully_correct", 0) or 0)
    audit_accuracy = fully_correct / reviewed * 100.0 if reviewed else 0.0
    audit_target = min(total, max(50, math.ceil(total * 0.05))) if total else 0

    gates = [
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

    source_parent_counts = Counter()
    for source, parent_id in parent_counts:
        if parent_id:
            source_parent_counts[source] += 1
    for allocation in sample_plan.get("allocation", []):
        source = normalize_space(allocation.get("source"))
        if not source:
            continue
        record_target = int(allocation.get("target_included_records", 0) or 0)
        parent_target = int(allocation.get("min_distinct_parents", 0) or 0)
        if record_target:
            gates.append(gate(
                f"source_{source}_records",
                sources[source],
                ">=",
                record_target,
                sources[source] >= record_target,
            ))
        if parent_target:
            gates.append(gate(
                f"source_{source}_distinct_parents",
                source_parent_counts[source],
                ">=",
                parent_target,
                source_parent_counts[source] >= parent_target,
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
    if total == 0 or not annotations:
        status = "blocked"
    elif failed:
        status = "partial"
    else:
        status = "pass"

    result = {
        "status": status,
        "thresholds": thresholds,
        "gates": gates,
        "failed_gate_names": [item["name"] for item in failed],
        "source_counts": dict(sorted(sources.items())),
        "policy_warnings": policy_warnings,
        "notes": [
            "Pass means the declared evidence package met structural gates; it is not platform-population representativeness.",
            "Partial findings may support hypotheses and targeted follow-up, not category-wide incidence claims.",
        ],
    }
    write_json(Path(args.output), result)
    print(f"status={status} failed={len(failed)}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
