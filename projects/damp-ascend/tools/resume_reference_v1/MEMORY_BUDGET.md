# Ordinary-RAM budget: accounted quantities, unclosed peak

This audit concerns the frozen FP32 TRAIN collector, not a DAMP speed claim.
It does not authorize freeing HugeTLB or external NPU0–3 work.

## Source and actual observations

- run_full_capture.py resources(): MemAvailable>=64GiB and diskfree>=40GiB
  before each arm.64 is a conservative constant, not derived from model
  host RSS or the capture dimensions.
- Original off.precheck.json:71,669,212KiB=68.349GiB ordinary available.
- Original off.log: checkpoint51.75GiB; EXT4 auto-prefetch disabled;
  weights12.8735GiB/rank are **NPU** memory, not host-private peak.
- Read-only MB02ca snapshot:63,797,700KiB=60.842GiB available;
  Hugetlb2,009,071,616KiB is reserved and cannot be treated as available.
-15 current weight shards, maximum3,995,081,848 bytes~3.721GiB.
  No conclusion that only one shard or four shards is resident is licensed
  by their sizes. Safetensors full-byte identity was not in original receipt.
- Old off receipt has no CPU RSS/cgroup high-water telemetry. The start/end
  delta cannot prove an upper bound; page cache and external tasks vary.

## Frozen collector live memory

timeline.py retains Timeline.finished for all completed rows; session.py
does not discard those timelines on slot retirement. Full dimensions yield:

- Per rank:36x48x6x256=2,654,208 row tuples.
- Across4 ranks:10,616,832 row tuples and127,401,984 float references.
- Assuming CPython float24B and tuple12=136B (to be queried in same image),
  object primitive accounting is4,501,536,768B=4.193GiB.
-1.5x planning allowance=6,752,305,152B=6.289GiB, **not a proven upper bound**
  on allocator, class/dict metadata or total model/runtime working set.
- RMS accumulators per rank48x12x128 FP64=589,824B; anchor temporaries
  and writer buffers are streaming. Runtime/IPC and model loading remain
  separate unknowns. Worker-process duplication cannot be guessed away.

## Disk is separate

36x48x6x4=41,472 anchor/future pairs:
anchor0.75MiB +future12KiB ->33,124,515,840B=30.850GiB payload.
JSON/events/logs/stat snapshots add overhead.40GiB disk admission is retained.
Do not add this entire disk payload as permanently resident RAM. Dirty-page
writeback and validator decoded-JSON peak are nonetheless additional runtime
quantities to observe.

## Admission disposition

Keep original64GiB ordinary admission in this prepared controller. With a
60.842GiB fresh snapshot it will still fail **before model load**, deliberately.
This is not refusal to repair; a no-evidence arbitrary32/48/60GiB knob would
just reproduce unsafe budget reasoning.

A lower-budget revision requires NEW evidence tying same image/frozen model
loader/samebatch/runtime to measured CPU-private/cgroup peak or a demonstrated
strict loading bound, then separately adds capture reserve and external host
reserve. It needs MAIN review and new receipt/source identity; it is not
available through the current command line. A memory cgroup cap can confine
a future attempt but alone does not prove the model will fit or make an OOM
a valid reference. No cache dropping, HugeTLB release or unrelated process
termination is proposed.

The prepared runtime monitor saves ordinary MemAvailable samples every5s.
The8GiB stop reserve only detects sustained observed pressure; it is not a
hard peak/cgroup guarantee and does not replace the unknown model peak.
MAIN should prioritize the already scheduled small-memory numerical seam
probe before committing the4-card several-hour reference capture.

