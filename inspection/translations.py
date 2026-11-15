"""Offline verified English equivalents for exact existing bilingual count templates.
No answer is used to pair questions. Free-form and dynamic room/quantity text is excluded.
"""
import json,collections
from functools import lru_cache
from qa.common import ROOT,write_json,sha
PATH=ROOT/'inspection/english-translations.json'
CATEGORIES={'count_doors','count_windows','count_toilet_fixtures','count_sinks','count_showers_and_baths','count_storeys','count_bedrooms','count_kitchens','count_bathrooms','count_separate_wc_rooms','count_saunas','count_balconies'}
def build():
 source=ROOT/'benchmarks/qa-v3/quick.answers.jsonl';qs=[json.loads(l)for l in source.open()];buckets=collections.defaultdict(list)
 for q in qs:
  if q.get('source')=='cubicasa5k'and q['category']in CATEGORIES and q['type']=='count':buckets[(q['path'],q['category'],q.get('unit'))].append(q)
 mapping={}
 for key,group in buckets.items():
  english={q['question']for q in group if q['language']=='en'}
  if len(english)!=1:continue
  e=next(q for q in group if q['language']=='en')
  for q in group:
   if q['language']!='fi':continue
   mapping[q['sample_id']]={'original_question':q['question'],'english':e['question'],'english_sample_id':e['sample_id'],'path':q['path'],'task':q['category'],'unit':q.get('unit'),'method':'verified_existing_english_equivalent','verification':'Exact fixed Finnish/English count templates manually checked; same drawing, category, quantity type and unit. Answers excluded from matching.'}
 write_json(PATH,{'schema':1,'source_sha256':sha(source),'entries':mapping,'note':'Only12 explicitly reviewed fixed count templates. No generated translations; unsupported free-form remains unavailable.'});print('English equivalents',len(mapping))
@lru_cache(maxsize=1)
def read_mapping(mtime):return json.loads(PATH.read_text())['entries']
def for_question(g):
 if not PATH.exists():return None
 data=read_mapping(PATH.stat().st_mtime_ns).get(g['sample_id'])
 return data if data and data['original_question']==g['question']and data['path']==g['path']and data['task']==g.get('category')and data['unit']==g.get('unit')else None
if __name__=='__main__':build()
