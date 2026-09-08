#!/usr/bin/env python3
"""Generate the Menubarn hero/social scene with Gemini (16:9), using the same key handling as gen_icons.

Usage: python3 art/gen_scene.py [variant-count]   -> art/raw/scene-<n>.png
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from gen_icons import _key, pick_model, _post, API, RAW_DIR  # noqa: E402
import base64

PROMPT = (
    "Wide cinematic illustration, 16:9. A cozy red wooden barn at dusk on a dark hill, warm light glowing from its "
    "windows and open doors, deep indigo-to-charcoal night sky with a few stars, soft fog at the ground. Along the very "
    "top edge of the barn's roofline runs a thin dark macOS-style menu bar strip with tiny glowing colored status dots. "
    "Peeking playfully over the roof and out of the hayloft are small cartoon critters: an owl with a headset, a raccoon "
    "in a detective coat, a golden retriever, a chameleon, and a green battery character. Cartoon style with bold clean "
    "outlines and flat cel shading, matching a set of mascot icons; mostly dark, moody palette so white text can sit on "
    "top of it; no text, no letters, no watermark, no logos."
)

def main(argv):
    n = int(argv[0]) if argv else 2
    key = _key(); model = pick_model(key); print("Using model", model)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for i in range(1, n + 1):
        body = {"contents": [{"parts": [{"text": PROMPT}]}],
                "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}}
        resp = _post(f"{API}/models/{model}:generateContent?key={key}", body)
        data = next((p["inlineData"]["data"] for c in resp.get("candidates", []) for p in c.get("content", {}).get("parts", []) if p.get("inlineData")), None)
        if not data: sys.exit("no image: " + json.dumps(resp)[:300])
        out = RAW_DIR / f"scene-{i}.png"; out.write_bytes(base64.b64decode(data)); print("  wrote", out)

if __name__ == "__main__":
    main(sys.argv[1:])
