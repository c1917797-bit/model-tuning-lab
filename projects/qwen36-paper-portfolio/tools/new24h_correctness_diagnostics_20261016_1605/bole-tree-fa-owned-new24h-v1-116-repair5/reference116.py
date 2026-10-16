"""CPUfloat32 path oracle, independent of FIA packed mask and API."""
def path_fp32(t,raw):
    q=raw['query'].float();k=raw['key'].float();v=raw['value'].float()
    b,h,n,d=q.shape;hk=k.shape[1];output=t.empty_like(q);paths=[]
    for i,parent in enumerate(raw['parents']):
        if not -1<=parent<i:raise ValueError('parent-before-child')
        paths.append(([]if parent<0 else paths[parent])+[i])
    for request,length in enumerate(raw['prefixes']):
        for head in range(h):
            kh=head//(h//hk)
            for node,path in enumerate(paths):
                index=list(range(length))+[length+j for j in path]
                score=t.mv(k[request,kh,index],q[request,head,node])*raw['scale']
                exp=(score-score.max()).exp();prob=exp/exp.sum()
                output[request,head,node]=t.mv(v[request,kh,index].transpose(0,1),prob)
    return output
