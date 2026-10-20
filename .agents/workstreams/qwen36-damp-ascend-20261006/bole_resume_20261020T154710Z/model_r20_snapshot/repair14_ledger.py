"""Verify exact current bytes and reverse only the declared R14 source delta."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
def digest(text):
 b=text.encode("utf8");return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def reverse(name,actual):
 ledger=json.loads((P/"FA_BOUNDARY_EDITS_R14.json").read_text())
 if name not in ledger:return actual
 row=ledger[name]
 if digest(actual)!={k:row["after"][k]for k in ("bytes","sha256")}:
  raise ValueError("current source differs from declared repair "+name)
 for edit in reversed(row["edits"]):
  if actual.count(edit["after"])!=1:raise ValueError("unambiguous inverse repair "+name)
  actual=actual.replace(edit["after"],edit["before"])
 if digest(actual)!={k:row["before"][k]for k in ("bytes","sha256")}:
  raise ValueError("repair does not recover exact predecessor "+name)
 return actual
def previous_text(path):
 path=Path(path)
 return reverse(str(path.relative_to(P)),path.read_text())
