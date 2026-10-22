"""Pure exact observer tap renderer. Never removes/changes candidate math or write actions."""
def need(v,s):
    if not v:raise ValueError(s)


def once(s,a,b):
    need(s.count(a)==1,'exact one actual source tap: '+a[:80])
    return s.replace(a,b,1)


def render(files):
    out=dict(files)
    s=out['model_entry.py']
    s=once(s,"  ctx=BUS.get();ctx.visit(b['index'],'gdn');t=self.t",
      "  ctx=BUS.get();qual=getattr(self,'fastpath_numeric_observer',None)\n  if qual is not None:qual.before_layer(self,b)\n  ctx.visit(b['index'],'gdn');t=self.t")
    marker="  # These are the actual model methods/operators, not a second projection model."
    s=once(s,marker,
      "  if qual is not None:qual.conv(b,trial,weight,obj.conv1d.bias,bool(obj.activation),convolved,tail)\n"+marker)
    marker="  output.copy_(value.permute(0,2,1,3).squeeze(0).to(output.dtype))"
    s=once(s,marker,marker+"\n  if qual is not None:qual.gdn(b,qh,kh,vh,bh,gamma,state,value,factors,output)")
    out['model_entry.py']=s
    s=out['service_bridge.py']
    s=once(s," ctx=BUS.get();ctx.visit(b['index'],'fa');t=self.t;o=ctx.owner",
      " ctx=BUS.get();qual=getattr(self,'fastpath_numeric_observer',None)\n if qual is not None:qual.before_layer(self,b)\n ctx.visit(b['index'],'fa');t=self.t;o=ctx.owner")
    marker=" out,_=self.A.native(t,boundary,trial,actual_fia,sparse_mode=1)"
    s=once(s,marker,marker+"\n if qual is not None:qual.fa(b,query,key,value,out,physical,(tensor_id(b['key']),tensor_id(b['value'])))")
    out['service_bridge.py']=s
    s=out['service_runner.py']
    marker="        SB.install_methods(bridge, state.live, C, m)"
    s=once(s,marker,marker+"""
        import fastpath_numeric_observer as FQ
        if os.environ.get(FQ.FLAG)=='1':
            import fastpath_numeric_sink as FQS
            E.need(fast_performance,'qualification must exercise actual FAST elisions')
            sink=FQS.configure(torch,C,source_ref,m,group.rank_in_group)
            bridge.fastpath_numeric_observer=FQ.install(torch,C,source_ref,m,group.rank_in_group,
                snapshot=_snap,sink=sink)
            state.request_restorers.append(bridge.fastpath_numeric_observer.close)
""".rstrip())
    marker="        state.live.publication(publication)"
    s=once(s,marker,marker+"""
        qualifier=getattr(state.bridge,'fastpath_numeric_observer',None)
        if qualifier is not None:
            qualifier.publication(state.bridge,proposal,publication)
""".rstrip())
    out['service_runner.py']=s
    for name,s in out.items():compile(s,name,'exec')
    return out
