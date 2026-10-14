"""Reuse reviewed generic prompt/scoring definitions only, never its HTTP runner."""
import ast,hashlib,re
from pathlib import Path
EXPECTED="9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0"
FUNCTIONS={"extract_non_reasoning","first_option","gsm8k_prediction","build_case","score_case"}
CONSTANTS={"LONGBENCH_PROMPT","GSM8K_PROMPT"}

def load_ruler(path):
    path=Path(path)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError("absolute regular reviewed ruler required")
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=EXPECTED:
        raise ValueError("reviewed quality ruler drift")
    tree=ast.parse(raw)
    selected=[];found=set()
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS:
            selected.append(node);found.add(node.name)
        elif isinstance(node,ast.Assign) and len(node.targets)==1:
            target=node.targets[0]
            if isinstance(target,ast.Name) and target.id in CONSTANTS:
                selected.append(node);found.add(target.id)
    if found!=FUNCTIONS|CONSTANTS:raise ValueError("ruler definitions incomplete")
    module=ast.Module(body=[ast.ImportFrom(module="__future__",names=[ast.alias(name="annotations")],level=0)]+selected,type_ignores=[])
    ast.fix_missing_locations(module)
    namespace={"re":re}
    exec(compile(module,str(path),"exec"),namespace)
    return {name:namespace[name] for name in found}
