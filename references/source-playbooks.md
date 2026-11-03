# Source Playbooks

Use each source for a distinct evidence role. Default limits are research guardrails, not platform permissions. Recheck current terms, account state, and official interfaces before every live study.

## High-risk social browser protocol

1. Use a user-authorized browser when authentication is required. For login or connection verification, save the query/page/parent/position checkpoint, stop automated interaction, and ask for direct user completion. Resume only after their completion reference plus visible-body verification. Never request or handle credentials. Use the event protocol in [execution-and-delivery.md](execution-and-delivery.md).
2. Name the session and collect only the planned public or account-visible sample.
3. Use one channel and one sequential browser flow at a time. Do not parallelize actions on the same account.
4. Read only. Do not like, follow, comment, message, purchase, join groups, or change settings.
5. Follow the predeclared sampling plan. A high-risk social channel normally needs at least 30 retained records and 10 independent parents to contribute to cross-channel agreement, while remaining below 6% of the total by default.
6. Record exact URL, visible timestamp, collection time, query, access mode, and any missing fields.
7. Login pauses as `waiting_for_user_login`; connection verification or CAPTCHA/checkpoint pauses automation as `waiting_for_user_verification` for direct user action. The agent never solves or bypasses it. Real 403/429, access denial, rate limits, or failed verification stop that affected route. Continue independent executable work; a local wait never becomes zero yield.
8. Do not solve access failures with proxy rotation, identity rotation, fingerprint spoofing, hidden endpoints, private areas, or guessed URL loops.

## YouTube

- Evidence role: deep reviews, demonstrations, installation, long-term ownership, comments, and transcripts.
- Main sample: delegate to `youtube-intelligence-researcher`. Use the official Data API first for search, video metadata, top-level comments, and replies within the current free quota.
- Current official documentation assigns a separate default bucket of 100 `search.list` calls/day; `videos.list`, `commentThreads.list`, and `comments.list` cost one unit/call in the 10,000-unit general daily allocation. Verify at run time: https://developers.google.com/youtube/v3/determine_quota_cost
- `commentThreads.list` can return up to 100 threads per page. Fetch missing replies with `comments.list`; preserve comment-disabled, pagination, and quota-stop states.
- Recover captions only after video relevance filtering. The official `captions.download` endpoint requires authorization and permission to edit the video, so an API key cannot download arbitrary public-video captions: https://developers.google.com/youtube/v3/docs/captions/download
- Keep video metadata, comments, and transcript-video denominators separate.
- Failure fallback: preserve quota, comments-disabled, unavailable, 429, and transcript challenge states.

## Reddit

- Evidence role: owner discussion, failures, workarounds, comparisons, fitment, and service experiences.
- Before collection, record `authorization_status`, approved scope, preferred entrypoint, fallback entrypoint, and confirmation time. A user attestation can be labeled `user_confirmed`; do not call it documented authorization unless evidence was actually reviewed. Never retain credentials, cookies, tokens, or account identifiers.
- Preferred route after authorization: Old Reddit search and original thread pages in the user's authorized browser. Use `https://www.reddit.com` only as a one-step fallback when a planned page is missing or materially incomplete.
- Record Old Reddit as `authorized_browser_old_reddit` and the fallback as `authorized_browser_modern_reddit`; do not merge the access modes in attempt manifests.
- Use bounded, sequential, restartable page collection with query and thread manifests. Large means the predeclared record/thread target, not unlimited crawling.
- Use standard search, pagination, and original thread links. Structured page output such as a visible `.json` endpoint is optional only when the authorization explicitly covers it and it is normally accessible. Never treat a hidden or blocked endpoint as a fallback.
- Prefer original posts and substantive comments. Exclude pure questions from owned-use incidence unless they contain experience evidence.
- Cap each parent thread at the study's predeclared concentration threshold; retain uncapped counts in the manifest.
- Official API fallback: use only if authorized and working. Record unavailable API access rather than inventing credentials.

## Public vertical forums

- Evidence role: long-term ownership, model-specific fitment, failures, repair, DIY workarounds, and specialist terminology.
- Treat normally searchable public threads as a core source. Plan the family before collection, build a domain/query matrix, deduplicate quoted replies, and retain the canonical thread/post URL. Passing YouTube or Reddit targets does not remove this family from a deep-study contract.
- Respect login walls, robots/access controls, explicit terms, and rate limits. Do not enter member-only areas or bypass anti-bot controls.
- Measure independent domains, threads, vehicle/product models, and publication periods; a large post count from one forum thread is not a broad sample.

## Amazon

- Evidence role: ratings, verified-purchase claims, fitment, shipping damage, durability, value, and service.
- Default route: supervised product and first review-page reading for a limited ASIN set.
- Record ASIN, star rating, review date, verified-purchase flag, helpful count, review URL, title, and body when visible.
- Keep product-level rating distributions separate from the sampled review-text distribution.
- Do not paginate continuously, run unattended scraping, or infer all reviews from the first page.
- Prefer authorized first-party exports or brand VOC tools when later available. Do not claim browser access is a stable commercial review API.

## X

