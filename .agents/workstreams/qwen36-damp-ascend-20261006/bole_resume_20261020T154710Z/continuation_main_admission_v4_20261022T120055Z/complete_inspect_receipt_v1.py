"""Lossless bounded command-receipt encoding; no host/device operations."""
import base64
import copy
import hashlib
import json
import zlib

MAX_RAW = 8 * 2**20  # Existing read-only CLI's whole-output cap, not increased.
MAX_COMPRESSED = MAX_RAW + 65536  # Encoding overhead only; raw bound remains8MiB.
SCHEMA = 'bole.complete-command-stdout-zlib/v1'


def need(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def unpack(envelope):
    need(type(envelope) is dict and set(envelope) == {
        'schema', 'codec', 'stdout_utf8_bytes', 'stdout_sha256', 'compressed_bytes',
        'compressed_sha256', 'data', 'metadata', 'receipt_canonical_utf8_bytes',
        'receipt_canonical_sha256'}, 'one complete exact receipt envelope')
    need(envelope['schema'] == SCHEMA and envelope['codec'] == 'zlib+base64', 'exact lossless codec')
    size, packed_size = envelope['stdout_utf8_bytes'], envelope['compressed_bytes']
    need(type(size) is int and 0 <= size <= MAX_RAW and type(packed_size) is int and
         0 < packed_size <= MAX_COMPRESSED, 'original raw bound and finite encoding overhead')
    encoded = envelope['data']
    need(type(encoded) is str and encoded.isascii() and
         len(encoded) <= 4*((MAX_COMPRESSED+2)//3), 'bounded complete ASCII base64')
    packed = base64.b64decode(encoded, validate=True)
    need(base64.b64encode(packed).decode('ascii') == encoded and
         len(packed) == packed_size and sha(packed) == envelope['compressed_sha256'],
         'canonical base64 and entire compressed bytes/SHA')
    inflater = zlib.decompressobj()
    raw = inflater.decompress(packed, size+1)
    need(len(raw) == size and inflater.eof is True and inflater.unused_data == b'' and
         inflater.unconsumed_tail == b'' and sha(raw) == envelope['stdout_sha256'],
         'complete exact bounded original bytes; no trailing/concatenated/incomplete stream')
    stdout = raw.decode('utf8', 'strict')
    metadata = envelope['metadata']
    need(type(metadata) is dict and 'stdout' not in metadata,
         'all other original receipt fields retained without duplicate stdout')
    receipt = copy.deepcopy(metadata)
    receipt['stdout'] = stdout
    full = canonical(receipt)
    need(len(full) == envelope['receipt_canonical_utf8_bytes'] and
         sha(full) == envelope['receipt_canonical_sha256'],
         'whole original receipt canonical bytes/SHA including every metadata field')
    return receipt


def pack(receipt):
    need(type(receipt) is dict and type(receipt.get('stdout')) is str,
         'complete original command receipt with decoded UTF8 stdout')
    # The frozen CLI reader uses decode(errors=replace). Refuse any ambiguous
    # replacement character rather than claim a lossy reconstruction is exact.
    need('\ufffd' not in receipt['stdout'], 'no potentially lossy UTF8 replacement in raw Docker JSON')
    raw = receipt['stdout'].encode('utf8', 'strict')
    need(len(raw) <= MAX_RAW, 'unchanged original CLI output bound')
    packed = zlib.compress(raw, level=6)
    full = canonical(receipt)
    envelope = dict(schema=SCHEMA, codec='zlib+base64', stdout_utf8_bytes=len(raw),
        stdout_sha256=sha(raw), compressed_bytes=len(packed), compressed_sha256=sha(packed),
        data=base64.b64encode(packed).decode('ascii'),
        metadata=copy.deepcopy({key: value for key, value in receipt.items() if key != 'stdout'}),
        receipt_canonical_utf8_bytes=len(full), receipt_canonical_sha256=sha(full))
    need(canonical(unpack(envelope)) == full, 'every original command-receipt byte value roundtrips before publication')
    return envelope
