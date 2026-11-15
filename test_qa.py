"""QA invariants using explicit synthetic document fixtures, not benchmark predictions."""
import tempfile,unittest,json,shutil
from pathlib import Path
from qa.router import route,validate_task
from qa.tools import pdf_answer,ifc_answer,raster_answer
from qa.common import inference_lock
from qa.pipeline import Pipeline
from qa.pdf import parse_pdf
from qa.vlm_client import LocalVLM,CloudAdapter

class QATests(unittest.TestCase):
 def test_multilingual_templates_and_registered_schema(self):
  self.assertEqual(route('Kuinka monta makuuhuonetta (MH) pohjapiirustuksessa on?')['target'],'bedroom')
  for q in ["How many rooms labelled 'Zimmer' are there on this floor?",'Wie viele Räume mit der Bezeichnung «Zimmer» gibt es?','Quanti locali con la denominazione «Zimmer» ci sono in questo piano?']:
   self.assertEqual(route(q)['filters']['label'],'zimmer')
  self.assertEqual(route('Wie gross ist die gesamte Nettogeschossfläche aller nummerierten Innenräume?')['target'],'room')
  with self.assertRaises(ValueError):validate_task({'operation':'run_shell','target':'wall','scope':'model'})
 def test_combined_shower_bath_does_not_use_bathtub_count(self):
  r=raster_answer({'entities':[]},route('How many showers or bathtubs are shown?'),'')
  self.assertEqual(r['status'],'abstained');self.assertIsNone(r['answer'])
 def test_missing_ifc_quantities_are_not_zero(self):
  f={'kind':'ifc','entities':[{'class':'IfcWall','guid':'fixture','id':'fixture','quantities':{}}],'unit_scales_to_si':{'AREAUNIT':1}}
  r=ifc_answer(f,route('What is the net area of the walls in this model?'),'')
  self.assertEqual(r['status'],'abstained');self.assertIsNone(r['answer'])
 def test_no_remote_worker_or_cloud_upload(self):
  for url in ['https://example.com','http://example.com','http://127.0.0.1.evil.test']:
   with self.assertRaises(ValueError):LocalVLM(url)
  with self.assertRaises(RuntimeError):CloudAdapter().answer('unused')
 def make_pdf(self,path,area=True):
  import pymupdf
  doc=pymupdf.open();p=doc.new_page();p.draw_rect(pymupdf.Rect(50,50,200,200),color=(.4,.4,.4),fill=(1,1,1));p.insert_text((100,100),'Zimmer');p.insert_text((100,115),'1.01')
  if area:p.insert_text((100,130),'12.00 m2')
  p.insert_text((300,100),'Legend Zimmer');p.insert_text((20,800),'Scale 1:100');doc.save(path);doc.close()
 def test_native_pdf_room_not_legend_and_area(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'fixture.pdf';self.make_pdf(p);f=parse_pdf(p);r=pdf_answer(f,route("How many rooms labelled 'Zimmer' are there?"),'')
   self.assertEqual(r['answer'],1);area=pdf_answer(f,route('What is the net floor area of room 1.01 in m2?'),'');self.assertEqual(area['answer'],12)
 def test_pdf_point_pixel_rotation_round_trip(self):
  import pymupdf
  for rotation in [0,90,180,270]:
   doc=pymupdf.open();page=doc.new_page(width=600,height=800);page.set_rotation(rotation);r=pymupdf.Rect(50,70,100,130);scale=1.75;display=r*page.rotation_matrix*pymupdf.Matrix(scale,scale);back=display/pymupdf.Matrix(scale,scale)*page.derotation_matrix
   self.assertTrue(all(abs(a-b)<.001 for a,b in zip(r,back)));doc.close()
 def test_content_cache_and_advisory_lock(self):
  with tempfile.TemporaryDirectory() as d:
   original=Path(d)/'a.pdf';copy=Path(d)/'different-name.pdf';self.make_pdf(original);shutil.copy2(original,copy);pipeline=Pipeline();one=pipeline.answer(original,"How many rooms labelled 'Zimmer' are there?");two=pipeline.answer(copy,'What is the net area of room 1.01?')
   self.assertEqual(one['status'],'success');self.assertEqual(two['status'],'success');self.assertTrue(two['timing']['cache_hit']);self.assertEqual(one['source_sha256'],two['source_sha256'])
   other=Path(d)/'new-fixture.pdf';self.make_pdf(other,False)
   with inference_lock():blocked=Pipeline().answer(other,"How many rooms labelled 'Zimmer' are there?")
   self.assertEqual(blocked['status'],'failed');self.assertIsNone(blocked['answer'])
 def test_ifc_types_are_not_occurrences(self):
  import ifcopenshell
  from qa.ifc import parse_ifc
  with tempfile.TemporaryDirectory() as d:
   model=ifcopenshell.file(schema='IFC4');model.create_entity('IfcWindow',GlobalId=ifcopenshell.guid.new(),Name='fixture occurrence');model.create_entity('IfcWindowType',GlobalId=ifcopenshell.guid.new(),Name='fixture type');path=Path(d)/'fixture.ifc';model.write(path);f=parse_ifc(path);r=ifc_answer(f,route('How many windows are in this IFC model?'),'')
   self.assertEqual(r['answer'],1);self.assertEqual(len(r['evidence']),1)

if __name__=='__main__':unittest.main()
