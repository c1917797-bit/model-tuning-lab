#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

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

const [specPath, outPath] = process.argv.slice(2);
if (!specPath || !outPath) {
  console.error("Usage: build_three_zone_deck.js <page-contracts.json> <output.pptx>");
  process.exit(2);
}

const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const specDir = path.dirname(path.resolve(specPath));

const pptx = new pptxgen();
pptx.defineLayout({ name: "THREE_ZONE_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "THREE_ZONE_WIDE";
pptx.author = "Codex";
pptx.company = "Internal";
pptx.subject = spec.meta?.title || "Technology company report";
pptx.title = spec.meta?.title || "Technology company report";
pptx.lang = spec.meta?.language === "zh" ? "zh-CN" : "en-US";
pptx.theme = {
  headFontFace: spec.meta?.language === "zh" ? "Microsoft YaHei" : "Arial",
  bodyFontFace: spec.meta?.language === "zh" ? "Microsoft YaHei" : "Arial",
  lang: pptx.lang
};

const W = 13.333;
const H = 7.5;
const C = {
  red: "C7000B",
  blue: "115CAA",
  black: "1D1D1A",
  body: "4D4D4D",
  gray: "BFBFBF",
  light: "F7F8FA",
  paleRed: "FFF1EF",
  white: "FFFFFF"
};

function asText(value) {
  return value == null ? "" : String(value);
}

function resolveImage(imagePath) {
  if (!imagePath) return null;
  if (path.isAbsolute(imagePath)) return imagePath;
  return path.resolve(specDir, imagePath);
}

function addText(slide, text, x, y, w, h, opts = {}) {
  slide.addText(asText(text), {
    x, y, w, h,
    fontFace: opts.fontFace || (spec.meta?.language === "zh" ? "Microsoft YaHei" : "Arial"),
    fontSize: opts.fontSize || 12,
    bold: Boolean(opts.bold),
    color: opts.color || C.black,
    align: opts.align || "left",
    valign: opts.valign || "mid",
    margin: opts.margin ?? 0.03,
    fit: opts.fit || "shrink",
    breakLine: false
  });
}

function addTitle(slide, title) {
  addText(slide, title, 0.55, 0.28, 11.9, 0.43, { fontSize: 22, bold: true, color: C.red });
  slide.addShape(pptx.ShapeType.line, { x: 0.55, y: 0.86, w: 12.25, h: 0, line: { color: C.gray, width: 0.8 } });
}

function addConclusion(slide, text) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.55, y: 6.58, w: 12.25, h: 0.58,
    rectRadius: 0.06,
    fill: { color: C.white },
    line: { color: "D7DCE2", width: 0.7 }
  });
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 0.74, y: 6.74, w: 0.62, h: 0.24,
    rectRadius: 0.05,
    fill: { color: C.blue },
    line: { color: C.blue, transparency: 100 }
  });
  addText(slide, "Insight", 0.78, 6.76, 0.54, 0.16, { fontSize: 7, bold: true, color: C.white, align: "center" });
  addText(slide, text, 1.52, 6.70, 10.9, 0.28, { fontSize: 11, bold: true, color: C.black });
}

function addMiddleImage(slide, imagePath) {
  const resolved = resolveImage(imagePath);
  if (!resolved || !fs.existsSync(resolved)) {
    if (process.env.ALLOW_VISUAL_FALLBACK !== "1") {
      throw new Error(`Missing middle canvas image: ${imagePath || "(empty)"}. Generate image2-middle assets before building, or set ALLOW_VISUAL_FALLBACK=1 for an explicitly downgraded draft.`);
    }
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 0.45, y: 1.02, w: 12.45, h: 5.25,
      rectRadius: 0.04,
      fill: { color: C.light },
      line: { color: "D7DCE2", width: 0.7 }
    });
    addText(slide, "Visual fallback: missing middle canvas image", 0.45, 3.35, 12.45, 0.3, { fontSize: 16, color: C.body, align: "center" });
    return;
  }
  slide.addImage({ path: resolved, x: 0.45, y: 1.02, w: 12.45, h: 5.25 });
}

