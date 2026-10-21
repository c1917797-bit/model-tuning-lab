"""Exact saved ABI geometry and explicit private unused-arena reconstruction."""
SHAPE=(4584,128,256)
STRIDE=(32768,256,1)
K_OFFSET=2933760
V_OFFSET=153142272
VIEW_ELEMENTS=4584*128*256
STORAGE_ELEMENTS=V_OFFSET+VIEW_ELEMENTS
VALID=132
FILLERS=('all_zero','finite_alternating')
KWARGS=('actual_seq_lengths','actual_seq_lengths_kv','atten_mask','block_size','block_table','input_layout',
    'key','num_heads','num_key_value_heads','query','scale','sparse_mode','value')


def rows(table):
    if type(table)is not list or len(table)!=36 or table not in([*range(12,24),*([0]*24)],[*range(60,72),*([0]*24)]):
        raise ValueError('exact original complete block-table row, never remap')
    return [table[token//128]*128+token%128 for token in range(VALID)]


def check_identity(frame):
    kw=frame['kernel'][0]['explicit_kwargs']
    if sorted(kw)!=list(KWARGS):raise ValueError('exact original13 keyword arguments; no defaults added')
    for name,offset in(('key',K_OFFSET),('value',V_OFFSET)):
        x=kw[name]['tensor_identity']
        if tuple(x['shape'])!=SHAPE or tuple(x['stride'])!=STRIDE or x['storage_offset']!=offset or x['dtype']!='torch.bfloat16':
            raise ValueError('exact full4584-paged shared-storage view ABI')
    k,v=(kw[name]['tensor_identity']for name in('key','value'))
    if k['storage_ptr']!=v['storage_ptr']or k['device']!=v['device']:
        raise ValueError('actual key/value share original storage and rank device')
    q=kw['query']['tensor_identity']
    if q['shape']!=[1,6,256]or q['stride']!=[1536,256,1]or q['storage_offset']!=0 or q['dtype']!='torch.bfloat16':
        raise ValueError('exact original contiguous query ABI')
    if(kw['input_layout']!='TND'or kw['num_heads']!=6 or kw['num_key_value_heads']!=1 or kw['scale']!=.0625 or
        kw['sparse_mode']!=3 or kw['block_size']!=128 or kw['actual_seq_lengths']!=[1]or kw['actual_seq_lengths_kv']!=[132]):
        raise ValueError('unchanged original FIA q1/KV132 geometry')
    table=kw['block_table']
    if tuple(table.shape)!=(1,36)or tuple(table.stride())!=(36,1):raise ValueError('exact full original block table shape/stride')
    return rows(table[0].tolist())


def build(t,frame,filler,device):
    """No model/live state writes; full original shape/offset/table with private storage.

    Only valid132 token operands are captured. Every other arena element is an
    explicitly declared reconstruction. Both fillers run every original frame.
    """
    indices=check_identity(frame)
    if filler not in FILLERS:raise ValueError('one of both preregistered finite fillers')
    storage=t.empty(STORAGE_ELEMENTS,dtype=t.bfloat16,device=device)
    if filler=='all_zero':storage.zero_()
    else:
        storage[::2]=.5;storage[1::2]=-.5
    key=t.as_strided(storage,SHAPE,STRIDE,K_OFFSET)
    value=t.as_strided(storage,SHAPE,STRIDE,V_OFFSET)
    selected=t.tensor(indices,dtype=t.int64,device=device)
    key.view(-1,1,256).index_copy_(0,selected,frame['key'].to(device))
    value.view(-1,1,256).index_copy_(0,selected,frame['value'].to(device))
    q=frame['query'].to(device).contiguous();old=frame['kernel'][0]['explicit_kwargs']
    kwargs={name:(q if name=='query'else key if name=='key'else value if name=='value'else
        old[name].to(device).contiguous()if name in('atten_mask','block_table')else old[name])for name in KWARGS}
    return storage,kwargs,selected
