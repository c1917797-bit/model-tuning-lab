"""CPU-only interval-union screen for retained profiler CSVs, not causal proof."""
import csv,hashlib,json,math
from collections import defaultdict
from decimal import Decimal,InvalidOperation
from pathlib import Path


def merged_intervals(intervals):
    result=[]
    for lo,hi in sorted(intervals):
        if not math.isfinite(lo) or not math.isfinite(hi) or hi<lo:
            raise ValueError("invalid timeline interval")
        if result and lo<=result[-1][1]:
            result[-1]=(result[-1][0],max(result[-1][1],hi))
        else:result.append((lo,hi))
    return result


def union_us(intervals):
    return sum(hi-lo for lo,hi in merged_intervals(intervals))


def kernel_timeline(path,*,max_rows=2000000):
    path=Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular retained CSV required")
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1048576),b""):digest.update(block)
    groups=defaultdict(list);all_intervals=[];noncomm=[];origin=None;count=0
    with path.open(newline="") as stream:
        reader=csv.DictReader(stream)
        if not {"Start Time(us)","Duration(us)","Name","Type"}<=set(reader.fieldnames or []):
            raise ValueError("exact profiler kernel columns required")
        for row in reader:
            count+=1
            if count>max_rows:raise ValueError("bounded CSV row limit")
            try:
                start=Decimal(row["Start Time(us)"].strip())
                if not start.is_finite():raise ValueError("nonfinite start")
                if origin is None:origin=start
                lo=float(start-origin);duration=float(row["Duration(us)"].strip())
            except (ValueError,InvalidOperation,TypeError) as exc:
                raise ValueError("invalid profiler kernel row "+str(count)) from exc
            if not math.isfinite(duration) or duration<0:
                raise ValueError("invalid kernel duration")
            interval=(lo,lo+duration);all_intervals.append(interval)
            name=row["Name"];kind=row["Type"]
            communication=any(x in (name+" "+kind).lower() for x in ("hccl","allreduce","all_reduce","allgather","all_gather","reducescatter","reduce_scatter"))
            groups[(kind,communication)].append(interval)
            if not communication:noncomm.append(interval)
    if not count:raise ValueError("empty kernel trace")
    merged=merged_intervals(all_intervals)
    envelope=merged[-1][1]-merged[0][0];busy=union_us(all_intervals)
    gaps=[merged[i+1][0]-merged[i][1] for i in range(len(merged)-1)]
    group_rows=[{"type":kind,"communication_name_match":comm,"calls":len(xs),
                 "summed_us":sum(hi-lo for lo,hi in xs),"union_us":union_us(xs)}
                for (kind,comm),xs in groups.items()]
    return {"path":str(path),"sha256":digest.hexdigest(),"kernel_rows":count,
            "absolute_origin_us":str(origin),"kernel_envelope_us":envelope,
            "all_kernel_union_us":busy,"uncovered_envelope_us":envelope-busy,
            "uncovered_fraction":(envelope-busy)/envelope if envelope else 0.,
            "communication_exclusive_us":busy-union_us(noncomm),
            "largest_uncovered_gaps_us":sorted(gaps,reverse=True)[:20],
            "types":sorted(group_rows,key=lambda x:x["union_us"],reverse=True)[:20],
            "limits":["Kernel union is not critical-path removable cost.",
                      "Gaps may include CPU/compile/driver/synchronization/instrumentation or incomplete capture; no root cause from gaps alone.",
                      "Communication name matching is a screening classifier, not collective ownership/causality.",
                      "Never sum ranks or group unions; overlapping work counted once only in all_kernel_union_us.",
                      "Profiled64-token timing is not formal1024 service performance."]}


if __name__=="__main__":
    import sys
    print(json.dumps([kernel_timeline(path) for path in sys.argv[1:]]))
