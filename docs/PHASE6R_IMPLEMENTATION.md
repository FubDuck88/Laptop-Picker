# Phase 6R implementation

21 October 2026 MYT. Recommended model: GPT-6.1 Sol, high effort.

Status: implementation and hosted recovery validation in progress; maintenance remains the public default. This is not full 6R completion.

## Completed local work

- Native ALL IT extraction now preserves explicit GPU type and dedicated graphics memory with separate source evidence. Model-name prefixes do not classify a GPU. Integrated/shared/system memory cannot become VRAM, and ambiguous values remain unknown.
- The manual batch/Python launcher runs the verified ALL IT collector and validator, propagates failures, and does not open a file-URL preview. The obsolete executable/spec are removed; tracked caches were removed previously.
- A fresh collection produced 22 accepted configurations, including three additional Acer parts. Six configuration identities changed with enriched evidence; no previous part disappeared. Historical prices were not transferred to a changed identity by assumption.
- Five configurations now have explicit GPU type, four VRAM, and four refresh rate. Independent source re-reading passed for 21 of 22 offers: the normal 20-record sample plus the additional repaired-GPU configuration, ensuring every newly populated GPU field was checked. This is automated evidence checking, not FubDuck88's field approval.
- Historical post-repair fixture: `tests/fixtures/releases/phase6r-2026-10-21/`. Release SHA-256 `4024cf5e837eaafe955f6eead170810535b2d7f2d8a5364e666215e4236f903d`, release format1/catalog schema2. Original fixture bytes remain unchanged; archive and fixture line-ending protection is explicit.
- 104 Python checks, 18 JavaScript checks and 48 browser regressions passed locally. Candidate/public packaging tests cover separate data roots, excluded inputs, expired cutover refusal, tampered recovery bytes and portable directory entries.

## Hosted operations

`.github/workflows/pages-release.yml` builds and checks candidate-C and public-P independently, stages the candidate alongside the known-good public root, verifies real browser loading and corrupt-release rejection, and activates only after a checked candidate. Archives are durable GitHub Release assets. `tools/pages_ops.py` verifies saved recovery bytes and uses the `codex/deployment-state` branch with compare-and-swap writes and run identities to avoid stale recovery overwrites.

The first drill [39598126437](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39598126437) failed before candidate browser verification. It automatically redeployed the stored maintenance archive and passed restored-site verification. It must not be counted as passing the three controlled browser failures. The archive layout was aligned with the Pages upload convention. Repeat [39598958048](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39598958048) passed: the real candidate loaded, HTTP/hash/frontend failures were detected, the stored maintenance archive was restored, and restored-site hashes/exclusion checks passed. Controlled cancellation run `39599444786` also left maintenance restored; its completion handler `39599630440` respected the cleared stale-run guard.

The owner notification was created by the workflow at [issue1](https://github.com/FubDuck88/Laptop-Picker/issues/1). Actual delivery to the authenticated FubDuck88 GitHub repository-notification inbox was independently verified, including an issue1 mention entry. A hash of that private evidence is recorded in deployment state; notification contents/read state are not published. This proves delivery, not that the owner read it or approved data/design. The delivery gate accepts this verified inbox evidence or explicit owner acknowledgement; issue creation alone does not meet it.

The existing scheduled collection workflow remains disabled until verified cutover. Its replacement calls the same checked Pages workflow. A failed candidate/collection retains or restores the last verified public archive and reports degraded status. A separate guarded workflow handles interrupted publication; the 09:37 MYT watchdog uses GitHub incident notifications. These still share GitHub's availability dependency, with no guaranteed finite detection bound in an outage.

## Remaining ordered gates

1. Complete: hosted controlled-failure/recovery drill and authenticated owner-inbox notification delivery proof.
2. Collect/audit and verify the hosted candidate, then activate and verify canonical public URLs. Until this gate passes, 7B code remains locked.
3. Implement and validate the fresh gate-isolation ledger after cutover, as ordered. No historical Phase6/6R receipt may count toward 7F.
4. Enable daily operations and record the first genuine successful 08:00 MYT scheduled publication. Manual dispatches do not replace scheduled proof. Full 6R closure and 7B release remain blocked until all these gates pass.
