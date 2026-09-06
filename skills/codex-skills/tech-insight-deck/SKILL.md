---
name: tech-insight-deck
description: "Generate professional technology-insight PowerPoint decks in a fixed Huawei-style template (cover → summary → tech list → per-tech insight pages → thanks). Triggers whenever the user asks for a technology insight, tech scouting report, technology landscape analysis, 技术洞察, 技术调研, or wants to analyze a technical area (LLMs, chips, compilers, agents, multimodal, embodied AI, etc.) and present findings as slides. Also use when the user references the fixed template, mentions arXiv/IEEE paper analysis with strategic implications, or wants to compare what major players (Google, Meta, Microsoft, ByteDance, Tencent, Alibaba, Kuaishou, Apple, Samsung, NVIDIA, AMD, Huawei, etc.) are doing in a given technical direction. Use this skill any time the user wants tech insight content delivered as a PPT — even if they don't say 'PPT' explicitly."
---

# Tech Insight Deck Skill

Generate a production-grade technology-insight PowerPoint deck using a fixed
template. The deck has five logical sections:

1. **Cover** — title, department, author, date
2. **Insight summary** — one paragraph per direction (≤130 字 each) + overall (≤80 字)
3. **Tech list** — table of (大类 / 技术名称 / 技术简介)
4. **Per-tech insight pages** — one slide per technology, fixed 6-block layout
   (技术背景 / 技术细节 + 系统图 / 实验结果 + 实验图 / 洞察启示)
5. **Final summary** — concise problems and future outlook
6. **Thank-you**

The template lives at `assets/template.pptx`. Slide 4 is the canonical
"insight page" layout; the build script duplicates it once per technology.

---

## Workflow

### Step 1 — Understand the topic

Read the user's request and identify:
- The **business question** behind the topic (what decision will this support?)
- The **technical scope** (what subfields are necessarily covered?)
- A draft of **≤3 directions** (mutually exclusive, each strong enough to stand
  on its own as a paragraph)

If anything is unclear, ask the user **before** starting research. Don't ask
more than two clarifying questions.

### Step 2 — Read the methodology

**Read [references/methodology.md](references/methodology.md) in full** before
doing research or writing content. It defines:
- How to source (≥3 distinct authoritative sources, last 18 months)
- Which players to track (Google, Meta, Microsoft, ByteDance, Tencent,
  Kuaishou, Alibaba, Apple, Samsung, NVIDIA, AMD, Huawei, etc.)
- How to filter techs (≤5 per direction; figure availability is mandatory)
- How to write each block (writing rules, AI-tone bans)

### Step 3 — Research

Use the `web_search` tool. The skill itself does **not** wrap web search —
the main agent runs the searches. Aim for:
- ≥3 distinct authoritative sources per technology
- arXiv / IEEE / ACM / vendor blogs / GTC-class talks / standards bodies
- Last 18 months unless citing a foundational paper as background

For each candidate technology, before adding it to the spec, **download the
paper PDF** (web_fetch the arXiv PDF URL or vendor PDF) — you'll need it to
extract figures.

### Step 4 — Extract figures from each paper

Each per-tech insight page **must** carry two real figure crops:
- System / architecture / pipeline screenshots for "技术细节". Use
  `tech_detail_figures` with one or two real crops from the paper. If only one
  crop is needed, it will span both image slots; never leave the second slot
  blank.
- Experimental result screenshots for "实验结果". Use `experiment_figures` with
  one or two real crops as needed.

Every `reference` line must link to the real source. Set `reference_url`
explicitly whenever possible; otherwise the build script can infer arXiv, DOI,
or an explicit URL embedded in the reference text.

Use `scripts/extract_figure.py`:

```bash
# Whole page first to find the right region
python scripts/extract_figure.py page --pdf paper.pdf --page 5 --out p5.png

# Then crop with percent bbox (left,top,right,bottom in [0,1])
python scripts/extract_figure.py crop \
    --pdf paper.pdf --page 5 \
    --bbox-pct 0.08,0.18,0.92,0.55 \
    --out fig_arch.png
```

