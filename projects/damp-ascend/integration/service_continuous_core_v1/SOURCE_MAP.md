# Minimal source seam map (no modification of cited native sources)

Native gdn.py SHA d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816:
- lines219–283: ALL-row mixed prefill conv run_mode0 (PCP1 branch), reused;
- lines284–309: pure decode conv run_mode1, reused;
- lines311–329: rearrange and fused_gdn_gating, reused once;
- lines337–369: native mixed decode prefix; replaced ONLY state ABI/native recurrence
  call with independently named all-batch compressed decode;
- lines377–410: original suffix chunk, starts/prebuilt/native initial orientation
  reused; initial read replaced selected unpack and final write selected pack;
- native output remains concat decode-prefix then suffix, no input reordering.

Builder SHA42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16:
decode_threshold1/mamba-none, q1-stateful continuation is reclassified decode;
733–771 rebased prefix/suffix GDN metadata,407–412 ALL-row conv metadata.
Frozen continuous_metadata_v1 contract113f37...1b owns CPU turn agreement.

Actual Mamba allocator SHA94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968:
4681–4714 four typed contiguous SoA real raw-backed views; shared_by may includeFA.
Do not repair alias with independent allocations or claim padded-page byte savings.
Cache_identity Agent owns exact early zero/live page admission and installs separate
source-bound runner observer; this packet does NOT replace that observer.

Original receiver/copier hashes pinned by binding.py. Constructor authority refuses
unaccepted packets, actual48 instances verified externally before model-call.
No edits to actual native forward/projection/weights/convolution/gating/chunk math,
frozen decode SO, old plan index, old source manifests or historical receipts.
