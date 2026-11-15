# Event-readiness verification

Completed 2026-11-15T08:03:37.075431+02:00. No training, threshold/routing changes or final-evaluation tuning. Models and frontend hash remain unchanged. Only public admission received operational fixes.

## Public admission

The cumulative application guard increased from7USD to15USD under the atomic admission transaction. Existing5.75USD reservations and all spending/quota/idempotency history were retained; allocation history records before/after values and authorization. After this pass,7.50USD is reserved, leaving an estimated30admissions at0.25USD each. This is a conservative application guard, not a Modal hard-dollar cap. Visitor limits remain5questions/code/300s,2distinct source uploads charged on submission/300s,1active request/visitor,10waiting and max1publicT4.

Workspace billing was actually queried: month-to-date metered8.73096901USD initially and9.40112724USD later; billed0USD with credits covering current charges. The approximately0.67USD change includes ongoing workspace/warm resources, not isolated task accounting. Remaining promotional-credit balance is unavailable and reporting can lag. No plan/credit purchase occurred; the allocation increase was bounded at8USD.

Initial simultaneous admission exposed immediate atomic-lock contention: two jobs completed and another received Admission busy. The public operational fix waits at most1.5seconds to acquire the same atomic lock. It retains fail-closed behavior and never expires/deletes a crashed owner. Focused contention and invalid-budget tests pass.

## Real Gemini through normal login

|Role|Provider|Validated answer|Visible localized regions|Browser seconds|Deployed revision|
|---|---|---|---:|---:|---|
|presenter|gemini-3-flash-preview,1HTTPattempt|1count|1|23.20|8fce908|
|judges|gemini-3-flash-preview,1HTTPattempt|1count|1|38.37|8fce908|
|public|gemini-3-flash-preview,1HTTPattempt|1count|1|32.09|9cd9301|

Question: How many kitchens are shown on this floor plan? Sourcepng-a. This registered semantic target follows the existing frozen router; deterministic routes were not forced into Gemini. Each call received cumulative local observations/source context. Validated evidence IDs resolved into visible regions; final selection sometimes retained local evidence and sometimes selected model-proposed review regions, labelled unverified. References were absent from custom questions/provider inputs.

Seven provider calls in total (two initial verification passes plus the final public check), all recorded by the one shared authority:407shared HTTPresponses/15.750USDconservative reservations, up from400/15.505USD. This pass added37477known input/2358output tokens; partial token-priced estimate0.0258125USD and reserved0.245USD. Thinking usage remains unknown. Lifetime729recorded responses+1unresolved reservation; partial known token estimate3.003068USD is not actual billing. No lifetime allocation reset/increase.

## Actual concurrent jobs

Two normal-login public visitors submitted real jobs concurrently. Both showed “Reading drawing · queued”; they completed as windows2 and doors4 on one public worker. Repeated idempotency returned the same job; another visitor received404for its result. Presenter and judges IFC requests used distinct workers/queues during this test. Their server end-to-end timings were3.68s and2.57s; public jobs17.83s and19.92s, including cold start/queue. Observation/poll order is not treated as server completion order. No provider calls were needed for these deterministic queue probes. Browser runtime errors:0. This is not a full queue saturation,20GPU-job or crash test.

The final source public operational revision is9cd9301; presenter/judges retain8fce908. Inference base5827eab, model/config hashes and frontendSHAa111edce02bc2803837609cf4b15bfc19d3ee1e9ff2f003826aa2a2c49aafae8are unchanged. Model load counters remained1. Public rollback: select `../floorhawk-modal/releases/event-readiness` (3d436a3, configurable allocation before bounded-wait change), then deploy through the standard entrypoint. This preserves the allocation reader; older hard-coded7USD snapshots would block once reservations exceed7USD.

## Documentation and asset handoff

README now has the requested structure, one qualified results table, a top-down specialist architecture, separate Gemini/Modal/Codex contributions and checked relative links. No YouTube URL was found; video remains pending. No iframe or invented thumbnail/link. Custom detector author attribution remains pending.

Required asset inventory: [config/deployed-assets.json](../config/deployed-assets.json),30entries with sizes/hashes/source/revision/role/license. ZIP contains only3unchanged Apache-2.0 PP-OCR models plus manifest, restore instructions, license and notices. Restricted/unclear weights are excluded with restoration instructions. No Drive upload connection was available.

Package: `floorhawk-modal/handoff/event-readiness/floorhawk-redistributable-ocr.zip`; 12318457bytes; SHA256`d22f60ae18e2d668c5392385577704113188972668af7b807b2d4f1231ed2871`. All7entries, CRC and modelSHA256verified. Free disk was88GiB before packaging. Archive stays outsideGit.

Raw browser/job/allocation/package records remain outsideGit under floorhawk-modal. [Shutdown and operator controls](EVENT_OPERATIONS.md). Presenter/judges remain warm and billable; publicmin0/max1. No temporary server or experiment remains.
