# Menubarn

**Where the menu-bar widgets live.** A one-page gallery of Nick Smith's
standalone macOS menu-bar apps, built on
[StatusItemKit](https://github.com/nicholaspsmith/StatusItemKit) and
[HotkeyKit](https://github.com/nicholaspsmith/HotkeyKit).

Live at https://widgets.nicksmith.software.

## Layout

- `site/` — the static site (`index.html`, `style.css`, `img/`, and one generated page per widget under `apps/<id>/`). This is the deploy root.
- `art/` — mascot generation: `prompts.json`, `gen_icons.py`, raw outputs in `art/raw/`; `art/glyphs/` renders the menu-bar glyph strips and the hero bar from the apps' own drawing code (`render-glyphs.sh`).
- `scripts/` — `build-pages.py` (one detail page per widget from its card plus its README in the sibling checkout), `collect-screenshots.sh` (copies screenshots in from the sibling repos under `~/Code`), `check-links.sh` (every page).
- `docs/` — plans, e.g. the GUI installer.

## Rebuilding the widget pages

```bash
python3 scripts/build-pages.py     # needs: python3 -m pip install --user --break-system-packages markdown
```

Run it after editing a card on `index.html` or any app's README; it reads both.

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
