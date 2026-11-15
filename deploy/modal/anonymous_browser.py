"""Fresh-cookie public access and protected-role regression verification."""
import os,time,json
from pathlib import Path

def main():
 root=Path(__file__).resolve().parents[2];work=root.parent/'floorhawk-modal';out=work/'verification/public-anonymous';out.mkdir(parents=True,exist_ok=True);os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(root/'cache/playwright')
 from playwright.sync_api import sync_playwright
 report={'passed':False,'browser_errors':[]};url='https://sm-hariprasanth--web.us-east.modal.run'
 def wait(page,expression,seconds=180):
  end=time.monotonic()+seconds
  while time.monotonic()<end:
   if page.evaluate(expression):return
   page.wait_for_timeout(150)
  raise AssertionError(expression+'; '+page.inner_text('#status'))
 with sync_playwright()as pw:
  b=pw.chromium.launch(headless=True)
  try:
   c=b.new_context();assert not c.cookies();p=c.new_page();p.on('pageerror',lambda e:report['browser_errors'].append(str(e)));response=p.goto(url,timeout=60000);wait(p,"() => typeof S!=='undefined' && !!S.config",60);assert p.locator('input[name=code]').count()==0;report['public_no_code']=True;assert response.headers.get('cache-control')=='private, no-store';cookie=next(x for x in c.cookies()if x['name']=='floorhawk-session');assert cookie['secure']and cookie['httpOnly']and cookie['sameSite']=='Strict'
   p.click('#preloadedTab');p.select_option('#galleryFormat','PNG');p.select_option('#galleryDrawing','png-a');wait(p,"() => S.validated && S.galleryId==='png-a'");p.select_option('#galleryQuestion','q2');start=time.monotonic();p.click('#run');wait(p,"() => S.job?.prediction && !S.busy");wait(p,"() => (S.activeEvidence || []).length>0 && S.boxes.length>0",60);job=p.evaluate('S.job');assert job['status']=='success';final=job['prediction']['paired']['hybrid'];assert final['status']=='success';report['example']={'job_id':job['id'],'question':job['question'],'answer':final.get('answer'),'evidence_regions':len(p.evaluate('S.activeEvidence || []')),'seconds':time.monotonic()-start,'release':job.get('submission_release')};(out/'job.json').write_text(json.dumps(job,indent=2));p.screenshot(path=str(out/'public.png'))
   other=b.new_context();assert not other.cookies();q=other.new_page();q.goto(url);wait(q,"() => typeof S!=='undefined' && !!S.config",60);second=next(x for x in other.cookies()if x['name']=='floorhawk-session');assert second['value']!=cookie['value'];assert q.request.get(url+'/api/jobs/'+job['id']).status==404;report['distinct_anonymous_sessions']=True;report['owner_isolation']=True
   for role in ['judges','presenter']:
    ctx=b.new_context();assert not ctx.cookies();page=ctx.new_page();u='https://sm-hariprasanth--'+role+'.us-east.modal.run';page.goto(u,timeout=60000);assert page.locator('input[name=code]').is_visible();assert page.request.get(u+'/api/jobs/'+job['id']).status==401;report[role]={'code_form':True,'unauthenticated_job_status':401};ctx.close()
   assert not report['browser_errors'];report['passed']=True
  finally:(out/'report.json').write_text(json.dumps(report,indent=2));b.close();print(json.dumps(report,indent=2))
if __name__=='__main__':main()
