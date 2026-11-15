"""Trusted backend config, never document/model supplied executable adapter names.
Tomorrow's checkpoint can replace one slot via this config + one adapter implementing
answer(file,task[,facts]) -> typed answer/evidence metadata. UI cannot select modules.
"""
import importlib,json,re
from .policy import ROOT
DEFAULT={'structural':{'module':'v2.structural','function':'answer'},'ocr':{'module':'v2.ocr','function':'answer'}}
def configured(slot,release='v2'):
 if release not in ('v2','v3'):raise ValueError('Unregistered adapter release')
 path=ROOT/release/'adapter-config.json';config=json.loads(path.read_text()) if path.exists() else DEFAULT
 item=config[slot];module=item['module'];name=item['function']
 if not re.fullmatch(r'v2\.[a-z_][a-z0-9_]*',module) or not re.fullmatch(r'[a-z_][a-z0-9_]*',name):raise ValueError('Invalid trusted adapter registration')
 return getattr(importlib.import_module(module),name)
