"""Source-only long qualification helpers. No authority, worker, or PASS producer."""
import hashlib
import json
import os
from pathlib import Path
import zlib

RAW_CAP=2**30
METADATA_CAP=64*2**20
STATE_CAP=10*2**20
LOGICAL_CAP=384*2**20
CHECKPOINT_CAP=128*2**20
REPORT_DECODE_CAP=256*2**10
REPORT_WIRE_CAP=20*2**10
RELEASE_CAP=1536
COMPACT_STATE_CAP=2048
ENVELOPE_CAP=1536


def need(value,why):
    if not value:raise ValueError(why)


def canonical(value):
    return (json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()


def frame_domain(output):
    need(type(output)is int and output in(160,1024),'explicit downstream output domain')
    return dict(output=output,generations=2,maximum_per_request=output-1,
                minimum_per_request=output//2,maximum_total=2*(output-1),
                maximum_current_length=131+output-2,
                # Original capacity reserves THREE private scheduled rows;
                # BOLE accepted tree paths contain at most TWO tokens.
                maximum_allocated_pages=(131+output-2+3+127)//128,
                maximum_committed_path_pages=(131+output-2+2+127)//128)


def encode_report(report):
    """Only compress an ALREADY independently consumed full report, losslessly."""
    data=canonical(report)
    need(len(data)<=REPORT_DECODE_CAP,'original full JSON report cap unchanged')
    wire=zlib.compress(data,9)
    need(len(wire)<=REPORT_WIRE_CAP,'new fixed suballocation, never enlarge original metadata budget')
    return wire,dict(codec='zlib-canonical-JSON/v1',wire_bytes=len(wire),
        wire_sha256=hashlib.sha256(wire).hexdigest(),decoded_bytes=len(data),
        decoded_sha256=hashlib.sha256(data).hexdigest())


def decode_report(wire,identity):
    need(type(identity)is dict and set(identity)=={'codec','wire_bytes','wire_sha256','decoded_bytes','decoded_sha256'}and
         type(identity['wire_bytes'])is int and 0<identity['wire_bytes']<=REPORT_WIRE_CAP and
         type(identity['codec'])is str and
         all(type(identity[k])is str and len(identity[k])==64 and
             all(c in '0123456789abcdef'for c in identity[k])for k in('wire_sha256','decoded_sha256')),
         'exact typed codec identity, no bool-as-int/extra fields')
    need(type(wire)is bytes and len(wire)==identity['wire_bytes']<=REPORT_WIRE_CAP and
         hashlib.sha256(wire).hexdigest()==identity['wire_sha256']and
         identity['codec']=='zlib-canonical-JSON/v1','complete exact compressed report identity')
    need(type(identity['decoded_bytes'])is int and 0<identity['decoded_bytes']<=REPORT_DECODE_CAP,
         'bounded decoded full report size before allocation')
    decoder=zlib.decompressobj()
    data=decoder.decompress(wire,REPORT_DECODE_CAP+1)
    need(len(data)<=REPORT_DECODE_CAP and decoder.eof and not decoder.unconsumed_tail and
         not decoder.unused_data,'one complete bounded stream, no trailing member or bomb')
    need(len(data)==identity['decoded_bytes']and hashlib.sha256(data).hexdigest()==identity['decoded_sha256'],
         'lossless complete decoded report identity')
    value=json.loads(data)
    need(canonical(value)==data,'canonical full report, no duplicate-key/NaN/trailing ambiguity')
    return value


def metadata_reservation(output,fixed_bytes):
    """One SHARED64MiB ledger: full compressed report+release+compact STATE."""
    d=frame_domain(output)
    need(type(fixed_bytes)is int and fixed_bytes>=0,'actual audited fixed evidence reservation')
    frames=d['maximum_total']+1 # reserve one additional failed/partial-frame record
    event=frames*(REPORT_WIRE_CAP+RELEASE_CAP+COMPACT_STATE_CAP+ENVELOPE_CAP)+4*256*2**10
    state=4*frames*COMPACT_STATE_CAP+16*256*2**10 # reader is ALL4 ranks, BEGIN/RETIRE separately
    need(state<=STATE_CAP,'original STATE10MiB cap unchanged')
    need(event+fixed_bytes<=METADATA_CAP,'combined all-leaf64MiB cap unchanged')
    return dict(frames=frames,event_reserved_bytes=event,state_reserved_bytes=state,
        fixed_reserved_bytes=fixed_bytes,total_reserved_bytes=event+fixed_bytes,
        maximum_fixed_bytes=METADATA_CAP-event,execution_ready=False)


def reservation160():
    # Preserve all V7 fixed buckets, including8MiB projection reservation,
    # and conservatively ALSO charge the old FRAME/ACK/REPORT/RELEASE stream.
    fixed=(16+8+3+16+8)*2**20
    original_events=(2048+3072+4000+1536)*325 #318frames+2*(open/retire/close)+failure
    value=metadata_reservation(160,fixed+original_events)
    value.update(original_fixed_bytes=fixed,original_event_reserved_bytes=original_events,
                 all_rank_STATE_cap=STATE_CAP,per_rank_metadata_cap=METADATA_CAP)
    return value


def raw_reservation(retained_first_wire,current_logical,current_wire,checkpoint_bytes,metadata_bytes):
    """Charge retainedG1-O0, current complete FAILED raw and CPU copies together."""
    vals=(retained_first_wire,current_logical,current_wire,checkpoint_bytes,metadata_bytes)
    need(all(type(x)is int and x>=0 for x in vals),'actual nonnegative byte counters')
    need(current_logical<=LOGICAL_CAP and checkpoint_bytes<=CHECKPOINT_CAP and
         metadata_bytes<=METADATA_CAP,'original subcaps unchanged')
    # Two logical copies is intentionally conservative, matching the original
    # short sink. Wire must be independently bounded before exporting a frame.
    total=retained_first_wire+2*current_logical+current_wire+checkpoint_bytes+metadata_bytes
    need(total<=RAW_CAP,'first+failed/current wire+copies+checkpoint+JSON <= original1GiB')
    return total


def page_transition(previous,current,previous_owner,current_owner,next_length,next_version,*,equal_page):
    """Compare by ACTUAL physical page, not whole request-table tensor shape.

    This helper does not certify a newly allocated page's pre-allocation bytes.
    Existing per-frame whole-page before/after checks must remain in place.
    Reordering/removal/reuse is rejected: no silent assumption about migration.
    """
    need(previous_owner['request']==current_owner['request']and
         previous_owner['generation']==current_owner['generation']and
         current_owner['length']==next_length and current_owner['version']==next_version,
         'same live request/generation and actual native frame continuity')
    old=list(previous['physical_pages']);new=list(current['physical_pages'])
    need(old and len(set(old))==len(old)and len(set(new))==len(new)and
         all(type(p)is int and p>=0 for p in old+new),'unique typed physical pages')
    need(previous['layer']==current['layer']and len(new)>=len(old)and new[:len(old)]==old,
         'original owned prefix pages retained in order; migration/reuse unproven')
    a,b=previous['ownership'],current['ownership']
    for key in('schema','request','logical_owner_slot','generation','cache_identities',
               'blocks_per_phys_block','kernel_block_size','physical_block_size',
               'use_hybrid_blocks','pcp_world_size','dcp_world_size'):
        need(a[key]==b[key]and type(a[key])is type(b[key]),'same actual cross-frame FA storage/geometry '+key)
    for kind in('key','value'):
        need(len(previous[kind])==len(old)and len(current[kind])==len(new),'page-axis ABI')
        for old_index,page in enumerate(old):
            equal_page(current[kind][new.index(page)],previous[kind][old_index],
                       'same physical owned page preserves previous committed postimage')
    return dict(existing_pages_verified=old,newly_owned_pages=new[len(old):],
        newly_owned_page_initialization_proven=False,outside_table_arena_proven=False,
        numerical_qualified=False)


def compact_rows_reference(report,wire_ref,codec):
    """Lossless reference, not a replacement numerical assertion or fake ACK."""
    rows=report['selected_write_digests']
    need(len(rows)==128 and len({(r['layer'],r['kind'])for r in rows})==128,
         'all128 actual permanent-write rows, not sampled summaries')
    need(set(wire_ref)=={'path','bytes','sha256'}and type(wire_ref['path'])is str and
         type(wire_ref['bytes'])is int and type(wire_ref['sha256'])is str and wire_ref['bytes']==codec['wire_bytes']and
         wire_ref['sha256']==codec['wire_sha256'],'actual durable full-report Ref joins codec')
    return dict(schema='bole.lossless-state-rows-reference/v1',source=report['source'],
        rank=report['rank'],generation=report['generation'],ordinal=report['ordinal'],
        report=wire_ref,codec=codec,rows_sha256=hashlib.sha256(canonical(rows)).hexdigest())


def resolve_rows(reference,expected,*,read_exact_ref):
    need(type(reference)is dict and set(reference)=={'schema','source','rank','generation','ordinal',
         'report','codec','rows_sha256'}and reference['schema']=='bole.lossless-state-rows-reference/v1',
         'one complete typed lossless STATE rows reference')
    need(type(reference['rank'])is int and 0<=reference['rank']<4 and
         type(reference['generation'])is int and reference['generation']in(1,2)and
         type(reference['ordinal'])is int and 0<=reference['ordinal']<1023,
         'typed bounded actual rank/generation/ordinal')
    for k in('source','rank','generation','ordinal'):
        need(reference[k]==expected[k]and type(reference[k])is type(expected[k]),'same actual STATE '+k)
    wr,codec=reference['report'],reference['codec']
    need(type(wr)is dict and set(wr)=={'path','bytes','sha256'}and type(wr['path'])is str and
         type(wr['bytes'])is int and type(wr['sha256'])is str and
         wr['bytes']==codec['wire_bytes']and wr['sha256']==codec['wire_sha256'],
         'complete actual wire Ref and codec identity agree before exact read')
    report=decode_report(read_exact_ref(reference['report']),reference['codec'])
    need(report['schema']=='bole.actual-fastpath-numeric-frame-ack/v1'and
         all(report[k]==expected[k]and type(report[k])is type(expected[k])for k in('source','rank','generation','ordinal')),
         'same exact decoded full independent report, not another frame/source')
    need(all(report[k]is False for k in('domain_complete','numerical_qualified','whole_model_pass','formal_performance'))and
         all(report[k]is True for k in('outside_table_FA_arena_pending','TP_raw_collective_receipts_pending',
                                      'HTTP_retirement_join_pending')),
         'all original incomplete-evidence flags retained, never promoted by transport')
    rows=report['selected_write_digests']
    expected_dest={(i,k)for i in range(64)for k in(('key','value')if i%4==3 else('state','conv'))}
    need(len(rows)==128 and {(r['layer'],r['kind'])for r in rows}==expected_dest and
         hashlib.sha256(canonical(rows)).hexdigest()==reference['rows_sha256'],
         'unchanged complete128 rows consumed by ORIGINAL state validator next')
    for row in rows:
        need(type(row['layer'])is int and type(row['kind'])is str and
             set(row)==({'layer','kind','before','after'}if row['kind']in('state','conv')else{'layer','kind','after'}),
             'exact typed complete state-row fields')
        for key in('before','after')if row['kind']in('state','conv')else('after',):
            d=row[key]
            need(type(d)is dict and set(d)=={'dtype','shape','bytes','sha256','finite'}and
                 type(d['dtype'])is str and d['dtype']in('torch.float32','torch.bfloat16')and
                 type(d['shape'])is list and d['shape']and all(type(n)is int and n>0 for n in d['shape'])and
                 type(d['bytes'])is int and d['bytes']>0 and d['finite']is True and
                 type(d['sha256'])is str and len(d['sha256'])==64 and
                 all(c in '0123456789abcdef'for c in d['sha256']),
                 'full typed digest ABI retained before original consumer checks')
    return rows,report # full metrics and all original flags remain present


def read_report(C,reference):
    envelope=C.obj(reference)
    need(type(envelope)is dict and set(envelope)=={'schema','source','rank','generation','ordinal','wire','codec'}and
         envelope['schema']=='bole.lossless-independent-full-report/v1',
         'actual complete lossless full-report envelope')
    need(reference['bytes']<=ENVELOPE_CAP,'original reserved envelope bytes')
    wr=envelope['wire'];codec=envelope['codec']
    need(type(wr)is dict and set(wr)=={'path','bytes','sha256'}and
         type(wr['path'])is str and type(wr['bytes'])is int and type(wr['sha256'])is str and
         wr['bytes']==codec['wire_bytes']and wr['sha256']==codec['wire_sha256'],
         'actual full report Ref joins complete codec identity')
    report=decode_report(C.checked(wr).read_bytes(),codec)
    for k in('source','rank','generation','ordinal'):
        need(type(report[k])is type(envelope[k])and report[k]==envelope[k],'full report/envelope '+k)
    return report,envelope


def store_report(context,root,stem,report,*,durable_json):
    """Exclusive full-wire+envelope; raw may only release AFTER this returns."""
    C=context['C'];wire,codec=encode_report(report)
    path=Path(root)/(stem+'.zjson')
    wr=dict(path=str(path),bytes=len(wire),sha256=hashlib.sha256(wire).hexdigest())
    envelope=dict(schema='bole.lossless-independent-full-report/v1',
        **{k:report[k]for k in('source','rank','generation','ordinal')},wire=wr,codec=codec)
    size=len(canonical(envelope))
    need(size<=ENVELOPE_CAP and context['metadata_bytes']+len(wire)+size<=METADATA_CAP and
         context['used']+context['metadata_bytes']+len(wire)+size<=RAW_CAP,
         'ALL complete compressed wire+envelope charged BEFORE exclusive create')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb')as stream:
        stream.write(wire);stream.flush();os.fsync(stream.fileno())
    need(C.ref(path)==wr,'actual complete wire exactly equals precharged Ref')
    context['metadata_bytes']+=len(wire)
    er=durable_json(Path(root)/(stem+'.json'),envelope)
    reopened,_=read_report(C,er)
    need(reopened==report,'actual durable complete report restored unchanged before raw release')
    return er
