# Presenter curated development checks — 2026-11-14

Six sources,18 final suggestions matched references on fresh execution after one failed toilet suggestion was replaced. Original20-run batch19matches; replacement sink twice matched. Two non-gallery controls matched. These selected checks are not held-out accuracy and do not update frozen v3 6641/9471 (70.12%). Detailed questions/timings and failure disclosure: docs/RECORDING_GUIDE.md; deployment: docs/PRESENTER_DEPLOYMENT.md.

# FloorHAWK current release analytics

Default remains **v3 policies**; the paired candidate is **opt-in and not promoted**. Runtime/configuration/Git improvements have no new full-development score. The9,544-question quick set is DEVELOPMENT, never final-test performance. Final eligibility questions are frozen separately without reading final answers or running them.

## Matched paired candidate — paired-evidence-v2

**16 questions / 15 distinct drawing groups**, identical IDs and unchanged Local evidence for both modes. Deterministic diagnostic sample: PNG fixtures/windows, Swiss-PDF doors, PDF-area abstentions, IFC properties. It overweights known difficult cases; it is not a representative accuracy estimate. Source/config/manifest SHA256 and exact per-question rows are in external `results/iteration60/paired-v2/score.json` and `scored-rows.jsonl`.

|Mode|Questions|Numeric denominator|Correct|Incorrect|Answered|Ungraded answered|Unresolved/errors|Numeric correct/all|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|Local|16|13|4|6|10|0|6|4/13|
|Hybrid|16|13|4|6|10|0|6|4/13|

Paired states: `{"text_ungraded": 3, "unchanged_correct": 4, "unresolved_or_wrong": 9}`. Actual provider invocation: 15 questions, 17 HTTP attempts, 2 final provider/schema errors. Enabled Hybrid is not equivalent to a request or successful answer. Unresolved outcomes and Local answers are preserved.

Separate versioned text rubric: 0 newly graded Hybrid text answers. Narrative semantics remain explicitly ungraded; no combined numeric/text headline is invented. Whole-string scalar/controlled aliases and explicit-list set metrics reject misleading substrings and supersets. Numeric units/tolerance rules are unchanged.

## Matched format outcomes

|Group|N|Local correct / numeric|Hybrid correct / numeric|Local answered|Hybrid answered|Hybrid unresolved|
|---|---:|---:|---:|---:|---:|---:|
|.ifc|3|N/A (0 scorable)|N/A (0 scorable)|0|0|3|
|.pdf|7|0/7|0/7|4|4|3|
|.png|6|4/6|4/6|6|6|0|
## Matched type outcomes

|Group|N|Local correct / numeric|Hybrid correct / numeric|Local answered|Hybrid answered|Hybrid unresolved|
|---|---:|---:|---:|---:|---:|---:|
|area|3|0/3|0/3|0|0|3|
|count|10|4/10|4/10|10|10|0|
|text|3|N/A (0 scorable)|N/A (0 scorable)|0|0|3|
## Matched target outcomes

|Group|N|Local correct / numeric|Hybrid correct / numeric|Local answered|Hybrid answered|Hybrid unresolved|
|---|---:|---:|---:|---:|---:|---:|
|area_aggregate_or_element|1|0/1|0/1|0|0|1|
|area_room|2|0/2|0/2|0|0|2|
|bim_properties_and_structured_text|3|N/A (0 scorable)|N/A (0 scorable)|0|0|3|
|count_doors|4|0/4|0/4|4|4|0|
|count_showers_and_baths|2|2/2|2/2|2|2|0|
|count_toilet_fixtures|2|2/2|2/2|2|2|0|
|count_windows|2|0/2|0/2|2|2|0|

## Timing, cost and resource limits

V2 reused the EXACT saved Local answers/bundle hashes from V1; local extraction was not rerun for the second contract check. Shared document extraction cost is recorded once per bundle; per-question Local answering may include cached specialist lookups. Original cache-generation timing is not new cold inference time. Median/p95 and sample counts: `{"additional_gemini": {"median": 3.5581479395004862, "n": 16, "p95": 58.57636098799958}, "cloud_queue": {"median": 8.217499271268025e-06, "n": 16, "p95": 1.2726999557344243e-05}, "local_answer": {"median": 0.02258243700089224, "n": 16, "p95": 7.888119373999871}}`. Extra cloud generation/wait is measured separately; run elapsed 130.537s. V1 Local runtime remains separately recorded; V2 adds cloud-only wall time. Queue initially2, global atomic lifetime reservations retained, max2 attempts/question; six HTTP starts/minute.

