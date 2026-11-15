# Overnight event deployment verification

Verified 2026-11-15T06:03:25.830248+02:00. Frozen source `5827eab5e423bae3eb7413a2c773183afa2f60f0`; identical frontend `a111edce02bc2803837609cf4b15bfc19d3ee1e9ff2f003826aa2a2c49aafae8` and configuration on all three roles.

|Role|Actual URL|Curated matches|Manual upload questions|GPU worker|
|---|---|---:|---:|---|
|presenter|https://sm-hariprasanth--presenter.us-east.modal.run|18/18|4|71da5a9cf6a74737aafe3a3f8052a661|
|judges|https://sm-hariprasanth--judges.us-east.modal.run|12/12|4|c89382aee18c4b9baefa7013505663ad|
|public|https://sm-hariprasanth--web.us-east.modal.run|1/1|0|67f7e2afcaa04b49ba13caabd4c77e88|

Normal code login, source/question association, exact reference clearing, fresh answers, source evidence, session ownership, duplicate-key job recovery, reload without inference resubmission, transient polling retry, annotated PNG/PDF export and1366×768/1920×1080layout checks passed. No browser runtime errors were recorded. Presenter/judges IFC:107source-linked meshes and11recorded window GUID highlights, including manually uploaded IFC. The other IFC source never received a substitute fzk mesh.

Models loaded once per worker: CubiCasa1, RT-DETR1, OCR1, customYOLO1. Distinct worker identities and independent role queues were exercised concurrently. Model startup verified28existing asset hashes plus custom checkpoint/selector hashes. Actual executing CUDA tensor devices and sampled GPU memory/activity are retained in private job JSON. PDF/IFC parsing and OCR remainCPU.

The isolated provider-disabled candidate returned explicit Local fallback with0provider attempts; the corrected test checks the status rather than replacing the singleResult heading. The earlier wrong-heading assertion remains recorded as a test failure, not hidden. No paid API call was needed for deployment browser checks. A successful new semantic review in these newly deployed roles has not been measured; earlier preflight generation/model-variant observations remain separate.

Public:20simultaneously authenticated browser contexts fetched the gallery; one live GPU job only. Real overlapping same-visitor submission received429. Duplicate key returned the same job and no second admission. This is not a20GPU-load or maximum-throughput measurement. Five-question/two-upload/queue upper bounds remain focused-tested; full deployed boundary exhaustion/crash injection was not repeated to preserve serving allowance.

## Timings

|Role|Warm-model browser N|Median seconds|Range seconds|
|---|---:|---:|---:|
|presenter|18|7.84|6.30–11.92|
|judges|12|8.27|6.69–11.94|

Public first cold browser query30.45s included a deliberate transient polling503 test. Staging candidate4 first cold query27.67s also included that fault;17subsequent warm queries median5.26s/range4.64–7.55s. Earlier candidate3 clean first cold browser query25.21s. These are selected raw runs, not p95 or a fixed latency promise. Worker entrypoint initialization was12.10–13.98s, separately from API/image scheduling. Queue+API delay is combined in records; evidence/export generation is not independently timed for every route.

## Budgets and resource limits

No lifetime ledger/history reset. Canonical reservations90.317USD already include the80USD shared envelope. Last reconciliation:722HTTPresponses+1unresolved reservation; knownIO2957430/392489tokens; thinking unrecorded. Known token-priced subtotal2.9772555USD is partial, not actual billing. Shared envelope reservation15.505USD; no new browser provider calls.

Two intended warm T4 workers remain billable (presenter/judges). Public min0/max1. Per-workerGPU memory fraction60%, CPUthreads2, RAM8GiB requested (the original integer request was not a hard bound), sequentialGPU requests and sampled admission retained; sampled utilization does not guarantee an instantaneous80% ceiling. Additional overnight compute is conservatively expected below the8USD planning ceiling; actual Modal invoicing is unavailable and this is not a platform dollar cap.

Public cumulative compute guard remains7USD; after one verification job its conservative reservations are5.75USD, leaving five further0.25USD admissions. It does not reset on the rolling visitor window. Use presenter/judges for the event recording/company demonstration. Raising/reconciling that guard requires explicit operator review; no budget was silently increased or reservation history deleted.

## Tests and preservation

Focused discovery79passed; approvedexisting suite93passed;30overlap means142unique tests, not172. Earlier combined137 run had one sandbox socket creation error; the approved rerun covered that assertion successfully. A separate initial command-line invocation had an argument error and is not a passed test run. Original split/reference/baseline/model hashes remain unchanged. Source history scan536blobs found no credential pattern.

Historical66tests/fiveerrors was a genuine failed run: an uncommitted Controls default referenced `s` before assignment. It was fixed before a later66-pass run; [the presenter record](PRESENTER_DEPLOYMENT.md) preserves the cause and subsequent70-test log. The current79/93successful suites are new evidence, not retroactive claims that the failed run passed.

CPU fallback development smoke used a real recording PNG:2sinks, observedCPUtensor forward,6.62s combined first loading/inference. Its raw model_loading_seconds0 is not a separately measured loading duration; report that substageN/A. No final answers were opened for this smoke.

Private raw browser/job/crop/export evidence: `../floorhawk-modal/verification/overnight-{presenter,judges,public}/`. Version/model metadata: [release manifest](release-manifest.json). Operations/rollback: [event operations](EVENT_OPERATIONS.md).


## Resource-only deployment verification — 2026-11-15T06:49:23.379965+02:00

All three unchanged URLs now serve deployment source `8fce90834c82935f6180baac8a7071763269b183` with frozen inference base `5827eab5e423bae3eb7413a2c773183afa2f60f0`. Only Modal resource declarations changed after optimization freeze: GPU worker2CPU cores/8192MiB and API1CPU core/4096MiB use explicit request/limit tuples. Original integer values were requests, not guaranteed hard limits; this correction is not model tuning. The frontend, model weights, preprocessing, thresholds, router and graders remain frozen.

Canary repeated all18curated questions (18matches), source-matched IFC107meshes/11windowGUIDhighlights, provider-disabled fallback, session ownership, reload/idempotency/poll retry and bothdesktop layouts. Every model loaded once. Final presenter/judges/public each passed a fresh doorcount4 with4evidenceboxes through normal login, ownership and reload checks, zero browser errors and0provider calls. Raw times:presenter9.40s,judges14.19s,public32.99s(cold+injectedpoll503). No throughput/p95 claim. Private reports: `floorhawk-modal/verification/overnight-*/resource-*/report.json`.

Presenter/judges are intentionally warm,max1T4 each;public min0,max1. Current public compute reservations5.75USD/7USD leave five0.25USDadmissions, independent of rolling visitor quotas. No accounting was reset. Focused79+existing93 with30overlap=142distinctpassed tests; source/artifact checks remain separate.

At published base rates, T4+2requested CPU cores+8GiB is approximately0.748656USD/hour per resident worker, or1.497312USD/hour for the intended pair, before API/network/region/tax adjustments. This is an estimate, not measured invoice or a hard-dollar cap. See [Modal pricing](https://modal.com/pricing) and [resource request/limit semantics](https://modal.com/docs/guide/resources). Warm resources remain billable until explicitly turned off.