If you cannot find a usable figure for a paper, **drop that paper** — don't
fabricate, and don't ship a per-tech page without real figures.

### Step 5 — Write the spec.json

Read [references/content_schema.md](references/content_schema.md) for the full
JSON shape. Save your spec to a working file (e.g., `/tmp/insight_spec.json`).

Bilingual style: paper titles and technical terms stay in English; explanatory
prose is in Chinese. Match the template's existing style.

Always include `final_summary` for a complete report. Keep it concise:
- `problems`: 2-4 concrete current issues or adoption blockers.
- `outlook`: 2-4 likely 12-24 month technology directions.
- `conclusion`: one decision-oriented closing judgment.

### Step 6 — Build the deck

```bash
python scripts/build_deck.py \
    --spec /tmp/insight_spec.json \
    --out /mnt/user-data/outputs/tech_insight.pptx
```

The script:
- Fills slides 1, 2, 3 in place
- Populates slide 4 with the first technology
- Clones slide 4 once per additional technology
- Reorders so the thank-you slide stays last

### Step 7 — Visual QA (REQUIRED)

The first render usually has overflow or alignment issues, especially on slide
4 where text blocks are tightly packed. Run the standard pptx visual-QA loop:

```bash
soffice --headless --convert-to pdf /mnt/user-data/outputs/tech_insight.pptx \
    --outdir /tmp/
pdftoppm -jpeg -r 120 /tmp/tech_insight.pdf /tmp/slide
ls /tmp/slide-*.jpg
```

Then `view` each slide image and look for:
- Text overflow past the rounded-rectangle borders on slide 4
- Figure aspect ratios that look squished or overly cropped
- Blank image areas in either the technical-detail or experiment sections
- Extra blank lines at the bottom of text boxes
- Missing or overlong final summary page
- Summary page prefix keywords (`方向1：`, `方向2：`, `总结：`) are bold
- Final summary title is centered
- Empty data rows in the slide-3 table
- Leftover placeholder text (`xxx`, `方向 1`, etc.)

Fix issues in the spec and rebuild. **Stop after one fix-and-verify cycle**
unless a real user-visible defect remains.

### Step 8 — Deliver

Use the `present_files` tool to deliver the final `.pptx` to the user.
Briefly summarize what's in the deck (number of directions, number of
technologies, key insight) — but don't repeat content verbatim.

---

## File map

```
tech-insight-deck/
├── SKILL.md                       (this file)
├── assets/
│   └── template.pptx              (the canonical template — do not edit)
├── scripts/
│   ├── build_deck.py              (main: spec.json -> deck.pptx)
│   ├── extract_figure.py          (paper PDF -> cropped figure PNG)
│   └── inspect_template.py        (debug: print shape map of a template)
└── references/
    ├── methodology.md             (HOW to do good insight — read first)
    └── content_schema.md          (spec.json schema)
```

---

## Key constraints (do not violate)

1. **One paper = one slide.** Never merge two papers onto one slide, and never
   spread one paper across two slides. If a paper is too rich for one page,
   pick the single most business-relevant angle.
2. **Every per-tech page must have real paper figures** — system diagram on
   left, experimental results on right. No figures = drop the paper.
3. **Last 18 months as primary window.** Older work only as foundational
   citations.
4. **≥3 distinct sources per technology.** Don't rely on a single arXiv paper;
   cross-reference vendor blogs / industry coverage / standards bodies.
5. **Track major players actively.** Each direction's summary should
   acknowledge what the major players (Google, Meta, Microsoft, ByteDance,
   Tencent, Kuaishou, Alibaba, Apple, Samsung, NVIDIA, AMD, Huawei) are doing
   — silence from a player is itself signal.
6. **Bilingual style** — English paper titles & terms, Chinese exposition.
7. **Avoid AI tone.** See [references/methodology.md](references/methodology.md)
   §6 for banned phrases. Read every paragraph aloud — if it doesn't sound
   like a senior engineer wrote it, rewrite.
