# Huawei Visual Style

## Visual Character

Use a disciplined internal-report style: high information density, strong grid, restrained color, real evidence, and conclusions visible in the hierarchy. The page should feel designed for technical planning and management review, not product marketing.

## Canvas And Grid

- Use 16:9 slides.
- Derive margins, title origin, footer position, and content guides from the selected page in `assets/huawei-template/PPT模板.pptx`.
- Keep left and right content boundaries stable across the deck.
- Use aligned columns, common baselines, and deliberate white space. Empty regions must separate ideas, not reveal unfinished composition.
- Prefer two-column, asymmetric split, three-column, full-width process, strong table, and large-image-plus-analysis layouts.

## Typography

- Chinese: Microsoft YaHei.
- English and numbers: Arial.
- Slide title: normally 28-30 pt, bold.
- Takeaway or lead sentence: 16-18 pt.
- Section heading: 15-17 pt.
- Body: 12-14 pt; main body must not be below 11 pt.
- Source and technical note: 9-10 pt.
- Do not scale fonts from viewport width or use negative letter spacing.

## Color

Separate base, structural and emphasis colors:

- Base: white background, dark body text, light gray secondary dividers. Keep body copy readable rather than coloring entire paragraphs.
- Structure: use a coordinated palette to distinguish categories, stages, components, ownership and chart series. Muted blue, teal and purple are a starting palette, not mandatory colors. Apply them consistently through section headings, icons, selected connectors and light tinted regions. A meaningful region may carry a light fill; it does not require an emphasis target.
- Establish a deck-level `color_system.role_colors` mapping before parallel slide design. The same role keeps the same color across pages. Peer categories use comparable saturation, brightness and coverage, so classification does not imply ranking. Pair color with labels or shapes.
- Emphasis: reserve muted red or other attention-grabbing treatment for exact `emphasis.targets` with a content-based difference, change or recommendation. “Important” and “Huawei style” alone are insufficient. Do not spread a phrase's emphasis to an entire row or tint “分析” merely as decoration.
- An absent emphasis contract means no special emphasis, not no color. A simple page may remain neutral; diagrams and comparisons should use structural color when it materially improves grouping and tracing. Neither colored area nor red frequency is a quota.
- Keep original evidence-image colors. Borrow coherent structural palettes from templates and report samples while replacing their old content and avoiding arbitrary red keywords.
- Avoid large saturated red blocks, gradients and unrelated rainbow colors. Use light fills and dark text rather than low-contrast pastel text.

## Shapes And Layout

- Use thin 0.5 pt lines and low-radius or square corners.
- Avoid heavy shadows, glass effects, glowing edges, decorative pills, and icon walls.
- Do not nest cards inside cards.
- Do not build a page from five to eight equal rounded cards when one clear composition can explain the idea.
- Use familiar icons only when they improve scanning. Decorative icons do not substitute for content.

## Evidence And Images

- Crop official screenshots to the exact evidence region; remove playback controls and unrelated desktop chrome.
- Keep screenshots readable at presentation scale and preserve aspect ratio.
- Use one dominant image rather than several unreadable thumbnails.
- Generated visuals must be marked as explanatory or scenario illustrations when that distinction matters.
- Product UI and vendor architecture evidence must come from official or user-supplied material, not an Image2 imitation.

## Information Density

Target medium-high density: the page should feel full but navigable. Use hierarchy, alignment, and grouping instead of shrinking text. A typical content page has one dominant visual and two or three concise explanatory groups. Every highlighted color, label, and border must have a specific semantic role.

## Avoid

- dashboard card walls;
- marketing hero compositions;
- abstract robots or decorative network nodes;
- speaker-only conference screenshots;
- warning boxes, red light bulbs, and alarm styling;
- unexplained red text;
- raw Excel formatting;
- visible production language such as “source PPT”, “previous version”, “prompt”, or “placeholder”.
