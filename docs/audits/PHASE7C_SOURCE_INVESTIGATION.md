# Phase 7C source investigation

Date: 21 October 2026 (MYT). Status: investigation started; no new source qualified and no overlap validation completed. Deadline remains **25 October 2026, 23:59 MYT**. Named field-evidence reviewer: **FubDuck88**; no review approval is inferred from this agent's access investigation.

## Scope and evidence handling

Requests were manual, bounded GETs with a two-million-byte cap and 25-second timeout, using an identifying research user agent. No production scraper, recurring schedule, website deployment, catalog pointer or legacy publisher ran. Original Gloo captures were preserved. Response bodies, request times, hashes and summaries are local ignored files under `artifacts/7c-sources/`; raw responses are not for the public backup or Pages package. No authentication challenge was bypassed.

One initial sandbox request failed locally with Windows socket permission error before reaching Gloo. The subsequent authorized network request is recorded separately; this local error is not a seller access block or a seller retry.

## Current outcomes

| Candidate | Observed access | Investigation outcome | Outstanding prerequisite |
| --- | --- | --- | --- |
| Gloo | Earlier `/laptops` listing HTTP 200; robots HTTP 404; linked terms HTTP 200 | Incomplete; sourcing conditions unresolved, further collection paused | Resolve product-listing/extraction restrictions before broader capture or qualification audit |
| TMT / Thunder Match | Homepage HTTP 200 after redirect to `www`; robots HTTP 403; linked terms HTTP 200 | Incomplete; homepage accessible, robots unavailable and sourcing conditions unresolved | Resolve robots/terms review before catalog capture or recurring collection |
| PC Image | Robots and gaming-laptop collection both HTTP 202 with an anti-robot JavaScript challenge | Documented access block; retry disposition pending | At most one later ordinary retry before cutoff, without bypass; terms and variant evidence remain unavailable |
| TechHypermart | Not attempted in this investigation | Deferred from current candidate list | Separate future investigation; it is not TMT |

None of these outcomes proves that no exact overlap exists. An accessible homepage or listing is not source qualification, and a terms concern is not reported as an HTTP block. At cutoff, unattempted work is **not attempted**, unfinished qualification is **incomplete**, and access-block outcomes retain the actual response evidence and retry disposition.

## Gloo population method and qualification hold

The preserved first request at **14:09:46–14:09:48 MYT** returned `https://www.gloo.com.my/laptops`, title `Laptops`, with two server-rendered `.product-layout` cards beneath `#category_listing`. The page states **Showing 1 to 2 of 2 (1 Pages)**. Both observed cards are present in the original HTML; a browser or infinite-scroll collector is not required to discover those two cards. Inline scripts offer separate filter AJAX behavior, but that endpoint was not invoked and is not established as a complete-catalog source.

The same navigation points to a different `https://www.gloo.com.my/laptop` category and consumer/commercial/2-in-1 children. Therefore the two-card `/laptops` population must not be treated as Gloo's whole laptop catalog or used to satisfy an all-records audit without a documented scope. Neither the alternate category nor a product detail page was fetched in this follow-up after the terms issue was identified. Pagination discovery and exact-variant completeness remain unverified.

At **17:11:55 MYT**, [robots.txt](https://www.gloo.com.my/robots.txt) returned a 404 HTML response, not usable crawler directives. At **17:12:09 MYT**, the linked [Terms of Use](https://www.gloo.com.my/terms-of-use) returned 200. Section **6.0 License and Website Access** excludes collecting/using product listings, descriptions and prices and using data-mining/robot extraction tools from its limited license. This fails the project's unresolved sourcing-condition gate; it is not a legal conclusion. Further catalog fetching and the planned 20-configuration audit are paused pending an accepted permission/source route. No seller contact was made.

For a reviewer after that prerequisite is resolved: confirm the canonical category and its population, discover pagination from actual links, collect exact product/variant evidence through a nonpublishing native adapter, then review at least 20 configurations or every configuration if fewer. Every field counted toward coverage requires individual recorded approval; the sampling rule does not approve unseen fields.

## TMT access and qualification hold

At **17:12:10 MYT**, `https://www.tmt.my/robots.txt` returned HTTP 403. One ordinary homepage request at **17:12:32 MYT** to [tmt.my](https://tmt.my/) redirected to `https://www.tmt.my/` and returned HTTP 200, title `Home | Thunder Match`. Thus this is not a site-wide verified access block. The homepage links Traditional, 2-in-1 and Gaming Laptop category queries under `/collections`, and `/products/` detail pages; their listings, pagination totals and exact selectable variants have not been inspected.

At **17:13:07 MYT**, the linked [TMT Full Terms & Conditions](https://www.tmt.my/pages/tmt-full-tnc) returned HTTP 200. The general website-use notice's prohibited-actions passage includes data-mining, robots and similar extraction tools. Record the relevant scope with the reviewer and resolve sourcing permission before automated collection; no catalog or product requests followed this discovery. Robots access remains unresolved rather than assumed permissive. No claim is made that the local TMT template's printed API message identifies a functioning API: that template currently returns an empty list.

Some homepage product URLs combine multiple model codes. A title or URL alone therefore cannot certify a single purchasable configuration. A future adapter must bind price, stock, specifications, image and destination to the selected variant; ambiguous grouped products cannot be accepted as exact overlap.

## PC Image access block and retry boundary

At **17:12:10 MYT**, [robots.txt](https://store.pcimage.com.my/robots.txt) returned HTTP 202 HTML with an anti-robot challenge. At **17:12:33 MYT**, the existing [gaming-laptop collection](https://store.pcimage.com.my/collection/gaming-laptop) returned the same challenge type and HTTP 202. HTTP 202 here does not constitute usable listing access. No challenge-solving, browser impersonation, alternate API probing or bypass was attempted. A later retry has not yet been used or scheduled; allow at most one ordinary retry before cutoff and record its outcome or explicit decision not to retry.

The existing scraper expects Next.js `productListingPagination` data and assumes 24 items per page. Neither assumption is validated against current accessible seller content. Population bounds, exact variants, terms and original-photo evidence remain unavailable. The older Phase 4.5 failure is historical context; the dated requests above are the new 7C access evidence.

## Evidence index and next closing tasks

| Evidence prefix under local `artifacts/7c-sources/` | Meaning |
| --- | --- |
| `gloo-initial-attempt.json` / `gloo-initial-response.html` | Preserved first listing request and body |
| `gloo-robots-20261021.json` | Local sandbox socket failure, no seller response |
| `gloo-robots-network-20261021.*`, `gloo-terms-20261021.*` | Authorized robots/terms captures |
| `tmt-robots-20261021.*`, `tmt-home-20261021.*`, `tmt-terms-20261021.*` | TMT access and source-condition evidence |
| `pcimage-robots-20261021.*`, `pcimage-listing-20261021.*` | Actual challenge responses |

All successful response captures have per-response SHA-256, exact requested/final URL, HTTP status, timestamp and truncation flag in their JSON sidecar. These are access records, not field-review receipts or production observations. No records have been handed to the coverage calculator.

Before the fixed cutoff: decide the permission route for Gloo/TMT or record it unresolved, finish PC Image's single-retry disposition, and record the actual investigation outcomes. Only if access and source-condition prerequisites clear should native extraction, exact-variant audit and human field review proceed. 7C-LIVE remains a later task after the 7B interface; it must record `live-validated` or `deferred: no real overlap` before 7F opens. This investigation does not close 7C-LIVE or the full source qualification phase.
