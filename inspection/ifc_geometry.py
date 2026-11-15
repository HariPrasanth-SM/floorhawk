from runtime_paths import DATASET_ROOT,MODEL_ROOT,RESULTS_ROOT,CACHE_ROOT
"""Bounded CPU IFC-to-GLB conversion with verified GlobalId mesh metadata.
No inference/model/provider imports. Original inputs never modified.
"""
import json,time,struct,hashlib,argparse,os
from pathlib import Path
from qa.common import ROOT,sha,write_json
VERSION='ifc-glb-si-world-v1';CACHE=CACHE_ROOT/'inspection-ifc';CACHE.mkdir(exist_ok=True)
def key(source):return sha(source)+'-'+VERSION
def convert(source,max_seconds=90,max_elements=2000,max_triangles=1_000_000):
 import ifcopenshell,ifcopenshell.geom,numpy as np
 from ifcopenshell.util.unit import calculate_unit_scale
 source=Path(source);dest=CACHE/key(source);dest.mkdir(exist_ok=True);meta=dest/'metadata.json'
 if meta.exists():return dest
 started=time.monotonic();model=ifcopenshell.open(str(source));settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);iterator=ifcopenshell.geom.iterator(settings,model,num_threads=2);meshes=[];failures=[];seen=set();faces_n=0;minimum=np.full(3,np.inf);maximum=np.full(3,-np.inf);partial=False
 if iterator.initialize():
  while True:
   if time.monotonic()-started>max_seconds or len(meshes)>=max_elements:partial=True;break
   shape=iterator.get();guid=shape.guid
   try:
    obj=model.by_guid(guid)
    if obj.GlobalId!=guid:raise ValueError('Mesh GUID verification failed')
    if guid in seen:raise ValueError('Duplicate product mesh')
    vertices=np.asarray(shape.geometry.verts,dtype=np.float64).reshape(-1,3);faces=np.asarray(shape.geometry.faces,dtype=np.uint32).reshape(-1,3)
    if len(vertices)and len(faces):
     if not np.isfinite(vertices).all():raise ValueError('Non-finite coordinates')
     if faces.max()>=len(vertices):raise ValueError('Invalid face index')
     if faces_n+len(faces)>max_triangles:partial=True;break
     minimum=np.minimum(minimum,vertices.min(0));maximum=np.maximum(maximum,vertices.max(0));faces_n+=len(faces);meshes.append((guid,obj.is_a(),str(getattr(obj,'Name','')or''),obj.id(),vertices,faces));seen.add(guid)
   except Exception as e:failures.append({'guid':guid,'reason':str(e)[:140]})
   if not iterator.next():break
 origin=(minimum+maximum)/2 if meshes else np.zeros(3);chunks=[];length=0;views=[];accessors=[];nodes=[];gmeshes=[];mapping=[]
 def append(raw,target,component,count,typ,minval=None,maxval=None):
  nonlocal length
  padding=(-length)%4
  if padding:chunks.append(b'\0'*padding);length+=padding
  index=len(views);views.append({'buffer':0,'byteOffset':length,'byteLength':len(raw),'target':target});chunks.append(raw);length+=len(raw);acc={'bufferView':index,'componentType':component,'count':count,'type':typ}
  if minval is not None:acc.update(min=minval,max=maxval)
  accessors.append(acc);return len(accessors)-1
 for guid,typ,name,step,vertices,faces in meshes:
  shifted=vertices-origin;positions=np.column_stack([shifted[:,0],shifted[:,2],-shifted[:,1]]).astype('<f4');indices=faces.astype('<u4').reshape(-1);a=append(positions.tobytes(),34962,5126,len(positions),'VEC3',positions.min(0).tolist(),positions.max(0).tolist());b=append(indices.tobytes(),34963,5125,len(indices),'SCALAR');gmeshes.append({'primitives':[{'attributes':{'POSITION':a},'indices':b,'material':0}]});node=len(nodes);nodes.append({'name':'ifc-'+guid,'mesh':len(gmeshes)-1,'extras':{'ifc_guid':guid,'ifc_type':typ,'ifc_name':name,'step_id':step}});mapping.append({'node':node,'guid':guid,'type':typ,'name':name,'step_id':step,'verified_against_ifc':True})
 gltf={'asset':{'version':'2.0','generator':'FloorHAWK bounded IfcOpenShell geometry inspection'},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],'nodes':nodes,'meshes':gmeshes,'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':length}],'materials':[{'name':'IFC context','pbrMetallicRoughness':{'baseColorFactor':[.67,.73,.77,1],'metallicFactor':0,'roughnessFactor':.8},'doubleSided':True}]};jb=json.dumps(gltf,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);binary=b''.join(chunks);binary+=b'\0'*((-len(binary))%4);total=12+8+len(jb)+8+len(binary)
 if total>64*1024**2:raise ValueError('GLB exceeds64MiB bound')
 path=dest/'model.glb';temp=dest/'model.building';temp.write_bytes(struct.pack('<4sII',b'glTF',2,total)+struct.pack('<I4s',len(jb),b'JSON')+jb+struct.pack('<I4s',len(binary),b'BIN\0')+binary);temp.replace(path)
 write_json(meta,{'status':'ready'if meshes else'empty','source_sha256':sha(source),'glb_sha256':sha(path),'ifcopenshell_version':ifcopenshell.version,'model_schema':model.schema,'source_length_unit_scale_to_m':calculate_unit_scale(model),'geometry_units':'metres (IfcOpenShell world coordinates; convert-back-units disabled)','source_world_origin_m':origin.tolist(),'axis_mapping':'IFC(x,y,z) -> glTF(x-originX,z-originZ,-(y-originY)); Y-up, right-handed','source_to_gltf_matrix':[[1,0,0,-float(origin[0])],[0,0,1,-float(origin[2])],[0,-1,0,float(origin[1])],[0,0,0,1]],'mesh_mapping':mapping,'meshes':len(meshes),'triangles':faces_n,'partial':partial,'errors':failures,'seconds':time.monotonic()-started,'limits':{'seconds':max_seconds,'elements':max_elements,'triangles':max_triangles,'glb_bytes':64*1024**2},'note':'Only actual IfcOpenShell meshes are shown; absent representation is not fabricated. GUID mapping verified by source model.by_guid. Recorded quantities/properties are not recomputed from meshes.'});return dest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args();out=convert(a.source);print(json.dumps({'cache':str(out),'metadata':json.loads((out/'metadata.json').read_text())['status']}))
