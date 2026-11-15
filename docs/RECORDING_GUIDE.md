# Recording guide — deployment8fce908 / frozen inference5827eab

Use the protected presenter: https://sm-hariprasanth--presenter.us-east.modal.run . It and the judges worker remain warm/billable. Code file: `../floorhawk-modal/.secrets/presenter-access-code` from canonical source; do not include it in a recording.

## Manual upload files

- PNG: `$HOME/Junction 2026/floorhawk-modal/recording-assets/png-a.png` (sourcehigh_quality_architectural-10478.png).
- PDF: `$HOME/Junction 2026/floorhawk-modal/recording-assets/pdf-a.pdf` (sourcesite10037_bldg14632_floor39102.pdf).
- Optional IFC: `$HOME/Junction 2026/floorhawk-modal/recording-assets/ifc-a.ifc` (actualfzk_house_arc); window answer11,107source meshes/11GUIDhighlights verified after manual upload.

Originals are intact. These copies are outside source/public exports. Actual paths/hashes/scope/license provenance remain in the protected external gallery manifest.

## Three questions per recording file

|File|Exact question|Reference|Observed fresh answer|Browser seconds|
|---|---|---|---|---:|
|png-a|How many doors are shown on this floor plan? Count doorways fitted with a door; open doorways without a door leaf do not count.|4 count|4 count|11.92|
|png-a|How many windows are shown on this floor plan?|2 count|2 count|9.01|
|png-a|How many sinks and wash basins (kitchen and bathroom combined; a double-bowl sink counts as one) are drawn on this floor plan?|2 count|2 count|8.60|
|pdf-a|How many rooms labelled 'Schlafzimmer' are there on this floor?|2 count|2 count|6.51|
|pdf-a|What is the net floor area of room 4.02 ('Korridor') in m²?|2.67 m2|2.67 m2|6.71|
|pdf-a|What is the net floor area of room 4.03 ('Bad') in m²?|3.93 m2|3.93 m2|6.92|

All values above are from fresh accepted requests on the promoted presenter, not replay. The firstdoor query included an intentional transient polling503 recovery; do not present that one as a clean latency benchmark. Models stayed loaded once. Manual repeats:PNGdoors4in10.90s/windows2in9.06s;PDFroom4.02area2.67m2in7.73s;manualIFCwindows11withactualgeometryin10.96s. These are curated development examples, not a held-out performance claim.

## Suggested sequence

1. Log in before recording the screen; keep the access code out of frame. Open Live Image and upload the PNG. Show immediate preview and Drawing ready.
2. Ask windows, then doors on the same source. Point at the numbered source instances and readable evidence crop. Optionally ask sinks.
3. Replace with the PDF; ask room4.02area. Point to its printed2.67m2 source crop. Upload/custom questions have no Reference answer card.
4. Open Preloaded samples → IFC A → windows, Ask. Orbit the real source model and show the11highlighted windowGUIDs. Manual IFC upload is also verified.
5. Export an annotated PNG/PDF image. Edit the question to show the exact reference clears; no inference starts until Ask.

Warm/status/off/rollback commands: [event operations](EVENT_OPERATIONS.md). Detailed checks: [deployment verification](OVERNIGHT_DEPLOYMENT_VERIFICATION.md). If a source has no localized evidence, show that limitation rather than inventing boxes. Rendering does not establish the correctness of an IFC property/count query by itself.


The resource-only8fce908canary repeated all18suggestions with the same answers; [latest complete table](GALLERY_OVERNIGHT_VERIFICATION.md). The table above records the earlier promoted presenter5827measurements, not a promise of current latency. After resource promotion, a fresh presenter door question again returned4with4boxes in9.40s. Frontend/model/configuration/inference hashes are unchanged.
