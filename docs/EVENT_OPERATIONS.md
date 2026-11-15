# FloorHAWK event operations

Run commands from canonical `proofplan/`. The selected event snapshot is `../floorhawk-modal/releases/overnight-resource-bounds`, source `5827eab5e423bae3eb7413a2c773183afa2f60f0`; promotion status and actually tested URLs belong in the morning handoff. Until promotion, the existing presenter/public remain unchanged.

## One source, separate roles

```bash
.venv/bin/python -m campaign.operator --role presenter --release ../floorhawk-modal/releases/overnight-resource-bounds --enable-live
.venv/bin/modal deploy deploy/modal/app.py
.venv/bin/python deploy/modal/presenter_ops.py warm
```

Use `--role judges` for `floorhawk-judges`/the `judges` endpoint, and `--role public` for `floorhawk-demo`/the existing `web` endpoint. Select each explicitly before deployment; the operator selection file persists outside Git. A backend-only export preserves the selected frontend/API contract. All roles use identical source/config/model registry; admission, jobs, worker and session state are separate. Do not point all roles at one public GPU queue.

Add `--disable-gemini` when selecting a role to keep its provider stop switch off while Local continues. Every accepted job captures that state. No request counter or prepaid permit increase occurs; new role requests share the existing durable80USD envelope inside the100USD authorization. Global provider in-flight concurrency is bounded at2. Missing/busy accounting fails closed to Local.

Access files live outside source under `../floorhawk-modal/.secrets/`: `presenter-access-code`, `judges-access-code`, `event-access-code`. Candidate uses `candidate-access-code`. Never print these into a terminal recording, URL, Git or export. Judges/presenter sessions have distinct derived cookie keys and independent job ownership.

## Warm, ready, status and shutdown

```bash
.venv/bin/python deploy/modal/presenter_ops.py warm
.venv/bin/python deploy/modal/presenter_ops.py ready
.venv/bin/python deploy/modal/presenter_ops.py status --admission --budget
.venv/bin/python deploy/modal/presenter_ops.py warm --app floorhawk-judges
.venv/bin/python deploy/modal/presenter_ops.py status --app floorhawk-judges --admission

# Stop permanent warming; queries can still cold-start.
.venv/bin/python deploy/modal/presenter_ops.py off
.venv/bin/python deploy/modal/presenter_ops.py off --app floorhawk-judges

# Disable new admission without resetting history.
.venv/bin/python deploy/modal/manage.py disable --role presenter
.venv/bin/python deploy/modal/manage.py disable --role judges
.venv/bin/python deploy/modal/manage.py disable --role public

# Stop the deployment and its running containers entirely.
.venv/bin/modal app stop floorhawk-presenter --yes
.venv/bin/modal app stop floorhawk-judges --yes
.venv/bin/modal app stop floorhawk-demo --yes
```

Presenter/judges warm T4 containers remain billable until turned off/stopped. Public starts at min0/max1, with a cold-start penalty. API containers are bounded; twenty idle/browser sessions do not imply twenty concurrent GPU jobs. Public admission retains5questions/300s per code,2distinct source uploads charged at accepted submission/300s,1active per visitor and10waiting jobs. Its existing7USD conservative cumulative compute-reservation ceiling is preserved and is not a Modal hard-dollar cap. Presenter/judges queue capacity is3 (one executing, two waiting).

## Safe admission-lock recovery

There is no unsafe automatic lock lease expiry. Stop the matching app first and verify no worker is executing; then:

```bash
.venv/bin/python deploy/modal/manage.py recover-lock --role presenter --confirm-app-stopped
```

Replace the role as appropriate. The command checks actual Modal app state, refuses a live owner, marks orphaned work interrupted and leaves admission/provider disabled. It does not clear usage/quota history. Redeploy and verify before enabling again. Do not remove a lock from a running app to bypass admission.

## Rollback

For a new event-role snapshot, select the prior pinned snapshot with `campaign.operator` and redeploy through the same entrypoint. Source/model files are immutable; never edit active weights in place.

To restore the original pre-campaign presenter exactly, import its own pinned deployment module rather than combining the newest entrypoint with old helpers:

```bash
cd "$HOME/Junction 2026/floorhawk-modal/releases/presenter-ifc-reliable"
FLOORHAWK_WORKSPACE="$HOME/Junction 2026/floorhawk-modal" FLOORHAWK_RELEASE="$PWD" PYTHONPATH="$PWD" "$HOME/Junction 2026/proofplan/.venv/bin/modal" deploy deploy/modal/presenter.py
```

Original public rollback uses the same environment pattern from `releases/ui-hybrid-verified`, deploying its `deploy/modal/app.py`. These old source snapshots remain intact. Rollback is pinned redeployment, not a claimed paid native rollback feature. Recheck health source, normal login, one live result and source evidence after any rollback.

## Export/update and verification

```bash
.venv/bin/python deploy/modal/export_release.py --commit COMMIT --output ../floorhawk-modal/releases/NEW --mode backend --frontend ../floorhawk-modal/releases/overnight-resource-bounds --extra-assets results/overnight-20261115/extra-assets.json
.venv/bin/python deploy/modal/ui_smoke.py --event --role candidate --all --limit 18 --manual --fallback --tag NEW-CHECK
```

The fallback check requires a provider-disabled candidate. Use a new immutable report tag. It performs real fresh submissions; it is not replay. Do not unnecessarily repeat it on public quotas. Selecting a source/question never automatically runs inference. References are never inference inputs. Source-matched IFC geometry is asynchronous and optional for answering.

Frozen Local evaluation is a separate explicit, provider-free path, guarded by `FROZEN.json` and matching `DELIVERY_VERIFIED.json`. It must not start before verified deployment/submission delivery. Use the monitored campaign launcher and absolute07:30 deadline; never relabel cached source reuse as cold per-question latency. Its CPU fallback is explicit and may leave partial coverage. No final score is reported before actual runs.
