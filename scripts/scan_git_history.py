"""Read-only scan of all reachable Git blobs; never prints matching contents."""
import argparse,subprocess,re,json
from pathlib import Path
PATTERN=re.compile(rb'AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----')
def scan(root):
 rows=subprocess.check_output(['git','rev-list','--objects','--all'],cwd=root,text=True).splitlines();proc=subprocess.Popen(['git','cat-file','--batch'],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE);bad=[];count=0;total=0
 try:
  for row in rows:
   ident,_,name=row.partition(' ');proc.stdin.write((ident+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().decode().split();size=int(header[2]);raw=proc.stdout.read(size);proc.stdout.read(1)
   if header[1]!='blob':continue
   count+=1;total+=size
   if PATTERN.search(raw):bad.append({'object':ident,'path':name,'reason':'credential-like bytes; contents suppressed'})
 finally:proc.stdin.close();proc.wait()
 report={'blob_count':count,'bytes_scanned':total,'findings':bad,'passed':not bad};print(json.dumps(report,indent=2));return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repository',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();raise SystemExit(0 if scan(a.repository)['passed']else 1)
