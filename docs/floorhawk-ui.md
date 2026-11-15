# FloorHAWK frontend repair — 2026-11-14

UI/export iteration only: no training, model, threshold, routing or provider changes and no new inference/API calls. Existing proofplan/ paths, environment variables, API protocol and private repository names remain compatible; product titles and source/documentation branding now read FloorHAWK.

Hybrid presentation resolves cited IDs against the saved Local/cumulative/document evidence, then uses the existing PDF rotation and ingestion coordinate transforms. The main viewer, evidence selector and source-resolution crop switch together. The Local checkbox switches back to saved Local evidence. Model-proposed regions remain explicitly unverified. Missing IDs never become fabricated objects.

Actual saved examples verified in Chromium: window question7f876a249612426180bc926548d8df1d shows Hybrid4 with four cited native-PDF regions; stove questionec2bf4691f6845dfa39d3d546a9772cb shows Hybrid4 with its cited page overview, explicitly labelled “no per-object locations returned.” The stove recording has no stove boxes; this UI-only change cannot recover missing localization. The overview frame is context, never a counted instance. Both source crops load and align using existing coordinate conversion.

The default shell has Explore and top Export ZIP, one combined evidence panel with short source/model labels, no Evaluation tab, no review-edit controls, no live sample selector and no attribution placeholder footer. Replay retains its saved-question selector. Attribution metadata and original drawing/license credit are retained in exports. Diagnostics is hidden by default; pass --diagnostics to enable it.

Export downloads use floorhawk-<random-id>.zip. ZIP contains the original supported source, Local annotated evidence, Hybrid annotated evidence when localized, and diagnostic.json with question, separate original/reviewed outputs, saved Local/Hybrid model and provider metadata, evidence catalog and selected Hybrid evidence. Secrets, raw prompts and reference answers are stripped. Original sources remain private runtime files; no dataset or drawing is tracked.

Commands from the parent directory:

```bash
# Only if the existing user-owned worker is not already running:
bash proofplan/start_host_worker_v2.sh
# Restart the live backend to load frontend/server changes:
bash proofplan/start_live.sh --port 8777
# Optional trace drawer:
bash proofplan/start_live.sh --diagnostics --port 8777
# Inference-free replay:
bash proofplan/start_demo_v3.sh --replay --include-failures --port 8774
```

Live URL http://127.0.0.1:8777 ; replay http://127.0.0.1:8774 . Temporary verification used the actual live launcher on8778 and replay with --diagnostics on8779; both task servers are stopped after verification. User-managed servers/host worker are preserved.

Verification:102 focused/regression tests pass; synthetic Hybrid-specific non-Local box/crop selection passes. Real saved-window/stove browser checks pass at1366×768 and1920×1080 with no page overflow or browser errors. Clear controls, top export, Local/Hybrid switching, hidden controls, crop loading, randomized ZIP download and export contents pass. Ledger unchanged throughout browser verification. Replay --diagnostics opens with an empty inference-module list. Reports are external: results/floorhawk-ui/verification.json and results/agile-ui/verification.json.
