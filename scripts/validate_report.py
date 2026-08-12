#!/usr/bin/env python3
"""Validate required HTML report sections and evidence traceability."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import normalize_space, read_jsonl


REQUIRED_SECTIONS = {"decision", "data-scope", "themes", "signals", "evidence", "quality", "method"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--records", required=True)
    args = parser.parse_args()

    report_path = Path(args.report)
    text = report_path.read_text(encoding="utf-8")
    records = read_jsonl(Path(args.records))
    errors: list[str] = []
    for section in sorted(REQUIRED_SECTIONS):
        if f'id="{section}"' not in text:
            errors.append(f"missing section: {section}")
    if re.search(r"\b(TODO|TBD|PLACEHOLDER)\b", text, re.IGNORECASE):
        errors.append("report contains a placeholder token")
    if "author_hash" in text:
        errors.append("report exposes author_hash")
    known_ids = {normalize_space(row.get("source_id")) for row in records}
    rendered_ids = {match for match in re.findall(r"[a-z0-9_]+_[0-9a-f]{16}", text)}
    unknown = rendered_ids - known_ids
    if unknown:
        errors.append(f"report contains unknown source ids: {sorted(unknown)[:5]}")
    if records and not (rendered_ids & known_ids):
        errors.append("report contains no traceable source id")
    if "Theme labels may overlap" not in text and "Theme percentages" not in text:
        errors.append("report does not disclose overlapping theme denominators")

    if errors:
        print("\n".join(errors))
        return 2
    print(f"valid report: {report_path} ({len(records)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
