"""Create original shareable fixtures; keep UI references outside inference images."""
import sys,json,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import modal,pymupdf,ifcopenshell,ifcopenshell.guid
from runtime_paths import DATASET_ROOT
W=ROOT.parent/'floorhawk-modal';d=W/'gallery-source';d.mkdir(exist_ok=True)
pdf=pymupdf.open();p=pdf.new_page(width=600,height=400)
for x,label,area in [(40,'1.01 KITCHEN','12.00 m²'),(310,'1.02 CORRIDOR','8.00 m²')]:
 p.draw_rect(pymupdf.Rect(x,70,x+230,300),color=(0,0,0),width=2);p.insert_text((x+25,140),label,fontsize=17);p.insert_text((x+25,170),area,fontsize=16)
p.insert_text((40,350),'FloorHAWK synthetic demonstration sheet. Printed illustrative areas; no raster scale.',fontsize=9);pdf.save(d/'rooms.pdf');pdf.close()
f=ifcopenshell.file(schema='IFC4');pr=f.create_entity('IfcProject',GlobalId=ifcopenshell.guid.new(),Name='FloorHAWK synthetic demo');unit=f.create_entity('IfcSIUnit',UnitType='LENGTHUNIT',Name='METRE');pr.UnitsInContext=f.create_entity('IfcUnitAssignment',Units=[unit])
for i in range(3):f.create_entity('IfcWindow',GlobalId=ifcopenshell.guid.new(),Name='Window '+str(i+1),OverallHeight=1.2,OverallWidth=.9)
space=f.create_entity('IfcSpace',GlobalId=ifcopenshell.guid.new(),Name='1.01',LongName='Kitchen');q=f.create_entity('IfcQuantityArea',Name='NetFloorArea',AreaValue=12.0);ps=f.create_entity('IfcElementQuantity',GlobalId=ifcopenshell.guid.new(),Name='Qto_SpaceBaseQuantities',Quantities=[q]);f.create_entity('IfcRelDefinesByProperties',GlobalId=ifcopenshell.guid.new(),RelatedObjects=[space],RelatingPropertyDefinition=ps);f.write(str(d/'rooms.ifc'))
rows=[{'id':'cubi-demo','format':'PNG','name':'CubiCasa development floor plan','filename':'plan.png','credit':'CubiCasa5K; CC BY-NC-SA4.0; restricted noncommercial demonstration','suggestions':[{'id':'windows','question':'How many windows are shown on this floor plan?'},{'id':'doors','question':'How many doors are shown on this floor plan?'}]}, {'id':'rooms-pdf','format':'PDF','name':'Printed room areas (synthetic)','filename':'rooms.pdf','credit':'FloorHAWK original synthetic fixture; CC0','suggestions':[{'id':'area-kitchen','question':'What is the net floor area of room 1.01 in m²?','reference':12,'unit':'m2'},{'id':'area-corridor','question':'What is the net floor area of room 1.02 in m²?','reference':8,'unit':'m2'}]}, {'id':'rooms-ifc','format':'IFC','name':'Window entities and room quantity (synthetic)','filename':'rooms.ifc','credit':'FloorHAWK original synthetic fixture; CC0','suggestions':[{'id':'windows','question':'How many windows are in this IFC model?','reference':3,'unit':'count'},{'id':'schema','question':'What IFC schema does this model use?','reference':'IFC4','unit':None}]}]
for r in rows:
 for q in r['suggestions']:q['verification']='Not yet checked on this release'
# References are UI-only Modal Dict data, never copied into the image/source Volume.
v=modal.Volume.from_name('floorhawk-assets');sources=[(DATASET_ROOT/'data/cubicasa5k/colorful-10052.png','plan.png'),(d/'rooms.pdf','rooms.pdf'),(d/'rooms.ifc','rooms.ifc')]
with v.batch_upload()as b:
 for p,name in sources:b.put_file(p,'/gallery-ui-v1/'+name)
modal.Dict.from_name('floorhawk-gallery-ui-v1',create_if_missing=True).put('catalog',rows);print('Uploaded3protected sources; UI references stored separately; no saved answers/detections uploaded')
