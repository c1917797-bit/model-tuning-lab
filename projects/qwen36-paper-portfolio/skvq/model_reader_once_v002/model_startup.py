"""Source-pinned spawn parent factory, no KIVI/SKVQ numerical authority reused."""
import importlib,multiprocessing as mp,os
from pathlib import Path
import bridge_contract as B
def parent(C,source,root):
    env={k:os.environ.get(k)for k in("VLLM_WORKER_MULTIPROC_METHOD","OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS")}
    B.need(env==dict(VLLM_WORKER_MULTIPROC_METHOD="spawn",OMP_NUM_THREADS="1",MKL_NUM_THREADS="1",OPENBLAS_NUM_THREADS="1"),
      "explicit native spawn and original thread budgets before LLM")
    row=next(x for x in C.obj(source)["multiprocessing_runtime_sources"]if x["module"]=="vllm.utils.system_utils")
    module=importlib.import_module(row["module"]);origin=C.ref(module.__file__)
    B.need(origin==dict(path=row["runtime_path"],bytes=row["snapshot"]["bytes"],sha256=row["snapshot"]["sha256"])and
      module.get_mp_context().get_start_method()=="spawn","real native source-qualified factory")
    return C.atomic(Path(root)/"SPAWN_PARENT.json",dict(source_ref=source,environment=env,actual_native_origin=origin,
      before_actual_LLM_constructor=True,identity=__import__("numeric").identity(),**B.false_scopes()))
