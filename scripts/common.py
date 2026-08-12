#!/usr/bin/env python3
"""Shared helpers for the omnichannel VOC deterministic pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


REQUIRED_LEVEL_1_IDS = {
    "people_context",
    "functional_value",
    "assurance_value",
    "experience_value",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_for_match(value: Any) -> str:
    text = normalize_space(value).lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return normalize_space(text)


def parse_bool(value: Any) -> bool | str:
    if isinstance(value, bool):
        return value
    if value is None or normalize_space(value) == "":
        return ""
    text = normalize_space(value).lower()
    if text in {"1", "true", "yes", "y", "verified", "verified purchase"}:
        return True
    if text in {"0", "false", "no", "n", "unverified"}:
        return False
    return ""


def parse_float(value: Any) -> float | str:
    if value is None or normalize_space(value) == "":
        return ""
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    if not match:
        return ""
    try:
        return float(match.group(0))
    except ValueError:
        return ""


def parse_int(value: Any) -> int | str:
    parsed = parse_float(value)
    return int(parsed) if parsed != "" else ""


def stable_hash(*parts: Any, length: int = 16) -> str:
    payload = "\x1f".join(normalize_space(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def safe_source_id(source: str, native_id: Any, url: Any, published_at: Any, text: Any) -> str:
    native = normalize_space(native_id)
    digest = stable_hash(source, native or url, published_at, normalize_for_match(text))
    prefix = re.sub(r"[^a-z0-9]+", "_", source.lower()).strip("_") or "source"
    return f"{prefix}_{digest}"


def safe_csv_cell(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    if value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, newline=""
    )
    tmp_name = handle.name
    try:
        with handle:
            handle.write(text)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=True, indent=2) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(value)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    payload = "".join(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n" for row in rows)
    atomic_write_text(path, payload)


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, delete=False, newline=""
    )
    tmp_name = handle.name
    try:
        with handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({key: safe_csv_cell(row.get(key, "")) for key in fieldnames})
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def iter_input_rows(path: Path, fmt: str = "auto") -> Iterator[tuple[int, dict[str, Any]]]:
    resolved = fmt
    if fmt == "auto":
        suffix = path.suffix.lower()
        resolved = {".csv": "csv", ".jsonl": "jsonl", ".ndjson": "jsonl", ".json": "json"}.get(suffix, "jsonl")

    if resolved == "csv":
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for line_number, row in enumerate(csv.DictReader(handle), start=2):
                yield line_number, dict(row)
        return

    if resolved == "jsonl":
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line.strip():
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError(f"{path}:{line_number} is not a JSON object")
                    yield line_number, row
        return

    if resolved == "json":
        payload = read_json(path)
        if isinstance(payload, dict):
            payload = payload.get("data", payload.get("records", [payload]))
        if not isinstance(payload, list):
            raise ValueError("JSON input must be an object or a list of objects")
        for line_number, row in enumerate(payload, start=1):
            if not isinstance(row, dict):
                raise ValueError(f"JSON item {line_number} is not an object")
            yield line_number, row
        return

    raise ValueError(f"Unsupported format: {resolved}")


def flatten_taxonomy(taxonomy: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], set[str]]:
    l3_to_l2: dict[str, str] = {}
    l2_labels: dict[str, str] = {}
    l3_ids: set[str] = set()
    for level_1 in taxonomy.get("level_1", []):
        for level_2 in level_1.get("level_2", []):
            l2_id = normalize_space(level_2.get("id"))
            if l2_id:
                l2_labels[l2_id] = normalize_space(level_2.get("label")) or l2_id
            for level_3 in level_2.get("level_3", []):
                l3_id = normalize_space(level_3.get("id"))
                if l3_id:
                    l3_ids.add(l3_id)
                    l3_to_l2[l3_id] = l2_id
    return l3_to_l2, l2_labels, l3_ids
