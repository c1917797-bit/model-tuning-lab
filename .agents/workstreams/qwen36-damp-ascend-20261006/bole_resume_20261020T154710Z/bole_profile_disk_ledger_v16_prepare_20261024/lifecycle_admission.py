"""Exact prefill/active-frame and source-owned initial-length repairs; no numerical change."""
def need(v,s):
 if not v:raise ValueError(s)
def once(s,a,b):
 need(s.count(a)==1,'one exact lifecycle seam '+a[:70]);return s.replace(a,b,1)
METHOD=""" def validate_prefill(self,owner):
  need(owner is self.initial and self.frame is None and self.pending is None and
       self.steps==0 and self.version==0 and self.length==self.initial.length and
       not self.retired,
       'one strongly held initial-prefill phase, never an active or stale frame')
  self.check_request()
  need(len(self.bindings)==64 and tuple(b['index']for b in self.bindings)==tuple(range(64)),
       'all64 registered initial-prefill bindings')
  for binding in self.bindings:
   if binding['kind']=='gdn':
    slot=self.registrations.get(id(binding))
    need(slot is binding['slot_binding']and slot is not None,
         'same registered initial native GDN slot binding')
    slot.check(owner)
   else:
    need(binding['kind']=='fa','only registered actual hybrid layers')
    self.check_fa(binding)
  return True
"""
def adapt(files):
 out=dict(files)
 text=out['state_capture_codec.py'].decode()
 text=once(text,'    actual.identity(2048)',"""    length=actual.initial.length
    need(type(length)is int and length==m['performance_profile']['scope']['input_tokens']==actual.registration.length,
         'same typed source/initial Owner/native-registration prefill length')
    actual.identity(length)""")
 out['state_capture_codec.py']=text.encode()
 text=out['runtime_admission_2k.py'].decode()
 text=once(text,'        self.bridge._validate_bindings(self.initial)',
                  '        self.bridge._bole_live.validate_prefill(self.initial)')
 out['runtime_admission_2k.py']=text.encode()
 text=out['live_owner.py'].decode()
 text=once(text,' def validate(self,owner):',METHOD+' def validate(self,owner):')
 out['live_owner.py']=text.encode()
 changed={n:dict(before=files[n],after=out[n])for n in out if files[n]!=out[n]}
 need(set(changed)=={'state_capture_codec.py','runtime_admission_2k.py','live_owner.py'},'exact three lifecycle-only files')
 return out,changed
def inverse(files,delta):
 out=dict(files)
 for n,r in delta.items():
  need(out[n]==r['after'],'exact lifecycle inverse');out[n]=r['before']
 return out
