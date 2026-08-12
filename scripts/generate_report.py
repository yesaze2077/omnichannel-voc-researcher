#!/usr/bin/env python3
"""Generate a source-traceable, denominator-aware HTML VOC report."""

from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Any

from common import normalize_space, read_json, read_jsonl, atomic_write_text


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def table(headers: list[str], rows: list[list[Any]], empty: str = "No evidence available.") -> str:
    if not rows:
        return f'<p class="muted">{esc(empty)}</p>'
    head = "".join(f"<th>{esc(header)}</th>" for header in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def list_items(values: list[Any], empty: str) -> str:
    if not values:
        return f'<p class="muted">{esc(empty)}</p>'
    return "<ul>" + "".join(f"<li>{esc(value)}</li>" for value in values) + "</ul>"


def source_sentiment_rows(statistics: dict[str, Any]) -> list[list[Any]]:
    counts: dict[str, dict[str, int]] = {}
    for row in statistics.get("source_sentiment", []):
        source = row.get("source", "unknown")
        counts.setdefault(source, {})[row.get("sentiment", "unlabeled")] = row.get("count", 0)
    return [
        [
            source,
            statistics.get("source_counts", {}).get(source, 0),
            values.get("positive", 0),
            values.get("negative", 0),
            values.get("mixed", 0),
            values.get("neutral", 0),
        ]
        for source, values in sorted(counts.items())
    ]


def top_tag_rows(statistics: dict[str, Any], sentiment: str, limit: int = 12) -> list[list[Any]]:
    rows = sorted(
        statistics.get("tag_frequency", []),
        key=lambda row: (int(row.get(sentiment, 0)), int(row.get("record_count", 0))),
        reverse=True,
    )
    return [
        [
            row.get("level_3_label", row.get("level_3_id", "")),
            row.get(sentiment, 0),
            row.get("record_count", 0),
            f'{row.get("pct_of_labeled_records", 0)}%',
        ]
        for row in rows[:limit]
        if int(row.get(sentiment, 0)) > 0
    ]


def evidence_html(statistics: dict[str, Any], limit: int = 40) -> str:
    rows: list[str] = []
    for item in statistics.get("evidence_candidates", [])[:limit]:
        url = normalize_space(item.get("source_url"))
        source_id = normalize_space(item.get("source_id"))
        source_link = f'<a href="{esc(url)}" target="_blank" rel="noreferrer">Open source</a>' if url else "No URL"
        tags = ", ".join(item.get("tags", []))
        rows.append(
            "<tr>"
            f'<td><code>{esc(source_id)}</code></td>'
            f'<td>{esc(item.get("source"))}</td>'
            f'<td>{esc(item.get("sentiment"))}</td>'
            f'<td>{esc(item.get("severity"))}</td>'
            f'<td>{esc(tags)}</td>'
            f'<td class="quote">{esc(item.get("evidence_excerpt"))}</td>'
            f'<td>{source_link}</td>'
            "</tr>"
        )
    if not rows:
        return '<p class="muted">No evidence candidates available.</p>'
    return (
        '<div class="table-wrap"><table><thead><tr>'
        "<th>Source ID</th><th>Source</th><th>Sentiment</th><th>Severity</th><th>Tags</th><th>Evidence</th><th>URL</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--statistics", required=True)
    parser.add_argument("--quality-gate", required=True)
    parser.add_argument("--taxonomy", required=True)
    parser.add_argument("--findings", default="")
    parser.add_argument("--title", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    records = read_jsonl(Path(args.records))
    annotations = read_jsonl(Path(args.annotations))
    statistics = read_json(Path(args.statistics))
    quality = read_json(Path(args.quality_gate))
    taxonomy = read_json(Path(args.taxonomy))
    findings = read_json(Path(args.findings)) if args.findings and Path(args.findings).exists() else {}
    denominators = statistics.get("denominators", {})
    status = quality.get("status", "partial")
    decision = findings.get(
        "decision",
        "Deterministic evidence package generated. Decision interpretation requires analyst review.",
    )
    confidence = findings.get("confidence", status)
    recommendations = findings.get("recommendations", [])
    veto_conditions = findings.get("veto_conditions", [])
    anomalies = findings.get("anomalies", [])
    behavioral_segments = findings.get("behavioral_segments", [])

    gate_rows = [
        [item.get("name"), item.get("actual"), item.get("operator"), item.get("threshold"), "PASS" if item.get("passed") else "MISS"]
        for item in quality.get("gates", [])
    ]
    source_rows = [[source, count] for source, count in sorted(statistics.get("source_counts", {}).items())]
    low_rating_rows = [
        [row.get("level_3_label", row.get("level_3_id")), row.get("low_rating_record_count", 0)]
        for row in statistics.get("low_rating_tags", [])[:12]
    ]
    ownership_rows = [[key, value] for key, value in sorted(statistics.get("ownership_counts", {}).items())]
    funnel_rows = [[key, value] for key, value in sorted(statistics.get("funnel_counts", {}).items())]

    css = """
    :root { color-scheme: light; --ink:#172027; --muted:#64727d; --line:#d9dfe3; --paper:#ffffff; --band:#f3f5f6; --accent:#006a63; --warn:#a14800; --bad:#a12d2d; }
    * { box-sizing: border-box; }
    body { margin:0; background:var(--paper); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.55; }
    header { border-bottom:1px solid var(--line); padding:40px 5vw 30px; }
    main { max-width:1180px; margin:0 auto; padding:0 28px 72px; }
    section { padding:34px 0; border-bottom:1px solid var(--line); }
    h1 { margin:0 0 8px; font-size:36px; letter-spacing:0; }
    h2 { margin:0 0 18px; font-size:24px; letter-spacing:0; }
    h3 { margin:24px 0 10px; font-size:17px; letter-spacing:0; }
    p { max-width:900px; }
    .eyebrow { color:var(--accent); font-weight:700; text-transform:uppercase; font-size:12px; }
    .status { display:inline-block; border:1px solid var(--line); padding:4px 9px; font-weight:700; font-size:12px; border-radius:4px; }
    .status-pass { color:var(--accent); } .status-partial { color:var(--warn); } .status-blocked { color:var(--bad); }
    .metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:1px; background:var(--line); border:1px solid var(--line); margin:24px 0; }
    .metric { background:var(--paper); padding:18px; min-height:104px; }
    .metric strong { display:block; font-size:27px; }
    .metric span { color:var(--muted); font-size:13px; }
    .decision { border-left:4px solid var(--accent); padding:14px 18px; background:var(--band); max-width:920px; }
    .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:28px; }
    .table-wrap { overflow:auto; border:1px solid var(--line); }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th,td { padding:10px 12px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
    th { background:var(--band); position:sticky; top:0; }
    tr:last-child td { border-bottom:0; }
    code { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12px; }
    a { color:var(--accent); } .muted { color:var(--muted); } .quote { max-width:420px; }
    footer { color:var(--muted); padding-top:24px; font-size:12px; }
    @media (max-width:760px) { h1{font-size:29px}.metrics,.grid{grid-template-columns:1fr 1fr}main{padding:0 18px 48px} }
    @media (max-width:480px) { .metrics,.grid{grid-template-columns:1fr} }
    """

    report = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(args.title)}</title><style>{css}</style></head><body>
<header><div class="eyebrow">Omnichannel Voice of Customer</div><h1>{esc(args.title)}</h1>
<p class="muted">Source-traceable evidence report. Channel denominators remain separate.</p>
<span class="status status-{esc(status)}">{esc(status.upper())}</span></header>
<main>
<section id="decision"><h2>Decision and confidence</h2><div class="decision"><strong>{esc(decision)}</strong><p>Confidence: {esc(confidence)}</p></div>
<div class="metrics">
<div class="metric"><strong>{esc(denominators.get("included_records", len(records)))}</strong><span>Included records</span></div>
<div class="metric"><strong>{esc(denominators.get("labeled_records", len(annotations)))}</strong><span>Labeled records</span></div>
<div class="metric"><strong>{esc(len(statistics.get("source_counts", {})))}</strong><span>Distinct sources</span></div>
<div class="metric"><strong>{esc(denominators.get("verified_purchase_records", 0))}</strong><span>Verified-purchase records</span></div>
</div>
<div class="grid"><div><h3>Recommended actions</h3>{list_items(recommendations, "Analyst recommendations have not been supplied.")}</div>
<div><h3>Veto conditions</h3>{list_items(veto_conditions, "No analyst-defined veto conditions supplied.")}</div></div></section>

<section id="data-scope"><h2>Data scope and denominator ledger</h2>
<div class="grid"><div><h3>Source mix</h3>{table(["Source","Included records"], source_rows)}</div>
<div><h3>Sentiment by source</h3>{table(["Source","Retained","Positive","Negative","Mixed","Neutral"], source_sentiment_rows(statistics))}</div></div>
<p class="muted">Theme labels may overlap. Search rank and collected record counts are not platform population estimates.</p></section>

<section id="themes"><h2>Positive themes and pain points</h2><div class="grid">
<div><h3>Positive theme mentions</h3>{table(["Theme","Positive","All mentions","% labeled records"], top_tag_rows(statistics,"positive"))}</div>
<div><h3>Negative theme mentions</h3>{table(["Theme","Negative","All mentions","% labeled records"], top_tag_rows(statistics,"negative"))}</div></div>
<h3>Low-rating theme mentions</h3>{table(["Theme","Records rated 1-2"], low_rating_rows)}</section>

<section id="signals"><h2>Anomaly and behavioral signals</h2><div class="grid"><div><h3>Analyst anomaly notes</h3>{list_items(anomalies, "No analyst anomaly notes supplied.")}
<h3>Severity counts</h3>{table(["Severity","Labeled records"], [[k,v] for k,v in sorted(statistics.get("severity_counts", {}).items())])}</div>
<div><h3>Ownership signals</h3>{table(["Signal","Records"], ownership_rows)}<h3>Funnel stages</h3>{table(["Stage","Records"], funnel_rows)}
<h3>Behavioral segments</h3>{list_items(behavioral_segments, "Segments require analyst interpretation; no personas were fabricated.")}</div></div></section>

<section id="evidence"><h2>Evidence chain</h2><p>Short excerpts remain tied to stable source IDs and source URLs.</p>{evidence_html(statistics)}</section>

<section id="quality"><h2>Quality gate</h2>{table(["Gate","Actual","Rule","Threshold","Result"], gate_rows)}
{list_items(quality.get("policy_warnings", []), "No automated policy warnings were generated.")}</section>

<section id="method"><h2>Method and limitations</h2>
<p>Taxonomy version: <code>{esc(taxonomy.get("version","unknown"))}</code>. The pipeline separated collection, cleaning, annotation, deterministic statistics, and interpretation.</p>
{list_items(statistics.get("notes", []), "No statistical notes supplied.")}
{list_items(quality.get("notes", []), "No quality notes supplied.")}
<p class="muted">A quality-gate pass confirms this evidence package met its declared structural checks. It does not prove representativeness, causality, market share, or population-wide sentiment.</p></section>
<footer>Generated by omnichannel-voc-researcher. Raw author identifiers are intentionally omitted.</footer>
</main></body></html>"""

    atomic_write_text(Path(args.output), report)
    print(Path(args.output).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
