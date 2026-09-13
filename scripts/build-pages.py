#!/usr/bin/env python3
"""Build one detail page per widget from its card on index.html plus its README.

    python3 scripts/build-pages.py

Reads each widget card in site/index.html (name, chips, blurb, in-bar strip
and description, menu capture, repo from data-repo), pulls the README from the
sibling checkout under ~/Code, keeps the sections a non-technical reader
wants, copies any README images into site/img/apps/<id>/, and writes
site/apps/<id>/index.html. Needs the `markdown` module
(python3 -m pip install --user --break-system-packages markdown).
"""
from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
CODE = ROOT.parent

# Repo folder under ~/Code for each widget id.
REPOS = {
    "keylight": "keylight-menubar",
    "vpn-dns": "vpn-dns-menubar",
    "barn": "menubar-barn",
    "process-monitor": "MacOS_Process_Monitor",
    "battery-time": "battery-time-menubar",
    "claude-usage": "claude-usage-menubar",
    "macrecorder": "MacRecorder",
    "apollo-monitor": "apollo-monitor-menubar",
    "media-tracking-killer": "media-tracking-killer-menubar",
    "download-recycler": "download-recycler-menubar",
    "monitor-lizard": "monitor-lizard-menubar",
}

# README sections that are for contributors, not users.
SKIP_SECTIONS = {
    "build", "run", "develop", "development", "repo layout", "standalone swift app",
    "test", "files", "layout", "license", "why not a swiftbar plugin?",
    "the menu-bar suite", "design notes", "diagnostics", "notes on the numbers",
    "the keychain", "ua watchdog", "caveats", "updates",
}
# ... unless the README has no Install section, in which case Build/Run are the install.
INSTALL_FALLBACK = {"build", "run"}

CARD_RE = re.compile(
    r'<a class="card(?: card-wide)?" href="apps/(?P<id>[a-z-]+)/" data-repo="(?P<repo>[^"]+)">\s*'
    r'<div class="card-top"><img class="mascot" src="(?P<mascot>[^"]+)"[^>]*><div><h3>(?P<name>[^<]+)</h3>'
    r'<p class="chips">(?P<chips>.*?)</p></div></div>\s*'
    r'<div class="inbar"><img src="(?P<strip>[^"]+)" alt="(?P<stripalt>[^"]*)"[^>]*><p>(?P<stripdesc>[^<]*)</p></div>\s*'
    r'<p>(?P<blurb>.*?)</p>\s*'
    r'(?:<div class="shot(?: shot-icon)?"><img src="(?P<shot>[^"]+)" alt="(?P<shotalt>[^"]*)"[^>]*></div>\s*)?'
    r'</a>',
    re.S,
)


def cards() -> list[dict]:
    src = (SITE / "index.html").read_text()
    found = [m.groupdict() for m in CARD_RE.finditer(src)]
    missing = set(REPOS) - {c["id"] for c in found}
    if missing:
        raise SystemExit(f"cards not parsed for: {sorted(missing)}")
    return found


