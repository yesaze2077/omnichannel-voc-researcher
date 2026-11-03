#!/usr/bin/env python3
"""End-to-end deterministic smoke tests for the omnichannel VOC skill."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(name: str, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPTS / name), *args]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != expected:
        raise AssertionError(
            f"command failed ({result.returncode}, expected {expected}): {' '.join(command)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def write_raw(path: Path, source: str) -> None:
    fieldnames = [
        "id",
        "parent_id",
        "body",
        "url",
        "author",
        "brand",
        "rating",
        "verified",
        "likes",
        "date",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(20):
            negative = index % 2 == 0
            writer.writerow(
                {
                    "id": f"{source}-{index}",
                    "parent_id": f"{source}-parent-{index // 2}",
                    "body": (
                        f"Record {index} reports weak airflow and bracket trouble after owned use."
                        if negative
                        else f"Record {index} reports easy installation and strong airflow after owned use."
                    ),
                    "url": f"https://example.invalid/{source}/{index}",
                    "author": f"user-{source}-{index}",
                    "brand": "BrandA" if index < 10 else "BrandB",
                    "rating": 1 if negative else 5,
                    "verified": "true" if source == "amazon" else "",
                    "likes": index,
                    "date": f"2026-07-{(index % 28) + 1:02d}",
                }
            )
        for index in range(2):
            writer.writerow(
                {
                    "id": f"{source}-promo-{index}",
                    "parent_id": f"{source}-promo-parent",
                    "body": f"Shop now and use code SAVE{index} for this sponsored post.",
                    "url": f"https://example.invalid/{source}/promo/{index}",
                    "author": f"seller-{source}",
                    "brand": "BrandA",
                    "rating": "",
                    "verified": "",
                    "likes": 0,
                    "date": "2026-07-30",
                }
            )


def taxonomy() -> dict:
    return {
        "version": "1.0",
        "category": "UTV cab fans",
        "level_1": [
            {"id": "people_context", "label": "People and context", "level_2": []},
            {
                "id": "functional_value",
                "label": "Functional value",
                "level_2": [
                    {
                        "id": "performance",
                        "label": "Performance",
                        "level_3": [
                            {"id": "airflow", "label": "Airflow", "definition": "Air movement performance."},
                            {"id": "fitment", "label": "Fitment", "definition": "Fit and bracket compatibility."},
                        ],
                    }
                ],
            },
            {"id": "assurance_value", "label": "Assurance value", "level_2": []},
            {
                "id": "experience_value",
                "label": "Experience value",
                "level_2": [
                    {
                        "id": "setup",
                        "label": "Setup",
                        "level_3": [
                            {"id": "installation", "label": "Installation", "definition": "Installation effort."}
                        ],
                    }
                ],
            },
        ],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="omnichannel-voc-test-") as temp:
        work = Path(temp)
        sample_plan_path = work / "sample_plan.json"
        run(
            "plan_sample.py",
            "--mode",
            "product-improvement",
            "--depth",
            "deep",
            "--channels",
            "youtube",
            "owner_forum",
            "reddit",
            "amazon",
            "x",
            "tiktok",
            "facebook",
            "ins",
            "review_site",
            "independent_web",
            "--output",
            str(sample_plan_path),
        )
        sample_plan = json.loads(sample_plan_path.read_text(encoding="utf-8"))
        allocations = {row["source"]: row for row in sample_plan["allocation"]}
        core_count = sum(allocations[source]["target_included_records"] for source in ("youtube", "owner_forum", "reddit"))
        assert sample_plan["target_included_records"] == 1500
        assert core_count / sample_plan["target_included_records"] >= 0.70
        assert allocations["youtube"]["access_order"][0] == "official_api_search_metadata_comments"
        assert allocations["youtube"]["target_transcript_videos"] > 0
        assert allocations["youtube"]["target_raw_comment_candidates"] >= 3000
        assert allocations["youtube"]["target_raw_comment_candidates"] > allocations["youtube"]["target_included_records"]
        assert allocations["youtube"]["target_raw_video_candidates"] >= allocations["youtube"]["target_relevant_videos"]
        assert "instagram" in allocations
        for source in ("x", "tiktok", "facebook", "instagram", "review_site", "independent_web"):
            assert allocations[source]["target_included_records"] >= 30
            assert allocations[source]["min_distinct_parents"] >= 10
            assert allocations[source]["required_for_completion"] is True
        for source, allocation in allocations.items():
            assert allocation["record_floor"] <= allocation["record_goal"] <= allocation["record_cap"], source
        assert sample_plan["allocation_semantics"]["goal"].endswith("not a selection cutoff.")
        assert len(sample_plan["round_strategy"]) == 6
        assert sample_plan["round_strategy"][-1]["stage"] == "targeted_completion"

        rating_plan_path = work / "rating_recovery_plan.json"
        run(
            "plan_sample.py",
            "--mode", "rating-recovery",
            "--depth", "deep",
            "--channels",
            "youtube", "owner_forum", "reddit", "amazon",
            "facebook", "tiktok", "instagram", "x",
            "review_site", "independent_web", "appstore",
            "--output", str(rating_plan_path),
        )
        rating_plan = json.loads(rating_plan_path.read_text(encoding="utf-8"))
        rating_allocations = {row["source"]: row for row in rating_plan["allocation"]}
        assert rating_plan["target_included_records"] == 1080
        assert rating_plan["mode"] == "rating-recovery"
        assert rating_plan["rating_recovery_profile"]["evidence_strata"]["target_model_low_star_records"] == 10
        assert rating_allocations["app_store"]["record_floor"] >= 20
        assert rating_allocations["app_store"]["min_distinct_parents"] == 2
        for source in ("facebook", "tiktok", "instagram", "x", "review_site", "independent_web", "app_store"):
            assert rating_allocations[source]["required_for_completion"] is True

        rating_matrix = work / "rating_recovery_matrix.jsonl"
        run(
            "build_search_matrix.py",
            "--category", "4x6 thermal shipping label printers",
            "--mode", "rating-recovery",
            "--stage", "formal",
            "--sources", "youtube",
            "--core-terms", "MUNBYN RW403B,bluetooth shipping label printer",
            "--target-terms", "MUNBYN RW403B",
            "--target-query-floor", "20",
            "--problems", "bluetooth disconnect,label misalignment,small text clarity",
            "--workflows", "iPhone,Android,Mac,Windows",
            "--queries-per-source", "60",
            "--output", str(rating_matrix),
        )
        rating_rows = [json.loads(line) for line in rating_matrix.read_text(encoding="utf-8").splitlines()]
        assert len(rating_rows) == 60
        rating_dimensions = {row["dimension"] for row in rating_rows}
        assert "rating_risk" in rating_dimensions
        assert "expectation_mismatch" in rating_dimensions
        assert "support_recovery" in rating_dimensions
        assert sum("munbyn rw403b" in row["query"].lower() for row in rating_rows) >= 20
        assert not any("jadens munbyn rw403b" in row["query"].lower() for row in rating_rows)

        rating_records_path = work / "rating_records.jsonl"
        rating_annotations_path = work / "rating_annotations.jsonl"
        rating_records = []
        rating_annotations = []
        for index in range(30):
            source = "amazon" if index < 20 else "youtube"
            rating = 1 if index < 10 else 4
            source_id = f"{source}:rating-{index}"
            rating_records.append({
                "source_id": source_id,
                "source": source,
                "parent_id": f"{source}:parent-{index}",
                "record_type": "review" if source == "amazon" else "comment",
                "text": "Direct target-model owner experience with setup and print quality.",
                "source_url": f"https://example.invalid/{source}/rating-{index}",
                "rating": rating,
                "product_relation": "target_model_direct",
                "time_bucket": "recent_90d",
                "access_mode": "public_page",
            })
            rating_annotations.append({
                "source_id": source_id,
                "sentiment": "negative" if rating <= 3 else "mixed",
                "level_3_tags": [],
                "ownership_signal": "owned_use",
                "funnel_stage": "ownership",
                "severity": "high" if rating <= 3 else "low",
                "evidence_excerpt": "setup and print quality",
                "taxonomy_version": "1.0",
                "rating_driver": "setup_or_workflow_friction",
            })
        rating_records_path.write_text("".join(json.dumps(row) + "\n" for row in rating_records), encoding="utf-8")
        rating_annotations_path.write_text("".join(json.dumps(row) + "\n" for row in rating_annotations), encoding="utf-8")
        rating_validation_path = work / "rating_validation.json"
        rating_validation_path.write_text(json.dumps({"annotation_coverage_pct": 100.0, "error_count": 0}), encoding="utf-8")
        rating_audit_path = work / "rating_audit.json"
        rating_audit_path.write_text(json.dumps({"reviewed": 30, "fully_correct": 30}), encoding="utf-8")
        rating_contract_path = work / "rating_contract.json"
        rating_contract_path.write_text(json.dumps({
            "research_mode": "rating-recovery",
            "sample_plan": rating_plan,
            "quality_thresholds": {
                "min_included_records": 30,
                "min_sources": 2,
                "max_single_source_pct": 70.0,
                "min_annotation_coverage_pct": 95.0,
                "max_missing_url_pct": 5.0,
                "max_parent_share_pct": 20.0,
                "min_audit_accuracy_pct": 90.0,
            },
            "rating_recovery": {
                "baseline_snapshot": {
                    "captured_at": "2026-08-19T00:00:00Z",
                    "listing_url": "https://www.amazon.com/dp/example",
                    "asin": "EXAMPLE",
                    "displayed_rating": 4.2,
                    "rating_count": 100,
                    "parent_child_scope": "parent",
                },
                "evidence_strata": rating_plan["rating_recovery_profile"]["evidence_strata"],
                "rating_driver_types": rating_plan["rating_recovery_profile"]["rating_driver_types"],
            },
        }), encoding="utf-8")
        rating_gate_path = work / "rating_gate.json"
        run(
            "quality_gate.py",
            "--records", str(rating_records_path),
            "--annotations", str(rating_annotations_path),
            "--validation", str(rating_validation_path),
            "--audit-result", str(rating_audit_path),
            "--config", str(rating_contract_path),
            "--output", str(rating_gate_path),
            expected=2,
        )
        rating_gate = json.loads(rating_gate_path.read_text(encoding="utf-8"))
        assert rating_gate["rating_recovery"]["enabled"] is True
        assert rating_gate["rating_recovery"]["baseline_missing_fields"] == []
        assert rating_gate["rating_recovery"]["low_star_driver_coverage_pct"] == 100.0

        pilot_matrix = work / "pilot_matrix.jsonl"
        pilot_summary = work / "pilot_matrix_summary.json"
        run(
            "build_search_matrix.py",
            "--category",
            "4x6 thermal shipping label printers",
            "--mode",
            "listing-content",
            "--stage",
            "pilot",
            "--sources",
            "youtube",
            "reddit",
            "--core-terms",
            "4x6 thermal label printer,bluetooth shipping label printer",
            "--brands",
            "BrandA,BrandB",
            "--scenes",
            "Etsy shipping,Shopify fulfillment",
            "--problems",
            "label calibration,bluetooth connection",
            "--workflows",
            "iPhone,Android,Mac,Windows",
            "--communities",
            "EtsySellers,smallbusiness",
            "--reject-context-terms",
            "mini label maker,receipt printer",
            "--queries-per-source",
            "12",
            "--reddit-entrypoint",
            "old",
            "--reddit-authorization-status",
            "user_confirmed",
            "--output",
            str(pilot_matrix),
            "--summary",
            str(pilot_summary),
        )
        pilot_rows = [json.loads(line) for line in pilot_matrix.read_text(encoding="utf-8").splitlines()]
        pilot_metrics = json.loads(pilot_summary.read_text(encoding="utf-8"))
        assert len(pilot_rows) == 24
        assert len({row["query_id"] for row in pilot_rows}) == 24
        assert {row["source"] for row in pilot_rows} == {"youtube", "reddit"}
        reddit_pilot_rows = [row for row in pilot_rows if row["source"] == "reddit"]
        assert all(row["preferred_entrypoint"] == "https://old.reddit.com" for row in reddit_pilot_rows)
        assert all(row["fallback_entrypoint"] == "https://www.reddit.com" for row in reddit_pilot_rows)
        assert all(row["access_mode"] == "authorized_browser_old_reddit" for row in reddit_pilot_rows)
        assert all(row["authorization_status"] == "user_confirmed" for row in reddit_pilot_rows)
        assert pilot_metrics["negative_query_share_pct"] <= 35.0
        assert len(pilot_metrics["dimension_counts"]) >= 5
        run(
            "build_search_matrix.py",
            "--category", "4x6 thermal shipping label printers",
            "--mode", "listing-content",
            "--stage", "pilot",
            "--sources", "youtube", "reddit",
            "--core-terms", "4x6 thermal label printer,bluetooth shipping label printer",
            "--brands", "BrandA,BrandB",
            "--scenes", "Etsy shipping,Shopify fulfillment",
            "--problems", "label calibration,bluetooth connection",
            "--workflows", "iPhone,Android,Mac,Windows",
            "--communities", "EtsySellers,smallbusiness",
            "--reject-context-terms", "mini label maker,receipt printer",
            "--queries-per-source", "12",
            "--reddit-entrypoint", "old",
            "--reddit-authorization-status", "user_confirmed",
            "--output", str(pilot_matrix),
            "--append",
        )
        assert len(pilot_matrix.read_text(encoding="utf-8").splitlines()) == 24
        reddit_access_summary = work / "reddit_access_summary.json"
        run(
            "configure_reddit_access.py",
            "--matrix", str(pilot_matrix),
            "--entrypoint", "old",
            "--authorization-status", "documented",
            "--summary", str(reddit_access_summary),
        )
        reddit_access_payload = json.loads(reddit_access_summary.read_text(encoding="utf-8"))
        assert reddit_access_payload["updated_reddit_rows"] == 12
        assert reddit_access_payload["access_mode"] == "authorized_browser_old_reddit"
        configured_rows = [json.loads(line) for line in pilot_matrix.read_text(encoding="utf-8").splitlines()]
        assert all(
            row.get("authorization_status") == "documented"
            for row in configured_rows
            if row["source"] == "reddit"
        )
        prior_terms = work / "prior_terms.json"
        prior_terms.write_text(json.dumps({"terms": [{"query": pilot_rows[0]["query"]}]}), encoding="utf-8")
        query_coverage = work / "query_coverage.json"
        run(
            "query_coverage.py",
            "--matrix", str(pilot_matrix),
            "--prior", str(prior_terms),
            "--source", pilot_rows[0]["source"],
            "--output", str(query_coverage),
        )
        query_coverage_payload = json.loads(query_coverage.read_text(encoding="utf-8"))
        assert query_coverage_payload["covered_exact"] == 1
        assert query_coverage_payload["covered_similar"] + query_coverage_payload["novel_after_similarity"] == 11

        round_1_matrix = work / "round_1_matrix.jsonl"
        round_2_matrix = work / "round_2_matrix.jsonl"
        supplement_matrix = work / "supplement_matrix.jsonl"
        completion_matrix = work / "targeted_completion_matrix.jsonl"
        for stage, path in (
            ("formal", round_1_matrix),
            ("round_2", round_2_matrix),
            ("supplement", supplement_matrix),
        ):
            command = [
                "--category", "4x6 thermal shipping label printers",
                "--mode", "listing-content",
                "--stage", stage,
                "--sources", "youtube", "reddit",
                "--core-terms", "4x6 thermal label printer,bluetooth shipping label printer",
                "--brands", "BrandA,BrandB",
                "--scenes", "Etsy shipping,Shopify fulfillment",
                "--problems", "label calibration,bluetooth connection",
                "--workflows", "iPhone,Android,Mac,Windows",
                "--queries-per-source", "4",
                "--output", str(path),
            ]
            if stage in {"round_2", "supplement"}:
                command.extend(["--gap-terms", "driver dependency,label misalignment"])
            run("build_search_matrix.py", *command)

        run(
            "build_search_matrix.py",
            "--category", "4x6 thermal shipping label printers",
            "--mode", "listing-content",
            "--stage", "targeted_completion",
            "--sources", "facebook", "tiktok", "instagram", "x", "review_site", "independent_web",
            "--core-terms", "4x6 thermal label printer,bluetooth shipping label printer",
            "--gap-terms", "driver dependency,label misalignment,warranty support",
            "--communities", "trustpilot.com,sitejabber.com,munbyn.com",
            "--queries-per-source", "4",
            "--output", str(completion_matrix),
        )
        completion_rows = [json.loads(line) for line in completion_matrix.read_text(encoding="utf-8").splitlines()]
        assert len(completion_rows) == 24
        assert {row["source"] for row in completion_rows} == {"facebook", "tiktok", "instagram", "x", "review_site", "independent_web"}
        assert all(row["round"] == "round_3_targeted_completion" for row in completion_rows)
        assert all(row["access_mode"] == "public_page" for row in completion_rows if row["source"] in {"review_site", "independent_web"})

        all_matrix = work / "all_matrix.jsonl"
        all_matrix.write_text(
            pilot_matrix.read_text(encoding="utf-8")
            + round_1_matrix.read_text(encoding="utf-8")
            + round_2_matrix.read_text(encoding="utf-8")
            + supplement_matrix.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        matrices = {
            row["round"]: row
            for row in [json.loads(line) for line in all_matrix.read_text(encoding="utf-8").splitlines()]
        }
        attempts_path = work / "round_attempts.jsonl"
        attempt_rows = []
        for round_id, new_relevant in (("pilot", 100), ("round_1", 100), ("round_2", 5), ("supplement", 4)):
            row = matrices[round_id]
            attempt_rows.append({
                "query_id": row["query_id"],
                "source": row["source"],
                "round": round_id,
                "is_expansion": round_id in {"round_2", "supplement"},
                "discovered_parents": 10,
                "new_parents": 5,
                "raw_records": new_relevant * 2,
                "relevant_records": new_relevant,
                "new_relevant_records": new_relevant,
                "retained_records": new_relevant,
                "duplicate_records": 0,
                "status": "complete",
            })
        attempts_path.write_text("".join(json.dumps(row) + "\n" for row in attempt_rows), encoding="utf-8")
        round_summary = work / "round_summary.json"
        run(
            "round_yield.py",
            "--matrix", str(all_matrix),
            "--attempts", str(attempts_path),
            "--output", str(round_summary),
        )
        round_payload = json.loads(round_summary.read_text(encoding="utf-8"))
        assert round_payload["consecutive_low_yield_expansions"] == 0
        assert round_payload["saturation_stop_allowed"] is False
        assert round_payload["unattempted_queries"] > 0

        normalized = work / "normalized.jsonl"
        for source in ("amazon", "reddit", "tiktok"):
            raw = work / f"{source}.csv"
            write_raw(raw, source)
            run(
                "normalize_records.py",
                "--input",
                str(raw),
                "--output",
                str(normalized),
                "--source",
                source,
                "--access-mode",
                "browser_assisted",
                "--append",
            )

        # Re-appending the same source must not duplicate records.
        run(
            "normalize_records.py",
            "--input",
            str(work / "amazon.csv"),
            "--output",
            str(normalized),
            "--source",
            "amazon",
            "--access-mode",
            "browser_assisted",
            "--append",
        )

        context_raw = work / "reddit_context.jsonl"
        context_raw.write_text(
            json.dumps({
                "source_id": "reddit:t1_context",
                "parent_id": "t3_context",
                "record_type": "comment",
                "text": "Bluetooth setup worked after choosing the printer app.",
                "source_url": "https://old.reddit.com/r/example/comments/context/comment/",
                "collected_at": "2026-08-18T01:02:03Z",
                "query_id": "q_context",
                "round": "pilot",
                "dimension": "workflow_platform",
                "scope": "EtsySellers",
                "authorization_status": "user_confirmed",
                "product_relation": "category",
                "evidence_type": "user_comment",
                "time_bucket": "last_24_months",
                "selection_mode": "frozen_matrix",
                "subreddit": "EtsySellers",
                "country": "United States",
                "language": "en",
                "variant": "Grey",
                "variant_scope": "parent_family",
            }) + "\n",
            encoding="utf-8",
        )
        context_normalized = work / "reddit_context_normalized.jsonl"
        run(
            "normalize_records.py",
            "--input", str(context_raw),
            "--output", str(context_normalized),
            "--source", "reddit",
            "--access-mode", "authorized_browser_old_reddit",
        )
        context_record = json.loads(context_normalized.read_text(encoding="utf-8"))
        assert context_record["source_id"] == "reddit:t1_context"
        assert context_record["collected_at"] == "2026-08-18T01:02:03Z"
        assert context_record["query_id"] == "q_context"
        assert context_record["dimension"] == "workflow_platform"
        assert context_record["authorization_status"] == "user_confirmed"
        assert context_record["time_bucket"] == "last_24_months"
        assert context_record["country"] == "United States"
        assert context_record["language"] == "en"
        assert context_record["variant"] == "Grey"
        assert context_record["variant_scope"] == "parent_family"
        assert "author" not in context_record

        included = work / "included.jsonl"
        excluded = work / "excluded.jsonl"
        run(
            "clean_records.py",
            "--input",
            str(normalized),
            "--included",
            str(included),
            "--excluded",
            str(excluded),
            "--summary",
            str(work / "cleaning.json"),
            "--max-per-parent",
            "5",
        )
        records = [json.loads(line) for line in included.read_text(encoding="utf-8").splitlines()]
        excluded_rows = [json.loads(line) for line in excluded.read_text(encoding="utf-8").splitlines()]
        assert len(records) == 60, len(records)
        assert sum(row["exclusion_reason"] == "pure_promotion_candidate" for row in excluded_rows) == 6
        assert all("author" not in row for row in records)
        assert all(row.get("author_hash") for row in records)

        run(
            "make_taxonomy_sample.py",
            "--input",
            str(included),
            "--sample",
            str(work / "taxonomy_sample.jsonl"),
            "--prompt",
            str(work / "taxonomy_prompt.md"),
            "--size",
            "30",
            "--category",
            "UTV cab fans",
        )
        taxonomy_path = work / "taxonomy.json"
        taxonomy_path.write_text(json.dumps(taxonomy()), encoding="utf-8")

        annotations = []
        for record in records:
            negative = "weak airflow" in record["text"]
            annotations.append(
                {
                    "source_id": record["source_id"],
                    "sentiment": "negative" if negative else "positive",
                    "level_3_tags": ["airflow", "fitment"] if negative else ["airflow", "installation"],
                    "ownership_signal": "verified_purchase" if record["verified_purchase"] is True else "owned_use",
                    "funnel_stage": "ownership",
                    "severity": "medium" if negative else "none",
                    "evidence_excerpt": "weak airflow" if negative else "easy installation",
                    "coder": "synthetic-test",
                    "taxonomy_version": "1.0",
                }
            )
        annotations_path = work / "annotations.jsonl"
        annotations_path.write_text("".join(json.dumps(row) + "\n" for row in annotations), encoding="utf-8")

        validation = work / "validation.json"
        run(
            "validate_annotations.py",
            "--records",
            str(included),
            "--annotations",
            str(annotations_path),
            "--taxonomy",
            str(taxonomy_path),
            "--output",
            str(validation),
            "--audit-sample",
            str(work / "audit_sample.jsonl"),
        )
        validation_payload = json.loads(validation.read_text(encoding="utf-8"))
        assert validation_payload["error_count"] == 0
        assert validation_payload["annotation_coverage_pct"] == 100.0

        requirements_path = work / "evidence_requirements.json"
        requirements_path.write_text(json.dumps({
            "evidence_cells": [
                {
                    "id": "owned_fitment",
                    "label": "Owned-use fitment evidence",
                    "search_term": "owner fitment experience",
                    "ownership_signals": ["owned_use"],
                    "tags": ["fitment"],
                    "min_records": 10,
                    "min_parents": 5,
                    "min_sources": 2,
                },
                {
                    "id": "safety_gap",
                    "label": "Safety evidence",
                    "search_term": "battery fire safety",
                    "tags": ["safety"],
                    "min_records": 1,
                    "min_parents": 1,
                    "min_sources": 1,
                },
            ]
        }), encoding="utf-8")
        gap_output = work / "gap_analysis.json"
        run(
            "gap_analysis.py",
            "--records", str(included),
            "--annotations", str(annotations_path),
            "--requirements", str(requirements_path),
            "--output", str(gap_output),
        )
        gap_payload = json.loads(gap_output.read_text(encoding="utf-8"))
        assert gap_payload["failed_cells"] == ["safety_gap"]
        assert gap_payload["gap_terms"] == ["battery fire safety"]
        assert gap_payload["round_2_required"] is True

        stats_dir = work / "statistics"
        run(
            "statistics.py",
            "--records",
            str(included),
            "--annotations",
            str(annotations_path),
            "--taxonomy",
            str(taxonomy_path),
            "--output-dir",
            str(stats_dir),
        )
        audit_result = work / "audit_result.json"
        audit_result.write_text(json.dumps({"reviewed": 50, "fully_correct": 48}), encoding="utf-8")
        gate = work / "quality_gate.json"
        run(
            "quality_gate.py",
            "--records",
            str(included),
            "--annotations",
            str(annotations_path),
            "--validation",
            str(validation),
            "--audit-result",
            str(audit_result),
            "--output",
            str(gate),
        )
        assert json.loads(gate.read_text(encoding="utf-8"))["status"] == "pass"

        # Standalone sample plans must load, and floor/goal/cap have distinct gate semantics.
        small_plan = work / "small_sample_plan.json"
        small_plan.write_text(json.dumps({
            "allocation": [
                {"source": "reddit", "required": True, "record_floor": 20, "record_goal": 20, "record_cap": 40, "min_distinct_parents": 10},
                {"source": "amazon", "required": False, "record_floor": 10, "record_goal": 20, "record_cap": 25, "min_distinct_parents": 10},
                {"source": "tiktok", "required": False, "required_for_completion": True, "record_floor": 10, "record_goal": 20, "record_cap": 20, "min_distinct_parents": 10},
            ]
        }), encoding="utf-8")
        planned_gate = work / "quality_gate_planned.json"
        run(
            "quality_gate.py",
            "--records", str(included),
            "--annotations", str(annotations_path),
            "--validation", str(validation),
            "--audit-result", str(audit_result),
            "--config", str(small_plan),
            "--output", str(planned_gate),
        )
        planned_payload = json.loads(planned_gate.read_text(encoding="utf-8"))
        planned_names = {row["name"] for row in planned_payload["gates"]}
        assert "source_reddit_record_floor" in planned_names
        assert "source_reddit_record_goal" in planned_names
        assert "source_reddit_record_cap" in planned_names

        completion_contract = work / "completion_contract.json"
        completion_contract.write_text(json.dumps({
            "quality_thresholds": {"min_included_records": 50, "min_sources": 2},
            "sample_plan": {
                "allocation": [
                    {
                        "source": "owner_forum",
                        "source_members": ["owner_forum", "shopify_community"],
                        "required": True,
                        "required_for_completion": True,
                        "record_floor": 1,
                        "record_goal": 10,
                        "record_cap": 20,
                        "min_distinct_parents": 1,
                    },
                    {
                        "source": "facebook",
                        "required": False,
                        "required_for_completion": True,
                        "record_floor": 10,
                        "record_goal": 10,
                        "record_cap": 20,
                        "min_distinct_parents": 5,
                    },
                ]
            },
        }), encoding="utf-8")
        completion_round_summary = work / "completion_round_summary.json"
        completion_round_summary.write_text(json.dumps({
            "unknown_attempt_query_ids": [],
            "waiting_for_user_login_sources": [],
            "consecutive_low_yield_expansions": 0,
            "saturation_stop_allowed": False,
        }), encoding="utf-8")
        completion_gate = work / "quality_gate_completion.json"
        run(
            "quality_gate.py",
            "--records", str(included),
            "--annotations", str(annotations_path),
            "--validation", str(validation),
            "--audit-result", str(audit_result),
            "--config", str(completion_contract),
            "--round-summary", str(completion_round_summary),
            "--output", str(completion_gate),
            expected=2,
        )
        completion_payload = json.loads(completion_gate.read_text(encoding="utf-8"))
        assert completion_payload["status"] == "needs_append"
        assert "source_facebook_record_floor" in completion_payload["failed_gate_names"]

        # A coverage shortfall with unsaturated rounds is needs_append, not a final partial.
        unsaturated = work / "round_summary_unsaturated.json"
        unsaturated.write_text(json.dumps({
            "unknown_attempt_query_ids": [],
            "waiting_for_user_login_sources": [],
            "consecutive_low_yield_expansions": 0,
            "saturation_stop_allowed": False,
        }), encoding="utf-8")
        short_contract = work / "short_contract.json"
        short_contract.write_text(json.dumps({
            "quality_thresholds": {"min_included_records": 100, "min_sources": 2},
            "sample_plan": {"allocation": []},
        }), encoding="utf-8")
        needs_append_gate = work / "quality_gate_needs_append.json"
        run(
            "quality_gate.py",
            "--records", str(included),
            "--annotations", str(annotations_path),
            "--validation", str(validation),
            "--audit-result", str(audit_result),
            "--config", str(short_contract),
            "--round-summary", str(unsaturated),
            "--output", str(needs_append_gate),
            expected=2,
        )
        assert json.loads(needs_append_gate.read_text(encoding="utf-8"))["status"] == "needs_append"

        saturated_gate = work / "quality_gate_saturated.json"
        run(
            "quality_gate.py",
            "--records", str(included),
            "--annotations", str(annotations_path),
            "--validation", str(validation),
            "--audit-result", str(audit_result),
            "--config", str(short_contract),
            "--round-summary", str(round_summary),
            "--output", str(saturated_gate),
            expected=2,
        )
        assert json.loads(saturated_gate.read_text(encoding="utf-8"))["status"] == "needs_append"

        # A normal login wall pauses for the user instead of declaring the source exhausted.
        login_source_plan = work / "source_plan_login.json"
        login_source_plan.write_text(json.dumps({
            "sources": [
                {"source": "youtube", "status": "complete"},
                {"source": "amazon", "status": "waiting_for_user_login", "user_action_required": "Sign in directly"},
            ]
        }), encoding="utf-8")
        login_round_summary = work / "round_summary_login.json"
        login_round_summary.write_text(json.dumps({
            "global_rounds": [{"round": "pilot"}, {"round": "round_1"}],
            "waiting_for_user_login_sources": ["amazon"],
            "saturation_stop_allowed": False,
        }), encoding="utf-8")
        workflow_state = work / "workflow_state.json"
        run(
            "collection_state.py",
            "--source-plan", str(login_source_plan),
            "--round-summary", str(login_round_summary),
            "--quality-gate", str(needs_append_gate),
            "--output", str(workflow_state),
        )
        workflow_payload = json.loads(workflow_state.read_text(encoding="utf-8"))
        assert workflow_payload["state"] == "waiting_for_user_login"
        assert workflow_payload["final_report_allowed"] is False
        assert "Do not ask for or handle credentials" in workflow_payload["login_instruction"]

        # A report receipt binds the actual frozen channels and current inputs.
        delivery_contract = work / "delivery_contract.json"
        delivery_plan = work / "delivery_plan.json"
        delivery_rounds = work / "delivery_rounds.json"
        delivery_lock = work / "scope_lock.json"
        delivery_receipt = work / "acceptance.json"
        channels = [{"source":s,"required":True,"required_for_completion":True,"record_floor":1,"min_distinct_parents":1} for s in ("amazon","reddit","tiktok")]
        delivery_contract.write_text(json.dumps({"sample_plan":{"allocation":channels},"quality_thresholds":{"min_included_records":50}}))
        delivery_plan.write_text(json.dumps({"sources":channels}))
        delivery_rounds.write_text(json.dumps({"global_rounds":[{"round":"round_1"}],"saturation_stop_allowed":False}))
        audit_result.write_text(json.dumps({"reviewed":50,"fully_correct":48,"audit_type":"human"}))
        run("freeze_scope.py","--contract",str(delivery_contract),"--source-plan",str(delivery_plan),"--output",str(delivery_lock))
        run("quality_gate.py","--records",str(included),"--annotations",str(annotations_path),"--validation",str(validation),"--audit-result",str(audit_result),"--config",str(delivery_contract),"--round-summary",str(delivery_rounds),"--output",str(gate))
        run("delivery_acceptance.py","--contract",str(delivery_contract),"--source-plan",str(delivery_plan),"--scope-lock",str(delivery_lock),"--records",str(included),"--annotations",str(annotations_path),"--quality-gate",str(gate),"--audit-result",str(audit_result),"--round-summary",str(delivery_rounds),"--statistics",str(stats_dir / "statistics.json"),"--taxonomy",str(taxonomy_path),"--output",str(delivery_receipt))
        report = work / "report.html"
        run(
            "generate_report.py",
            "--acceptance", str(delivery_receipt),
            "--records",
            str(included),
            "--annotations",
            str(annotations_path),
            "--statistics",
            str(stats_dir / "statistics.json"),
            "--quality-gate",
            str(gate),
            "--taxonomy",
            str(taxonomy_path),
            "--title",
            "Synthetic Omnichannel VOC",
            "--output",
            str(report),
        )
        run("validate_report.py", "--report", str(report), "--records", str(included), "--acceptance", str(delivery_receipt))
        html_text = report.read_text(encoding="utf-8")
        assert "Channel denominators remain separate" in html_text
        assert "author_hash" not in html_text
        assert "PASS" in html_text

        # Report validation must accept preserved bridge IDs and multilingual
        # overlap disclosures without truncating or guessing ID formats.
        bridge_report = work / "bridge_report.html"
        bridge_report.write_text(
            """<html><body>
            <section id="decision">decision</section><section id="data-scope">scope</section>
            <section id="themes">多标签主题可重叠</section><section id="signals">signals</section>
            <section id="evidence"><code data-source-id="reddit:t1_context">reddit:t1_context</code></section>
            <section id="quality">quality</section><section id="method">method</section>
            </body></html>""",
            encoding="utf-8",
        )
        run("validate_report.py", "--report", str(bridge_report), "--records", str(context_normalized), "--traceability-only")

        # Missing audit evidence must remain partial.
        partial_gate = work / "quality_gate_partial.json"
        run(
            "quality_gate.py",
            "--records",
            str(included),
            "--annotations",
            str(annotations_path),
            "--validation",
            str(validation),
            "--output",
            str(partial_gate),
            expected=2,
        )
        assert json.loads(partial_gate.read_text(encoding="utf-8"))["status"] == "partial"

        # CSV outputs must neutralize spreadsheet formula prefixes.
        tag_csv = (stats_dir / "tag_frequency.csv").read_text(encoding="utf-8")
        assert "level_3_id" in tag_csv
        subprocess.run([sys.executable,str(ROOT / "tests" / "test_workflow.py")],check=True)
        print("all omnichannel VOC tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
