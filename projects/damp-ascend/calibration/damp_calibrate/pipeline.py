"""Fit/tune/frozen-validation selector; writes offline plans, never arms serving."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
from damp_capture.contract import LAYERS, MODEL_HASHES, RESULT_ROOT, canonical, digest, file_digest
from .evidence import Capture
from .numerics import candidate, mixed_cost, storage_errors
from .rules import ALPHAS, PAPER, choose, protected, require, retention

def weight(future, torch):
    require(tuple(future.shape) == (256,12), "exact future horizon required")
    return torch.tensor(retention(future.tolist()),dtype=torch.float64)

def select(samples, torch):
    """Only fit+tune inputs; validation is deliberately absent from this function."""
    require(set(samples) == {"fit","tune"} and all(len(v) == 72 for v in samples.values()),
            "exact72 fit and tune anchors required")
    rms_sum = torch.zeros((12,128),dtype=torch.float64)
    for state,future in samples["fit"]:
        require(tuple(state.shape) == (12,128,128), "full native geometry required")
        rms_sum += state.double().square().mean(-1)
    rms = (rms_sum / 72).sqrt()
    fits, layouts, costs, invalid = [], [], [], []
    for alpha in ALPHAS:
        sr,pv = candidate(rms,alpha,torch)
        risk = torch.zeros((12,128),dtype=torch.float64)
        for state,future in samples["fit"]:
            error8,_ = storage_errors(state,sr,pv,torch)
            risk += error8 * weight(future,torch)[:,None] / 72
        pk = []; high = torch.zeros((12,128),dtype=torch.bool)
        for head in range(12):
            indices,order = protected(risk[head].tolist(),16)
            high[head,indices] = True; pk.append(order)
        score = torch.zeros(12,dtype=torch.float64)
        for state,future in samples["tune"]:
            e8,e16 = storage_errors(state,sr,pv,torch)
            score += mixed_cost(e8,e16,weight(future,torch),high,torch) / 72
        validity = [math.isfinite(float(v)) and float(v) >= 0 for v in score]
        fits.append(risk); costs.append([float(v) if ok else None for v,ok in zip(score,validity)])
        layouts.append(dict(sr=sr,pv=pv.to(torch.int32),pk=torch.tensor(pk,dtype=torch.int32),high=high))
        invalid.append([None if ok else "FP16 protected-region error overflow" for ok in validity])
    selected = [choose([costs[c][h] for c in range(len(ALPHAS))]) for h in range(12)]
    plan = {key:torch.stack([layouts[selected[h]][key][h] for h in range(12)])
            for key in ("pk","pv","sr")}
    high = torch.stack([layouts[selected[h]]["high"][h] for h in range(12)])
    report = dict(grid=list(ALPHAS),grid_provenance="project-selected RMS-power grid; author grid unpublished",
        selected_candidates=selected, selected_alphas=[ALPHAS[c] for c in selected],
        candidate_tune_j=costs,candidate_invalid=invalid,
        candidate_fit_c=[r.tolist() for r in fits],rms=rms.tolist(),
        protected_original_keys=[plan["pk"][h,:16].tolist() for h in range(12)],
        selection_scope="per-rank-layer-Hv; fit then tune only",
        equal_weight="anchor/window/sequence/domain; balanced36 and six anchors imply1/72 per split")
    return plan,high,report

def validation(samples,plan,high,torch):
    require(len(samples) == 72, "exact72 independent validation anchors required")
    score = torch.zeros(12,dtype=torch.float64); energy = torch.zeros(12,dtype=torch.float64)
    for state,future in samples:
        e8,e16 = storage_errors(state,plan["sr"],plan["pv"],torch); w = weight(future,torch)
        score += mixed_cost(e8,e16,w,high,torch) / 72
        energy += state.double().square().sum((1,2)) * w / 72
    finite = [math.isfinite(float(v)) for v in score]
    return dict(status="finite_diagnostic" if all(finite) else "failed_nonfinite_diagnostic",
        weighted_j=[float(v) if ok else None for v,ok in zip(score,finite)],
        weighted_state_energy=energy.tolist(),
        weighted_relative_rms=[math.sqrt(float(score[h])/max(float(energy[h]),1e-300))
                               if finite[h] else None for h in range(12)],
        feedback_to_selection=False, task_accuracy=False)

def write_json(path,value):
    with Path(path).open("xb") as stream: stream.write(canonical(value)+b"\n")

def run(manifest,root,source_lock,output,threads):
    require(os.environ.get("DAMP_CALIBRATION_CPU_ONLY") == "1" and sys.byteorder == "little",
            "explicit little-endian CPU-only calibration required")
    import torch
    require(1 <= threads <= 32, "CPU thread budget outside1..32")
    torch.set_num_threads(threads)
    directory = Path(output).resolve()
    require(directory.is_relative_to(RESULT_ROOT) and directory != RESULT_ROOT and not directory.exists(),
            "existing/unsafe result path")
    directory.mkdir(parents=False,exist_ok=False)
    try:
        capture = Capture(manifest,root,source_lock)
        code = {str(p.resolve()):file_digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))}
        write_json(directory/"PROVENANCE.json",dict(schema="damp-calibration-provenance/v1",
            paper=PAPER,paper_equations=[14,15,16,17],official_code_verified=False,
            candidate_grid="project-selected-not-author-exact",code=code,torch_version=torch.__version__,
            arithmetic="CPU FP32 SR/round-ties-even reciprocal0x3c010204; FP64 original-coordinate risk",
            model_hashes=MODEL_HASHES,**capture.provenance))
        entries = []
        for rank in range(4):
            for layer in LAYERS:
                # One rank/layer's72 anchors per split only; no all-model state in memory.
                data = {split:[(state,future) for _,_,state,future in capture.samples(rank,layer,split,torch)]
                        for split in ("fit","tune")}
                plan,high,report = select(data,torch)
                del data
                # Selection is frozen before validation bytes are loaded.
                plan_semantic_sha = digest({k:v.tolist() for k,v in plan.items()})
                val = [(state,future) for _,_,state,future in capture.samples(rank,layer,"validation",torch)]
                report["validation"] = validation(val,plan,high,torch); del val
                require(digest({k:v.tolist() for k,v in plan.items()}) == plan_semantic_sha,
                        "validation changed frozen plan")
                p = directory/f"rank-{rank}-layer-{layer}.pt"
                with p.open("xb") as stream: torch.save(plan,stream)
                report_path = directory/f"rank-{rank}-layer-{layer}.calibration.json"
                write_json(report_path,report)
                entries.append(dict(rank=rank,layer=layer,path=str(p),sha256=file_digest(p),
                    tensor_semantic_sha256=plan_semantic_sha,report_path=str(report_path),
                    report_sha256=file_digest(report_path),validation_status=report["validation"]["status"]))
        require(len(entries) == 192 and {(p["rank"],p["layer"]) for p in entries} ==
                {(r,l) for r in range(4) for l in LAYERS}, "partial calibration plans")
        status = "calibrated_offline_candidate" if all(p["validation_status"] == "finite_diagnostic" for p in entries) \
                 else "frozen_validation_failed"
        index = dict(schema="damp-calibration-plan/v1",status=status,purpose="offline-not-serving",
            model_config_sha256=MODEL_HASHES["config.json"],tp=4,plans=entries,
            calibration=dict(manifest_path=str(Path(manifest).resolve()),full_manifest_sha256=file_digest(manifest),
                manifest_semantic_sha256=digest(capture.manifest),train_only=True,prompts=36,input_tokens=1024,
                output_tokens=4096,protected_k=16,int8_group=32,validation_feedback=False),
            provenance_path=str(directory/"PROVENANCE.json"),provenance_sha256=file_digest(directory/"PROVENANCE.json"),
            not_proven=["compressed NPU recurrence","NPUGraph","cache allocation","E2E performance","task accuracy"])
        write_json(directory/"PLAN_INDEX.json",index)
        return dict(status=status,plans=192,path=str(directory/"PLAN_INDEX.json"),sha256=file_digest(directory/"PLAN_INDEX.json"))
    except Exception as error:
        write_json(directory/"FAILURE.json",dict(status="failed",error=type(error).__name__,detail=str(error),
            partial_outputs_not_servable=True))
        raise

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",required=True); p.add_argument("--capture-root",required=True)
    p.add_argument("--source-lock",required=True); p.add_argument("--output-dir",required=True)
    p.add_argument("--cpu-threads",type=int,default=8); a = p.parse_args()
    print(json.dumps(run(a.manifest,a.capture_root,a.source_lock,a.output_dir,a.cpu_threads),sort_keys=True))

if __name__ == "__main__": main()
