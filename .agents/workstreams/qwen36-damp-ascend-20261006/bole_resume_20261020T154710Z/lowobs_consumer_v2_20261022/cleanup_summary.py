"""Read the producer's exact path/SHA cleanup summary without weakening Ref3.

This stdlib helper only reads an already completed cleanup JSON file.  It does
not import the model, start an owner, or change any cleanup/state predicate.
"""
import hashlib
import json
import os
import stat
from pathlib import Path


CAP = 2**22


def _need(value, message):
    if not value:
        raise ValueError(message)


def _file_identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_uid, value.st_gid, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def _parents_identity(path):
    identities = []
    for parent in path.parents:
        value = parent.lstat()
        _need(stat.S_ISDIR(value.st_mode) and not stat.S_ISLNK(value.st_mode),
              'cleanup evidence ancestors must be ordinary directories')
        identities.append((str(parent), value.st_dev, value.st_ino,
                           value.st_mode))
    return tuple(identities)


def read_cleanup_summary(summary, expected_path):
    """Return (derived Ref3, JSON) from one bounded, whole, verified read.

    The producer supplied no byte count.  The returned byte count is newly
    observed metadata; it is never inserted into the original producer report.
    Only the documented two-key summary format is accepted here.  Full Ref3
    consumers elsewhere remain unchanged.
    """
    _need(type(summary) is dict and set(summary) == {'path', 'sha256'},
          'exact cleanup summary shape: path and sha256')
    _need(type(summary['path']) is str and type(summary['sha256']) is str,
          'cleanup summary path and SHA must be strings')
    digest = summary['sha256']
    _need(len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
          'cleanup summary SHA must be lowercase SHA256')
    _need(isinstance(expected_path, (str, Path)), 'explicit expected cleanup path')
    expected = Path(expected_path)
    path = Path(summary['path'])
    _need(expected.is_absolute() and path.is_absolute()
          and '..' not in expected.parts and '..' not in path.parts
          and '\x00' not in summary['path']
          and summary['path'] == str(path) == str(expected),
          'exact absolute expected cleanup path')

    parents_before = _parents_identity(path)
    before = path.lstat()
    _need(stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
          'cleanup evidence must be an ordinary regular file')
    _need(0 <= before.st_size <= CAP, 'bounded complete cleanup evidence')

    # O_NOFOLLOW closes the final-component symlink race.  O_NONBLOCK prevents
    # a concurrently substituted non-regular file from blocking this reader.
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    descriptor = os.open(str(path), flags)
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        _need(stat.S_ISREG(opened.st_mode)
              and _file_identity(opened) == _file_identity(before),
              'cleanup evidence changed before read')
        data = stream.read(CAP + 1)
        after = os.fstat(stream.fileno())
        _need(len(data) <= CAP and len(data) == opened.st_size,
              'bounded complete cleanup evidence')
        _need(_file_identity(after) == _file_identity(opened),
              'cleanup evidence changed during read')

    final = path.lstat()
    _need(stat.S_ISREG(final.st_mode)
          and _file_identity(final) == _file_identity(before)
          and _parents_identity(path) == parents_before,
          'cleanup evidence path changed during read')
    actual_sha = hashlib.sha256(data).hexdigest()
    _need(actual_sha == digest, 'exact whole cleanup evidence SHA256')
    # Parse the same bytes whose whole-file SHA was checked above; do not reopen.
    value = json.loads(data)
    return dict(path=str(path), bytes=len(data), sha256=actual_sha), value
