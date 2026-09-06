# Content Schema (`spec.json`)

`build_deck.py` consumes a JSON file with this structure:

```jsonc
{
  // Slide 1 (cover)
  "title": "Groq 编译器栈技术洞察",       // 大标题
  "department": "战略规划部",
  "author": "张三",
  "date": "2026-05-09",

  // Slide 2 (summary)
  "topic": "Groq 引入后的技术价值与编译器作用",   // 填入"本次洞察主要围绕<topic>"
  "directions": [
    {
      "name": "Groq 编译器作为核心壁垒",         // 内部标识，用于 slide 3 大类列
      "category_label": "Groq 编译器栈",         // slide 3 表格大类列实际显示文本（可选，缺省用 name）
      "summary": "Groq 的核心壁垒在编译器……",     // ≤130字，slide 2 第 1 条
      "technologies": [                           // 这个方向下的技术（≤5 个）
        {
          // 用于 slide 3 表格
          "name": "Groq Compiler (TSP-aware)",
          "brief": "确定性调度的静态编译器，把所有内存与计算决策推到编译期。",

          // ===== 用于 slide 4 (per-tech insight page) =====
          "title": "A Software-Defined Tensor Streaming Multiprocessor for Large-Scale Machine Learning",
          "reference": "ISCA 2022, doi:10.1145/3470496.3527405",

          "background": "Groq 团队在 ISCA 2022 公开 TSP 架构……",   // 80-120字

          // 技术细节区
          "tech_detail_figure": "/path/to/groq_arch.png",            // 必须：系统/架构图截图
          "tech_detail_figure2": null,                               // 可选第二张图（多数情况留空）
          "tech_detail_points": [                                    // 3 条要点
            "确定性指令调度：所有数据流路径在编译期确定，运行时无仲裁。",
            "片上 SRAM 替代 HBM：……",
            "无缓存、无分支预测：……"
          ],

          // 实验结果区
          "experiment_method_header": "实验方法（Experimental Setup）",
          "experiment_method_points": [
            "平台与模型：单卡 Groq LPU，Llama 2 70B int8。",
            "负载模拟：批量 1-32，序列长度 128-4096。",
            "对比基准：A100 80GB（vLLM）、H100（TensorRT-LLM）。"
          ],
          "experiment_figure": "/path/to/groq_throughput.png",        // 必须：实验结果图截图
          "experiment_result_points": [                               // 2 条带数字结论
            "性能：单 token 延迟较 H100 降低 ~10×（batch=1, seq=2048）。",
            "效率：每 token 能耗下降约 5×，但单卡吞吐落后 H100。"
          ],

          // 洞察启示
          "takeaway": "Groq 的速度优势在小 batch、低延迟场景明显……"  // 60-100字
        }
        // ... more technologies
      ]
    }
    // ... up to 3 directions
  ],

  // Final summary page: inserted after all insight pages and before thanks.
  "final_summary": {
    "title": "存在问题与未来展望",
    "problems": [
      "KV cache 复用依赖请求相似度，低复用业务很难摊薄额外控制面成本。",
      "跨节点迁移对网络、序列长度、批调度强相关，实验收益不能直接等价为生产收益。"
    ],
    "outlook": [
      "未来 12-24 个月，cache 层会从引擎内部模块变成推理集群共享数据平面。",
      "调度器会同时感知 GPU 负载、cache 命中率、网络拥塞和租户 SLA。"
    ],
    "conclusion": "优先把 KV cache 能力做成可观测、可调度的基础设施，再逐步接入跨节点迁移和远端 offload。"
  },

  "overall_summary": "Groq 走的是用编译器复杂度换运行时确定性的极端路线……"  // ≤80字
}
```

## Field rules

- All text fields accept `\n` for line breaks within a paragraph block.
- Image paths must be absolute or relative to the working directory where you
  run `build_deck.py`.
- `tech_detail_figure` and `experiment_figure` are **required** for every
  technology — if you can't find a figure for a paper, drop the paper.
- `reference_url` should be set to the real source URL for the reference line.
  If omitted, `build_deck.py` infers arXiv (`https://arxiv.org/abs/<id>`), DOI
  (`https://doi.org/<doi>`), or an explicit URL found in `reference`.
- Prefer the list forms `tech_detail_figures` and `experiment_figures` when a
  section needs one or two screenshots. One image automatically spans the whole
  available slot; two images are placed into the two available slots without
  leaving a blank placeholder.
- Images are center-cropped to the target slot ratio before insertion so the
  PPT does not stretch screenshots. Crop the source figure tightly enough that
  center-cropping will not remove important labels.
- `directions` should contain 1-3 entries; each entry's `technologies` list
  should contain 1-5 entries.  Outside this range will still build but may
  look odd on slide 3.
- `final_summary` is strongly recommended. Keep `problems` and `outlook` to
  2-4 short items each. This page should summarize adoption blockers and the
  next 12-24 month direction, not repeat per-paper details.
- Backward compatibility: older specs using `future_trends` still build, but
  new decks should use `final_summary`.

## Generating images for figure fields

Use `scripts/extract_figure.py crop`:

```bash
python scripts/extract_figure.py crop \
    --pdf paper.pdf --page 4 \
    --bbox-pct 0.08,0.18,0.92,0.55 \
    --out fig_arch.png
```

Tips for picking a bounding box:
- Render the whole page first (`page` subcommand) to see coordinates.
- Include the figure caption in the crop — it adds context on the slide.
- Aim for an aspect ratio close to the slot on slide 4:
  - tech_detail_figure: about 3.0" × 2.2" → ratio ~1.36
  - experiment_figure: about 5.1" × 1.8" → ratio ~2.85 (wide, often a row of charts)
