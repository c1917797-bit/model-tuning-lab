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

def exact_occurrences(prompt,public):
    if not public:raise ValueError("nonempty public segment required")
    # Linear exact matching avoids allocating a full segment tuple at every
    # candidate offset for16K/32K inputs. Still rejects repeated occurrences.
    failure=[0]*len(public);j=0
    for i in range(1,len(public)):
        while j and public[i]!=public[j]:j=failure[j-1]
        if public[i]==public[j]:j+=1
        failure[i]=j
    matches=[];j=0
    for i,value in enumerate(prompt):
        while j and value!=public[j]:j=failure[j-1]
        if value==public[j]:j+=1
        if j==len(public):
            matches.append(i-len(public)+1)
            if len(matches)>1:break
            j=failure[j-1]
    return tuple(matches)

def select_segment(prompt_tokens,public_tokens,*,canonical_public=False):
    prompt=tuple(prompt_tokens);public=tuple(public_tokens)
    digest=token_digest(public);token_digest(prompt)
    if canonical_public:
        if prompt!=public:raise ValueError("canonical public prompt must equal exact frozen tokens")
        return SegmentSelection(0,len(public),True,digest)
    matches=exact_occurrences(prompt,public)
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
