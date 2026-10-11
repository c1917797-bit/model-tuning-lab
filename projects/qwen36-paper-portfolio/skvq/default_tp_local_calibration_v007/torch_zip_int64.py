"""Read bounded ORIGINAL torch.save CPU int64 results without importing Torch.
No arbitrary pickle globals, constructors, execution or candidate decoder.
"""
import collections,io,pickle,struct,zipfile
from pathlib import Path
class Storage:
    pass
def parse_bytes(raw):
    if len(raw)>4*1024*1024:raise ValueError("bounded original group archive")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(n.startswith("/") or ".." in n.split("/") for n in names):
            raise ValueError("archive member identity")
        roots={n.split("/")[0] for n in names}
        if len(roots)!=1:raise ValueError("one original torch.save archive root")
        prefix=next(iter(roots))+"/"
        if prefix+"data.pkl" not in names:raise ValueError("original PyTorch zip pickle required")
        if any(x.file_size>4*1024*1024 or x.compress_size>4*1024*1024 for x in z.infolist()):
            raise ValueError("bounded archive members")
        order=z.read(prefix+"byteorder") if prefix+"byteorder" in names else None
        if order!=b"little":raise ValueError("actual stored little endian proof required")
        def storage(pid):
            if (type(pid) is not tuple or len(pid)!=5 or pid[0]!="storage" or pid[1] is not Storage or
                type(pid[2]) is not str or not pid[2].isdigit() or pid[3]!="cpu" or
                type(pid[4]) is not int or not 0<pid[4]<=1024):
                raise ValueError("only original CPU int64 bounded storage")
            name=prefix+"data/"+pid[2];b=z.read(name)
            if len(b)!=pid[4]*8:raise ValueError("whole int64 storage bytes")
            return struct.unpack("<"+"q"*pid[4],b)
        def tensor(st,offset,size,stride,requires_grad,hooks,*extra):
            if (type(offset) is not int or offset!=0 or type(size) is not tuple or len(size)!=1 or
                type(size[0]) is not int or not 0<size[0]<=1024 or
                stride!=(1,) or requires_grad is not False or size[0]!=len(st) or extra):
                raise ValueError("ordinary unviewed original contiguous one-dimensional int64 tensor")
            if hooks is not None and type(hooks) not in (dict,collections.OrderedDict):
                raise ValueError("no tensor hook constructor")
            return {"storage_int64":list(st),"shape":list(size),"stride":list(stride)}
        class Safe(pickle.Unpickler):
            def find_class(self,module,name):
                allowed={("torch","LongStorage"):Storage,
                    ("torch._utils","_rebuild_tensor_v2"):tensor,
                    ("collections","OrderedDict"):collections.OrderedDict}
                if (module,name) not in allowed:raise ValueError("forbidden pickle global:"+module+"."+name)
                return allowed[(module,name)]
            def persistent_load(self,pid):return storage(pid)
        result=Safe(io.BytesIO(z.read(prefix+"data.pkl"))).load()
        if type(result) is not dict or set(result)!={"reorder_indices","cluster_st_inds"}:
            raise ValueError("original author result dictionary")
        return result
def decode(path):
    with Path(path).open("rb") as h:raw=h.read(4*1024*1024+1)
    return parse_bytes(raw)
