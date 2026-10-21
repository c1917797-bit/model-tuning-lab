"""Exact-source staged software gate; one original MAIN deadline, default OFF."""
import argparse,json,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))


def main():
 entry=time.monotonic()
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--source-audit',action='store_true');p.add_argument('--software',action='store_true')
 for name in('phase-entry','lane-start','lane-deadline'):p.add_argument('--'+name,type=float)
 a=p.parse_args()
 if not(a.source_audit or a.software):print('{"enabled":false,"NPU":false}');return 0
 import sourceio as C
 sr=C.ref(P/'SOURCE_BOUND.json')
 if a.source_audit:
  import g3_validate as V
  print(json.dumps(V.validate(sr)));return 0
 from g3_software_stages import run
 print(json.dumps(run(sr,phase_entry=a.phase_entry,lane_start=a.lane_start,lane_deadline=a.lane_deadline,guest_entry=entry)));return 0


if __name__=='__main__':raise SystemExit(main())
