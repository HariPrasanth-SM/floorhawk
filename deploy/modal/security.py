"""Atomic admission under Modal Dict put(skip_if_exists=True), fail closed on crash.
The guard has NO automatic lease expiry: an interrupted lock requires operator
verification and manual recovery, never an unsafe timeout-based unlock.
"""
import contextlib,time,hashlib,secrets,math
class Denied(Exception):
 def __init__(self,message,retry=1):super().__init__(message);self.retry=retry
class Controls:
 def __init__(self,store,code_hash):self.store=store;self.code_hash=code_hash
 @contextlib.contextmanager
 def transaction(self):
  key='admission-lock-v1';owner=secrets.token_hex(16)
  until=time.monotonic()+1.5
  while not self.store.put(key,owner,skip_if_exists=True):
   if time.monotonic()>=until:raise Denied('Admission busy; retry shortly',2)
   time.sleep(.04)
  try:
   state=self.store.get('admission-state-v1',{'events':[],'jobs':{},'idempotency':{},'live':False,'gemini':False})
   yield state
   self.store.put('admission-state-v1',state)
  finally:self.store.pop(key,None)
 def authenticate(self,code):return secrets.compare_digest(hashlib.sha256(code.encode()).hexdigest(),self.code_hash)
 def reserve(self,session,idem,upload,release,mode):
  now=time.time()
  with self.transaction()as s:
   old=s['idempotency'].get(session+':'+idem)
   if old and now-old['time']<(5 if idem.startswith('auto:')else 300):return old['id'],False
   from deploy.modal.event_policy import active,policy,role
   event=active();cfg=policy()if event else{}
   cap=s.get('compute_limit_usd',7)
   if not event and (not isinstance(cap,(int,float))or isinstance(cap,bool)or not math.isfinite(cap)or cap<0):raise Denied('Invalid compute allocation; admission stopped',60)
   if not event and s.get('compute_reservation_usd',0)+.25>cap:raise Denied('Conservative compute reservation limit reached',60)
   if not s['live']and session not in s.get('verification_sessions',[]):raise Denied('Live inference disabled',60)
   active=[j for j in s['jobs'].values()if j['status']in ['reserved','queued','running']]
   if any(j['owner']==session for j in active):raise Denied('One active request per visitor; poll your current job',3)
   if len(active)>=(role()['max_active_and_waiting']if event else 11):raise Denied('Queue full; wait for an active job to complete',5)
   events=[e for e in s['events']if now-e['time']<300];s['events']=events
   upload_key=session+':'+upload if isinstance(upload,str)else None
   upload=bool(upload)and not(upload_key and any(e.get('upload_key')==upload_key for e in events))
   questions=len(events);uploads=sum(e['upload']for e in events)
   recent=[e for e in events if e.get('owner')==session and now-e['time']<cfg.get('submission_burst_window_seconds',10)]
   if event and len(recent)>=cfg['submission_burst_per_session']:raise Denied('Rapid submission limit; retry shortly',10)
   if not event and questions>=5:raise Denied('Question allowance exhausted',max(1,int(300-(now-events[0]['time']))))
   if not event and upload and uploads>=2:raise Denied('Upload allowance exhausted',max(1,int(300-(now-next(e['time']for e in events if e['upload'])))))
   if mode=='hybrid'and not s['gemini']:raise Denied('Gemini disabled: shared lifetime accounting not connected',60)
   if not event:s['compute_reservation_usd']=s.get('compute_reservation_usd',0)+.25
   s['accepted_event_requests']=s.get('accepted_event_requests',0)+int(event)
   ident=secrets.token_hex(16);s['jobs'][ident]={'owner':session,'status':'reserved','release':release,'mode':mode,'created':now};s['idempotency'][session+':'+idem]={'id':ident,'time':now};s['events'].append({'id':ident,'time':now,'owner':session,'upload':int(upload),'upload_key':upload_key})
   return ident,True
 def publish(self,reserved,real,status='queued',metadata=None):
  with self.transaction()as s:
   row=s['jobs'].pop(reserved);row['status']=status;row.update(metadata or {});s['jobs'][real]=row
   for item in s['idempotency'].values():
    if item['id']==reserved:item['id']=real
   for item in s['events']:
    if item['id']==reserved:item['id']=real
 def rollback(self,ident):
  with self.transaction()as s:
   existed=s['jobs'].pop(ident,None)
   from deploy.modal.event_policy import active
   if existed and not active():s['compute_reservation_usd']=max(0,s.get('compute_reservation_usd',0)-.25)
   s['events']=[e for e in s['events']if e['id']!=ident];s['idempotency']={k:v for k,v in s['idempotency'].items()if v['id']!=ident}
 def own(self,session,ident):
  row=self.store.get('admission-state-v1',{}).get('jobs',{}).get(ident)
  if not row or row['owner']!=session:raise Denied('Job not found',0)
  return row
 def complete(self,ident,status,metadata=None):
  with self.transaction()as s:
   if ident in s['jobs']:s['jobs'][ident].update(status=status,**(metadata or {}))
 def allowance(self):
  s=self.store.get('admission-state-v1',{});now=time.time();e=[e for e in s.get('events',[])if now-e['time']<300]
  from deploy.modal.event_policy import active,role
  if active():return {'questions_remaining':None,'uploads_remaining':None,'estimated_queries_remaining':None,'application_spending_cap_enforced':False,'retry_seconds':0,'queue_capacity':role()['max_active_and_waiting'],'live':s.get('live',False),'gemini':bool(s.get('gemini',False))}
  cap=s.get('compute_limit_usd',7);spent=s.get('compute_reservation_usd',0)
  return {'compute_limit_usd':cap,'compute_reserved_usd':spent,'estimated_queries_remaining':max(0,int((cap-spent+1e-9)/.25)),'questions_remaining':max(0,5-len(e)),'uploads_remaining':max(0,2-sum(x['upload']for x in e)),'retry_seconds':max(0,int(300-(now-e[0]['time'])))if e else 0,'live':s.get('live',False),'gemini':bool(s.get('gemini',False))}
