# Morning handoff — FloorHAWK

Academic Menaces · STOA — Make Blueprints Talk · Junction2026.

Campaign checkpoint 2026-11-15T07:29:04.583972+02:00. Optimization froze05:45:00.918Helsinki. Deployment and private submission were verified before07:00. Frozen final LocalCPU inference has now stopped; no final-reference tuning or provider calls. Intended event deployments remain available.

- Presenter: https://sm-hariprasanth--presenter.us-east.modal.run
- Judges/company: https://sm-hariprasanth--judges.us-east.modal.run
- Public: https://sm-hariprasanth--web.us-east.modal.run

Private repository: https://github.com/HariPrasanth-SM/floorhawk . Original private development repository remains intact. Initial submission4d3704d; later verified submission22706a1; final source/report commit is recorded in Git/SOURCE_RELEASE.json and campaign completion metadata. No public conversion, secrets, drawings, weights, raw sessions or bulk predictions were pushed.

Access files from canonicalproofplan/: `../floorhawk-modal/.secrets/presenter-access-code`, `judges-access-code`, `event-access-code`. Never paste their values. Presenter/public URLs are unchanged. Deployment `8fce90834c82935f6180baac8a7071763269b183`, frozen inference `5827eab5e423bae3eb7413a2c773183afa2f60f0`; only platform CPU/RAM hard limits changed later. Full model/config/frontend hashes: [release manifest](release-manifest.json).

## Scores:85% not achieved

|Development result|Correct /9471valid numeric references|
|---|---:|
|Frozen v3 baseline|6641/9471(70.12%)|
|Local specialists|7205/9471(76.07%)|
|Best cached groupedOOF estimate|7925/9471(83.68%)|
|Practical serving policy estimate|7923/9471(83.66%)|

There are9544development questions/448drawinggroups;73narrative references remain ungraded. Best correct/all9544=7925/9544(83.04%). Practical answer coverage9179/9544(96.18%), countMAE0.484050,bias-0.250121,N8276; baselineMAE0.666586,bias-0.405379,N8254. Practical policy versus baseline:1428rescues,146regressions,6495unchangedcorrect,1402unresolved. These are cached development estimates, not fresh full cloud accuracy. No85%before04:30, so90%early-target escalation did not activate. [Development breakdown and visual count audit](OVERNIGHT_DEVELOPMENT.md).

Final LocalCPU: recorded5602/6876(81.47%), 274/354drawinggroups(273uniquecontentcheckpoints). Correct/all eligible4214/6876(61.29%); correct/recorded subset4214/5602(75.22%). CountMAE0.473979,bias-0.240192,N4996. These partial LocalCPU results are not deployedHybrid accuracy. PDF no-known-local-overlap: 1106/1298(85.21%),recorded1298/1298. Unknown-custom-overlap PNG: recorded4304/5578; never certified unseen. TextN=0/N/A. [Exact final outcomes, coverage and provenance](FINAL_EVALUATION.md).

## Verification and remaining limits

Frozen inference presenter18/18curated+4manual PNG/PDF/IFC; judges12/12+4manual; public1fresh question+20authenticated browsing contexts, not20GPUjobs. Resource-bound canary18/18; final roles each passed a further fresh question. Normal login, reference clearing, repeated/source-replaced questions, session ownership, idempotency, completed-job reopening/reload, transient polling retry, PNG/PDF exports and bothdesktop sizes passed. Real source-matched fzk107meshes/11windowGUIDhighlights, including manualIFCupload. Actual model input tensorscuda:0,734–736MiBGPUused and sampledactivity up to41%; all model load counters1 perresident.

Focused79+approved93tests with30overlap=142distinctpassed tests. Historical66/fiveerrors genuinely failed (Controls uninitialized`s`); later passes do not rewrite that failure. One later sandbox socket failure was covered by approved rerun. Full queue exhaustion/worker-crash injection and all public boundary limits were not exercised on serving apps. Pending-source replacement was not newly exhaustively browser-tested. New browser checks made0provider calls; successful semantic review on each new role is not claimed. [Verification](OVERNIGHT_DEPLOYMENT_VERIFICATION.md), [all18curated outcomes](GALLERY_OVERNIGHT_VERIFICATION.md).

