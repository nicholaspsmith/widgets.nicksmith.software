# Menubarn

**Where the menu-bar widgets live.** A one-page gallery of Nick Smith's
standalone macOS menu-bar apps, built on
[StatusItemKit](https://github.com/nicholaspsmith/StatusItemKit) and
[HotkeyKit](https://github.com/nicholaspsmith/HotkeyKit).

Live at https://widgets.nicksmith.software.

## Layout

- `site/` — the static page (`index.html`, `style.css`, `img/`). This is the deploy root.
- `art/` — mascot generation: `prompts.json`, `gen_icons.py`, raw outputs in `art/raw/`.
- `scripts/` — `collect-screenshots.sh` (copies screenshots in from the sibling repos under `~/Code`), `check-links.sh`.

## Regenerating a mascot

```bash
GOOGLE_GENERATIVE_AI_API_KEY=… python3 art/gen_icons.py keylight
```

Or put `GOOGLE_GENERATIVE_AI_API_KEY=…` in an untracked `.env` at the repo root.
Omit the id to regenerate everything; `--reprocess` redoes only the
background removal from `art/raw/` with no API calls. Output lands in
`site/img/mascots/`.

## Deploy

```bash
npm install
npm run deploy
```
