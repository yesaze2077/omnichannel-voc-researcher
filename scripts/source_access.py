#!/usr/bin/env python3
"""Record a human access handoff and verified continuation, without handling credentials."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit,parse_qsl

from common import read_json,read_jsonl,write_json,utc_now


def public_url(value):
    u=urlsplit(value)
    forbidden=('token','cookie','password','secret','signature','api_key','session','sig')
    if u.scheme not in {'https','http'} or not u.netloc or u.username or u.password:
        raise ValueError('page URL must be a public HTTP(S) URL without credentials')
    if any(any(term in k.lower() for term in forbidden) for k,_ in parse_qsl(u.query)):
        raise ValueError('do not store credential or session parameters in a handoff URL')
    return value


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-plan',required=True);p.add_argument('--source',required=True)
    p.add_argument('--event',choices=('verification_required','login_required','resume_confirmed','verification_failed','access_denied'),required=True)
    p.add_argument('--event-id',required=True)
    for key in ('page-url','browser-ref','query-id','parent-id','position','last-source-id','evidence-ref','user-action-ref','reason','log'):
        p.add_argument('--'+key,default='')
    a=p.parse_args();path=Path(a.source_plan);plan=read_json(path)
    row=next((r for r in plan.get('sources',[]) if r.get('source')==a.source),None)
    if row is None:p.error('source is absent from the channel plan; do not create or downgrade scope during handoff')
    if row.get('last_access_event_id')==a.event_id:
        print('access event already applied; no duplicate handoff or resume');return 0
    log=Path(a.log) if a.log else path.parent/'manifests'/'access_handoffs.jsonl'
    if log.exists() and any(e.get('event_id')==a.event_id and e.get('source')==a.source for e in read_jsonl(log)):
        print('access event already recorded; no state rewind');return 0
    previous=row.get('status','planned');handoff=dict(row.get('handoff',{}))
    if a.event in {'verification_required','login_required'}:
        try:url=public_url(a.page_url)
        except ValueError as e:p.error(str(e))
        if not a.browser_ref:p.error('handoff needs --browser-ref so the user can take over the visible page')
        handoff.update({'id':a.event_id,'page_url':url,'browser_ref':a.browser_ref,'query_id':a.query_id,
                        'parent_id':a.parent_id,'position':a.position,'last_source_id':a.last_source_id,
                        'requested_at':utc_now(),'status':'waiting','automatic_actions_stopped':True})
        row['status']='waiting_for_user_verification' if a.event=='verification_required' else 'waiting_for_user_login'
        row['user_action_required']='Open the retained browser page, complete verification/sign-in directly, and confirm completion. Do not send credentials. Resume only after content visibility is checked.'
    elif a.event=='resume_confirmed':
        if previous not in {'waiting_for_user_verification','waiting_for_user_login','blocked_checkpoint'} or not handoff:
            p.error('resume requires a retained waiting handoff')
        if not a.evidence_ref or not a.user_action_ref:
            p.error('resume requires --user-action-ref and --evidence-ref for a fresh visible-content check')
        handoff.update({'status':'resolved','resolved_at':utc_now(),'user_action_ref':a.user_action_ref,
                        'content_visible_evidence_ref':a.evidence_ref,'automatic_actions_stopped':False})
        row['status']='collecting';row['user_action_required']=''
        row['resume_from']={k:handoff.get(k,'') for k in ('page_url','query_id','parent_id','position','last_source_id')}
    elif a.event=='verification_failed':
        if previous not in {'waiting_for_user_verification','waiting_for_user_login'} or not handoff:
            p.error('verification_failed requires a waiting handoff')
        if not a.user_action_ref or not a.reason:p.error('record the actual user attempt and failure reason')
        handoff.update({'manual_attempts':int(handoff.get('manual_attempts',0))+1,
                        'last_user_action_ref':a.user_action_ref,'last_failure_reason':a.reason})
        # Keep the channel pending; another source does not replace it.
    else:
        if not a.reason:p.error('access denial needs a concrete reason; a verification prompt alone is not denial')
        row['status']='blocked_access';row['failure_reason']=a.reason
        handoff['automatic_actions_stopped']=True
    row['handoff']=handoff;row['last_access_event_id']=a.event_id
    event={'event_id':a.event_id,'source':a.source,'event':a.event,'previous_status':previous,
           'status':row['status'],'at':utc_now(),'handoff':handoff,'reason':a.reason}
    write_json(path,plan)
    log=Path(a.log) if a.log else path.parent/'manifests'/'access_handoffs.jsonl'
    log.parent.mkdir(exist_ok=True,parents=True)
    with log.open('a',encoding='utf-8') as h:h.write(json.dumps(event,ensure_ascii=False)+'\n')
    print(f"source={a.source} state={row['status']} resume_checkpoint_preserved={bool(handoff)}")
    return 0

if __name__=='__main__':raise SystemExit(main())
