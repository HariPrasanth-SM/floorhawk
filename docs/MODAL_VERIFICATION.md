# FloorHAWK cloud verification — 14 November 2026

## Result

Protected Local demo verified and enabled at **https://sm-hariprasanth--web.us-east.modal.run**.

Deployed source release: `966248c9a121e881882febd0deef53cc282a09d0` (`local-verified`). Stable app: `floorhawk-demo`, workspace `sm-hariprasanth`. Gemini disabled; its secret is not mounted. Cloud image explicitly Python3.11, torch2.6/cu124; remote functions use source imports with serialized=False. Local SDK interpreter3.10 emits a deprecation warning; this is not the cloud interpreter.

## Actual checks

|Check|Observed result|
|---|---|
|Existing asset verification|All28 remote files match exact SHA256 and size;288554394bytes; reused existing Volume|
|Protected browser upload→Local answer→crop|Pass,3 accepted jobs on2PNG sources|
|Same image, second question|Windows7 then doors5; both fresh jobs,7/5 evidence regions|
|Different image|Windows4,4 evidence regions; selection/crop replaced|
|CUDA execution|CubiCasa and RT-DETR forward-input tensors cuda:0; RT-DETR parameter device cuda:0|
|Peak allocation|CubiCasa up to251209216bytes; RT-DETR369708544bytes|
|Live performance note|Entire3-job browser smoke86.28s, includes upload/provisioning/UI; not a benchmark|
|Duplicate requests|Identical explicit idempotency key returns the same job ID; no duplicate GPU dispatch|
|Unauthenticated access|Landing login available; config/jobs protected with401|
|Two authenticated sessions|Second session cannot read first session's job:404|
|Deployed upload rate|Third distinct upload rejected429; two remaining questions/zero remaining uploads at that observation|
|Reload|Existing job reopened without new submission|
|Reference isolation|No reference card in Local live; no evaluation answers sent|
|Local-only provider use|Shared Gemini ledger unchanged during smoke|
|Viewport/browser|1366×768 and1920×1080 fit; no page errors|
|Backend-only update|Frontend SHA and URL unchanged; model-worker/pipeline source identical; old jobs remain accessible|
|Final admission|live=true,gemini=false,lock absent,active jobs0|
|Local tests|62 focused/regression tests pass; includes6 deployment-control tests|

Smoke outputs are **unscored exploratory results**, not accuracy or localization ground truth. Only PNG inference was exercised. PDF/IFC/large-sheet paths and full queues were not cloud-tested. Five-question and eleven-active/ten-waiting caps have focused tests/code inspection; the deployed third-upload limit was exercised. No deliberate cloud-worker crash was induced. Crash recovery remains manual/fail-closed and is documented below.

External detailed artifacts: `floorhawk-modal/verification/cloud-smoke.json`, `job-0.json` through `job-2.json`. These include original predictions/execution evidence and must not be committed. Snapshot manifests are in `floorhawk-modal/releases/*/release.json`; model manifest is `floorhawk-modal/assets.json`.

## Timing and resource interpretation

Each accepted job starts an isolated process with a fresh extraction-cache directory. Within that job the shared evidence preparation and answer can reuse facts; therefore a final Local answer's cache_hit=true can describe **within-request reuse**, not a prior-request answer cache. The actual forward events are cache_hit=false, with source hashes/tensor-device proof saved.

GPU maximum1/minimum0,scaledown15s; worker480s/subprocess420s. CPU/API maximum1/minimum0. Parsing and OCR run on CPU within the GPU job process; CPU parsing is not independently scheduled yet. IFC geometry rendering is disabled in cloud live; properties do not require meshes.

Three jobs reserved $0.75 conservatively in the deployment's compute counter. No GPU test launched beyond these three. This is not settled billing; T4/CPU runtime and storage charges require the Modal dashboard. Additional task testing was bounded far below the authorized approximate$5 estimate. The existing global deployment reservation ceiling remains$7 with a margin, not a platform-enforced hard-dollar cap. No plan changes or credit purchases.

## Recovery

Admission uses atomic Modal Dict put(skip_if_exists=True), not unsafe counter get/set or shared SQLite. A crashed lock owner has no automatic lease expiry: live admissions fail closed until recovery. Worker subprocess failure normally marks a failed job and releases active admission. Parent/container interruption can leave an orphan; do not automatically unlock a potentially live owner.

First disable/stop the app, verify it is stopped, then run manage.py recover-lock. The helper checks actual Modal app description/state and refuses while floorhawk-demo is active. It marks orphaned control records execution_error, preserves spend/event history, disables live/Gemini and keeps saved prediction files. The gateway reports interrupted orphan jobs honestly. Recovery was unit/code-inspected, not exercised by intentionally crashing a paid worker.
