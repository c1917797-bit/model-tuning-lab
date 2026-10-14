"""Independent arithmetic layout for the reviewed successful-case protocol."""
from dataclasses import dataclass

@dataclass(frozen=True)
class FormalLayout:
    total: int
    native_prefix: int
    bridge: int
    pic_start: int
    pic_end: int
    tail: int

def formal_layout(index):
    if type(index) is not int or index<0:
        raise ValueError("nonnegative integer request index required")
    total,native,pic=32768,8192,16384
    bridge=1024+(index%13)*512
    start=native+bridge
    end=start+pic
    tail=total-end
    if tail<512:raise ValueError("insufficient private tail")
    return FormalLayout(total,native,bridge,start,end,tail)
