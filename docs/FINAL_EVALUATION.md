# Frozen final LocalCPU evaluation

Generated 2026-11-15T07:29:04.583972+02:00. Frozen inference5827eab; deployment8fce908 changes only platform resource limits. No final-result tuning. This is **LocalCPU**, not a fresh cloud Hybrid score.

|Stratum|Correct / valid references|Recorded / eligible|Answered / eligible|Unique drawing groups in denominator|
|---|---:|---:|---:|---:|
|All eligible (missing remain incorrect)|4214/6876 (61.29%)|5602/6876|5384/6876|354eligible groups; see source coverage below|
|Recorded subset (partial, selection-biased)|4214/5602 (75.22%)|5602/5602|5384/5602|274eligible groups; see source coverage below|
|PDF: no known local training/dev overlap|1106/1298 (85.21%)|1298/1298|1234/1298|36eligible groups; see source coverage below|
|PNG: custom training membership unknown|3108/5578 (55.72%)|4304/5578|4150/5578|318eligible groups; see source coverage below|

Coverage: 273unique content-hash checkpoints; 274/354drawing groups recorded, 274fully recorded. One identical-byte alias shares a checkpoint; legacy completion flags are not group completeness. Questions5602/6876(81.47%). Missing1274are Not recorded, not fabricated predictions. Source processing order was deterministic, PDFfirst, then PNG; the recorded subset is not a representative random sample.

Outcomes across all eligible questions: `{"Abstained": 58, "Correct": 4214, "Incorrect": 1170, "Not recorded": 1274, "Unsupported": 160}`. Recorded execution statuses: `{"abstained": 58, "success": 5384, "unsupported": 160}`. Execution failures/recorded=0.00%; failures/all eligible=0.00%. Missing and abstained remain separate.

Count finite/unit-compatible answer error N=4996, MAE=0.473979, signed bias=-0.240192; undercounts766, overcounts384; within-one=93.84%. Error denominator excludes absent/non-numeric answers; primary denominator does not. No relative error against zero references.

|Quantity|Finite/unit-compatible error N|MAE|Signed bias|Units|
|---|---:|---:|---:|---|
|count|4996|0.473979|-0.240192|{"count": 4996}|
|area|388|1.496228|-1.493498|{"m2": 388}|
|length|0|N/A|N/A|{}|
|volume|0|N/A|N/A|{}|

All6876references are numeric:6460counts/416areas. Text/list metricsN/A(N=0); no semantic text correctness is invented. Original development retains73ungraded narrative references. Frozen unit normalization/fixed2%quantity tolerance and exact integral counts are unchanged.

|Recorded format|Correct / valid references|Recorded / eligible|Answered / eligible|
|---|---:|---:|---:|
|.pdf|1106/1298|1298/1298|1234/1298|
|.png|3108/5578|4304/5578|4150/5578|

No SVG/IFC/JPEG final-input questions exist in this manifest. PNGs are legitimate raster inputs, not SVG training annotations. All1298PDFquestions/36sources have no known local training/dev exposure; external pretrained overlap and unknown aliases remain possible. The5578PNGquestions/318CubiCasa sources have unknown4200-plan custom-training membership and are not certified held out. Original corrected manifests remain unchanged.

## Timing, resources and provenance

Runner wall elapsed seconds=4630.526555. Source processing calls: `{"n": 274, "sum": 4150.128057673013, "median": 16.060920443499526, "min": 0.00025801000083447434, "max": 33.369098844999826}`. Query elapsed including cached source reuse: `{"n": 5602, "median": 0.0037795694997839746, "min": 3.929999365936965e-07, "max": 26.45826673100055}`. Source preparation/model extraction cost is charged once per recorded source call, not once per translated question. Per-query cache retrieval is not cold inference. FirstCPUloading/forward smoke6.62s was combined; separate loading isN/A, not0. CPU/CUDA numerical differences remain possible.

Sampled resource summary: `{"n": 2050, "cpu_percent_max_sampled": 20.6, "ram_percent_max_sampled": 54.28546584259484, "disk_free_bytes_min_sampled": 94185738240}`. Recorder gaps over5seconds: `[{"after_epoch": 1794716862.2374008, "before_epoch": 1794719056.3219442, "seconds": 2194.084543466568}]`. The telemetry-only recorder stopped and resumed; no gap was backfilled. The distinct inference launcher/admission stayed active. These samples do not guarantee an instantaneous utilization ceiling.

Provider attempts: 0. Runner terminal state: `{"status": "stopped", "returncode": 1, "reason": null, "finished": "2026-11-15T07:27:57.222033+02:00"}`. Source checkpoints are atomic and resumable; no new task may start beyond07:30. Every final prediction is linked to source SHA and frozen revision.

Separate evaluator inputs/outputs remain outside Git under `results/overnight-20261115/`: `final-eligibility/questions.jsonl`, owner-only `evaluation-only/final.answers.jsonl`, `final-local/predictions.from-source-checkpoints.jsonl`, `final-local/metrics/*/{score.json,rows.jsonl}` and `final-local/final-summary.json`. Per-format/task/target/source/language/route/evidence tables are in each scoreJSON. References are never mounted as inference inputs.

Reproduce only reporting after inference stops: `.venv/bin/python -m campaign.report_final`. It refuses a running inference task, checks the unchanged grader and reconstructs actual rows from atomic source checkpoints without overwriting original predictions. Source hashes:

```json
{
  "questions": "af1f6f7865830f4e440dafff9611e5ceaf0655db3e76bd2a1449f1b34e4a6d62",
  "answers": "f701cc16f5078ece81b269c264a877b71c72b013a92df0b91a1b030437507215",
  "predictions": "62dbc13ee661cfef857d5c959cb8c80e76da948e98c5dd81a0d53476091bf1f2"
}
```
