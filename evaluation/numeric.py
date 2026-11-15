#!/usr/bin/env python3
"""Offline scoring only. Predictions: sample_id, status, answer, unit, latency_seconds."""
import argparse,collections,json,math,re
from pathlib import Path

def number(x):
    if isinstance(x,bool):return None
    if isinstance(x,(float,int)):v=float(x)
    elif isinstance(x,str) and re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?',x.strip()):v=float(x)
    else:return None
    return v if math.isfinite(v) else None

def unit(u):
    return {'m²':'m2','m^2':'m2','m³':'m3','m^3':'m3','metres':'m','meters':'m'}.get(u,u)

def score(gold,pred):
    if pred is None:return {'passed':False,'reason':'missing'}
    if pred.get('status')!='success':return {'passed':False,'reason':pred.get('status','invalid_status')}
    typ=gold['type']
    if typ=='text':
        # Not an official semantic grade. No same-model judging.
        norm=lambda s:' '.join(str(s).casefold().split())
        return {'passed':None,'reason':'text_requires_rubric','text_normalized_exact':norm(gold['answer'])==norm(pred.get('answer',''))}
    if typ not in ('count','area','volume','length'):return {'passed':None,'reason':'unsupported_gold_type'}
    a,b=number(gold['answer']),number(pred.get('answer'))
    if a is None:return {'passed':None,'reason':'invalid_numeric_reference'}
    if b is None:return {'passed':False,'reason':'invalid_numeric_prediction'}
    if unit(gold.get('unit'))!=unit(pred.get('unit')):return {'passed':False,'reason':'unit_mismatch'}
    err=abs(a-b)
    passed=(a==b and b.is_integer()) if typ=='count' else (err<=abs(a)*.02+1e-9 if a else err<=1e-9)
    return {'passed':passed,'reason':'numeric','absolute_error':err,'signed_error':b-a}

def main():
    p=argparse.ArgumentParser();p.add_argument('--answers',required=True);p.add_argument('--predictions',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    gold=[json.loads(l) for l in Path(a.answers).read_text().splitlines() if l.strip()]
    predictions=[json.loads(l) for l in Path(a.predictions).read_text().splitlines() if l.strip()]
    ids=[x['sample_id'] for x in predictions];gids=[x['sample_id'] for x in gold]
    if len(ids)!=len(set(ids)) or len(gids)!=len(set(gids)):raise SystemExit('Duplicate sample_id')
    if set(ids)-set(gids):raise SystemExit('Predictions contain IDs outside this benchmark')
    lookup={r['sample_id']:r for r in predictions};records=[];buckets=collections.defaultdict(list)
    for g in gold:
        p=lookup.get(g['sample_id']);r=score(g,p);r.update(sample_id=g['sample_id'],type=g['type'],category=g.get('category','unknown'),source=g.get('source','unknown'))
        records.append(r)
        for k in ('all','type:'+r['type'],'category:'+r['category'],'source:'+r['source']):buckets[k].append(r)
    report={}
    for k,rs in buckets.items():
        numeric=[r for r in rs if r['type'] in ('count','area','volume','length')];graded=[r for r in numeric if r['passed'] is not None];errors=[r for r in rs if r['type']=='count' and 'absolute_error'in r]
        report[k]={'total':len(rs),'numeric_total':len(numeric),'numeric_graded':len(graded),'numeric_passed':sum(r['passed'] is True for r in graded),'numeric_accuracy_including_missing':sum(r['passed'] is True for r in graded)/len(numeric) if numeric else None,'text_total':sum(r['type']=='text' for r in rs),'reasons':dict(collections.Counter(r['reason'] for r in rs)),'count_mae_valid_outputs':sum(r['absolute_error'] for r in errors)/len(errors) if errors else None,'count_mae_denominator':len(errors)}
    Path(a.output).write_text(json.dumps({'metrics':report,'records':records,'note':'2% numeric tolerance per supplied README; text requires a separate semantic rubric. Scores on trained-on data are descriptive only.'},indent=2))
    print(json.dumps(report['all'],indent=2))
if __name__=='__main__':main()
