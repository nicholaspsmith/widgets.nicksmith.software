#!/usr/bin/env python3
"""Generate Menubarn mascot icons with Gemini and post-process them.

Usage:
  GOOGLE_GENERATIVE_AI_API_KEY=... python3 art/gen_icons.py            # all mascots
  GOOGLE_GENERATIVE_AI_API_KEY=... python3 art/gen_icons.py keylight   # one or more ids
  python3 art/gen_icons.py --reprocess [id ...]                        # redo post-processing from art/raw, no API calls

Raw 1024px output is saved to art/raw/<id>.png; the transparent 256px icon to
site/img/mascots/<id>.png. The API key is read from the environment only.
"""
from __future__ import annotations

import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "art" / "prompts.json"
RAW_DIR = ROOT / "art" / "raw"
OUT_DIR = ROOT / "site" / "img" / "mascots"
API = "https://generativelanguage.googleapis.com/v1beta"
PREFERRED_MODEL = "gemini-2.5-flash-image"


# ---------- post-processing (pure, tested) ----------

def postprocess(raw_png: bytes, size: int = 256, tolerance: int = 40, pad_ratio: float = 0.06) -> Image.Image:
    """White background -> transparent, trim to content, pad, square, resize."""
    im = Image.open(io.BytesIO(raw_png)).convert("RGBA")
    w, h = im.size
    # Flood-fill the background from every corner. The white the model paints is
    # not always exactly #FFFFFF, so allow a tolerance (sum of per-band deltas).
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if im.getpixel(seed)[3] != 0:
            ImageDraw.floodfill(im, seed, (0, 0, 0, 0), thresh=tolerance)
    bbox = im.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("post-processing removed everything; is the background not white?")
    im = im.crop(bbox)
    # Pad, then square up around the centre.
    cw, ch = im.size
    pad = int(max(cw, ch) * pad_ratio)
    side = max(cw, ch) + 2 * pad
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - cw) // 2, (side - ch) // 2))
    return canvas.resize((size, size), Image.LANCZOS)


# ---------- Gemini call ----------

def _key() -> str:
    """The API key: from the environment, else from an untracked .env at the repo root."""
    key = os.environ.get("GOOGLE_GENERATIVE_AI_API_KEY")
    env_file = ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("GOOGLE_GENERATIVE_AI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("'\"")
    if not key:
        sys.exit("GOOGLE_GENERATIVE_AI_API_KEY is not set. Export it (or put it in .env) and re-run.")
    return key


def _post(url: str, body: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        raise SystemExit(f"Gemini HTTP {e.code}: {detail}") from None


def pick_model(key: str) -> str:
    """Use the preferred model if the key can see it, else the newest image model listed."""
    with urllib.request.urlopen(f"{API}/models?key={key}&pageSize=200", timeout=60) as r:
        names = [m["name"].split("/", 1)[1] for m in json.load(r).get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
    if PREFERRED_MODEL in names:
        return PREFERRED_MODEL
    image_models = sorted(n for n in names if "image" in n.lower())
    if not image_models:
        sys.exit("No image-capable Gemini model is available to this key.")
    return image_models[-1]


def generate(model: str, key: str, prompt: str) -> bytes:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    resp = _post(f"{API}/models/{model}:generateContent?key={key}", body)
    for cand in resp.get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            data = part.get("inlineData", {}).get("data")
            if data:
                return base64.b64decode(data)
    raise SystemExit(f"No image in response: {json.dumps(resp)[:400]}")


# ---------- CLI ----------

def main(argv: list[str]) -> None:
    reprocess = "--reprocess" in argv
    ids = [a for a in argv if not a.startswith("--")]
    spec = json.loads(PROMPTS.read_text())
    mascots = {m["id"]: m for m in spec["mascots"]}
    unknown = [i for i in ids if i not in mascots]
    if unknown:
        sys.exit(f"Unknown mascot id(s): {', '.join(unknown)}. Known: {', '.join(mascots)}")
    targets = ids or list(mascots)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    model = key = None
    if not reprocess:
        key = _key()
        model = pick_model(key)
        print(f"Using model {model}")

    for mid in targets:
        raw_path = RAW_DIR / f"{mid}.png"
        if reprocess:
            if not raw_path.exists():
                print(f"  skip {mid}: no raw image")
                continue
            raw = raw_path.read_bytes()
        else:
            prompt = f"{spec['style']} Subject: {mascots[mid]['subject']}."
            print(f"  generating {mid} ...", flush=True)
            raw = generate(model, key, prompt)
            raw_path.write_bytes(raw)
        icon = postprocess(raw)
        icon.save(OUT_DIR / f"{mid}.png", optimize=True)
        print(f"  wrote site/img/mascots/{mid}.png")


if __name__ == "__main__":
    main(sys.argv[1:])
