# Verified event deployment — 15 November2026

All three URLs serve frozen source5827eab with the preserved frontend. Presenter: https://sm-hariprasanth--presenter.us-east.modal.run ; judges: https://sm-hariprasanth--judges.us-east.modal.run ; public: https://sm-hariprasanth--web.us-east.modal.run . Normal-login browser checks and actual model forwards passed. See [event operations](EVENT_OPERATIONS.md) and [verification](OVERNIGHT_DEPLOYMENT_VERIFICATION.md) for measured scope, access-file paths, warming, limits and shutdown. Cloud does not need the laptop host worker. One Result is selected from shared local evidence/optional Gemini review; recorded fallback is explicit. No competing cards or old assistance checkbox are used in the cloud UI.

LAPTOP commands below remain compatible; older notes describe their historical release/candidate behavior. No task-owned local demo server remains running. Replay still performs no inference/API calls. Current primary development estimate remains below85%; curated success is not held-out accuracy.

# Current live launcher and exploratory large drawings

From the canonical source parent: `bash proofplan/start_live.sh --port 8777`, http://127.0.0.1:8777 . This sets paired/large-drawing adapters while keeping Gemini assistance OFF by default. Existing default benchmark launcher remains unchanged. Host worker: `bash proofplan/start_host_worker_v2.sh` in normal terminal, one worker only. Preserve existing resource supervision and lifetime ledger.

Source originals are retained; previews are not the sole large-image inference input.1536px/20% overlap tiles,64/150s detector and12/90s OCR budgets; incomplete coverage never becomes a total count. Original evidence crops and transforms remain. A completed upload alone is not inference verification. Company sample outcomes are unscored in [samples-smoke.md](samples-smoke.md).

The temporary8777 server was actually launched and automatically stopped when host telemetry became stale. No task demo remains running at delivery. Restore the user-owned host worker heartbeat with the command above before launching again. Current replay command remains `bash proofplan/start_demo_v3.sh --replay --include-failures --port 8774`. Older command/reproduction context follows.

# Current demo commands

The canonical source is the existing `proofplan/` Git repository; no competing submission copy exists. Run these commands from its parent directory. Restore external assets/venv/results first; see ARTIFACTS.md and `.env.example`. Export optional path variables in the server shell; `.env.example` is documentation, not automatically loaded.

Default v3, unchanged model/routing policies:

```bash
bash proofplan/start_demo_v3.sh --mode local --port 8775
```

URL: http://127.0.0.1:8775 . This default-v3 startup/configuration check passed with paired=False and no inference/provider calls. All iteration-owned test services were stopped at delivery; launch when the port is free. Default without --port remains8765.

Existing host worker (normal Ubuntu terminal, only one):

```bash
bash proofplan/start_host_worker_v2.sh
```

URL: http://127.0.0.1:8766 . Endpoint configurable with PROOFPLAN_WORKER_URL, restricted to localhost. Original sampled GPU/resource admission and one inference lock remain. Cached CPU fallback is explicitly labelled; it is not current GPU execution.

Explicit opt-in paired candidate, actually tested:

```bash
PROOFPLAN_PAIRED=1 bash proofplan/start_demo_v3.sh --mode local --port 8773
```

URL: http://127.0.0.1:8773 . Upload PNG/JPEG/PDF/IFC, enter a question and Ask. Local makes no Gemini request. Selecting Hybrid saves/shows Local first, then adds a separate Hybrid answer panel. Original Local predictions/review boxes remain distinct from Hybrid proposals. `predictions.local.json`, `predictions.hybrid.json`, original response/paired metadata and review records are separate. Provider failure retains Local. Do not mistake unverified model-proposed regions for verified local evidence. IFC properties/GUID counts do not require geometry conversion.

Complete saved-result replay, actually tested:

```bash
bash proofplan/start_demo_v3.sh --replay --include-failures --port 8774
```

URL: http://127.0.0.1:8774 . No inference or provider initialization. Run/version/outcome/format filters retain all compatible saved runs, including failures. Ground truth stays in replay, never live inference. Analytics button serves the current-only report; full historical index remains available for inspection. The older sealed replay is preserved externally.

Tests:

```bash
cd proofplan
.venv/bin/python -m unittest tests.test_iteration test_qa test_v2 test_v3 test_demo_polish test_inspection test_geometry -q
```

`scripts/verify_iteration.py` performs a real Local upload and one paid paired upload; do not repeatedly rerun it unnecessarily. Existing run results are external under results/iteration60. No background experiment should be launched after the authorized cutoff. Servers are interactive services, not experiments; Ctrl+C stops foreground launchers.

Large raster uploads: images above30MP are resized to at most8MP/4096px for inference, with original file and coordinate transforms retained. Up to100MP source images supported; larger sources need manual resizing. File-size/resource limits remain. Results show a resize warning; evidence crops read the retained original. Restart the server after updating source.

Hybrid terminal responses: unsupported/abstained explanations remain visible even if the model also supplies an unnecessary invalid crop. Validation errors are distinct from API failures. PDF Local supports “How many corridors are there?” by exact controlled corridor/Korridor labels in the numbered room registry; it does not infer unlabelled corridors or assume complete extraction. Restart after source updates.

## First agile UI iteration

Existing launch commands remain: from parent, `bash proofplan/start_host_worker_v2.sh` once, then `bash proofplan/start_live.sh --port 8777`; open http://127.0.0.1:8777 . Restart the live backend to load changes. Gemini assistance defaults OFF; current workspace instructions require Local only. Cumulative multi-model provider policy is not promoted and defaults off. Clear drawing/question resets state; Ask needs both. A saved Hybrid request displays Hybrid first, with an explicit Local-output checkbox; unresolved replies remain labelled. Diagnostic ZIP exports source/query/separate outcomes without secrets/reference answers.

Verification used a temporary localhost8778 Local server and synthetic browser fixtures, without new API calls. See [iteration report](agile-hour1.md). Replay launch remains `bash proofplan/start_demo_v3.sh --replay --include-failures --port 8774`.

## FloorHAWK focused UI

See [frontend verification and commands](floorhawk-ui.md). Use `bash proofplan/start_live.sh --port 8777`; optionally add `--diagnostics`. Replay command remains compatible. Restart the backend to load saved-Hybrid evidence resolution and the top ZIP export.