This V2 run reserved **$0.204**, 17 attempts; this is conservative reservation, not settled billing. Actual token usage and current registered price calculation are in generation metadata and the accounting report. Lifetime limits remain1,000/$10, never reset. Original user-reported dashboard143 requests/$0.48 remains historical and unreconciled to later runs; do not mix it with this iteration. Resource samples and actual recorded device/cache flags remain external under iteration60. No final-test, paid training, public deployment or new model download occurred.

## Frozen full-development baseline — separate earlier run

Earlier frozen v3 Local: **6641/9471 (70.12%) numeric**, 9544 questions, 448 drawing groups/452 physical input paths. Correct6,641; Incorrect2,350; answered-ungraded20; abstained469; unsupported64; errors0; missing Local0. Coverage9,011/9,54494.42%; correct/graded answered6,641/8,99173.86%. Count MAE0.666586 on8,254 valid counts. Full-quick Hybrid does not exist. **Do not compare this full baseline against the small Hybrid sample as a paired result.** All full-run pipeline timings are cached retrieval; unknown original model times are not filled with zero. Full original row outputs/hashes remain external and unchanged.

### Full frozen baseline by format

|Group|N|Recorded|Answered|Correct / scorable|Incorrect|Ungraded|Abstained/unsupported/errors|
|---|---:|---:|---:|---:|---:|---:|---:|
|IFC|74|74|23|3/4|0|20|15/36/0|
|PDF|3066|3066|2584|2270/3063|314|0|454/28/0|
|PNG|6404|6404|6404|4368/6404|2036|0|0/0/0|
|Other raster|0|0|0|N/A (0 scorable)|0|0|0/0/0|
|SVG|0|0|0|N/A (0 scorable)|0|0|0/0/0|
|Other|0|0|0|N/A (0 scorable)|0|0|0/0/0|
### Full frozen baseline by question_type

|Group|N|Recorded|Answered|Correct / scorable|Incorrect|Ungraded|Abstained/unsupported/errors|
|---|---:|---:|---:|---:|---:|---:|---:|
|area|1026|1026|737|701/1026|36|0|284/5/0|
|count|8423|8423|8254|5940/8423|2314|0|149/20/0|
|length|8|8|0|0/8|0|0|6/2/0|
|text|73|73|20|N/A (0 scorable)|0|20|17/36/0|
|volume|14|14|0|0/14|0|0|13/1/0|
### Full frozen baseline by target

|Group|N|Recorded|Answered|Correct / scorable|Incorrect|Ungraded|Abstained/unsupported/errors|
|---|---:|---:|---:|---:|---:|---:|---:|
|apartment|448|448|384|370/448|14|0|64/0/0|
|balcony|222|222|222|164/222|58|0|0/0/0|
|bathroom|356|356|356|194/356|162|0|0/0/0|
|beam|6|6|1|1/4|0|0|4/1/0|
|bedroom|426|426|426|232/426|194|0|0/0/0|
|building|19|19|2|0/1|0|2|5/12/0|
|column|8|8|1|1/7|0|0|6/1/0|
|door|720|720|705|382/715|321|2|13/2/0|
|kitchen|476|476|476|426/476|50|0|0/0/0|
|material|6|6|4|N/A (0 scorable)|0|4|2/0/0|
|room|1691|1691|1450|1391/1687|56|3|236/5/0|
|sanitary|3|3|0|0/2|0|0|2/1/0|
|sauna|492|492|492|442/492|50|0|0/0/0|
|shower_bath|842|842|792|506/842|286|0|50/0/0|
|sink|868|868|860|474/868|386|0|8/0/0|
|slab|7|7|1|0/5|0|1|6/0/0|
|software_schema|2|2|2|N/A (0 scorable)|0|2|0/0/0|
|stair|5|5|0|0/4|0|0|4/1/0|
|storey|722|722|722|606/722|116|0|0/0/0|
|toilet_fixture|885|885|868|684/884|184|0|17/0/0|
|unknown|37|37|0|0/22|0|0|3/34/0|
|wall|46|46|5|1/37|0|4|37/4/0|
|wc_room|350|350|350|230/350|120|0|0/0/0|
|window|907|907|892|537/901|353|2|12/3/0|

