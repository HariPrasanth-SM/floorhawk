"""Fresh replacement and small non-gallery controls; reference-only client grading."""
import os,json,time,uuid,base64,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));W=ROOT.parent/'floorhawk-modal';O=W/'verification/presenter';os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'cache/playwright')
from playwright.sync_api import sync_playwright
from runtime_paths import DATASET_ROOT
import modal
short=json.loads((W/'presenter-shortlist.json').read_text());store=modal.Dict.from_name('floorhawk-presenter-gallery-v1');catalog=store.get('catalog');a=catalog[0];replacement=next(q for q in short[a['source_path']]if q['category']=='count_sinks');replacement.update(id='q3',verification='Replacement from saved development success; fresh verification pending');a['suggestions'][2]=replacement;store.put('catalog',catalog);(W/'presenter-gallery-manifest.json').write_text(json.dumps(catalog,indent=2))
plan=[({'gallery_id':'png-a','question':replacement['question'],'mode':'hybrid'},replacement['reference'],'replacement'),({'gallery_id':'png-a','question':replacement['question'],'mode':'hybrid'},replacement['reference'],'replacement-repeat')]
for path,target in [('data/cubicasa5k/high_quality_architectural-12969.png','count_doors'),('data/swiss_dwellings/site605_bldg1321_floor50804.pdf','count_labelled_rooms')]:
 q=next(q for q in short[path]if q['category']==target);p=DATASET_ROOT/path;plan.append(({'file_name':p.name,'file_base64':base64.b64encode(p.read_bytes()).decode(),'question':q['question'],'mode':'hybrid'},q['reference'],'non-gallery'))
rows=[]
with sync_playwright()as p:
 b=p.chromium.launch(headless=True);c=b.new_context();page=c.new_page();u='https://sm-hariprasanth--presenter.us-east.modal.run';page.goto(u);page.fill('input[name=code]',(W/'.secrets/presenter-access-code').read_text());page.click('button');page.wait_for_timeout(500)
 for body,reference,kind in plan:
  start=time.monotonic();r=page.request.post(u+'/api/jobs',data=body,headers={'Idempotency-Key':uuid.uuid4().hex});assert r.status==202,r.text();ident=r.json()['id'];end=time.monotonic()+150
  while time.monotonic()<end:
   response=page.request.get(u+'/api/jobs/'+ident)
   if not response.ok:time.sleep(.3);continue
   j=response.json()
   if j['status']not in ['running','queued']:break
   time.sleep(.25)
  h=j.get('prediction',{}).get('paired',{}).get('hybrid',{});row={'kind':kind,'question':body['question'],'reference':reference,'answer':h.get('answer'),'match':h.get('answer')==reference,'seconds':time.monotonic()-start,'resident':j.get('resident'),'attempts':h.get('provider_attempts'),'job_id':ident,'timing':j.get('presenter_timing')};rows.append(row);print(json.dumps({k:v for k,v in row.items()if k not in['resident','timing']},ensure_ascii=False),flush=True);(O/'supplement.json').write_text(json.dumps(rows,indent=2))
 c.storage_state(path=str(W/'.secrets/presenter-browser-state.json'));(W/'.secrets/presenter-browser-state.json').chmod(0o600);b.close()
