"""Default-OFF bounded post-inspect handoff; no tensor runtime imports."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

PYTHON = '/usr/local/python3.12.13/bin/python3'


def common(inputs_ref):
    def checked(r):
        p = Path(r['path']); b = p.read_bytes()
        if (not p.is_absolute() or any(x.is_symlink() for x in (p, *p.parents)) or
                len(b) != r['bytes'] or hashlib.sha256(b).hexdigest() != r['sha256']):
            raise ValueError('exact bootstrap source before imports')
        return p, b
    _, data = checked(inputs_ref); x = json.loads(data)
    p, _ = checked(x['files']['timing_owner_common.py'])
    s = importlib.util.spec_from_file_location('_bole_timing_owner_common', str(p))
    C = importlib.util.module_from_spec(s); s.loader.exec_module(C)
    return C, C.package(inputs_ref, __file__)


def main():
    p = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    p.add_argument('--execute', action='store_true'); p.add_argument('--inputs-ref'); p.add_argument('--root', type=Path)
    a = p.parse_args()
    if not a.execute:
        print(json.dumps(dict(enabled=False, NPU=False, tensor_runtime_imported=False, prepared_only=True))); return 0
    if not a.inputs_ref or a.root is None or os.environ.get('BOLE_GDN3_TIMING_ENABLE') != '1':
        p.error('explicit reviewed inputs and bounded MAIN handoff required')
    reference = json.loads(a.inputs_ref); C, x = common(reference)
    C.need(a.root.is_absolute() and a.root.is_dir() and not any(z.is_symlink() for z in (a.root, *a.root.parents)),
           'new ordinary MAIN-owned output leaf')
    # Independent successful replay/source checks happen before even waiting for admission.
    C.prior_chain(x, installed=True)
    pointer = a.root/'MANIFEST-REF.json'; until = time.monotonic()+C.HANDOFF
    while not pointer.exists():
        if time.monotonic() >= until:
            raise TimeoutError('finite MAIN actual-inspect/admission handoff absent')
        time.sleep(.1)
    manifest_ref = json.loads(pointer.read_bytes()); m = C.final_manifest(x, manifest_ref, current=True)
    C.need(Path(m['admission']['path']).parent == a.root and
           Path(manifest_ref['path']) == a.root/'MANIFEST.json', 'exact new output-scoped handoff')
    driver = C.checked(m['files']['time_gdn.py'])
    # Frozen CLI reruns the whole source/prior/current-admission gate before Torch;
    # only its already MAIN-admitted logical0 is initialized there.
    os.execv(PYTHON, [PYTHON, '-I', '-B', str(driver), '--execute',
                    '--manifest-ref', json.dumps(manifest_ref), '--output', str(a.root/'data')])


if __name__ == '__main__':
    raise SystemExit(main())
