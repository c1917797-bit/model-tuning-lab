"""Exact token-based canonical public and relocated private segment selection."""
from dataclasses import dataclass
import hashlib,json
@dataclass(frozen=True)
class SegmentSelection:
    start: int
    end: int
    public: bool
    tokens_sha256: str

def token_digest(tokens):
    values=tuple(tokens)
    if not values or any(type(x) is not int or x<0 for x in values):
        raise ValueError("nonempty nonnegative integer token IDs required")
    return hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest()

def select_segment(prompt_tokens,public_tokens,*,canonical_public=False):
    prompt=tuple(prompt_tokens);public=tuple(public_tokens)
    digest=token_digest(public);token_digest(prompt)
    if canonical_public:
        if prompt!=public:raise ValueError("canonical public prompt must equal exact frozen tokens")
        return SegmentSelection(0,len(public),True,digest)
    matches=[i for i in range(len(prompt)-len(public)+1) if prompt[i:i+len(public)]==public]
    if len(matches)!=1:
        raise ValueError("private prompt requires one unambiguous public segment")
    start=matches[0]
    return SegmentSelection(start,start+len(public),False,digest)

def require_full_scheduled_segment(selection,request):
    """First implementation supports complete scheduled Prefill, not partial reuse."""
    if request.computed_tokens>selection.start:
        raise ValueError("prefix caching already overlaps selected segment")
    if request.computed_tokens+request.scheduled_tokens<selection.end:
        raise ValueError("chunked prefill does not yet cover complete segment")
    return selection.start-request.computed_tokens,selection.end-request.computed_tokens
