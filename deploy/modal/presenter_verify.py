"""Fresh protected presenter verification. References read only after each answer."""
import os,sys,time,json,uuid,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));W=ROOT.parent/'floorhawk-modal';O=W/'verification/presenter';O.mkdir(parents=True,exist_ok=True)
os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(ROOT/'cache/playwright')
from playwright.sync_api import sync_playwright
U='https://sm-hariprasanth--presenter.us-east.modal.run';rows=[];report={'passed':False,'rows':rows};start=time.time();deadline=start+600
try:
 with sync_playwright()as p:
  browser=p.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1366,'height':768});page=context.new_page();page.goto(U);page.fill('input[name=code]',(W/'.secrets/presenter-access-code').read_text());page.click('button');page.wait_for_timeout(600);catalog=page.request.get(U+'/api/gallery').json();assert len(catalog)==6
  # Provider requests receive only source identity + actual question; no reference data.
  plan=[(r,q,False)for r in catalog for q in r['suggestions']];plan+=[(catalog[0],catalog[0]['suggestions'][1],True),(catalog[2],catalog[2]['suggestions'][1],True)]
  for index,(source,suggestion,repeat)in enumerate(plan):
   if time.time()>deadline-60:raise RuntimeError('Bounded verification deadline; partial results retained')
   body={'gallery_id':source['id'],'question':suggestion['question'],'mode':'hybrid'};submitted=time.monotonic();response=page.request.post(U+'/api/jobs',data=body,headers={'Idempotency-Key':'presenter-verify-'+uuid.uuid4().hex});assert response.status==202,response.text();ident=response.json()['id']
   while time.time()<deadline:
    result=page.request.get(U+'/api/jobs/'+ident)
    if result.status in[429,500,502,503,504]:time.sleep(.5);continue
    assert result.ok,result.text();job=result.json()
    if job['status']not in['queued','running']:break
    time.sleep(.25)
   elapsed=time.monotonic()-submitted;(O/('job-'+str(index)+'.json')).write_text(json.dumps(job,indent=2));h=job.get('prediction',{}).get('paired',{}).get('hybrid',{});final=h if h.get('status')in ['success','abstained','unsupported']else job.get('prediction',{}).get('paired',{}).get('local',{});answer=final.get('answer');reference=suggestion.get('reference');from evaluation.numeric import score
   grade=score({'type':'count'if suggestion.get('unit')=='count'else'area'if suggestion.get('unit')in['m2','m²']else'text','answer':reference,'unit':suggestion.get('unit')},final);match=grade.get('passed')is True if grade.get('passed')is not None else grade.get('text_normalized_exact',False)
   row={'source':source['id'],'path':source['source_path'],'question_id':suggestion['id'],'question':suggestion['question'],'reference':reference,'unit':suggestion.get('unit'),'answer':answer,'status':final.get('status'),'match':match,'repeat':repeat,'seconds':elapsed,'job_id':ident,'resident':job.get('resident'),'timing':job.get('presenter_timing'),'route':h.get('chosen_route'),'reason':h.get('route_reason'),'provider_attempts':h.get('provider_attempts',0),'evidence_n':len(job.get('prediction',{}).get('evidence',[]))};rows.append(row);(O/'results-progress.json').write_text(json.dumps(rows,indent=2));print(json.dumps({k:row[k]for k in['source','question_id','answer','reference','status','match','seconds','provider_attempts']},ensure_ascii=False),flush=True)
  ids={r['resident']['worker_id']for r in rows if r['resident']};assert len(ids)==1;assert all(r['resident']['loads']['cubicasa']==1 and r['resident']['loads']['rtdetr']==1 for r in rows);report.update(passed=True,worker_ids=list(ids),queries=len(rows),correct=sum(r['match']for r in rows),provider_attempts=sum(r['provider_attempts']for r in rows),latency={'median':statistics.median(r['seconds']for r in rows),'min':min(r['seconds']for r in rows),'max':max(r['seconds']for r in rows)},note='Handpicked development cases, not held-out accuracy. Raw rows and timings retained; no p95 claimed.');context.storage_state(path=str(W/'.secrets/presenter-browser-state.json'));(W/'.secrets/presenter-browser-state.json').chmod(0o600);browser.close()
finally:(O/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items()if k!='rows'},indent=2))
