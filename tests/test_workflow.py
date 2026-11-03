#!/usr/bin/env python3
"""Behavioral regressions with synthetic records only; no live network or credentials."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from workflow_contract import acceptance,make_lock,digest,check_scope,valid_voc


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='voc-workflow-');self.addCleanup(self.temp.cleanup)
        self.w=Path(self.temp.name)
        channels=[{'source':s,'role':'core','required_for_completion':True,'record_floor':1,'min_distinct_parents':1} for s in ('youtube','reddit')]
        self.contract={'sample_plan':{'allocation':channels},'quality_thresholds':{'min_included_records':2,'min_sources':2,'max_parent_share_pct':100}}
        self.lock=make_lock(self.contract);self.plan={'sources':copy.deepcopy(channels)}
        self.records=[{'source_id':s+'_1','source':s,'parent_id':s+'_p','record_type':'comment','text':'Synthetic installed fan experience','source_url':'https://example.invalid/'+s,'collection_status':'included'} for s in ('youtube','reddit')]
        self.anns=[{'source_id':r['source_id'],'evidence_excerpt':'Synthetic installed fan experience','level_3_tags':['airflow'],'sentiment':'positive','ownership_signal':'claimed_use','funnel_stage':'ownership','severity':'none'} for r in self.records]
        self.audit={'reviewed':2,'fully_correct':2,'audit_type':'human'}
        self.rounds={'global_rounds':[{'round':'round_1'}],'unknown_attempt_query_ids':[],'saturation_stop_allowed':False}
        self.refresh_quality()

    def put(self,name,obj,jsonl=False):
        p=self.w/name
        p.write_text(''.join(json.dumps(r)+'\n' for r in obj) if jsonl else json.dumps(obj));return p

    def run_cli(self,name,*args,code=0):
        r=subprocess.run([sys.executable,str(ROOT/'scripts'/name),*map(str,args)],capture_output=True,text=True)
        self.assertEqual(r.returncode,code,r.stdout+r.stderr);return r

    def refresh_quality(self,failed=()):
        names=['included_records','annotation_validation_errors','audit_records_reviewed']
        self.q={'status':'pass' if not failed else 'needs_append','gates':[{'name':n,'passed':n not in failed,'critical':True} for n in set(names)|set(failed)],
                'input_digests':{k:digest(v) for k,v in {'records':self.records,'annotations':self.anns,'contract':self.contract,'audit_result':self.audit,'round_summary':self.rounds}.items()}}

    def accept(self):return acceptance(self.contract,self.lock,self.plan,self.records,self.anns,self.q,self.audit,self.rounds)

    def test_complete_requires_current_scope_and_audit(self):
        r=self.accept();self.assertTrue(r['task_complete']);self.assertTrue(r['final_report_allowed'])

    def test_large_other_source_does_not_replace_youtube(self):
        self.records=self.records[1:]*100;self.refresh_quality()
        r=self.accept();self.assertIn('youtube',r['required_shortfalls']);self.assertFalse(r['task_complete'])

    def test_optional_login_does_not_stop_runnable_required_channel(self):
        self.contract['sample_plan']['allocation'].append({'source':'x','required_for_completion':False,'record_floor':0,'min_distinct_parents':0})
        self.lock=make_lock(self.contract);self.plan['sources']=copy.deepcopy(self.contract['sample_plan']['allocation'])
        self.plan['sources'][-1]['status']='waiting_for_user_login'
        self.records=self.records[1:];self.anns=self.anns[1:];self.refresh_quality()
        r=self.accept();self.assertEqual(r['state'],'needs_append');self.assertIn('youtube',r['actionable_sources'])

    def test_required_verification_does_not_stop_other_required_work(self):
        self.records=[];self.anns=[];self.plan['sources'][1]['status']='waiting_for_user_verification';self.refresh_quality()
        r=self.accept();self.assertEqual(r['state'],'needs_append');self.assertIn('reddit',r['waiting_sources'])

    def test_wait_only_when_remaining_required_work_needs_human(self):
        self.records=self.records[:1];self.anns=self.anns[:1];self.plan['sources'][1]['status']='waiting_for_user_verification';self.refresh_quality()
        self.assertEqual(self.accept()['state'],'waiting_for_user_verification')

    def test_required_handoff_blocks_final_even_after_quantity_floors(self):
        self.plan['sources'][1]['status']='waiting_for_user_verification';self.refresh_quality()
        r=self.accept();self.assertFalse(r['task_complete']);self.assertFalse(r['final_report_allowed']);self.assertEqual(r['state'],'waiting_for_user_verification')

    def test_round_wait_cannot_be_hidden_by_completed_source_plan(self):
        self.rounds['waiting_for_user_verification_sources']=['reddit'];self.refresh_quality()
        self.assertFalse(self.accept()['task_complete'])

    def test_unfinished_required_query_blocks_final_after_floors(self):
        self.rounds['source_execution']={'reddit':{'required_unfinished_queries':1}};self.refresh_quality()
        self.assertFalse(self.accept()['task_complete']);self.assertIn('reddit',self.accept()['actionable_sources'])

    def test_total_shortfall_keeps_eligible_core_sources_actionable(self):
        self.contract['quality_thresholds']['min_included_records']=5;self.lock=make_lock(self.contract);self.refresh_quality(['included_records'])
        self.assertEqual(set(self.accept()['actionable_sources']),{'youtube','reddit'})

    def test_plan_cannot_downgrade_required_source(self):
        self.plan['sources'][0]['required_for_completion']=False
        self.assertFalse(self.accept()['scope_valid'])

    def test_rewriting_contract_and_plan_does_not_replace_lock(self):
        self.contract['sample_plan']['allocation']=self.contract['sample_plan']['allocation'][1:]
        self.plan['sources']=self.plan['sources'][1:]
        self.assertFalse(self.accept()['scope_valid'])

    def test_floor_and_membership_changes_detected(self):
        for key,value in [('record_floor',0),('min_distinct_parents',0),('source_members',['youtube','reddit'])]:
            plan=copy.deepcopy(self.plan);plan['sources'][0][key]=value
            self.assertTrue(check_scope(self.contract,self.lock,plan))

    def test_titles_transcripts_and_snippets_are_discovery_only(self):
        for typ in ('title','video','transcript','search_result'):
            r=dict(self.records[0],record_type=typ);self.assertFalse(valid_voc(r))
        r=dict(self.records[0],verification_tier='search_index_only');self.assertFalse(valid_voc(r))

    def test_no_human_audit_credit_from_model_review(self):
        self.audit['audit_type']='assistant';self.refresh_quality()
        self.assertFalse(self.accept()['human_audit_complete']);self.assertFalse(self.accept()['task_complete'])

    def test_group_approval_does_not_count_as_record_audit(self):
        self.audit={'reviewed':0,'fully_correct':0,'audit_type':'human','taxonomy_approved':True};self.refresh_quality()
        self.assertFalse(self.accept()['final_report_allowed'])

    def test_stale_quality_blocks_reacceptance(self):
        self.records[0]['text']='Changed evidence after quality checks'
        self.assertFalse(self.accept()['quality_inputs_current']);self.assertFalse(self.accept()['final_report_allowed'])

    def test_forged_pass_does_not_override_failed_gate(self):
        self.refresh_quality(['annotation_validation_errors']);self.q['status']='pass'
        self.assertFalse(self.accept()['final_report_allowed'])

    def test_independent_channel_saturation_required_for_partial(self):
        self.records=self.records[1:];self.anns=self.anns[1:]
        self.rounds.update(saturation_stop_allowed=True,source_saturation={'reddit':{'saturation_stop_allowed':True}})
        self.refresh_quality(['included_records'])
        self.assertFalse(self.accept()['final_report_allowed'])
        self.rounds['source_saturation']['youtube']={'saturation_stop_allowed':True};self.refresh_quality(['included_records'])
        r=self.accept();self.assertEqual(r['state'],'partial');self.assertTrue(r['final_report_allowed']);self.assertFalse(r['task_complete'])

    def test_manual_handoff_preserves_checkpoint_and_deduplicates_resume(self):
        plan=self.put('plan.json',self.plan)
        base=['--source-plan',plan,'--source','reddit']
        args=['--event','verification_required','--event-id','handoff-1','--page-url','https://example.invalid/reviews?page=4','--browser-ref','tab:fixture','--query-id','q1','--parent-id','p1','--position','page4','--last-source-id','last-record']
        self.run_cli('source_access.py',*base,*args)
        row=json.loads(plan.read_text())['sources'][1];self.assertEqual(row['status'],'waiting_for_user_verification')
        self.run_cli('source_access.py',*base,'--event','resume_confirmed','--event-id','resume-1',code=2)
        resume=['--event','resume_confirmed','--event-id','resume-1','--user-action-ref','user:fixture-completed','--evidence-ref','visible-body:fixture']
        self.run_cli('source_access.py',*base,*resume);self.run_cli('source_access.py',*base,*resume)
        row=json.loads(plan.read_text())['sources'][1]
        self.assertEqual(row['status'],'collecting');self.assertEqual(row['resume_from']['position'],'page4')
        self.assertEqual(row['resume_from']['last_source_id'],'last-record')
        self.run_cli('source_access.py',*base,*args)
        self.assertEqual(json.loads(plan.read_text())['sources'][1]['status'],'collecting')
        self.assertEqual(len((self.w/'manifests/access_handoffs.jsonl').read_text().splitlines()),2)

    def test_failed_manual_attempt_keeps_channel_pending(self):
        plan=self.put('plan.json',self.plan);base=['--source-plan',plan,'--source','reddit']
        self.run_cli('source_access.py',*base,'--event','verification_required','--event-id','v1','--page-url','https://example.invalid/review','--browser-ref','tab:fixture')
        self.run_cli('source_access.py',*base,'--event','verification_failed','--event-id','v2','--user-action-ref','user:fixture','--reason','Verification still displayed')
        row=json.loads(plan.read_text())['sources'][1];self.assertEqual(row['status'],'waiting_for_user_verification');self.assertEqual(row['handoff']['manual_attempts'],1)

    def test_handoff_rejects_session_parameters(self):
        plan=self.put('plan.json',self.plan)
        self.run_cli('source_access.py','--source-plan',plan,'--source','reddit','--event','verification_required','--event-id','v1','--page-url','https://example.invalid/reviews?session=synthetic','--browser-ref','tab:fixture',code=2)

    def test_freeze_refuses_unapproved_change_after_collection(self):
        c=self.put('contract.json',self.contract);lock=self.put('scope_lock.json',self.lock)
        (self.w/'raw').mkdir();(self.w/'raw/evidence.csv').write_text('{}\n')
        self.run_cli('freeze_scope.py','--contract',c,'--output',lock,code=2)
        self.run_cli('freeze_scope.py','--contract',c,'--output',lock,'--before-collection',code=2)
        self.run_cli('freeze_scope.py','--contract',c,'--output',lock,'--approval-ref','user:fixture-scope-decision')
        self.assertTrue((self.w/'manifests/scope_history.jsonl').exists())

    def yield_run(self,values,statuses=None,extra_matrix=False):
        rounds=['round_1','round_2','round_3'];matrix=[{'query_id':str(i),'source':'youtube','round':r} for i,r in enumerate(rounds)]
        attempts=[dict(m,new_relevant_records=n,relevant_records=999 if n==0 else n,status=(statuses or ['complete']*3)[i]) for i,(m,n) in enumerate(zip(matrix,values))]
        if extra_matrix:matrix.append({'query_id':'unrun','source':'youtube','round':'round_3'})
        mp=self.put('matrix.jsonl',matrix,True);ap=self.put('attempts.jsonl',attempts,True)
        self.run_cli('round_yield.py','--matrix',mp,'--attempts',ap,'--output',self.w/'yield.json')
        return json.loads((self.w/'yield.json').read_text())

    def test_unknown_failed_rounds_never_establish_saturation(self):
        r=self.yield_run([100,None,None],['complete','blocked_checkpoint','waiting_for_user_login'])
        self.assertFalse(r['saturation_stop_allowed']);self.assertIsNone(r['global_rounds'][-1]['new_relevant_records'])

    def test_zero_increment_is_not_replaced_by_relevant_total(self):
        r=self.yield_run([100,0,0]);self.assertTrue(r['saturation_stop_allowed']);self.assertEqual(r['global_rounds'][-1]['new_relevant_records'],0)

    def test_unattempted_expansion_query_prevents_saturation(self):
        self.assertFalse(self.yield_run([100,0,0],extra_matrix=True)['saturation_stop_allowed'])

    def test_two_successful_empty_expansions_can_document_zero_universe(self):
        r=self.yield_run([0,0,0]);self.assertTrue(r['source_saturation']['youtube']['saturation_stop_allowed'])
        self.assertIsNone(r['global_rounds'][-1]['incremental_new_relevant_pct'])

    def write_receipt(self,incomplete=False):
        if incomplete:self.records=self.records[1:];self.anns=self.anns[1:];self.refresh_quality(['included_records'])
        data={'contract':self.contract,'scope_lock':self.lock,'source_plan':self.plan,'records':self.records,'annotations':self.anns,'quality_gate':self.q,'audit_result':self.audit,'round_summary':self.rounds,'statistics':{'denominators':{'included_records':len(self.records)},'evidence_candidates':[dict(r,evidence_excerpt=r['text']) for r in self.records]},'taxonomy':{}}
        paths={k:self.put(k+('.jsonl' if k in {'records','annotations'} else '.json'),v,k in {'records','annotations'}) for k,v in data.items()}
        args=[v for k,p in paths.items() for v in ('--'+k.replace('_','-'),p)]
        self.run_cli('delivery_acceptance.py',*args,'--output',self.w/'acceptance.json',code=2 if incomplete else 0)
        return paths

    def report(self,paths,kind='final',code=0):
        args=[v for k in ('records','annotations','statistics','quality_gate','taxonomy') for v in ('--'+k.replace('_','-'),paths[k])]
        return self.run_cli('generate_report.py',*args,'--acceptance',self.w/'acceptance.json','--artifact-kind',kind,'--title','Synthetic VOC','--output',self.w/'report.html',code=code)

    def test_incomplete_final_refused_but_labelled_snapshot_allowed(self):
        paths=self.write_receipt(incomplete=True);self.report(paths,code=2);self.report(paths,'snapshot')
        text=(self.w/'report.html').read_text();self.assertIn('PROGRESS SNAPSHOT',text);self.assertIn('"task_complete": false',text)
        self.run_cli('validate_report.py','--report',self.w/'report.html','--records',paths['records'],'--acceptance',self.w/'acceptance.json','--artifact-kind','snapshot')

    def test_complete_render_and_delivery_validation(self):
        paths=self.write_receipt();self.report(paths)
        self.run_cli('validate_report.py','--report',self.w/'report.html','--records',paths['records'],'--acceptance',self.w/'acceptance.json')

    def test_data_change_invalidates_old_receipt(self):
        paths=self.write_receipt();paths['records'].write_text('[]\n');self.report(paths,code=2)

    def test_final_validation_cannot_be_bypassed_by_renaming_snapshot(self):
        paths=self.write_receipt(incomplete=True);self.report(paths,'snapshot')
        self.run_cli('validate_report.py','--report',self.w/'report.html','--records',paths['records'],'--acceptance',self.w/'acceptance.json',code=2)

    def test_custom_html_needs_same_delivery_marker(self):
        paths=self.write_receipt();self.report(paths)
        p=self.w/'report.html';p.write_text(p.read_text().replace('id="delivery-acceptance"','id="renamed-marker"'))
        self.run_cli('validate_report.py','--report',p,'--records',paths['records'],'--acceptance',self.w/'acceptance.json',code=2)

if __name__=='__main__':unittest.main(verbosity=1)
