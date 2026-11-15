# Morning handoff — FloorHAWK

Academic Menaces · STOA — Make Blueprints Talk · Junction2026.

Checkpoint 2026-11-15T06:07:14.398390+02:00. Deployment/browser delivery is verified; private submission push is being finalized. Untouched evaluation has not started. This file will be updated after evaluation/07:30 shutdown.

## Three protected links

- Presenter: https://sm-hariprasanth--presenter.us-east.modal.run
- Judges/company: https://sm-hariprasanth--judges.us-east.modal.run
- Public: https://sm-hariprasanth--web.us-east.modal.run

Access files, relative to canonical proofplan/: `../floorhawk-modal/.secrets/presenter-access-code`, `judges-access-code`, `event-access-code`. Never record/commit their contents. Presenter/public URLs are unchanged. All use frozen source `5827eab5e423bae3eb7413a2c773183afa2f60f0`, frontend/model/config hashes in [release manifest](docs/release-manifest.json). Original rollback snapshots remain intact.

## Result —85% not achieved

Frozen development primary: baseline **6641/9471(70.12%)**; best cached/grouped out-of-fold estimate **7925/9471(83.68%)**. Practical serving-policy estimate **7923/9471(83.66%)**. All9544quick questions are DEVELOPMENT;73narrative text references remain ungraded. Best correct/all9544=7925/9544(83.04%); reference coverage9471/9544(99.24%). No claim of held-out85%,90%or95%.

Selected policy answer coverage9179/9544(96.18%); count MAE0.484050, signed bias-0.250121 on8276valid answered count outputs. Failed/abstained/unsupported remain in primary correctness. Compared with baseline:1428rescues/146regressions/6495unchangedcorrect/1402unresolved. No localization precision/recall is claimed. [Full development report](docs/OVERNIGHT_DEVELOPMENT.md), [current analytics](SOLUTION_ANALYTICS.md).

## Actually verified

Presenter18/18curated+4manual PNG/PDF/IFC; judges12/12curated+4manual; public1fresh live GPU question+20authenticated browsing contexts. Actual source-linked fzk model107meshes/11windowGUIDhighlights, including manual upload. Repeated/source-replaced questions, exact reference clearing, session isolation, idempotent job recovery, reload/poll retry without resubmission, PNG/PDF annotated export and bothdesktop sizes passed. No browser runtime errors. Models loaded once per role; actual CUDA input tensors and GPU memory/activity recorded.

Focused78test suite and approved93suite passed, with30overlap =>141unique tests. Earlier137combined run had one sandbox socket error, successfully covered by approved rerun. Full queue/crash injection and all public quota boundary cases were not repeated. Successful new semantic cloud review is not claimed from provider-free browser smokes; earlier preflight/provider variant generation and explicit Local fallback are separate evidence. [Verification](docs/OVERNIGHT_DEPLOYMENT_VERIFICATION.md).

## Timings and accounting

Staging cold query27.67s included an injected polling503;17warm staging queries median5.26s/range4.64–7.55s. Earlier clean candidate3cold browser25.21s. Model entrypoint startup12.10–13.98s; platform/API startup separate. Promoted per-question raw timings are in the verification report. No p95 claim from a small sample; cached development retrieval is not inference latency.

Lifetime read-only reconciliation:722HTTPresponses+1unresolved reservation; known input2957430/output392489tokens; thinkingunrecorded. Partialknown token-priced subtotal2.9772555USD is not final providerbilling. Canonical90.317USDreservations already include80USDsharedallocation. Sharedreserved15.505USD; no new browser provider calls. No reset or cap increase. Actual Modal invoice unavailable;8USDadditional campaign planning ceiling is conservative, not platformenforced.

**Public limitation:** retained7USDcumulative compute guard is5.50USDreserved, leaving six additional0.25USDadmissions. This does not reset with the five-minute visitor window. Presenter/judges are independent; use them for company/recording. No budget was silently raised.

## Record this

Upload PNG `$HOME/Junction 2026/floorhawk-modal/recording-assets/png-a.png`: windows2, doors4, sinks2. Upload PDF `$HOME/Junction 2026/floorhawk-modal/recording-assets/pdf-a.pdf`: Schlafzimmer rooms2, room4.02area2.67m2, room4.03area3.93m2. All freshly matched on the promoted presenter. Exact questions, observed times and sequence: [recording guide](docs/RECORDING_GUIDE.md). Optional manualIFC copy `recording-assets/ifc-a.ifc`:windows11withrealrender.

## Warm, inspect, off and stop

From canonical proofplan/:

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

Two intended warm T4 workers remain billable; public min0/max1. No laptop host worker is required for these URLs. [Deployment/update/rollback and lock recovery](docs/EVENT_OPERATIONS.md). The original presenter rollback module imported successfully; no disruptive serving rollback was performed after successful promotion.

## Final evaluation and next improvement

Answer-free audit:6876provisional questions/354groups;1298have no known local custom-training/dev overlap,5578CubiCasa questions have unknown4200-plan custom training membership. Pretrained/unknown near-alias overlap remains possible. Original split files are unchanged. Evaluation may begin only after matching verified private submission delivery, with no tuning based on results, and stops by07:30. LocalCPU fallback is explicit and may leave partial coverage; final score is not yet available.

Highest-value follow-up: verify spatial window/door annotations and instance grouping/recall on development sources, rather than trusting scalar count agreement or adding arbitrary model weights. Windows remain the largest residual error category; an absent class is not established as the sole cause.

System architecture: [architecture](docs/architecture.md). Asset checksums/restore: [ARTIFACTS](ARTIFACTS.md). Canonical source remains proofplan/; a private submission snapshot is not a second active backend fork. No supplied drawing, weight, credential, raw transcript or bulk prediction belongs in Git.
