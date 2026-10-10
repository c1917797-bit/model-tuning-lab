"""Close the actual per-instance installer only after real native finished IDs.
Retains deferred original update return. No HTTP DONE -> worker retirement guess.
"""
import hashlib
import inspect
import types
from pathlib import Path
def need(v,m):
    if not v:raise ValueError(m)
def pin(fn,sha):
    path=Path(inspect.getfile(getattr(fn,"__func__",fn))).resolve()
    need(path.is_file() and not path.is_symlink()
         and hashlib.sha256(path.read_bytes()).hexdigest()==sha,"exact installed update owner")
def install(runner,close,expected_ids,installer_sha,publish_final):
    need(type(expected_ids)is list and expected_ids and len(set(expected_ids))==len(expected_ids)
         and callable(close) and callable(publish_final),"actual declared complete owner set")
    current=runner._update_states;pin(current,installer_sha)
    need("_update_states"in vars(runner),"actual per-instance installer exists")
    finished=set();state={"final":None}
    def update(self,scheduler):
        ids=list(scheduler.finished_req_ids)
        need(not finished.intersection(ids) and set(ids)<=set(expected_ids),
             "actual finish once, no unrelated retirement substitute")
        answer=current(scheduler) # real native/installer exactly once, preserve deferred callable
        finished.update(ids)
        if finished==set(expected_ids):
            need(not self.requests and self.input_batch.num_reqs==0
                 and not self.input_batch.req_ids,"actual complete native request/batch drain")
            need(self._update_states is replacement,"only exact own finish wrapper")
            self._update_states=current
            final=close() # unchanged book.close -> exact installer restore -> actual journal.finish
            state["final"]=final;publish_final(final)
        return answer
    replacement=types.MethodType(update,runner);runner._update_states=replacement
    def final():
        need(state["final"]is not None,"actual finished-only final has not occurred")
        return state["final"]
    return final
