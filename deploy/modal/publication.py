"""Bounded synchronization cache for immutable, already-published job artifacts.

This never reuses extraction or answers for another job. Ownership must be
checked by the caller before synchronization or any artifact is returned.
"""
from collections import OrderedDict

class PublishedJobs:
 def __init__(self,volume,limit=256):
  self.volume=volume;self.limit=limit;self.terminal=OrderedDict()
 def sync(self,ident,read):
  if ident in self.terminal:
   self.terminal.move_to_end(ident);return
  self.volume.reload()
  job=read(ident)
  if job.get('status')not in ['queued','running','reserved']:
   self.terminal[ident]=True
   while len(self.terminal)>self.limit:self.terminal.popitem(last=False)
