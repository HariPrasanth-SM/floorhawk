"""Bounded normal-login provider and real queue verification; no gold payloads."""
import argparse,json,os,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--readiness',action='store_true');p.add_argument('--phase',choices=['hybrid','queue'],required=True);p.add_argument('--only-role',choices=['presenter','judges','public']);a=p.parse_args();root=Path(__file__).resolve().parents[2];work=root.parent/'floorhawk-modal';out=work/'verification/event-readiness';out.mkdir(parents=True,exist_ok=True);os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(root/'cache/playwright')
 from playwright.sync_api import sync_playwright
 report={'phase':a.phase,'passed':False,'jobs':[],'browser_errors':[]};deadline=time.monotonic()+480
 def wait(page,expr,seconds=180):
  end=min(deadline,time.monotonic()+seconds)
  while time.monotonic()<end:
   if page.evaluate(expr):return
   page.wait_for_timeout(200)
  raise AssertionError(expr+' status='+page.inner_text('#status'))
 with sync_playwright()as pw:
  b=pw.chromium.launch(headless=True)
  def login(role):
   label={'public':'web'}.get(role,role);url=f'https://sm-hariprasanth--{label}.us-east.modal.run';c=b.new_context(viewport={'width':1366,'height':768});page=c.new_page();page.on('pageerror',lambda e:report['browser_errors'].append(str(e)));page.goto(url);page.fill('input[name=code]',(work/'.secrets'/({'public':'event'}.get(role,role)+'-access-code')).read_text());page.click('button');wait(page,"() => typeof S!=='undefined' && !!S.config",60);return page,url
  def prepare(page,source,fmt,question):
   page.click('#preloadedTab');page.select_option('#galleryFormat',fmt);page.select_option('#galleryDrawing',source);wait(page,'() => S.validated && S.galleryId==='+json.dumps(source));page.fill('#question',question);assert page.locator('#expectedReference').is_hidden()
  def finish(page,url,label,start):
   wait(page,"() => !!S.job?.prediction && !S.busy",240);job=page.evaluate('S.job');
   if a.phase=='hybrid':wait(page,'() => (S.activeEvidence || []).length>0 && S.boxes.length>0',60)
   h=job['prediction']['paired']['hybrid'];local=job['prediction']['paired']['local'];(out/(a.phase+'-'+label+'.json')).write_text(json.dumps(job,indent=2));r={'role':label,'job_id':job['id'],'job_status':job['status'],'hybrid_status':h['status'],'provider_invoked':h.get('provider_invoked'),'provider_attempts':h.get('provider_attempts',0),'answer':h.get('answer'),'local_answer':local.get('answer'),'evidence_ids':h.get('evidence_ids',[]),'localized_evidence_count':len(page.evaluate('S.activeEvidence || []')),'generation':h.get('generation',[]),'elapsed_seconds':time.monotonic()-start,'finished_monotonic':time.monotonic(),'resident':job.get('resident'),'failure':h.get('failure_reason')or h.get('explanation'),'release':job.get('submission_release'),'server_timing':job.get('presenter_timing')};report['jobs'].append(r);print(json.dumps(r),flush=True);return job,r
  try:
   if a.phase=='hybrid':
    for role in ([a.only_role]if a.only_role else ['presenter','judges','public']):
     page,url=login(role);before=page.request.get(url+'/api/budget').json();prepare(page,'png-a','PNG','How many kitchens are shown on this floor plan?');start=time.monotonic();page.click('#run');job,r=finish(page,url,role,start);after=page.request.get(url+'/api/budget').json();r['budget_before']=before;r['budget_after']=after;assert r['provider_attempts']>=1,r;assert r['hybrid_status']=='success',r;assert r['evidence_ids']or r['localized_evidence_count'],r;assert after['requests_reserved']>before['requests_reserved'];page.screenshot(path=str(out/('hybrid-'+role+'.png')))
   else:
    pages=[]
    for i,q in enumerate(['How many windows are shown on this floor plan?','How many doors are shown on this floor plan?','How many sinks are shown on this floor plan?'][:2]):
     page,url=login('public');prepare(page,'png-a','PNG',q);pages.append((page,url,'public-'+str(i)))
    peers=[]
    for role in ['presenter','judges']:
     page,url=login(role);prepare(page,'ifc-a','IFC','How many storeys are in this IFC model?');peers.append((page,url,role))
    starts={}
    for page,url,label in pages+peers:starts[label]=time.monotonic();page.click('#run')
    for page,url,label in pages:wait(page,"() => !!S.job?.id || location.search.startsWith('?job=')",30)
    snapshot=[]
    for page,url,label in pages:
     ident=page.evaluate("S.job?.id || new URL(location.href).searchParams.get('job')");r=page.request.get(url+'/api/jobs/'+ident);snapshot.append({'label':label,'status':r.json().get('status'),'ui_status':page.inner_text('#status'),'job_id':ident})
    report['public_queue_snapshot']=snapshot;assert any(x['status']=='queued'for x in snapshot),snapshot
    first,url,label=pages[0];ident=snapshot[0]['job_id'];dup=first.request.post(url+'/api/jobs',data={'gallery_id':'png-a','question':'How many windows are shown on this floor plan?'},headers={'Idempotency-Key':first.evaluate('S.requestKey')});assert dup.status==202 and dup.json()['id']==ident;report['duplicate_prevented']=True;assert pages[1][0].request.get(url+'/api/jobs/'+ident).status==404;report['owner_isolation']=True
    # Observe independent serving peers while the public queue drains.
    for page,url,label in peers:finish(page,url,label,starts[label])
    for page,url,label in pages:finish(page,url,label,starts[label])
    assert all(j['job_status']=='success'and j['hybrid_status']=='success'for j in report['jobs']);public_workers={j['resident']['worker_id']for j in report['jobs']if j['role'].startswith('public')};peer_workers={j['resident']['worker_id']for j in report['jobs']if not j['role'].startswith('public')};assert not public_workers&peer_workers;report['isolated_worker_ids']=True;report['completion_order_note']='Observation order is not server completion order; use recorded server timings and isolated worker IDs.'
   assert not report['browser_errors'];report['passed']=True
  finally:
   (out/(a.phase+'-report.json')).write_text(json.dumps(report,indent=2));b.close();print(json.dumps({k:v for k,v in report.items()if k!='jobs'},indent=2))
if __name__=='__main__':main()