function cover(slide, s) {
  slide.background = { color: C.white };
  slide.addShape(pptx.ShapeType.line, { x: 0.75, y: 1.36, w: 11.85, h: 0, line: { color: C.gray, width: 0.8 } });
  addText(slide, s.title || spec.meta?.title, 0.75, 1.7, 10.8, 0.75, { fontSize: 34, bold: true, color: C.red });
  addText(slide, s.subtitle || spec.meta?.subtitle || "", 0.78, 2.6, 9.5, 0.35, { fontSize: 16, color: C.body });
  const cards = s.cards || ["Clear storyline", "Image2 middle canvas", "Editable conclusions"];
  cards.slice(0, 3).forEach((card, i) => {
    const x = 0.8 + i * 4.0;
    slide.addShape(pptx.ShapeType.roundRect, { x, y: 4.2, w: 3.45, h: 0.9, rectRadius: 0.05, fill: { color: C.light }, line: { color: "D7DCE2", width: 0.6 } });
    addText(slide, card, x + 0.18, 4.43, 3.1, 0.22, { fontSize: 11, bold: true, color: C.red, align: "center" });
  });
}

function agenda(slide, s) {
  addTitle(slide, s.title || "Agenda");
  const items = s.items || [];
  const current = s.current || items[0];
  items.forEach((item, i) => {
    const y = 1.35 + i * 0.66;
    const active = item === current || String(item).includes(String(current));
    slide.addShape(pptx.ShapeType.roundRect, {
      x: 1.35, y, w: 10.55, h: 0.46,
      rectRadius: 0.04,
      fill: { color: active ? C.paleRed : C.light },
      line: { color: active ? C.red : "D7DCE2", width: active ? 1.1 : 0.6 }
    });
    addText(slide, String(i + 1).padStart(2, "0"), 1.62, y + 0.12, 0.45, 0.16, { fontSize: 9, bold: true, color: active ? C.red : C.body });
    addText(slide, item, 2.25, y + 0.1, 8.9, 0.2, { fontSize: 12, bold: active, color: active ? C.red : C.black });
  });
}

function standard(slide, s) {
  addTitle(slide, s.title);
  addMiddleImage(slide, s.middleImage);
  addConclusion(slide, s.bottomConclusion || s.conclusion || "");
}

function tablePage(slide, s) {
  addTitle(slide, s.title);
  const columns = s.columns || [];
  const rows = s.rows || [];
  const tableRows = [columns, ...rows];
  if (!columns.length || !rows.length) {
    addMiddleImage(slide, s.middleImage);
  } else {
    const styledRows = tableRows.map((row, rowIndex) => row.map((value, colIndex) => {
      if (rowIndex === 0) {
        return {
          text: asText(value),
          options: {
            fill: { color: colIndex === 0 ? C.red : C.blue },
            color: C.white,
            bold: true,
            align: "center"
          }
        };
      }
      return {
        text: asText(value),
        options: {
          fill: { color: rowIndex % 2 ? C.white : C.light },
          color: colIndex === row.length - 1 ? C.red : C.black,
          bold: colIndex === row.length - 1
        }
      };
    }));
    slide.addTable(styledRows, {
      x: 0.55, y: 1.15, w: 12.25, h: 5.0,
      border: { color: "D7DCE2", pt: 0.6 },
      margin: 0.05,
      fontFace: spec.meta?.language === "zh" ? "Microsoft YaHei" : "Arial",
      fontSize: 8.5,
      color: C.black,
      valign: "mid",
      fit: "shrink",
      fill: { color: C.white }
    });
  }
  addConclusion(slide, s.bottomConclusion || s.conclusion || "");
}

for (const s of spec.slides || []) {
  const slide = pptx.addSlide();
  slide.background = { color: C.white };
  const type = s.type || "standard";
  if (type === "cover") cover(slide, s);
  else if (type === "agenda" || type === "section") agenda(slide, s);
  else if (type === "table" || type === "opportunity") tablePage(slide, s);
  else standard(slide, s);
}

pptx.writeFile({ fileName: outPath });
