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

def assemble_formal_prompts(native_prefix, public_segment, private_parts):
    """Assemble supplied tokenized streams without altering their identities.

    Tokenization/generation is external and must be frozen before device runs.
    No algorithm hook or successful-case treatment implementation is reused.
    """
    native=tuple(native_prefix);public=tuple(public_segment)
    parts=tuple(private_parts)
    if len(native)!=8192 or len(public)!=16384 or len(parts)!=40:
        raise ValueError("formal native/PIC/full40 denominator required")
    def tokens(xs):
        if any(type(x) is not int or x<0 for x in xs):
            raise ValueError("nonnegative integer token IDs required")
    tokens(native);tokens(public)
    prompts=[]
    for index,(bridge,tail) in enumerate(parts):
        x=formal_layout(index);bridge=tuple(bridge);tail=tuple(tail)
        tokens(bridge);tokens(tail)
        if len(bridge)!=x.bridge or len(tail)!=x.tail:
            raise ValueError("private bridge/tail geometry mismatch")
        prompt=native+bridge+public+tail
        if len(prompt)!=x.total or prompt[x.pic_start:x.pic_end]!=public:
            raise ValueError("formal segment identity mismatch")
        # Keep explicit independent segment coordinates for runtime selection.
        prompts.append({"index":index,"token_ids":prompt,
                        "segment_start":x.pic_start,"segment_end":x.pic_end})
    return tuple(prompts)
