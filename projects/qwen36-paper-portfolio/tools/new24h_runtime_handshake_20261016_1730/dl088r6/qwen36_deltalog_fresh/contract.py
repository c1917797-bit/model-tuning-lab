"""Exact installed source pins; olda369 not an admitted library."""
import hashlib
from pathlib import Path
AUX_NAMES=('k_log','u_log','lambda_log','decay','length')
GDN_SHA='d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816'
MAMBA_SHA='1d854c36fe1b32cfacd071393c05fc155f37190fe19afc5e6c02d5d0a2d561f3'
RUNNER_SHA='94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968'
LEGACY_SHA='ec4381191fbc9afd47bf15ac47c38f00c4d80ae0148dbfb115da37ba5255aac9'
NAMESPACE='qwen36_deltalog_split_scale_v051'
LIBRARY_SHA=None # Set only after exact actual051 build admission; never an old B010 certificate.
STEPS=160
OUTPUT_LIMIT=.00303
STATE_LIMIT=7.92e-7
QWEN_SHA='885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0'
CHUNK_SHA='6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5'
BUILDER_SHA='42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16'
PARALLEL_SHA='df02e5386bc83e6ac644ff46f0297fdd19003bd55584c629840348a5fda8473f'
CONTEXT_SHA='1c6fa51e9a02a120fed5e7357afb1190516cbdfefd1c644dfcd860603f1527c5'
CONFIG_SHA='69db4eb7196bc8190813231b3018ca05d8c2e3abc7b1af19d55c157af44a9d9c'
def require_digest(path,expected):
 if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=expected:raise RuntimeError('actual source drift '+str(path))
