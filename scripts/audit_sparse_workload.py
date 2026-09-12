"""Past-only overlap opportunity audit, no inference or speedup measurement."""
import hashlib
import json
from pathlib import Path
from transformers import AutoTokenizer
from model_tuning_lab.sparse_checkpoint_plan import plan_checkpoints, restorable_position

dataset = Path("/data/query_rewrite.jsonl")
model = Path("/model")
assert hashlib.sha256(dataset.read_bytes()).hexdigest() == "a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e"
assert hashlib.sha256((model / "config.json").read_bytes()).hexdigest() == "191e0af232104ed8b65258cf3fb2b842e288008baca7633c11b82a1ac7203aab"
questions = [json.loads(line)["question"] for line in dataset.read_text().splitlines() if line.strip()]
assert len(questions) == 357 and all(isinstance(q, str) and q for q in questions)
tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True)
reports = []
for special in (False, True):
    tokens = tokenizer(questions, add_special_tokens=special)["input_ids"]
    trie, overlaps = {}, []
    for sequence in tokens:
        node, shared = trie, 0
        for token in sequence:
            if token not in node:
                break
            shared += 1
            node = node[token]
        overlaps.append(shared)
        node = trie
        for token in sequence:
            node = node.setdefault(token, {})
    # Train on the first71 sequential requests, evaluate on the remaining286.
    # Each training overlap and evaluation overlap sees past requests only.
    train_count = 71
    histogram = [0] * (max(overlaps[:train_count], default=0) + 1)
    for overlap in overlaps[:train_count]:
        histogram[overlap] += 1
    plans = []
    for budget in (1, 2, 4):
        positions = plan_checkpoints(histogram, 1536, budget)
        saved = [restorable_position(positions, overlap, overlap) for overlap in overlaps[train_count:]]
        plans.append(dict(budget=budget, positions=positions,
                          evaluation_potential_saved_tokens=sum(saved),
                          evaluation_potential_hits=sum(x > 0 for x in saved)))
    reports.append(dict(add_special_tokens=special, request_count=len(tokens),
                        raw_completion_prompts=True, cache_salt_assumed_shared=True,
                        block_size=1536, train_count=train_count,
                        evaluation_count=len(tokens)-train_count,
                        max_overlap=max(overlaps), block_eligible_requests=sum(x >= 1536 for x in overlaps),
                        total_input_tokens=sum(map(len,tokens)),
                        lengths=list(map(len,tokens)), past_only_overlaps=overlaps,
                        plans=plans))
result = dict(scope="optimistic token-reuse opportunity only; no state capacity/eviction or timing modeled",
              model="Qwen3.8-27B", dataset_sha256=hashlib.sha256(dataset.read_bytes()).hexdigest(),
              tokenizer_config_sha256=hashlib.sha256((model / "tokenizer_config.json").read_bytes()).hexdigest(),
              no_model_inference=True, reports=reports)
Path("/output/opportunity.json").write_text(json.dumps(result, indent=2))
print(json.dumps({"scope":result["scope"], "reports":[{k:v for k,v in r.items() if k not in ("lengths","past_only_overlaps")} for r in reports]}, indent=2))
