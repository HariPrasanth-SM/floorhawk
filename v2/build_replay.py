from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Offline evaluator-side replay packaging. References never enter live inference.
Copies only explicit preview/result evidence, never keys, configs or raw user uploads.
"""
import argparse,json,shutil,hashlib,io,math
from pathlib import Path
from PIL import Image,ImageDraw
from qa.common import ROOT,sha,write_json

def build(output,local,hybrid,answers):
 if output.exists():raise ValueError('Replay is immutable; choose a fresh directory')
 output.mkdir(parents=True);records={};gold={r['sample_id']:r for r in map(json.loads,answers.open())}
 from qa_score import provided
 for mode,path in [('local',local),('hybrid',hybrid)]:
  if not path.exists():continue
  for pred in map(json.loads,path.open()):
   g=gold[pred['sample_id']];grade=provided.score(g,pred);entry=records.setdefault(pred['sample_id'],{'sample_id':pred['sample_id'],'question':g['question'],'category':g.get('category'),'format':Path(g['path']).suffix,'source_path':g['path'],'modes':{}});ident=pred['sample_id']+'-'+mode;dest=output/ident;dest.mkdir()
   source=DATASET_ROOT/g['path'];suffix=source.suffix.lower();pages=[]
   if suffix=='.pdf':
    import pymupdf
    with pymupdf.open(source) as doc:
     for i,page in enumerate(doc):
      scale=1400/max(page.rect.width,page.rect.height);pix=page.get_pixmap(matrix=pymupdf.Matrix(scale,scale),alpha=False);pix.save(dest/f'page-{i+1}.png');pages.append({'page':i+1,'width':pix.width,'height':pix.height,'scale':scale,'rotation':page.rotation,'coordinate_system':'PDF displayed page pixels'})
   elif suffix=='.ifc':
    im=Image.new('RGB',(1000,600),'#f2f5ef');ImageDraw.Draw(im).text((30,40),'IFC GUID/property evidence below. No 3D rendering.',fill='black');im.save(dest/'page-1.png');pages=[{'page':1,'width':1000,'height':600,'coordinate_system':'No spatial image evidence'}]
   else:
    im=Image.open(source).convert('RGB');im.save(dest/'page-1.png');pages=[{'page':1,'width':im.width,'height':im.height,'coordinate_system':'Original image pixels'}]
   boxes=[]
   for e in pred.get('evidence',[]):
    if 'bbox' not in e:continue
    pn=e.get('page',1);b=e['bbox']
    if not 1<=pn<=len(pages):continue
    if suffix=='.pdf':
     import pymupdf
     with pymupdf.open(source) as doc:b=list(pymupdf.Rect(b)*doc[pn-1].rotation_matrix*pymupdf.Matrix(pages[pn-1]['scale'],pages[pn-1]['scale']))
    boxes.append({'xyxy':b,'page':pn,'included':True,'evidence_id':e['id'],'class_name':e.get('class',e.get('label','evidence')),'detector_score':e.get('score')})
   credit='CubiCasa5K (c)2019 CubiCasa; Kalervo et al.2019; CC BY-NC-SA4.0' if 'cubicasa5k/' in g['path'] else 'Swiss Dwellings / Archilyse CC BY4.0' if 'swiss_dwellings/' in g['path'] else 'Source attribution/licence retained: '+str(Path(g['path']).parent/'LICENSE.md')
   review={'revision':0,'boxes':boxes,'included_evidence_ids':[e['id'] for e in pred.get('evidence',[])],'reviewed_count':len(boxes),'answer':pred.get('answer'),'unit':pred.get('unit'),'reviewed':False,'instance_count':any(t.get('operation')=='count_unique_included_entities' for t in pred.get('calculation_trace',[]))}
   job={'id':ident,'status':'success','stage':'Recorded evaluation replay','device':pred.get('device','recorded'),'credit':credit,'question':g['question'],'source_name':g['path'],'source_sha256':pred['source_sha256'],'input_kind':'pdf' if suffix=='.pdf' else 'ifc' if suffix=='.ifc' else 'image','image_size':[pages[0]['width'],pages[0]['height']],'pages':pages,'prediction':pred,'review':review,'replay':{'expected':g['answer'],'unit':g['unit'],'grade':grade,'evaluation_label':'Frozen40 quick-development paired; curated gallery not benchmark accuracy','original_compute_seconds':pred['timing']['total_seconds'],'original_cloud_generation_seconds':pred.get('cloud',{}).get('original_generation',{}).get('timing_seconds'),'cache_note':'Recorded pipeline timing includes its recorded cache state; original cloud/model stage timings are retained separately','source_predictions_sha256':sha(path)}}
   write_json(dest/'job.json',job)
   for p in pages:
    from detector import render
    render(dest/f"page-{p['page']}.png",[b for b in boxes if b['page']==p['page']],dest/f"annotated-{p['page']}.png",credit,'RECORDED model/tool evidence; not live inference')
   entry['modes'][mode]={'id':ident,'correct':grade['passed'] is True,'status':pred['status'],'grade_reason':grade['reason']}
 index={'schema_version':1,'banner':'RECORDED EVALUATION REPLAY — no live inference','curation':'Correct numeric cases only by default; failures/unknown text grades available with --include-failures. No wrong counts labelled partial.','questions_sha256':sha(ROOT/'benchmarks/v2/paired.questions.jsonl'),'answers_sha256':sha(answers),'records':list(records.values())}
 write_json(output/'index.json',index);write_json(output/'checksums.json',{str(f.relative_to(output)):sha(f) for f in output.rglob('*') if f.is_file() and f.name!='checksums.json'});print('Replay saved records',len(records))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--local',type=Path,required=True);p.add_argument('--hybrid',type=Path,required=True);p.add_argument('--answers',type=Path,required=True);a=p.parse_args();build(a.output,a.local,a.hybrid,a.answers)
