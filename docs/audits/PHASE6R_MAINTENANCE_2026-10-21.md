# 6R maintenance deployment — 21 October 2026

Status: first deployment milestone only. Verified-catalog activation and full 6R completion are pending.

- Source commit: `fca90cc7f153f3b92c917808d212316792a546f3`.
- [Workflow run 39593836589](https://github.com/FubDuck88/Laptop-Picker/actions/runs/39593836589): package, deploy and hosted verification passed.
- Site: [Laptop Picker](https://fubduck88.github.io/Laptop-Picker/).
- Legacy collection workflow ID `326306870` was disabled; no active legacy runs needed cancellation. Pages build type changed from branch-based legacy publication to explicit workflow deployment.
- [Durable maintenance release](https://github.com/FubDuck88/Laptop-Picker/releases/tag/maintenance-fca90cc7f153f3b92c917808d212316792a546f3), release ID `419488074`.
- Archive asset ID `662315139`, `artifact.tar`, 20,480 bytes. SHA-256: `eed794e1253af5cdfe7ffdc7c8b9363b1e6589d57e6887119c7c830fc8ae04bf`.
- Stored archive was independently downloaded and matched the locally checked digest. Release assets also contain `archive.sha256` and `manifest.json`; the latter records each served file hash.

The package contains exactly `index.html`, `mobile.html`, `analytics.html` and `404.html`, all serving maintenance. No catalog pointer, scripts, tests, diagnostic files or executable are packaged. Deterministic rebuild and local Chromium checks passed for desktop, phone, light/dark modes and overflow. The cloud verification job checked served bytes, root content and representative excluded paths. A first local urllib check encountered local DNS resolution failure; it does not override successful cloud checks, and a separate requests-client verification was used to confirm the public result.

The maintained source and workflow are committed; unrelated collector/frontend work remains outside this deployment. Twelve tracked cache files were removed from the current tree; historical path exposure remains documented separately. No gate receipts were backfilled, no collection schedule resumed and no real prices were published by this maintenance deployment.

Next required milestones are the controlled recovery drill and owner notification proof before verified-catalog activation, then gate isolation and the first successful unattended scheduled publication. Maintenance deployment does not satisfy any of those later gates.