def split_sections(md: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (intro, [(heading, body), ...]) split on '## ' headings."""
    parts = re.split(r"^## (.+)$", md, flags=re.M)
    intro = parts[0]
    sections = [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]
    return intro, sections


def clean_intro(intro: str) -> str:
    # Drop the centred mascot/title block, the H1, the Menubarn line and the
    # menu screenshot: the page shows all of those itself.
    intro = re.sub(r"<h1[^>]*>.*?</h1>", "", intro, flags=re.S)
    intro = re.sub(r'<p align="center">.*?</p>', "", intro, flags=re.S)
    intro = re.sub(r"^# .*$", "", intro, flags=re.M)
    intro = re.sub(r"^!\[[^\]]*\]\([^)]*menu\.png\)\s*$", "", intro, flags=re.M)
    intro = re.sub(r"\s*Part of the\s+\[Menubarn\]\([^)]*\)\s+widget\s+library\.", "", intro)
    intro = re.sub(r"\n{3,}", "\n\n", intro)
    return intro.strip()


def rewrite_assets(md: str, wid: str, repo: str) -> str:
    """Copy README-relative images into the site and point links at GitHub."""
    repo_dir = CODE / repo
    out_dir = SITE / "img" / "apps" / wid
    gh = f"https://github.com/nicholaspsmith/{repo}/blob/main/"

    def copy_image(rel: str) -> str:
        src = repo_dir / rel
        if not src.is_file():
            return gh.replace("/blob/", "/raw/") + rel
        out_dir.mkdir(parents=True, exist_ok=True)
        dest = out_dir / src.name
        shutil.copyfile(src, dest)
        return f"../../img/apps/{wid}/{src.name}"

    def is_relative(p: str) -> bool:
        return not re.match(r"^(https?:|mailto:|#|/)", p)

    md = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)",
                lambda m: f"![{m.group(1)}]({copy_image(m.group(2)) if is_relative(m.group(2)) else m.group(2)})", md)
    md = re.sub(r'<img([^>]*?)src="([^"]+)"',
                lambda m: f'<img{m.group(1)}src="{copy_image(m.group(2)) if is_relative(m.group(2)) else m.group(2)}"', md)
    md = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)\)",
                lambda m: f"[{m.group(1)}]({gh + m.group(2) if is_relative(m.group(2)) else m.group(2)})", md)
    return md


def readme_html(wid: str, repo: str) -> str:
    path = CODE / repo / "README.md"
    if not path.is_file():
        raise SystemExit(f"no README at {path}")
    intro, sections = split_sections(path.read_text())
    headings = {h.lower() for h, _ in sections}
    skip = set(SKIP_SECTIONS)
    if "install" not in headings:
        skip -= INSTALL_FALLBACK
    kept = [(h, b) for h, b in sections if h.lower() not in skip]
    md = clean_intro(intro) + "\n\n" + "\n\n".join(f"## {h}\n{b}" for h, b in kept)
    # The page already shows the in-bar strip above, so drop the README's copy.
    md = re.sub(r"^!\[The menu-bar icon\]\([^)]*\)\s*$", "", md, flags=re.M)
    md = rewrite_assets(md, wid, repo)
    # Anchor the Install section so the hero button can jump to it.
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    body = re.sub(r"<h2>(Install|Build)</h2>", r'<h2 id="install">\1</h2>', body, count=1)
    return body


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{name} — Menubarn</title>
  <meta name="description" content="{blurb_text}">
  <meta name="theme-color" content="#0b0d12">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{name} — Menubarn">
  <meta property="og:description" content="{blurb_text}">
  <meta property="og:image" content="https://widgets.nicksmith.software/{mascot}">
  <meta property="og:url" content="https://widgets.nicksmith.software/apps/{id}/">
  <meta name="twitter:card" content="summary">
  <link rel="icon" href="../../favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
  <link rel="stylesheet" href="../../style.css">
</head>
<body>

<header class="nav">
  <a class="brand" href="../../" aria-label="Menubarn home">
    <img src="../../img/mascots/menubarn.png" alt="" width="28" height="28">
    <span>Menubarn</span>
  </a>
  <nav class="nav-links" aria-label="Sections">
    <a href="../../#widgets">All widgets</a>
    <a class="btn btn-ghost" href="#install">Install</a>
  </nav>
</header>

<main id="top">
<section class="hero app-hero">
  <div class="hero-bg" aria-hidden="true"></div>
  <div class="app-hero-inner">
    <img class="app-mascot" src="../../{mascot}" alt="The {name} mascot" width="220" height="220">
    <div>
      <p class="eyebrow">A Menubarn widget</p>
      <h1>{name}</h1>
      <p class="lede">{blurb}</p>
      <p class="chips">{chips}</p>
      <div class="cta">
        <a class="btn btn-primary" href="#install">Install</a>
        <a class="btn btn-ghost" href="{repo}">Source on GitHub</a>
      </div>
    </div>
  </div>
</section>

<section class="section app-section">
  <div class="app-glance">
    <div class="glance">
      <h2>In the menu bar</h2>
      <img class="glance-strip" src="../../{strip}" alt="{stripalt}">
      <p>{stripdesc}</p>
    </div>
    {shot_block}
  </div>
</section>

<section class="section app-section">
  <article class="prose">
{readme}
  </article>
</section>
</main>

<footer>
  <p>Made by <a href="https://nicksmith.software">Nick Smith</a></p>
</footer>

</body>
</html>
"""

SHOT = """<div class="glance">
      <h2>The menu</h2>
      <img class="glance-shot" src="../../{shot}" alt="{shotalt}">
    </div>"""


def build() -> None:
    for c in cards():
        wid = c["id"]
        repo_url = c["repo"]
        repo = REPOS[wid]
        blurb_text = html.unescape(re.sub(r"<[^>]+>", "", c["blurb"]))
        page = PAGE.format(
            id=wid,
            name=c["name"],
            blurb=c["blurb"],
            blurb_text=html.escape(blurb_text, quote=True),
            mascot=c["mascot"],
            chips=c["chips"],
            repo=repo_url,
            strip=c["strip"],
            stripalt=c["stripalt"],
            stripdesc=c["stripdesc"],
            shot_block=SHOT.format(shot=c["shot"], shotalt=c["shotalt"]) if c.get("shot") else "",
            readme=readme_html(wid, repo),
        )
        out = SITE / "apps" / wid / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page)
        print(f"wrote site/apps/{wid}/index.html")


if __name__ == "__main__":
    build()
