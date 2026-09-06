# Dependencies And Fallbacks

## Preferred Middle Canvas Source

Use Codex `image_gen` / image2 when available. It is the default for complex middle canvases because it gives better visual quality than script-drawn PPT boxes.

The agent must save:

- the prompt in `image2-prompts/slide-XX.md`;
- the generated image in `image2-middle/slide-XX.png`;
- the source method in `workflow-notes.md`.

## Fallback Order

1. **User-provided assets**: screenshots, report pages, PPT pages, official diagrams, product UI, architecture images.
2. **Verified public assets**: official documentation screenshots, public architecture diagrams, free-to-use images, or web-sourced visuals with citations when browsing is used.
3. **Other raster generation tools**: any available image generation tool may be used if it creates a bitmap middle canvas. Record the tool and prompt.
4. **PPT-native fallback**: use editable PPT shapes only when no raster generation or source image is available, and only when the user accepts a visually downgraded draft.

## Disclosure Rules

- Do not claim a fallback PPT-native drawing has image2 quality.
- If no image generation tool is available, ask whether to proceed with a visually downgraded draft. If proceeding, write `visual fallback` in `workflow-notes.md` and `qa/notes.txt`.
- Do not let the build script silently create missing-image placeholder slides. Missing middle canvases must block the build unless `ALLOW_VISUAL_FALLBACK=1` is explicitly set for a draft.
- Do not use speaker-only conference screenshots as the main visual unless the speaker is the subject.
- Do not present generated visuals as official evidence.

## When To Browse

Browse when the slide depends on current facts, official screenshots, product UI, public diagrams, or source attribution. Prefer official sources first, then reputable public sources, then generated visuals.
