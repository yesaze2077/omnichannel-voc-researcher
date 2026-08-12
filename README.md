# Omnichannel VOC Researcher

> **仅供非商业的交流学习、个人研究和教学实验。** 本仓库不授权商业化使用，也不授权访问、抓取、复制、存储、再发布或出售任何第三方平台数据。使用者必须自行遵守适用法律、平台服务条款、API 政策、robots/access controls、隐私义务和内容权利。详见 [NOTICE.md](NOTICE.md) 与 [LICENSE](LICENSE)。

> **For noncommercial learning, research, and technical exchange only.** This repository does not authorize access to, collection of, storage of, republication of, or commercial use of third-party platform data. Users remain responsible for applicable law, platform terms, API policies, access controls, privacy duties, and content rights. See [NOTICE.md](NOTICE.md) and [LICENSE](LICENSE).

An auditable Codex/agent Skill for multi-channel Voice of Customer research across YouTube, public forums, Old Reddit, Amazon, X, TikTok, Facebook, Instagram, and authorized first-party data.

## What it does

- chooses a post-clean evidence target from the business decision and research depth;
- allocates evidence by channel role instead of assigning equal counts;
- makes YouTube, searchable vertical forums, and Old Reddit the core of deep public-web research;
- uses the YouTube Data API first for search, metadata, comments, and replies, with captions recovered separately;
- keeps high-control social channels small, supervised, and subject to explicit stop rules;
- normalizes, cleans, deduplicates, codes, audits, and calculates statistics with separate denominators;
- produces source-traceable reports with `pass`, `partial`, or `blocked` quality status.

## Default deep product-improvement portfolio

The bundled planner starts from 1,500 post-clean records and adapts the allocation to enabled channels. A plan with all supported sources keeps YouTube, public forums, and Old Reddit as the majority, while X, TikTok, Facebook, and Instagram each receive a small interpretability floor.

```bash
python3 scripts/plan_sample.py \
  --mode product-improvement \
  --depth deep \
  --channels youtube owner_forum reddit amazon x tiktok facebook instagram first_party \
  --output sample_plan.json
```

For YouTube, the deep default also emits raw collection goals of at least 180 video candidates and 3,000 comment/reply candidates before relevance filtering, deduplication, parent caps, and quality exclusions. Raw candidates are not added to the post-clean total.

## Safe-use boundary

- Use official or explicitly authorized APIs where practical.
- Use browser-assisted reading only for a bounded, supervised, read-only sample.
- Stop on CAPTCHA, checkpoint, re-authentication, 403, 429, explicit access limits, or repeated error pages.
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
