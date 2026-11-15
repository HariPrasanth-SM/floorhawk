# Current event deployment8fce908 — frozen inference5827eab

The current actual workflow is [event operations](EVENT_OPERATIONS.md), with [verified deployment results](OVERNIGHT_DEPLOYMENT_VERIFICATION.md) and [release/model manifest](release-manifest.json). All roles use the same source/config/frontend, separate admission/jobs/GPU workers, and the shared80USD provider envelope already inside the100USD authorization. Old permit/1000request descriptions below are historical and do not govern the new event workers. Presenter/judges warming remains billable; public retains its7USD compute guard.

Backend-only snapshot export preserved frontend SHA256a111edce02bc2803837609cf4b15bfc19d3ee1e9ff2f003826aa2a2c49aafae8 and endpoint URLs across actual staging/promotions. `assets.json` is included and28remote assets verified. Rollback construction was imported successfully from the original presenter snapshot; no serving rollback was unnecessarily performed after successful promotion.


The private submission has its own sanitized Git history. Canonical deployment hashes such as8fce908 are provenance identifiers and are not necessarily Git objects in that new repository. `SOURCE_RELEASE.json` records canonical revision and per-file hashes. For a fresh submission clone, export its explicit own commit (`git rev-parse HEAD`) after restoring external manifests/assets; verify frontend/model/config hashes against the recorded release. For byte-identical rollback use the retained canonical repository and pinned operational snapshot. Do not pretend the new snapshot contains the canonical historical commits or duplicate an active backend fork.

## Historical deployment record

# Pinned release workflow

Canonical source is proofplan/. Operational snapshots are outside Git in floorhawk-modal/releases/. Never export a moving tree.

Full: `.venv/bin/python deploy/modal/export_release.py --commit COMMIT --output ../floorhawk-modal/releases/NAME`.
Backend only: add `--mode backend --frontend ../floorhawk-modal/releases/PREVIOUS`. Exporter checks API contract and preserves web bytes/hash. Local tests cover this; cloud update/rollback not executed.
Assets: `.venv/bin/python deploy/modal/assets.py --manifest ../floorhawk-modal/assets.json --upload`; only missing versioned paths are uploaded. Do not overwrite active weights. Manifest includes hashes/size/license caveats. Current uploader was fixed after initial snapshot; use current canonical script.
Deployment requires selected release at floorhawk-modal/current and assets.json copied into it. Initial assets/model metadata were attached manually after export; fully automated manifest assembly remains unfinished. `FLOORHAWK_RELEASE` selects a pinned release. `.venv/bin/modal deploy deploy/modal/app.py` uses stable app name floorhawk-demo; `FLOORHAWK_APP_NAME=floorhawk-candidate` selects a candidate. Candidate promotion/URL stability and cloud rollback are unverified. Rollback is redeploying previous source/asset manifest, not a claimed paid native feature.

Disable live/Gemini in floorhawk-control-v1 under its atomic admission lock; stop all paid services with `.venv/bin/modal app stop floorhawk-demo`. Do not remove a stuck lock until its owner is verified dead. Keep lifetime Gemini accounting external and disabled until safe shared reservation integration is complete. Source commits are private; no secrets/artifacts in Git.

## Verified protected Local release — 14 November 2026

Current deployed snapshot: `../floorhawk-modal/releases/local-verified`, source966248c. Previous model-pipeline-tested snapshot: `releases/local-candidate`, source517ef6d. Both use frontend SHA2569ed412c6b8ccc6e275768c34fb2283d08e47919a7a3a6d7a5efbc64d1bcfc441. Actual endpoint remained https://sm-hariprasanth--web.us-east.modal.run across backend updates. Old jobs remained readable. Remote hashes for all28assets passed; actual T4 inference and protected browser checks passed. See MODAL_VERIFICATION.md. Earlier statements that cloud verification is wholly incomplete are historical.

Backend-only export was actually executed:

```bash
.venv/bin/python deploy/modal/export_release.py --commit COMMIT --output ../floorhawk-modal/releases/NEW --mode backend --frontend ../floorhawk-modal/releases/local-verified
```

Attach the existing assets manifest to a new export before deploying (do not modify an existing immutable release):

```bash
.venv/bin/python - ../floorhawk-modal/releases/NEW <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1]);a=json.loads(Path('../floorhawk-modal/assets.json').read_text())
(r/'assets.json').write_text(json.dumps(a,indent=2))
m=json.loads((r/'release.json').read_text());m['assets']=a;m['models_sha256']={x['filename']:x['sha256']for x in a['models']}
(r/'release.json').write_text(json.dumps(m,indent=2))
PY
FLOORHAWK_RELEASE="$PWD/../floorhawk-modal/releases/NEW" .venv/bin/modal deploy deploy/modal/app.py
```

This preserves the selected frontend; intentionally updating it requires --mode full from a committed source. Recheck health release, authenticated app.js hash, previous-job access and one Local model smoke before promotion. No gold manifests or outputs enter the image. The source exporter checks API contract compatibility; it is not a proof that an arbitrary future backend change is behaviorally compatible.

Rollback command: `FLOORHAWK_RELEASE="$PWD/../floorhawk-modal/releases/local-candidate" .venv/bin/modal deploy deploy/modal/app.py`. This is redeployment of a pinned earlier snapshot, not a paid native rollback feature. The exact rollback command was documented, not executed after final verification; keep live disabled during recovery/rollback until checked. Original laptop release/source and newer untracked documentation were not overwritten.

## Unified Hybrid release — current

Same stable URL now serves oneResult from sharedLocal+Gemini. Sourcea44e94f; Local rollback966248c preserved.66tests and normal-login PNG/PDF/IFCsmokes pass; these do not alter benchmark accuracy. Budget100USDtotal includinghistory, requestcap1000unchanged;30prepaidcloudpermits are part of the canonical ledger. [Current behavior, verification, operator commands and limits](UI_HYBRID_RELEASE.md). Earlier Local-only/Gemini-disabled sections are historical.


## Dedicated presenter

Public deployment is independent. Pinned source, warming/off, stable endpoint and rollback commands: [PRESENTER_DEPLOYMENT.md](PRESENTER_DEPLOYMENT.md). Never replace public with an unverified presenter candidate.