Staging first cold27.67s included a polling fault;17warm requests median5.26s/range4.64–7.55s. Final resource-bound presenterdoor9.40s,judges14.19s,publiccold32.99s(withpollfault). Raw worker startup12.01–16.17s excluding platform startup. Not p95/fixed latency; cached retrieval is not cold inference.

## Usage and operation

Lifetime722recordedHTTPresponses+1unresolved reservation.384additional shared responses overnight; none during final browser/evaluation phase. Knowninput2957430/output392489tokens;thinkingunrecorded/26missingIOrecords. Partialknown token-priced subtotal2.9772555USD is not actual bill. Canonical90.317USDreservations already include80USDsharedallocation; shared15.505USDreserved,64.495USDreservable inside thatallocation. Historical dashboard143calls/0.48USD cannot be exactly reconciled without its billing window/lag. No reset/increase. [Accounting detail](BUDGET_RECONCILIATION.md).

Modal actualinvoice unavailable; additional campaign planning ceiling8USD was not platformenforced. Intended warm pair estimated1.497312USD/hour at published baseGPU/CPU/RAMrates beforeAPI/network/adjustments. Presenter/judges remain warm/billable; publicmin0/max1. Public preserved7USDcompute guard has5.75USDreservations, leaving five0.25USDadmissions, separate from rolling quotas. Use presenter/judges for recording.

From canonicalproofplan/:

```bash
.venv/bin/python deploy/modal/presenter_ops.py warm
.venv/bin/python deploy/modal/presenter_ops.py ready
.venv/bin/python deploy/modal/presenter_ops.py status --admission --budget
.venv/bin/python deploy/modal/presenter_ops.py warm --app floorhawk-judges
.venv/bin/python deploy/modal/presenter_ops.py off
.venv/bin/python deploy/modal/presenter_ops.py off --app floorhawk-judges
.venv/bin/modal app stop floorhawk-presenter --yes
.venv/bin/modal app stop floorhawk-judges --yes
.venv/bin/modal app stop floorhawk-demo --yes
```

Pinned rollback to pre-resource inference release: selectrole with `campaign.operator --release ../floorhawk-modal/releases/overnight-candidate-4 --enable-live`, then `.venv/bin/modal deploy deploy/modal/app.py`. Original pre-campaign rollback snapshots remain intact. Safe fail-closed lock recovery, backend-only updates and originalrollback: [EVENT_OPERATIONS.md](EVENT_OPERATIONS.md). Turning warming off permits future coldstarts; appstop fully stops execution.

## Recording and follow-up

Upload `$HOME/Junction 2026/floorhawk-modal/recording-assets/png-a.png`: windows2,doors4,sinks2. Upload `$HOME/Junction 2026/floorhawk-modal/recording-assets/pdf-a.pdf`: Schlafzimmerrooms2,room4.02area2.67m2,room4.03area3.93m2. Exact questions, observed fresh timings and repeats: [RECORDING_GUIDE.md](RECORDING_GUIDE.md). OptionalmanualIFC`ifc-a.ifc`:windows11withrealrender. Dataset originals intact; copies remain outsideGit/publicexports.

Highest-value next improvement: audit true spatial door/window labels and instance recall/grouping on disjoint development drawings; correct scalar heads alone are not localization proof. No big vision training/newlarge model was performed overnight. Small developmentselectors/rejected alternatives are preserved. Final references must not guide a new candidate without explicitly reclassifying this evaluation as development.

[Architecture](architecture.md) · [Current analytics](../SOLUTION_ANALYTICS.md) · [Asset restore/licensing](../ARTIFACTS.md) · [Append-only progress](OVERNIGHT_PROGRESS.md). Full predictions/crops/metrics remain outsideGit. Task-owned inference/test processes stop by07:30; intended event deployments are excluded from campaign shutdown.


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
