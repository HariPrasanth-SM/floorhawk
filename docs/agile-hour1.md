# First agile iteration — 2026-11-14

Candidate work began16:11:21UTC with a one-hour maximum. Cloud work was stopped after the newly supplied local-only AGENTS instruction. No experiment remains running; the user-owned GPU host worker is preserved. Existing default answer/model policy is retained. Cumulative evidence is explicitly opt-in (`PROOFPLAN_HYBRID_EVIDENCE_V3=1`), not promoted on a small development gain.

## Measured diagnostic results

Selection was frozen before inference/scoring:32 English development questions,10 source groups,28 numeric and4 text;20 CubiCasa opening/fixture questions,8 Swiss-PDF door/area questions,4 IFC property questions. No references entered inference. This is a deliberately stratified diagnostic sample, not representative or held-out accuracy. Supplied custom YOLO training membership is unknown; CubiCasa overlap is possible.

| Candidate | Numeric correct / manifest | Recorded questions | Notes |
|---|---:|---:|---|
| Existing Local |18/28 (64.29%)|32/32|29 answered;3 unsupported;1 answered text ungraded|
| Custom YOLO on supported raster targets + unchanged native routes |21/28 (75.00%)|32/32|3 rescues,0 regressions versus Local|
| Interrupted Hybrid |14/28 (50.00%)|28/32|Four absent outcomes retained; not a complete paired comparison|

On the24 numeric questions actually recorded in both Local/Hybrid: Local16/24, Hybrid14/24;0 rescues,2 regressions,14 unchanged correct,8 unresolved/wrong. Raw Hybrid includes24 successes,3 unsupported and1 schema-validation failure; the failed proposal retains Local as explicitly labelled fallback. Successful execution is not correctness. Text outcomes remain separate: four text questions, no graded text outputs. Do not claim95% accuracy or global improvement.

Count MAE among valid count outputs: Local1.667 (24), custom1.375 (24), interrupted Hybrid0.909 (22). Different valid-output denominators prevent interpreting MAE alone as a better overall system. Current frozen full-dev numeric baseline remains6641/9471 (70.12%); previous16-case comparison remains4/13 in each mode.

External reproducible artifacts: `results/agile1/experiment/{selection.json,questions.jsonl,local.predictions.jsonl,custom.predictions.jsonl,hybrid.predictions.jsonl,score.json,scored-rows.jsonl}`. Source and scorer/configuration hashes are recorded there. Regenerate scoring only after inference is stopped: `.venv/bin/python scripts/agile_score.py --inference-complete`. Inputs and original results are not overwritten. The interrupted run must not be resumed after scoring against these exposed references.

## Implementation

The supplied nine-class YOLO11m checkpoint has an explicit adapter, class mapping, weight SHA256 and provenance/license caveats in [custom-detector.md](custom-detector.md). Host execution uses the existing single-GPU worker/lock and releases models when switching. Bench detections are not sauna-room counts. No weights are copied into Git.

Opt-in cumulative evidence retains native facts, existing detector/OCR outputs, custom-YOLO hypotheses and local alternatives separately. Evidence IDs and source regions preserve origins; bounded provider context reports omitted regions. A structured review can disagree or abstain, but is never an oracle for selecting the correct answer. Cached outputs are keyed by source/weights/settings; answer caches also include question/context/prompt version. No generic embedding cache is claimed to replace extraction.

The shared UI displays Hybrid first for a submitted Hybrid request, with an explicit Local-output checkbox. Provider failure preserves Local; genuine abstention remains visible. Evidence shows recorded method/model and Hybrid citations. Clear drawing/question controls and Ask gating prevent incomplete requests. Diagnostic ZIP includes bounded original source, query, separate Local/Hybrid outputs, reviewed state and annotated Local evidence; reference answers, credentials and raw provider prompts are omitted. Exports containing user drawings remain private files for the user to handle.

## Resource and cost observations

Actual uncached custom YOLO host forward recorded CUDA tensor devices `cuda:0`, peak allocated328,530,432bytes. Smoke artifact: `results/agile1/custom-yolo-gpu-smoke.json`. Fresh host telemetry later showed596MiB GPU use/46% utilization, RAM45.4%; this is a sampled observation, not attributable entirely to a particular query. Native PDF/IFC and OCR remain CPU. Existing monitored limits and one-GPU queue remain.

Before this run the lifetime ledger was265 requests/$9.165 reserved. At stop it was295/$9.525:30 attempts/$0.360 additional reservation, unchanged1000/$10 caps, $0.475 remaining reserved allowance. Reservations are conservative bounds, not dashboard billing. Historical dashboard observation143calls/$0.48 is neither overwritten nor treated as a settled total for this run. Recorded30 generations contain148,376 input and9,932 output tokens: known input/output price estimate $0.051992. Thinking usage is unknown for all30, so this is not a complete or settled bill; the $0.360 reservation remains. Lifetime outstanding status includes one pre-existing $0.020 reservation, retained unchanged. Accounting is saved in `results/agile1/accounting.json`; zero in an aggregation is not evidence of free usage. No new API calls are authorized by the current local-only instructions.

Local timings predominantly reused existing document/model caches. Recorded Local end-to-end median0.174s/p9512.477s; additional Hybrid median3.148s/p9557.812s includes rate waiting. These are not cold model benchmarks. Shared preprocessing remains reported separately.

## Limits and next step

The target80%Local/90–95%Hybrid was not reached. Keep the candidate unpromoted. The highest-value next experiment is a preselected evidence audit of the remaining fixture errors and the two Hybrid regressions, followed by a new frozen diagnostic set and explicit cloud authorization if wanted. No training, new large downloads, paid compute or final evaluation was performed. Existing Qwen is available; Gemma/FloorplanVLM/DINOv2 additions were not justified within this window. See [model-options-hour1.md](model-options-hour1.md).

## Verification delivered

93 regression tests and6 additional cumulative-evidence tests pass. Synthetic browser fixture21checks and a real Local-only image upload/export/repeated-request check pass, without browser errors or page overflow at1366×768 and1920×1080. The real check confirms the budget ledger did not change, the repeated request reused the document bundle, clear drawing removed stale state, and diagnostic ZIP contained source.png/local-evidence.png/diagnostic.json. Fresh recorded replay browser loading and diagnostics also passed both sizes with no browser errors and an empty inference-module list. No claim of fresh inference from cached retrieval.

The one schema failure was an answered proposal without recorded evidence references. It was rejected rather than inventing support. The three IFC unsupported outcomes report missing properties/task data; no geometry render or fallback count was substituted.
