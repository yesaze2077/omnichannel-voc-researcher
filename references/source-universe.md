# Source universe and completion contract

Create a source-universe inventory before sampling. Its purpose is not to force collection from every site on the internet; it prevents a relevant evidence family from disappearing merely because a high-volume source reached the total-row target.

## Required fields

Each source-family row must include:

- `source_family` and `source_members`
- `decision_role`
- `evidence_class`
- `relevance_status`: `required`, `relevant_case_only`, `optional`, or `excluded_with_reason`
- `record_floor`, `record_goal`, `record_cap`, and `min_distinct_parents`
- `collection_stage`
- `access_order`, `access_mode`, and `authorization_status`
- `current_records`, `current_parents`, `completion_status`, and `gap`
- `exclusion_reason` when excluded
- `denominator_rule` and `allowed_interpretation`

`required` means the source family must meet its floor or the study remains `needs_append`, `waiting_for_user_login`, or `partial`. `Relevant_case_only` means examples may inform hypotheses but cannot enter cross-source agreement or incidence claims. `Optional` must be justified in the contract. Never infer `optional` from collection difficulty. Derive the source plan from the contract and freeze required status, roles, members, record/parent floors, and quality thresholds before collection. A waiting source cannot be relabeled case-only or optional to make delivery pass. Only an actual user-approved scope decision may revise the lock; see [execution-and-delivery.md](execution-and-delivery.md).

## Default deep listing-content universe

| Source family | Typical members | Primary role | Default completion treatment |
|---|---|---|---|
| Video/community video | YouTube | workflows, demonstrations, setup, long-form owner experience, comments | core required |
| General discussion | Old Reddit / Reddit | candid problems, workarounds, comparisons, purchase language | core required |
| Vertical and commerce communities | Shopify Community, Amazon Seller Forums, eBay Community, Etsy Community, seller forums and category forums | operational workflows, platform-specific problems, troubleshooting | required family; multiple domains |
| Marketplace reviews and Q&A | target Amazon parent, direct competitors, premium and value alternatives, relevant retailer reviews | purchase objections, ratings, verified-use signals, competitor comparison | required when the decision is a listing or product claim |
| High-risk social | Facebook, TikTok, Instagram, X | current creator language, short-form objections, use demonstrations, community reactions | required targeted completion when relevant; normally 30 records and 10 parents per enabled channel |
| Third-party review platforms | Trustpilot, Sitejabber and relevant equivalents | brand trust, shipping, warranty and support | required when assurance or service affects purchase; keep brand-level evidence separate |
| Independent and brand/store review pages | public store review widgets, public product Q&A, public comments on independent reviews | product language, store-level ownership signals, additional objections | required targeted completion when user expression exists |
| App stores | Apple App Store and Google Play | app setup, driver/app dependency, mobile workflow and update problems | required or case-only based on product workflow relevance |
| First-party | support, returns, surveys, site search, CRM | direct operational truth | required only when supplied and authorized; separate denominator |

Editorial reviews, affiliate articles, official product copy, manuals, help pages, and creator sponsorship disclosures are contextual evidence. They may verify product facts, search vocabulary, or claim boundaries, but are not VOC unless a retained user review, Q&A, or comment is the record.

## Sequencing

1. Inventory all relevant families.
2. Build and collect broad core matrices.
3. Clean and run preliminary analysis.
4. Translate the top objections, conflicts, and missing segments into a targeted-completion matrix.
5. Collect small bounded samples from Facebook, TikTok, Instagram, X, review platforms, independent/store review pages, app stores, and any remaining vertical-community gaps.
6. Recompute each family ledger and the all-channel completion gate.

High-risk social collection remains sequential, supervised, read-only, and bounded. Login becomes `waiting_for_user_login`; connection verification becomes `waiting_for_user_verification`. Stop automation, save the checkpoint, and ask for direct user completion; resume after the completion reference and visible-body verification. Real 403/429, access denial, rate limits, or failed verification stop the affected route. Continue other executable work while one source waits.

## Completion semantics

Track two independent statuses:

- `core_evidence_status`: whether broad evidence is large and diverse enough for preliminary themes.
- `omnichannel_completion_status`: whether every required family met its floor and evidence question.

A final decision-grade report requires both and a fresh unified acceptance receipt. If only the first passes, a progress snapshot may present hypotheses and a completion plan with `CORE READY / OMNICHANNEL NEEDS APPEND`, the unmet source rows, and `task_complete=false`. Source saturation is measured per unfinished required source; verification/login waits are not saturation. Custom and bundled reports use the same acceptance path.
