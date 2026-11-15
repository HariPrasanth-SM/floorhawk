# Upload submission repair


## Upload submit repair — 2026-11-15

Presenter sourcecc9c0f9, snapshot presenter-upload-repair. Reproduced normal-upload error before repair: HTTP500 body Internal Server Error parsed asJSON. Server log confirmed UnboundLocalError for hashlib: conditional import in IFC endpoint shadowed module global for upload POST. Removed conditional import; browser now handles nonJSON responses with HTTPstatus/actionable text and retains submission recovery/idempotency. Fresh normal-login UI: PNG windows2(11.54s), reupload/newquestion doors4(6.56s), replacewithPDF room4.02area2.67m2(3.80s), no browser errors. Injected plain-text503 handled clearly without parseerror.16focusedtests pass. Before/after evidence ../floorhawk-modal/verification/upload-repair/{before,after}.json. IFC route retained; public a44e94f untouched; warm presenter retained. No temporary test process remains. Rollback to last browser-verified preIFC snapshot presenter-browser-complete if necessary.

Release: https://sm-hariprasanth--presenter.us-east.modal.run
