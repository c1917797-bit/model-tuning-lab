"""Qualification-only state witness adapter, never the timed FAST implementation."""
import short_state_digest as ORIGINAL


class Probe(ORIGINAL.Probe):
    def capture(self,bridge,frame,native_output):
        # Keep original BEGIN/RETIRE/calibration/HTTP consumer and exact STATE
        # schema. Replace only the diagnostic-array producer with the already
        # completed independent numeric capture of these real FAST writes.
        try:
            C=self.C;need=ORIGINAL.need
            C.need(C.ref(__file__)==self.m['files']['qualification_state_probe.py'],
                   'actual source-owned qualification state receipt adapter')
            need(not self.failed and self.active==frame.owner.request and
                 frame.owner.generation==self.generation and
                 frame.owner.version==self.last_version+1,'monotonic actual FAST frame')
            need(self.profile['observation']=='OFF'and bridge.collect_observation_only is False,
                 'actual FAST observer-policy OFF, not native AR')
            proposal,publication=frame.proposal,frame.publication
            need(proposal['owner']==frame.owner and publication['owner']==frame.owner and
                 proposal['published']is False and publication['cache_published']is True and
                 publication['actual_applied']==[]and publication['diagnostic_readback_performed']is False and
                 proposal['processed_nodes']==publication['processed_nodes'],
                 'actual FAST transaction, not reinstated diagnostic publication arrays')
            observer=bridge.fastpath_numeric_observer
            need(observer.current is None and observer.receipts,
                 'real numeric frame consumed synchronously before state receipt')
            ref=observer.receipts[-1];C.checked(ref);report=C.obj(ref)
            need(report['source']==self.source and report['rank']==self.rank and
                 report['generation']==self.generation and report['ordinal']==frame.owner.version and
                 report['frame_checks_passed']is True and
                 report['full128_actual_state_writes_verified']is True,
                 'exact current actual independent numeric report, not another frame')
            need(native_output['req_ids']==[self.active]and
                 native_output['sampled_token_ids']==[list(publication['emitted_tokens'])],
                 'real native returned token IDs join actual publication')
            if self.last_publication is not None:
                ack=frame.previous_native_ack
                need(ack['request']==self.active and ack['previous_version']==self.last_version and
                     ack['version']==frame.owner.version and ack['scheduler_committed']is True and
                     ack['computed_tokens']==self.last_publication['next_length']and
                     ack['next_root']==self.last_publication['emitted_tokens'][-1],
                     'original next-native ACK of previous successful publication')
            rows=report['selected_write_digests']
            need(len(rows)==128 and {(r['layer'],r['kind'])for r in rows}==ORIGINAL.DESTINATIONS,
                 'independently observed all128 full write values')
            for row in rows:
                for k in ('after','before')if row['kind']in('state','conv')else('after',):
                    d=row[k]
                    need(set(d)=={'dtype','shape','bytes','sha256','finite'}and d['finite']is True and
                         type(d['bytes'])is int and d['bytes']>0 and len(d['sha256'])==64,
                         'complete full-tensor numeric write digest, not sampled/PASS')
            key=(self.generation,frame.owner.version)
            need(0<=key[1]<7 and key not in self.frames,'one bounded current frame receipt')
            self.last_version=frame.owner.version;self.last_publication=publication
            self.frames.add(key)
            return self.emit('STEP',*key,dict(request=self.active,length=frame.owner.length,
                version=frame.owner.version,tokens=list(frame.tokens),
                actual_collect_observation_only=False,processed_nodes=list(proposal['processed_nodes']),
                emitted_tokens=list(publication['emitted_tokens']),
                rows=sorted(rows,key=lambda r:(r['layer'],r['kind']))))
        except BaseException:
            self.failed=True
            raise
