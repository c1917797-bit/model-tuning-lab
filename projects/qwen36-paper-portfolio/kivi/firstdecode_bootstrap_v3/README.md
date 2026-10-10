# KIVI first-decode v003 immutable source archive

Byte-exact archive of the executed, failed v003 bootstrap. Its SOURCE_MANIFEST
retains the original /cache deployment paths and is not a relocated-run manifest.
Same-image CPU import/parser passed; actual N1 failed importing acl in the native
worker before tensor/model execution. Do not treat this archive as model-ready.
See KIVI_FIRSTDECODE_ACL_IMPORT_FAILURE_20261010.json in the active workstream
for original evidence and the bounded source-supported successor.
