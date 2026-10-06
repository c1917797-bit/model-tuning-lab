"""Allocator-faithful contiguous typed SoA views sharing one raw ND allocation."""
from selected_contract import arena_layout,require,REGIONS
from evidence import exact

class Arena:
    def __init__(self,torch,npu,nd,slots,kind,golden):
        self.t,self.npu=torch,npu
        self.layout=arena_layout(slots,kind)
        self.raw=nd(((torch.arange(self.layout["bytes"],dtype=torch.int64)*29+73)%256).
                    to(torch.uint8).view(torch.int8))
        self.views={}
        dtypes={"conv":torch.bfloat16,"high":torch.float16,"low":torch.int8,"scales":torch.float32}
        for row in self.layout["regions"]:
            # Do NOT format-cast typed views: that would silently allocate sidecars.
            view=self.raw[row["start"]:row["stop"]].view(dtypes[row["name"]]).view(row["shape"])
            require(view.is_contiguous() and npu.get_npu_format(view)==2 and view.data_ptr()%32==0,
                    "actual typed SoA ND32 views")
            self.views[row["name"]]=view
        self.states=[self.views[n] for n in REGIONS]
        for n in REGIONS: self.views[n].copy_(getattr(golden,n).to(self.raw.device))
        torch.npu.synchronize()
        self.identity=self.identities()
    def identities(self):
        return {n:{"pointer":x.data_ptr(),"base":x.untyped_storage().data_ptr(),
                   "storage_bytes":x.untyped_storage().nbytes(),"offset":x.storage_offset(),
                   "dtype":str(x.dtype),"shape":list(x.shape),"stride":list(x.stride())}
                for n,x in {"raw":self.raw,**self.views}.items()}
    def expected_raw(self,before,golden):
        result=before.clone()
        for row in self.layout["regions"]:
            if row["name"] in REGIONS:
                result[row["start"]:row["stop"]].copy_(getattr(golden,row["name"]).
                    contiguous().view(self.t.int8).reshape(-1))
        return result
    def observe(self,after,before,golden):
        expected=self.expected_raw(before,golden)
        return {"entire_raw_bitwise":exact(self.t,after,expected),
                "all_views_pointer_storage_stride_stable":self.identities()==self.identity,
                "raw_storage_shared":all(x.untyped_storage().data_ptr()==self.raw.untyped_storage().data_ptr()
                                         for x in self.states),
                "full_arena_no_sidecar":all(x.untyped_storage().nbytes()==self.raw.numel()
                                           for x in self.states)}

    def outside_selected(self,before,after,indices):
        keep=self.t.ones(before.numel(),dtype=self.t.bool)
        for row in self.layout["regions"]:
            if row["name"] not in REGIONS:continue
            size=(row["stop"]-row["start"])//self.layout["slots"]
            for slot in indices.tolist():
                if 0<=slot<self.layout["slots"]:
                    keep[row["start"]+slot*size:row["start"]+(slot+1)*size]=False
        return exact(self.t,before[keep],after[keep])
