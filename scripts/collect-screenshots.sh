#!/usr/bin/env bash
# Copy screenshots from the sibling widget repos under ~/Code into site/img/screens/
# so the site never depends on those repos at deploy time. Re-run any time.
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="$HOME/Code"
DST="site/img/screens"

copy() { # copy <dest-relative> <source-relative>
  mkdir -p "$DST/$(dirname "$1")"
  cp "$SRC/$2" "$DST/$1"
  echo "  $1"
}

echo "Collecting screenshots into $DST"
copy vpn-dns/menu.png               vpn-dns-menubar/screenshots/menu.png
copy vpn-dns/connected.png          vpn-dns-menubar/screenshots/menubar-connected.png
copy vpn-dns/connecting.png         vpn-dns-menubar/screenshots/menubar-connecting.png
copy vpn-dns/blocked.png            vpn-dns-menubar/screenshots/menubar-blocked.png
copy vpn-dns/off.png                vpn-dns-menubar/screenshots/menubar-off.png
copy barn/icon.png                  menubar-barn/docs/images/icon.png
copy barn/panel.png                 menubar-barn/docs/images/panel.png
copy process-monitor/arc.png        MacOS_Process_Monitor/screenshots/menubar-mode-arc.png
copy process-monitor/gauge.png      MacOS_Process_Monitor/screenshots/menubar-mode-gauge.png
copy process-monitor/pie.png        MacOS_Process_Monitor/screenshots/menubar-mode-pie.png
copy process-monitor/wedge.png      MacOS_Process_Monitor/screenshots/menubar-mode-wedge.png
copy process-monitor/sev-orange.png MacOS_Process_Monitor/screenshots/menubar-sev-orange.png
copy process-monitor/sev-red.png    MacOS_Process_Monitor/screenshots/menubar-sev-red.png
copy battery-time/charging.png      battery-time-menubar/screenshots/menubar-charging.png
copy battery-time/discharging.png   battery-time-menubar/screenshots/menubar-discharging.png
copy battery-time/low.png           battery-time-menubar/screenshots/menubar-low.png
copy claude-usage/menu.png          claude-usage-menubar/screenshots/menu.png
copy apollo-monitor/menu.png        apollo-monitor-menubar/screenshots/menu.png
copy apollo-monitor/menubar-icon.png apollo-monitor-menubar/docs/menubar-icon.png

# MacRecorder only ships an .icns; extract a 256px PNG from it.
mkdir -p "$DST/macrecorder"
sips -s format png -z 256 256 "$SRC/MacRecorder/Resources/bundle/AppIcon.icns" \
  --out "$DST/macrecorder/app-icon.png" >/dev/null
echo "  macrecorder/app-icon.png"
echo "Done."
