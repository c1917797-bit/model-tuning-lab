"""Exact inverse codec taps; caller must bind complete source in a legal window."""
from pathlib import Path
import hashlib

HERE = Path(__file__).resolve().parent


def need(v, s):
    if not v:
        raise ValueError(s)


def once(s, old, new):
    need(s.count(old) == 1, 'exact one capture-codec seam: ' + old[:90])
    return s.replace(old, new, 1)


def ref(path):
    raw = Path(path).read_bytes()
    return dict(path=str(Path(path).resolve()), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def adapt(files):
    out = dict(files)
    need('state_capture_codec.py' not in out, 'codec not applied twice')
    inverse = {}
    for name in ('fastpath_numeric_observer.py', 'fastpath_numeric_sink.py', 'service_runner.py'):
        need(type(out.get(name)) is str, 'actual source before codec: ' + name)
        inverse[name] = out[name]
    s = out['fastpath_numeric_observer.py']
    s = once(s, 'import os\n', 'import os\nimport state_capture_codec as SC\n')
    marker = '        self.receipts=[];self.used=0'
    s = once(s, marker, marker + "\n        SC.enabled(self)\n        SC.require_runtime_admission(self.C,self.m)")
    s = once(s, 'row.update(self._capture(dict(state=state,keys=k,',
             'row.update(self._capture(dict(state=SC.canonical_input(self,b,state),keys=k,')
    marker = '    def publication(self,bridge,proposal,result):'
    s = once(s, marker, '    def before_publication(self,proposal):\n        return SC.before_publication(self,proposal)\n\n' + marker)
    s = once(s, '        after=self._snapshot(bridge,proposal[\'owner\']);applied=[]',
        "        after=self._snapshot(bridge,proposal['owner']);applied=[]\n        encoded_proposal=SC.encode_publication(self,proposal,after)")
    s = once(s, '            applied.append(self._capture(actual))',
        '            applied.append(self._capture(SC.observed(self,row,actual,after)))')
    s = once(s, 'after_GDN=after[0],after_FA=after[1],staged=self._capture(proposal),',
        'after_GDN=after[0],after_FA=after[1],staged=self._capture(encoded_proposal),')
    s = once(s, '        proof=self.sink(f)', '        SC.finish(self,f)\n        proof=self.sink(f)')
    # Preserve a bounded first-error pair before every actual clone/snapshot.
    s = once(s, "self.used+count<=384*2**20,'qualification clone budget before allocation'",
        "self.used+count+2*SC.STATE_BYTES<=384*2**20,'qualification clone plus first-failure pair before allocation'")
    s = once(s, "self.used+count<=384*2**20,'actual snapshot budget before native clone'",
        "self.used+count+2*SC.STATE_BYTES<=384*2**20,'actual snapshot plus first-failure pair before native clone'")
    out['fastpath_numeric_observer.py'] = s
    s = out['fastpath_numeric_sink.py']
    s = once(s, 'import json\n', 'import json\nimport state_capture_codec as SC\n')
    # Original independent reader executes on decoded complete tensors, unchanged.
    marker = "    report=N.consume_frame(t,C,m,source,saved['payload'],previous=previous)"
    s = once(s, marker, """    C.need(C.ref(SC.__file__)==m['files']['state_capture_codec.py'],
           'source-owned full-state codec before CPU restoration')
    _,state_digest=N.actual_cpu_digest(C,m)
    decoded=SC.decode(t,saved['payload'],digest=state_digest,expected_source=source,rank=c['rank'])
    report=N.consume_frame(t,C,m,source,decoded,previous=previous)""")
    s = once(s, "    current=saved['payload']", "    current=decoded")
    s += """\n\ndef state_partial_failure(observer,error):
    c=_CONTEXT
    if c is None:raise ValueError('failure evidence requires actual configured host receipt leaf')
    import diagnostic_export as X
    c['C'].need(c['C'].ref(SC.__file__)==c['m']['files']['state_capture_codec.py']and
                c['C'].ref(X.__file__)==c['m']['files']['diagnostic_export.py'],
                'source-owned bounded partial-failure exporter')
    return SC.partial_failure(c,observer,error,X)
"""
    out['fastpath_numeric_sink.py'] = s
    s = out['service_runner.py']
    marker = "        proposal['decision'] = decision\n        publication = transaction.publish("
    s = once(s, marker, """        proposal['decision'] = decision
        state_codec_qualifier=getattr(state.bridge,'fastpath_numeric_observer',None)
        if state_codec_qualifier is not None:
            state_codec_qualifier.before_publication(proposal)
        publication = transaction.publish(""")
    out['service_runner.py'] = s
    out['state_capture_codec.py'] = (HERE / 'state_capture_codec.py').read_text()
    for name, source in out.items():
        compile(source, name, 'exec')
    inverse['added'] = ['state_capture_codec.py']
    return out, inverse


def undo(files, inverse):
    result = dict(files)
    need(inverse['added'] == ['state_capture_codec.py'] and
         set(inverse) == {'fastpath_numeric_observer.py', 'fastpath_numeric_sink.py',
                          'service_runner.py', 'added'}, 'exact codec inverse readset')
    del result['state_capture_codec.py']
    for name in ('fastpath_numeric_observer.py', 'fastpath_numeric_sink.py', 'service_runner.py'):
        result[name] = inverse[name]
    return result


if __name__ == '__main__':
    import json
    import sys
    need(not sys.argv[1:], 'library-only source renderer; complete composition remains pending')
    print(json.dumps(dict(enabled=False, runtime_admitted=False, source_bound=False, NPU=False)))
