"""Pure exact-source proof of the untimed TP4/3CPU launch configuration."""
import ast
from pathlib import Path
import sourceio as C

INSTALLED=dict(multiproc_executor='/vllm-workspace/vllm/vllm/v1/executor/multiproc_executor.py',
    worker_base='/vllm-workspace/vllm/vllm/v1/worker/worker_base.py',
    ascend_worker='/vllm-workspace/vllm-ascend/vllm_ascend/worker/worker.py',
    ompmultiprocessing='/vllm-workspace/vllm/vllm/utils/ompmultiprocessing.py',
    cpu_binding='/vllm-workspace/vllm-ascend/vllm_ascend/cpu_binding.py',
    ascend_config='/vllm-workspace/vllm-ascend/vllm_ascend/ascend_config.py')


def consume(sources):
    C.need(set(sources)==set(INSTALLED),'all exact native TP4/OMP/binding source operands')
    trees={}
    for name,r in sources.items():
        p=C.checked(r);body=p.read_bytes();compile(body,str(p),'exec');trees[name]=ast.parse(body)
    omp=next(n for n in trees['ompmultiprocessing'].body if isinstance(n,ast.ClassDef)and n.name=='OMPProcessManager')
    methods={n.name:n for n in omp.body if isinstance(n,ast.FunctionDef)}
    first=methods['__init__'].body[0]
    C.need(isinstance(first,ast.If)and ast.unparse(first.test)=='not current_platform.is_cpu()'and
        len(first.body)==1 and isinstance(first.body[0],ast.Return),'actual nonCPU OMP initialization returns before CPU partitioning')
    first=methods['configure_omp_envs'].body[0]
    C.need(isinstance(first,ast.If)and ast.unparse(first.test)=='not current_platform.is_cpu() or self.skip_setup'and
        isinstance(first.body[0],ast.Expr)and isinstance(first.body[0].value,ast.Yield)and isinstance(first.body[1],ast.Return),
        'actual nonCPU launcher context yields without dividing CPU cores by TP ranks')
    loops=[n for n in ast.walk(trees['multiproc_executor'])if isinstance(n,ast.For)and ast.unparse(n.target)=='local_rank'and ast.unparse(n.iter)=='range(self.local_world_size)']
    C.need(len(loops)==1 and any(isinstance(n,ast.Call)and ast.unparse(n.func)=='WorkerProc.make_worker_process'for n in ast.walk(loops[0])),
        'native executor spawns every configured TP rank independent of cpuset length')
    config=[n for n in ast.walk(trees['ascend_config'])if isinstance(n,ast.Assign)and any(ast.unparse(t)=='self.enable_cpu_binding'for t in n.targets)]
    C.need(len(config)==1 and ast.unparse(config[0].value)=="additional_config.get('enable_cpu_binding', True)",
        'actual supported additional-config enable_cpu_binding knob and default')
    blocks=[n for n in ast.walk(trees['ascend_worker'])if isinstance(n,ast.If)and ast.unparse(n.test)=='get_ascend_config().enable_cpu_binding']
    C.need(len(blocks)==1 and any(isinstance(n,ast.Call)and ast.unparse(n.func)=='bind_cpus'for n in ast.walk(blocks[0])),
        'actual worker optional CPU binding is guarded by that exact knob')
    return dict(schema='bole.native-TP4-CPU3-source-proof/v1',sources=sources,
        four_workers_by_native_local_world_size=True,nonCPU_OMP_partition_bypassed=True,
        explicit_enable_cpu_binding=False,actual_runtime_launch_proven=False,formal_timing=False)


def installed(sources):
    consume(sources)
    return{name:dict(r,path=INSTALLED[name])for name,r in sources.items()}
