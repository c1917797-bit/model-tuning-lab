"""Exact actual025 Ref2 -> strict sourceio Ref3 at the evidence boundary only."""
from pathlib import Path

def upgrade(C,original,expected_path):
 C.need(type(original)is dict and set(original)=={'path','sha256'},'exact actual025 Ref2, not arbitrary mapping')
 C.need(type(original['path'])is str and type(original['sha256'])is str,'actual025 Ref2 string fields')
 path=Path(expected_path)
 C.need(path.is_absolute()and original['path']==str(path),'original Ref2 matches the actual requested evidence path')
 current=C.ref(path) # stable pre/post inode/mtime/size + streamed full SHA.
 C.need(current['path']==original['path']and current['sha256']==original['sha256'],'original whole SHA unchanged during strict Ref3 conversion')
 C.checked(current) # exact three keys, full SHA/bytes and no symlink parent chain.
 return current

def file_ref(C,c,path):
 return upgrade(C,c.ref(path),path)
