"""Independent complete retained coverage/ACK/output chain, no tensor inputs."""
import sourceio as C
import g2_contract as G2


def audit(events,completed,requests):
    C.need(len(completed)==len(requests)==2,'two complete actual request summaries')
    cursor=0
    for generation,(summary,item)in enumerate(zip(completed,requests),1):
        rid=summary['request'];steps=item['steps'];stream=summary['output_token_ids'][:1];length=131
        C.need(summary['generation']==generation and item['request']==dict(request=rid,generation=generation,slot=0,length=131,version=0)and
            item['output_token_ids']==summary['output_token_ids']and 2<=len(steps)<=G2.MAX_OUTPUT-1,
            'exact generation/native owner/output count before coverage join')
        event=events[cursor];cursor+=1
        C.need(event['kind']=='open'and event['coverage']==dict(generation=generation,request=rid)and
            item['open_event']==event,'complete actual request open event')
        acknowledgements=[]
        for ordinal,step in enumerate(steps):
            event=events[cursor];cursor+=1;v=event['coverage'];emitted=step['emitted_tokens']
            owner=dict(request=rid,generation=generation,slot=0,length=length,version=ordinal)
            C.need(event['kind']=='step'and v['request']==rid and v['generation']==generation and
                v['ordinal']==ordinal and v['length']==length and v['emitted_tokens']==emitted and
                v['processed_nodes']in([0],[0,1],[0,2])and len(v['processed_nodes'])==len(emitted)and
                1<=len(emitted)<=min(2,G2.MAX_OUTPUT-len(stream))and step['owner']==owner and
                step['stream_event']==event,'every actual target frame in monotonic complete output coverage')
            stream+=emitted;length+=len(v['processed_nodes']);publication=step['publication']
            C.need(publication==dict(next_length=length,next_version=ordinal+1,emitted_tokens=emitted),
                'retained actual selected publication joins exact coverage and output stream')
            if ordinal<len(steps)-1:
                ack=dict(schema='bole.service-native-scheduler-ack/v1',request=rid,previous_version=ordinal,
                    version=ordinal+1,computed_tokens=length,next_root=emitted[-1],scheduler_committed=True,
                    whole_model_qualification=False,final_success=False)
                C.need(step['next_ack']==ack,'actual next CPU counter/root ACK joins preceding selected step')
                acknowledgements.append(ack)
            else:C.need(step['next_ack']is None,'final pending publication has actual retirement closure, no fabricated next forward')
        retirement=item['retirement'];event=events[cursor];cursor+=1
        C.need(stream==summary['output_token_ids']and len(stream)==G2.MAX_OUTPUT and
            summary['steps']==len(steps)and summary['processed_tokens']==G2.MAX_OUTPUT-1 and
            event['kind']=='retire'and event['coverage']==dict(generation=generation,request=rid,
                steps=len(steps),output_tokens=G2.MAX_OUTPUT)and item['retire_event']==event and
            retirement['schema']=='bole.service-owner-native-retirement/v1'and retirement['request']==rid and
            retirement['generation']==generation and retirement['steps']==len(steps)and
            retirement['next_counter_acknowledgements']==acknowledgements and
            retirement['final_ack_by_retirement_pending']is True and retirement['last_publication']==dict(
                owner=owner,next_length=length,next_version=len(steps),emitted_tokens=emitted),
            'complete output/actual counter/retirement chain with no omitted successful segment')
    C.need(cursor+1==len(events)and events[cursor]['kind']=='close'and
        events[cursor]['coverage']==dict(request_count=2,output_budget=G2.MAX_OUTPUT),
        'one final close after exactly all segments of both requests')
    return dict(request_count=2,complete_output_tokens=2*G2.MAX_OUTPUT,
        target_step_count=sum(len(v['steps'])for v in requests),all_coverage=True,
        final_pending_by_retirement=True)
