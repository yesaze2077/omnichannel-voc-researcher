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
        for source in ("x", "tiktok"):
            assert allocations[source]["target_included_records"] >= 30
            assert allocations[source]["min_distinct_parents"] >= 10

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

        report = work / "report.html"
        run(
            "generate_report.py",
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
        run("validate_report.py", "--report", str(report), "--records", str(included))
        html_text = report.read_text(encoding="utf-8")
        assert "Channel denominators remain separate" in html_text
        assert "author_hash" not in html_text
        assert "PASS" in html_text

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
        print("all omnichannel VOC tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
