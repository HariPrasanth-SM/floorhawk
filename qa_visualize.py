"""Offline visualization of real cached entities and semantic output maps."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from qa.common import ROOT,CACHE
COLORS=['#fafafa','#d7e8bd','#424b50','#e9c47a','#a3cdd2','#a1b8dd','#d0a6c9','#e4c6a7','#68686b','#c5b99f','#b8c4b1','#c7c7c7']
def visualize(record,target):
 import pymupdf
 path=ROOT.parent/'datasets/junction-dataset'/record['path'];kind=record['input_kind'];evidence=record['evidence']
 if kind=='raster':im=Image.open(path).convert('RGB');boxes=[dict(e,xyxy=e['bbox'],included=True) for e in evidence if 'bbox'in e]
 elif kind=='pdf':
  doc=pymupdf.open(path);page=doc[0];scale=1400/max(page.rect.width,page.rect.height);pix=page.get_pixmap(matrix=pymupdf.Matrix(scale,scale));im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);boxes=[]
  for e in evidence:
   if e.get('page')==1 and 'bbox'in e:boxes.append(dict(e,xyxy=list(pymupdf.Rect(e['bbox'])*page.rotation_matrix*pymupdf.Matrix(scale,scale)),included=True))
 else:
  im=Image.new('RGB',(1300,700),'white');d=ImageDraw.Draw(im);d.text((10,10),'IFC GUID/property evidence (not a model rendering)',fill='black')
  y=40
  for e in evidence[:25]:d.text((10,y),str(e.get('guid',e.get('id')))+' '+str(e.get('property',''))[:120],fill='black');y+=23
  boxes=[]
 d=ImageDraw.Draw(im);font=ImageFont.load_default(size=max(12,im.width//90))
 for index,b in enumerate(boxes,1):
  d.rectangle(b['xyxy'],outline='#d33d1f',width=3);d.text((b['xyxy'][0],max(0,b['xyxy'][1]-18)),f"#{index} {b.get('class',b.get('label','evidence'))}",fill='#b02c15',font=font)
 im.thumbnail((1400,1000));canvas=Image.new('RGB',(max(600,im.width),im.height+100),'white');canvas.paste(im,(0,0));d=ImageDraw.Draw(canvas)
 credit='CubiCasa5K (c) 2019 CubiCasa; Kalervo et al., SCIA 2019; CC BY-NC-SA 4.0' if kind=='raster' else 'Swiss Dwellings / Archilyse, CC BY 4.0' if 'swiss_dwellings/' in record['path'] else 'Source attribution/licence: '+str(Path(record['path']).parent/'LICENSE.md') if kind=='pdf' else 'Retain source IFC licence; see dataset source LICENSE.md'
 d.text((5,im.height+4),credit,fill='black');d.text((5,im.height+24),record['question'][:160],fill='black');d.text((5,im.height+44),f"{record['status']}: {record['answer']} {record.get('unit') or ''}; {record['route']}",fill='black');d.text((5,im.height+64),'Model/tool evidence; no localization accuracy or completeness claim.',fill='black');canvas.save(target)
 if kind=='raster':
  raw=CACHE/(record['facts_cache_key']+'-rooms.png')
  if raw.exists():
   labels=np.array(Image.open(raw));rgb=np.zeros((*labels.shape,3),dtype=np.uint8)
   for i,color in enumerate(COLORS):rgb[labels==i]=tuple(int(color[j:j+2],16) for j in (1,3,5))
   Image.fromarray(rgb).save(Path(target).with_name(Path(target).stem+'-raw-room-semantics.png'))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--predictions',type=Path,required=True);p.add_argument('--sample-id',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=next(json.loads(l) for l in a.predictions.open() if json.loads(l)['sample_id']==a.sample_id);visualize(r,a.output)
