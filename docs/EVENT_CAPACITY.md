# Event capacity verification

Verified 2026-11-15T08:37:09.741895+02:00. Release d1ae1e2; no model, threshold, routing or frontend change. [Operational policy](../config/event-serving.json).

|Role|Worker ID|Queue/API s|Model init s|Total server s|Provider attempts|
|---|---|---:|---:|---:|---:|
|public|f16e35759ba34d94a74f254416878bbc|1.27|9.55|23.30|1|
|public|287f62745e734a6ab5f562b5f04e3057|1.51|8.53|23.80|1|
|public|a7fd71689c764c4c9c6ab82b9662caa2|1.44|9.57|24.06|1|
|judges|b698f11532f848bdaa7eef058fac1888|1.75|8.02|23.02|1|
|judges|3c37d600668845268d26ba08b6396e74|1.25|8.04|25.45|1|
|presenter|c972cc9e684047fb8a3ffd269ca58a1a|2.40|8.16|26.60|1|

Three public jobs ran on3distinctT4workers with18.79seconds common job-execution overlap. Two judges jobs ran on2distinctworkers with20.56seconds common overlap. Presenter executed during publicload on its own worker. These are recorded server execution intervals, not browser-tab or polling-order claims. Normal access-code login was used for every independent session.

All6semantic kitchen-count questions followed the frozen registered route and each invokedGemini once, returned a validated answer and visible source evidence. No reference was attached to these custom questions. These are unscored operational checks, not a new accuracy campaign. Shared accounting grew by6HTTPattempts; no second provider ledger/permit pool was created.

Warm repeat reused worker`f16e35759ba34d94a74f254416878bbc`, callindex2; every model load counter remained1. It executed a fresh specialist request with0provider calls and2.11seconds serverend-to-end time. Model loading was0for this repeat; cached answer replay was not used.

Public allowance returned questions_remaining=null, uploads_remaining=null, estimated_queries_remaining=null and application_spending_cap_enforced=false. Atomic idempotency returned the same job; another owner received404. Burst protection and one active session job remain; queue maximum is25includingrunning. Provider accounting has a bounded11inflight limit and no application monetary/cumulative request gate.

Storage audit: each accepted job has its own randomUUIDdirectory; every result carries originalsourceSHA, jobID, workerID and release. Worker scratch caches are container-local; no sharedSQLiteWAL is mounted. Volume reload/commit brackets publication of separate job directories. HTTP proxy work is synchronous between body receipt and commit in eachAPIeventloop, preventing a concurrent localreload from discarding an uncommitted source. Readers synchronize already-published jobs after ownership checks; terminal-state metadata is committed and admission completed. One input perGPUcontainer protects mutable model state. Model weights are read-only/versioned. All6returned independent artifacts without source/result leakage.

EnvironmentAPI reported max_concurrent_gpus=null (no explicitenvironmentlimit), spend_limit_reached=false. The inherited workspace numeric GPU quota is not exposed by the installedSDK. Per-role deployments accepted1/1,2/5,2/5; minimum readiness observed1presenter,2judges and3publicworkers (one extra verification worker). Actual6worker parallelism is proven; simultaneous11GPUmaximum was not load-tested.

Initial new-policy startup failed because automatic package mounting looked under/root/config. Logs confirmedFileNotFoundError; the loader now resolves/opt/floorhawk/config from the immutable cloud image. The corrected release passed startup, asset checksum checks and the full normal-login concurrent test. Early failed reports are preserved separately. A stale readiness probe was interrupted; later readiness calls have explicit bounded cancellation.

85focused tests passed, including cap-retirement with a zero legacy allocation, retained history, burst/queue/session limits and provider stop-switch checks. No final evaluation answers were used. Browser errors:0. FrontendSHAa111edce02bc2803837609cf4b15bfc19d3ee1e9ff2f003826aa2a2c49aafae8is unchanged. Raw job/interval/evidence records remain outsideGit in floorhawk-modal/verification/event-capacity/.

Cost, warm/off/stop commands and rollback: [EVENT_OPERATIONS.md](EVENT_OPERATIONS.md). Public20waiting/fullcrash recovery were not stress-tested. Provider quota, billing lag and extraAPI/network/storage costs remain limitations. Intended deployments remain warm; no automatic shutdown was scheduled.
