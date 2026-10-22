"""Source-bound saved collective operands; default import has no side effect."""
import hashlib
import json
import os
import sys
from pathlib import Path

CAP = 8 * 2**20
TENSOR_BYTES = 131 * 5120 * 2
STAGES = ('pre_reduce', 'post_reduce')
NAMES = tuple('G%d-%s.bin' % (g, s) for g in (1, 2) for s in STAGES)


def need(value, why):
    if not value:
        raise ValueError(why)


def retained_files(C, manifest, rank):
    root = Path(manifest['model_receipt_root']) / ('PROJECTION-R%d' % rank)
    if not root.exists():
        return set()
    need(root.is_dir() and not any(p.is_symlink() for p in (root, *root.parents)),
         'ordinary owned projection raw directory')
    files = set(root.iterdir())
    need(len(files) <= 4 and all(p.name in NAMES and p.is_file() and
         not p.is_symlink() and 0 <= p.stat().st_size <= TENSOR_BYTES for p in files),
         'every retained full or interrupted operand is accounted')
    return files


def validate_geometry(geometry, raw):
    need(type(geometry) is dict and geometry.get('shape') == [131, 5120] and
         geometry.get('dtype') == 'torch.bfloat16' and geometry.get('logical_bytes') == TENSOR_BYTES
         and type(raw) is bytes and len(raw) == TENSOR_BYTES and sys.byteorder == 'little',
         'complete actual131x5120 BF16 little endian bytes, never slice or proxy')


class Writer:
    def __init__(self, owner):
        C, m = owner.C, owner.manifest
        need(C.ref(__file__) == m['files']['projection_raw_v1.py'] and
             type(owner.rank) is int and owner.rank in range(4),
             'exact source-owned helper and actual worker rank')
        self.owner = owner
        self.root = Path(m['model_receipt_root']) / ('PROJECTION-R%d' % owner.rank)
        need(self.root.parent.is_dir() and not self.root.exists() and
             not any(p.is_symlink() for p in (self.root, *self.root.parents)),
             'fresh ordinary raw directory under actual receipt owner')
        self.root.mkdir(mode=0o700)
        self.written = {}
        self.failed = False
        self.bytes = 0

    def put(self, generation, stage, raw, geometry):
        try:
            validate_geometry(geometry, raw)
            need(not self.failed and type(generation) is int and generation in (1, 2) and
                 stage in STAGES and (generation, stage) not in self.written,
                 'one actual pre/post operand per bounded generation')
            before = self.owner.B.actual(self.owner.C, self.owner.manifest, self.owner.rank)
            need(before['charges']['projection_raw'] == self.bytes and
                 self.bytes + len(raw) <= CAP and
                 before['bytes'] + len(raw) + 8 * 2**20 <= self.owner.G.METADATA_CAP and
                 before['bytes'] + len(raw) + self.owner.G.FRAME_LOGICAL_CAP +
                 self.owner.G.FRAME_WIRE_CAP + self.owner.G.CHECKPOINT_CAP <= self.owner.G.RAW_CAP,
                 'prospective allocation inside original64MiB/1GiB aggregate caps')
            path = self.root / ('G%d-%s.bin' % (generation, stage))
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                need(stream.write(raw) == len(raw), 'complete exclusive full operand write')
                stream.flush()
                os.fsync(stream.fileno())
            reference = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            need(self.owner.C.ref(path) == reference, 'saved whole operand Ref equals actual bytes')
            self.written[generation, stage] = reference
            self.bytes += len(raw)
            after = self.owner.B.actual(self.owner.C, self.owner.manifest, self.owner.rank)
            need(after['charges']['projection_raw'] == self.bytes,
                 'actual ledger includes all saved operand bytes')
            return reference
        except BaseException:
            self.failed = True
            self.owner.failed = True
            raise

    def complete(self):
        need(not self.failed and set(self.written) == {(g, s) for g in (1, 2) for s in STAGES}
             and self.bytes == 4 * TENSOR_BYTES, 'all four complete original operands retained')
        files = retained_files(self.owner.C, self.owner.manifest, self.owner.rank)
        need(files == {Path(r['path']) for r in self.written.values()},
             'no hidden or missing retained operand')
        for reference in self.written.values():
            need(self.owner.C.ref(reference['path']) == reference, 'all raw Refs unchanged at retirement')
        return dict(bytes=self.bytes, references=list(self.written.values()),
                    numerical_qualified=False, formal_performance=False)
