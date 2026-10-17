"""Host-side exact CPU IPC proof consumer; does not construct resource owners."""
from packet_contract import SOFTWARE_CASES
from ipc_controls import SCANNER_REF
FLAGS=('actual_Linux_AF_UNIX','direct_UUID4_scan_consume_pass','nested_original_rejection_pass','bad_basename_original_rejection_pass','scanner_unchanged')

def check(cp,sr,obj,expected_ref):
 def need(v,m):
  if not v:raise ValueError(m)
 need(cp['source']==sr and cp['mode']=='cpu'and cp['NPU']is False and cp['pass_preflight']is True,'actual owned CPU receipt')
 need(cp['actual_rootfs_write_errno']==30,'actual readonly EROFS proof')
 sw=cp['software_controls'];need(sw['discovered']==SOFTWARE_CASES and sw['executed']==SOFTWARE_CASES and sw['passed']is True,'same current complete software count')
 need(cp['actual_IPC_controls_ref']==expected_ref,'same owned IPC proof file')
 r=obj(expected_ref);need(r==cp['actual_IPC_controls'],'CPU result and independently reopened IPC receipt')
 need(r['schema']=='mxr.actual-Linux-IPC-original-scan-controls/v043-repair2'and r['original_scanner']==SCANNER_REF and r['NPU']is False,'unchanged exact original scanner proof')
 need(all(r[k]is True for k in FLAGS),'actual Linux AF_UNIX scan/consume and original rejections required')
 return True
