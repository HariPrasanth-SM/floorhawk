# Overnight accounting reconciliation

Read-only checkpoint:15November2026,06:53Helsinki. No ledger reset, reservation deletion or cap increase. Values below are not a provider invoice.

|Record|Observed value|Meaning|
|---|---:|---|
|Canonical lifetime entries|342|Includes allocations and unused prepaid permits, not342new HTTP calls|
|Canonical reservations|90.317USD|Already includes the80USD shared serving allocation|
|Shared serving records|400HTTPresponses|Includes setup/retries;16records existed at preflight,384additional recorded responses overnight|
|Shared conservative reservations|15.505USD /80USD|64.495USD remains reservable inside that allocation; not a statement of provider credit|
|Deduplicated lifetime records|723|722recorded HTTPresponses and1unresolved reservation|
|Known input/output tokens|2,957,430 /392,489|Thinking tokens unrecorded for723records;26records lack input/output usage|
|Partial known token-priced subtotal|2.9772555USD|Excludes unknown usage/thinking and two unpriced historical model records; not actual final cost|
|Old cloud remote records|12|Share IDs with canonical permits; do not add them as a second allowance|

The shared records contain18Lite,15Pro and367Flash responses. Their known input/output token-priced subtotals are0.0232385USD,0.360518USD and1.7683135USD respectively. Their conservative reservations are0.200USD,2.460USD and12.845USD. HTTPresponse does not imply a correct answer or successful schema validation.

The user's historical dashboard observation was143calls/0.48USD, later approximately2USD. Its exact project/time window, billing lag, credits and thinking-token coverage are unavailable. It cannot be reconciled exactly to the later722response lifetime ledger. Do not substitute reservations for billing, subtract the partial token subtotal from100USD as if it were a verified remaining credit balance, or add the80USDallocation twice. The existing unresolved0.02USD reservation is retained conservatively. No new provider calls were made during the final deployment browser checks or frozen LocalCPU evaluation.

Read-only reproduction, from canonical source:

```bash
.venv/bin/python deploy/modal/presenter_ops.py status --admission --budget
```

The shared durable authority, finite-cost atomic reservations, max2provider attempts in flight, bounded retries and role stop switches remain. LocalCPU evaluation explicitly blocks provider generation. Existing secrets are server-side; no values are required in this report.

## Modal

Actual invoice/credit consumption is unavailable to this task. Additional campaign compute was planned conservatively below8USD, not enforced as a platform dollar ceiling; inherited presenter warming is separate from newly started evaluation resources. No new GPU evaluation fleet was launched: extraction/candidate workers scale to zero, and final evaluation uses supervised local CPU.

Two intended event T4 workers remain warm and billable. At the published base rates, each T4+2CPU cores+8GiB worker is approximately0.748656USD/hour; the pair approximately1.497312USD/hour, before API/network/region/tax adjustments. Requests/limits are explicit2cores/8192MiB forGPU workers and1core/4096MiB forAPI containers. CPU/memory billing uses the higher of request or usage. See [Modal pricing](https://modal.com/pricing) and [resource semantics](https://modal.com/docs/guide/resources). These estimates are not measured spend.

Public's existing cumulative compute-reservation guard is5.75USD/7USD after two overnight smoke jobs: five additional0.25USD admissions remain. This is independent of its rolling5questions/300seconds and is not a Modal invoice. Presenter/judges do not use that public pool. It was not silently raised or reset.

Use [event operations](EVENT_OPERATIONS.md) to inspect, disable warming, stop deployments and recover fail-closed admission safely. The intended event deployments remain available after experiment shutdown.
