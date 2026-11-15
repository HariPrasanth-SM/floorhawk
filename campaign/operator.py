"""Select a pinned role/release for the single existing Modal deployment entrypoint."""
import argparse,json
from pathlib import Path
from .clock import atomic,now
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent/'floorhawk-modal'
def main():
 p=argparse.ArgumentParser();p.add_argument('--role',choices=['candidate','presenter','judges','public','evaluation'],required=True);p.add_argument('--release',type=Path,required=True);p.add_argument('--enable-live',action='store_true');p.add_argument('--disable-gemini',action='store_true');a=p.parse_args();release=a.release.resolve()
 if not release.is_relative_to((WORK/'releases').resolve())or not(release/'release.json').is_file():raise ValueError('Explicit operational release required')
 atomic(WORK/'operator-role.json',{'role':a.role,'release':str(release),'prepare_assets':a.role!='evaluation','enable_live':a.enable_live,'gemini_enabled':not a.disable_gemini,'selected_at':now()});print('Selected',a.role,release.name,'only; run .venv/bin/modal deploy deploy/modal/app.py')
if __name__=='__main__':main()
