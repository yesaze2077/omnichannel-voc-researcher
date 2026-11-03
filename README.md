# Omnichannel VOC Researcher

Version **1.3.0** · 2026-11-03

> **仅供非商业的交流学习、个人研究和教学实验。** 本仓库不授权商业化使用，也不授权访问、抓取、复制、存储、再发布或出售任何第三方平台数据。使用者必须自行遵守适用法律、平台服务条款、API 政策、robots/access controls、隐私义务和内容权利。详见 [NOTICE.md](NOTICE.md) 与 [LICENSE](LICENSE)。

> **For noncommercial learning, research, and technical exchange only.** This repository does not authorize access to, collection of, storage of, republication of, or commercial use of third-party platform data. Users remain responsible for applicable law, platform terms, API policies, access controls, privacy duties, and content rights. See [NOTICE.md](NOTICE.md) and [LICENSE](LICENSE).

An auditable Codex/agent Skill for multi-channel Voice of Customer research across YouTube, public forums, Old Reddit, Amazon, X, TikTok, Facebook, Instagram, review platforms, independent sites, app stores, and authorized first-party data.

## What it does

- chooses a post-clean evidence target from the business decision and research depth, allowing smaller justified teaching/pilot targets declared before collection without dropping promised channels;
- freezes required sources, roles/members, record/parent floors, and quality thresholds; later scope reductions require an actual recorded user decision;
- allocates evidence by channel role instead of assigning equal counts;
- separates each channel's interpretability floor, collection goal, and concentration cap so optional-source shortfalls can move to core channels without truncating valid evidence;
- builds pilot, formal, gap-driven, and supplemental search matrices with a declared negative-query cap;
- measures per-query and per-source round yield; unknown increments, failed requests, unattempted queries, and user waits cannot count as zero-yield saturation;
- saves browser checkpoints for user-assisted login or connection verification, resumes only after actual user completion plus visible-body verification, and continues other executable work meanwhile;
- records Reddit authorization scope and can make Old Reddit the preferred authorized entrypoint while keeping normal Reddit as a one-step fallback;
- makes YouTube, searchable vertical forums, and Old Reddit the core of deep public-web research;
- uses the YouTube Data API first for search, metadata, comments, and replies, with captions recovered separately;
- keeps high-control social channels small, supervised, and subject to explicit stop rules;
- normalizes, cleans, deduplicates, codes, audits, and calculates statistics with separate denominators;
- uses one input-hash-bound delivery-acceptance receipt for bundled and custom reports; progress snapshots always show `task_complete=false`, and only full acceptance completes the original task.

## Default deep product-improvement portfolio

The bundled planner adapts the post-clean target to the research decision. Deep rating-recovery work defaults to 1,080 retained records, keeps YouTube, public forums, and Old Reddit as the core, and reserves bounded completion cells for X, TikTok, Facebook, Instagram, review platforms, independent sites, and app stores.

```bash
python3 scripts/plan_sample.py \
  --mode product-improvement \
  --depth deep \
  --channels youtube owner_forum reddit amazon x tiktok facebook instagram first_party \
  --output sample_plan.json
```

Build and measure the restartable search rounds:

```bash
python3 scripts/build_search_matrix.py \
  --category "4x6 thermal shipping label printers" \
  --mode listing-content \
  --stage pilot \
  --sources youtube reddit \
  --core-terms "4x6 thermal label printer,bluetooth shipping label printer" \
  --reddit-entrypoint old \
  --reddit-authorization-status user_confirmed \
  --output search/pilot.jsonl

python3 scripts/round_yield.py \
  --matrix search/all_queries.jsonl \
  --attempts rounds/attempts.jsonl \
  --output rounds/round_yield.json
```

For YouTube, the deep default also emits raw collection goals of at least 180 video candidates and 3,000 comment/reply candidates before relevance filtering, deduplication, parent caps, and quality exclusions. Raw candidates are not added to the post-clean total.

## Restart and delivery contract

`init_study.py` derives the source plan from the contract and creates a scope lock. Inspect and finalize the contract before collecting. `freeze_scope.py --before-collection` may replace the lock only before any nonempty raw/normalized/analysis JSONL exists; later changes need `--approval-ref user:<actual-decision-reference>` and preserve history.

Use `source_access.py` to save `verification_required` or `login_required` checkpoints and `resume_confirmed` with user-action and readable-body evidence references. Trustpilot-style connection verification follows this direct-user-assistance path; it does not justify omitting required review-site coverage. Real access denial remains a stop boundary.

Before exporting any report:

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

A receipt can report unfinished work and exit 2; inspect it and continue `next_action`. Both `generate_report.py` and `validate_report.py` require `--acceptance`. Recompute acceptance after bound inputs change. `--artifact-kind final` is the renderer default; use `--artifact-kind snapshot` only for visibly marked `PROGRESS SNAPSHOT` material with `task_complete=false`. Custom HTML embeds the same `delivery-acceptance` JSON marker and uses the same validator; a legacy `--traceability-only` check does not authorize delivery.

A smaller target chosen before collection is valid for a bounded teaching task. Retrospectively renaming the task, dropping a required channel, lowering its floor, or replacing the requested output with a taxonomy draft/CSV/snapshot is not completion. A permitted saturation-limited `partial` report also retains `task_complete=false`.

See [the execution and delivery contract](references/execution-and-delivery.md) for event commands, resume evidence, source-local progress, scope revision, and final acceptance.

## Safe-use boundary

- Use official or explicitly authorized APIs where practical.
- Use browser-assisted reading only for a bounded, supervised, read-only sample.
- On normal login or connection verification/CAPTCHA/checkpoint, stop automated interaction, save the exact page/query/position, and actively ask the user to complete the displayed browser action directly. Never solve/bypass challenges or request credentials.
- Resume only after a user-completion reference and verified readable body. A real 403/429, denied access, rate limit, private-space boundary, or failed verification still stops that restricted route.
- One source wait or human calibration/audit dependency pauses only dependent work; continue other executable required sources and preparation. Required coverage cannot be downgraded because access is inconvenient.
- Do not rotate accounts, identities, proxies, or fingerprints; do not discover or call private endpoints.
- Do not enter private groups, private accounts, member-only areas, or content outside the authorized research scope.
- Keep API keys, cookies, browser profiles, raw author identifiers, and live study data outside Git.
- Treat successful page visibility as technical access only, not permission for recurring collection or commercial reuse.

## Install

```bash
git clone https://github.com/yesaze2077/omnichannel-voc-researcher.git
cp -R omnichannel-voc-researcher ~/.codex/skills/omnichannel-voc-researcher
```

Restart the agent session after installation. Read [SKILL.md](SKILL.md) for the full workflow and [references/sampling-strategy.md](references/sampling-strategy.md) for the sample-design contract.

## Validate

```bash
python3 tests/run_tests.py
python3 -m py_compile scripts/*.py tests/run_tests.py
```

Tests use synthetic fixtures. Do not commit live comments, transcripts, customer records, credentials, cookies, or commercial study outputs.

## License

Versions in this repository are provided under the [PolyForm Noncommercial License 1.0.0](LICENSE). Noncommercial sharing and modification must preserve the required notices. No license is granted to third-party platform content, trademarks, personal data, or datasets.
