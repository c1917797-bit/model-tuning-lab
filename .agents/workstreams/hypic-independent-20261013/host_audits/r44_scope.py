"""Private-process reversible binding of the reviewed generic HOST tools."""
import contextlib,copy,threading
from host_audits import r44_profile_policy as policy
from host_audits import r43_profile_controller as controller
from host_audits import r43_profile_audit as auditor
BASE_RECEIPT=controller.receipt
_LOCK=threading.Lock()
def renewal_receipt(c):
 result=BASE_RECEIPT(c);result["r44_wrapper_identity"]=policy.receipt(c);return result
@contextlib.contextmanager
def scope(c,*,checker=None):
 if not _LOCK.acquire(blocking=False):raise RuntimeError("one private R44 scope, no nesting")
 checker=checker or policy.check
 edits=[(policy.prior,"check",checker),(policy.prior,"require_budget",policy.require_budget),
        (controller,"check_contract",checker),(controller,"receipt",renewal_receipt),
        (auditor,"receipt",renewal_receipt),(policy.prior.prior,"PROFILE",copy.deepcopy(policy.PROFILE))]
 saved=[(obj,key,getattr(obj,key))for obj,key,value in edits]
 try:
  for obj,key,value in edits:setattr(obj,key,value)
  yield
 finally:
  for obj,key,value in reversed(saved):setattr(obj,key,value)
  _LOCK.release()
