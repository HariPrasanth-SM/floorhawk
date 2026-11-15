"""Read-only sample identity registration; no answers/scoring or dataset writes."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,write_json
from PIL import Image,ImageOps
rows=json.loads((ROOT/'results/samples25/sources.json').read_text());out=[]
for row in rows:
 with Image.open(row['path'])as image:
  pixels=ImageOps.exif_transpose(image).convert('RGB');h=hashlib.sha256();h.update(str(pixels.size).encode());h.update(pixels.tobytes());pixel_sha=h.hexdigest()
 out.append({'group':'company-exploratory:'+row['sha256'],'source_sha256':row['sha256'],'pixel_sha256':pixel_sha,'role':'exploratory development, excluded from future untouched evaluation'})
write_json(ROOT/'config/exploratory-exclusions.json',{'version':1,'groups':out,'policy':'Exclude every matching drawing/project group and byte/pixel alias; never merge into untouched evaluation. Filenames/drawings/results are not published.'});print('Registered',len(out),'exploratory groups')
