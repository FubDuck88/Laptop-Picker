# Phase 7A: responsive design study

21 October 2026 · Recommended model: **GPT-6.1 Sol, high effort**.

**Status: concrete design preview for review; not approved, not production implementation.**
The project owner and named source reviewer is **FubDuck88**. No field-level review
approval or reviewed coverage count is asserted by this deliverable. Phase 7B remains
blocked until the agreed 6R cutover and 7A design approval gates pass.

## Open and review

Open [the self-contained preview](../design/phase7a/index.html) in a browser. It works
directly from disk, without a server, packages, remote fonts or image requests.
Navigation provides Find, a real historical MSI detail, a comparison study and Research.
The header toggles light/dark. On phones, Requirements opens a native modal sheet.
The local [verification script](../design/phase7a/check_preview.py) and
[verification report](../design/phase7a/verification.json) describe the checks performed.

This is an isolated static design prototype under `design/phase7a/`. Production HTML,
JavaScript, CSS, release readers, seller collection and the shared phase plan are not
changed. Do not count prototype checks as 7B acceptance or release-gate observations.

## Direction and components

The visual direction is a restrained, light-first research tool: warm neutral canvas,
forest-green actions, readable system sans typography and clear price hierarchy.
Dark mode has independent semantic colors. Product photography has a fixed region;
this offline preview deliberately displays a labeled omission rather than a fake MSI image.

The [semantic tokens](../design/phase7a/tokens.css) define surface, text, accent, focus,
warning, spacing, radius, typography and motion. The spacing scale is 4/8/12/16/24/32/48px.
Body text is 16px, supporting text 14px, and primary page titles scale from 32px to 56px.
Controls are at least 44px high. Rounded panels use 16px corners; controls use 8px.
One simple outline SVG family supplies the brand and photo-placeholder laptop glyph.

| Component | Design behavior |
| --- | --- |
| Main navigation | Find laptops and Research; comparison/details stay inside Find; one responsive page, no device redirect. |
| Requirements | Desktop sidebar, native phone dialog below 900px; explicit field labels, numeric price entry, clear action and coverage explanation. |
| Result card | Exact model/part number, recorded CPU/GPU and RAM/storage, then item price, seller, unknown stock, timestamp and same-variant seller action. |
| Shortlist | Session-only working add/remove demonstration, polite announcement, comparison entry; device persistence is specified for 7B, not implemented here. |
| Details | Exact recorded specifications, same seller offer, three actual timestamped receipts and explicit missing ownership evidence. |
| Comparison | Two readable columns on phones; second choice switches between isolated fixtures; differences-only never hides unknown evidence. |
| Research | Clear pending naming/measurement states; no fabricated benchmark charts, citations or scores; secondary ALL IT snapshot description. |
| Disclosure | Historical snapshot notice at screen level; fixture warnings at both screen/section where applicable; no synthetic outbound purchase link. |

Layouts use a maximum 1280px container, 32px desktop gutters and 16px phone gutters.
At 900px the sidebar becomes a dialog; at 600px cards stack and grids become one column.
The comparison retains two columns with wrapping labels. The preview tray is in normal
flow at all widths to avoid covering content; a production persistent tray needs reserved
space and focus-obscuration checks before adoption.

## Data and review boundaries

The real example is **MSI B13VF-3492MY**, ALL IT variant **48918847357156**, recorded
at **RM3,879**, stock unknown. Its recorded CPU is Intel Core i5-13420H, GPU model is
NVIDIA GeForce RTX 4060, RAM 16GB DDR4, storage 512GB SSD. GPU type/VRAM remain unknown.
Snapshot bytes are derived from release
`116059d4de1016c9ceba960b43fa8d827a598bdcd8d17a75caef1ddc45620268`.
The [snapshot file](../design/phase7a/snapshot.js) retains exact configuration/offer
evidence and the three actual receipt timestamps. All three prices are RM3,879;
the preview creates no additional observations or interpolated history.

The page shows **one illustrative selection from the historical 19-configuration
catalog**, not a newly filtered full-catalog result. It does not evaluate today's
freshness; the global historical notice is permanent. Seller links preserve the
original exact variant and warn that present price/availability may differ.

No real-record specification controls are shown because approved field-level counts
have not been supplied. A populated field is not presumed reviewed. Price and seller
are offer fields and are not governed by the sparse-specification threshold.
The noninteractive coverage summary explains the pending audit and single-seller scope.
Once approved evidence exists, 7B must compute coverage from the whole eligible base
catalog, include seller breakdowns, and show a specification control only at 50% or more.

The separate expandable interaction fixture demonstrates 9/19 hidden versus 10/19
shown, a restored RAM requirement remaining visible below the threshold, explicit
removal, keyboard/numeric price ranges and an explicit over-budget alternative.
These numbers are labeled synthetic and are **not approved real coverage**. Comparison
Examples A/B/C and their RM4,200 price are synthetic, with purchase disabled.
RM4,000 is a test-only range ceiling, not the user's personal budget default.

## Review workflow and limitations

Applied the UI/UX Pro Max workflow: inspected requirements and web stack, generated
a system suggestion, then searched keyboard/focus guidance and HTML implementation
guidance. The generated hero/features/CTA pattern was rejected as inappropriate for
a catalog tool. The focused catalog-pattern search returned no match; the layout here
is a product-specific design judgment, not a purported verified database prescription.
No Tailwind or animation framework was introduced. The skill's native-only units and
patterns were not copied into web requirements.

Native dialog supplies focus containment and Escape handling; the preview restores
focus to the trigger. Route changes focus main content. Visible focus rings, skip
link, explicit labels, text status, semantic tables and reduced-motion tokens are present.
Automated Chromium verification passed 40 route/theme/viewport cases at widths
320, 375, 768, 844 (landscape) and 1440px, plus dialog Escape/focus restoration,
shortlisting, empty search, 9/19-to-10/19 fixture visibility, preserved restored
requirement, keyboard range entry, explicit alternatives and comparison differences.
Both themes' tested normal-text pairs exceed 4.5:1 (lowest measured 6.30:1).
Reduced-motion and 200% text comparison reflow checks passed; no page exceptions or
remote requests occurred. Desktop light and phone dark screenshots were visually
inspected and the tray was moved to normal flow after noticing it covered content.

This preview does not implement durable shortlist storage, URL search serialization,
full-catalog matching, four real saved choices, live freshness, real source review,
benchmark collection, guide search or a complete loading/error state library. Those
remain 7B/later implementation work. Native screen-reader and Safari/Firefox checks,
real photograph composition and full WCAG conformance are not certified here.

Approval should settle visual hierarchy, card density, phone filter/dialog ergonomics,
comparison readability and the prominence of review/coverage explanations. Source
review approval is a separate action from approving this appearance.
