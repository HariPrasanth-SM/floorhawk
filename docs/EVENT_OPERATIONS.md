# FloorHAWK event operations

Current release: d1ae1e2 (`../floorhawk-modal/releases/event-capacity-path`). Frozen inference base5827eab; frontend/model/configuration hashes are unchanged. All three working URLs are retained. [Measured verification](EVENT_CAPACITY.md).

|Role|URL|Warm minimum / maximum T4 workers|Total admitted jobs|
|---|---|---:|---:|
|Presenter|https://sm-hariprasanth--presenter.us-east.modal.run|1 /1|3|
|Judges|https://sm-hariprasanth--judges.us-east.modal.run|2 /5|15|
|Public|https://sm-hariprasanth--web.us-east.modal.run|2 /5|25|

One inference input perGPUworker; models remain resident. GPUworkers request/limit2CPUcores and8192MiBRAM each. Public queue accommodates20waiting at maximum5executing. Public short burst protection allows6accepted submissions/session/10seconds; one active job/session, idempotency, authentication, ownership, bounded retries/timeouts and file/decode/page/tile limits remain. There is no per-code five-question or two-upload restriction in event mode. Model routing is unchanged; deterministic answers do not unnecessarily callGemini.

## Explicit event policy and accounting

`config/event-serving.json`, activated with `FLOORHAWK_EVENT_CAPACITY=1` in cloud images, disables application dollar/cumulative-query/prepaid-permit gates. Old public compute reservations and the historical80USDprovider allocation are retained for reporting, not enforced event spending limits. The unchanged frontend's legacy budget fields can show the historical allocation; API metadata identifies it as historical with `application_cap_enforced=false`. Requests/tokens and per-job worker-time estimates still append to the same durable authority. Reservations are never labelled actual billing. No provider quota or billing setting was changed. Server-side role live/Gemini and shared provider stop switches remain. No automatic shutdown is scheduled.

Access files stay outsideGit under `../floorhawk-modal/.secrets/{presenter-access-code,judges-access-code,event-access-code}`. Never print or commit contents.

## Status, warming and readiness

Run from canonicalproofplan/:

```bash
.venv/bin/python deploy/modal/presenter_ops.py status --admission --quota --billing --budget
.venv/bin/python deploy/modal/presenter_ops.py status --app floorhawk-judges --admission
.venv/bin/python deploy/modal/presenter_ops.py status --app floorhawk-demo --admission
.venv/bin/python deploy/modal/presenter_ops.py warm
.venv/bin/python deploy/modal/presenter_ops.py warm --app floorhawk-judges
.venv/bin/python deploy/modal/presenter_ops.py warm --app floorhawk-demo
.venv/bin/python deploy/modal/presenter_ops.py ready --app floorhawk-demo
```

Warm commands read the role policy and preserve maximums1/5/5; they never reset every pool toone. `warm` verifies the configured minimum; `--verify-workers3` is available on public for bounded parallel readiness checks. Readiness calls are bounded/cancelled on timeout. `ready` reports one executing worker. Normal idle autoscaling retains the specified minimum, and temporarily excess verification workers can scale down. The environment has no explicit GPU cap; inherited workspace quota is not returned by the availableAPI. Six simultaneous real workers were verified, not all eleven possible maxima. Provider-enforced quota remains authoritative.

## Turn warming off or stop completely

```bash
.venv/bin/python deploy/modal/presenter_ops.py off
.venv/bin/python deploy/modal/presenter_ops.py off --app floorhawk-judges
.venv/bin/python deploy/modal/presenter_ops.py off --app floorhawk-demo
# Full shutdown; unlike off, this also stops future inference:
.venv/bin/modal app stop floorhawk-presenter --yes
.venv/bin/modal app stop floorhawk-judges --yes
.venv/bin/modal app stop floorhawk-demo --yes
```

`off` sets minimumzero while retaining role maximums; incoming requests can cold-start. No billing plan is changed. Stop all three apps to stop their inference entirely.

## Update / rollback

Select each role explicitly; the selected operational role persists outsideGit:

```bash
.venv/bin/python -m campaign.operator --role public --release ../floorhawk-modal/releases/event-capacity-path --enable-live
.venv/bin/modal deploy deploy/modal/app.py
```

Use presenter/judges as appropriate. Subsequent deployments read the same role-capacity policy. Immutable source snapshots/weights remain intact. For rollback use `releases/event-readiness-lock` (public9cd9301) and `releases/overnight-resource-bounds` (presenter/judges8fce908). Those earlier releases restore their former constraints and warming. Import their OWN pinned deployment entrypoint, not current helpers against an old image. For public rollback:

```bash
# From canonical proofplan/ select the old role/snapshot first:
.venv/bin/python -m campaign.operator --role public --release ../floorhawk-modal/releases/event-readiness-lock --enable-live
cd "$HOME/Junction 2026/floorhawk-modal/releases/event-readiness-lock"
FLOORHAWK_WORKSPACE="$HOME/Junction 2026/floorhawk-modal" FLOORHAWK_RELEASE="$PWD" PYTHONPATH="$PWD" "$HOME/Junction 2026/proofplan/.venv/bin/modal" deploy deploy/modal/app.py
```

For presenter/judges select that role and use its pinned overnight-resource-bounds directory in the same environment pattern. Use each snapshot's matching operator helpers after rollback; current readiness keyword arguments are not promised compatible with old signatures. Rollback snapshots remain intact; disruptive rollback was not performed after successful verification. Never edit a live weight or frozen source snapshot in place.

Admission locks have no unsafeTTL expiry. Stop the matching app first, then `.venv/bin/python deploy/modal/manage.py recover-lock --role public --confirm-app-stopped`. Recovery verifies appstate, interrupts orphaned jobs and leaves admission/provider disabled; it preserves histories. Do not unlock a running owner.

## Eight-hour estimate

Published base rates: T4 0.000164USD/s, CPU0.0000131USD/core/s, RAM0.00000222USD/GiB/s. A2core/8GiBT4worker is0.748656USD/hour. Five minimumwarm workers for8hours:29.94624USD. Eleven continuously busy maximumworkers:65.881728USD; four bounded APIcontainers at1core/4GiB continuously active add2.532096USD, total68.413824USD. MinimumAPIwarm count iszero; activeAPI/network/storage/region/tax adjustments are extra to the29.95USDminimumGPU estimate. The maximum scenario is below the reported130USDremainingModalcredit, but the balance and billing lag cannot be guaranteed by application accounting. See [Modal pricing](https://modal.com/pricing). Gemini is billed separately and remains provider-quota controlled. Warm capacity remains billable until manually turned off/stopped.
