# Byte-exact source archive

This is a source-only historical archive of actual DL061 and MXR065 packets,
not a relocated executable deployment. SOURCE_COPY_MAP.json records every
original and archived byte identity. Absolute source dependencies, external
build products and raw evidence remain explicitly external; this directory is
not a claim that all device validation can run from this archive alone.

All186 archived payloads were rehashed before staging. Eight original Python
files contain a terminal blank line. Preserve those exact historical bytes;
formatting them would break the archived source identity. At this checkpoint,
normal git diff --cached --check rejected only those eight blank-at-EOF cases.
All other staged files use the normal check. For this exact archive only, run
Git's whitespace check with blank-at-eof disabled while retaining the remaining
whitespace checks. No global Git configuration or source file is changed.

This archive does not claim NPU/model/performance/accuracy acceptance.
