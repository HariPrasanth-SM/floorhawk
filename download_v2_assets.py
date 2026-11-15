"""Reproduce selected public v2 specialists only; run under resource supervision.
Pinned code/checkpoint and SHA checks; no datasets, extra VLMs or inference APIs.
"""
from pathlib import Path
from assets import ROOT,download,ledger,sha
from runtime_paths import MODEL_ROOT
from qa.common import write_json
REV='8ef73f8c42e35f4a4c42a9e2db643ca115531e5f';HASH='7c86051cc9f620f119ad16ee5c30a7c4893871ec8684897eac02e996d3307506';out=MODEL_ROOT/'rtdetr';out.mkdir(exist_ok=True)
for name in ('README.md','predict.py','requirements.txt','weights/rtdetr_l_autoresearch_60ep.pt'):
 dest=out/Path(name).name;url='https://raw.githubusercontent.com/OldDeLorean/rtdetr-floorplan-detector/'+REV+'/'+name;download(url,dest,'selected RT-DETR-L checkpoint/source')
 if name.endswith('.pt') and sha(dest)!=HASH:raise RuntimeError('Pinned RT-DETR SHA mismatch')
(out/'revision.txt').write_text(REV+'\n');ledger(out/'revision.txt','pinned GitHub revision','selected model revision')
write_json(out/'provenance.json',{'source_revision':REV,'sha256':HASH,'url':'https://raw.githubusercontent.com/OldDeLorean/rtdetr-floorplan-detector/'+REV+'/weights/rtdetr_l_autoresearch_60ep.pt','path':'external/rtdetr/rtdetr_l_autoresearch_60ep.pt','size':(out/'rtdetr_l_autoresearch_60ep.pt').stat().st_size,'license':'Ultralytics AGPL3; CubiCasa-derived. No separate checkpoint grant located; verify before redistribution/commercial use.'})
from v2.download_ocr import main
main()
import json
for a in json.loads((MODEL_ROOT/'ppocr-v5/provenance.json').read_text())['assets']:ledger(MODEL_ROOT/Path(a['path']).relative_to('external'),a['url'],'selected PP-OCR local asset')
print('Selected public assets verified; no inference executed.')