- Evidence role: current discussion, launch reaction, service events, comparisons, and links to longer evidence.
- Default route: supervised search and detail-page reading for a small sample.
- On browser error or block, use the official API only with the user's authorized app, token, budget, and requested query. Never print tokens.
- Record API credits or resource reads in the manifest. Keep browser and API records distinguishable with `access_mode`.
- Recent-search windows and endpoint pricing can change; verify them at run time.

## TikTok

- Evidence role: scenes, installation ideas, creator demonstrations, objections, and user language.
- Default route: supervised logged-in search, open a small number of relevant videos, and read visible comments.
- Label creator/seller/affiliate content separately from organic user comments. A commission-eligible video is not independent product evidence.
- Exclude emoji-only, link requests, giveaway participation, and unrelated jokes from theme incidence.
- Official research interfaces may exclude commercial users. Verify eligibility rather than assuming access.
- When TikTok is declared in the source plan, run its small targeted sample after preliminary core analysis. Keep `waiting_for_user_login`, `needs_append`, or `partial` until the planned attempt/floor or documented saturation condition is satisfied.

## Facebook

- Evidence role: public Page posts and public group/community discussions visible to the authorized account.
- Status: experimental supplement. Search and rendering may be unstable or personalized.
- Do not enter or collect from private groups, friends-only content, or content not intended for the public research scope.
- A `Not Found`, login wall, or empty result after one standard path ends the attempt. Do not try URL variants in a loop.
- Automated collection generally requires Meta permission; small supervised reading lowers operational exposure but does not create authorization.
- When Facebook is declared in the source plan, run its small targeted sample after preliminary core analysis. A sufficient YouTube/Reddit/Amazon sample does not make this coverage optional.

## Instagram

- Evidence role: public posts/Reels, product demonstrations, captions, and visible comments.
- Status: experimental supplement. Login, dynamic loading, personalization, and access limits reduce reproducibility.
- Do not collect private-account content. Separate creator promotion from owner experience.
- Treat visible like/comment counts as distribution signals, not demand or satisfaction.
- Automated collection generally requires Meta permission; do not scale browser sampling into recurring automation.

## Third-party review platforms

- Evidence role: brand trust, fulfillment, warranty, customer support, returns, and cross-product reliability language. Trustpilot and Sitejabber are examples, not a complete or guaranteed source list.
- Preserve platform, company/profile URL, review URL, date, rating, verification label when visible, product/model named in the text, and company response as a separate record type.
- Keep brand-level service reviews separate from product-model evidence. A MUNBYN service review cannot prove an RW403B performance claim.
- Use normal public pages or an authorized export. Respect robots/access controls, pagination limits, terms, and rate limits; do not infer a stable commercial API from browser visibility.
- For Trustpilot-style connection verification, stop automated interaction and actively ask the user to complete the displayed verification in the browser. Save the exact review profile, query, page, and last retained ID. After user confirmation, verify the review body is readable and resume there; do not downgrade required review-site coverage. A real access denial or unsuccessful verification still stops that route.
- Platform aggregate ratings are contextual metadata. Sampled review text keeps its own denominator and must not be presented as the platform-wide distribution.

## Independent sites and brand/store review pages

- Evidence role: model-specific reviews, public Q&A, user comments, niche use scenes, setup language, and retailer/brand-store verified-purchase signals.
- Classify each record as user review/comment/Q&A, editorial review, affiliate/creator content, official copy, or retailer metadata. Only real user-expression records enter VOC counts.
- Brand-owned review widgets and independent third-party sites use separate source and evidence-class denominators; ownership by the seller must remain visible.
- Deduplicate syndicated reviews and copied editorial text across retailer, affiliate, and manufacturer pages.
- Capture canonical URL, visible date, product/model, rating/verification label when visible, and access mode. Use saved user-assisted login/verification checkpoints; stop restricted access under the standard failure rules. Keep waiting source floors unchanged.

## App stores

- Evidence role: app installation, Bluetooth pairing, permissions, updates, platform compatibility, account/login, template workflow, and app support.
- Use public Apple App Store and Google Play pages or an authorized export. Preserve app name/version when visible, store, rating, review/update date, device/OS context, and developer response as a separate record type.
- Keep app-level evidence separate from hardware-model evidence. A review of the brand app can define a workflow risk or search term, but it confirms a named device defect only when the review identifies that model.
- Deduplicate review updates and syndicated copies. Do not infer app-wide incidence from sorted or featured review pages.

## First-party data

- Evidence role: purchased-use feedback, support contacts, returns, refunds, warranty, surveys, product reviews, and site-search language.
- Preferred route: authorized exports or read-only APIs with a documented retention and access policy.
- Remove direct identifiers before normalization. Use stable case/order hashes only when linkage is necessary and authorized.
- Keep each operational system and event type as a separate denominator. A support ticket rate needs an eligible-order denominator, not the number of comments.

## Search and content discovery sources

Sitemaps, RSS, public product JSON, regulatory notices, and public documentation can support vocabulary, product facts, and safety context. They are external evidence, not consumer voice. Store them in a separate evidence table and never count them as VOC records.

## Source-local progress and completion

A source wait, denied route, taxonomy checkpoint, or audit dependency does not stop other authorized work. Preserve the source and resume metadata, then follow `actionable_sources` from unified acceptance. Unknown counts remain unknown; neither a login challenge nor a failed fetch is a successful zero-yield expansion. A working snapshot must retain the missing family in its coverage ledger and `task_complete=false`.
