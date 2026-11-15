# Morning handoff — FloorHAWK

Current event update: release d1ae1e2; presenter1/1,judges2/5,public2/5T4. No application cumulative dollar/query/permit gates; preserved historical accounting is not a current allowance. Sixworker parallelism, Gemini and residentreuse verified. [Current guide](docs/EVENT_OPERATIONS.md) and [verification](docs/EVENT_CAPACITY.md) supersede operational limits in older checkpoints below. Benchmark claims are unchanged.

Latest event-readiness pass: public15USDallocation/7.50USDreserved (~30admissions); real Gemini+visible evidence verified on all3roles; concurrent public jobs, idempotency, ownership and isolated peers passed. Publicoperational9cd9301; models/frontend/inferenceunchanged. [Current verification and limits](docs/EVENT_READINESS.md). Older accounting below is historical.

Academic Menaces · STOA — Make Blueprints Talk · Junction2026.

Campaign checkpoint 2026-11-15T07:29:04.583972+02:00. Optimization froze05:45:00.918Helsinki. Deployment and private submission were verified before07:00. Frozen final LocalCPU inference has now stopped; no final-reference tuning or provider calls. Intended event deployments remain available.

- Presenter: https://sm-hariprasanth--presenter.us-east.modal.run
- Judges/company: https://sm-hariprasanth--judges.us-east.modal.run
- Public: https://sm-hariprasanth--web.us-east.modal.run

Private repository: https://github.com/HariPrasanth-SM/floorhawk . Original private development repository remains intact. Initial submission4d3704d; later verified submission22706a1; final source/report commit is recorded in Git/SOURCE_RELEASE.json and campaign completion metadata. No public conversion, secrets, drawings, weights, raw sessions or bulk predictions were pushed.

Access files from canonicalproofplan/: `../floorhawk-modal/.secrets/presenter-access-code`, `judges-access-code`, `event-access-code`. Never paste their values. Presenter/public URLs are unchanged. Deployment `8fce90834c82935f6180baac8a7071763269b183`, frozen inference `5827eab5e423bae3eb7413a2c773183afa2f60f0`; only platform CPU/RAM hard limits changed later. Full model/config/frontend hashes: [release manifest](docs/release-manifest.json).

## Scores:85% not achieved

|Development result|Correct /9471valid numeric references|
|---|---:|
|Frozen v3 baseline|6641/9471(70.12%)|
|Local specialists|7205/9471(76.07%)|
|Best cached groupedOOF estimate|7925/9471(83.68%)|
|Practical serving policy estimate|7923/9471(83.66%)|

There are9544development questions/448drawinggroups;73narrative references remain ungraded. Best correct/all9544=7925/9544(83.04%). Practical answer coverage9179/9544(96.18%), countMAE0.484050,bias-0.250121,N8276; baselineMAE0.666586,bias-0.405379,N8254. Practical policy versus baseline:1428rescues,146regressions,6495unchangedcorrect,1402unresolved. These are cached development estimates, not fresh full cloud accuracy. No85%before04:30, so90%early-target escalation did not activate. [Development breakdown and visual count audit](docs/OVERNIGHT_DEVELOPMENT.md).

Final LocalCPU: recorded5602/6876(81.47%), 274/354drawinggroups(273uniquecontentcheckpoints). Correct/all eligible4214/6876(61.29%); correct/recorded subset4214/5602(75.22%). CountMAE0.473979,bias-0.240192,N4996. These partial LocalCPU results are not deployedHybrid accuracy. PDF no-known-local-overlap: 1106/1298(85.21%),recorded1298/1298. Unknown-custom-overlap PNG: recorded4304/5578; never certified unseen. TextN=0/N/A. [Exact final outcomes, coverage and provenance](docs/FINAL_EVALUATION.md).

## Verification and remaining limits

