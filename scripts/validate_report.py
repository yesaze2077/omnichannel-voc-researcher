#!/usr/bin/env python3
"""Validate required HTML report sections and evidence traceability."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from common import normalize_space, read_jsonl


from workflow_contract import load_acceptance, delivery_marker


REQUIRED_SECTIONS = {"decision", "data-scope", "themes", "signals", "evidence", "quality", "method"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    parser.add_argument("--records", required=True)
    parser.add_argument("--acceptance", default="")
    parser.add_argument("--artifact-kind", choices=("final","snapshot"), default="final")
    parser.add_argument("--traceability-only", action="store_true", help="Read-only structural check; does not authorize delivery.")
    args = parser.parse_args()

    report_path = Path(args.report)
    text = report_path.read_text(encoding="utf-8")
    records = read_jsonl(Path(args.records))
    errors: list[str] = []
    if not args.traceability_only:
        if not args.acceptance:
            parser.error('delivery validation requires --acceptance; traceability-only checks never authorize delivery')
        try:
            receipt=load_acceptance(Path(args.acceptance),args.artifact_kind,{'records':Path(args.records)})
            match=re.search(r'<script[^>]*id=["\']delivery-acceptance["\'][^>]*>(.*?)</script>',text,re.S)
            if not match or json.loads(match.group(1))!=delivery_marker(receipt,args.artifact_kind):
                errors.append('missing or inconsistent delivery-acceptance marker')
            if args.artifact_kind=='snapshot':
                if not re.search(r'<title>[^<]*PROGRESS SNAPSHOT',text) or not re.search(r'<h1>[^<]*PROGRESS SNAPSHOT',text):
                    errors.append('snapshot title and H1 need PROGRESS SNAPSHOT labels')
                for value in [receipt['state'],receipt['next_action'],*receipt['required_shortfalls']]:
                    if html.escape(value) not in text:errors.append('snapshot omits visible status, shortfall or next action: '+value)
                if 'data-delivery-state' not in text:errors.append('snapshot lacks visible delivery state')
        except (ValueError,OSError,KeyError) as exc:errors.append(str(exc))
    for section in sorted(REQUIRED_SECTIONS):
        if f'id="{section}"' not in text:
            errors.append(f"missing section: {section}")
    if re.search(r"\b(TODO|TBD|PLACEHOLDER)\b", text, re.IGNORECASE):
        errors.append("report contains a placeholder token")
    if "author_hash" in text:
        errors.append("report exposes author_hash")
    known_ids = {normalize_space(row.get("source_id")) for row in records}
    # Extract explicit evidence identifiers instead of guessing their shape.
    # Bridges may preserve native IDs such as ``reddit:t1_context`` or use
    # hashes longer than 16 characters, so prefix/length regexes are unsafe.
    rendered_ids = {
        normalize_space(html.unescape(match))
        for match in re.findall(r"data-source-id=[\"']([^\"']+)[\"']", text)
        if normalize_space(html.unescape(match))
    }
    unknown = rendered_ids - known_ids
    if unknown:
        errors.append(f"report contains unknown source ids: {sorted(unknown)[:5]}")
    if records and not (rendered_ids & known_ids):
        errors.append("report contains no traceable source id")
    if not any(marker in text for marker in ("Theme labels may overlap", "Theme percentages", "multi-label", "多标签")):
        errors.append("report does not disclose overlapping theme denominators")

    if errors:
        print("\n".join(errors))
        return 2
    print(f"{'traceability only; delivery not accepted' if args.traceability_only else 'delivery validated'}: {report_path} ({len(records)} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
