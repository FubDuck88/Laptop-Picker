# Laptop Picker: product direction and design overhaul plan

Date: 21 October 2026 (Malaysia)

Status: Phase 6R cutover is verified and daily publication is active; phase closure awaits the first successful scheduled run. The 7A preview is ready for review, 7C investigation has started, and 7B/7D–7F have not started. Historical Phase 6 completion remains unsubstantiated; older receipts do not count toward 7F.

## Purpose

Help Malaysian buyers find the cheapest laptop that meets their requirements, understand confusing specifications, and inspect evidence about a particular laptop before buying.

The problem behind the project is the effort and frustration of searching different vendors and manufacturers for the desired specifications at an affordable price. The experience should reduce that work and make compromises understandable.

Laptop Picker is a research and comparison service. Its initial release may contain one qualified seller or several sellers with no overlapping exact configurations. In those cases it helps compare different laptops while clearly disclosing coverage; it does not claim a validated best price for the same laptop across sellers. Buyers follow a link to the original seller to purchase. The initial scope uses ordinary outbound links, without checkout, accounts, or affiliate tracking. These are initial defaults, not permanent business-model decisions.

Inspiration: [The Beans Hub shop](https://www.thebeanshub.com/shop), particularly the catalog-plus-learning-library approach. The user identified its seller-referral model as inspiration. The independently observed reference is limited to catalog filters and a learning library. Its outbound purchase flow and affiliate arrangements were not verified. Use the product pattern as inspiration rather than copying its branding or layout.

## Audience and navigation

Design primarily for buyers who know their budget and intended use but are not confident interpreting CPU/GPU names. Keep detailed specifications accessible for experienced buyers.

There are two main destinations:

- **Find laptops:** search, requirements, seller prices, shortlist, comparison, and laptop details.
- **Research:** specification explanations, naming guides, sourced CPU/GPU performance and efficiency information, and secondary catalog insights.

Comparison belongs within Find laptops. Owner experiences belong with the specific laptop. Research primarily explains hardware and specifications.

## Find laptops

### Requirements and ordering

- Use one responsive experience across phones and desktops, replacing the separate device-specific experiences.
- Provide direct filters for RAM, storage, CPU, GPU, display, and seller, with advanced controls disclosed progressively.
- Use a two-handle price slider with editable minimum/maximum MYR fields. Start the minimum at RM0. Support keyboard operation and precise numeric entry.
- Treat selected specifications and the price maximum as strict requirements. Minimum RAM/storage controls mean “at least.” Multiple CPU/GPU selections mean “any of these.”
- Default to lowest qualifying public item price first, excluding shipping and conditional discounts. At equal price, confirmed in-stock offers precede unknown-stock offers, followed by a stable offer-ID tie-break. Do not silently substitute a supposedly equivalent CPU/GPU or infer performance from naming alone.
- Exclude records with unknown required specifications from qualifying matches. Offer a separate, optional view of possible matches with missing information.
- Include confirmed in-stock and unknown-stock offers with a persistent text label immediately beside the price and seller action, including in comparisons; hide confirmed out-of-stock offers by default.
- Preserve the existing stale/expired rules: stale after 48 hours and expired after seven days, with expired offers hidden by default.

### When nothing fits

Keep the ordinary filters simple. Do not add a mandatory “must have/prefer” decision to every control.

Offer **Explore options** when requested:

- Keep all specifications and show the cheapest exact match above budget, including the amount over budget.
- Let the buyer choose one requirement to relax and show actual offers and actual savings from that change.
- Identify every deviation from the original search. Do not blend alternatives into qualifying results or automatically relax filters.
- Present upgrade candidates separately and only by explicit request. Default results must meet the requirements out of the box. Upgrade candidates are deferred to phase 7E until upgrade evidence exists; phase 7B has no disabled upgrade-candidate control. Parts and installation price quotes and upgrade-inclusive totals are outside the initial scope because no cost source has been selected.

### Results and purchase handoff

Cards show the exact configuration, lowest qualifying checked price, seller, CPU/GPU, RAM/storage, stock status, last-checked time, and a brief ownership summary where evidence exists.

Use **Lowest checked item price** and disclose seller coverage. “Cheapest” refers to the public item prices among sellers and offers checked, not the entire market or delivered totals.

The purchase action reads **View at [seller]**. Its price, availability, photo, and original destination must refer to the same seller offer and exact variant. Public MYR prices exclude shipping and conditional discounts. Label the sort “Item price: low to high” and show “Shipping not included; check seller” near offer prices. Unknown shipping must never imply free shipping or a cheapest delivered total. A location-aware shipping quote and delivered-price ranking require a separate future data scope.

### Comparison and continuity

- Allow up to four shortlisted laptops, saved on the current device without an account.
- Show a persistent comparison tray and open comparison within Find laptops.
- On narrow screens, show two selected laptops at a time, with selectors for switching between saved choices.
- Offer **Show differences only**, while keeping unknown information explicit.
- Preserve filters and sorting in shareable URLs. Explicit URL settings take precedence over remembered device settings.
- Restore only the last search on normal return (named or multiple saved searches are out of scope), provide **Clear requirements**, and preserve search state when returning from details/comparison.

## Laptop details and ownership evidence

Bring together exact specifications, seller offers, actual observed price history, and an **Ownership & upgrades** section.

Ownership fields include replaceable versus soldered RAM, memory/storage slots, documented capacity limits, local warranty, and sourced repair information. Unsupported fields read **Not confirmed**.

Owner experiences should:

- Link to original forum, Reddit, or other owner discussions and show dates.
- Match the exact laptop model where possible; label family-level reports separately and avoid implying that all configurations share an issue.
- Distinguish individual anecdotes, recurring reports, and unresolved uncertainty.
- Include useful positives as well as complaints. Do not turn a few comments into a reliability rating or claim consensus without evidence.
- Avoid guarantees about future durability. Upgradeability, warranty coverage, and reported faults are evidence to inspect, not proof of trouble-free ownership.

Begin with a small manually reviewed set. Automated opinion collection is a later capability requiring validated model matching and sourcing rules.

## Research and scoring

### Specification education

Provide searchable CPU/GPU profiles that explain full model names, generations, suffixes, naming changes, and laptop versus desktop variants. Link relevant explanations directly from filters, specification labels, and comparison rows.

Explain what hardware differences mean for everyday work, gaming, study, and demanding creative work. Include RAM, storage, displays, and upgrade limitations rather than requiring users to interpret benchmark charts alone.

Keep broader catalog charts within Research under a secondary **Catalog snapshot** section, labeled with the actual seller count/names, observation period, and sample size. With one seller, use “ALL IT catalog snapshot”; do not describe the results as market-wide statistics.

### Benchmark evidence

- Use published measurements from other testers, with visible original sources, dates, test versions, and configuration context.
- Validate source access and reuse conditions before selecting a dataset or building collection tools.
- Distinguish hardware-level measurements from tests of an exact laptop. Record relevant power limits and laptop configuration where available; cooling and power settings affect results.
- Show performance and efficiency separately. Efficiency is not automatically a battery-life prediction.
- Compare compatible measurements. Do not blend different test versions or incompatible methodologies into a precise ranking.
- Show insufficient evidence when measurements are absent. Missing efficiency data must not become a zero or silently penalize a device.

The initial research release presents sourced results and explanations. A later internal scoring method may normalize compatible measurements and expose visible, adjustable weights. An overall score is deferred until its methodology, coverage, and treatment of missing data have been validated. Never invent scores from model names or present heuristic scores as measured performance.

## Visual and interaction direction

- Light-first appearance with an optional dark theme, tested independently.
- Readable typography, restrained color, clear price hierarchy, consistent product-photo areas, and one coherent SVG icon family.
- Shared semantic design tokens for color, typography, spacing, focus, elevation, and motion.
- Desktop filter sidebar; phone filter sheet with applied-filter visibility and clear result feedback.
- Progressive disclosure for technical details and provenance. Keep the core search controls and results prominent.
- Accessible labels, semantic accordions/dialogs, keyboard navigation, focus containment/restoration, Escape support, readable contrast, reduced motion, and zoom support.
- Meaningful loading, retry, empty-result, missing-photo, missing-specification, stale-data, and unavailable-research states.

Use the [UI/UX Pro Max skill](../.agents/skills/ui-ux-pro-max/SKILL.md) as a workflow and quality checklist. Generated styles are suggestions evaluated against this product brief; the agreed product requirements take precedence over generic dataset recommendations. Its initial generated design suggestions were generic promotional layouts, so they are not an approved visual specification. Phase 7A must establish the actual design system around the agreed shopping and research journeys.

## Implementation phases

Model and effort are recommendations for implementation sessions; they do not switch the chat settings automatically.

| Phase | Deliverable and completion gate | Data dependency | Recommended model | Effort |
| --- | --- | --- | --- | --- |
| 6R — Hosted verified-pipeline cutover | Deploy the verified pipeline with the existing desktop/mobile frontend; repair qualified-source GPU extraction and the manual launcher; remove unused executable/cache artifacts; implement **6R-GATE-ISOLATION**, including fixture fingerprint coverage. Record pipeline-only hosted evidence; complete only after **6R-SCHEDULED-FIRST** passes. Cutover unlocks 7B code; full 6R closure gates 7B release. Owned by pipeline/release work. | Reviewed existing Phase 4/5 implementation plus confirmed hosting configuration; see the hosted audit | GPT-6.1 Sol | high |
| 7A — Design foundation | Establish shared tokens and component specifications. Produce responsive designs for Find, details, comparison, and Research. Real-record designs expose only specification controls meeting the reviewed 50% threshold; below-threshold control demonstrations use labeled fixtures. Check hierarchy, accessibility, and both themes before implementing the full experience. | Verified local catalog; labeled synthetic states for unavailable data | GPT-6.1 Sol | high |
| 7B — Shopping experience | Complete the unified UI and deterministic acceptance tests, closing as **fixture-tested**. Show field coverage and actionable restored requirements. Review AMD/NVIDIA naming sources during this phase; omit links for unreviewed entries. Record live validation separately under 7C-LIVE. | **Code unlock: 6R-CUTOVER-PASSED / awaiting scheduled proof + approved 7A design. Release unlock: 6R complete, including 6R-SCHEDULED-FIRST and 6R-GATE-ISOLATION.** Verified releases, frozen fixtures and reviewed published glossary entries | GPT-6.1 Sol | high |
| 7C — Seller coverage | **7C-SOURCES** closes after the bounded qualification/overlap investigation. **7C-LIVE** runs after fixture-tested 7B and closes either **live-validated** with real overlap evidence or **deferred: no real overlap**, invoking the limited-coverage release policy. | Source investigation starts alongside 7A; only 7C-LIVE depends on the completed 7B UI | GPT-6.1 Sol | high |
| 7D — Specification research | Validate tester sources and reuse conditions. Publish naming guides and a small sourced benchmark dataset, with compatible comparisons, measurement context, and honest missing-data states. Overall weighted scoring remains gated by methodology validation. | Validated tester sources, compatible measurements, source/reuse review | GPT-6.1 Sol | high |
| 7E — Ownership evidence | Add model-specific upgrade, warranty, and owner-report records with source links, dates, explicit model matching, and distinctions between anecdotes and recurring reports. | Exact-model manufacturer/service/warranty evidence and reviewed owner links | GPT-6.1 Sol | high |
| 7F — Release validation | Verify accessibility, both themes, layouts, seller links, photo failures, stale data, unknown specs, and research provenance. Open a new gate identity using **6R-GATE-ISOLATION** and run a fresh seven-day window; assess hosted operation separately. | Completed integrated implementation; 7C-LIVE outcome recorded; scoped receipts and hosted deployment evidence | GPT-6.1 Sol | high |

Start seller qualification alongside 7A, before or concurrently with 7B. Synthetic multi-seller fixtures prove application logic independently of access to a second live source. A claim of live multi-seller comparison requires at least two qualified sources and a captured overlapping exact configuration; qualification of two non-overlapping catalogs is insufficient. After the bounded investigation, a one-seller or non-overlapping multi-seller interface may ship under the limited-coverage policy below, with live same-configuration comparison marked deferred rather than passed. Research and ownership data require separate sourced records associated with the appropriate hardware/model identities; do not repurpose seller observations as benchmark or owner-review evidence. Exact schemas, source choices, and score formulas must be specified in their respective phases after source feasibility research.

## Worked example and acceptance scenarios

The user's example search is approximately RM4,000+, an RTX 4060 Laptop GPU, a Ryzen 5 preference with no exact CPU selected, at least 16GB RAM and 512GB storage, for gaming/work/study. This is a product-design scenario, not an executable saved query. Any executable CPU filter must list the explicitly selected model identifiers; an empty CPU selection means unrestricted, not “suitable.” Ownership priorities are longevity, a confirmed upgrade path, and visibility into documented problems. The exact budget maximum remains a user input; RM4,500 was suggested during discussion but was not confirmed. Exclude RM4,500 entirely from design fixtures, example query values, and defaults. Test numerical boundaries using explicitly synthetic values independent of this personal example.

This example guides design testing without becoming a hardcoded preset or restricting the site's audience.

Acceptance scenarios:

- Exact matches are ordered by qualifying seller price and retain correct variant links.
- No matches leads to explicit over-budget or one-requirement compromise exploration.
- Unknown required specifications never pass strict filters.
- Unknown stock, out-of-stock offers, stale offers, and expired offers behave as stated.
- Seller filtering updates the displayed price and destination together.
- Phone and desktop comparison preserve selections and expose meaningful differences.
- Shared URLs, last-search restoration, browser back, and clear/reset behavior remain predictable.
- Missing/broken photos, long model names, large text, keyboard navigation, and narrow layouts remain usable.
- Benchmarks retain source and test context; absent measurements remain absent.
- Owner reports cannot silently attach to a different model or become an unsupported reliability claim.
- Research explains naming without claiming unsupported performance equivalence.

## Existing safeguards and release status

Preserve hash-checked verified releases, exact configuration/offer identity, conservative matching, explicit unknowns, separate system RAM and VRAM, original seller URLs, photo provenance, honest availability, and actual observed history.

At planning time, ALL IT is the only qualified live source. Wider seller coverage is planned, not already delivered. See [existing implementation phases](IMPLEMENTATION_PHASES.md) and [release gates](RELEASE_GATES.md) for recorded status.

Planning documentation does not change the implementation fingerprint. Changes to application code, styles, tests, or other fingerprinted implementation files start a fresh validation window. Previous receipts remain historical evidence and must not be counted toward a changed implementation. Local validation and hosted deployment/operation are separate gates.

## Review resolutions: baseline, dependencies, and acceptance

### 1. Baseline status and fingerprint lifecycle (question 1)

The available evidence does not confirm the statement that Phase 6 has finished for the local verified implementation:

- Local receipt ledger contains one successful Malaysia date, 20 October 2026. Its status records `local_seven_day_gate_passed: false` and hosted operation as not assessed.
- Active local release SHA-256: `116059d4de1016c9ceba960b43fa8d827a598bdcd8d17a75caef1ddc45620268`.
- Current implementation SHA-256, recalculated during this review: `7c93ab85245c8d5bbf4d82de779c16023d3fcba4a8475af13fdcc0968b0b9a47`.
- Public GitHub checks during this review returned 404 for `data/current.json` on the default branch, and the remote daily workflow differs from the local workflow. Successful older workflow runs therefore do not establish deployment of this implementation. These checks do not establish the contents of every possible deployment branch.
- The latest inspected [successful workflow run](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39364147431) used commit `9f16cdbbe8309243bc41ad14f4812aeab057673d`. That success alone is not the missing verified-release evidence.

Treat the named local release and implementation as the recorded pre-overhaul baseline, with Phase 6 still unverified as complete. If separate completion evidence exists, reconcile its commit, release hash, daily receipts, and hosted deployment before updating the status. Do not overwrite historical receipts.

6R and 7B changes start new implementation fingerprints. Any fingerprinted changes during 7A, 7C, 7D, or 7E do likewise; a phase label does not control the reset. Phase 7F is the new integrated release gate. A genuinely completed Phase 6 baseline would remain historical completion for its own implementation rather than being undone by the redesign. Documentation-only edits made in this review do not reset the fingerprint.

### 2. Actual catalog example and coverage (questions 2, 3, 10, 20)

The validated local snapshot contains 19 configurations/offers from ALL IT, all with unknown stock. The following are snapshot results, not freshly checked buying recommendations:

| Query against the recorded snapshot | Result |
| --- | --- |
| RTX 4060 + Ryzen 5 + at least 16GB RAM/512GB storage | Zero records, even before applying a budget |
| RTX 4060 + at least 16GB RAM/512GB storage, with CPU unrestricted | One record: MSI B13VF-3492MY, Intel Core i5-13420H, RM3,879, unknown stock |
| Same CPU-unrestricted query with an illustrative RM4,000 ceiling | Same one record |

The offer was observed at `2026-10-20T15:36:01.589289+00:00` (23:36 MYT). Normal freshness rules still apply when showing this snapshot later.

No exact Ryzen CPU model was selected by the user. “Suitable Ryzen 5” is an unresolved personal preference, not an executable performance threshold. The Intel result is a CPU-unrestricted diagnostic, not a claim that the user selected it or that it is equivalent. The design must make zero-result, one-result, and one-seller states first-class. Do not invent sellers or matching laptops to make production pages look populated.

### 3. Browser-test migration (question 4)

The 48 checks are the numbered entries in [the recorded browser report](audits/phase6-2026-10-20/browser.json). Preserve behavioral coverage rather than the numeric count or old selectors.

| Existing checks | Migration decision |
| --- | --- |
| 1–10, 12–18 | Port catalog loading, ascending price, screenshots, overflow, empty/reset behavior, budget filtering, details, and comparison to the unified page at phone and desktop widths. Preserve the small-catalog pagination behavior. |
| 11, 19 | Retire automatic device redirect and desktop-switch expectations. Replace with unified responsive behavior and a compatibility redirect from the legacy mobile URL that retains query/hash state. Keep `index.html` as the main entry. |
| 20–26 | Port directory, observed history, price statistics, screenshots and layout coverage to the relevant laptop-details/Research catalog-snapshot views. Preserve original receipt semantics. |
| 27–29 | Preserve system-RAM-versus-VRAM, unknown-RAM exclusion and integrated-Arc classification. Test strict filters directly; legacy gaming/Steam preset control names are not acceptance requirements. |
| 30–32 | Preserve seller-count filtering if exposed, inclusive 16GB+ matching, and two 8GB modules displaying as 16GB. Add seller-specific price/link consistency assertions using multi-seller fixtures. |
| 33–37 | Preserve large-catalog pagination, expired hide/reveal, actual history without filled gaps, explicit load failure with no legacy fallback, and verified retry. |
| 38–48 | Retain no-JavaScript-exception assertions for equivalent migrated scenarios. |

BUG-07, 08, 09, 11, 12 and 13 remain regression invariants. BUG-10's old desktop-override mechanism retires with device-specific rendering, replaced by no redirect loop and no lost navigation/search state. Add phone comparison, focus restoration, shared-URL precedence, last-search restoration, price-slider keyboard controls, both themes, and missing research data coverage. Historical passes do not certify the rewritten frontend.

### 4. Data-dependent screens and delivery boundaries (questions 6–9, 11)

7A uses real catalog data for the listing, offers and recorded price history. Benchmark charts, owner reports, warranty and upgrade layouts use isolated fixtures when reviewed evidence is absent. Every such preview must carry **Design preview — illustrative data, not validated** at the screen level and at the evidence section; synthetic external purchase actions must be disabled. Keep fixtures out of published catalog/research payloads. Production designs also demonstrate the real **Not confirmed** or **No reviewed evidence yet** state.

Pull a minimal sourced glossary into 7B: explain RAM versus VRAM, capacity, CPU/GPU naming basics, and why names do not establish equivalence. For manually written, cited definitions, check accuracy, applicability, source access and attribution; no separate dataset-reuse approval is required when no protected expression or assets are reproduced. Apply the fuller 7D access/reuse review if the work imports measurements, copies assets or tables, quotes beyond ordinary attribution, or automates collection. Its initial scope contains original explanations of definitions only, without imported benchmark measurements or performance rankings. General help links can ship after editorial/source review. Model-specific links appear only when their destination has reviewed content; no dead or placeholder profile links. Full naming profiles and benchmark charts remain in 7D. The source shortlist and publication gate are recorded below.

Move upgrade-candidate search to 7E, gated on exact-model upgrade evidence. Drop parts/installation quotes and upgrade-inclusive totals from the initial phases. No collector or source has been chosen to substantiate them.

Longevity is represented through confirmed upgrade options, warranty scope, service documentation, and dated model-specific owner reports. It is not a predicted lifespan or composite reliability score.

### 5. Empty results and search persistence (questions 12, 13)

Show the empty-state explanation and applied requirements first. Present two separate optional actions:

1. **Explore options:** retain known required specifications and show the cheapest over-budget exact match; alternatively, let the user relax one selected requirement and show the resulting differences. If no such records exist, say so.
2. **Check possible matches:** retain the original budget and all known requirements, but list records missing required information, with each missing field identified.

Do not combine missing evidence and relaxed requirements in the initial implementation. Either action leaves the original search intact until the user explicitly applies a change. “Saved search” means only last-search restoration plus shareable URLs; named and multiple saved searches are excluded.

### 6. Pricing, presentation, and scope (questions 5, 14–19)

- Replace the old **Later visual refinement** roadmap row with 7A–7F and link this plan.
- Shipping can reverse delivered-price rankings. Initial ranking remains public item price with a visible shipping-excluded label. Do not infer shipping from absence or add a schema field without an evidence source. Shipping-aware ranking is deferred.
- Keep catalog charts in Research under explicit seller coverage and date/sample labels, including the one-seller case.
- UI/UX Pro Max supplies the workflow and quality checklist; generated aesthetics remain proposals checked against the agreed brief.
- Cite Beans Hub only for the observed catalog and learning-library structure. Seller referral is this project's agreed behavior; affiliate tracking remains outside the initial scope.
- Retain model/effort columns because the user explicitly requested them for every phase. They are the same because each phase involves integration or evidence judgments; they are recommendations, not a claim that every subtask needs high effort. Add data dependencies alongside them.
- Put **Stock not confirmed — check seller** next to the price and seller action, not in a tooltip. Confirmed stock wins an equal-price tie; unknown stock may still be first when its item price is lower. Offer an explicit **Confirmed in stock only** filter.

## Follow-up decisions before 7A

### Hosted publication ownership and pre-7B gate

The [pinned hosted workflow audit](audits/HOSTED_PIPELINE_REVIEW_2026-10-21.md) compares remote commit `9f16cdbbe8309243bc41ad14f4812aeab057673d` with the local verified pipeline. The remote workflow can publish legacy files without the verified release builder, SHA-256 pointer, pre-publication checks, or atomic activation. Its runner entry point only combines stored CSVs; it does not invoke its defined scraper function. Its corresponding frontend reads preloaded JavaScript, JSON, and CSV without the verified reader.

**Phase 6R owns the fix. 7B code unlocks at 6R-CUTOVER-PASSED / awaiting scheduled proof, with approved 7A design; 7B release stays forbidden until full 6R closure.** 7A design and 7C source investigation may proceed alongside 6R. The existing local replacement is implementation material, not proof that the hosted defect is already fixed.

6R completion requires:

1. Deploy the reviewed collector, full validation dependencies, schemas, verified reader, and matching frontend together. Retire the old scheduled legacy publisher as an active production writer; retained legacy files must not remain a reader fallback.
2. Run the qualified-source collection and full release validation; permit publication only for a valid release. A source failure may publish a validated retained snapshot with original observation times, while reporting a failed/degraded collection. A validation failure must prevent publication of that candidate.
3. Publish only the validated immutable release and pointer. Record the application commit, workflow run, release SHA, and deployment identity; avoid broad `git add data/` publication.
4. Inspect the actual Pages configuration and provide an explicit deployment path. The local replacement currently commits/pushes data but has no explicit Pages deployment job. Do not assume its bot push or `[skip ci]` commit triggers a Pages rebuild. A dependent deployment job must package and deploy the validated revision, with appropriate Pages permissions and concurrency, and exclude diagnostics/test fixtures from public artifacts.
5. Verify the served pointer and release digest, actual hosted frontend loading, and rejection of a corrupt release through browser routing/test fixtures. Test failed-source retention and invalid-candidate refusal using controlled fixtures; do not corrupt production data. Retain evidence that invalid candidates do not reach the deployment job.
6. Complete GPU extraction repair, manual-launcher migration and artifact cleanup; re-audit affected ALL IT fields and frozen-release compatibility before cutover. Per the approved work order, implement **6R-GATE-ISOLATION** after verified cutover but before full 6R closure or any 7B release. Pre-ledger observations remain operational evidence only and cannot count toward 7F.
7. **6R-PACKAGE-EXCLUSIONS:** inspect the actual assembled Pages deployment package before upload, not merely the source ignore rules. Fail packaging if it contains `tests/`, frozen or captured test fixtures, diagnostics (including `data/catalog.v2.diagnostics.json`), `artifacts/`, raw audit/run logs, executable/cache artifacts or other files outside the approved runtime allowlist. Save its file inventory and verify that the deployed revision corresponds to that checked package; probe representative excluded paths to confirm they are not served. Source-repository backup is allowed, Pages publication of those files is not.
8. Follow the numbered collection-resumption and hosted-cutover sequence below. Deploy maintenance first, run an immediate verified collection while schedules remain paused, inspect the hosted candidate, activate it, and complete the canonical-URL smoke checks before enabling daily operation in **6R-CUTOVER-PASSED / awaiting scheduled proof** status; declare 6R complete only after **6R-SCHEDULED-FIRST** passes. Never backfill missed receipt dates.

6R is **pipeline-only validation using the current index.html/mobile.html pair**. Its browser checks establish that the hosted reader consumes the verified pipeline; they do not validate the later unified UI. Its daily receipts are operational evidence for 6R only, with zero carry-over into the 7F window or the earlier Phase 6 fingerprint. 7F starts on the first complete successful daily run after the final fingerprinted change across 6R and 7A–7E, including final test and workflow changes. Any further fingerprinted change restarts 7F. Preserve all earlier receipts as dated historical evidence.

### Real multi-seller acceptance

7B has separate statuses for **application behavior tested with fixtures** and **live multi-seller behavior validated**. The claims “seller filter updates price and destination together” and “lowest checked item price across sellers” remain unvalidated against live data until 7C provides overlapping exact configurations from at least two qualified sellers and runs the integrated checks through the 7B UI.

Capture each seller's original variant URL, public price, observation time, and exact hardware identity. Verify that choosing each seller changes the displayed price and destination together, and that the default offer is the minimum eligible observed item price. Do not fabricate different prices if both sellers happen to charge the same amount. A single overlapping configuration validates this captured case, not every possible source pairing. The 7B phase closes as fixture-tested independently. The named 7C-LIVE task owns subsequent real-data acceptance or the explicit no-overlap deferral described below.

### Minimal glossary source shortlist and publication gate

No glossary has been published. The following primary-source pages were opened during this review and are the citation shortlist, not blanket approvals for copying or collecting their content:

| Definition | Source | Review status |
| --- | --- | --- |
| System memory versus persistent storage | [Kingston: difference between memory and storage](https://www.kingston.com/en/blog/pc-performance/difference-between-memory-storage) | Page accessible; definition accuracy/applicability and attribution review pending |
| Dedicated video memory versus shared system memory | [Microsoft Learn: calculating graphics memory](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/calculating-graphics-memory) | Definition text accessible; definition accuracy/applicability and attribution review pending |
| Intel model names and suffixes | [Intel: processor names and numbers](https://www.intel.com/content/www/us/en/processors/processor-numbers.html), [Intel: processor suffixes](https://www.intel.com/content/www/us/en/support/articles/000058567/processors/intel-core-processors.html) | Page contents accessible; definition applicability by naming generation and attribution review pending |

AMD model-specific explanations and NVIDIA model-specific naming entries have no approved source in this glossary yet. **7B-GLOSSARY-SOURCES**, owned by 7B editorial/frontend work, reviews AMD Ryzen mobile naming and NVIDIA GeForce RTX Laptop GPU naming during 7B, rather than waiting for 7D. Prioritize the Ryzen/RTX terms used in the buying journey; distinguish laptop/desktop and generation-specific naming without inferring performance equivalence. Record exact manufacturer URLs and supported claims under the editorial gate below. This is scheduled review work, not a claim that those sources are already approved. **7B ships without a glossary link for any spec still lacking a reviewed source.** Display its verified specification as plain text. Missing explanations do not block the rest of 7B. Do not treat search snippets, blocked pages, or an unread oversized specification table as reviewed evidence.

Each published definition needs an exact source URL, title/publisher, access/review date, supported claims, applicability limits, and accuracy/attribution review. Write a concise original explanation in our own words, without importing benchmark measurements or reproducing charts, images, tables, or source prose. This narrow editorial check is sufficient for the initial glossary; it is not the full dataset-reuse gate. If the proposed use expands to copied material, collected datasets or automated access, apply the fuller 7D access/reuse review to that work before publication. Entries with unresolved editorial review remain provisional in isolated design previews and absent from production; omit their links without holding the rest of 7B open.

### Shipping scope, explicitly

Neither an optional per-offer shipping amount nor a persisted `shipping_unknown` field has been adopted. Every initial offer has the same presentation state: **Shipping not included; check seller**. There is no postcode-aware collection, delivery-cost evidence source, or validated shipping contract in this scope, so a per-offer boolean would imply a distinction we cannot support.

The note is sufficient only to explain an **item-price comparison**. It cannot establish the cheapest delivered purchase once shipping differs between sellers. Use **Lowest checked item price** and **Item price: low to high** consistently in cards, details, comparisons, and alternatives. Display the shipping note beside each offer and avoid claims about final totals. Delivered-price ranking remains a separate future capability with location, eligibility, cost, source, and freshness evidence requirements.

### Where the seven remaining wording questions are settled

| Question | Decision and location |
| --- | --- |
| Exact Ryzen models | **Worked example** and **Actual catalog example and coverage**: none selected. Remove “suitable” from executable behavior; only explicit models constrain a CPU filter. |
| Longevity | **Laptop details and ownership evidence** and **Data-dependent screens**: documented upgrade options, warranty, service information, and dated model-specific reports; unknowns stay explicit. |
| Missing-information matches versus Explore options | **Empty results and search persistence**: empty-state explanation first, Explore options first action, Check possible matches second action; separate modes that cannot combine in the initial implementation. |
| Catalog charts | **Specification education**: Research > Catalog snapshot, with seller names/count, dates, and sample size. |
| UI/UX Pro Max | **Visual and interaction direction**: workflow and quality checklist; generated style suggestions are evaluated against the approved product requirements. |
| Beans Hub | **Purpose**: only catalog filters and the learning library were independently observed. Outbound buying/affiliate behavior was not verified. |
| RM4,500 | **Worked example**: excluded from defaults, fixtures, and example query values; no exact maximum was confirmed. |

## Final sequencing and acceptance clarifications

### 7B closure and the named 7C closing task

The dependency order is `6R-CUTOVER-PASSED + approved 7A -> 7B code / fixture-tested -> 7C-LIVE`; a 7B release separately requires full 6R closure. Separately, `7C-SOURCES` starts alongside 7A and can finish before the UI exists. There is no dependency from 7B completion back to 7C-LIVE.

- **7B fixture-tested:** the implemented UI passes deterministic unit/browser checks, including synthetic overlapping-seller price/destination updates and lowest eligible item-price selection. This status closes 7B.
- **7C-SOURCES:** report qualification outcomes and real exact-configuration overlap for each attempted source.
- **7C-LIVE:** after 7B exists, run its seller-selection and lowest-item-price checks against captured overlapping real offers from at least two qualified sources. Close as **live-validated** if evidence passes. If the bounded source search yields no overlap, close the task as **deferred: no real overlap**, release only the supported limited-coverage behavior, and retain the unvalidated capability explicitly in the backlog. A failure with actual overlap is a defect to fix, not a no-overlap exception.

This separation does not equate synthetic and live results. **7C-LIVE must record exactly one closing outcome, live-validated or deferred: no real overlap, before 7F opens.** Pending, failed, or incomplete live checks cannot satisfy this prerequisite. Fix any defect found with actual overlap before closing live-validated. 7F must report which coverage mode was validated.

### Bounded no-overlap policy

Investigate three additional seller candidates in order: **Gloo, TMT (Thunder Match Technology, tmt.my), PC Image**, alongside the existing qualified ALL IT source. TMT and **TechHypermart (techhypermart.com)** are different sources with different adapters; **TechHypermart is deferred to a later seller-expansion scope, not permanently dropped.** It is not in this initial three-source scope. The older Phase 4.5 photo report's PC Image/TechHypermart pairing records that historical investigation, not an alias for TMT. The threshold is three documented qualification investigations, not a promise that three sellers will qualify. For an accessible source, audit 20 accepted configurations or all if fewer, and check all accepted configurations in its bounded collected catalog for exact overlap. Record acquisition scope/pagination bounds, audit results, and overlap counts. For a blocked source, record the response and permit at most one later retry during the investigation; do not substitute access bypasses for qualification. **Documented as blocked is a completed investigation outcome**, including for PC Image, but is never source qualification or evidence of no market overlap. Record an actual dated 7C attempt, attempted URL/method, blocking response and retry disposition. The old Phase 4.5 block alone does not count as a new investigation; an unattempted source at cutoff remains unattempted.

The planned investigation start date is **21 October 2026 MYT, inclusive day one**; day five is **25 October 2026**. The first attempt started **21 October 2026 at 14:09:46 MYT**, with a bounded Gloo listing request; see the manual investigation record below. Qualification remains incomplete. Stop when all three outcomes are documented, or at **25 October 2026, 23:59 MYT**, whichever occurs first. This fixed window replaces the earlier floating first-attempt wording; **a delayed first attempt does not move the deadline: it still ends 25 October at 23:59 MYT**, even if less investigation time remains. On cutoff, record unattempted/incomplete/blocked sources explicitly. This is a project scope limit, not evidence that no overlap exists across the market. Do not reset the deadline or add substitute sellers to prolong the initial gate. Further expansion is a separate follow-up scope.

At the stop point:

- If overlap exists, 7C-LIVE uses that evidence after 7B closes.
- If only ALL IT remains qualified, release a **single-seller catalog: ALL IT** with laptop-to-laptop comparisons. Do not present a per-laptop multi-seller savings claim or a seller-switch control with one option.
- If several sellers qualify but have no exact overlap, release a **catalog from N checked sellers** with seller filters and different-laptop comparisons. Each configuration shows its actual seller and **Checked item price**. Do not call it a validated best price for that configuration across sellers.
- In both no-overlap cases, the Purpose remains helping users find affordable qualifying laptops and research specifications, with the explicit limited-coverage statement added there. Same-configuration price competition stays unvalidated. Core safety and publication gates still apply.

### Confirmed-stock filter with no stock evidence

Show **Confirmed in stock only** disabled with the explanation **No confirmed-stock offers in this catalog** when the base non-expired eligible catalog contains no confirmed-stock offers. Do not base enablement on the user's other filters, which could temporarily eliminate every result. Enable it when a current qualified offer has confirmed stock.

If a shared URL or remembered search already has the filter selected, honor it and show **No results because Confirmed in stock only is selected; no current offers have confirmed stock.** Keep a removable selected requirement even while adding this filter is disabled. **Explore options** offers **Include offers with unknown stock** as an explicit single-requirement relaxation; apply it only when the buyer chooses it, retaining every other requirement and the unknown-stock labels. It may still return zero if other requirements conflict. Do not silently clear the requirement or trap a checked disabled control. Test normal-disabled, restored-selected and explicit-relaxation states. All 19 current snapshot offers have unknown stock.

### Frozen acceptance data and separate freshness tests

The zero-result/one-result regression scenarios use an immutable fixture copied from the named 20 October verified release, through the same validated release reader, with the browser/test clock fixed at **2026-10-20T16:00:00Z** (21 October 00:00 MYT). Keep original observation timestamps and the source-release hash in fixture provenance. These deterministic tests make no live vendor queries and do not rewrite observations to today's date.

Recorded files now live in **`tests/fixtures/releases/phase6-2026-10-20/`**: `current.json`, `releases/<sha256>.json`, `clock.json`, `manifest.json`, `catalog-v2.schema.json`, and `README.md`. The release SHA-256 is **`116059d4de1016c9ceba960b43fa8d827a598bdcd8d17a75caef1ddc45620268`**; release envelope version **1**, catalog schema version **2**. The manifest records the schema and clock hashes, source implementation identity, counts and expected configuration IDs. The payload and pointer are exact local-release copies; they do not depend on public `main` having a `data/current.json` endpoint. A local commit does not make that remote endpoint exist.

Keep these bytes immutable. A later 6R/7C schema or reader change must preserve a tested version-1/schema-2 read path or supply a tested compatibility adapter outside this fixture folder; introduce separately versioned fixtures for new formats. Wire the frozen clock into the unified browser suite in 7B. Exclude fixtures from production deployment, and include their test-input bytes in the implementation fingerprint under **6R-GATE-ISOLATION**.

The fixture-local `.gitattributes` disables line-ending conversion, preserving the recorded hashes on Windows and Unix checkouts. Verify staged Git blob bytes as well as working-copy hashes before committing this fixture.

**Pre-repair versus post-repair fixtures:** the committed 20 October fixture describes the pre-6R extraction, including missing GPU fields and its historical 19 accepted configurations. Its counts, identities and zero/one-result expectations are historical regression assertions, not promises about repaired or live data. 6R must capture a separate post-repair verified release fixture after extraction repair and re-audit, with its own dated path, release hash, schema version, fixed clock and reviewed expected results. Record accepted/rejected counts and identity changes with reasons; do not assume 19 configurations survive unchanged. Preserve both fixtures and test their intended compatibility. Include the new fixture in the fingerprint before starting 7F.

The historical Ryzen-family zero-match diagnostic is not a default executable CPU selection. For deterministic UI zero-result coverage, use explicit test-only filters such as RTX 4060 plus at least 32GB RAM against the frozen snapshot; the one-result case uses RTX 4060, at least 16GB RAM/512GB storage, CPU unrestricted, and a test ceiling of RM4,000. Label those test inputs as test cases, not confirmed personal preferences.

Test freshness separately with an injected clock immediately before, at, and after the existing 48-hour and seven-day boundaries, preserving the implementation's documented boundary semantics. The MSI offer reaches 48 hours at **22 October 2026, 23:36:01.589289 MYT** and seven days at **27 October 2026, 23:36:01.589289 MYT**. Actual operational validation runs retain the real clock and report current availability/freshness rather than expecting a permanent result count of one.

### Possible-match coverage from the snapshot

A check of all 19 configurations in the named release found:

| Field | Missing/unknown records |
| --- | --- |
| CPU model | 0 / 19 |
| GPU model | 0 / 19 |
| Installed RAM capacity | 0 / 19 |
| Storage capacity | 0 / 19 |
| GPU kind (integrated/discrete) | 19 / 19 |
| VRAM capacity | 19 / 19 |
| Display refresh rate | 15 / 19 |

These are field-population counts, not independent certifications of normalized hardware values. For the worked example's CPU/GPU-model, RAM and storage requirements, **Check possible matches has no real missing-field case** and is tested using explicitly synthetic missing-field fixtures. Real missing advanced fields can support additional cases only when that field is actually selected as a requirement; do not claim that all 19 are possible matches for the user's original query. Known conflicting fields still exclude a record from possible matches.

### 6R artifact cleanup and receipt scope

`LaptopScraper.exe` is a tracked legacy desktop artifact, approximately 28 MB, not part of either inspected production workflow. `LaptopScraper.spec` points to `scrape_and_compile.py`, not the verified daily runner. There is no verified source-to-binary attestation in the current evidence; do not execute or endorse it as the production collector.

During 6R remove the tracked `LaptopScraper.exe`, its obsolete packaging specification, and all tracked `__pycache__`/`.pyc` files (12 cache files found in this review). Remove cache files by explicit in-workspace paths; the cleanup does not require deleting unrelated user files or rewriting Git history. Existing ignore rules already cover executable, spec, cache, build and dist outputs; ignoring a tracked file does not remove it from the repository. Verify the resulting tracked-file list and exclude such artifacts from the allowlisted Pages package. This is a 6R implementation task, not a claim that cleanup happened during this documentation review.

6R receipts establish operation of the verified publication pipeline with the current UI pair only. Keep them as operational evidence under their own implementation/deployment identity. They contribute **zero days to 7F**, even if an unchanged fingerprint would otherwise allow the generic counter to include an earlier receipt. At 7F start, record a new gate-start timestamp and fingerprint and use a fresh ledger or explicitly filter receipts to that gate; do not modify receipt timestamps. Any acceptance-test changes required to set up the gate must precede that start.

The 7F window starts only after the last fingerprinted change across 7A–7E (and prerequisite 6R), using the finished integrated implementation. A later fingerprinted fix resets the window. Daily catalog observations alone do not reset it. Until this gate-scoping support is implemented, the generic Phase 6 counter must not be treated as proof of 7F completion.

### GPU extraction gap and filter availability — 6R / 7B

Inspection of the recorded release and native adapter confirms an **extraction gap**, not evidence that all 19 seller pages lack GPU type or VRAM. `source_adapters.py` maps the bounded Graphics text to `gpu_model` only; `catalog_v2.py` defaults `gpu_kind` to `unknown` and `vram_gb` to null. `source_normalization.py` keeps the model name but does not populate those separate fields. Saved seller evidence already contains four explicit VRAM capacities: 8GB GDDR7 for HP 15-GA0066TX, 15-GA0264TX and DJ6P0PA, and 6GB for HP DT7T9PA. Two other records explicitly say Integrated Intel Graphics (Lenovo 83RR00RAMJ and HP E21QCPA). These are extraction candidates to audit, not a claim that every omitted field can be recovered. This review inspected saved bounded seller evidence; it did not exhaustively re-check every live product page.

**6R-GPU-EXTRACTION**, owned by qualified-source pipeline work, must populate independently evidenced GPU kind and VRAM with field-level provenance, retaining unknown when ambiguous. Separate system RAM, dedicated VRAM and shared memory. Do not classify by a model-name prefix or invent a capacity from a typical specification. Re-audit the affected ALL IT configurations and test explicit capacities, integrated/shared memory, ambiguous text and absent values. 7C applies the same contract to new adapters. Do not loosen exact-configuration matching merely to manufacture seller overlap; missing GPU/display identity can still prevent a merge.

The Phase 5 integrated-Arc and RAM/VRAM checks used constructed records to test frontend behavior. They did not establish native collector coverage. The **RTX 4060 GPU-model filter works independently**: verified rows expose `gpu_model` as graphics, and its model filter matches that field without requiring known GPU kind or VRAM. At the frozen clock, RTX 4060 with at least 16GB RAM, 512GB storage and a test-only RM4,000 ceiling returns the MSI B13VF-3492MY at RM3,879; raising the minimum RAM to 32GB returns zero. This does not establish CPU equivalence or confirm an exact Ryzen selection.

7B applies the **single 50% reviewed-coverage rule** below to VRAM and GPU type as well as every other specification filter. A few repaired records do not automatically enable a control. Four VRAM values or two integrated descriptions are evidence candidates, not a post-repair coverage forecast; determine actual reviewed coverage after the repair and re-audit. A restored unsupported requirement remains visible and removable even when adding that filter is hidden.

### One coverage rule for specification filters — 7B

**Show a specification filter only when at least 50% of the base catalog has a reviewed, usable value for that field** (`known_count >= ceil(configuration_count / 2)`, with a non-empty catalog). Apply the same rule to refresh rate, VRAM, GPU type, CPU/GPU model, RAM, storage and future specification fields. This is an initial product threshold, not a statistical guarantee: it prevents a control excluding most of the catalog solely because its values are unknown. Count unique configurations with at least one non-expired eligible offer before other user filters, not offers or the current result count. Count only reviewed values usable by that control; unknown and not-applicable values are not invented numeric values. Recompute on catalog refresh. Availability has its separate confirmed-stock rule; price and seller are offer fields, not sparse specification filters.

Every visible specification control shows **Known for X of Y laptops; Z unknown or unavailable values excluded when filtering**. Below 50%, hide the control for adding a new requirement, while a noninteractive Data coverage summary still explains the missing field and its count. In the frozen 19-configuration catalog the threshold is **10 reviewed values**: refresh rate at 4/19 is hidden, just like VRAM or GPU type below 10/19 after repair. This supersedes the earlier visible-refresh and zero-only GPU rules.

If a saved/shared search already requires a hidden field, keep its selected requirement chip, coverage count and remove action visible. Honor the strict requirement, exclude unknowns, and explain limited coverage in an empty state. Explore options can offer an explicit one-requirement relaxation; never silently clear it. Crossing below the threshold after a refresh must not erase an existing selection. Test 9/19 hidden versus 10/19 shown, an empty base catalog, refreshed counts and restored selections.

The four populated values are 144Hz. Some saved display evidence says “up to” a refresh rate; the normalizer deliberately refuses to turn such a maximum into a confirmed exact configuration value. The other missing values cannot be declared absent from all live seller pages on this evidence alone. 6R may correct proven extraction omissions after audit, but must not fill unknowns just to improve coverage. Coverage labels always derive from the loaded release, not hard-coded counts.

### Manual launcher and scheduled routine audit — 6R

| Entry point inspected | Actual invocation | 6R action |
| --- | --- | --- |
| `ScrapeLaptops.bat` | Changes to the repository directory, then runs `python scrape_and_compile.py`; no executable invocation | Preserve this manual entry point but migrate it to the verified workflow |
| `scrape_and_compile.py` | Calls `run_all.run_scrapers()` and `run_all.combine_all_csvs()`, catches errors, then opens `index.html` using `file://` | Replace the legacy collection/combination path with `python -B tools/run_daily.py --sources allit` followed by `python -B tools/run_daily.py --validate`; propagate failures and remove the incompatible automatic `file://` preview |
| Local daily automation, Laptop Picker seven-day validation | Calls `python -B tools/run_phase6.py --if-needed`, which invokes the verified daily runner and validation directly | Verify this path still works after cleanup; it does not depend on the batch file, executable or packaging spec |

The automation was **PAUSED** when inspected on 21 October; this review does not resume it. Neither routine invokes `LaptopScraper.exe`. Its packaging spec builds the old Python launcher, so remove the executable/spec only alongside the manual-launcher migration and a launch-path check. Keep this work in 6R; no launcher or executable was changed during the planning review.

### 6R-GATE-ISOLATION and 7C-LIVE fingerprint policy

**Owner: 6R pipeline/release work. Deliverable: 6R-GATE-ISOLATION.** Implement an explicit gate identity and start timestamp with a fresh gate-specific ledger, and reject receipts from other gates, before the gate start, or for another implementation fingerprint. Do not scan the old aggregate ledger as the 7F input. Tests must prove that the historical Phase 6 day-one receipt and 6R operational receipts cannot increment 7F, even if their fingerprints happen to match. Preserve original receipts and timestamps. The current generic fingerprint counter does not enforce this separation.

As part of this deliverable, make the implementation digest cover nested test inputs, including the frozen release payload, manifest, schema and fixed clock; it currently includes only top-level Python/CJS tests, not nested fixture JSON. Include the maintained manual-launcher entry point as an implementation input too. Prove a change to any acceptance input changes the digest. Keep generated operational reports and daily live catalog observations outside that digest, so an ordinary observation does not itself reset the window. Do not exclude test inputs under the guise of evidence.

**Owner: 7F release validation.** After 6R and the integrated 7A–7E work are complete, including a recorded 7C-LIVE pass or permitted no-overlap deferral, open a new 7F gate with the final fingerprint and start timestamp. The first complete successful run at or after that start is day one; 6R contributes zero days. Any further fingerprinted implementation or acceptance-input change requires a new gate identity, fresh window and seven new qualifying daily runs.

Store generated 7C-LIVE run reports/screenshots under ignored `artifacts/7c-live/`, outside the implementation digest, with the tested implementation and release hashes. However, any captured offer data promoted into regression fixtures is a fingerprinted test input. A UI fix, parser change, or new/edited captured fixture therefore resets an already-started 7F window. **Complete 7C-LIVE and record live-validated or deferred: no real overlap before opening 7F.** A later follow-up defect or promoted fixture still restarts an open window; moving evidence files cannot conceal implementation changes.


### Collection resumption and interim hosted behavior — 6R

**Collection before cutover; schedules after cutover checks; phase completion after scheduled proof.** The immediate collection and candidate deployment are prerequisites, not evidence that 6R is already complete. Keep recurring publication paused through preparation and the public smoke checks. Then enable the schedules in **6R-CUTOVER-PASSED / awaiting scheduled proof** status. This supersedes earlier shorthand saying schedules resume only after the whole phase completes.

1. **Deploy maintenance first.** Retire or disable the legacy scheduled production writer and deploy a small maintenance page at the canonical public entry points saying **Catalog refresh in progress. Current prices are unavailable; please check sellers directly**, with no catalog price cards. Confirm it is served before proceeding. Before this deployment, the public site remains the legacy implementation described in the hosted audit; this plan does not itself change that state.

2. **Collect and validate while maintenance remains live.** After the collector, launcher, extraction repair and compatibility work is ready, manually run one immediate qualified-source collection and full release validation with recurring schedules still paused. Record the actual collection outcome, original observation times and release SHA-256. A failed source may produce a validated retained snapshot only under the existing retention rules; record the collection as failed/degraded. An invalid candidate cannot proceed to deployment. Require an eligible validated release for this cutover.

3. **Publish an inspectable hosted candidate.** Package the matching current `index.html`/`mobile.html` frontend, verified reader, schemas, validated immutable release and pointer through the explicit deployment job. Apply **6R-PACKAGE-EXCLUSIONS** to the assembled package before upload. Deploy the combined maintenance-plus-candidate artifact at the same Pages site: the candidate lives under `candidate/<deployment-id>/`, while maintenance remains at the public entry points. Candidate requests use only that subpath's `data/current.json`; see the artifact topology below. Record the application commit, workflow run, release SHA-256, package identity and candidate deployment identity. Do not assume a bot push triggers Pages deployment.

4. **Pass candidate checks before activation.** At the candidate URL, verify the served pointer, hash the actual release response bytes against the expected SHA-256, and confirm both frontend entry points load that release through the verified reader. Check asset and data URL resolution, freshness/expiry behavior and representative excluded paths. Use controlled browser routing or isolated fixtures for corrupt-release rejection, failed-source retention and invalid-candidate refusal; never corrupt production data or publish test fixtures. Retain evidence that invalid candidates cannot reach deployment. Candidate-path checks are pre-cutover evidence, not proof that canonical URLs already work.

5. **Activate the checked candidate, then check canonical URLs.** Deploy the prebuilt, independently checked **public-P** archive in place of **candidate-C**, recording the activation deployment identity and public-P digest. These are distinct whole-site packages containing the same validated release payload. Validate public-P at the intended base path before activation. If any package bytes change after checking, assign a new artifact identity and repeat those checks; do not rebuild during promotion or silently change the candidate pointer. Immediately after activation, verify the canonical public entry points, served pointer, release digest, matching frontend loading, expiry behavior and excluded paths. After these checks and the recovery/notification drills pass, record **6R-CUTOVER-PASSED / awaiting scheduled proof**. This is permission to enable recurring publication, not full phase completion.

6. **Enable daily operation after cutover checks, then prove the first scheduled run.** Enable the verified hosted daily workflow at **08:00 MYT**. Resume the local app follow-up as a read-only scheduled-proof observer; manual local collection uses the scoped operational runner. The local observer cannot collect, commit, push or deploy. The hosted workflow is the authoritative unattended collector; the local observer does not refresh GitHub Pages. Record both schedule states and the immediate hosted run/deployment. The first actual 08:00 MYT hosted schedule event must pass **6R-SCHEDULED-FIRST** before 6R is complete; a manual dispatch cannot substitute. Never fabricate freshness or backfill receipts. No 6R run counts toward 7F.

**Initial-cutover failure policy:** before switching, maintenance stays the default on failure. After a failed switch, the automated recovery jobs below redeploy the stored maintenance artifact and leave publication inhibited. After a successful cutover, a failed scheduled update instead retains or restores the last verified public artifact. Neither case restores the legacy frontend, writer or data fallback. Recovery is an implementation requirement, not a tested capability today.

After verified cutover, show actual observation times and stale labels after 48 hours; hide offers older than seven days by default. If no eligible offers remain, show **No current offers available. The last successful collection was [actual timestamp]. Please check back later**. Preserve access to general research and permit past prices only in an explicitly dated historical view if one exists. Do not load frozen test fixtures, remove expiry limits, or silently fall back to legacy data to fill the page. The saved MSI observation becomes stale on 22 October and expires on 27 October at the timestamps above; all offers age from their own observations. A data-unavailable empty state does not imply that the buyer's specifications are impossible.


### 6R-CANDIDATE-HOSTING — one Pages site, separate data roots

Use **a subpath of the same repository's Pages site**, not a separate branch as a second site and not a built-in preview service. Let `SITE` be the actual Pages base URL recorded by configuration, including the repository prefix when present. Build three named deployable archives:

| Archive | Default public entry points | Candidate / pointer placement |
| --- | --- | --- |
| `maintenance-M` | Known-good maintenance HTML | No public catalog pointer; no candidate |
| `candidate-C` | Same maintenance HTML | `SITE/candidate/<deployment-id>/index.html` and `mobile.html`; pointer at `SITE/candidate/<deployment-id>/data/current.json`, with immutable releases beneath that same data directory |
| `public-P` | Verified current desktop/mobile frontend | Pointer at `SITE/data/current.json`; candidate subtree absent |

6R must make asset and data URLs base-relative and test both roots. During candidate verification, intercept/inspect requests and fail if the candidate reads `SITE/data/current.json` or escapes its own data root. A direct request for the public pointer during initial maintenance must fail rather than expose a legacy pointer. The switch is an **Actions Pages deployment of public-P replacing the currently served candidate-C archive**, not a rename or a pointer edit inside the candidate. Both candidate and public archives are built and hashed before deployment; their release payload bytes must have the same recorded SHA-256. Record their distinct package digests and deployment IDs. Check public-P locally at its intended base path before activation, then verify the real public URLs after deployment.

Run **6R-PACKAGE-EXCLUSIONS independently on maintenance-M, candidate-C and public-P**, inspecting the full assembled tree, not just the candidate directory. Candidate-C permits only maintenance assets and its production-runtime candidate subtree; public-P permits only public runtime assets and the validated release/pointer. Neither permits tests, diagnostics, raw captures or audit logs. A passing candidate manifest never substitutes for a passing public manifest. Keep manifests and archives as deployment evidence outside the served package.

Every candidate HTML page, including error pages, has `<meta name="robots" content="noindex,nofollow">`; remove candidate URLs from navigation and sitemaps, and remove the subtree on activation. Do not block these HTML pages in robots.txt, since crawlers must read the noindex directive. This is search-exclusion intent for compliant crawlers, **not access control or an absolute guarantee against every indexer**; the candidate and its seller-data JSON remain publicly reachable while deployed. If a private preview is required, this same-site design is insufficient and must change before deployment. Verify the tags and absence of discovery links in the candidate checks. See [Google's noindex documentation](https://developers.google.com/search/docs/crawling-indexing/block-indexing).

This topology uses [GitHub's custom Pages workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) and the explicit artifact selection supported by [actions/deploy-pages](https://github.com/actions/deploy-pages). It does not rely on a preview feature or a bot commit automatically redeploying the site.

### 6R-AUTOMATED-RECOVERY — stored artifact and controlled failure

**Owner: 6R pipeline/release implementation. Status: not implemented or tested yet.** Build maintenance-M once, validate its file inventory and browser rendering, and store the exact Pages archive plus SHA-256 and per-file manifest as a versioned GitHub Release asset. Record the immutable source revision, release/asset ID and digest in the deployment ledger. Download and verify that stored archive before any switch; rollback re-uploads/deploys those saved bytes without rebuilding HTML, dependencies or the archive. Retain it durably beyond ordinary expiring workflow artifacts. Missing or mismatched maintenance bytes block initial cutover. Once public-P has passed checks, retain its exact archive in the same way as the last verified public recovery target.

The workflow has named `verify-public` and `restore-known-good` jobs. `verify-public` detects non-success HTTP responses or timeout at expected public URLs; malformed/wrong pointers; release hash/schema mismatch; wrong deployment marker; missing critical JS/CSS; frontend exceptions or failure to render the release-backed catalog/valid empty state; incorrect freshness behavior; and served excluded paths. Ordinary missing vendor photos use the established fallback and do not alone trigger rollback. Retry transient fetch failures within a bounded five-minute verification period; persistent failure or an integrity mismatch fails the check. Declare success only after this job passes.

`restore-known-good` runs automatically after a failed activation/check using failure-safe job conditions, without awaiting a person. Initial cutover restores maintenance-M; a later scheduled update restores the last verified public-P. A separate `workflow_run` recovery workflow handles failed, timed-out or cancelled publication runs whose post-switch checks did not pass. Serialize deploy and recovery through one concurrency group with `cancel-in-progress: false`; compare the failed run's deployment identity with the current identity before restoring, so an old failure cannot overwrite a newer verified release. Use trusted workflow code and recorded artifact identities, not commands from downloaded reports. Verify the restored site's marker and expected content, record the recovery outcome, inhibit further publication after a switch failure, and send the incident notification below.

**Required before first public activation:** a controlled hosted recovery drill deploys candidate-C with maintenance still at the public root, injects a failure result into the same verification/recovery path, and proves automatic redeployment of stored maintenance-M, digest equality, restored URLs and owner notification. Add controlled checks for HTTP failure, release-hash mismatch and frontend-load failure without corrupting production seller data; test cancellation/timeout recovery and stale-run guards. Keep run/deployment IDs and results. No drill has run during this planning review. Recovery cannot be guaranteed during a GitHub Actions/Pages outage; failed recovery is an incident, not permission to claim maintenance was restored.

### 6R-SCHEDULED-FIRST — phase closure and failure notification

**6R is complete only after the first successful unattended hosted run triggered by the 08:00 MYT schedule**, after cutover. Until then its status is **6R-CUTOVER-PASSED / awaiting scheduled proof**. If that first attempt fails, retain its failure evidence and keep 6R open until a later genuine scheduled attempt passes. A manual repair/dispatch may restore service but cannot replace the scheduled checkpoint. Record the nominal scheduled date, actual start/finish, `event_name=schedule`, workflow/source commit, source outcomes, release digest, served deployment identity, public browser checks, notification/drill evidence and pass/fail result. An identical price/catalog may still pass if it contains genuine new observations and all checks succeed; never manufacture a changed price.

For subsequent candidate staging, keep the last verified public site at the root of the combined candidate artifact instead of maintenance. A collection, eligibility, validation or packaging failure must leave the last verified public release/pointer unchanged, report **degraded**, and fail the run. Do not publish a newly timestamped retained snapshot to make this checkpoint pass. If a deployed update fails public checks, automatically restore the stored last verified public artifact. Original observation timestamps continue to age normally; the site retains stale/expired behavior. A controlled initial-cutover failure uses maintenance because no verified public baseline exists yet.

**Notification recipient: repository owner FubDuck88. Channel: GitHub notification inbox through an assigned/mentioned operational incident issue, with email enabled if the owner's GitHub preferences allow it.** The failed-run/recovery workflow opens or updates one deduplicated incident containing the run URL, stage, last successful observation, retained/restored release digest and recovery result. Set `issues: write` only on the notification job. Test actual owner receipt during the controlled drill before public activation; current preferences and delivery are not yet verified. Do not rely solely on cron-actor workflow mail, which may target whoever last edited the schedule. No alert was sent during this planning review. The local follow-up remains a supplementary Codex notification path, not the hosted alert's dependency.

A separate scheduled watchdog checks at **09:37 MYT** for a completed qualifying 08:00 run and alerts through the same issue if it is missing, failed, still running beyond the expected duration or not serving its verified release. Delayed runs remain pending/fail the checkpoint until they finish; a late pass records actual timing. This catches missed events without waiting seven days, but is not independent of a GitHub-wide outage. Scheduled execution can be delayed or dropped; see [GitHub's schedule event documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows). Verify notification preferences and delivery using [GitHub Actions notification settings](https://docs.github.com/en/subscriptions-and-notifications/how-tos/managing-github-actions-notifications); successful workflow logging alone is not proof the owner was notified.

### Reviewed coverage and 7A design inputs

**Named source reviewer: FubDuck88 (the project owner/user).** Agents prepare evidence and run automated checks; only the owner's recorded per-field approval makes a value reviewed for coverage. With 19 configurations, inspect every counted field in every applicable configuration, not a sample. Unapproved fields remain pending review and do not enter the coverage numerator. A populated field is not automatically reviewed. To count a value, independently compare that exact configuration/variant's normalized value with its bounded seller evidence and record source URL/locator, observation date, field, evidence excerpt/hash, normalized value, reviewer and audit result tied to the parser version. Manufacturer conventions or model-name guesses do not substitute for variant evidence. Automated schema/provenance and ambiguity checks run on every record. Source qualification still audits at least 20 configurations or all if fewer, but a sampled source audit does not mark all uninspected field values reviewed. Initially only individually passed field values count toward coverage; automation may carry review forward only when the exact value and relevant evidence remain unchanged under the same approved extraction contract. Changed/new evidence requires review.

Compute the 50% eligibility threshold **across the whole non-expired eligible catalog, before buyer filters**, using unique exact configurations rather than offer counts. Alongside the global X/Y label, expose a per-seller coverage breakdown and the names of sellers supplying reviewed values. A single seller may legitimately supply all known values; label that concentration and do not imply other sellers have those fields. A reviewed value applies across offers only when conservative exact-configuration matching independently establishes identity; never transfer it across uncertain matches. Seller selection does not silently change the global control-visibility rule, but the control's help shows coverage among that seller's offers too.

On loading a new release, including one adding a seller, recompute coverage. A previously unselected control falling below 50% disappears from available filters; show a concise catalog-update notice such as **Refresh-rate filtering is unavailable: reviewed coverage is now 8 of 21 laptops**, and keep the Data coverage summary accessible. A selected/restored requirement stays as a removable chip with its new coverage and explicit relaxation option. Do not silently change the query. Announce the update accessibly and preserve focus if a control is removed.

**7A real-record designs show only controls whose reviewed coverage meets 50%.** Refresh at 4/19 and hypothetical repaired VRAM at 4/19 do not qualify. Real-record layouts may show those honest counts in the noninteractive coverage summary. Demonstrations of a below-threshold control, restored selection, threshold transition or future high-coverage state are separate panels labeled **Synthetic interaction fixture — not current catalog availability**. They cannot be presented as validated real-data functionality. The saved 19-record population counts alone do not prove field-level review.

### Public baseline backup scope and credential check

The backup to the existing public repository was intentional; it preserves public seller evidence and the product/release plan, not a private workspace dump. The hosted-cutover audit summary is intentionally public engineering status. No deployment credentials, bypass instructions or private diagnostic artifacts are needed in it. The longer local audit files were not added by the backup commits. This review checked the added file contents in `d70d417`, `ed7b0f6` and `e205716`: nine distinct files, consisting of two plans and seven frozen-fixture files. **No absolute local user-directory paths or credential/token pattern matches were found.** The local absolute links shown in chat are not file contents committed by those changes. Recheck future public additions before backup; use repository-relative references in documents.

This is a bounded content/pattern review of those added files and versions, not a guarantee about every historical file inherited from the existing repository or every possible secret format. The original fixture bytes and hash remain unchanged. No branch-history rewrite or private-repository move is needed on these findings; public backup remains intentional. Do not place raw investigation responses or local automation settings into this public branch.

### 7C manual investigation record and cutoff classification

The first attempt ran **21 October 2026, 14:09:46–14:09:48 MYT** against `https://www.gloo.com.my/laptops`: HTTP 200, 297,456 bytes, two recognized listing cards, response SHA-256 `ccbceda7b0177b45f171927157720c54943b4794a6f3e22d7d4230f2bc3bbdd3`. Its status is **in progress: listing accessible**, not qualified and not a completed variant/overlap audit. Local evidence is in ignored `artifacts/7c-sources/gloo-initial-attempt.json` and the associated response capture. No website data or production pointer was changed.

7C uses manual, bounded, nonpublishing requests and candidate extraction into `artifacts/7c-sources/` while recurring schedules are paused. Do not run the production daily publisher or legacy all-vendor launcher to investigate unqualified sellers. A future native candidate collector must have an explicit nonproduction output directory. 7C does not depend on 6R completion for access/evidence investigation; qualification still requires the native evidence contract and audit.

The deadline remains **25 October 2026, 23:59 MYT**. If 6R or other work consumes the available time, sources with no actual attempt are recorded **not attempted — project time/dependency limit**. An unfinished accessible audit is **incomplete**. Use **documented as blocked** only for an actual recorded access block, with the permitted retry disposition. Neither elapsed time nor the old Phase 4.5 block converts an unattempted source into a completed investigation. The cutoff still invokes the limited-coverage policy; it does not assert absence of overlap across the market.


### Final unlock, alerting limit and tracked-bytecode exposure

**7B unlock:** code may begin at **6R-CUTOVER-PASSED / awaiting scheduled proof**, provided 7A design is approved. Deployment/release of 7B remains blocked until 6R is fully complete, including the first successful unattended scheduled publication and the post-cutover gate-isolation ledger. This replaces the earlier requirement to finish all of 6R before writing 7B code. Single-seller is the expected initial default; add that explicit operating assumption to the 7B implementation brief when 7B starts.

**Archive location:** both maintenance-M and the last verified public-P archive are durable, versioned **GitHub Release assets**, with release/asset IDs, exact archive SHA-256 and file manifests recorded in the deployment ledger. Actions artifacts are transport/evidence copies only. Recovery downloads the stored archive and re-verifies the recorded digest before deployment; it never rebuilds it. Missing archives or digest mismatches abort recovery and raise an incident.

**Alerting limit:** no independent external monitor is added in this scope. When Actions executes on time, the 09:37 MYT watchdog targets detection within **97 minutes of the nominal 08:00 run**; this is a target, not a guaranteed maximum. A GitHub-wide outage or a dropped/delayed watchdog has **no finite maximum undetected delay** under this design. Record that accepted capability limit explicitly; do not promise bounded detection without an independent service. Native failed-run notifications and the issue watchdog share the GitHub dependency.

**Known inherited path exposure:** full inspection of all **12 tracked Python 3.14 cache files**, including nested code filenames and string constants, found absolute Windows paths in **10 files**. Four contain paths in code filenames; **`test_filter` contains a Windows user-profile path/username in a string constant**. The initial filename-only check found four and missed this constant; the full check supersedes it. See [the redacted exposure inventory](audits/TRACKED_BYTECODE_EXPOSURE_2026-10-21.md). These files were already in repository history; the earlier nine-file backup scan did not cover them. Exact local directories and username are omitted publicly. All 12 tracked cache files were removed from the current tree in commit `fca90cc`; removal prevents new deployment but does not erase Git history, clones or existing public copies. A history rewrite is a separate coordinated decision, not implied by ordinary cleanup.

**Implementation order:** (1) deploy checked maintenance and disable the legacy publisher; (2) prove rollback and owner notification before activation; (3) verify cutover, then implement the 6R-GATE-ISOLATION ledger; (4) 7A design and bounded 7C investigations run in parallel starting 21 October. The 25 October 23:59 MYT investigation deadline does not move. Source population methods and robots/terms review remain 7C qualification work before recurring seller collection.


### Implementation checkpoint — maintenance live, 7A/7C started

On 21 October, maintenance deployment [run 39593836589](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39593836589) passed package, deploy and hosted verification jobs at commit `fca90cc7f153f3b92c917808d212316792a546f3`. The legacy scheduled workflow is disabled and Pages now uses explicit Actions deployment. This is **maintenance deployed**, not 6R-CUTOVER-PASSED: verified-catalog activation, rollback drill, owner-notification proof, gate-isolation work and scheduled publication proof remain pending. See [maintenance evidence](audits/PHASE6R_MAINTENANCE_2026-10-21.md).

The [7A preview](PHASE7A_DESIGN.md) is ready for visual review, with synthetic interactions kept separate from historical records and no field-review approval implied. [7C source findings](audits/PHASE7C_SOURCE_INVESTIGATION.md) record unresolved Gloo/TMT sourcing conditions and the current PC Image access challenge; none is newly qualified. Production collection remains paused. The fixed 25 October deadline remains unchanged.


### Notification-delivery evidence and 6R implementation progress

The notification gate requires proven delivery to FubDuck88's configured GitHub inbox, not additional deployment permission or proof that the message was read. Authenticated repository-notification inspection verified the issue1 mention in that exact account on 21 October. The deployment state records the evidence hash and recipient/issue association, with private inbox metadata kept outside Git. Explicit owner acknowledgement remains a fallback when direct delivery evidence is unavailable. Neither form approves source fields or the 7A design.

The complete hosted recovery drill [39598958048](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39598958048) passed, and a controlled cancellation also left maintenance restored. Native GPU extraction and the manual launcher are repaired, the executable/spec removed, and a separate post-repair release fixture records 22 accepted configurations. See [6R implementation evidence](PHASE6R_IMPLEMENTATION.md). Verified catalog cutover is now the next authorized step; full 6R completion still requires post-cutover gate isolation and the first successful unattended scheduled run.


### Current 6R checkpoint — 21 October 2026

The [cutover](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39600483435) passed and the verified 22-offer catalog is live. Controlled HTTP/hash/frontend recovery, cancellation cleanup, actual timeout recovery and authenticated owner-inbox delivery are evidenced in [the implementation report](PHASE6R_IMPLEMENTATION.md). Gate isolation is implemented and tested; a fresh 6R-only operational ledger has a healthy actual receipt. No 7F validation window is open.

The GitHub publisher is enabled for 08:00 MYT daily and the watchdog for 09:37. Full 6R closure awaits the first actual successful scheduled publication, nominally **22 October 2026 at 08:00 MYT**; a manual dispatch is not that proof. The app follow-up is an approved read-only observer, superseding the earlier dual-collector proposal. It cannot make future repository changes. Data/design approvals remain with FubDuck88, and the 25 October 23:59 MYT source-investigation cutoff is unchanged.
