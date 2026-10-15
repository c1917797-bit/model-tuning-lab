"""CPU-only certificate from actual pinned prebuilt GDN metadata, no tensor readback."""
from dataclasses import dataclass
def version(tensor):
    try:return tensor._version
    except RuntimeError:return None  # actual inference tensor; tested separately
@dataclass(frozen=True)
class Certificate:
    tokens:int
    chunks:int
    cu:object
    indices:object
    cu_version:int
    index_version:int
    prefix:str
    host_boundaries:tuple
def host_geometry(cu,flat,tokens):
    if not isinstance(cu,(tuple,list)) or not isinstance(flat,(tuple,list)):return None
    if len(cu)<2 or len(cu)>17 or any(type(x)is not int for x in cu):return None
    if cu[0]!=0 or cu[-1]!=tokens or not 0<tokens<2**31:return None
    # Zero-length compact-ranked metadata requires a separate qualification.
    if any(b<=a for a,b in zip(cu,cu[1:])):return None
    expected=[]
    for seq,(a,b)in enumerate(zip(cu,cu[1:])):
        for chunk in range((b-a+63)//64):expected.extend((seq,chunk))
    if tuple(flat)!=tuple(expected):return None
    return len(expected)//2
def certificate(prebuilt,cu,tokens,prefix,qualified_lengths):
    if prebuilt is None or tokens not in qualified_lengths:return None
    host=getattr(prebuilt,'cu_seqlens_host',None)
    flat=getattr(prebuilt,'chunk_indices_chunk64_host',None)
    count=host_geometry(host,flat,tokens)
    indices=getattr(prebuilt,'chunk_indices_chunk64',None)
    if count is None or indices is None:return None
    if indices.ndim!=2 or tuple(indices.shape)!=(count,2) or not indices.is_contiguous():return None
    if cu is None or cu.ndim!=1 or len(cu)!=len(host) or not cu.is_contiguous():return None
    return Certificate(tokens,count,cu,indices,version(cu),version(indices),prefix,tuple(host))
def consume(cert,A,cu,indices,dtype):
    if cert is None or cu is not cert.cu or indices is not cert.indices:return None
    if version(cu)!=cert.cu_version or version(indices)!=cert.index_version:return None
    if A.shape[1]!=cert.tokens or cu.device!=A.device or indices.device!=A.device:return None
    return dict(validated_length=cert.tokens,qualified_length=cert.tokens,chunks=cert.chunks,
                host_boundaries=cert.host_boundaries,cu_pointer=cu.data_ptr(),index_pointer=indices.data_ptr())
