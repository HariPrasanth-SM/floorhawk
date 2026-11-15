import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from PIL import Image
from diagnostic_export import build_archive,sanitize

class DiagnosticExportTests(unittest.TestCase):
 def test_allowlisted_reference_free_archive_and_cache(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);source=root/'private-drawing.png';Image.new('RGB',(80,60),'white').save(source)
   job={'question':'Count windows','source_path':'/home/private/input.png','input_kind':'image','credit':'Company drawing attribution','pages':[{'page':1,'width':80,'height':60}], 'reference':99,
        'prediction':{'status':'success','answer':1,'expected':3,'token':'DO_NOT_EXPORT','api_key':'DO_NOT_EXPORT','prompt':'DO_NOT_EXPORT','cache_path':'/home/private/cache','timing':{'input_tokens':23},'paired':{'local':{'answer':1},'hybrid':{'answer':2,'evidence_ids':['one']}},'evidence':[{'id':'one','bbox':[2,3,20,30],'source_model':'detector','reference':99}]},
        'review':{'revision':0,'reviewed':False,'answer':1,'boxes':[{'xyxy':[2,3,20,30],'included':True,'evidence_id':'one'}]}}
   archive=build_archive(job,source,source,root/'exports')
   self.assertEqual(archive,build_archive(job,source,source,root/'exports'))
   with zipfile.ZipFile(archive) as z:
    self.assertEqual(set(z.namelist()),{'source.png','local-evidence.png','diagnostic.json'})
    raw=z.read('diagnostic.json').decode();data=json.loads(raw)
    for forbidden in ['DO_NOT_EXPORT','expected','reference','/home/','private-drawing','api_key','cache_path']:self.assertNotIn(forbidden,raw)
    self.assertEqual(data['input']['sha256'],hashlib.sha256(source.read_bytes()).hexdigest())
    self.assertEqual(data['original_prediction']['timing']['input_tokens'],23)
    self.assertEqual(data['original_prediction']['evidence'][0]['bbox'],[2,3,20,30])
    self.assertEqual(data['human_review']['answer'],1)
   job['review']['revision']=1
   self.assertNotEqual(archive,build_archive(job,source,source,root/'exports'))
 def test_paths_credentials_and_source_omission(self):
  self.assertEqual(sanitize({'note':'read /home/test-user/private/file.png','access_token':'x','token_usage':{'total_tokens':10}}),{'note':'read [private path]','token_usage':{'total_tokens':10}})
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'a.ifc';source.write_text('IFC fixture')
   archive=build_archive({'question':'Property','prediction':{'answer':'A'},'review':{}},source,root/'missing.png',root/'out')
   with zipfile.ZipFile(archive) as z:
    self.assertEqual(z.namelist(),['diagnostic.json']);self.assertFalse(json.loads(z.read('diagnostic.json'))['input']['source_included'])

if __name__=='__main__':unittest.main()
