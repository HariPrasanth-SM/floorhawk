"""Bounded, normal-login browser verification for versioned event roles."""
import argparse,json,time,os,sys,re
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--event',action='store_true');p.add_argument('--role',choices=['candidate','presenter','judges','public'],default='candidate');p.add_argument('--limit',type=int,default=12);p.add_argument('--all',action='store_true');p.add_argument('--manual',action='store_true');p.add_argument('--fallback',action='store_true');p.add_argument('--sessions',type=int,choices=[0,20],default=0);p.add_argument('--active-limit',action='store_true');p.add_argument('--tag',default='');a=p.parse_args()
 root=Path(__file__).resolve().parents[2];work=root.parent/'floorhawk-modal';label={'candidate':'overnight-candidate','presenter':'presenter','judges':'judges','public':'web'}[a.role];url=f'https://sm-hariprasanth--{label}.us-east.modal.run';codefile=work/'.secrets'/({'public':'event'}.get(a.role,a.role)+'-access-code');out=work/'verification'/('overnight-'+a.role);out.mkdir(parents=True,exist_ok=True);os.environ['PLAYWRIGHT_BROWSERS_PATH']=str(root/'cache/playwright')
 sys.path.insert(0,str(root))
 from playwright.sync_api import sync_playwright
 from evaluation.numeric import score
 if a.tag and not a.tag.replace('-','').isalnum():raise ValueError('Invalid report tag')
 if a.tag:out=out/a.tag;out.mkdir(exist_ok=False)
 report={'url':url,'passed':False,'rows':[]};errors=[];posts=[];deadline=time.monotonic()+900;poll_failure=[False]
 def wait(page,expression,seconds=120):
  until=min(deadline,time.monotonic()+seconds)
  while time.monotonic()<until:
   if page.evaluate(expression):return
   page.wait_for_timeout(200)
  raise AssertionError(expression+'; status='+page.inner_text('#status'))
 try:
  with sync_playwright()as pw:
   browser=pw.chromium.launch(headless=True);context=browser.new_context(viewport={'width':1366,'height':768});page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:posts.append(r.url)if r.method=='POST'and r.url.endswith('/api/jobs')else None);page.goto(url);page.fill('input[name=code]',codefile.read_text());page.click('button');wait(page,"() => typeof S!=='undefined' && !!S.config",60);report['normal_login']=True
   def transient(route):
    if not poll_failure[0]and re.search(r'/api/jobs/[a-f0-9]{32}$',route.request.url):poll_failure[0]=True;route.fulfill(status=503,content_type='application/json',body='{"error":"Bounded polling interruption test"}')
    else:route.continue_()
   page.route('**/api/jobs/*',transient)
   catalog=page.request.get(url+'/api/gallery').json();plan=[(s,q)for s in catalog for q in (s['suggestions']if a.all else s['suggestions'][:2])][:a.limit]
   for index,(source,suggestion)in enumerate(plan):
    if time.monotonic()>deadline-90:raise TimeoutError('Bounded browser verification deadline')
    page.click('#preloadedTab');page.select_option('#galleryFormat',source['format']);page.select_option('#galleryDrawing',source['id']);wait(page,'() => S.validated===true && S.galleryId==='+json.dumps(source['id']));page.select_option('#galleryQuestion',suggestion['id']);before=len(posts);began=time.monotonic();page.click('#run')
    if index==0 and a.active_limit:
     wait(page,"() => S.busy && location.search.startsWith('?job=')",60);probe=page.request.post(url+'/api/jobs',data={'gallery_id':source['id'],'question':'How many windows are shown on this floor plan?','mode':'hybrid'},headers={'Idempotency-Key':'bounded-active-probe-'+str(time.time_ns())});assert probe.status==429,probe.status;assert 'active request'in probe.json()['error'].lower();report['deployed_one_active_limit']=True
    wait(page,"() => !!S.job?.prediction && !S.busy",180);job=page.evaluate('S.job');assert len(posts)==before+1;assert job['question']==suggestion['question'];prediction=job['prediction'];final=prediction.get('final')or prediction.get('paired',{}).get('hybrid',{});local=prediction.get('paired',{}).get('local',{});assert job['status']=='success',job.get('error');assert final.get('provider_attempts',0)==0,'This browser pass is restricted to deterministic specialist cases';row={'source':source['id'],'question':suggestion['question'],'answer':final.get('answer'),'status':final.get('status'),'local':local.get('answer'),'reference':suggestion.get('reference'),'unit':suggestion.get('unit'),'seconds':time.monotonic()-began,'job_id':job['id'],'resident':job.get('resident'),'evidence_n':len(prediction.get('evidence',[]))};report['rows'].append(row);(out/f'job-{index}.json').write_text(json.dumps(job,indent=2));print(json.dumps(row),flush=True)
    grade=score({'type':'count'if suggestion.get('unit')=='count'else'area','answer':suggestion.get('reference'),'unit':suggestion.get('unit')},final);row['match']=grade.get('passed')is True;assert row['match'],row
    wait(page,'() => S.activeEvidence && S.activeEvidence.length==='+str(len(prediction.get('evidence',[]))),60)
    if source['id']=='ifc-a'and 'windows' in suggestion['question']:
     wait(page,'() => window.IFCViewDebug?.meshCount>0 && window.IFCViewDebug.highlightedGuids.length===11',90);report['verified_ifc_geometry']=page.evaluate('window.IFCViewDebug')
    assert page.locator('#expectedReference').is_visible();page.fill('#question',suggestion['question']+' custom');assert not page.locator('#expectedReference').is_visible();assert page.locator('nav button.active').count()==1
    for width,height in[(1366,768),(1920,1080)]:
     page.set_viewport_size({'width':width,'height':height});assert page.evaluate('document.documentElement.scrollHeight<=innerHeight && document.documentElement.scrollWidth<=innerWidth')
    if source['format']!='IFC':assert page.request.get(url+'/api/jobs/'+job['id']+'/annotated.png?page=1').ok
    if index==0:
     duplicate=page.request.post(url+'/api/jobs',data={'gallery_id':source['id'],'question':suggestion['question'],'mode':'hybrid'},headers={'Idempotency-Key':page.evaluate('S.requestKey')});assert duplicate.status==202;assert duplicate.json()['id']==job['id'];report['duplicate_same_job_without_resubmit']=True
     oldposts=len(posts);page.reload();wait(page,"() => !!S.job?.prediction && !S.busy",60);assert page.evaluate('S.job.id')==job['id'];assert len(posts)==oldposts;report['reload_without_resubmit']=True
    page.screenshot(path=str(out/f'case-{index}.png'))
   # Ownership is verified through a second independently authenticated visitor.
   second=browser.new_context();other=second.new_page();other.goto(url);other.fill('input[name=code]',codefile.read_text());other.click('button');wait(other,"() => typeof S!=='undefined' && !!S.config",60)
   if report['rows']:
    forbidden=other.request.get(url+'/api/jobs/'+report['rows'][0]['job_id']);assert forbidden.status==404;report['cross_session_isolation']=True
   second.close()
   if a.manual:
    page.click('#workspaceTab')
    manual=[('png-a.png',catalog[0]['suggestions'][:2]),('pdf-a.pdf',[catalog[2]['suggestions'][1]]),('ifc-a.ifc',[catalog[4]['suggestions'][0]])]
    report['manual_uploads']=[]
    for filename,questions in manual:
     page.set_input_files('#upload',str(work/'recording-assets'/filename));wait(page,'() => S.validated && S.file?.name==='+json.dumps(filename));assert page.evaluate('!!S.image && !S.job');assert page.locator('#expectedReference').is_hidden()
     for q in questions:
      before=len(posts);page.fill('#question',q['question']);assert page.locator('#expectedReference').is_hidden();started=time.monotonic();page.click('#run');wait(page,"() => !!S.job?.prediction && !S.busy",180);job=page.evaluate('S.job');assert len(posts)==before+1;assert job['source_name']==filename;assert job['question']==q['question'];assert job.get('expected_reference')is None;wait(page,'() => S.activeEvidence && S.activeEvidence.length>0',60);report['manual_uploads'].append({'filename':filename,'question':q['question'],'answer':page.inner_text('#modelCount'),'reference':q['reference'],'seconds':time.monotonic()-started,'job_id':job['id']})
      if filename.endswith('.ifc'):wait(page,'() => window.IFCViewDebug?.meshCount===107 && window.IFCViewDebug.highlightedGuids.length===11',90);report['manual_ifc_source_geometry']=True
      else:assert page.request.get(url+'/api/jobs/'+job['id']+'/annotated.png?page=1').ok
   if a.fallback:
    allowance=page.request.get(url+'/api/allowance').json();assert not allowance['gemini'],'Fallback check requires operator-disabled role provider switch'
    page.click('#workspaceTab');page.set_input_files('#upload',str(work/'recording-assets/png-a.png'));wait(page,"() => S.validated && S.file?.name==='png-a.png'");page.fill('#question','How many bedrooms are shown on this floor plan?');page.click('#run');wait(page,"() => !!S.job?.prediction && !S.busy",180);job=page.evaluate('S.job');hybrid=job['prediction']['paired']['hybrid'];assert hybrid['status']in ['provider_error','blocked','disabled'];assert hybrid.get('provider_attempts',0)==0;assert page.inner_text('#answerSource')=='Result';assert 'Local fallback'in page.inner_text('#answerStatus');(out/'fallback-job.json').write_text(json.dumps(job,indent=2));report['provider_stop_fallback']={'status':hybrid['status'],'provider_attempts':hybrid.get('provider_attempts',0),'local_answer':job['prediction']['paired']['local'].get('answer'),'display_label':page.inner_text('#answerStatus')}
   if a.sessions:
    visitors=[]
    for i in range(a.sessions):
     c=browser.new_context(viewport={'width':1366,'height':768});tab=c.new_page();tab.goto(url);tab.fill('input[name=code]',codefile.read_text());tab.click('button');wait(tab,"() => typeof S!=='undefined' && !!S.config",60);assert tab.locator('nav button.active').count()==1;visitors.append((c,tab))
    for c,tab in visitors:tab.evaluate("window.sessionProbe=fetch('/api/gallery').then(r=>r.status)")
    assert all(tab.evaluate('window.sessionProbe')==200 for c,tab in visitors);report['authenticated_browser_sessions']=len(visitors);report['session_probe_scope']='20 simultaneously open normal-login browser contexts; gallery GETs only, no20GPU-load claim'
    for c,tab in visitors:c.close()
   report['health']=page.request.get(url+'/health').json();report['allowance']=page.request.get(url+'/api/allowance').json();report['poll_retry_without_resubmit']=poll_failure[0];report['browser_errors']=errors;assert not errors;report['passed']=True;browser.close()
 finally:
  (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items()if k!='rows'},indent=2))
