"""Print the shape map of slide 4 in a template.

Use this if the template is updated and the canonical shape IDs in
build_deck.py (INSIGHT_SHAPE_IDS) need refreshing.

    python inspect_template.py path/to/template.pptx
"""
import sys
from pptx import Presentation
from pptx.util import Emu

if len(sys.argv) != 2:
    sys.exit("Usage: python inspect_template.py <template.pptx>")

p = Presentation(sys.argv[1])
print(f"Total slides: {len(p.slides)}\n")
for i, slide in enumerate(p.slides, start=1):
    print(f"=== Slide {i} ===")
    for shape in slide.shapes:
        left = Emu(shape.left).inches if shape.left is not None else 0
        top = Emu(shape.top).inches if shape.top is not None else 0
        w = Emu(shape.width).inches if shape.width is not None else 0
        h = Emu(shape.height).inches if shape.height is not None else 0
        text = ""
        if shape.has_text_frame:
            text = " | ".join(p.text for p in shape.text_frame.paragraphs)
            if len(text) > 70:
                text = text[:70] + "..."
        print(
            f"  id={shape.shape_id:3} {shape.name:25s} "
            f"({left:5.2f},{top:5.2f}) {w:5.2f}x{h:5.2f}  {text}"
        )
    print()
