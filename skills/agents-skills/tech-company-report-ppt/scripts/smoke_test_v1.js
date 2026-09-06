#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

let pptxgen;
try {
  pptxgen = require("pptxgenjs");
} catch {
  const Module = require("module");
  const runtimeModules = process.env.CODEX_NODE_MODULES || path.join(
    process.env.USERPROFILE || process.env.HOME || "",
    ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "node", "node_modules"
  );
  process.env.NODE_PATH = [
    runtimeModules,
    path.join(runtimeModules, ".pnpm", "node_modules"),
    process.env.NODE_PATH
  ].filter(Boolean).join(path.delimiter);
  Module._initPaths();
  pptxgen = require("pptxgenjs");
}

const skillDir = path.resolve(__dirname, "..");
const exampleDir = path.join(skillDir, "examples");
const outDir = path.join(skillDir, "tmp-smoke");
fs.mkdirSync(outDir, { recursive: true });

const pngPath = path.join(exampleDir, "sample-middle-canvas.png");
if (!fs.existsSync(pngPath)) {
  const { PNG } = require("pngjs");
  const width = 1600;
  const height = 675;
  const png = new PNG({ width, height });
  function fillRect(x, y, w, h, color) {
    const [r, g, b] = color;
    for (let yy = y; yy < y + h; yy++) {
      for (let xx = x; xx < x + w; xx++) {
        const idx = (width * yy + xx) << 2;
        png.data[idx] = r;
        png.data[idx + 1] = g;
        png.data[idx + 2] = b;
        png.data[idx + 3] = 255;
      }
    }
  }
  fillRect(0, 0, width, height, [255, 255, 255]);
  fillRect(40, 40, 1520, 3, [199, 0, 11]);
  fillRect(80, 120, 1440, 80, [247, 248, 250]);
  fillRect(80, 250, 300, 250, [238, 245, 255]);
  fillRect(450, 250, 300, 250, [247, 248, 250]);
  fillRect(820, 250, 300, 250, [238, 245, 255]);
  fillRect(1190, 250, 300, 250, [247, 248, 250]);
  fillRect(80, 560, 1440, 50, [255, 241, 239]);
  fs.writeFileSync(pngPath, PNG.sync.write(png));
}

const pptxPath = path.join(outDir, "tech-company-report-ppt-smoke.pptx");
const initResult = spawnSync(process.execPath, [
  path.join(skillDir, "scripts", "init_three_zone_project.js"),
  path.join(exampleDir, "minimal-page-contract.json"),
  outDir
], { encoding: "utf8" });

if (initResult.status !== 0) {
  process.stderr.write(initResult.stderr || initResult.stdout);
  process.exit(initResult.status || 1);
}

const promptPath = path.join(outDir, "image2-prompts", "slide-03.md");
const notesPath = path.join(outDir, "workflow-notes.md");
const projectImagePath = path.join(outDir, "image2-middle", "slide-03.png");
if (!fs.existsSync(promptPath)) {
  console.error("Smoke test failed: prompt skeleton was not created.");
  process.exit(1);
}
if (!fs.existsSync(notesPath)) {
  console.error("Smoke test failed: workflow-notes.md was not created.");
  process.exit(1);
}
fs.copyFileSync(pngPath, projectImagePath);

const result = spawnSync(process.execPath, [
  path.join(skillDir, "scripts", "build_three_zone_deck.js"),
  path.join(outDir, "page-contracts.json"),
  pptxPath
], { encoding: "utf8" });

if (result.status !== 0) {
  process.stderr.write(result.stderr || result.stdout);
  process.exit(result.status || 1);
}

if (!fs.existsSync(pptxPath) || fs.statSync(pptxPath).size === 0) {
  console.error("Smoke test failed: PPTX was not created.");
  process.exit(1);
}

console.log(`Smoke test passed: ${pptxPath}`);
