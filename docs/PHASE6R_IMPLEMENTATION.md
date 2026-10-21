# Phase 6R implementation

21 October 2026 MYT. Recommended model: GPT-6.1 Sol, high effort.

**Status: 6R-CUTOVER-PASSED / awaiting scheduled proof.** The verified catalog is live; daily publication is enabled. Full phase closure awaits the first successful actual scheduled run at 08:00 MYT, nominally 22 October 2026.

## Completed local work

- Native ALL IT extraction now preserves explicit GPU type and dedicated graphics memory with separate source evidence. Model-name prefixes do not classify a GPU. Integrated/shared/system memory cannot become VRAM, and ambiguous values remain unknown.
- The manual batch/Python launcher runs the verified ALL IT collector and validator, propagates failures, and does not open a file-URL preview. The obsolete executable/spec are removed; tracked caches were removed previously.
- A fresh collection produced 22 accepted configurations, including three additional Acer parts. Six configuration identities changed with enriched evidence; no previous part disappeared. Historical prices were not transferred to a changed identity by assumption.
- Five configurations now have explicit GPU type, four VRAM, and four refresh rate. Independent source re-reading passed for 21 of 22 offers: the normal 20-record sample plus the additional repaired-GPU configuration, ensuring every newly populated GPU field was checked. This is automated evidence checking, not FubDuck88's field approval.
- Historical post-repair fixture: `tests/fixtures/releases/phase6r-2026-10-21/`. Release SHA-256 `4024cf5e837eaafe955f6eead170810535b2d7f2d8a5364e666215e4236f903d`, release format1/catalog schema2. Original fixture bytes remain unchanged; archive and fixture line-ending protection is explicit.
- 113 Python checks, 18 JavaScript checks and 48 browser regressions passed locally. Candidate/public packaging tests cover separate data roots, excluded inputs, expired cutover refusal, tampered recovery bytes and portable directory entries.

## Hosted operations

`.github/workflows/pages-release.yml` builds and checks candidate-C and public-P independently, stages the candidate alongside the known-good public root, verifies real browser loading and corrupt-release rejection, and activates only after a checked candidate. Archives are durable GitHub Release assets. `tools/pages_ops.py` verifies saved recovery bytes and uses the `codex/deployment-state` branch with compare-and-swap writes and run identities to avoid stale recovery overwrites.

The first drill [39598126437](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39598126437) failed before candidate browser verification. It automatically redeployed the stored maintenance archive and passed restored-site verification. It must not be counted as passing the three controlled browser failures. The archive layout was aligned with the Pages upload convention. Repeat [39598958048](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39598958048) passed: the real candidate loaded, HTTP/hash/frontend failures were detected, the stored maintenance archive was restored, and restored-site hashes/exclusion checks passed. Controlled cancellation run `39599444786` also left maintenance restored; its completion handler `39599630440` respected the cleared stale-run guard.

The owner notification was created by the workflow at [issue1](https://github.com/FubDuck88/Laptop-Picker/issues/1). Actual delivery to the authenticated FubDuck88 GitHub repository-notification inbox was independently verified, including an issue1 mention entry. A hash of that private evidence is recorded in deployment state; notification contents/read state are not published. This proves delivery, not that the owner read it or approved data/design. The delivery gate accepts this verified inbox evidence or explicit owner acknowledgement; issue creation alone does not meet it.

The existing scheduled collection workflow has been replaced with the verified publisher and is now enabled. Its replacement calls the same checked Pages workflow. A failed candidate/collection retains or restores the last verified public archive and reports degraded status. A separate guarded workflow handles interrupted publication; the 09:37 MYT watchdog uses GitHub incident notifications. These still share GitHub's availability dependency, with no guaranteed finite detection bound in an outage.

## Cutover and ledger proof

- [Actual cutover run 39600483435](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39600483435) passed fresh collection, source audit, candidate checks, public activation and canonical-URL checks.
- Served release SHA-256: `b129b6c30148a5d0de9da8eb45abee1cdae577f94ab0b4046a9693e22ec80f71`, with 22 offers. It was independently fetched and hashed after activation and after recovery testing.
- Public archive: GitHub Release `pages-39600483435-1`, release ID `419536493`; archive SHA-256 `cc3e7ea19f6dcf112e5ed8fd15fb2bc398bb462ba1c0cb9e4fea2f09297d1d48`.
- Post-cutover controlled timeout [39603595580](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39603595580) exceeded its real one-minute job limit. Completion handler `39603854156` dispatched automatic recovery [39603867438](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39603867438), which restored and verified the exact public archive and preserved the pre-test enabled publication state. The timeout drill did not collect or publish new prices.
- `tools/gate_ledger.py` opens fresh phase/environment/implementation identities with real start timestamps. Tests exclude old Phase6 day-one receipts, 6R operational receipts, different gates, pre-start receipts, changed implementations and wrong environments from 7F. Malformed current-gate receipts prevent a pass.
- The implementation fingerprint includes nested fixture bytes and metadata, manual launcher, runtime sources and workflows. Live data and generated evidence are excluded. Windows working-copy and clean committed-checkout fingerprints were compared; two synthetic JSON fixture line-ending rules were corrected before recording the final ledger.
- Final operational gate ID: `7667d8da039a4a2b847b5ecc97bf6e70`. Fingerprint: `369081cd48b4b203bb9b0f6b0440e4a299ecc6b3238e41ab229dc4e75bd2e2b1`. Its actual offline/collection/validation/source/browser/responsive/photo steps passed. Scope is **6R operational only**, with one healthy receipt and zero counted release-window days. No real 7F gate has opened.

## First scheduled checkpoint

The native GitHub workflow is active for **08:00 MYT daily**, and its 09:37 watchdog is active. `last_schedule` is currently null, correctly reflecting that no actual scheduled publication has passed since cutover. Only `GITHUB_EVENT_NAME=schedule` can create that proof; a manual dispatch cannot substitute.

The resumed Codex follow-up is a temporary **read-only scheduled-proof monitor**. It may inspect status and notify this chat; it cannot collect, edit, commit, push, deploy or approve data/design. Local collection remains available through the manual verified launcher and `tools/run_operational.py`. GitHub is the authoritative unattended collector. This replaces the earlier proposal for a second recurring local collector and future automatic documentation commits.

Full 6R closure remains pending that actual scheduled checkpoint. 7B code still also needs approved 7A design, and 7B release remains forbidden until 6R closes. The monitor will report actual proof rather than mark an unobserved run successful.
