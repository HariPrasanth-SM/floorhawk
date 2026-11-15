# Presenter browser follow-up — 2026-11-14

Presenter https://sm-hariprasanth--presenter.us-east.modal.run; public unchanged a44e94f. Deployed22543b6, immutable snapshot `presenter-browser-complete`; previous `presenter-verified` retained.

Original assertion was correct: reopening rendered the answer but skipped `showExpectedReference(job.expected_reference)` and tab/source state restoration. Fixed dedicated restore helper; reference remains server validated, no gold enters inference. Normal new login cannot read another session’s job (404), as intended.

Packaging correction: initial source export omitted external assets.json, causing startup failure. New complete snapshot includes unchanged verified manifest/hash. Failed snapshot and actual startup/test failures retained externally. No models/settings/routing changed.

Focused regression suite:71passed (tests.txt). Browser checks:
- exactly one active tab: PASS
- tab matches live: PASS
- exact tab labels: PASS
- exactly one active tab: PASS
- tab matches samples: PASS
- curated reference visible: PASS
- curated window answer: PASS
- reload creates no inference: PASS
- restored full reference: PASS
- restored answer: PASS
- exactly one active tab: PASS
- tab matches samples: PASS
- URL reopening creates no inference: PASS
- edit clears reference immediately: PASS
- exactly one active tab: PASS
- tab matches live: PASS
- PNG immediate preview before inference: PASS
- new upload clears reference: PASS
- upload/custom has no reference: PASS
- one UI submission: PASS
- answer matches submitted question: PASS
- drawing image rendered: PASS
- evidence list populated: PASS
- Result visible: PASS
- upload/custom has no reference: PASS
- one UI submission: PASS
- answer matches submitted question: PASS
- drawing image rendered: PASS
- evidence list populated: PASS
- Result visible: PASS
- upload/custom has no reference: PASS
- one UI submission: PASS
- answer matches submitted question: PASS
- drawing image rendered: PASS
- evidence list populated: PASS
- Result visible: PASS
- PNG annotated export downloaded: PASS
- PDF preview replaces PNG and clears result: PASS
- PDF replacement clears reference: PASS
- exactly one active tab: PASS
- tab matches live: PASS
- upload/custom has no reference: PASS
- one UI submission: PASS
- answer matches submitted question: PASS
- drawing image rendered: PASS
- evidence list populated: PASS
- Result visible: PASS
- upload/custom has no reference: PASS
- one UI submission: PASS
- answer matches submitted question: PASS
- drawing image rendered: PASS
- evidence list populated: PASS
- Result visible: PASS
- upload/custom has no reference: PASS
- one UI submission: PASS
- answer matches submitted question: PASS
- drawing image rendered: PASS
- evidence list populated: PASS
- Result visible: PASS
- PDF localized evidence boxes: PASS
- evidence crop caption: PASS
- PDF annotated export downloaded: PASS
- uploaded PDF reload creates no inference: PASS
- exactly one active tab: PASS
- tab matches live: PASS
- upload reload no curated reference: PASS
- no page overflow (1366, 768): PASS
- no page overflow (1920, 1080): PASS
- no browser console runtime errors: PASS

|Source|Question|Reference|Observed|Browser seconds|
|---|---|---|---|---|
|png-a.png|How many doors are shown on this floor plan? Count doorways fitted with a door; open doorways without a door leaf do not count.|4|4 count|7.39|
|png-a.png|How many windows are shown on this floor plan?|2|2 count|8.19|
|png-a.png|How many sinks and wash basins (kitchen and bathroom combined; a double-bowl sink counts as one) are drawn on this floor plan?|2|2 count|24.12|
|pdf-a.pdf|How many rooms labelled 'Schlafzimmer' are there on this floor?|2|2 count|5.44|
|pdf-a.pdf|What is the net floor area of room 4.02 ('Korridor') in m²?|2.67|2.67 m2|5.13|
|pdf-a.pdf|What is the net floor area of room 4.03 ('Bad') in m²?|3.93|3.93 m2|5.28|

Browser overall passed: True. Remaining error: none

Private raw results, downloaded exports and screenshots: `../floorhawk-modal/verification/presenter-browser-finish/`. Browser harness is `deploy/modal/presenter_browser_verify.py`; normal login, real UI Ask, no bypass or replay. Warm T4 retained min1/max1 and billable. Public health verified unchanged. No test loop intentionally remains.

All six upload answers used the same resident worker: fa0b862b1bea4303a47971125371c11b. Load counters remained CubiCasa1/RT-DETR1/OCR1. PDF overlay assertion originally ran before asynchronous presentation arrived; corrected browser harness waits for the layer, with original assertion preserved. No additional app change required.