## Whole iteration setup and smoke accounting

45 actual provider attempts:26 strict V1,17 corrected V2,2 paired UI smokes. Total conservative reservations$0.540; token-price estimate$0.057782. Global247 requests/$8.949 reserved of the unchanged1,000/$10 caps. These totals are NOT the matched V2 sample cost/score denominator. Original reused-operation counters are corrected in derivative accounting.json using append-only ledger row ranges; raw predictions remain immutable. Later unique UUID/rate/cache/projection guards were smoke-tested without another evaluation campaign.

## Previous versus current

Earlier v3 policy/full-dev baseline is preserved. V1 paired strict schema exposed an optional-region contract issue; V2 accepts only source-bounded proposals labelled unverified, while preserving all ID/unit/type checks. Same Local evidence was reused; fresh Hybrid generation was measured separately. This is not a causal model ablation or evidence of full-dataset improvement. History summaries live in reports/history; full old predictions/reports stay external with hashes. No model/threshold promotion follows this diagnostic.

Regenerate current-only report: `.venv/bin/python scripts/current_analytics.py`. Rebuild complete replay index separately with `python -m inspection.analytics`; its all-version historical report is external, not this main current report.

## Separate unscored company exploration

See [samples smoke report](docs/samples-smoke.md). These exploratory drawings have no supplied ground truth and do not alter the frozen development/diagnostic metrics above. Source/pixel identities are quarantined from future untouched evaluation.

## Agile candidate — separate diagnostic, not promoted

[2026-11-14 first-iteration report](docs/agile-hour1.md):32questions/10groups,28numeric/4text. ExistingLocal18/28; custom+native21/28; interruptedHybrid14/28 with4missing. Matched24numeric: Local16/24 vsHybrid14/24,0rescues/2regressions. No full-dev score replacement; frozen baseline and previous runs remain unchanged. External score/rows: `results/agile1/experiment/score.json`, `scored-rows.jsonl`.

## Modal deployment checks (not accuracy)

19focusedtests pass;28runtime assets uploaded. Real cloud inference and browser not verified; live disabled. No accuracy score or speed claim. See docs/MODAL_DEPLOYMENT.md.

## Protected Local cloud verification (not accuracy)

Source966248c deployed at https://sm-hariprasanth--web.us-east.modal.run .3freshjobs/2PNGimages yielded7/5/4countanswers with7/5/4evidence regions and recordedCUDAinputs forCubiCasa/RT-DETR. No expected answers used; no accuracy change claimed. All28assets remotehashverified. Sessionisolation, idempotency, deployeduploadquota, browser/reload and unchangedfrontend/URL checks pass.62tests pass. Gemini disabled/ledgerunchanged;3jobs$0.75conservativecompute reservation, unsettledbilling. Full details docs/MODAL_VERIFICATION.md.

## Unified Hybrid release — current

Same stable URL now serves oneResult from sharedLocal+Gemini. Sourcea44e94f; Local rollback966248c preserved.66tests and normal-login PNG/PDF/IFCsmokes pass; these do not alter benchmark accuracy. Budget100USDtotal includinghistory, requestcap1000unchanged;30prepaidcloudpermits are part of the canonical ledger. [Current behavior, verification, operator commands and limits](docs/UI_HYBRID_RELEASE.md). Earlier Local-only/Gemini-disabled sections are historical.


## Final handoff caveats

Six HTTP200 Gemini attempts; $0.072 reserved; known input/output token-price subtotal $0.008711, excludes any unreported thinking tokens and is not provider billing. $80 presenter envelope is already included in canonical $90.317 reservations, not additional spend. Final browser probe confirmed exact tab labels, one active tab and immediate reference clearing on edit; two fresh window queries returned2 in6.02s/3.99s. It then failed a combined completed-job reopen assertion, so reload/reference restoration and remaining viewport/upload checks are NOT claimed passed. Cold end-to-end measurement was blocked by unsupported SDK class stats lookup; initialization7.63s is not cold total latency. Warm resident restored min1/max1, explicitly billable. No evaluation/test loops remain.
