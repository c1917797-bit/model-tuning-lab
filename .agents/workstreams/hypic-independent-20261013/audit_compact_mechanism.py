"""Independent exact-coverage auditor for the compact Canary worker ledger."""
from collections import defaultdict


def audit_mechanism(events,acceptance,*,manifest_sha256):
    required_ranks=set(range(4))
    relevant={'compact_public_state_published','compact_public_kv_published',
              'compact_gdn_body_composed','compact_c2_queries_completed',
              'compact_model_rows_completed'}
    events=[e for e in events if e.get('event') in relevant]
    if not events:raise ValueError('no actual compact worker events')
    public_linear=defaultdict(set);public_full=defaultdict(set)
    linear=defaultdict(set);full=defaultdict(set);models={};rank_pids=defaultdict(set)
    for e in events:
        if e.get('manifest_sha256')!=manifest_sha256:raise ValueError('worker manifest identity drift')
        rank=e.get('rank')
        if type(rank) is not int or rank not in required_ranks or type(e.get('pid')) is not int:
            raise ValueError('worker rank/PID coverage invalid')
        rank_pids[rank].add(e['pid']);kind=e['event']
        if kind.startswith('compact_public_'):
            target=public_linear if kind=='compact_public_state_published' else public_full
            if e['layer'] in target[rank]:raise ValueError('duplicate public layer receipt')
            target[rank].add(e['layer']);continue
        if kind=='compact_model_rows_completed':
            ids=tuple(e['request_ids'])
            if not ids or len(set(ids))!=len(ids):raise ValueError('model request IDs invalid')
            if e['original_rows']!=acceptance['original_rows']*len(ids) or e['retained_rows']!=acceptance['model_retained_rows']*len(ids):
                raise ValueError('model did not prune expected rows')
            for rid in ids:
                key=(rank,rid,e['step'])
                if key in models:raise ValueError('duplicate model completion')
                models[key]=e
            continue
        key=(rank,e['request_id'],e['step'])
        target=linear if kind=='compact_gdn_body_composed' else full
        if e['layer'] in target[key]:raise ValueError('duplicate per-request layer receipt')
        if e['retained_rows']!=acceptance['model_retained_rows']:
            raise ValueError('layer projection/query row count mismatch')
        skipped=e.get('skipped_body_tokens') if kind=='compact_gdn_body_composed' else e.get('skipped_body_queries')
        if skipped!=acceptance['skipped_body_rows']:raise ValueError('body work was not skipped')
        if kind=='compact_gdn_body_composed' and e.get('finite') is not True:
            raise ValueError('linear state finite receipt missing')
        target[key].add(e['layer'])
    if set(rank_pids)!=required_ranks or any(len(pids)!=1 for pids in rank_pids.values()):
        raise ValueError('one stable worker PID per TP rank required')
    if set(linear)!=set(full) or set(linear)!=set(models):raise ValueError('request/step mechanism coverage incomplete')
    rank_ids=[]
    for rank in range(4):
        if len(public_linear[rank])!=acceptance['public_state_per_rank'] or len(public_full[rank])!=acceptance['public_kv_per_rank']:
            raise ValueError('all-layer public material incomplete')
        keys=[key for key in models if key[0]==rank]
        if len(keys)!=acceptance['private_requests'] or len({k[1] for k in keys})!=len(keys):
            raise ValueError('private request coverage incomplete')
        rank_ids.append({k[1] for k in keys})
        for key in keys:
            if linear[key]!=public_linear[rank] or full[key]!=public_full[rank]:
                raise ValueError('private layer set differs from canonical material')
    if any(ids!=rank_ids[0] for ids in rank_ids):raise ValueError('TP ranks executed different requests')
    return {'scope':'hash-bound all-rank/all-layer compact mechanism coverage only',
            'requests':sorted(rank_ids[0]),'worker_pids':{str(r):next(iter(p)) for r,p in rank_pids.items()},
            'per_rank_linear_layers':48,'per_rank_full_layers':16,
            'skipped_body_rows':acceptance['skipped_body_rows'],
            'quality_or_numeric_equivalence_proven':False}
