"""Shared scope, evidence and delivery invariants. No network or account access."""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from common import normalize_space, read_json, read_jsonl, utc_now

WAITING = {"waiting_for_user_login", "waiting_for_user_verification", "blocked_checkpoint"}
BLOCKED = {"blocked", "blocked_access", "access_denied", "blocked_authorization", "blocked_robots", "rate_limited"}
CONTEXT_TYPES = {"video", "transcript", "transcript_video", "search_result", "title", "metadata", "editorial", "official_copy"}
CONTEXT_CLASSES = {"official", "official_context", "editorial", "editorial_context", "promotion", "creator_title_search_only", "search_index_only"}


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allocations(contract: dict) -> list[dict]:
    plan = contract.get("sample_plan", contract)
    return plan.get("allocation", [])


def required(row: dict) -> bool:
    return bool(row.get("required_for_completion", row.get("required", True)))


def scope_projection(contract: dict) -> dict:
    rows = []
    for row in allocations(contract):
        source = normalize_space(row.get("source"))
        if not source:
            raise ValueError("scope allocation needs a source")
        floor = int(row.get("record_floor", row.get("target_included_records", 0)))
        parents = int(row.get("min_distinct_parents", 0))
        if floor < 0 or parents < 0 or (required(row) and (floor < 1 or parents < 1)):
            raise ValueError(f"{source}: required sources need positive record and parent floors")
        rows.append({"source": source, "required_for_completion": required(row),
                     "record_floor": floor, "min_distinct_parents": parents,
                     "role": row.get("role", ""), "source_members": sorted(row.get("source_members", [source]))})
    declared=set(contract.get('channels',[]))
    if declared and declared!={r['source'] for r in rows}:
        raise ValueError('declared channels differ from scope allocations')
    if not rows or len({r['source'] for r in rows}) != len(rows):
        raise ValueError("scope needs nonempty, unique channel allocations")
    return {"channels": sorted(rows, key=lambda x: x['source']),
            "quality_thresholds": contract.get("quality_thresholds", {}),
            "research_mode": contract.get("research_mode", "")}


def make_lock(contract: dict, approval_ref: str = "initial_planning") -> dict:
    scope = scope_projection(contract)
    return {"schema_version": "3.0", "scope": scope, "scope_sha256": digest(scope),
            "frozen_at": utc_now(), "approval_ref": approval_ref}


def check_scope(contract: dict, lock: dict, plan: dict) -> list[str]:
    errors = []
    try:
        scope = scope_projection(contract)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    if lock.get("scope_sha256") != digest(lock.get("scope")) or lock.get("scope") != scope:
        errors.append("frozen scope differs from current contract; approved scope revision required")
    planned = {normalize_space(r.get('source')): r for r in plan.get('sources', [])}
    for row in scope['channels']:
        source = row['source']
        other = planned.get(source)
        if other is None:
            errors.append(f"missing planned channel: {source}")
            continue
        for key in ('record_floor', 'min_distinct_parents', 'role'):
            if other.get(key, '' if key == 'role' else 0) != row[key]:
                errors.append(f"{source}: source plan {key} differs from contract")
        if required(other) != row['required_for_completion']:
            errors.append(f"{source}: source plan changes completion requirement")
        if sorted(other.get('source_members', [source])) != row['source_members']:
            errors.append(f"{source}: source plan changes channel membership")
        if row['required_for_completion'] and other.get('relevance_status') in {'optional','excluded_with_reason','relevant_case_only'}:
            errors.append(f"{source}: required channel downgraded")
    return errors


def valid_voc(row: dict) -> bool:
    if not all(normalize_space(row.get(k)) for k in ('source_id', 'source', 'text', 'source_url')):
        return False
    if row.get('collection_status') in {'excluded', 'discovered', 'candidate', 'blocked'} or row.get('not_voc') is True:
        return False
    if row.get('verification_tier') in {'search_index_only', 'search_snippet_only', 'search_result_only'}:
        return False
    if row.get('record_type') in CONTEXT_TYPES or row.get('evidence_class') in CONTEXT_CLASSES:
        return False
    if row.get('source') == 'youtube' and row.get('record_type') not in {'comment','reply','youtube_comment','youtube_reply'}:
        return False
    return True


