# Model-Vision Text Extraction

## Authority

`deck_spec.json` is authoritative for every known title, label, number, note, and body sentence. Never recover known copy from a rendered design.

## Local Vision Only

When a source image contains unknown text that affects layout or meaning, inspect it directly with the model's local visual capability. Do not call PaddleOCR, Tesseract, a cloud OCR service, or `editppt` text-hint generation.

Record only transient reconstruction guidance in the page workspace:

```json
{
  "blocks": [
    {
      "id": "label-01",
      "text": "observed label",
      "source": "model_vision",
      "box_px": [120, 80, 360, 42],
      "role": "caption",
      "lines": 1,
      "confidence": "high"
    }
  ]
}
```

Use this file only to reconstruct geometry, grouping, line breaks, and unknown labels. Delete it with the other workfiles after successful delivery.

## Conflict Rule

If model-read visual text conflicts with `deck_spec.json`, keep the contract text and adapt its geometry. If the conflict changes factual meaning, block the page for content correction rather than guessing.
