"""Authorized private publication via existing Git credential helper, never token logs.
Only explicitly reviewed main is pushed. No force push, mirror, tags or checkpoint refs.
"""
import subprocess,os,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--owner',required=True);p.add_argument('--name',default='proofplan-junction-2026');p.add_argument('--push',action='store_true');a=p.parse_args();gh=ROOT/'.tools/gh'
 cred=subprocess.run(['git','credential','fill'],cwd=ROOT,input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env=dict(os.environ,GIT_TERMINAL_PROMPT='0'));fields=dict(l.split('=',1)for l in cred.stdout.splitlines()if '='in l);token=os.environ.get('GH_TOKEN');saved=subprocess.run([str(gh),'auth','status'],capture_output=True,env=dict(os.environ,GH_PROMPT_DISABLED='1'))
 if not token and saved.returncode!=0:token=fields.get('password')
 if not token and saved.returncode!=0:raise SystemExit('GitHub API login required; use .tools/gh auth login --hostname github.com --git-protocol ssh --web')
 env=dict(os.environ,GH_PROMPT_DISABLED='1',GIT_TERMINAL_PROMPT='0')
 if token:env['GH_TOKEN']=token
 def api(args,missing=False):
  r=subprocess.run([str(gh),'api',*args],cwd=ROOT,env=env,capture_output=True,text=True)
  if r.returncode:
   if missing and 'HTTP 404'in r.stderr:return None
   raise SystemExit('GitHub API authentication/permission failed; no credential or response body logged')
  return json.loads(r.stdout)
 identity=api(['user'])
 if identity['login'].casefold()!=a.owner.casefold()or identity.get('type')!='User':raise SystemExit('Authenticated API account does not match approved personal SSH identity')
 remote=subprocess.run(['git','remote','get-url','origin'],cwd=ROOT,capture_output=True,text=True);repo=api(['repos/'+a.owner+'/'+a.name],True);created=False
 if repo is None:
  if remote.returncode==0:raise SystemExit('Existing origin preserved; refusing a competing repository')
  repo=api(['user/repos','--method','POST','-f','name='+a.name,'-F','private=true','-f','description=Local drawing QA and evidence review; sanitized source only']);created=True
 if repo.get('private')is not True or repo['owner']['login'].casefold()!=a.owner.casefold():raise SystemExit('Repository is not verified private under approved owner; stop')
 url=repo['ssh_url']
 if remote.returncode==0 and remote.stdout.strip()!=url:raise SystemExit('Existing origin preserved; URL mismatch')
 if remote.returncode!=0:
  refs=subprocess.check_output(['git','ls-remote',url],cwd=ROOT,text=True)
  known=set(subprocess.check_output(['git','rev-list','--all'],cwd=ROOT,text=True).split())
  if any(line.split()[0]not in known for line in refs.splitlines()):raise SystemExit('Existing repository contains unrelated history; stop')
  subprocess.run(['git','remote','add','origin',url],cwd=ROOT,check=True)
 print(json.dumps({'url':repo['html_url'],'private':True,'created':created,'owner':identity['login']}),flush=True)
 if a.push:
  subprocess.run([str(ROOT/'.venv/bin/python'),'scripts/stage_source.py'],cwd=ROOT,check=True)
  if subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).strip():raise SystemExit('Uncommitted reviewed changes remain; commit before push')
  subprocess.run(['git','push','--set-upstream','origin','main'],cwd=ROOT,env=env,check=True)
  print('Reviewed main pushed; no other refs published',flush=True)
if __name__=='__main__':main()
