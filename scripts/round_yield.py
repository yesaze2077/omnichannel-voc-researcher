#!/usr/bin/env python3
"""Measure known successful query yields; failed/unknown rounds never establish saturation."""
from __future__ import annotations
import argparse
import math
from collections import Counter,defaultdict
from pathlib import Path
from common import normalize_space,read_jsonl,write_json,utc_now

ROUND_ORDER={'pilot':0,'round_1':1,'round_2':2,'round_3':3,'supplement':4}
SUCCESS={'complete','collected','success','empty_confirmed','bounded_sample_collected'}

def number(row,key):
    value=row.get(key)
    if value is None or isinstance(value,bool):return None
    try:
        parsed=float(value)
        return int(parsed) if math.isfinite(parsed) and parsed>=0 and parsed.is_integer() else None
    except (TypeError,ValueError):return None

def total(rows,key):
    values=[number(r,key) for r in rows]
    return sum(values) if values and all(x is not None for x in values) else None

def order(values):return sorted(values,key=lambda x:(ROUND_ORDER.get(x,100),x))

def summarize(rows,previous,expansion,planned,threshold):
    ids={r.get('query_id') for r in rows}
    # A repeated query ID is a retry/page update, not new evidence; the caller retains latest attempts.
    known=total(rows,'new_relevant_records')
    complete=bool(rows) and all(r.get('status') in SUCCESS for r in rows) and known is not None and set(planned).issubset(ids)
    pct=round(known/previous*100,2) if complete and previous else (100.0 if complete and known else None)
    low=bool(expansion and complete and ((pct is not None and pct<threshold) or known==0))
    return {'is_expansion':expansion,'queries_attempted':len(ids),'new_relevant_records':known,
            'previous_cumulative_relevant':previous,'incremental_new_relevant_pct':pct,
            'round_execution_complete':complete,'low_yield':low,
            'zero_yield_expansion':bool(expansion and complete and known==0),
            'unknown_yield_attempts':sum(number(r,'new_relevant_records') is None for r in rows),
            'status_counts':dict(Counter(r.get('status','unknown') for r in rows)),
            **{k:total(rows,k) for k in ('discovered_parents','new_parents','raw_records','relevant_records','retained_records','duplicate_records')}}

def consecutive(rows):
    count=0
    for row in reversed(rows):
        if not row['is_expansion']:continue
        if not row['low_yield']:break
        count+=1
    return count

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--matrix',required=True);p.add_argument('--attempts',required=True)
    p.add_argument('--low-yield-threshold-pct',type=float,default=5.0);p.add_argument('--output',required=True)
    a=p.parse_args();matrix=read_jsonl(Path(a.matrix));attempts=read_jsonl(Path(a.attempts))
    by_id={r['query_id']:r for r in matrix}
    latest={};unknown=[];mismatches=[]
    for r in attempts:
        q=r.get('query_id')
        if q not in by_id:unknown.append(q);continue
        if r.get('source')!=by_id[q].get('source') or r.get('round')!=by_id[q].get('round'):
            mismatches.append(q);continue
        latest[q]=r
    groups=defaultdict(list)
    for r in latest.values():groups[(r['source'],r['round'])].append(r)
    planned=defaultdict(list)
    for r in matrix:planned[(r['source'],r['round'])].append(r['query_id'])
    source_execution={}
    for source in {r['source'] for r in matrix}:
        needed=[r for r in matrix if r['source']==source and r.get('required_for_completion',True)]
        unfinished=[r['query_id'] for r in needed if r['query_id'] not in latest or latest[r['query_id']].get('status') not in SUCCESS or number(latest[r['query_id']],'new_relevant_records') is None]
        source_execution[source]={'required_queries':len(needed),'required_unfinished_queries':len(unfinished),'unfinished_query_ids':unfinished}
    sources=sorted({r['source'] for r in matrix});round_ids=order({r['round'] for r in matrix})
    source_rows=[];saturation={}
    for source in sources:
        cumulative=0;sr=[]
        for rid in order({r['round'] for r in matrix if r['source']==source}):
            rows=groups[(source,rid)]
            expansion=rid not in {'pilot','round_1'} or any(r.get('is_expansion') for r in rows)
            s=summarize(rows,cumulative,expansion,planned[(source,rid)],a.low_yield_threshold_pct)
            s.update(source=source,round=rid);sr.append(s)
            if s['round_execution_complete']:cumulative+=s['new_relevant_records']
        source_rows+=sr
        n=consecutive(sr)
        saturation[source]={'consecutive_low_yield_expansions':n,'saturation_stop_allowed':n>=2 and not unknown and not mismatches}
    global_rows=[];cumulative=0
    for rid in round_ids:
        rows=[r for r in latest.values() if r['round']==rid]
        qs=[r['query_id'] for r in matrix if r['round']==rid]
        s=summarize(rows,cumulative,rid not in {'pilot','round_1'} or any(r.get('is_expansion') for r in rows),qs,a.low_yield_threshold_pct)
        s['round']=rid;global_rows.append(s)
        if s['round_execution_complete']:cumulative+=s['new_relevant_records']
    waits=sorted({r['source'] for r in latest.values() if r.get('status') in {'waiting_for_user_login','waiting_for_user_verification','blocked_checkpoint'}})
    blocked=sorted({r['source'] for r in latest.values() if r.get('status','').startswith('blocked') or r.get('status') in {'rate_limited','access_denied'}})
    unattempted=[r for r in matrix if r['query_id'] not in latest]
    result={'schema_version':'3.0','generated_at':utc_now(),'matrix_queries':len(by_id),'attempted_queries':len(latest),
            'unattempted_queries':len(unattempted),'unknown_attempt_query_ids':sorted(set(unknown)),
            'mismatched_attempt_query_ids':sorted(set(mismatches)), 'source_rounds':source_rows,'global_rounds':global_rows,
            'source_saturation':saturation,'source_execution':source_execution,'consecutive_low_yield_expansions':consecutive(global_rows),
            'saturation_stop_allowed':bool(sources) and all(v['saturation_stop_allowed'] for v in saturation.values()),
            'waiting_for_user_login_sources':sorted({r['source'] for r in latest.values() if r.get('status')=='waiting_for_user_login'}),
            'waiting_for_user_verification_sources':sorted({r['source'] for r in latest.values() if r.get('status') in {'waiting_for_user_verification','blocked_checkpoint'}}),
            'blocked_sources':blocked,'coverage_gaps':{'sources':dict(Counter(r['source'] for r in unattempted))},
            'recommendation':'Continue runnable required channels; request retained-page human handoffs separately. Missing/failed counts are unknown, not zero.'}
    write_json(Path(a.output),result)
    print(f"attempted={len(latest)} unattempted={len(unattempted)} saturation={result['saturation_stop_allowed']}")
    return 0

if __name__=='__main__':raise SystemExit(main())
