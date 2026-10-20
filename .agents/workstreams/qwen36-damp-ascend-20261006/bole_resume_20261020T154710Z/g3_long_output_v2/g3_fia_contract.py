"""Declared fixed1024 FA domain inside one native1536 physical allocation."""
from sourceio import need
PREFIX=131
OUTPUT=1024
MAX_BEFORE=PREFIX+OUTPUT-2
KERNEL=128
PHYSICAL=1536


def shape(length):
    need(type(length)is int and PREFIX<=length<=MAX_BEFORE,
         'declared actual long-output committed prefix131..1153')
    scratch=(length+3+127)//128
    publication=(length+2+127)//128
    need(2<=publication<=scratch<=10 and length+3<=PHYSICAL,
         'three private branch rows inside initial1536 physical capacity')
    return dict(length=length,query_shape=(1,6,3,256),KV_shape=(scratch,1,128,256),
        mask_shape=(1,1,3,scratch*128),table_shape=(1,scratch),
        scratch_kernel_pages=scratch,publication_kernel_pages=publication,
        initial_kernel_pages=12,physical_allocation_growth_proven=False)


def allocation(*,table,physical_blocks,ratio,physical_size,kernel_size,use_hybrid):
    need(type(ratio)is int and ratio==12 and physical_size==PHYSICAL and kernel_size==KERNEL and
         use_hybrid is True and len(physical_blocks)==1 and type(physical_blocks[0])is int and
         physical_blocks[0]>=0 and tuple(table)==tuple(physical_blocks[0]*12+j for j in range(12)),
         'actual one native1536 physical block expanded to its exact12 kernel pages; allocation growth excluded')
    return True
