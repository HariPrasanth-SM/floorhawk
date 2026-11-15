"""Normal-authentication multi-GPU execution proof. No reference payloads."""
import argparse,json,time,os
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--capacity',action='store_true');a=p.parse_args();root=Path(__file__).resolve().parents[2];work=root.parent/'floorhawk-modal';out=work/'verification/event-capacity';out.mkdir(parents=True,exist_ok=True);os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(root/'cache/playwright')
 from playwright.sync_api import sync_playwright
 report={'passed':False,'jobs':[],'browser_errors':[]};deadline=time.monotonic()+420
 def wait(page,expr,seconds=240):
  end=min(deadline,time.monotonic()+seconds)
  while time.monotonic()<end:
   if page.evaluate(expr):return
   page.wait_for_timeout(150)
  raise AssertionError(expr+'; '+page.inner_text('#status'))
 with sync_playwright()as pw:
  browser=pw.chromium.launch(headless=True);pages=[]
  try:
   for role,n in [('public',3),('judges',2),('presenter',1)]:
    for i in range(n):
     context=browser.new_context(viewport={'width':1366,'height':768});page=context.new_page();page.on('pageerror',lambda e:report['browser_errors'].append(str(e)));url='https://sm-hariprasanth--'+{'public':'web'}.get(role,role)+'.us-east.modal.run';page.goto(url);page.fill('input[name=code]',(work/'.secrets'/({'public':'event'}.get(role,role)+'-access-code')).read_text());page.click('button');wait(page,"() => typeof S!=='undefined' && !!S.config",60);page.click('#preloadedTab');page.select_option('#galleryFormat','PNG');page.select_option('#galleryDrawing','png-a');wait(page,"() => S.validated && S.galleryId==='png-a'");page.fill('#question','How many kitchens are shown on this floor plan?');assert page.locator('#expectedReference').is_hidden();pages.append((page,url,role,str(i)))
   for page,url,role,i in pages:page.click('#run')
   for page,url,role,i in pages:wait(page,"() => location.search.startsWith('?job=')",60)
   first,url,_,_=pages[0];ident=first.evaluate("new URL(location.href).searchParams.get('job')");duplicate=first.request.post(url+'/api/jobs',data={'gallery_id':'png-a','question':'How many kitchens are shown on this floor plan?'},headers={'Idempotency-Key':first.evaluate('S.requestKey')});assert duplicate.status==202 and duplicate.json()['id']==ident;report['idempotent']=True;assert pages[1][0].request.get(url+'/api/jobs/'+ident).status==404;report['owner_isolation']=True
   allowance=first.request.get(url+'/api/allowance').json();assert allowance['application_spending_cap_enforced']is False and allowance['questions_remaining']is None;report['public_allowance']=allowance
   for page,url,role,i in pages:
    wait(page,"() => S.job?.prediction && !S.busy");wait(page,"() => (S.activeEvidence || []).length>0",60);job=page.evaluate('S.job');h=job['prediction']['paired']['hybrid'];assert job['status']=='success'and h['status']=='success',h;assert h.get('provider_attempts',0)>=1,h;assert job.get('expected_reference')is None;interval=job['worker_execution_interval'];row={'role':role,'job_id':job['id'],'worker_id':interval['worker_id'],'started':interval['started_epoch'],'finished':interval['finished_epoch'],'timing':job['presenter_timing'],'resident':job['resident'],'provider_attempts':h['provider_attempts'],'answer':h.get('answer'),'evidence_count':len(page.evaluate('S.activeEvidence || []'))};report['jobs'].append(row);(out/f'{role}-{i}.json').write_text(json.dumps(job,indent=2));print(json.dumps(row),flush=True)
   for role,n in [('public',3),('judges',2)]:
    rows=[r for r in report['jobs']if r['role']==role];assert len({r['worker_id']for r in rows})==n,(role,rows);overlap=min(r['finished']for r in rows)-max(r['started']for r in rows);assert overlap>0,(role,overlap);report[role+'_parallel_workers']=n;report[role+'_common_overlap_seconds']=overlap
   presenter=next(r for r in report['jobs']if r['role']=='presenter');assert any(max(presenter['started'],r['started'])<min(presenter['finished'],r['finished'])for r in report['jobs']if r['role']=='public');report['presenter_during_public_load']=True
   # A new accepted request, same source, uses resident weights and fresh inference.
   page,url,role,i=pages[0];page.fill('#question','How many windows are shown on this floor plan?');page.click('#run');wait(page,"() => S.job?.prediction && !S.busy && S.job.question.includes('windows')");job=page.evaluate('S.job');assert job['status']=='success';assert job['resident']['worker_id']in {r['worker_id']for r in report['jobs']if r['role']=='public'};assert job['resident']['calls']>=2;assert all(v==1 for v in job['resident']['loads'].values());report['warm_reuse']={'worker_id':job['resident']['worker_id'],'call_index':job['resident']['calls'],'loads':job['resident']['loads'],'timing':job['presenter_timing']};(out/'warm-repeat.json').write_text(json.dumps(job,indent=2));assert not report['browser_errors'];report['passed']=True
  finally:(out/'report.json').write_text(json.dumps(report,indent=2));browser.close();print(json.dumps({k:v for k,v in report.items()if k!='jobs'},indent=2))
if __name__=='__main__':main()
