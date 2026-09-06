#!/usr/bin/env bash
# Verify every href/src in site/index.html: local paths must exist under site/,
# http(s) URLs must answer 2xx/3xx. Exit 1 on any failure.
set -uo pipefail
cd "$(dirname "$0")/.."
html="site/index.html"
fail=0

refs=$(grep -oE '(href|src)="[^"]+"' "$html" | sed -E 's/^(href|src)="//; s/"$//' | sort -u)

while IFS= read -r ref; do
  [ -z "$ref" ] && continue
  case "$ref" in
    \#*|mailto:*|data:*) continue ;;
    http://*|https://*)
      code=$(curl -sIL -o /dev/null -w '%{http_code}' --max-time 20 -A "menubarn-check" "$ref")
      if [[ "$code" =~ ^[23] ]]; then echo "ok   $code $ref"; else echo "FAIL $code $ref"; fail=1; fi ;;
    /*)
      if [ -e "site$ref" ]; then echo "ok   local $ref"; else echo "FAIL missing site$ref"; fail=1; fi ;;
    *)
      if [ -e "site/$ref" ]; then echo "ok   local $ref"; else echo "FAIL missing site/$ref"; fail=1; fi ;;
  esac
done <<< "$refs"

exit $fail
