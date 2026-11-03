# Scope, assisted access, resumption, and delivery

Use this contract for every study, including bounded teaching studies and custom reports. It prevents a local collection obstacle from silently changing the requested task.

## 1. Freeze the actual scope

Choose the decision, target, channel portfolio, source roles/members, record and independent-parent floors, evidence limits, and quality thresholds before collection. A small teaching or pilot task may justify a target below the default tiers. Record the reason and limits before collecting; preserve all channels promised by the user or contract. Smaller volume does not create permission to omit a channel.

`init_study.py` derives the source plan from the contract and creates `scope_lock.json`. Inspect the generated source inventory and plan before using them. The lock protects required status, floors, parent floors, roles, source members, and quality thresholds; collection goals and caps remain budgets, subject to the unchanged floors.

After pre-collection edits:

```bash
python3 scripts/freeze_scope.py \
  --contract study_contract.json \
  --source-plan source_plan.json \
  --before-collection \
  --output scope_lock.json
```

`--before-collection` may replace an existing lock only if raw, normalized, and analysis contain no nonempty collection files. Once collection starts, an actual user decision is required:

```bash
python3 scripts/freeze_scope.py \
  --contract study_contract.json \
  --source-plan source_plan.json \
  --approval-ref user:scope-decision-reference \
  --output scope_lock.json
```

The reference must identify the user's real decision; a CLI string cannot grant approval. Preserve the previous lock and decision in scope history. Do not change required sources to optional/case-only, reduce floors, drop a source member, or rename the task as a “pilot” after seeing missing evidence. A source-plan-only edit does not revise the contract.

## 2. Save a checkpoint before asking for direct user action

Distinguish these observations:

| Observation | Action |
|---|---|
| Normal login or expired session | Record `login_required`; ask the user to sign in directly without sharing credentials |
| Connection verification, CAPTCHA, or checkpoint challenge | Record `verification_required`; stop automated interaction and ask the user to complete the displayed browser verification directly |
| User says the action is complete and the normal page body is visibly readable | Record `resume_confirmed` with both the user-action reference and visible-body evidence; resume the saved bounded route |
| User action did not clear the challenge | Record `verification_failed`; preserve the failure and stop this route |
| Real HTTP 403/429, denied access, rate limit, or explicit access restriction | Record `access_denied`; stop this restricted route and consider only an authorized fallback |

The agent must not solve the verification, bypass controls, rotate identity/proxy, enter private spaces, or request credentials. User-assisted completion applies only to the ordinary verification/login flow; it is not a workaround for a real access denial.

Record URL, browser/tab reference, query ID, parent ID, visible position, and last retained source ID, when available. Preserve unknown values as absent/empty rather than inventing them. Never store cookies, tokens, browser profiles, account identifiers, or secret-bearing screenshots.

Example pause:

```bash
python3 scripts/source_access.py \
  --source-plan source_plan.json \
  --source review_site \
  --event verification_required \
  --event-id review-verification-01 \
  --page-url https://example.invalid/reviews \
  --browser-ref browser-tab-reference \
  --query-id q_support_recovery \
  --parent-id review-profile \
  --position visible-review-position \
  --last-source-id last-retained-record \
  --evidence-ref manifests/verification-observation.json \
  --reason "Browser shows connection verification"
```

Tell the user which tab and action are needed: “The review page asks for connection verification. Please complete the displayed verification directly in that browser tab and tell me when the review text is visible. I will continue the other available sources meanwhile.” Trustpilot-style connection verification follows this route when the user has authorized assistance; do not substitute an automatic permanent stop.

After their completion message, inspect the normal page body once through the authorized browser. Confirmation alone is insufficient, and page visibility alone is not proof of the user's completed action:

```bash
python3 scripts/source_access.py \
  --source-plan source_plan.json \
  --source review_site \
  --event resume_confirmed \
  --event-id review-resume-01 \
  --user-action-ref user:verification-completed-reference \
  --evidence-ref manifests/visible-review-body.json
```

