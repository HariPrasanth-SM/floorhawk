# Dedicated presenter deployment

Public unchanged: https://sm-hariprasanth--web.us-east.modal.run (a44e94f).
Presenter: https://sm-hariprasanth--presenter.us-east.modal.run . Deployed source `dedf5e72fa44af55b1e5eae332c298ab6f69ab9f`; snapshot `../floorhawk-modal/releases/presenter-verified`. Dedicated T4 resident max1/min1, independent queue, protected server-side presenter session. **Warm idle GPU remains billable until disabled/stopped.** No billing-plan change.

Run from canonical `proofplan/`:
```bash
.venv/bin/python deploy/modal/presenter_ops.py warm
.venv/bin/python deploy/modal/presenter_ops.py ready
.venv/bin/python deploy/modal/presenter_ops.py status
# Turn warming off (new queries may cold-start):
.venv/bin/python deploy/modal/presenter_ops.py off
# Stop presenter entirely; public is separate:
.venv/bin/python deploy/modal/presenter_ops.py stop
# Redeploy exact verified artifact, preserving URL:
FLOORHAWK_RELEASE="$PWD/../floorhawk-modal/releases/presenter-browser-complete" .venv/bin/modal deploy deploy/modal/presenter.py
# Previous pinned presenter rollback:
FLOORHAWK_RELEASE="$PWD/../floorhawk-modal/releases/presenter-candidate" .venv/bin/modal deploy deploy/modal/presenter.py
```

Code: `../floorhawk-modal/.secrets/presenter-access-code` (0600), separate from public visitor code. Do not print/share in public screenshots. Existing public quotas untouched. Presenter has server authentication, ownership, one active visitor job, bounded global3active/two waiting, idempotent submission and input bounds. Shared resident models perform fresh forwards, no per-request weight-loading subprocess. Native IFC/PDF deterministic evidence may finalize without Gemini; ambiguous fixtures use bounded Gemini review. Local output and chosen route/reason retained. Reference data never reaches model prompts and server exact-question/source checks clear edited questions.

## Budget

Preserved canonical ledger and $100 total. Reserved a non-overlapping $80 presenter envelope once; canonical reservations now342entries/$90.317 (includes old allocations). These are NOT billed usage. Presenter has no artificial request-count/22permit/1000counter bottleneck; atomic monetary reservations, kill switch, bounded attempts/timeouts and provider quotas remain. Public allowance unchanged. User reported about$2 actual provider billing; dashboard timing not independently verified. Private runtime budget state is `floorhawk-presenter-budget-v1`; token-priced estimates and outstanding reservations must be reported separately.

## Verification and limitations

70 focused tests passed, output `../floorhawk-modal/verification/presenter/tests-final.txt`. Earlier66tests/fiveerrors genuinely failed: an uncommitted Controls default referenced `s` before assignment; fixed before a later66-pass run. Current70-test output supersedes that discrepancy, not the historical failure.

Six actual sources/18curated questions matched after replacing one failing toilet suggestion; details and all exact questions in [RECORDING_GUIDE.md](RECORDING_GUIDE.md). Two non-gallery checks matched; not an evaluation campaign. Fresh browser/API flows exercised normal presenter login, source changes and final results. Desktop/last cold-start checks are only claimed if saved `browser-cold-warm.json` says passed. IFC geometry is not newly implemented; properties/counts do not wait for rendering. OCR orientation/general model weaknesses remain. Sample licensing restricts redistribution. Runtime uses Python3.11; local Modal client3.10 emits deprecation warnings. Existing public deployment not overwritten.


## Final handoff caveats

Six HTTP200 Gemini attempts; $0.072 reserved; known input/output token-price subtotal $0.008711, excludes any unreported thinking tokens and is not provider billing. $80 presenter envelope is already included in canonical $90.317 reservations, not additional spend. Final browser probe confirmed exact tab labels, one active tab and immediate reference clearing on edit; two fresh window queries returned2 in6.02s/3.99s. It then failed a combined completed-job reopen assertion, so reload/reference restoration and remaining viewport/upload checks are NOT claimed passed. Cold end-to-end measurement was blocked by unsupported SDK class stats lookup; initialization7.63s is not cold total latency. Warm resident restored min1/max1, explicitly billable. No evaluation/test loops remain.


Latest follow-up: deployed22543b6, snapshot `presenter-browser-complete`. See [actual browser follow-up](PRESENTER_BROWSER_VERIFICATION.md); supersedes earlier reopen limitation where checks pass. Prior dedf5e7 snapshot remains rollback.


## IFC window render — 2026-11-15

Presenter source0fa0754, snapshot presenter-ifc-view. fzk_house_arc window question freshly returned11; browser rendered107actual source meshes with11recorded window GUIDs highlighted. Normal login, visible viewer and zero browser errors verified. Cached GLB/metadata source hash and GLB SHA verified; no model/provider call to generate geometry, no reference geometry invented. Geometry displayed only after answer; metadata inference independent. Public release unchanged; prior presenter-browser-complete rollback retained.11focusedtests passed. Private screenshot/results: ../floorhawk-modal/verification/ifc-view/. Warm T4 retained, no temporary test process remains.


## Upload submit repair — 2026-11-15

Presenter sourcecc9c0f9, snapshot presenter-upload-repair. Reproduced normal-upload error before repair: HTTP500 body Internal Server Error parsed asJSON. Server log confirmed UnboundLocalError for hashlib: conditional import in IFC endpoint shadowed module global for upload POST. Removed conditional import; browser now handles nonJSON responses with HTTPstatus/actionable text and retains submission recovery/idempotency. Fresh normal-login UI: PNG windows2(11.54s), reupload/newquestion doors4(6.56s), replacewithPDF room4.02area2.67m2(3.80s), no browser errors. Injected plain-text503 handled clearly without parseerror.16focusedtests pass. Before/after evidence ../floorhawk-modal/verification/upload-repair/{before,after}.json. IFC route retained; public a44e94f untouched; warm presenter retained. No temporary test process remains. Rollback to last browser-verified preIFC snapshot presenter-browser-complete if necessary.


## IFC render reliability

Presenter efc01a8 (snapshot presenter-ifc-reliable) retains both manual uploads and source-hash-verified FZK geometry. Three-second UI deadline now reports background loading instead of cancelling the current render. Source replacement still invalidates old renders; model/property answers remain independent.17focusedtests passed. Baseline fresh IFC question returned11,107meshes/11GUIDshighlights; combined delayed-geometry/manual-upload verification: ../floorhawk-modal/verification/ifc-upload-combined/verification.json. Public unchanged; no model/routing changes.

Combined normal-login browser test PASSED: manualFZK IFC11/107meshes/11linkedwindows → PNG2 → manualFZK IFC11/107meshes/11linkedwindows. Artificial3.6sGLBnetworkdelay included; no browsererrors, source switch cleared3D correctly. Temporary browser stopped; warm presenter retained.
