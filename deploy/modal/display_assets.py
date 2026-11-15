"""Bounded source rendering only; no AI calls or fabricated localization."""
import io,base64
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw

def validate(data):
 raw=base64.b64decode(data.get('file_base64',''),validate=True);suffix=Path(data.get('file_name','')).suffix.lower()
 if len(raw)>20*1024**2:raise ValueError('Use a source under20MiB')
 if suffix in ['.png','.jpg','.jpeg']:
  from image_ingest import prepare
  im,info=prepare(raw);im.thumbnail((1600,1600))
 elif suffix=='.pdf':
  import pymupdf
  with pymupdf.open(stream=raw,filetype='pdf')as doc:
   if doc.is_encrypted or not 1<=len(doc)<=20:raise ValueError('Use an unencrypted PDF with1–20pages')
   p=doc[0];pix=p.get_pixmap(matrix=pymupdf.Matrix(1400/max(p.rect.width,p.rect.height),1400/max(p.rect.width,p.rect.height)),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
 elif suffix=='.ifc':
  if len(raw)>10*1024**2 or b'ISO-10303-21'not in raw[:2000]or raw.count(b'=IFC')>100000:raise ValueError('IFC exceeds supported STEP/size/entity bounds')
  im=Image.new('RGB',(1000,650),'white');ImageDraw.Draw(im).text((40,220),'IFC document ready\nProperties can be queried without rendering geometry.',fill='black')
 else:raise ValueError('Upload PNG/JPEG, PDF or IFC')
 out=io.BytesIO();im.convert('RGB').save(out,format='PNG');return {'ready':True,'preview':'data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()}

def annotated(app,job,page=1):
 if job['input_kind']=='ifc':raise ValueError('No rendered IFC view is available for export')
 from presentation import selected
 p=job['prediction'];h=p.get('paired',{}).get('hybrid',{});mode='hybrid'if h.get('status')in['success','abstained','unsupported']else'local';e=selected(job,mode);boxes=app.view_boxes(job,dict(p,evidence=e))
 if job['input_kind']=='pdf':
  import pymupdf,qa_app
  with pymupdf.open(qa_app.STORE/job['id']/job['source_file'])as doc:
   pg=doc[page-1];s=3200/max(pg.rect.width,pg.rect.height);pix=pg.get_pixmap(matrix=pymupdf.Matrix(s,s),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
 else:im=Image.open(app.preview(job,page)).convert('RGB');im.thumbnail((4096,4096))
 meta=job['pages'][page-1];sx,sy=im.width/meta['width'],im.height/meta['height'];d=ImageDraw.Draw(im);n=0
 for b in boxes:
  if b.get('page',1)!=page:continue
  n+=1;x1,y1,x2,y2=b['xyxy'];box=[x1*sx,y1*sy,x2*sx,y2*sy];d.rectangle(box,outline='#00b8e6',width=3);d.text((box[0]+2,box[1]+2),str(n),fill='#9a0077',stroke_width=1,stroke_fill='white')
 out=io.BytesIO();im.save(out,format='PNG');return out.getvalue()
