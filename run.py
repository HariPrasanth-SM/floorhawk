"""Local CLI adapter, sharing the same detector as the browser and batch runner."""
import argparse,json
from pathlib import Path
from detector import ROOT,Detector,sha,render

def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,default=ROOT/'manifests/windows-dev.jsonl');p.add_argument('--sample',default='window-000');p.add_argument('--device',choices=['cpu','0'],default='cpu');p.add_argument('--profile',choices=['baseline','hires','tiled','diagnostic'],default='baseline');p.add_argument('--output',type=Path,default=ROOT/'results/smoke');a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=True)
 if any(a.output.iterdir()):raise ValueError('Use an empty output directory')
 rows=[json.loads(l) for l in a.manifest.read_text().splitlines()]
 if any('answer' in r or 'expected' in r for r in rows):raise ValueError('Answer-free manifest required')
 row=next(r for r in rows if r['id']==a.sample);image=ROOT.parent/row['image'];assert sha(image)==row['image_sha256']
 settings=json.loads((ROOT/'profiles.json').read_text())[a.profile];r=Detector(a.device).predict(image,settings,row['credit']);r.update(sample=row,sample_id=row['id'],manifest_sha256=sha(a.manifest))
 (a.output/'predictions.json').write_text(json.dumps(r,indent=2)+'\n')
 if r['status']=='success':render(image,r['boxes'],a.output/'overlay.png',row['credit'])
 print(json.dumps({'status':r['status'],'count':r.get('predicted_count'),'seconds':r['end_to_end_seconds']}))
 if r['status']!='success':raise SystemExit(r['error'])
if __name__=='__main__':main()
