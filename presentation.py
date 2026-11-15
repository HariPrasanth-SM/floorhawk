"""Saved evidence selection only. No model or provider calls."""
import copy,json
from pathlib import Path
from qa.common import sha

def catalog(job):
 p=job.get('prediction',{});local=p.get('paired',{}).get('local',p);rows=[]
 for item in [local,p]:
  rows.extend(item.get('evidence',[]));rows.extend(item.get('cumulative_evidence',{}).get('evidence',[]))
 record=local.get('shared_evidence',{})
 if record.get('path')and record.get('sha256'):
  path=Path(record['path'])
  if path.is_file()and sha(path)==record['sha256']:rows.extend(json.loads(path.read_text()).get('facts',{}).get('entities',[]))
 return {str(e.get('id')or e.get('guid')):copy.deepcopy(e)for e in rows if e.get('id')or e.get('guid')}

def selected(job,mode):
 p=job.get('prediction',{});pair=p.get('paired',{});local=pair.get('local',p)
 if mode!='hybrid'or not pair:return copy.deepcopy(local.get('evidence',[]))
 h=pair.get('hybrid',{});lookup=catalog(job)
 for e in h.get('model_proposed_regions',[]):lookup[e['id']]=dict(e,origin_model='Gemini',verified_local_evidence=False,evidence_role='Model-proposed region; unverified')
 rows=[lookup[i] for i in h.get('evidence_ids',[])if i in lookup]
 for ident in h.get('evidence_ids',[]):
  if ident.startswith('source-view-page-'):
   rows.append({'id':ident,'kind':'source_overview','origin_model':'Gemini','page':int(ident.rsplit('-',1)[1]),'localization':'Page overview only; no per-object locations returned'})
 if h.get('status')=='success':
  seen={e['id']for e in rows}
  rows.extend(lookup[e['id']]for e in h.get('model_proposed_regions',[])if e['id']not in seen)
 return rows
