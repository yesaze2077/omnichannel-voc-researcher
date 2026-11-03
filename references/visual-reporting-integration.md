# Visual report integration contract

Use `visual-report-skill` for the final decision report whenever it is available. The purpose is to turn validated evidence into a fast, source-traceable decision interface.

## Inputs

For final rendering, require a fresh unified acceptance receipt plus these files:

- study contract, scope lock/history, and source universe
- source plan and channel-family completion ledger
- workflow state, failure log, and access-authorization manifest
- included records, annotations, taxonomy, and audit result
- deterministic statistics with explicit denominators
- core quality gate, omnichannel completion gate, and input-hash-bound delivery acceptance
- listing or business recommendations with claim-evidence links

A progress snapshot can render the available subset only when unified acceptance allows snapshots. Clearly show `PROGRESS SNAPSHOT`, the current state, missing inputs/coverage, next action, and `task_complete=false`; leave absent statistics absent. It is an intermediate artifact, not a replacement task.

## Report IR

Write `reports/report_ir.json` as the single report contract. Include:

- `report_status`, `core_evidence_status`, `omnichannel_completion_status`, artifact kind, `task_complete`, and the delivery-acceptance reference
- audience, decision question, scope, time window, and product relation
- top decisions, prioritized actions, veto conditions, and confidence labels
- source coverage ledger with floor, actual records, parent count, access state, gap, and interpretation permission
- source-specific themes and conflicts; never a blended internet sentiment rate
- evidence chains from conclusion to statistic to retained `source_id` and source URL
- claim-evidence matrix and listing/content implications when relevant
- missingness, excluded evidence, limitations, and next collection step
- chart specifications, table specifications, citations, and proof notes
- for rating recovery: baseline provenance, rating-driver tree, product-vs-setup-vs-expectation-vs-support action lanes, recent-window evidence, target/hold period, and guardrails

## Visual structure

Default to the `voc_insight_report` template and `voc_insight` archetype. Use progressive disclosure:

- L0: one-screen answer, decision status, largest risks, and next action
- L1: prioritized actions, purchase objections, source-family coverage, and confidence
- L2: channel comparisons, theme evidence, competitor patterns, and claim boundaries
- L3: methods, denominators, quality gates, missingness, evidence IDs, and collection history

Apply CEICA: conclusion, evidence, implication, confidence, action. Every visual needs a decision purpose. Prefer small-multiple source comparisons, ranked bars, coverage ledgers, evidence matrices, and action tables over decorative charts.

For rating recovery, the executive layer should show the displayed-rating baseline and its evidence status, the controllable-driver priority stack, and the next intervention. Do not draw a rating trajectory when only one verified observation exists; use a baseline card and a measurement plan instead.

## Status presentation

Always show core readiness and all-channel completion separately. Use these labels exactly when applicable:

- `CORE READY / OMNICHANNEL COMPLETE`
- `CORE READY / OMNICHANNEL NEEDS APPEND`
- `CORE READY / WAITING FOR USER LOGIN`
- `CORE READY / WAITING FOR USER VERIFICATION`
- `PARTIAL / SATURATION STOP`
- `BLOCKED`

Do not let a legacy or core-only `PASS` badge appear as the overall report status when a required social, vertical-community, review-platform, independent-site, app-store, or marketplace cell is missing. An eligible `PARTIAL / SATURATION STOP` report still states `task_complete=false`. Verification/login waits and unknown increments cannot justify that status.

## QA gate

Before delivery:

1. Recompute `delivery_acceptance.py` from current inputs, inspect final/snapshot permission, and verify its bound hashes. All custom HTML and bundled render paths use this same receipt and embedded `delivery-acceptance` JSON marker; call `validate_report.py --acceptance ...`. A legacy `--traceability-only` check does not satisfy delivery acceptance.
2. Validate HTML structure and local links.
3. Validate Report IR fields, denominators, evidence IDs, and source URLs.
4. Confirm every displayed number resolves to deterministic statistics or a contract field.
5. Confirm every required source family appears in the coverage ledger, including zero-count rows.
6. Inspect desktop and narrow layouts in a browser for clipping, overflow, contrast, hierarchy, and table readability.
7. Confirm the title, bullets, images/visual scripts, FAQ, or other recommended assets cover the top purchase objections or state an exclusion reason.
8. Save `reports/visual_qa.json` with viewport, result, findings, and unresolved risks.

The fallback report generator can prove traceability and structure. It cannot claim visual-report QA unless the Report IR and browser checks above pass.

A custom template, manually written HTML, different filename, or visually polished snapshot cannot bypass acceptance or shrink locked coverage. Rendering is presentation; only the acceptance result can authorize a final artifact or task-complete claim.
