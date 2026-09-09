#!/usr/bin/env bash
# Verify every href/src in every page under site/: local paths must exist
# (resolved against the page's own directory), http(s) URLs must answer
# 2xx/3xx. Exit 1 on any failure.
set -uo pipefail
cd "$(dirname "$0")/.."
fail=0

while IFS= read -r html; do
  dir="$(dirname "$html")"
  refs=$(grep -oE '(href|src)="[^"]+"' "$html" | sed -E 's/^(href|src)="//; s/"$//' | sort -u)
  while IFS= read -r ref; do
    [ -z "$ref" ] && continue
    case "$ref" in
      \#*|mailto:*|data:*) continue ;;
      http://*|https://*)
        case "$ref" in https://*/*) ;; *) continue ;; esac
        code=$(curl -sIL -o /dev/null -w '%{http_code}' --max-time 20 -A "menubarn-check" "$ref")
        if [[ "$code" =~ ^[23] ]]; then echo "ok   $code $ref"; else echo "FAIL $code $ref ($html)"; fail=1; fi ;;
      /*)
        if [ -e "site$ref" ]; then echo "ok   local $ref"; else echo "FAIL missing site$ref ($html)"; fail=1; fi ;;
      *)
        target="${ref%%#*}"
        [ -z "$target" ] && continue
        if [ -e "$dir/$target" ]; then echo "ok   local $ref"; else echo "FAIL missing $dir/$target ($html)"; fail=1; fi ;;
    esac
  done <<< "$refs"
done < <(find site -name '*.html' | sort)

exit $fail
