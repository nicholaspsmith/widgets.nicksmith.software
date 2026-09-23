#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2026 Nicholas Smith

"""Stamp the site's shared assets with a content hash so a changed file is
never served stale from a browser cache: style.css, nav.js and the hero bar
become style.css?v=<hash8> and so on in every page under site/. Idempotent;
runs as npm's predeploy step."""
import hashlib
import re
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
ASSETS = ["style.css", "nav.js", "img/hero/bar.png"]

stamps = {a: hashlib.md5((SITE / a).read_bytes()).hexdigest()[:8] for a in ASSETS}
pattern = re.compile(r'((?:\.\./)*)(' + "|".join(re.escape(a) for a in ASSETS) + r')(\?v=[0-9a-f]+)?(?=["\'])')
changed = 0
for page in SITE.rglob("*.html"):
    before = page.read_text()
    after = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}?v={stamps[m.group(2)]}", before)
    if after != before:
        page.write_text(after)
        changed += 1
print("stamped", {a: v for a, v in stamps.items()}, "in", changed, "page(s)")
