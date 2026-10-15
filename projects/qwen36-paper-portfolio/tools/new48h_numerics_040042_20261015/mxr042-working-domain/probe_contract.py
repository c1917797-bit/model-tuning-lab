"""Fixed two real heldout frames plus separate initial-state calibration, 3 repeats."""
REPEATS=3
FRAMES=3
ARMS=('native','candidate','a32_refined','cpu64_cast')
CANDIDATE_HITS=FRAMES*REPEATS*2
def ready(v,sr):
 return v['source']==sr and v['primary']is None and len(v['raws'])==FRAMES*REPEATS and len({r['path']for r in v['raws']})==FRAMES*REPEATS and v['candidate_hits']==CANDIDATE_HITS and len(v['teardown'])==3 and all(x.get('pass_release')is True for x in v['teardown'])
