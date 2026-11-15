"""Shared pinned Python3.11 cloud image and unchanged model-volume registry."""
import os,json
from pathlib import Path
import modal
WORK=Path(os.environ.get('FLOORHAWK_WORKSPACE',Path(__file__).resolve().parents[3]/'floorhawk-modal'))if modal.is_local()else Path('/opt/floorhawk')
OPERATOR=WORK/'operator-role.json'
ROLE_CONFIG=json.loads(OPERATOR.read_text())if modal.is_local()and OPERATOR.is_file()else{}
RELEASE=Path(os.environ.get('FLOORHAWK_RELEASE',ROLE_CONFIG.get('release',str(WORK/'current'if modal.is_local()else WORK)))).resolve()
MANIFEST=json.loads((RELEASE/'release.json').read_text());ASSETS=json.loads((WORK/'assets.json').read_text());REV=MANIFEST['source_commit'];VERSION=ASSETS['version']
weights=modal.Volume.from_name('floorhawk-assets',create_if_missing=True)
GPU_APP=os.environ.get('FLOORHAWK_GPU_APP','')
image=(modal.Image.debian_slim(python_version='3.11').apt_install('libgl1','libglib2.0-0','tesseract-ocr','tesseract-ocr-eng')
 .pip_install('torch==2.6.0','torchvision==0.21.0',index_url='https://download.pytorch.org/whl/cu124')
 .pip_install('numpy==1.26.4','opencv-python==4.10.0.84','Pillow==10.4.0','ultralytics==8.3.40','PyMuPDF==1.26.6','ifcopenshell==0.8.3.post2','shapely==2.1.2','scikit-image==0.25.2','lmdb==1.7.5','svgpathtools==1.7.2','psutil==7.2.2','rapidocr==3.4.1','onnxruntime==1.23.2','google-genai==1.51.0','fastapi==0.115.12','uvicorn==0.34.2','gdown==5.2.0')
 .env({'FLOORHAWK_GPU_APP':GPU_APP,'PROOFPLAN_RELEASE':'v3','PROOFPLAN_PAIRED':'1','PROOFPLAN_LARGE_DRAWINGS':'1','PROOFPLAN_HYBRID_EVIDENCE_V3':'0','PROOFPLAN_MODEL_ROOT':'/weights/'+VERSION,'PROOFPLAN_RESULTS_ROOT':'/jobs','PROOFPLAN_CACHE_ROOT':'/tmp/floorhawk-api-cache','PROOFPLAN_DATASET_ROOT':'/opt/floorhawk/empty-samples','PROOFPLAN_HOST_VISION':'0','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','YOLO_OFFLINE':'true','PROOFPLAN_IN_HOST':'1','PYTHONPATH':'/opt/floorhawk'})
 .add_local_dir(RELEASE,'/opt/floorhawk',copy=True))
