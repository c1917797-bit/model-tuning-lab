#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const [specPath, outDir] = process.argv.slice(2);
if (!specPath || !outDir) {
  console.error("Usage: init_three_zone_project.js <page-contracts.json> <output-project-dir>");
  process.exit(2);
}

const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const projectDir = path.resolve(outDir);
const promptDir = path.join(projectDir, "image2-prompts");
const imageDir = path.join(projectDir, "image2-middle");
const previewDir = path.join(projectDir, "preview");
const qaDir = path.join(projectDir, "qa");

for (const dir of [projectDir, promptDir, imageDir, previewDir, qaDir]) {
  fs.mkdirSync(dir, { recursive: true });
}

const copiedSpec = path.join(projectDir, "page-contracts.json");
if (path.resolve(specPath) !== copiedSpec) {
  fs.copyFileSync(specPath, copiedSpec);
}

function needsPrompt(slide) {
  const type = slide.type || "standard";
  return ["standard", "synthesis"].includes(type);
}

function promptFor(slide, index) {
  const language = spec.meta?.language === "zh" ? "Chinese" : "English";
  const labels = [
    ...(slide.keyPoints || []),
    slide.coreMessage || ""
  ].filter(Boolean).join("; ");
  return [
    "Create a polished wide infographic panel for the middle area of a technology-company internal report slide.",
    "Canvas role: middle content only.",
    "Aspect ratio: exactly 2.37:1 wide panel, optimized to fill a PowerPoint middle canvas. Do not create a 16:9 full slide.",
    "Do NOT include a slide title, footer conclusion, page number, logo, speaker portrait, placeholder, lorem ipsum, or garbled text.",
    "Style: white background, restrained red accents for key points, blue/gray capability cards, light-gray section backgrounds, thin grid lines, compact executive-report density.",
    `Language: ${language}; use concise readable labels.`,
    `Topic: ${slide.title || `slide ${index}`}.`,
    `Required content: ${labels || "architecture, flow, key modules, and implications"}.`,
    `Visual layout: ${slide.visualType || "structured architecture / matrix / flow diagram"}.`,
    "Text density: medium.",
    "Output should fill the panel edge-to-edge with minimal empty top and bottom margins.",
    "No red warning boxes. No red lightbulb. No decorative hero image. No speaker-only screenshot."
  ].join("\n");
}

const promptIndex = [];
(spec.slides || []).forEach((slide, i) => {
  const pageNo = String(i + 1).padStart(2, "0");
  if (needsPrompt(slide)) {
    const promptPath = path.join(promptDir, `slide-${pageNo}.md`);
    fs.writeFileSync(promptPath, promptFor(slide, i + 1) + "\n", "utf8");
    promptIndex.push({ slide: i + 1, title: slide.title || "", prompt: `image2-prompts/slide-${pageNo}.md`, expectedImage: `image2-middle/slide-${pageNo}.png` });
  }
});

fs.writeFileSync(path.join(promptDir, "prompt-index.json"), JSON.stringify(promptIndex, null, 2) + "\n", "utf8");

const missingImages = (spec.slides || []).map((slide, i) => {
  const type = slide.type || "standard";
  if (!["standard", "synthesis"].includes(type)) return null;
  const expected = slide.middleImage || `image2-middle/slide-${String(i + 1).padStart(2, "0")}.png`;
  return fs.existsSync(path.resolve(projectDir, expected)) ? null : expected;
}).filter(Boolean);

const notes = [
  `# ${spec.meta?.title || "Three-zone PPT Project"}`,
  "",
  "## Workflow",
  "",
  "1. User brief is converted into page contracts.",
  "2. Each standard/synthesis page receives a middle-canvas prompt.",
  "3. Middle canvases are generated or sourced, then saved into `image2-middle/`.",
  "4. PPT is assembled with editable title, static middle canvas, editable bottom conclusion.",
  "5. Contact sheet is exported for light QA.",
  "",
  "## Prompt Files",
  "",
  ...promptIndex.map((p) => `- slide ${p.slide}: ${p.prompt}`),
  "",
  "## Missing Middle Images",
  "",
  ...(missingImages.length ? missingImages.map((p) => `- ${p}`) : ["- none"]),
  "",
  "## QA Notes",
  "",
  "- Confirm title and bottom conclusion remain editable.",
  "- Confirm middle images fill the reserved canvas and do not duplicate title/conclusion.",
  "- Mark `visual fallback` if no image generation or useful source asset is available."
];

fs.writeFileSync(path.join(projectDir, "workflow-notes.md"), notes.join("\n") + "\n", "utf8");

console.log(`Initialized: ${projectDir}`);
console.log(`Prompt files: ${promptIndex.length}`);
console.log(`Missing middle images: ${missingImages.length}`);
