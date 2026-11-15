import unittest
from qa.router import route
from qa.tools import pdf_answer,raster_answer,ifc_answer
class CorridorTests(unittest.TestCase):
 def facts(self):return {'pages':[{'page':1}],'entities':[{'id':str(i),'kind':'room','room_number':'1.'+str(i),'label':label,'page':1,'bbox':[0,0,10,10]}for i,label in enumerate(['Korridor','Korridor','Kitchen','Corridor','Hall'])]}
 def test_narrow_count_route(self):
  task=route('How many corridors are available?');self.assertEqual(task['target'],'room');self.assertEqual(pdf_answer(self.facts(),task,'How many corridors?')['answer'],3)
 def test_does_not_count_halls_or_all_rooms(self):
  q='How many corridors are there?';r=pdf_answer(self.facts(),route(q),q);self.assertEqual({e['label']for e in r['evidence']},{'Korridor','Corridor'})
 def test_doors_in_corridor_stays_door_target(self):self.assertEqual(route('How many doors are in the corridor?')['target'],'door')
 def test_other_formats_do_not_count_all_rooms(self):
  t=route('How many corridors?');self.assertEqual(raster_answer(self.facts(),t,'How many corridors?')['status'],'unsupported');self.assertEqual(ifc_answer(self.facts(),t,'How many corridors?')['status'],'unsupported')
if __name__=='__main__':unittest.main()
