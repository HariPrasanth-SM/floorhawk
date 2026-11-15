"""Make a ledger-recorded compatibility copy; leave pinned upstream source intact."""
from pathlib import Path
import shutil,json
from assets import ROOT,EXTERNAL,ledger,CUBI_REV,sha
src=EXTERNAL/'cubicasa/floortrans';dst=EXTERNAL/'cubicasa-compatible/floortrans'
if not dst.exists():shutil.copytree(src,dst,ignore=shutil.ignore_patterns('__pycache__'))
p=dst/'post_prosessing.py';original=(src/'post_prosessing.py').read_text();patched=original.replace('stats.mode(widths).mode[0]','stats.mode(widths, keepdims=True).mode[0]')
p.write_text(patched)
for file in dst.rglob('*'):
 if file.is_file():ledger(file,f'https://github.com/CubiCasa/CubiCasa5k/tree/{CUBI_REV}','retained CPU/reference compatibility source')
(EXTERNAL/'cubicasa-compatible/patches.json').write_text(json.dumps({'upstream_revision':CUBI_REV,'changes':['SciPy stats.mode(widths, keepdims=True) restores the pre-SciPy-1.11 result shape expected by reference code.'],'original_sha256':sha(src/'post_prosessing.py'),'patched_sha256':sha(p)},indent=2)+'\n')
print('Compatibility copy ready')
