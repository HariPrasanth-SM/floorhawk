"""Restricted real-development gallery and explicit non-overlapping dollar envelope."""
import sys,json,time,uuid,hashlib,secrets,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from runtime_paths import DATASET_ROOT
from qa.common import sha
from v2.budget import Ledger
import modal,ifcopenshell
W=ROOT.parent/'floorhawk-modal';short=json.loads((W/'presenter-shortlist.json').read_text());rows=[]
configs=[('png-a','data/cubicasa5k/high_quality_architectural-10478.png',['count_doors','count_windows','count_toilet_fixtures']),('png-b','data/cubicasa5k/high_quality_architectural-12093.png',['count_doors','count_windows','count_sinks'])]
for ident,path,cats in configs:
 selected=[next(q for q in short[path]if q['category']==cat)for cat in cats];rows.append({'id':ident,'path':path,'format':'PNG','suggestions':selected})
for ident,path in [('pdf-a','data/swiss_dwellings/site10037_bldg14632_floor39102.pdf'),('pdf-b','data/swiss_dwellings/site420_bldg1063_floor4654.pdf')]:
 qs=short[path];area=[q for q in qs if q['type']=='area'and'room 'in q['question']][:2];labels=[q for q in qs if q['category']=='count_labelled_rooms'][:1];rows.append({'id':ident,'path':path,'format':'PDF','suggestions':labels+area})
for ident,path,targets in [('ifc-a','data/ifc_bench/fzk_house_arc.ifc',[('windows','IfcWindow'),('spaces','IfcSpace'),('storeys','IfcBuildingStorey')]),('ifc-b','data/ifc_models/resbim-9_model.ifc',[('windows','IfcWindow'),('doors','IfcDoor'),('storeys','IfcBuildingStorey')])]:
 m=ifcopenshell.open(str(DATASET_ROOT/path));qs=[{'question':'How many '+name+' are in this IFC model?','reference':len(m.by_type(cls)),'unit':'count','category':'explicit_'+cls,'reference_method':'Independent source entity count; no inference output used'}for name,cls in targets];qs.append({'question':'What IFC schema does this model use?','reference':m.schema,'unit':None,'category':'schema','reference_method':'Original IFC schema header'});rows.append({'id':ident,'path':path,'format':'IFC','suggestions':qs})
for row in rows:
 p=DATASET_ROOT/row['path'];row.update(filename=row['id']+p.suffix,name=p.stem,source_path=row['path'],source_sha256=sha(p),bytes=p.stat().st_size,scope='page1 / current drawing'if row['format']!='IFC'else'explicit occurrences in entire IFC model',credit='CubiCasa5K; CC BY-NC-SA4.0'if row['format']=='PNG'else'Supplied Stoa development source; redistribution license not established; restricted presenter only')
 for i,q in enumerate(row['suggestions']):q.update(id='q'+str(i+1),verification='Saved development case/source checked; fresh presenter verification pending')
# Dollar envelope is accounted once in canonical lifetime reservations, never cloned.
ledger=Ledger();op='presenter-dollar-envelope-v1'
with ledger.connect()as c:
 c.execute('BEGIN IMMEDIATE');old=c.execute('select id,reserved from attempts where operation=?',(op,)).fetchall()
 if not old:
  total=c.execute('select coalesce(sum(reserved),0)from attempts').fetchone()[0]
  if total+80>100:raise RuntimeError('Insufficient unallocated canonical monetary capacity')
  ident=uuid.uuid4().hex;c.execute('insert into attempts values(?,?,?,?,?,?)',(ident,time.time(),op,80,'allocated-presenter-envelope',json.dumps({'kind':'non-HTTP budget allocation'})))
 else:ident,amount=old[0];assert amount==80
budget=modal.Dict.from_name('floorhawk-presenter-budget-v1',create_if_missing=True);budget.put('ui-release-grant-v1',{'allocated_usd':80,'canonical_allocation_id':ident,'records':[],'enabled':True,'note':'No query counter/permit cap; bounded by non-overlapping80USD reservation envelope'},skip_if_exists=True)
v=modal.Volume.from_name('floorhawk-assets');existing={x.path for x in v.listdir('/presenter-gallery-v1')}if False else set()
with v.batch_upload()as b:
 for r in rows:b.put_file(DATASET_ROOT/r['path'],'/presenter-gallery-v1/'+r['filename'])
modal.Dict.from_name('floorhawk-presenter-gallery-v1',create_if_missing=True).put('catalog',rows)
sec=W/'.secrets';p=sec/'presenter-access-code'
if not p.exists():p.write_text(secrets.token_urlsafe(20));p.chmod(0o600)
k=sec/'presenter-session-key'
if not k.exists():k.write_text(secrets.token_hex(32));k.chmod(0o600)
try:modal.Secret.objects.create('floorhawk-presenter-access',{'FLOORHAWK_ACCESS_HASH':hashlib.sha256(p.read_bytes()).hexdigest(),'FLOORHAWK_SESSION_KEY':k.read_text()},allow_existing=False)
except Exception as e:
 if type(e).__name__!='AlreadyExistsError':raise
st=modal.Dict.from_name('floorhawk-presenter-control-v1',create_if_missing=True);st.put('admission-state-v1',{'events':[],'jobs':{},'idempotency':{},'live':False,'gemini':True},skip_if_exists=True)
(W/'presenter-gallery-manifest.json').write_text(json.dumps(rows,indent=2));record=W/'recording-assets';record.mkdir(exist_ok=True)
for r in [rows[0],rows[2]]:shutil.copy2(DATASET_ROOT/r['path'],record/r['filename'])
print(json.dumps({'sources':len(rows),'questions':sum(len(r['suggestions'])for r in rows),'presenter_dollar_envelope':80,'query_count_cap':None,'access_file':str(p.relative_to(W)),'canonical_summary':ledger.summary()}))
