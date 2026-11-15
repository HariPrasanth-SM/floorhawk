"""Alternative opening proposals from real detector score/geometry profiles."""
import copy
from .candidate import suppress
from .ensemble import instances
from .selector import features as original_features,FEATURE_NAMES as ORIGINAL_FEATURE_NAMES
CONFIDENCES=[.25,.4,.5,.65,.8]
def candidates(local,rt,custom,review):
 target=local['task']['target'];rows=[]
 for origin,raw in [('rt',rt),('custom',custom)]:
  if not raw or raw.get('status','success')not in['success']:continue
  for conf in CONFIDENCES:
   e=suppress([e for e in raw.get('entities',[])if e['class']==target],conf,.5);r=copy.deepcopy(local);r.update(answer=len(e),evidence=e,status='success',unit='count',route='raster.opening-score-proposal.campaign-v1',opening_profile={'source':origin,'confidence':conf,'iou':.5});rows.append((origin+':'+str(conf),r))
 for profile in ['corroborated','strict','intersection','union70','union60_strong']:
  if rt and custom and custom.get('status')=='success':
   e=instances(rt.get('entities',[]),custom.get('entities',[]),target,profile);r=copy.deepcopy(local);r.update(answer=len(e),evidence=e,status='success',unit='count',route='raster.opening-corroboration-proposal.campaign-v1',opening_profile={'source':'ensemble','profile':profile});rows.append(('ensemble:'+profile,r))
 # Identical count/instance sets need not create duplicate training proposals.
 seen=set();result=[]
 for source,r in rows:
  identity=(source.split(':')[0],r['answer'],tuple(sorted(tuple(round(v,2)for v in e['bbox'])for e in r['evidence'])))
  if identity not in seen:seen.add(identity);result.append((source,r))
 return result
FEATURE_NAMES=ORIGINAL_FEATURE_NAMES+['from_rt','from_custom','from_ensemble','mean_corroboration','maximum_corroboration','mean_review_overlap','profile_confidence','log_rt_50','log_custom_40','difference_rt_50','difference_custom_40']
def features(local,candidate,source,review,words,size,rt,custom):
 import math
 from v3.dedup import overlap
 x=original_features(local,candidate,'local'if source=='local'else'review'if source=='review'else source,review,words,size);target=local['task']['target'];other=[e for e in(custom or{}).get('entities',[])if e['class']==target and e.get('score',0)>=.4];visual=[e for e in(review or{}).get('entities',[])if e['class']==target];boxes=candidate.get('evidence',[]);support=[max((overlap(e['bbox'],k['bbox'])[1]for k in other),default=0)for e in boxes if e.get('bbox')];review_support=[max((overlap(e['bbox'],k['bbox'])[0]for k in visual),default=0)for e in boxes if e.get('bbox')];rt_count=len(suppress([e for e in(rt or{}).get('entities',[])if e['class']==target],.5,.5));custom_count=len(suppress(other,.4,.5));return x+[float(source.startswith('rt:')),float(source.startswith('custom:')),float(source.startswith('ensemble:')),sum(support)/len(support)if support else 0,max(support,default=0),sum(review_support)/len(review_support)if review_support else 0,candidate.get('opening_profile',{}).get('confidence',.5),math.log1p(rt_count),math.log1p(custom_count),candidate['answer']-rt_count,candidate['answer']-custom_count]


def choose(local,review,words,size,rt,custom,model):
 from .selector import proposals,rank
 options=proposals(local,review,words)+candidates(local,rt,custom,review);ranked=[(rank(model,features(local,r,source,review,words,size,rt,custom)),source,r)for source,r in options];s,origin,r=max(ranked,key=lambda e:(e[0],e[1]=='local'));r=copy.deepcopy(r);r['opening_selector']={'version':'opening-proposal-selector-v1','selected':origin,'selection_score':s,'score_is_not_probability':True,'reason':'Grouped evidence-feature ranking of actual detector/review instance proposals; no count averaging'};return r
