# HYPIC native-plugin delivery identity and reuse

As of2026-10-12 UTC, this is an identity/feasibility audit, NOT a completed
runtime delivery MANIFEST or a new NPU acceptance. Keep the existing supported
vLLM general-plugin route; do not replace it with sitecustomize merely to fit
the generic template validator.

## Fresh source and retained live identity

exec00c7: clean source checkout
/cache/cch/hypic_vllm_ascend-hotproof-20261008 at
4429e35177979c874bf053ab29789e4773f39b22, package0.8.5.
pyproject declares vllm.general_plugins:
hypic_vllm_ascend = hypic_vllm_ascend:register.

exec00cc recomputed all32 package Python files with the original attestation
algorithm (sorted relative path, NUL, bytes, NUL):
a5ebed77cc4ae0035e2634b81dc0606d8e37cc9d32f8894b984325bec1056692.
Both r19 LongBench arms' stored container attestations exactly match.
This is current-host-to-retained-container source consistency, not proof of
identity with the colleague's older environment or a currently running service.

- pyproject SHA256:67470f68a303d5292289f5bdee508cece00b2f8e3ea5d87fb81ee8b68f43cfbb
- __init__.py SHA256:84cfc3a61ac52aec9c40f6272fbab3768d728b7e0f94225c50b40ff3857f4fd8
- envs.py SHA256:0f4a5abcfed256493f453cbd9eaeca6e65012ef2667c9cf10220e012711b22dd

The retained r19 launch copied the read-only source into /opt/hypic, installed
it editable with no dependencies, then used vllm serve. This already employs
the native plugin entry point. No new image, framework edit or runtime rewrite
is needed just to rediscover registration.

## Bounded real entrypoint dispatch check

exec00cd ran actual register/get_config bytes in host Python3.11. Bootstrap,
logging and evidence sinks were mocked so no vLLM/NPU patch ran:
unset and0 dispatched zero times;1 dispatched once; invalid raised ValueError.
This proves only the actual entrypoint/config dispatch behavior, not that
apply_patches installed all hooks or that any worker/device activated.

Reproduce in an isolated CPU interpreter, not inside a live service:

```python
import sys,os,types,json
from unittest.mock import Mock,patch
from pathlib import Path
source=Path('/cache/cch/hypic_vllm_ascend-hotproof-20261008')
sys.path.insert(0,str(source))
import hypic_vllm_ascend as plugin
assert Path(plugin.__file__).resolve()==source/'hypic_vllm_ascend/__init__.py'
results=[]
for value in [None,'0','1','invalid']:
 stub=types.ModuleType('hypic_vllm_ascend.patches.bootstrap')
 stub.apply_patches=Mock()
 env={} if value is None else {'VLLM_ASCEND_HYPIC_ENABLE':value}
 with patch.dict(os.environ,env,clear=True), patch.dict(sys.modules,{'hypic_vllm_ascend.patches.bootstrap':stub}), patch.object(plugin,'configure_package_logging'), patch.object(plugin,'emit_evidence') as emit:
  if value=='invalid':
   try: plugin.register()
   except ValueError: pass
   else: raise AssertionError('invalid enable value accepted')
   assert not stub.apply_patches.called
   results.append({'switch':value,'rejected':True})
  else:
   plugin.register()
   expected=1 if value=='1' else 0
   assert stub.apply_patches.call_count==expected
   assert emit.call_count==expected
   results.append({'switch':value,'bootstrap_dispatches':expected})
print(json.dumps({'scope':'real register/config source; bootstrap is mocked, no vLLM/NPU activation proof','cases':results}))
```

## Minimal next route and genuine gaps

Exact-main Runtime Monkeypatch Delivery says to prefer a supported hook when
it expresses the treatment. Retain this native registration and existing
VLLM_ASCEND_HYPIC_ENABLE switch. Do not add another active patch/observer.

The branch static validator currently requires sitecustomize.py and
run_with_patch.sh. That template-specific schema is not proof native plugins
are forbidden, nor permission to declare a native package statically valid.
A native delivery profile would need a reviewed schema and binding of the
entrypoint declaration, complete source, launch receipt and disabled switch.
No profile was implemented or acceptance claimed in this audit.

Historical r19 receipts do not provide the complete explicit framework/CANN
version fields required by the delivery manifest. Do not fill them with guessed
labels or infer old host-driver state from today's host. Existing manifest
files in this workstream belong to diagnostic observer packages only.

Technique-level disable/uninstall/restart rollback remains missing. Negative
quality and same-source missing performance remain unchanged. No old suite is
restarted to attach a manifest after the fact. Future performance still needs
the pending prospective choice; no launch follows from this audit.
Counts8 bounded verified/21 partial, no main/remote integration.
