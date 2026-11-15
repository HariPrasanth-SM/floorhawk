"""Reconcile owned attempts in append-only ledger row ranges; never edits predictions."""
import sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from qa.common import ROOT,write_json
from runtime_paths import RESULTS_ROOT
from v2.budget import Ledger
from v2.gemini import MODEL_PRICES
O=RESULTS_ROOT/'iteration60'
def account(name):
 folder=O/name;r=json.loads((folder/'run.json').read_text());locals=[json.loads(l)for l in(folder/'local.predictions.jsonl').open()];operations={'paired-development-v1:'+str(p['request_id']):p['sample_id']for p in locals};questions=collections.defaultdict(list)
 with Ledger().connect()as c:rows=c.execute('SELECT rowid,id,operation,reserved,status,metadata FROM attempts WHERE rowid>? AND rowid<=?',(r['before']['requests_reserved'],r['after']['requests_reserved'])).fetchall()
 total_est=0;missing=0;records=[]
 for rowid,id,op,reserved,status,meta in rows:
  if op not in operations:continue
  m=json.loads(meta);prices=MODEL_PRICES.get(m.get('model'));estimated=None
  if prices and isinstance(m.get('input_tokens'),int)and isinstance(m.get('output_tokens'),int):estimated=(m['input_tokens']*prices[0]+(m['output_tokens']+(m.get('thinking_tokens')or 0))*prices[1])/1e6;total_est+=estimated
  else:missing+=1
  item={'rowid':rowid,'attempt_id':id,'sample_id':operations[op],'reserved_usd':reserved,'status':status,'metadata':m,'token_price_estimate_usd':estimated};records.append(item);questions[operations[op]].append(item)
 result={'run':name,'ledger_row_range':[r['before']['requests_reserved']+1,r['after']['requests_reserved']],'attempts':len(records),'reserved_usd':sum(x['reserved_usd']for x in records),'token_price_estimate_usd':total_est,'unknown_usage_attempts':missing,'questions':{p['sample_id']:{'actual_attempts':len(questions[p['sample_id']]),'provider_invoked':bool(questions[p['sample_id']]),'reserved_usd':sum(x['reserved_usd']for x in questions[p['sample_id']])}for p in locals},'records':records,'note':'Derived correction: V2 reused Local request IDs, so original raw per-question provider counters accidentally included prior V1 operations. Original outputs/ledger untouched; row-range ownership provides actual fresh requests. New dispatch uses a unique operation UUID. Token cost is estimated, not dashboard settled spend.'};write_json(folder/'accounting.json',result);print(name,result['attempts'],result['reserved_usd'],result['token_price_estimate_usd'])
if __name__=='__main__':
 account('paired-v1');account('paired-v2')