Resume at the saved query/page/parent/position, append only new records, and deduplicate against the last retained IDs. Do not restart the study or silently replace the blocked source with a larger easy-channel sample.

## 3. Keep independent work moving

A source wait pauses that route, not the whole study. While it is pending, continue other executable required sources, clean collected records, preserve provenance, prepare review samples, and validate links. Keep high-risk social browser interactions sequential on the same account.

Human taxonomy calibration pauses dependent full annotation; human audit pauses final acceptance. Neither prevents unrelated collection or cleaning. Ask early, state the concrete review needed, and keep the unresolved dependency visible. Do not manufacture approval, audit results, or a user response.

Unknown incremental yield is null, never zero. A failed request, verification/login wait, absent count, or unattempted query cannot satisfy a saturation expansion. Each unfinished required source needs its own two consecutive successful, measured targeted expansions below the declared 5% threshold; a saturated easy source cannot close a waiting required source.

## 4. Use one acceptance receipt for every artifact

Quantity floors do not close an active required query or human-verification handoff. A required channel must also have no unfinished required query or access wait, even after its record and parent floors are met. The round summary records `source_execution` for this check.

The quality gate checks evidence. The unified delivery gate additionally checks locked scope, actual coverage, current access waits, audit, and measured rounds:

```bash
python3 scripts/delivery_acceptance.py \
  --contract study_contract.json \
  --scope-lock scope_lock.json \
  --source-plan source_plan.json \
  --records analysis/records_included.jsonl \
  --annotations analysis/annotations.jsonl \
  --quality-gate analysis/quality_gate.json \
  --audit-result analysis/audit_result.json \
  --round-summary rounds/round_yield.json \
  --statistics analysis/statistics/statistics.json \
  --taxonomy analysis/taxonomy.json \
  --output analysis/delivery_acceptance.json

python3 scripts/collection_state.py \
  --acceptance analysis/delivery_acceptance.json \
  --output rounds/workflow_state.json
```

The gate may write an unfinished receipt and exit 2. Inspect that receipt and continue its next action; do not treat it as task completion or hide it by manually generating another report.

Key receipt fields are `task_complete`, `final_report_allowed`, `snapshot_allowed`, `scope_valid`, `scope_errors`, `channel_coverage`, `required_shortfalls`, `actionable_sources`, `waiting_sources`, `state`, and `next_action`. The receipt binds its inputs by SHA; rendering and validation recheck those hashes. Recompute it after any bound input changes.

- Scope drift produces `scope_revision_needed` until the original scope is restored or an actual user-approved revision is frozen.
- Executable required collection produces `needs_append`/continue collection even if another source is waiting.
- Only unresolved direct-user access steps produce `waiting_for_user_verification` or `waiting_for_user_login` once other executable work is exhausted.
- Full acceptance produces `complete`, `task_complete=true`.
- A permitted saturation-limited report may produce `partial` and `final_report_allowed=true`, but retains `task_complete=false`; it does not claim the requested full task is achieved.

Use the receipt with both bundled and custom HTML paths. `generate_report.py` requires `--acceptance`; `--artifact-kind final` is the default and requires final permission. For intermediate material use `--artifact-kind snapshot`, show `PROGRESS SNAPSHOT` and `task_complete=false` in the title and body, plus the current state, missing coverage, and next action. Custom HTML must embed the same `delivery-acceptance` JSON marker as the bundled renderer. Run `validate_report.py --acceptance ...` on it as well. `--traceability-only` is available for legacy link/ID inspection only; it is not a delivery gate and cannot authorize a final artifact. A different filename, visual template, hand-written status badge, or report title cannot bypass acceptance.

A snapshot can make progress reviewable without claiming completion. It does not authorize ending the original task while required executable work remains. A limited final report must state the remaining original scope and the acceptance result honestly.
