"""Small count-supervised inclusion classifier on actual detector/review proposals.
Inference contains no counts/references beyond its input model observations.
"""
import math,copy
import numpy as np
from v3.dedup import overlap
VERSION='weak-instance-consensus-v1'
FEATURES=['bias','rt_logit','yolo_logit','rt_present','yolo_present','review_present','review_iou','review_ios','cubi_same_ios','cubi_other_ios','log_area','log_aspect','center_x','center_y','edge_distance','review_region_count_log','rt_region_count_log','yolo_region_count_log']
def pool(rt,custom,review,cubi,target):
 rts=[e for e in(rt or{}).get('entities',[])if e['class']==target];ys=[e for e in(custom or{}).get('entities',[])if e['class']==target and e.get('score',0)>=.25];gs=[e for e in(review or{}).get('entities',[])if e['class']==target];cs=[e for e in(cubi or{}).get('entities',[])if e.get('kind')=='icon'and e['class']==target];other=[e for e in(cubi or{}).get('entities',[])if e.get('kind')=='icon'and e['class']in['closet','electrical_appliance',('door'if target=='window'else'window')]];size=(rt or custom).get('image_size');w,h=size;rows=[]
 for origin,items in [('rt',rts),('yolo',ys),('review',gs)]:
  for e in sorted(items,key=lambda e:e.get('score',0),reverse=True):
   if origin=='rt'and e.get('score',0)<.25:continue
   if any(overlap(e['bbox'],k['bbox'])[0]>.4 or overlap(e['bbox'],k['bbox'])[1]>.8 for k in rows):continue
   q=copy.deepcopy(e);q.update(id=origin+':'+e['id'],origin_model={'rt':'RT-DETR','yolo':'Custom YOLO','review':(review or{}).get('model','Gemini')}[origin]);q.pop('score',None)if origin=='review'else None;rows.append(q)
 def support(e,items,k):return max((overlap(e['bbox'],o['bbox'])[k]for o in items),default=0.)
 def confidence(e,items):return max((o.get('score',0)for o in items if overlap(e['bbox'],o['bbox'])[0]>.2 or overlap(e['bbox'],o['bbox'])[1]>.65),default=.01)
 logit=lambda s:math.log(max(.01,min(.99,s))/(1-max(.01,min(.99,s))))
 for e in rows:
  b=e['bbox'];bw=max(b[2]-b[0],1e-6);bh=max(b[3]-b[1],1e-6);rt_s=confidence(e,rts);y_s=confidence(e,ys);e['_features']=[1.,logit(rt_s),logit(y_s),float(rt_s>.01),float(y_s>.01),float(support(e,gs,1)>.5),support(e,gs,0),support(e,gs,1),support(e,cs,1),support(e,other,1),math.log(max(1e-6,bw*bh/(w*h))),abs(math.log(bw/bh)),(b[0]+b[2])/2/w,(b[1]+b[3])/2/h,min(b[0]/w,b[1]/h,(w-b[2])/w,(h-b[3])/h),math.log1p(len(gs)),math.log1p(len(rts)),math.log1p(len(ys))]
 return rows

def fit(groups,counts,steps=400,l2=.015,learning_rate=.025):
 X=np.asarray([e['_features']for g in groups for e in g],dtype=np.float64);doc=np.asarray([i for i,g in enumerate(groups)for e in g]);y=np.asarray(counts,dtype=float);mean=X.mean(0);std=np.maximum(X.std(0),.15);mean[0]=0;std[0]=1;Z=(X-mean)/std;w=np.zeros(X.shape[1]);w[0]=-.5;m=w.copy();v=w.copy();norm=np.maximum(y,1.)
 for t in range(1,steps+1):
  prob=1/(1+np.exp(-np.clip(Z@w,-25,25)));pred=np.bincount(doc,weights=prob,minlength=len(groups));err=(pred-y)/norm;grad=Z.T@(2*err[doc]*prob*(1-prob))/len(groups)+l2*w;m=.9*m+.1*grad;v=.999*v+.001*grad*grad;w-=learning_rate*(m/(1-.9**t))/(np.sqrt(v/(1-.999**t))+1e-8)
 return {'version':VERSION,'features':FEATURES,'coefficients':w.tolist(),'mean':mean.tolist(),'std':std.tolist(),'threshold':.5,'supervision':'Development drawing counts, five grouped folds; no spatial labels','steps':steps,'l2':l2,'learning_rate':learning_rate}
def predict(rows,model):
 if model['version']!=VERSION or model['features']!=FEATURES:raise ValueError('Instance feature version mismatch')
 result=[]
 for e in rows:
  z=sum((a-b)/s*w for a,b,s,w in zip(e['_features'],model['mean'],model['std'],model['coefficients']));score=1/(1+math.exp(-max(-25,min(25,z))))
  if score>=model['threshold']:r={k:v for k,v in e.items()if k!='_features'};r['weak_inclusion_score']=score;r['provenance']='Count-supervised inclusion of actual detector/review instance proposal; score not probability';result.append(r)
 return result
