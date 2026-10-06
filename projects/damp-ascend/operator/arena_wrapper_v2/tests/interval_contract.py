"""Stdlib model of v2 DATA-span admission; not Tensor/NPU validation."""
from dataclasses import dataclass

MAXPTR = (1 << 64) - 1
MAXI64 = (1 << 63) - 1


@dataclass(frozen=True)
class View:
    base: int
    backing_bytes: int
    data: int
    element_offset: int
    count: int
    item_bytes: int
    nd: bool = True
    contiguous: bool = True
    device: str = "npu:0"


def data_span(view, query_device="npu:0", writer=False):
    if not view.nd or not view.contiguous or view.device != query_device:
        raise ValueError("physical ND/contiguous/same-device required")
    if not 0 < view.count <= MAXI64 or not 0 < view.item_bytes <= MAXPTR:
        raise ValueError("nonempty positive-width tensor required")
    if view.count > MAXPTR // view.item_bytes:
        raise ValueError("byte-count overflow")
    if not 0 < view.base <= MAXPTR or not 0 < view.backing_bytes <= MAXPTR - view.base:
        raise ValueError("backing byte range empty/overflows")
    if not 0 <= view.element_offset <= MAXI64:
        raise ValueError("negative/invalid storage offset")
    if view.element_offset > MAXPTR // view.item_bytes:
        raise ValueError("storage offset byte-conversion overflow")
    offset = view.element_offset * view.item_bytes
    if offset >= view.backing_bytes or offset > MAXPTR - view.base:
        raise ValueError("storage offset outside backing")
    if view.data != view.base + offset:
        raise ValueError("data pointer disagrees with element offset")
    size = view.count * view.item_bytes
    if size > view.base + view.backing_bytes - view.data:
        raise ValueError("data interval outside backing")
    if view.data % 32:
        raise ValueError("pointer is not 32B aligned")
    if writer and size % 32:
        raise ValueError("writer length is not 32B aligned")
    return view.data, view.data + size


def disjoint(a, b):
    return a[1] <= b[0] or b[1] <= a[0]


def admit(writers, readers):
    spans_w = [data_span(v, writer=True) for v in writers]
    spans_r = [data_span(v) for v in readers]
    for index, span in enumerate(spans_w):
        if any(not disjoint(span, other) for other in spans_w[index + 1:] + spans_r):
            raise ValueError("DATA byte interval overlap")
    return True
