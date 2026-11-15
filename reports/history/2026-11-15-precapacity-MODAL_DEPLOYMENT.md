# Current event deployment8fce908 — frozen inference5827eab

The current actual workflow is [event operations](EVENT_OPERATIONS.md), with [verified deployment results](OVERNIGHT_DEPLOYMENT_VERIFICATION.md) and [release/model manifest](release-manifest.json). All roles use the same source/config/frontend, separate admission/jobs/GPU workers, and the shared80USD provider envelope already inside the100USD authorization. Old permit/1000request descriptions below are historical and do not govern the new event workers. Presenter/judges warming remains billable; public retains its7USD compute guard.

Backend-only snapshot export preserved frontend SHA256a111edce02bc2803837609cf4b15bfc19d3ee1e9ff2f003826aa2a2c49aafae8 and endpoint URLs across actual staging/promotions. `assets.json` is included and28remote assets verified. Rollback construction was imported successfully from the original presenter snapshot; no serving rollback was unnecessarily performed after successful promotion.

## Historical deployment record

# FloorHAWK — protected Local cloud demo

**Live URL: https://sm-hariprasanth--web.us-east.modal.run**

Workspace `sm-hariprasanth`; app `floorhawk-demo`; deployed release `966248c9a121e881882febd0deef53cc282a09d0`. Verified on2PNG images/3Local questions with real T4 CUDA forwards, evidence/crops, session isolation and duplicate prevention. Read [MODAL_VERIFICATION.md](MODAL_VERIFICATION.md) for exact evidence and limitations. Earlier payment-method blocker is resolved.

The landing page asks for the event access code. Its private local file is `../floorhawk-modal/.secrets/event-access-code` relative to canonical proofplan/. It is0600; never print it into logs, commit it or include it in slides. floorhawk-access holds only server-side authentication material. Gemini remains disabled; no budget reset/increase or provider test was performed.

## Operator commands

Run from canonical `proofplan/`:

```bash
# Status and logs
.venv/bin/modal app list --json
.venv/bin/python deploy/modal/manage.py status
.venv/bin/modal app logs floorhawk-demo

# Redeploy current pinned operational snapshot (current points to local-verified)
.venv/bin/modal deploy deploy/modal/app.py

# Previous cloud-tested model-pipeline snapshot
FLOORHAWK_RELEASE="$PWD/../floorhawk-modal/releases/local-candidate" .venv/bin/modal deploy deploy/modal/app.py

# Disable live immediately; no new GPU work admitted
.venv/bin/python deploy/modal/manage.py disable

# Stop deployment/containers completely (destructive to running work)
.venv/bin/modal app stop floorhawk-demo --yes

# Recover only AFTER stopping and verifying no live owner
.venv/bin/python deploy/modal/manage.py recover-lock --confirm-app-stopped

# After redeployment and checks, enable from a passing report
.venv/bin/python deploy/modal/manage.py enable --verified-report ../floorhawk-modal/verification/cloud-smoke.json
```

Logs command streams until Ctrl+C; do not leave it running unattended. No laptop host worker is needed for the cloud URL. Laptop launchers remain unchanged.

## Persistence and limits

Weights are in `floorhawk-assets/a18a52dae0e7-3ec800c811f2`,28verified files/288554394bytes; no company drawings or gold data uploaded. `floorhawk-jobs` persists private source/jobs/evidence. `floorhawk-control-v1` persists atomic quotas, owners, idempotency and kill switches; no cross-container SQLite WAL.

One T4 worker,max1,min0,15s scale-down; bounded CPU/API max1,min0. Fresh processing per accepted request, shared extraction only within it. Existing frontend snapshot unchanged; cloud mutations/review editing disabled. Current cloud gallery intentionally empty because redistribution permission was not cleared. Upload your own permitted images.

Per event code:5accepted questions/300s,2distinct uploaded documents/300s (repeated questions on the same source do not consume another distinct-upload slot); one active request per visitor; maximum11active/queued total (one running,10waiting). Quotas persist across API redeploy/restart; poll requests do not consume them. `/api/allowance` returns remaining allowance/retry time to an authenticated visitor.

Bounds:20MiB source/28MiBencoded request; existing100MP ingestion bound;20PDFpages;10MiB/100kIFC entities. Worker480s and child420s. Existing tile budgets remain. Limits do not establish full-sheet completeness. Missing quota state fails closed. The five-question/queue upper bounds are focused-tested; deployed upload rejection and session protections were exercised. PDF/IFC/large-image inference was not cloud-tested.

Three smoke jobs reserved$0.75 conservatively, not settled actual billing; no further billable test loop remains. Existing deployment compute-reservation ceiling$7 plus margin is not a Modal hard-dollar cap. Check dashboard charges. Gemini lifetime limits remain unchanged; cloud integration disabled.

## Layout and releases

`proofplan/` is canonical source. `../floorhawk-modal/` contains generated snapshots/manifests/private files, outside Git. `current` points to `releases/local-verified`. Full assets/model hashes and frontend/API/config metadata are in each release.json. Browser storage/outputs are private external verification artifacts. See [RELEASE_WORKFLOW.md](RELEASE_WORKFLOW.md).

## Unified Hybrid release — current

Same stable URL now serves oneResult from sharedLocal+Gemini. Sourcea44e94f; Local rollback966248c preserved.66tests and normal-login PNG/PDF/IFCsmokes pass; these do not alter benchmark accuracy. Budget100USDtotal includinghistory, requestcap1000unchanged;30prepaidcloudpermits are part of the canonical ledger. [Current behavior, verification, operator commands and limits](UI_HYBRID_RELEASE.md). Earlier Local-only/Gemini-disabled sections are historical.
