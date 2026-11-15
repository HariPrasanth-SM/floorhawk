"""UI-only catalog association. Never imported by inference workers."""
import modal,os,time
from pathlib import Path
_cached=None;_at=0
def catalog():
 global _cached,_at
 if os.environ.get('FLOORHAWK_PRESENTER')=='1'and _cached is not None and time.time()-_at<30:return _cached
 value=modal.Dict.from_name(os.environ.get('FLOORHAWK_GALLERY_STORE','floorhawk-gallery-ui-v1')).get('catalog',[])
 if os.environ.get('FLOORHAWK_PRESENTER')=='1':_cached=value;_at=time.time()
 return value
def drawing(ident):
 r=next((r for r in catalog()if r['id']==ident),None)
 if r is None:raise ValueError('Unknown curated source')
 return r,Path(os.environ.get('FLOORHAWK_GALLERY_ROOT','/weights/gallery-ui-v1'))/r['filename']
def reference(ident,question):
 if not ident:return None
 r,_=drawing(ident);q=next((q for q in r['suggestions']if q['question']==question),None)
 if not q or 'reference'not in q:return None
 return {'question':q['question'],'value':q['reference'],'unit':q.get('unit'),'label':'Expected reference','verification':q['verification']}
