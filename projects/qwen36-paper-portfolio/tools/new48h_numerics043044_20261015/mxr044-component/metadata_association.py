"""Unique producer epochs + single-per-layer consumption of actual metadata.

Pinned builder creates a fresh chunk object per build. Attach alone never grants
a certificate. Reattaching/reusing an inference tensor without a fresh producer
epoch cannot re-arm a previously consumed layer.
"""
import weakref
from metadata_certificate import version
class Associations:
 def __init__(self):self.rows={};self.created={};self.epoch=0
 def produced(self,metadata):
  if metadata is None:return
  key=id(metadata);self.epoch+=1
  # A producer must return a genuinely new metadata object, not re-arm old one.
  if key in self.created and self.created[key][0]()is metadata:raise ValueError('builder metadata object reused')
  self.created[key]=(weakref.ref(metadata,lambda unused:self.created.pop(key,None)),self.epoch,
                     tuple(metadata.cu_seqlens_host),tuple(metadata.chunk_indices_chunk64_host))
 def attach(self,metadata,cu):
  if metadata is None or cu is None:return
  key=id(metadata);source=self.created.get(key)
  if source is None or source[0]()is not metadata:return
  if key in self.rows and self.rows[key]['meta']()is metadata:raise ValueError('metadata attached twice')
  self.rows[key]=dict(meta=weakref.ref(metadata,lambda unused:self.rows.pop(key,None)),
    cu=cu,host=source[2],flat=source[3],epoch=source[1],
    cu_version=version(cu),index_version=version(metadata.chunk_indices_chunk64),
    indices=metadata.chunk_indices_chunk64,used_prefixes=set())
 def verified(self,metadata,cu,prefix=None):
  row=self.rows.get(id(metadata));source=self.created.get(id(metadata))
  if row is None or source is None or row['meta']()is not metadata or row['cu']is not cu:return False
  ok=(row['epoch']==source[1]and tuple(metadata.cu_seqlens_host)==row['host']
      and tuple(metadata.chunk_indices_chunk64_host)==row['flat']
      and metadata.chunk_indices_chunk64 is row['indices']
      and version(cu)==row['cu_version']and version(row['indices'])==row['index_version'])
  if prefix is None:return ok
  if not ok or prefix in row['used_prefixes']:return False
  row['used_prefixes'].add(prefix)
  return True
