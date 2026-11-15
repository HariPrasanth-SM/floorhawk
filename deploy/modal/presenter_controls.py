"""Trusted presenter admission, separate from public visitor quotas."""
import time,secrets
from deploy.modal.security import Controls,Denied
class PresenterControls(Controls):
 def reserve(self,session,idem,upload,release,mode):
  now=time.time()
  with self.transaction()as s:
   old=s['idempotency'].get(session+':'+idem)
   if old and now-old['time']<300:return old['id'],False
   if not s.get('live'):raise Denied('Presenter is not ready',5)
   active=[j for j in s['jobs'].values()if j['status']in ['reserved','queued','running']]
   if any(j['owner']==session for j in active):raise Denied('One active presenter request per session',2)
   from deploy.modal.event_policy import active as event_active,role
   if len(active)>=(role()['max_active_and_waiting']if event_active()else 3):raise Denied('Presenter queue full (two waiting)',2)
   ident=secrets.token_hex(16);s['jobs'][ident]={'owner':session,'status':'reserved','release':release,'mode':mode,'created':now};s['idempotency'][session+':'+idem]={'id':ident,'time':now};s['events'].append({'id':ident,'time':now,'upload':0});return ident,True
 def allowance(self):
  s=self.store.get('admission-state-v1',{});return {'questions_remaining':None,'uploads_remaining':None,'retry_seconds':0,'live':s.get('live',False),'gemini':s.get('gemini',False),'role':'authenticated-presenter','queue_capacity':__import__('deploy.modal.event_policy',fromlist=['role']).role()['max_active_and_waiting']}
