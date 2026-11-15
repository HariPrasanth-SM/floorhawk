"""Explicit event-only operational policy; legacy local/default behavior preserved."""
import json,os
from pathlib import Path
PATH=Path('/opt/floorhawk/config/event-serving.json')
if not PATH.is_file():PATH=Path(__file__).resolve().parents[2]/'config/event-serving.json'
def policy():return json.loads(PATH.read_text())
def active():return os.environ.get('FLOORHAWK_EVENT_CAPACITY')=='1'
def role(name=None):return policy()['roles'][name or os.environ.get('FLOORHAWK_EVENT_ROLE','public')]
