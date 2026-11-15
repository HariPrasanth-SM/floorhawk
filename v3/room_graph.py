"""Physical room graph hypotheses from model polygons + dedicated fixture class.
Sauna benches are grouped inside unique reconstructed rooms, never counted as rooms
one-for-one. Unassigned/ambiguous benches abstain. No references are accepted.
"""
import copy
from shapely.geometry import Polygon,Point
from qa.tools import count

def sauna(facts):
 rooms=[r for r in facts['entities'] if r.get('kind')=='room' and r.get('class') not in ('background','outdoor')];benches=[e for e in facts['entities'] if e.get('kind')=='icon' and e.get('class')=='sauna_bench'];matched={};unassigned=[]
 for bench in benches:
  b=bench['bbox'];p=Point((b[0]+b[2])/2,(b[1]+b[3])/2);hosts=[r for r in rooms if Polygon(r['polygon']).is_valid and Polygon(r['polygon']).covers(p)]
  if len(hosts)!=1:unassigned.append(bench['id']);continue
  matched.setdefault(hosts[0]['id'],{'room':hosts[0],'benches':[]})['benches'].append(bench)
 if unassigned:return None
 selected=[]
 for item in matched.values():
  room=copy.deepcopy(item['room']);room['segmentation_class']=room['class'];room['class']='sauna';room.update(class_name='sauna',semantic_class='sauna',supporting_bench_ids=[e['id'] for e in item['benches']],provenance='Physical-room hypothesis: dedicated sauna-bench detections uniquely contained in this room polygon; not bench count');selected.append(room)
 r=count(selected,'Unique reconstructed physical rooms containing sauna-bench detections');r.update(route='raster.sauna-room-graph.v3',room_graph={'bench_detections':len(benches),'unique_host_rooms':len(selected),'unassigned_benches':unassigned});r['warnings']=['Sauna-room hypothesis from model fixture/room geometry; false bench detections or omissions can change count.','Zero is a model prediction, not verified absence. No localization accuracy established.'];return r
