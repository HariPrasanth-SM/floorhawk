# Unified Hybrid UI and reliability release — 2026-11-14

Stable URL: https://sm-hariprasanth--web.us-east.modal.run . Promoted UI/source a44e94f; private repo retains the Local rollback966248c at floorhawk-modal/releases/local-verified. Operational current points to releases/ui-hybrid-verified. Access-code file remains floorhawk-modal/.secrets/event-access-code; values never printed.

## Product and verification

One Result replaces competing Local/Hybrid cards. All accepted questions use shared Local evidence plus bounded Gemini review. Valid structured Hybrid answers are displayed; unsupported/abstained responses remain unresolved. Provider/schema/budget failure retains Local and explicitly displays “Local fallback — Gemini unavailable.” Original Local/Gemini outputs remain separate in records. No intermediate Local answer is displayed as final.

Logo uses Arial32px, Floor#ffab40 and HAWK#595959. Tabs: Live demo / Preloaded examples. Validated PNG/PDF previews appear before Ask; Drawing ready appears only after server validation. IFC shows a file placeholder; optional context rendering has a3second viewer budget, otherwise the placeholder/property evidence remains. Cloud geometry is currently unavailable, so IFC export is honestly disabled. Evidence list scrolls separately and full-size source evidence remains available. Whole-image/current-page annotated export has no UI panels/reference card. Export sizes tested: PNG2730×2048,PDF3200×2134. Actual PNG annotation pixels align with source boxes. Aspect ratio and existing PDF transforms are reused.

Normal access-code login passed, without verification-session bypass. Candidate browser cases: PNG windows7,PNGdoors5,PDFprintedarea12m²,IFCwindowentities3. Each final candidate case used1real provider attempt. PDF Local was unresolved, Hybrid read the printed area. These are selected unscored smoke outputs, not accuracy/generalization results. Final production IFC count3 also passed with1real provider attempt.66focused/regression tests pass. Both1366×768 and1920×1080 fit; no page errors. Browser-only provider-failure fixture verified explicit Local fallback, without another provider call.

## Reference isolation and gallery gaps

One licensed CubiCasa development PNG and two original synthetic CC0 PDF/IFC documents are protected source assets, not replay records. No saved detections/answers are served as live inference. All accepted asks process source anew; shared extraction is reused only within the request. Model worker remains subprocess-isolated, so weights are not yet retained between requests. No permanent warm GPU spending was added.

Starting catalog contains only checked suggestions:2PNG/1PDF/1IFC. Unchecked suggestions were removed. PNG expected counts were not independently established and are not invented from model outputs. PDF12m² and IFC3references come from the original synthetic source definitions, stored in a separate UI-only Modal Dict. Expected reference appears only for exact suggested text, clears on edits and is associated server-side. Reference resources are not passed to the inference payload/bundles/prompts. No IFC mesh views were added; this is an explicit coverage gap.

## Reliability findings

Historical logs showed a429 but did not prove the original reported transient error's root cause. Two concrete browser races were reproduced and corrected: source replacement could leave the prior file briefly eligible for Ask; reload before POST acceptance could reopen the previous job. Source readiness now gates Ask, and a random submission key is persisted before POST. Reload resolves that key server-side without resubmitting inference. Ownership checks also apply to reuse of a prior job's source.

Status polling retries transient failures at most5times with bounded exponential backoff and Reconnecting. An injected503 verified no second POST. Reload during processing, same-image/new-question, changed source while pending and switched formats passed. Terminal failures clear loading and permit safe retry. An initial candidate dispatch configuration omitted its shared-worker environment variable; that produced a real CUDA-unavailable failure in its CPU-only function. This was fixed and the failed candidate was not promoted. The old stable frontend stayed pinned until checks passed.

## Budget and deployment

User authorized100USD TOTAL including prior reservations; request cap remains1000. The original311ledger rows/$9.717reservations were retained.30new prepaid permits/$0.60 were reserved atomically in that same canonical ledger and assigned to a durable cloud authority. Canonical totals became341reserved slots/$10.317, leaving89.683USD reservation capacity. Unused prepaid slots are not HTTP calls. Cloud can consume only these non-overlapping permits; this release stops at30cloud attempts. No cloned independently spendable ledger exists. Consumed permit metadata is reconciled back without reducing any reservation or rewriting prior history.

Exact final attempts/token estimates: external floorhawk-modal/verification/ui-release/accounting.json. Reservations, known token-price estimates and unsettled actual billing are distinct. Missing thinking usage is unknown. No Gemini key reaches browser/export. Existing Modal Secret is mounted server-side on the worker only. No plan changes, training, new models or benchmark campaign.

One T4 GPU worker,max1/min0. Candidate API delegated to it and was stopped after promotion. Quotas/access codes/ownership and previous jobs are preserved. Local extraction/model and Gemini timing are separate; queue/container startup is labelled combined where separate timestamps are unavailable. Final production IFC example:9.67s end-to-end, including4.80s combinedqueue/startup,0.90s sharedpreprocessing and3.58s additionalGemini; this is one smoke, not a speed benchmark.

## Commands (from proofplan/)

```bash
.venv/bin/python deploy/modal/manage.py status
.venv/bin/modal app list --json
.venv/bin/modal deploy deploy/modal/app.py
# Previous verified Local product:
FLOORHAWK_RELEASE="$PWD/../floorhawk-modal/releases/local-verified" .venv/bin/modal deploy deploy/modal/app.py
# Disable/stop:
.venv/bin/python deploy/modal/manage.py disable
.venv/bin/modal app stop floorhawk-demo --yes
```

Current manage.py can re-enable Hybrid only from a passing report with real successful provider attempts: `manage.py enable --verified-report ../floorhawk-modal/verification/ui-release/report.json`. No budget funding/reset occurs. Crash recovery stays fail-closed/manual: stop all apps sharing admission first, verify no running owner, then `manage.py recover-lock --confirm-app-stopped`. Do not automatically clear a live lock.
