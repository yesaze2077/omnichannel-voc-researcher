#!/usr/bin/env python3
"""Schedule runnable channels before waiting; only acceptance can authorize delivery."""
from __future__ import annotations
import argparse
from pathlib import Path
from common import read_json,utc_now,write_json
from workflow_contract import WAITING,BLOCKED,load_acceptance,required


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--acceptance',default='')
    p.add_argument('--source-plan',default='')
    p.add_argument('--round-summary',default='')
    p.add_argument('--quality-gate',default='')
    p.add_argument('--preliminary-analysis-complete',action='store_true')
    p.add_argument('--human-audit-complete',action='store_true',help='Legacy planning hint; never substitutes for audit evidence.')
    p.add_argument('--output',required=True)
    a=p.parse_args()
    if a.acceptance:
        try:r=load_acceptance(Path(a.acceptance),'snapshot')
        except (ValueError,OSError,KeyError) as e:p.error(str(e))
        result={k:r[k] for k in ('state','next_action','task_complete','final_report_allowed','actionable_sources','waiting_sources','required_shortfalls')}
        result['acceptance_sha256']=r['acceptance_sha256']
    elif a.source_plan:
        # Legacy planning remains usable, but cannot produce final-report permission.
        rows=read_json(Path(a.source_plan)).get('sources',[])
        needed=[r for r in rows if required(r) and r.get('status') not in {'complete','collected_complete'}]
        waiting=[r.get('source') for r in needed if r.get('status') in WAITING]
        runnable=[r.get('source') for r in needed if r.get('status') not in WAITING|BLOCKED]
        if runnable:state,action='needs_append','continue_collection'
        elif waiting:
            state='waiting_for_user_verification' if any(r.get('status')!='waiting_for_user_login' for r in needed if r.get('status') in WAITING) else 'waiting_for_user_login'
            action='request_human_handoff_then_resume'
        else:state,action='acceptance_required','run_delivery_acceptance'
        result={'state':state,'next_action':action,'actionable_sources':runnable,'waiting_sources':waiting,
                'task_complete':False,'final_report_allowed':False,'acceptance_required':True}
    else:p.error('provide --acceptance, or --source-plan for non-final legacy planning')
    result['updated_at']=utc_now()
    result['login_instruction']='Ask the user to complete sign-in or verification directly in the retained browser. Do not ask for or handle credentials. Recheck visible content, then resume the checkpoint; continue other runnable channels meanwhile.' if result.get('waiting_sources') else ''
    write_json(Path(a.output),result)
    print(f"state={result['state']} next={result['next_action']}")
    return 0

if __name__=='__main__':raise SystemExit(main())
