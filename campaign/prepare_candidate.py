"""Assemble a pinned portable release configuration; weights stay external to Git."""
import json,hashlib,copy
from pathlib import Path
from .clock import atomic,now
from qa.common import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/overnight-20261115';WORK=ROOT.parent/'floorhawk-modal'
def main():
 cfg=json.loads((OUT/'candidate-config.json').read_text());cfg['ensemble']=json.loads((OUT/'ensemble-calibration.json').read_text())['policy'];cfg.update(version='overnight-production-candidate-v1',review_model='gemini-3-flash-preview',semantic_review_targets=['bedroom','kitchen','bathroom','wc_room','sauna','balcony','storey'],reason='Full development grouped validation; keep fast structural specialists because extra opening selector gained only2of9471questions',native_pdf_prefixed_ids=True,native_pdf_closed_areas=True,large_drawings_feature_gate='existing bounded path; new CPU tile variant not promoted')
 bundle={'semantic':json.loads((OUT/'selector-full361/model.json').read_text()),'opening':None};path=OUT/'deployment-selector.json';atomic(path,bundle);digest=sha(path);cfg.update(selector_sha256=digest,selector_asset='campaign-release-assets/'+digest+'/selector.json');atomic(ROOT/'config/overnight-candidate.json',cfg)
 extra=[{'local_source':str(path.relative_to(ROOT.parent)),'remote_path':'/'+cfg['selector_asset'],'size':path.stat().st_size,'sha256':digest,'license':'Own count-calibration artifact; underlying dataset/observation licenses and overlap restrictions apply','purpose':'Small grouped-development proposal selector; not a new vision model'}];atomic(OUT/'extra-assets.json',extra)
 base={r['sample_id']:r for r in(json.loads(l)for l in(OUT/'candidate-ensemble/predictions.jsonl').open())};current=[json.loads(l)for l in(OUT/'candidate-pdf-recovery-v3/predictions.jsonl').open()];result=[]
 for r in current:
  if r.get('input_kind')=='raster'and r.get('task',{}).get('target')in['door','window']:r=base[r['sample_id']]
  result.append(r)
 folder=OUT/'candidate-production-policy';folder.mkdir(exist_ok=True);(folder/'predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in result));atomic(folder/'manifest.json',{'time':now(),'configuration_sha256':sha(ROOT/'config/overnight-candidate.json'),'selector_sha256':digest,'selection':'Simple structural router retained over2question opening gain; original best retained separately','metrics_kind':'Grouped out-of-fold development estimate; live per-question context can differ from batched review context'})
 print('Prepared candidate; no current deployment changed')
if __name__=='__main__':main()
