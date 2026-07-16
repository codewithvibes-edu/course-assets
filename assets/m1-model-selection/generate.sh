#!/usr/bin/env bash
# Regenerate one-pager.pdf from one-pager.html using headless Chrome/Chromium.
# Usage: ./generate.sh
set -euo pipefail
cd "$(dirname "$0")"

find_chrome() {
  local candidates=(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
    "$(command -v google-chrome || true)"
    "$(command -v chromium || true)"
    "$(command -v chromium-browser || true)"
  )
  for c in "${candidates[@]}"; do
    [ -n "$c" ] && [ -x "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

CHROME="$(find_chrome)" || { echo "No Chrome/Chromium found" >&2; exit 1; }

"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$(pwd)/one-pager.pdf" \
  "file://$(pwd)/one-pager.html"

echo "Wrote one-pager.pdf"
