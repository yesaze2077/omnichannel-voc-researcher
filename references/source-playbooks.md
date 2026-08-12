# Source Playbooks

Use each source for a distinct evidence role. Default limits are research guardrails, not platform permissions. Recheck current terms, account state, and official interfaces before every live study.

## High-risk social browser protocol

1. Use a user-authorized, already logged-in browser when authentication is required.
2. Name the session and collect only the planned public or account-visible sample.
3. Use one channel and one sequential browser flow at a time. Do not parallelize actions on the same account.
4. Read only. Do not like, follow, comment, message, purchase, join groups, or change settings.
5. Follow the predeclared sampling plan. A high-risk social channel normally needs at least 30 retained records and 10 independent parents to contribute to cross-channel agreement, while remaining below 6% of the total by default.
6. Record exact URL, visible timestamp, collection time, query, access mode, and any missing fields.
7. Stop on CAPTCHA, checkpoint, re-login, 403, 429, explicit rate limit, or repeated error/empty pages.
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
- Default route: standard public Old Reddit search and original thread pages. It may be a core, large planned sample when pages remain normally accessible.
- Use bounded, sequential, restartable page collection with query and thread manifests. Large means the predeclared record/thread target, not unlimited crawling.
- Structured page output such as a visible `.json` endpoint is optional only when normally accessible and permitted. Never depend on it as the sole route.
- Prefer original posts and substantive comments. Exclude pure questions from owned-use incidence unless they contain experience evidence.
- Cap each parent thread at the study's predeclared concentration threshold; retain uncapped counts in the manifest.
- Official API fallback: use only if authorized and working. Record unavailable API access rather than inventing credentials.

## Public vertical forums

- Evidence role: long-term ownership, model-specific fitment, failures, repair, DIY workarounds, and specialist terminology.
- Treat normally searchable public threads as a core source. Build a domain/query matrix, deduplicate quoted replies, and retain the canonical thread/post URL.
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

## Facebook

- Evidence role: public Page posts and public group/community discussions visible to the authorized account.
- Status: experimental supplement. Search and rendering may be unstable or personalized.
- Do not enter or collect from private groups, friends-only content, or content not intended for the public research scope.
- A `Not Found`, login wall, or empty result after one standard path ends the attempt. Do not try URL variants in a loop.
- Automated collection generally requires Meta permission; small supervised reading lowers operational exposure but does not create authorization.

## Instagram

- Evidence role: public posts/Reels, product demonstrations, captions, and visible comments.
- Status: experimental supplement. Login, dynamic loading, personalization, and access limits reduce reproducibility.
- Do not collect private-account content. Separate creator promotion from owner experience.
- Treat visible like/comment counts as distribution signals, not demand or satisfaction.
- Automated collection generally requires Meta permission; do not scale browser sampling into recurring automation.

## First-party data

- Evidence role: purchased-use feedback, support contacts, returns, refunds, warranty, surveys, product reviews, and site-search language.
- Preferred route: authorized exports or read-only APIs with a documented retention and access policy.
- Remove direct identifiers before normalization. Use stable case/order hashes only when linkage is necessary and authorized.
- Keep each operational system and event type as a separate denominator. A support ticket rate needs an eligible-order denominator, not the number of comments.

## Search and content discovery sources

Sitemaps, RSS, public product JSON, regulatory notices, and public documentation can support vocabulary, product facts, and safety context. They are external evidence, not consumer voice. Store them in a separate evidence table and never count them as VOC records.
