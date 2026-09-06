#!/usr/bin/env python3
"""Generate Menubarn mascot icons with Gemini and post-process them.

Usage:
  GOOGLE_GENERATIVE_AI_API_KEY=... python3 art/gen_icons.py            # all mascots
  GOOGLE_GENERATIVE_AI_API_KEY=... python3 art/gen_icons.py keylight   # one or more ids
  python3 art/gen_icons.py --reprocess [id ...]                        # redo post-processing from art/raw, no API calls
  python3 art/gen_icons.py --missing                                   # only ids with no art/raw/<id>.png yet

Raw 1024px output is saved to art/raw/<id>.png; the transparent 256px icon to
site/img/mascots/<id>.png. The API key comes from the environment or an untracked .env.
"""
from __future__ import annotations

import base64
import io
import json
import math
import os
import sys
import time
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


def looks_like_tile(icon: Image.Image) -> bool:
    """True when the model drew the subject on a white rounded tile: after
    background removal the icon is still mostly opaque near-white along a ring
    just inside its edge."""
    w, h = icon.size
    cx, cy, r = w / 2, h / 2, min(w, h) * 0.46
    hits = total = 0
    for k in range(64):
        ang = 2 * math.pi * k / 64
        x, y = int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang))
        rr, gg, bb, a = icon.getpixel((max(0, min(w - 1, x)), max(0, min(h - 1, y))))
        total += 1
        if a > 200 and rr > 225 and gg > 225 and bb > 225:
            hits += 1
    return hits / total > 0.5


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
    key = key.strip()
    # Keys are 'AIza…' (classic) or 'AQ.…' (newer AI Studio format); either way no whitespace.
    if len(key) < 30 or any(c.isspace() for c in key) or key.startswith(("http", "GOOGLE")):
        sys.exit(f"That does not look like a Gemini API key (got {len(key)} chars starting "
                 f"{key[:4]!r}). Check the clipboard and re-run.")
    return key


def _post(url: str, body: dict, attempts: int = 6) -> dict:
    """POST JSON; on 429 (quota/rate limit) back off and retry, since a freshly
    billed project can keep answering 429 for a few minutes while it propagates."""
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code == 429 and attempt < attempts:
                wait = 20 * attempt
                print(f"    429 from Gemini; retrying in {wait}s ({attempt}/{attempts - 1})", flush=True)
                time.sleep(wait)
                continue
            raise SystemExit(f"Gemini HTTP {e.code}: {detail}") from None
    raise AssertionError("unreachable")


def pick_model(key: str) -> str:
    """Use the preferred model if the key can see it, else the newest image model listed."""
    try:
        with urllib.request.urlopen(f"{API}/models?key={key}&pageSize=200", timeout=60) as r:
            names = [m["name"].split("/", 1)[1] for m in json.load(r).get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])]
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:600]
        raise SystemExit(f"Gemini rejected the key when listing models (HTTP {e.code}): {detail}") from None
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
    missing_only = "--missing" in argv
    ids = [a for a in argv if not a.startswith("--")]
    spec = json.loads(PROMPTS.read_text())
    mascots = {m["id"]: m for m in spec["mascots"]}
    unknown = [i for i in ids if i not in mascots]
    if unknown:
        sys.exit(f"Unknown mascot id(s): {', '.join(unknown)}. Known: {', '.join(mascots)}")
    targets = ids or list(mascots)
    if missing_only:
        targets = [t for t in targets if not (RAW_DIR / f"{t}.png").exists()]
        print(f"Missing: {', '.join(targets) or 'none'}")
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
            for attempt in range(1, 4):
                print(f"  generating {mid} ..." + (f" (attempt {attempt})" if attempt > 1 else ""), flush=True)
                raw = generate(model, key, prompt if attempt == 1 else prompt + " Sticker-style die-cut illustration with no backing shape.")
                if not looks_like_tile(postprocess(raw)):
                    break
                print(f"    {mid} came back on a white tile; regenerating", flush=True)
            raw_path.write_bytes(raw)
        icon = postprocess(raw)
        if looks_like_tile(icon):
            print(f"    warning: {mid} still looks like a tile; review it by hand", flush=True)
        icon.save(OUT_DIR / f"{mid}.png", optimize=True)
        print(f"  wrote site/img/mascots/{mid}.png")


if __name__ == "__main__":
    main(sys.argv[1:])