def channel_coverage(contract: dict, plan: dict, records: list[dict], rounds: dict) -> list[dict]:
    valid = {r['source_id']: r for r in records if valid_voc(r)}
    planned = {r.get('source'): r for r in plan.get('sources', [])}
    saturation = rounds.get('source_saturation', {})
    rows = []
    for row in scope_projection(contract)['channels']:
        source = row['source']
        members = set(row['source_members'])
        subset = [r for r in valid.values() if r['source'] in members]
        parents = {(r['source'], r.get('parent_id')) for r in subset if normalize_space(r.get('parent_id'))}
        met = len(subset) >= row['record_floor'] and len(parents) >= row['min_distinct_parents']
        status = planned.get(source, {}).get('status', 'planned')
        round_waits = set(rounds.get('waiting_for_user_login_sources',[])) | set(rounds.get('waiting_for_user_verification_sources',[]))
        execution = rounds.get('source_execution',{}).get(source,{})
        needs_handoff = status in WAITING or source in round_waits
        if source in round_waits and status not in WAITING:
            status = 'waiting_for_user_verification' if source in rounds.get('waiting_for_user_verification_sources',[]) else 'waiting_for_user_login'
        execution_met = not needs_handoff and status not in BLOCKED and not execution.get('required_unfinished_queries',0)
        saturated = all(saturation.get(s, {}).get('saturation_stop_allowed') is True for s in members)
        rows.append(dict(row, valid_records=len(subset), independent_parents=len(parents),
                         coverage_met=met, execution_met=execution_met, status=status, saturated=saturated,
                         actionable=row['required_for_completion'] and (not met or not execution_met) and not needs_handoff and status not in BLOCKED and not saturated,
                         waiting_for_user=needs_handoff))
    return rows


