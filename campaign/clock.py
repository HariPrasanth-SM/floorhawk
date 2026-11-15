"""Hard Helsinki deadlines shared by orchestrator and every campaign worker."""
import time,os,signal,json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
ZONE=ZoneInfo('Europe/Helsinki')
DEADLINES={k:datetime.fromisoformat('2026-11-15T'+v).replace(tzinfo=ZONE).timestamp()for k,v in {'optimize':'05:45:00','deploy':'07:00:00','evaluate':'07:30:00'}.items()}
def now():return datetime.now(ZONE).isoformat()
def remaining(phase):return max(0,DEADLINES[phase]-time.time())
def admit(phase,bound_seconds=0):
 if phase=='optimize'and(Path(__file__).resolve().parents[1]/'results/overnight-20261115/FROZEN.json').exists():raise TimeoutError('Optimization candidate frozen')
 if remaining(phase)<=bound_seconds:raise TimeoutError('Campaign '+phase+' deadline prevents new work')
def atomic(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp-'+str(os.getpid()));temp.write_text(json.dumps(value,indent=2,ensure_ascii=False));temp.replace(path)

PUSH_90_BEFORE=datetime.fromisoformat('2026-11-15T04:30:00').replace(tzinfo=ZONE).timestamp()
def effective_target(first_85_epoch=None):return .90 if first_85_epoch is not None and first_85_epoch<PUSH_90_BEFORE else .85
