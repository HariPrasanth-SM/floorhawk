# Company samples — unscored exploratory smoke

These are exploratory DEVELOPMENT sheets, not a scored test. No reference answers were supplied. Agreement does not prove correctness. Original source dimensions, byte sizes and hashes are recorded externally in results/samples25/sources.json; source/pixel identities are quarantined in config/exploratory-exclusions.json and honored by the future final-manifest builder. Original drawings/data were not changed or committed.

|Question|Source scope|Local|Hybrid|Coverage / limitation|
|---|---|---|---|---|
|1 Windows|Actual second-floor dormitory sheet, not a school|165 candidate windows|165 (unverified agreement)|54/54 source tiles; no claim of detection completeness or correctness|
|2 Printed room/wing area|Same dormitory|Untested|Untested|Stopped before this question; no room area invented|
|3 Suction-header diameter|Piping sheet|Literal OCR excerpts: HEADER; HEADER; 16" SUCTION HEADER|16"|12 distributed source OCR tiles, partial text coverage; citation needs human review|
|4 Labelled equipment types|Same piping sheet|Untested|Untested|No complete equipment inventory claimed|
|5 Slab/reinforcement notes|Slab sheet|Incomplete extraction; no completed answer|Not called|Stopped on stale host telemetry; source accepted, not inference success|
|6 Annotated region / reliable area|Same slab|Untested|Untested|No raster area, connectivity or construction rule inferred|

## Processing and actual device

All3 originals are PNGs: two10200×6600 (67.32MP) and one9934×7017 (69.707MP). Compressed bytes1,455,262 /1,264,730 /1,838,653 (exact source association in the external manifest). Original-resolution1536px tiles/20% overlap were processed sequentially with existing RT-DETR1024 preprocessing/confidence/class map.54 uncached worker forwards recorded **cuda:0 input tensors**, executing PID, model/weight provenance and GPU samples. Peak allocated GPU memory in these forwards: **352.59MiB**. GPU evidence is in results/samples25/gpu-forward.json, not inferred from CUDA availability. CPU OCR remains ONNX PP-OCRv5; tile boxes/text map through source offsets, then into display coordinates; original-resolution crops remain available.

Full detector grid coverage is not proof that every window was found or that non-windows were rejected. Class-aware overlap suppression prevents simple tile-count summation, but nearby/fractured detections remain a limitation. OCR12-region coverage is deliberately incomplete; no blank-region suppression was used. Gemini received an overview plus up to3 selected readable source crops/evidence, not every tile. Those selected crops are incomplete context, and proposed localizations remain unverified.

The first attempt was safely stopped at RAM78.74% (existing78% shedding threshold), with no completed question. The user freed memory (later39.48%). The recovery completed2 questions, then a stale host heartbeat stopped owned work. The temporary live server also stopped on stale telemetry. No safeguard/driver was disabled and no user process was killed. Live toggle/document-switch behavior was implemented but final real-browser interaction checks were blocked by that telemetry loss. A previous8776 demo was connection-refused and had no listening task server to stop.

## Cost, attempts and preserved results

2 actual HTTP attempts; **$0.024 reserved**, **$0.003283 token-priced estimate**, not settled billing. Shared ledger now249/1,000 and$8.973/$10 reserved; no reset/increase. These costs/answers remain separate from benchmark accuracy. Frozen v3 numeric development6,641/9,47170.12% and the16-case Local/Hybrid4/13 diagnostic remain unchanged.

Raw new results/evidence/crops/coverage/device/cache/timing records are outside Git under results/samples25 and cache/large-drawings. Stopped/partial attempts remain preserved. Detailed host/global resource telemetry is results/samples25/resources.jsonl. No full benchmark, training, model download, Modal deployment or external artifact upload was run.

## Remaining verification limits

All original uploads were checked through the actual ingestion route without claiming that validation is inference. Grid/offset/class/text dedup and original/display mapping have focused tests. Four questions are explicitly untested; full live switch/retry/toggle browser flows were not verified after the heartbeat failure. Per-tile calls are bounded by existing worker timeouts; tile dispatch budgets are checked between calls, so an active call can extend the stated dispatch budget. No verified annotated floor area is inferred from a printed scale ratio. User must restart the existing host worker to restore fresh telemetry before launching live again.
