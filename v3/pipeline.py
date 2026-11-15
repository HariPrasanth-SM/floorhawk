"""Shared version3 QA: local specialists, geometry postprocessing, targeted review.
References are never imported; Local never reads provider keys/cloud caches.
"""
import copy,json,time
from pathlib import Path
from qa.common import ROOT,sha
from v2.pipeline import Pipeline as Previous
class Pipeline(Previous):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.adapter_release='v3';self.legacy_ocr_enabled=self.ocr;self.ocr=False;self.config=json.loads((ROOT/'v3/config.json').read_text());self.v3_sources={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'v3').glob('*.py')};self.v3_sources['v3/config.json']=sha(ROOT/'v3/config.json');self.v3_sources['v3/adapter-config.json']=sha(ROOT/'v3/adapter-config.json')
 def _answer(self,file,question,sample_id=None,progress=None,mode='local'):
  started=time.perf_counter();r=super()._answer(file,question,sample_id,progress,'local');r.update(controller_version=self.config['version'],execution_mode=mode,v3_source_revision=self.v3_sources);r['cloud']={'status':'off' if mode=='local' else 'not-needed','requests':0,'estimated_usd_reserved':0};task=r.get('task',{});target=task.get('target');unfiltered=task.get('operation')=='count' and not task.get('filters') and task.get('scope')!='model'
  if r.get('input_kind')=='raster' and unfiltered:
   strategy=self.config.get('room_strategies',{}).get(target)
   if strategy:
    try:
     from .rooms import predict as room_predict,native_label_answer,MODEL as room_weights
     if strategy=='learned' and sha(room_weights)!=self.config['room_model_sha256']:raise ValueError('Room checkpoint checksum mismatch')
     if progress:progress('Fusing room semantics, fixture geometry and observed labels',0,1)
     r['escalation_steps']+=1;r['before_room_refinement']={k:copy.deepcopy(r.get(k)) for k in ('answer','status','evidence','route')};proposal=native_label_answer(file,target) if strategy=='native-label' else room_predict(file,target);r.update(proposal);r['stage_timings']['room_refinement']=proposal['room_fusion_timing']
    except Exception as e:r['warnings'].append('Room specialist unavailable; previous local result retained: '+type(e).__name__)
   if target=='shower_bath' and self.config.get('wash_head'):
    try:
     from .wash import predict as wash_predict,MODEL as wash_weights
     if sha(wash_weights)!=self.config['wash_model_sha256']:raise ValueError('Washing-region checkpoint checksum mismatch')
     if progress:progress('Evaluating weak washing-installation region hypotheses',0,1)
     r['escalation_steps']+=1;r['before_wash_refinement']={k:copy.deepcopy(r.get(k)) for k in ('answer','status','evidence','route')};proposal=wash_predict(file);r.update(proposal);r['stage_timings']['wash_refinement']=proposal['fixture_timing']
    except Exception as e:r['warnings'].append('Washing-region specialist unavailable; previous local result retained: '+type(e).__name__)
   if target=='storey' and self.config.get('storey_layout_model'):
    try:
     from .layouts import predict as layout_predict,MODEL as layout_weights
     if sha(layout_weights)!=self.config['layout_model_sha256']:raise ValueError('Layout checkpoint checksum mismatch')
     r['escalation_steps']+=1;r['before_layout_refinement']={k:copy.deepcopy(r.get(k)) for k in ('answer','status','evidence','route')};proposal=layout_predict(file);r.update(proposal);r['stage_timings']['layout_refinement']=proposal['layout_timing']
    except Exception as e:r['warnings'].append('Experimental layout model unavailable; previous local result retained: '+type(e).__name__)
   if target in ('sink','toilet_fixture') and self.config.get('fixture_profile') and r.get('escalation_steps',0)<2:
    try:
     from .raster import parse
     from qa.tools import raster_answer
     if progress:progress('Refining small fixture geometry at higher resolution',0,1)
     r['escalation_steps']+=1;facts=parse(file,self.config['fixture_profile']);proposal=raster_answer(facts,task,question)
     if proposal['status']=='success':
      r['before_fixture_refinement']={k:copy.deepcopy(r.get(k)) for k in ('answer','status','evidence','route')};r.update(proposal);r.update(route='raster.cubicasa-fixtures.v3',model=facts['model'],preprocessing=facts['preprocessing'],fixture_timing=dict(facts['timing'],cache_hit=facts['cache_hit'],parse_seconds=facts['parse_seconds']));r['stage_timings']['fixture_refinement']=r['fixture_timing']
    except Exception as e:r['warnings'].append('Higher-resolution fixture refinement unavailable; previous local result retained: '+type(e).__name__)
   if target=='sauna' and self.config.get('sauna_room_graph') and strategy!='learned':
    try:
     from .room_graph import sauna
     facts,_,_,_=self.base.facts(file);proposal=sauna(facts)
     if proposal:
      r['room_graph_alternative']=copy.deepcopy(proposal)
      if r['status']=='success' and r['answer']!=proposal['answer']:r.update(status='abstained',answer=None);r['warnings'].append('OCR and bench-in-room sauna hypotheses disagree; review required.')
      else:r.update(proposal)
    except Exception as e:r['warnings'].append('Sauna room-graph postprocessing unavailable: '+type(e).__name__)
  if Path(file).suffix.lower()=='.pdf' and r['status']!='success' and self.config.get('native_pdf_symbols') and unfiltered:
   try:
    from .pdf_symbols import answer as native_symbol_answer
    proposal=native_symbol_answer(file,task)
    if proposal:r.update(proposal);r['stage_timings']['native_pdf_symbols']=proposal['native_symbol_timing']
   except ValueError:pass
   except Exception as e:r['warnings'].append('Native legend-symbol analysis unavailable: '+type(e).__name__)
  if Path(file).suffix.lower()=='.pdf' and r['status']!='success' and self.config.get('rendered_pdf_structural') and unfiltered and target in ('window','door'):
   try:
    from .pdf_raster import answer as rendered_pdf_answer
    if progress:progress('Checking openings inside the native-anchor plan crop',0,1)
    r['escalation_steps']+=1;proposal=rendered_pdf_answer(file,task)
    if proposal:r.update(proposal);r['stage_timings']['rendered_pdf']=proposal.get('structural_timing',{})
   except Exception as e:r['warnings'].append('Rendered opening detector unavailable; previous local result retained: '+type(e).__name__)
  if Path(file).suffix.lower()=='.pdf' and r['status']!='success' and task.get('filters',{}).get('schedule') and r.get('escalation_steps',0)<2:
   try:
    from .schedules import answer as schedule_answer
    facts,_,_,_=self.base.facts(file);proposal=schedule_answer(facts,task,question)
    if proposal:r.update(proposal);r['escalation_steps']+=1
   except Exception as e:r['warnings'].append('Native schedule aggregation unavailable: '+type(e).__name__)
  if Path(file).suffix.lower()=='.pdf' and r['status']!='success' and r.get('escalation_steps',0)<2:
   try:
    from .pdf import answer as vector_answer
    proposal=vector_answer(file,task)
    if proposal:r.update(proposal);r['escalation_steps']+=1
   except Exception as e:r['warnings'].append('Native vector-room supplement unavailable: '+type(e).__name__)
  if r['route_decisions'][-1].get('route')!=r['route']:r['route_decisions'].append({'stage':'v3-specialist','route':r['route'],'status':r['status']})
  r['local_answer']={k:copy.deepcopy(r.get(k)) for k in ('status','answer','unit','evidence','route','warnings')}
  if mode=='hybrid' and self.cloud_enabled and r['status']!='success' and r.get('escalation_steps',0)<2:
   try:
    from .inventory import extract,answer as inventory_answer
    semantic=target in ('bathroom','wc_room','balcony','sauna','bedroom','kitchen','storey','shower_bath') and unfiltered and task.get('scope')!='model' and Path(file).suffix.lower() in ('.png','.jpg','.jpeg','.pdf')
    r['escalation_steps']+=1
    if semantic:
     if progress:progress('Resolving missing semantic evidence with a cached scene inventory',0,1)
     inventory=extract(file);proposal=inventory_answer(inventory,target);g=inventory['generation'];cached=inventory['cache_hit'];r['cloud']={'status':'cache-hit' if cached else 'completed','requests':0 if cached else 1,'estimated_usd_reserved':0 if cached else g['reserved_usd'],'original_generation':g}
     if proposal:
      r['inventory_alternative']=copy.deepcopy(proposal);cloud=r['cloud'];r.update(proposal);r['cloud']=cloud;r['device']='cloud (local stages cpu)';r['model']={'name':g['model'],'prompt_version':inventory['version'],'kind':'cloud visual inventory hypotheses'};r['stage_timings']['cloud']=g
     else:r['cloud']['status']='inventory-uncertain-local-retained'
    else:
     if progress:progress('Repairing unresolved evidence with the validated selective adapter',0,1)
     self.repair(file,question,r)
   except Exception as e:
    r['cloud'].update(status='blocked',reason=str(e) if type(e).__name__ in ('BudgetBlocked','ProviderBlocked') else 'Evidence repair unavailable: '+type(e).__name__,requests='consult shared ledger');r['warnings'].append('Hybrid evidence unavailable; local answer/abstention retained.')
  elif mode=='hybrid' and not self.cloud_enabled:r['cloud']['status']='disabled-before-transmission'
  elif mode=='hybrid' and r.get('escalation_steps',0)>=2 and r['status']!='success':r['cloud']['status']='escalation-limit'
  if r['route_decisions'][-1].get('route')!=r['route']:r['route_decisions'].append({'stage':'selected-result','route':r['route'],'status':r['status']})
  if r['route'].startswith('hybrid.'):r['device']='cloud (local stages cpu)'
  r['timing']['total_seconds']=time.perf_counter()-started;r['latency_seconds']=r['timing']['total_seconds'];return r
