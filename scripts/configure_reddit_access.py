#!/usr/bin/env python3
"""Apply a Reddit entrypoint and authorization label to an existing search matrix."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from build_search_matrix import REDDIT_ENTRYPOINTS, reddit_access_fields
from common import read_jsonl, utc_now, write_json, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--output", default="", help="Defaults to updating --matrix in place.")
    parser.add_argument("--summary", default="")
    parser.add_argument("--entrypoint", choices=tuple(REDDIT_ENTRYPOINTS), default="old")
    parser.add_argument(
        "--authorization-status",
        choices=("unconfirmed", "user_confirmed", "documented"),
        default="unconfirmed",
    )
    args = parser.parse_args()

    matrix_path = Path(args.matrix)
    rows = read_jsonl(matrix_path)
    if not rows:
        raise SystemExit("matrix is empty")
    access_fields = reddit_access_fields(args.entrypoint, args.authorization_status)
    updated = 0
    for row in rows:
        if row.get("source") == "reddit":
            row.update(access_fields)
            updated += 1
    if updated == 0:
        raise SystemExit("matrix contains no Reddit rows")

    output_path = Path(args.output) if args.output else matrix_path
    write_jsonl(output_path, rows)
    summary = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "matrix_rows": len(rows),
        "updated_reddit_rows": updated,
        "source_counts": dict(sorted(Counter(str(row.get("source", "")) for row in rows).items())),
        "preferred_entrypoint": access_fields["preferred_entrypoint"],
        "fallback_entrypoint": access_fields["fallback_entrypoint"],
        "access_mode": access_fields["access_mode"],
        "authorization_status": args.authorization_status,
        "rule": "Authorization credentials and account identifiers are not stored in the matrix.",
    }
    summary_path = Path(args.summary) if args.summary else output_path.with_suffix(".reddit_access.json")
    write_json(summary_path, summary)
    print(f"updated_reddit_rows={updated} output={output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
