"""Exact persisted nine-step per-layer evidence, independent of candidate math."""
def check(notes,prefixes):
 ps=set(prefixes)
 if len(ps)!=48 or len(notes)!=432:raise ValueError('all48 times9 actual decode records required')
 keys=[(n['prefix'],n['prefill_tokens'],n['step'])for n in notes]
 if len(set(keys))!=432 or set(keys)!={(p,2048,s)for p in ps for s in range(9)}:raise ValueError('no duplicate/missing/relabelled actual2K decode step')
 return dict(layers=48,steps=9,rows=432,scope='one-request physical-slot continuity; no request reset/reuse/graph proof')
