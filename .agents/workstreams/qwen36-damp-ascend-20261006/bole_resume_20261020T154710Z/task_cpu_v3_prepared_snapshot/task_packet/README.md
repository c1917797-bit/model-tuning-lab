# Prepared three-task decoder/scorer packet

This is new default-OFF code, ready for MAIN review and an actual same-image **software-only** smoke. No model, tokenizer, Docker sandbox or official generated-code execution has run in this local preparation. No benchmark score, native/BOLE identity, acceleration, accuracy acceptance or model readiness is claimed.

The current task cohort is exactly GSM8K1319 / HumanEval164 / MMLU14042, with the original fixed two smoke IDs per task. LongBench-v2 is outside the current R115/R118 scope. The rule freeze is prospective, before task model outputs, under MAIN's accepted v012 repair and MMLU/HE conversion semantics.

The important input repair is explicit: render011 omitted GSM's answer-format instruction, while the unchanged original scorer requires `####`. v012 restores the already existing correct original GSM token lists and independently requires that **each**011 list changes only by insertion of the same12-token segment before user EOS. It neither re-renders nor re-tokenizes any task prompt. HE/MMLU retain whole011 row refs/metadata. The actual decoder must decode that instruction and replay full original source/gold/author-template coverage on all15,525 rows. A count or header alone cannot pass this check. Historical sources, token lists and deadlines remain unchanged.

The prepared scoring rules are:

| Task | Frozen semantics |
|---|---|
| GSM8K | Whole original scorer is byte-exact. First `#### ` numeric-string match; comma removal only; no numeric/fallback/last-match normalization. |
| HumanEval | Only an exact whole-output single Python/empty-language fence can be unwrapped; only an exact original official prompt prefix can then be removed. Preserve all remaining bytes and indentation. Original official evaluator/executor, pass@1, one worker,3-second timeout, external strict sandbox. |
| MMLU | Existing five-shot prompts and official gold; newly declared generative first-nonempty-line extraction, uppercase A-D at the start, optional literal `Answer:`, required letter boundary. Full micro accuracy; invalid answers count as wrong. Old likelihood source is retained for author-format provenance, not misrepresented as a deployed generative scorer. |

Normal EOS policy is max2048, ignore_eos false, no forced minimum or extra stop rule, temperature0/seed0, thinkOFF complete frozen frame. Longest prompt3151 requires **max_model_len>=5199**, so a4096 service cannot admit this full cohort unchanged. The component reader reports stop/length cases and actual returned tokens separately; HTTP stop alone does not establish native-worker EOS cause. Full CPU provenance/decoding may require more memory/time than the small software controls; MAIN must enforce and record actual CPU-owner resource/wall budgets, provision adequate RAM, and measure them rather than inheriting a model-device or host budget silently.

The HE source capsule is deliberately minimal and contains only the two exact worker/helper files, new public authority and source metadata. The suite and completion inputs are separately copied public-only read-only mounts with explicit readable modes. Root filesystem is read-only; writes are confined to private temporary scratch. Container argv requires network none, Devices[], runc, env-i without host credentials, uid65534, dropped capabilities/no-new-privileges, private namespaces and bounded memory/CPU/PIDs/FDs/file sizes. The official reliability guard is preserved; external sandbox isolation supplies the host security boundary. MAIN's actual owner controls lifecycle. This packet never starts or stops a container. The independent reader consumes raw CID/create/wait/inspect/logs and exact official result rows; a self-reported success flag is insufficient.

See [EVIDENCE_SCHEMA.md](EVIDENCE_SCHEMA.md) for all executable stages and exact raw record contracts. The code can prepare prompt-only request plans but does not send task model requests. Actual model admission/client/lifecycle, every-request BOLE activation, CPU same-image owner evidence and native reference remain explicit MAIN integration gates. The decoder records real tokenizer assets/library/runtime identity but leaves same-image ownership unaccepted until externally joined. Formal/model/performance flags remain false even when all software/component checks pass.

Local verification:

```bash
python3 -I -B /absolute/candidate/task_decoder_scorer/test_software.py
```

38 pure tests pass: exact actual first-row GSM excerpt repair plus mutated question/gold/instruction/frame/EOS negatives; original scorer hash and strict extraction; HE no-fuzzy/indent behavior; synthetic decoder algorithm controls; raw token/usage/EOS/truncation/request-policy negatives; actual-inspect schema fixtures with network/device/mount/resource/identity failures; umask-safe public staging and extra-file rejection; exact integer paired loss/zero-baseline handling; every CLI default OFF and `--help`. The synthetic tokenizer, HTTP, inspect and public staging fixtures are explicitly not actual tokenizer/model/sandbox evidence. No generated code executes in these tests. All Python sources parse. The three original frozen function files remain whole-byte identical to the supplied primary sources.

Small-source availability is sufficient for this packet. Actual execution still needs the already referenced original full row arrays, official132-file index/source tree, GSM source/data/token-list/license, HE package/dataset and seven checkpoint tokenizer files at their frozen paths. MAIN must preserve those paths or declare a new explicit relocation protocol. No15k rows are copied or re-rendered by this advisory preparation.
