"""Immutable token catalog; actual multi-segment runtime routing remains separate."""
from independent_segment_selection import token_digest,SegmentSelection,exact_occurrences
class SegmentCatalog:
    def __init__(self,segments,*,boundary_tokens=8):
        if type(boundary_tokens) is not int or boundary_tokens<3:raise ValueError("boundary required")
        entries={}
        for raw in segments:
            tokens=tuple(raw);digest=token_digest(tokens)
            if len(tokens)<=boundary_tokens:raise ValueError("segment has no reusable body")
            if digest in entries:raise ValueError("duplicate segment identity")
            entries[digest]=tokens
        if not 1<=len(entries)<=128:raise ValueError("bounded catalog required")
        from types import MappingProxyType
        self.entries=MappingProxyType(entries);self.boundary=boundary_tokens
    def tokens(self,digest):
        try:return self.entries[digest]
        except KeyError:raise ValueError("unknown public segment identity") from None
    def select_one(self,prompt):
        prompt=tuple(prompt);token_digest(prompt)
        found=[]
        for digest,tokens in self.entries.items():
            matches=exact_occurrences(prompt,tokens)
            if len(matches)>1:raise ValueError("repeated catalog segment ambiguous")
            if matches:
                start=matches[0]
                found.append(SegmentSelection(start,start+len(tokens),False,digest))
        if len(found)!=1:raise ValueError("one unambiguous catalog segment required")
        return found[0]
