"""Bounded current-process executable maps and exact ELF/hash inventory. No dlopen."""
import hashlib
import os
from pathlib import Path
import struct


def need(v,message):
    if not v:raise ValueError(message)


def elf(path):
    p=Path(path);size=p.stat().st_size
    with p.open('rb')as f:
        header=f.read(64)
        if not header.startswith(b'\x7fELF'):return dict(ELF=False,build_ids=[])
        need(len(header)==64 and header[4]==2 and header[5]in(1,2),'known ELF64 byte order')
        order='<'if header[5]==1 else'>'
        _,machine,_,_,phoff,shoff,_,_,phsize,phcount,shsize,shcount,_=struct.unpack(order+'HHIQQQIHHHHHH',header[16:])
        need(phcount<=4096 and shcount<=65535,'bounded ELF tables')
        ranges=set()
        for i in range(phcount):
            need(phsize>=56 and phoff+(i+1)*phsize<=size,'complete ELF program table')
            f.seek(phoff+i*phsize);entry=f.read(56);kind,_,offset,_,_,filesize,_,_=struct.unpack(order+'IIQQQQQQ',entry)
            if kind==4:ranges.add((offset,filesize))
        for i in range(shcount):
            need(shsize>=64 and shoff+(i+1)*shsize<=size,'complete ELF section table')
            f.seek(shoff+i*shsize);entry=f.read(64);_,kind,_,_,offset,filesize,_,_,_,_=struct.unpack(order+'IIQQQQIIQQ',entry)
            if kind==7:ranges.add((offset,filesize))
        ids=set()
        for offset,length in ranges:
            need(length<=2**20 and offset+length<=size,'bounded complete ELF notes')
            f.seek(offset);data=f.read(length);position=0
            while position+12<=len(data):
                names,desc,kind=struct.unpack_from(order+'III',data,position);position+=12
                need(names<=2**20 and desc<=2**20 and position+((names+3)//4)*4+((desc+3)//4)*4<=len(data),'complete bounded ELF note')
                name=data[position:position+names];position+=((names+3)//4)*4
                value=data[position:position+desc];position+=((desc+3)//4)*4
                if kind==3 and name.rstrip(b'\0')==b'GNU':ids.add(value.hex())
        return dict(ELF=True,machine=machine,build_ids=sorted(ids))


def fingerprint(path):
    p=Path(path)
    need(p.is_absolute()and p.is_file()and not any(v.is_symlink()for v in(p,*p.parents)),'ordinary canonical library file')
    before=p.stat();h=hashlib.sha256();n=0
    with p.open('rb')as f:
        while b:=f.read(2**20):h.update(b);n+=len(b)
    after=p.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)and
        n==after.st_size,'library stable during full streaming SHA')
    return dict(ref=dict(path=str(p),bytes=n,sha256=h.hexdigest()),ELF=elf(p),
        stat=dict(device=after.st_dev,inode=after.st_ino,size=after.st_size,mtime_ns=after.st_mtime_ns))


def executable_paths(text):
    need(type(text)is str and len(text.encode())<=4*2**20,'bounded full current-process maps')
    paths={}
    for row in text.splitlines():
        parts=row.split(maxsplit=5);need(len(parts)>=5,'complete Linux maps row')
        if 'x'not in parts[1]:continue
        need(len(parts)==6,'unbound anonymous executable mapping has no source/library identity')
        name=parts[5]
        if name in('[vdso]','[vsyscall]'):continue  # Explicit kernel-provided mappings, never a file/path-prefix exemption.
        need(not name.startswith('['),'unknown named executable mapping')
        need(name.startswith('/')and not name.endswith(' (deleted)')and '\\'not in name,'ordinary executable map path, no deleted/escaped image')
        canonical=Path(name).resolve(strict=True)
        need(canonical.is_file(),'executable file mapping is regular')
        s=canonical.stat();major,minor=parts[3].split(':')
        need(int(parts[4])==s.st_ino and(int(major,16),int(minor,16))==(os.major(s.st_dev),os.minor(s.st_dev)),
            'maps inode/device belongs to current exact backing file')
        key=str(canonical)
        paths.setdefault(key,[]).append(row)
    need(paths and len(paths)<=1024,'nonempty bounded executable-library catalog')
    return paths


def inventory():
    text=Path('/proc/self/maps').read_text();paths=executable_paths(text)
    return dict(maps=text,libraries={p:dict(fingerprint(p),map_rows=rows)for p,rows in paths.items()},host_pid=os.getpid())


def bind(libraries):
    """Join CPU/stopped-image content to this NPU process; inode is process-local.

    Docker overlay inode/device may differ between containers. Never treat a
    CPU process stat as the NPU process's file identity. Rehash every exact
    canonical path here, then retain this process's stat for per-call checks.
    """
    output={}
    for path,expected in libraries.items():
        actual=fingerprint(path)
        need(actual['ref']==expected['ref']and actual['ELF']==expected['ELF'],'exact CPU/stopped-image fullSHA/buildID join in this actual process: '+path)
        output[path]=actual
    return output


def check(text,allowed,*,rehash=False):
    """No basename/RPATH/prefix exceptions. Every mapped executable file is exact."""
    paths=executable_paths(text);observed={}
    for path,rows in paths.items():
        need(path in allowed,'unknown executable library before/after actual operator call: '+path)
        expected=allowed[path];p=Path(path);s=p.stat();stat=dict(device=s.st_dev,inode=s.st_ino,size=s.st_size,mtime_ns=s.st_mtime_ns)
        need(stat==expected['stat'],'library inode/size/mtime changed during replay: '+path)
        if rehash:
            actual=fingerprint(p);need(actual['ref']==expected['ref']and actual['ELF']==expected['ELF'],'library wholeSHA/buildID changed: '+path)
        observed[path]=dict(map_rows=rows,ref=expected['ref'],ELF=expected['ELF'],stat=stat)
    return observed
