# Implementation phases and model recommendations

These settings are recommendations for the person starting each implementation session.
They do not change the current chat's model automatically. GPT-6.1 Sol is the default
recommendation for this project's coding work; high effort suits the data integrity
and integration decisions. The narrower baseline work can use medium effort.
See the [official model documentation](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
and [reasoning effort guide](https://developers.openai.com/api/docs/guides/reasoning).

| Phase | Work and completion gate | Model | Effort | Status |
| --- | --- | --- | --- | --- |
| 1 | Freeze representative inputs, establish offline checks, remove unsupported history claims | GPT-6.1 Sol | medium | Complete |
| 2 | Separate configurations, seller offers, observations, and run reports; validate evidence and money; quarantine legacy imports | GPT-6.1 Sol | high | Complete |
| 3 | Extract actual variants, normalize bounded fields, preserve seller identity, reject ambiguity, match conservatively, qualify each enabled source | GPT-6.1 Sol | high | Complete for ALL IT; other sources deferred |
| 4 | Collect daily at 08:00 Malaysia time; stage and validate before publication; retain last good data on failure; mark stale at 48 hours and hide by default after seven days | GPT-6.1 Sol | high | Implemented and live-tested locally; hosted schedule not yet deployed |
| 4.5 | Repair product photo extraction, check image responses during collection, verify real desktop/phone loading and honest unavailable states | GPT-6.1 Sol | high | Implemented locally; ALL IT and two current Gloo cards verified; PC Image/TechHypermart live recovery blocked by vendor responses |
| 5 | Migrate frontend to verified records, fix the seven known frontend defects, show explicit unknown/freshness states, build history only from real observations | GPT-6.1 Sol | high | Implemented and tested locally; 48 browser checks pass |
| 6 | Re-audit enabled sources, inspect responsive/browser behavior, observe seven successful daily runs and confirm release gates | GPT-6.1 Sol | high | In progress: source/browser/layout checks pass; local day 1/7 recorded; daily follow-up PAUSED when inspected 21 October; hosted gate pending |
| 6R | Pipeline-only hosted cutover; repair ALL IT GPU extraction and manual launcher; remove unused executable/caches; implement 6R-GATE-ISOLATION, post-repair fixtures, package-exclusion checks, and maintenance-to-verified cutover | GPT-6.1 Sol | high | Required before 7B code starts; implementation pending; resume daily collection after 6R passes |
| 7A | Establish the design system and labeled responsive previews | GPT-6.1 Sol | high | Planned; may proceed alongside 6R |
| 7B | Unified shopping, comparison, specification filters with 50% minimum reviewed coverage, labels and actionable restored requirements; review AMD/NVIDIA naming sources; links only for reviewed entries | GPT-6.1 Sol | high | Planned; closes as fixture-tested after 6R/7A; live validation is a separate 7C-LIVE task |
| 7C | 7C-SOURCES: Gloo, TMT (Thunder Match), PC Image audits; 7C-LIVE: validate overlap through completed UI or record no-overlap deferral | GPT-6.1 Sol | high | Planned source window 21–25 October MYT inclusive; first attempt pending; LIVE after fixture-tested 7B and must close before 7F; fixed cutoff even if first attempt is late; TechHypermart deferred |
| 7D | Sourced specification education and compatible benchmark comparisons | GPT-6.1 Sol | high | Planned; source feasibility required |
| 7E | Model-specific ownership evidence and supported upgrade candidates | GPT-6.1 Sol | high | Planned; exact-model evidence required |
| 7F | Open a new gate/ledger using 6R-GATE-ISOLATION after final integrated changes and 7C-LIVE outcome; run seven qualifying daily runs; fixes or fixture changes restart window | GPT-6.1 Sol | high | Planned; no historical Phase 6 or 6R receipt carry-over |

Source qualification is incremental: audit at least 20 accepted configurations per source,
or every accepted configuration if its population is smaller. A source that cannot
prove exact variants stays deferred. Marketing coverage and catalog size do not
override accuracy. The Phase 3 audit covers all 19 accepted ALL IT configurations.
The local frontend now reads verified releases. See [Phase 5 behavior and verification](FRONTEND_VERIFIED.md).

Phase 4 also preserves variant photo provenance and handles missing/broken photos. See
[the pipeline guide](RELEASE_PIPELINE.md) and [photo investigation](audits/PHOTOS_2026-10-20.md).
Phase 4.5 results and remaining vendor limits are in the
[photo reliability report](audits/PHOTOS_PHASE45_2026-10-20.md).
Phase 6 progress, evidence and remaining hosted requirements are in
[the release gate report](RELEASE_GATES.md).

The [design overhaul plan](DESIGN_OVERHAUL_PLAN.md) records the agreed product direction,
data dependencies, baseline evidence, and migration of Phase 5 browser checks.
The 21 October review found no additional local daily receipts or hosted proof for the
verified implementation; Phase 6 completion must not be inferred from older successful workflows.
