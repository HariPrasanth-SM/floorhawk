"""Versioned finite evidence contracts; no executable tool strings."""
from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
class BoxEvidence(BaseModel):
 model_config=ConfigDict(extra='forbid')
 id:str=Field(min_length=1,max_length=80)
 region_id:Literal['page-1']
 target:str=Field(max_length=40)
 bbox_1000_yxyx:list[float]=Field(min_length=4,max_length=4)
 text:str=Field(default='',max_length=120)
class EvidencePatch(BaseModel):
 model_config=ConfigDict(extra='forbid')
 objects:list[BoxEvidence]=Field(max_length=60)
 proposal_usable:bool
 caveat:str=Field(max_length=500)
class Request(BaseModel):
 model_config=ConfigDict(extra='forbid')
 question:str=Field(min_length=1,max_length=4000)
 mode:Literal['local','hybrid']='local'

# The provider accepts a smaller schema dialect. Full constraints remain local.
PATCH_PROVIDER_SCHEMA={'type':'object','properties':{'objects':{'type':'array','maxItems':60,'items':{'type':'object','properties':{'id':{'type':'string'},'region_id':{'type':'string','enum':['page-1']},'target':{'type':'string'},'bbox_1000_yxyx':{'type':'array','items':{'type':'number'},'minItems':4,'maxItems':4},'text':{'type':'string'}},'required':['id','region_id','target','bbox_1000_yxyx','text'],'additionalProperties':False}},'proposal_usable':{'type':'boolean'},'caveat':{'type':'string'}},'required':['objects','proposal_usable','caveat'],'additionalProperties':False}
