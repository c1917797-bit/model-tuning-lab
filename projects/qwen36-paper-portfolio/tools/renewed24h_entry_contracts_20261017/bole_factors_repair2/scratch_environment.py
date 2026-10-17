"""Private import/runtime scratch inside the existing sole stage RW mount."""
import os
from pathlib import Path
import stat

def need(v,s):
    if not v:raise ValueError(s)

def prepare(host_root,guest_root=None):
    root=Path(host_root);guest=Path(guest_root) if guest_root is not None else root
    need(root.is_absolute() and root.is_dir() and '..' not in root.parts and
         all(not p.is_symlink() for p in(root,*root.parents)),'exact existing ordinary sole RW stage root')
    need(guest.is_absolute() and '..' not in guest.parts,'exact declared guest destination')
    dev=root.stat().st_dev
    for name in('.tmp','.home'):
        p=root/name;need(not p.exists() and not p.is_symlink(),'exclusive private stage scratch/home')
        p.mkdir(mode=0o700);s=p.lstat()
        need(stat.S_ISDIR(s.st_mode) and s.st_dev==dev and s.st_nlink>=1,'same-filesystem ordinary scratch')
    tmp=str(guest/'.tmp')
    return dict(TMPDIR=tmp,TMP=tmp,TEMP=tmp,HOME=str(guest/'.home'))

def validate(root):
    root=Path(root);expected=dict(TMPDIR=str(root/'.tmp'),TMP=str(root/'.tmp'),TEMP=str(root/'.tmp'),HOME=str(root/'.home'))
    need(all(os.environ.get(k)==v for k,v in expected.items()),'actual exact sole-RW TMPDIR/HOME environment')
    for name in('.tmp','.home'):
        p=root/name
        need(p.is_dir() and '..' not in p.parts and all(not q.is_symlink() for q in(p,*p.parents)),'actual ordinary private import scratch')
    import tempfile
    need(Path(tempfile.gettempdir())==root/'.tmp','actual tempfile selection follows declared stage, no ambient fallback')
    with tempfile.NamedTemporaryFile(prefix='scratch-probe-',delete=False) as f:
        f.write(b'actual-scratch-write-read\0');f.flush();os.fsync(f.fileno());target=Path(f.name)
    need(target.parent==root/'.tmp' and target.read_bytes()==b'actual-scratch-write-read\0','actual exact-stage temporary write/read')
    # Retain the tiny probe as evidence; whole original output cap includes it.
    return dict(schema='bole.actual-private-scratch/v1',stage_root=str(root),environment=expected,
                actual_tempfile=str(target),sole_existing_RW_mount=True,extra_mounts_created=False)
