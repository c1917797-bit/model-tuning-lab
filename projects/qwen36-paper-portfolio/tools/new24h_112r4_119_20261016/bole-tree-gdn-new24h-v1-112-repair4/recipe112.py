import math

SEED=2610161121


def parents(kind, depth):
    # depth is max strict ancestors; depth0 = one node.
    if kind == 'chain':return [-1]+list(range(depth))
    # Two branches share root; forest has two independent roots.
    p=[-1] if kind == 'branch' else [-1,-1]
    tips=[0,0] if kind == 'branch' else [0,1]
    for _ in range(depth):
        for branch in range(2):
            p.append(tips[branch]);tips[branch]=len(p)-1
    return p


def masks(t, p):
    n=len(p);a=t.zeros((n,n),dtype=t.float32)
    for i,parent in enumerate(p):
        if parent>=0:a[i]=a[parent];a[i,parent]=1
    return a,a+t.eye(n)


def cases(profile):
    if profile=='smoke':return [(1,'branch',2),(16,'forest',2)]
    return [(b,kind,d) for b in (1,16) for kind in ('chain','branch','forest') for d in (0,1,3,7)]


def recipe(t,b,kind,d,case_index):
    p=parents(kind,d);g=t.Generator(device='cpu').manual_seed(SEED+case_index)
    initial=t.randn((b,12,128,128),generator=g,dtype=t.float32)*.01
    steps=[]
    for step in range(3):
        q=t.randn((b,4,len(p),128),generator=g);k=t.randn(q.shape,generator=g)
        q=(q/(q.square().sum(-1,keepdim=True)+1e-6).sqrt()).bfloat16()
        k=(k/(k.square().sum(-1,keepdim=True)+1e-6).sqrt()).bfloat16()
        v=(t.randn((b,12,len(p),128),generator=g)*.1).bfloat16()
        beta=t.rand((b,12,len(p)),generator=g)*.8
        gamma=t.rand((b,12,len(p)),generator=g)*.2+.75
        steps.append(dict(q=q,k=k,v=v,beta=beta,gamma=gamma,terminal=(len(p)-1 if step==0 else (0 if step==1 else None))))
    return p,initial,steps


def logical_raw_upper(profile):
    total=0
    for b,kind,d in cases(profile):
        n=len(parents(kind,d))
        # Initial + 3 actual committed FP32 states; eachstep original q/k/v,
        # gamma/beta, output FP32 and P/U factorreadback. + 64KiB serialization.
        total+=4*b*12*128*128*4
        total+=3*(b*(8+12)*n*128*2+b*12*n*(2*4+128*4+4+128*4)+65536)
    return total