Frozen inference presenter18/18curated+4manual PNG/PDF/IFC; judges12/12+4manual; public1fresh question+20authenticated browsing contexts, not20GPUjobs. Resource-bound canary18/18; final roles each passed a further fresh question. Normal login, reference clearing, repeated/source-replaced questions, session ownership, idempotency, completed-job reopening/reload, transient polling retry, PNG/PDF exports and bothdesktop sizes passed. Real source-matched fzk107meshes/11windowGUIDhighlights, including manualIFCupload. Actual model input tensorscuda:0,734–736MiBGPUused and sampledactivity up to41%; all model load counters1 perresident.

Focused79+approved93tests with30overlap=142distinctpassed tests. Historical66/fiveerrors genuinely failed (Controls uninitialized`s`); later passes do not rewrite that failure. One later sandbox socket failure was covered by approved rerun. Full queue exhaustion/worker-crash injection and all public boundary limits were not exercised on serving apps. Pending-source replacement was not newly exhaustively browser-tested. New browser checks made0provider calls; successful semantic review on each new role is not claimed. [Verification](docs/OVERNIGHT_DEPLOYMENT_VERIFICATION.md), [all18curated outcomes](docs/GALLERY_OVERNIGHT_VERIFICATION.md).

Staging first cold27.67s included a polling fault;17warm requests median5.26s/range4.64–7.55s. Final resource-bound presenterdoor9.40s,judges14.19s,publiccold32.99s(withpollfault). Raw worker startup12.01–16.17s excluding platform startup. Not p95/fixed latency; cached retrieval is not cold inference.

## Usage and operation

Lifetime722recordedHTTPresponses+1unresolved reservation.384additional shared responses overnight; none during final browser/evaluation phase. Knowninput2957430/output392489tokens;thinkingunrecorded/26missingIOrecords. Partialknown token-priced subtotal2.9772555USD is not actual bill. Canonical90.317USDreservations already include80USDsharedallocation; shared15.505USDreserved,64.495USDreservable inside thatallocation. Historical dashboard143calls/0.48USD cannot be exactly reconciled without its billing window/lag. No reset/increase. [Accounting detail](docs/BUDGET_RECONCILIATION.md).

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

Pinned rollback to pre-resource inference release: selectrole with `campaign.operator --release ../floorhawk-modal/releases/overnight-candidate-4 --enable-live`, then `.venv/bin/modal deploy deploy/modal/app.py`. Original pre-campaign rollback snapshots remain intact. Safe fail-closed lock recovery, backend-only updates and originalrollback: [EVENT_OPERATIONS.md](docs/EVENT_OPERATIONS.md). Turning warming off permits future coldstarts; appstop fully stops execution.

## Recording and follow-up

Upload `$HOME/Junction 2026/floorhawk-modal/recording-assets/png-a.png`: windows2,doors4,sinks2. Upload `$HOME/Junction 2026/floorhawk-modal/recording-assets/pdf-a.pdf`: Schlafzimmerrooms2,room4.02area2.67m2,room4.03area3.93m2. Exact questions, observed fresh timings and repeats: [RECORDING_GUIDE.md](docs/RECORDING_GUIDE.md). OptionalmanualIFC`ifc-a.ifc`:windows11withrealrender. Dataset originals intact; copies remain outsideGit/publicexports.

Highest-value next improvement: audit true spatial door/window labels and instance recall/grouping on disjoint development drawings; correct scalar heads alone are not localization proof. No big vision training/newlarge model was performed overnight. Small developmentselectors/rejected alternatives are preserved. Final references must not guide a new candidate without explicitly reclassifying this evaluation as development.

[Architecture](docs/architecture.md) · [Current analytics](SOLUTION_ANALYTICS.md) · [Asset restore/licensing](ARTIFACTS.md) · [Append-only progress](docs/OVERNIGHT_PROGRESS.md). Full predictions/crops/metrics remain outsideGit. Task-owned inference/test processes stop by07:30; intended event deployments are excluded from campaign shutdown.
