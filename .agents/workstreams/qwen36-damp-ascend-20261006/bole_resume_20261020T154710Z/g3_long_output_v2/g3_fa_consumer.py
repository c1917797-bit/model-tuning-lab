"""Independent actual long-prefix scratch operand join; original oracle unchanged."""
import sourceio as C
import g3_fia_contract as DOMAIN


def bits(t,a,b,why):
    C.need(a.dtype==b.dtype and a.shape==b.shape and
        t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8)),why)


def consume(t,row,anchor,length):
    g=DOMAIN.shape(length);proof=anchor['ownership']
    DOMAIN.allocation(table=proof['CPU_table'],physical_blocks=proof['request_physical_blocks'],
        ratio=proof['blocks_per_phys_block'],physical_size=proof['physical_block_size'],
        kernel_size=proof['kernel_block_size'],use_hybrid=proof['use_hybrid_blocks'])
    native=row['trial']['native_before'];receipt=row['trial']['fp16_boundary']
    C.need(receipt['scratch_kernel_pages']==g['scratch_kernel_pages']and
        receipt['publication_kernel_pages']==g['publication_kernel_pages']and
        receipt['physical_allocation_growth_proven']is False,
        'actual declared new FA scratch/publication domain receipt')
    C.need(native['key'].shape==native['value'].shape==g['KV_shape']and
        native['query'].shape==g['query_shape']and native['atten_mask'].shape==g['mask_shape']and
        native['block_table'].shape==g['table_shape'],'actual long-prefix FIA operand shapes')
    bits(t,native['query'],row['query'].reshape(3,6,256).permute(1,0,2).unsqueeze(0),
        'exact original post-RoPE three query operands')
    for name in('key','value'):
        expected=t.zeros(g['KV_shape'],dtype=t.bfloat16)
        flat=expected.permute(0,2,1,3).reshape(-1,1,256)
        # n_kv_heads1 makes this exact contiguous logical page order.
        flat[:length].copy_(anchor[name].reshape(-1,1,256)[:length])
        flat[length:length+3].copy_(row[name].reshape(3,1,256))
        bits(t,native[name],expected,'actual whole private scratch prefix/nodes/zero padding '+name)
    mask=t.ones(g['mask_shape'],dtype=t.bool)
    mask[0,0,:,:length+1]=False;mask[0,0,1,length+1]=False;mask[0,0,2,length+2]=False
    bits(t,native['atten_mask'],mask,'actual sibling isolation and all physical padding forbidden')
    table=t.arange(g['scratch_kernel_pages'],dtype=t.int32).reshape(1,-1)
    bits(t,native['block_table'],table,'actual complete private contiguous scratch table')
    return True