def acceptance(contract: dict, lock: dict, plan: dict, records: list[dict], annotations: list[dict], quality: dict, audit: dict, rounds: dict) -> dict:
    scope_errors = check_scope(contract, lock, plan)
    coverage = channel_coverage(contract, plan, records, rounds) if not scope_errors else []
    unmet = [r for r in coverage if r['required_for_completion'] and (not r['coverage_met'] or not r['execution_met'])]
    actionable = [r['source'] for r in unmet if r['actionable']]
    waiting = [r['source'] for r in unmet if r['waiting_for_user']]
    valid_ids = {r['source_id'] for r in records if valid_voc(r)}
    annotation_ids = [a.get('source_id') for a in annotations]
    qgates = quality.get('gates', [])
    # Legacy gate statuses are not sufficient proof. Verify each critical gate too.
    critical_failed = [g.get('name','unknown') for g in qgates if g.get('critical', True) and g.get('passed') is not True]
    thresholds = contract.get('quality_thresholds', {})
    reviewed, correct = int(audit.get('reviewed',0)), int(audit.get('fully_correct',0))
    human = audit.get('audit_type', audit.get('reviewer_type','unconfirmed')) in {'human','human_audit'}
    audit_target = min(len(valid_ids), max(50, (len(valid_ids)+19)//20))
    audit_ok = bool(valid_ids) and human and reviewed >= audit_target and correct <= reviewed and correct/max(1,reviewed)*100 >= float(thresholds.get('min_audit_accuracy_pct',90))
    coding_ok = len(annotation_ids)==len(set(annotation_ids)) and valid_ids==set(annotation_ids)
    evidence_clean = len(records)==len(valid_ids)
    expected_digests = {'records':digest(records),'annotations':digest(annotations),'contract':digest(contract),'audit_result':digest(audit),'round_summary':digest(rounds)}
    quality_fresh = all(quality.get('input_digests',{}).get(k)==v for k,v in expected_digests.items())
    round_ok = bool(rounds.get('global_rounds')) and not rounds.get('unknown_attempt_query_ids') and not rounds.get('mismatched_attempt_query_ids')
    minimum_total = int(thresholds.get('min_included_records',50))
    remaining_floor_records=sum(max(0,r['record_floor']-r['valid_records']) for r in unmet)
    if len(valid_ids)+remaining_floor_records<minimum_total:
        for r in coverage:
            if r['required_for_completion'] and r['role']=='core' and r['execution_met'] and not r['saturated'] and r['source'] not in actionable:
                allocation=next(x for x in allocations(contract) if x['source']==r['source'])
                cap=int(allocation.get('record_cap',0))
                if not cap or r['valid_records']<cap:actionable.append(r['source'])
    all_quality_pass = len(valid_ids)>=minimum_total and bool(qgates) and not critical_failed
    complete = not scope_errors and not unmet and audit_ok and coding_ok and round_ok and evidence_clean and quality_fresh and all_quality_pass
    coverage_names = ('included_records','distinct_sources','largest_source_pct','largest_parent_share_pct','source_')
    quality_data_ok = bool(qgates) and all(n.startswith(coverage_names) for n in critical_failed)
    partial = (not scope_errors and not complete and audit_ok and coding_ok and round_ok and quality_data_ok and evidence_clean and quality_fresh
               and not actionable and not waiting and all(r['saturated'] for r in unmet)
               and rounds.get('saturation_stop_allowed') is True)
    if scope_errors:
        state, action = 'scope_revision_needed', 'restore_frozen_scope_or_record_user_approved_revision'
    elif complete:
        state, action = 'complete', 'generate_final_report'
    elif actionable:
        state, action = 'needs_append', 'continue_collection'
    elif waiting:
        verification = any(r['status'] != 'waiting_for_user_login' for r in unmet if r['waiting_for_user'])
        state = 'waiting_for_user_verification' if verification else 'waiting_for_user_login'
        action = 'request_human_handoff_then_resume'
    elif partial:
        state, action = 'partial', 'generate_partial_report_with_shortfalls'
    elif not audit_ok or not coding_ok:
        state, action = 'human_audit', 'complete_coding_and_human_audit'
    else:
        state, action = 'needs_append', 'resolve_remaining_quality_or_access_gaps'
    return {'schema_version':'3.0', 'generated_at':utc_now(), 'state':state, 'next_action':action,
            'task_complete':bool(complete), 'final_report_allowed':bool(complete or partial),
            'snapshot_allowed':True, 'scope_valid':not scope_errors, 'scope_errors':scope_errors,
            'channel_coverage':coverage, 'required_shortfalls':[r['source'] for r in unmet],
            'actionable_sources':actionable, 'waiting_sources':waiting,
            'valid_voc_records':len(valid_ids), 'context_or_discovery_records':len(records)-len(valid_ids),
            'human_audit_complete':audit_ok, 'coding_complete':coding_ok, 'round_evidence_present':round_ok, 'quality_inputs_current':quality_fresh, 'core_evidence_clean':evidence_clean,
            'quality_status':quality.get('status','not_run'), 'failed_quality_gates':critical_failed}


def add_input_provenance(result: dict, paths: dict[str,Path], output: Path) -> dict:
    result['inputs'] = {key:{'path':os.path.relpath(p.resolve(), output.resolve().parent), 'sha256':file_digest(p)} for key,p in paths.items()}
    result['acceptance_sha256'] = digest(result)
    return result


def load_acceptance(path: Path, kind: str, expected: dict[str,Path] | None = None) -> dict:
    receipt = read_json(path)
    unsigned = {k:v for k,v in receipt.items() if k!='acceptance_sha256'}
    if receipt.get('acceptance_sha256') != digest(unsigned):
        raise ValueError('delivery acceptance receipt is missing or altered')
    required_inputs = {'contract','scope_lock','source_plan','records','annotations','quality_gate','audit_result','round_summary'}
    if not required_inputs.issubset(receipt.get('inputs',{})):
        raise ValueError('delivery acceptance receipt lacks required inputs')
    if expected and not set(expected).issubset(receipt['inputs']):
        raise ValueError('render inputs were not bound by delivery_acceptance.py')
    loaded = {}
    for key, item in receipt['inputs'].items():
        target = (path.parent/item['path']).resolve()
        if not target.is_file() or file_digest(target)!=item['sha256']:
            raise ValueError(f'stale acceptance input: {key}; rerun delivery_acceptance.py')
        if expected and key in expected and target != expected[key].resolve():
            raise ValueError(f'render input differs from accepted {key}')
        loaded[key] = read_jsonl(target) if key in {'records','annotations'} else read_json(target)
    recomputed = acceptance(loaded['contract'],loaded['scope_lock'],loaded['source_plan'],loaded['records'],loaded['annotations'],loaded['quality_gate'],loaded['audit_result'],loaded['round_summary'])
    for key in ('task_complete','final_report_allowed','state','scope_valid'):
        if receipt.get(key)!=recomputed[key]:
            raise ValueError('acceptance result differs from current invariants')
    if kind=='final' and not receipt.get('final_report_allowed'):
        raise ValueError('final report refused: unresolved channel, verification, scope, or audit gates; export a labelled snapshot and continue work')
    return receipt


def delivery_marker(receipt: dict, kind: str) -> dict:
    return {'artifact_kind':kind, 'task_complete':receipt['task_complete'] if kind=='final' else False,
            'state':receipt['state'], 'acceptance_sha256':receipt['acceptance_sha256']}
