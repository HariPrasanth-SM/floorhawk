# Supplied floorplan detector audit and opt-in adapter

The user's existing `floorplan_detector/` contains a40,569,507-byte YOLO11m checkpoint, README and inference script. No weights/source were copied or trained. The adapter is `custom_detector.py`; source-only metadata is `config/custom-detector.json`. Runtime location may be set with `PROOFPLAN_CUSTOM_YOLO_WEIGHTS`, or restored under `PROOFPLAN_MODEL_ROOT/custom-yolo/floorplan_yolo11m.pt`; otherwise the existing sibling folder is reused.

## Verified identity and compatibility

SHA256: `95fd78b75b72f50963c03d710dbd38b9c7259e21e141c019f58ab7fbb57e54ea`.

CPU checkpoint loading under the existing advisory lock succeeded with the current Ultralytics8.3.40. No package upgrade or forward was needed for this check. The exported checkpoint records Ultralytics8.3.141, task detection and1024 input. Its epoch field is−1 (stripped export), so the README's epoch29 description cannot be independently confirmed from that field. Exact original training/validation membership manifests and conversion code were not supplied.

Actual checkpoint class identities/order were checked, not guessed:

|ID|Native class|Adapter class/count semantics|
|---:|---|---|
|0|electrical_appliance|Direct detection; no room claim|
|1|door|Direct fitted-door proposal; README excludes open doorways|
|2|bathtub|Direct bathtub; included in shower+bathtub count|
|3|shower|Direct shower; included in shower+bathtub count|
|4|window|Direct window proposal; pane fragmentation remains a risk|
|5|sauna_bench|Bench detection only, **not sauna-room count**|
|6|stairs|Canonical `stair` instance|
|7|toilet|Canonical `toilet_fixture` instance|
|8|sink|Direct sink; README says double bowl counts once|

The source inference defaults are retained exactly: confidence0.4, image size1024, NMS IoU0.7, max detections500, one image per forward. Ultralytics handles letterboxing and already returns boxes in original image pixels; the adapter does not scale those coordinates a second time. Source pixel boxes are range/finite/class validated and include model provenance. Existing default routes/weights/thresholds are unchanged; these facts are additional opt-in evidence or separate count proposals.

## APIs and caching

- `infer(file, device='cpu', acquire_lock=True)`: one admitted uncached forward; captures actual model-input tensor device, executing PID, parameter device, GPU allocation where applicable and separate model load/forward/total timings.
- `parse(file, device='cpu', use_cache=True)`: adds a cache keyed by source SHA, exact weight SHA, adapter SHA/version, author settings, installed library version and execution device. A cache hit is labelled; retained generation timings are not current inference speed.
- `answer(facts, target)`: separate supported-class count proposal, not an automatic baseline replacement. Unsupported targets return an explicit unsupported status.
- `release()`: unload the adapter model when the host controller switches GPU models.

CUDA execution is restricted to the existing authenticated host queue (`PROOFPLAN_IN_HOST=1`). The host call uses `infer(..., device='cuda:0', acquire_lock=False)` because the client already holds the advisory inference lock; arbitrary callers cannot skip it. The parent integration retains the single-GPU-job admission policy and controls model residency. Sources above30MP must use bounded original-resolution tiles rather than silently reducing a full large drawing.

## Training overlap, metrics and licence

The supplied README reports training on4,200 CubiCasa5K plans using converted SVG labels. Exact membership/identities are unavailable: overlap with the existing9,544-question DEVELOPMENT set or other CubiCasa-derived models is possible and cannot be certified absent. A previously group-clean final split is **not automatically untouched relative to this newly supplied model**; original training/project membership is required before that claim. No reserved final answers were read or evaluated here.

README validation detection metrics are mAP50.842/mAP50–95.597; its per-plan count metrics refer to epoch26 rather than the supplied epoch29 description. They are author-reported, not reproduced measurements in this integration, and must not be presented as held-out FloorHAWK accuracy. Window pane splitting, missing/common-area doorway conventions and non-Finnish/technical drawing domain shift remain explicit risks.

Treat the model as non-commercial, CubiCasa-derived CC BY-NC-SA4.0 per the supplied README; Ultralytics is AGPL-3.0. No broader checkpoint licence grant or commercial suitability is inferred. Preserve CubiCasa/Kalervo et al. attribution. The weight file remains outside Git and no external archive/upload is performed.

Verification performed by this subtask: actual CPU checkpoint class/metadata inspection, five pure contract tests (pixel mapping, class grouping, invalid values, class order and host-only CUDA guard). No real inference forward was performed by this subtask; parent-run host forwards and paired measurements are separate evidence.
