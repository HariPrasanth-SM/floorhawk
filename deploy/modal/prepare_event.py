"""Explicit event deploy preparation: immutable assets, private role codes, durable state.
Called only by the deployment CLI when operator-role.json explicitly enables it.
"""
import json,hashlib,hmac,os
from pathlib import Path
import modal

def prepare(config):
 from deploy.modal.event import ROLES
 role=config['role'];spec=ROLES[role];work=Path(__file__).resolve().parents[3]/'floorhawk-modal';release=Path(config['release']).resolve()
 if not release.is_relative_to((work/'releases').resolve()):raise ValueError('Deployment snapshot must be in operational releases')
 manifest=json.loads((release/'release.json').read_text())
 for name,digest in manifest['files'].items():
  p=release/name
  if not p.is_file()or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Release hash mismatch: '+name)
 if not(release/'assets.json').is_file():raise ValueError('Required assets.json omitted')
 extra=release/'extra-assets.json'
 if extra.is_file():
  assets=json.loads(extra.read_text());volume=modal.Volume.from_name('floorhawk-assets')
  for row in assets:
   source=(work.parent/row['local_source']).resolve()
   if not source.is_relative_to(work.parent.resolve())or any(k in source.parts for k in ['.secrets','.config']):raise ValueError('Unapproved asset source')
   if source.stat().st_size!=row['size']or hashlib.sha256(source.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Extra asset source mismatch')
   target=row['remote_path']
   if not target.startswith('/campaign-release-assets/')or'..'in target:raise ValueError('Unapproved asset destination')
   try:existing=list(volume.listdir(target));present=bool(existing)
   except Exception:present=False
   if not present:
    with volume.batch_upload()as batch:batch.put_file(source,target)
  print('Versioned model assets prepared:',len(assets))
 private=work/'.secrets';private.mkdir(exist_ok=True)
 if role in['candidate','judges']:
  root=(private/'presenter-session-key').read_text().encode();code=hmac.new(root,('floorhawk-access-'+role+'-v1').encode(),'sha256').hexdigest();path=private/(role+'-access-code')
  if path.exists()and path.read_text()!=code:raise ValueError('Existing role code differs; preserve and resolve explicitly')
  if not path.exists():path.write_text(code);path.chmod(0o600)
 store=modal.Dict.from_name(spec['control'],create_if_missing=True);initial={'events':[],'jobs':{},'idempotency':{},'live':role=='candidate','gemini':True};store.put('admission-state-v1',initial,skip_if_exists=True)
 # Existing histories/counters are never reset. Enabling is an explicit operator field.
 if config.get('enable_live'):
  from deploy.modal.security import Controls
  with Controls(store,'').transaction()as state:state['live']=True;state['gemini']=config.get('gemini_enabled',True);state['event_release']=manifest['source_commit']
 print('Prepared role',role,'source',manifest['source_commit'],'access values never printed')
