"""Export a sanitized source commit for a NEW private submission repository.

No source history, agent checkpoints, drawings, gold files or weights are copied.
Repository creation/push remain explicit operator operations.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DIRS={'qa','v2','v3','iteration','inspection','evaluation','campaign','scripts','tests','config','docs','reports','web','deploy'}
SUFFIXES={'.py','.sh','.js','.css','.html','.md','.json','.txt'}
def scan(name,raw):
 p=Path(name)
 if p.parts[0]not in DIRS and len(p.parts)>1:raise ValueError('Non-source directory: '+name)
 if p.suffix not in SUFFIXES and p.name not in ['.gitignore','.env.example']and not p.name.startswith(('LICENSE','COPYING','NOTICE')):raise ValueError('Non-source extension: '+name)
 if any(part in ['datasets','weights','results','external','cache','.entire','.git','.secrets','benchmarks']for part in p.parts):raise ValueError('Restricted artifact path: '+name)
 if len(raw)>2_000_000:raise ValueError('Unexpected bulk source: '+name)
 if re.search(rb'AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----',raw):raise ValueError('Credential pattern: '+name)
 if b'/home/'+b'harry/'in raw:raise ValueError('Private absolute path: '+name)
def main():
 p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();commit=subprocess.check_output(['git','rev-parse',a.commit+'^{commit}'],cwd=ROOT,text=True).strip();dest=a.output.resolve()
 if dest.exists():raise ValueError('Submission destination exists; do not overwrite newer source')
 paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit],cwd=ROOT,text=True).splitlines();files={};raws={}
 for name in paths:
  raw=subprocess.check_output(['git','show',commit+':'+name],cwd=ROOT);scan(name,raw);raws[name]=raw;files[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
 dest.mkdir(parents=True)
 for name,raw in raws.items():
  out=dest/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
 (dest/'SOURCE_RELEASE.json').write_text(json.dumps({'source_commit':commit,'repository':'private FloorHAWK submission','files':files,'exclusions':'No history, datasets, drawings, references, weights, predictions, secrets or raw agent sessions. External artifact checksums/restoration instructions retained.'},indent=2)+'\n');print(json.dumps({'source_commit':commit,'files':len(files),'bytes':sum(x['bytes']for x in files.values()),'output_directory':dest.name}))
if __name__=='__main__':main()
