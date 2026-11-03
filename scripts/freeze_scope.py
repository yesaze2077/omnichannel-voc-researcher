#!/usr/bin/env python3
"""Freeze the channel contract; changes require pre-collection evidence or a user reference."""
from pathlib import Path
import argparse
import json
from common import read_json,write_json,utc_now
from workflow_contract import make_lock,check_scope

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--contract',required=True);p.add_argument('--source-plan',default='')
    p.add_argument('--output',required=True);p.add_argument('--approval-ref',default='')
    p.add_argument('--before-collection',action='store_true')
    a=p.parse_args();out=Path(a.output);contract=read_json(Path(a.contract))
    if out.exists():
        if a.before_collection:
            root=Path(a.contract).resolve().parent
            if any(f.stat().st_size for folder in ('raw','normalized','analysis') for f in (root/folder).rglob('*') if f.is_file()):
                p.error('collection records already exist; a user:<reference> approval is required')
        elif not a.approval_ref.startswith('user:') or len(a.approval_ref)<=5:
            p.error('existing frozen scope requires --approval-ref user:<actual-user-decision-reference>')
    lock=make_lock(contract,a.approval_ref or 'initial_or_precollection_planning')
    if a.source_plan:
        errors=check_scope(contract,lock,read_json(Path(a.source_plan)))
        if errors:p.error('; '.join(errors))
    if out.exists():
        history=out.parent/'manifests'/'scope_history.jsonl';history.parent.mkdir(exist_ok=True,parents=True)
        with history.open('a') as h:h.write(json.dumps({'replaced_at':utc_now(),'previous_lock':read_json(out),'approval_ref':lock['approval_ref']})+'\n')
    write_json(out,lock);print(f'frozen scope={lock["scope_sha256"]}')
    return 0

if __name__=='__main__':raise SystemExit(main())
