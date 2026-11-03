#!/usr/bin/env python3
"""Validate task/channel completion separately from exporting a progress snapshot."""
from pathlib import Path
import argparse
from common import read_json, read_jsonl, write_json
from workflow_contract import acceptance, add_input_provenance

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('contract','scope-lock','source-plan','records','annotations','quality-gate','audit-result','round-summary'):
        p.add_argument('--'+key,required=True)
    p.add_argument('--statistics',default='');p.add_argument('--taxonomy',default='')
    p.add_argument('--output',required=True)
    a=p.parse_args()
    paths={k:Path(getattr(a,k)) for k in ('contract','scope_lock','source_plan','records','annotations','quality_gate','audit_result','round_summary')}
    values={k:read_jsonl(v) if k in {'records','annotations'} else read_json(v) for k,v in paths.items()}
    result=acceptance(values['contract'],values['scope_lock'],values['source_plan'],values['records'],values['annotations'],values['quality_gate'],values['audit_result'],values['round_summary'])
    for k in ('statistics','taxonomy'):
        if getattr(a,k):paths[k]=Path(getattr(a,k))
    write_json(Path(a.output),add_input_provenance(result,paths,Path(a.output)))
    print(f"state={result['state']} task_complete={result['task_complete']} final_report_allowed={result['final_report_allowed']}")
    return 0 if result['task_complete'] else 2

if __name__=='__main__':raise SystemExit(main())
