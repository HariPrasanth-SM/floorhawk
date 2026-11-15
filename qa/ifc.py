"""IFC occurrences, containment, units, properties and QTOs; never reads associated files."""
import re

def parse_ifc(path):
 import ifcopenshell
 from ifcopenshell.util.element import get_psets,get_container,get_materials,get_type
 from ifcopenshell.util.unit import calculate_unit_scale
 model=ifcopenshell.open(str(path));entities=[];warnings=[]
 scales={k:calculate_unit_scale(model,k) for k in ['LENGTHUNIT','AREAUNIT','VOLUMEUNIT']}
 for obj in model.by_type('IfcProduct'):
  guid=getattr(obj,'GlobalId',None)
  if not guid:continue
  container=get_container(obj);floor=container
  for _ in range(8):
   if floor is None or floor.is_a('IfcBuildingStorey'):break
   floor=get_container(floor)
  if obj.is_a('IfcBuildingStorey'):floor=obj
  data={'id':guid,'guid':guid,'kind':'ifc_occurrence','class':obj.is_a(),'name':getattr(obj,'Name',None),'long_name':getattr(obj,'LongName',None),'description':getattr(obj,'Description',None),'predefined_type':getattr(obj,'PredefinedType',None),'object_type':getattr(obj,'ObjectType',None),'floor':getattr(floor,'Name',None),'floor_guid':getattr(floor,'GlobalId',None),'elevation':getattr(obj,'Elevation',None),'properties':{},'quantities':{},'materials':[],'method':'IFC explicit occurrence'}
  # IFC product excludes type definitions. Each GUID is represented once.
  if obj.is_a('IfcElement') or obj.is_a('IfcSpace') or obj.is_a('IfcBuildingStorey'):
   data['properties']=get_psets(obj,psets_only=True)
   data['quantities']=get_psets(obj,qtos_only=True)
   data['materials']=[getattr(m,'Name',None) for m in get_materials(obj)]
   typ=get_type(obj)
   if typ:data['type']={'guid':getattr(typ,'GlobalId',None),'name':getattr(typ,'Name',None),'class':typ.is_a()}
  entities.append(data)
 apps=[{'name':a.ApplicationFullName,'version':a.Version,'identifier':a.ApplicationIdentifier} for a in model.by_type('IfcApplication')]
 return {'kind':'ifc','entities':entities,'schema':model.schema,'applications':apps,'unit_scales_to_si':scales,'warnings':warnings+['Counts use explicit occurrence classes, not type definitions.','Missing QTO is not zero; quantities may have inherited type properties.','Floor-scoped queries require matched spatial containment. No geometry-derived quantities are silently substituted.'],'tool':'IfcOpenShell'}
