#!/usr/bin/env bash
# Render the menu-bar glyphs from the apps' own drawing code and place them:
#   site/img/glyphs/<id>.png       state strips for the site
#   site/img/hero/bar.png          the hero bar, composed from the single states
#   ../<repo>/docs/menubar-icon.png  the same strip for each app's README
# Needs the sibling checkouts of StatusItemKit and battery-time-menubar.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../.." && pwd)"
code="$(cd "$root/.." && pwd)"
work="$here/build"; mkdir -p "$work"
cp "$code/StatusItemKit/Sources/StatusItemKit/CharacterIcon.swift" "$work/"
cp "$code/battery-time-menubar/Sources/BatteryTime/BatteryGlyph.swift" "$work/"
cp "$here/main.swift" "$work/"
(cd "$work" && swiftc -O CharacterIcon.swift BatteryGlyph.swift main.swift -o render-glyphs 2>&1 | grep -v warning || true)
(cd "$work" && ./render-glyphs)
mkdir -p "$root/site/img/glyphs"
declare -A repo=( [curtain]=menubar-curtain [keylight]=keylight-menubar [vpn-dns]=vpn-dns-menubar [process-monitor]=MacOS_Process_Monitor [battery-time]=battery-time-menubar [claude-usage]=claude-usage-menubar [macrecorder]=MacRecorder [apollo-monitor]=apollo-monitor-menubar [media-tracking-killer]=media-tracking-killer-menubar [download-recycler]=download-recycler-menubar )
for id in "${!repo[@]}"; do
  cp "$work/states-$id.png" "$root/site/img/glyphs/$id.png"
  if [ -d "$code/${repo[$id]}/docs" ]; then cp "$work/states-$id.png" "$code/${repo[$id]}/docs/menubar-icon.png"; fi
done
# The hero bar: real crops of the clock and Control Center plus the rendered glyphs.
(cd "$here" && mkdir -p render && cp "$work"/icon-*.png render/ && swift compose-bar.swift 2>&1 | grep -v -E "warning|colorspace|Unknown number" || true)
cp "$here/bar/hero-bar.png" "$root/site/img/hero/bar.png"
echo "glyphs placed"
