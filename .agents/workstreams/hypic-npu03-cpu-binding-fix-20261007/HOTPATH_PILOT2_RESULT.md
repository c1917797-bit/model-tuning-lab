# Explicit-boundary quality pilot-2 — PASS (2026-10-08)

This is a protocol/activation pilot, **not** a 127-sample quality conclusion.
The first pilot's exit-1 ID-join failure remains separately preserved.

- Target: chicaihong01, physical NPU0–3 only, independent exact-owned HYPIC
  service; operation `exec-000000000000128b`, exit 0.
- Frozen 3 LongBench-v2 cases: index 0, shortest 55, longest 48. Each used
  two one-token observations followed by one natural-EOS scored request,
  max output 2048 and explicit segment ends. All 3 scored requests completed.
- Scheduler evidence: 3/3 scored request IDs uniquely joined to explicit
  boundary events; 3 verified hot repairs, 41,048 verified skipped tokens
  in total. First scored request had four distinct worker-hot PIDs and
  16,376 verified skipped tokens; its two warm observations had no worker-hot
  event or verified hot repair.
- Physical-lane guard: 27 samples, no foreign NPU0–3 process or probe error.
  Exact container was removed, its workers/port released, lane available.
- The three pilot answers are not a quality score gate. The 381-row matched
  baseline and treatment arms are required for that decision.

Raw artifacts: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-pilot2-hypic`.
SHA256: contract `fa1ffb9ecdb2144b0c74ae16cca66296ce77d0747b4dca22415e333e66f1a32a`;
arm result `4c6fdc0d43a38eda1dbfa205c1eb9b0154b98a97a40cc038e909c085204aaae8`;
event JSONL `2a0514adf374ed2d4c64e60434cbffa4e455938aa5d573654aa03a962f86cda6`.

Next operation: full no-cache baseline `exec-0000000000001293`, started only
after pilot release and NPU0–3 lane availability check. Do not start the
candidate arm until baseline exit, exact release, and row audit are established.
