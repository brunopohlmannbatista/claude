#!/bin/sh
# grab_image.sh -- copy the png just made by Codex's built-in image generation into the film folder
# Codex stores generated images in ${CODEX_HOME:-~/.codex}/generated_images/<session id>/*.png.
#
# Usage:
#   sh grab_image.sh --stamp <stamp file>                  # record a time point before generating (recommended for every image)
#   (call the built-in image generation tool)
#   sh grab_image.sh <out.png> --since <stamp file>        # take only the newest image newer than the stamp; error if none, never an old image
#   sh grab_image.sh <out.png>                            # without --since: take the newest of all (says how long ago it was made)
# On success prints: output path, width×height, source file. Aspect reference: 2:1 sheet about 1774×887, 16:9 about
# 1672×941, 1:1 about 1254×1254.
# With several new images after one stamp it takes the newest and lists the others (when generating several at once,
# take them in order yourself).
set -eu
DIR="${CODEX_HOME:-$HOME/.codex}/generated_images"
usage() { echo "usage: sh grab_image.sh --stamp <stamp file> | sh grab_image.sh <out.png> [--since <stamp file>]" >&2; exit 2; }
[ $# -ge 1 ] || usage
if [ "$1" = "--stamp" ]; then
  [ $# -eq 2 ] || usage
  mkdir -p "$(dirname "$2")"
  : > "$2"; touch "$2"
  sleep 1          # file system time resolution is one second: wait a second so later images are always newer
  echo "stamp recorded: $2"
  exit 0
fi
OUT="$1"; shift; SINCE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --since) [ $# -ge 2 ] || usage; SINCE="$2"; shift 2 ;;
    *) usage ;;
  esac
done
# mtime + path of every png (GNU find has -printf; BSD/macOS uses stat -f)
list_png() {
  if find "$DIR" -maxdepth 0 -printf '' >/dev/null 2>&1; then find "$DIR" -type f -name '*.png' "$@" -printf '%T@ %p\n' 2>/dev/null
  else find "$DIR" -type f -name '*.png' "$@" -exec stat -f '%Fm %N' {} + 2>/dev/null; fi
}
fsize() { wc -c < "$1" | tr -d ' '; }
png_wh() { python3 -c 'import struct,sys; d=open(sys.argv[1],"rb").read(24); print("%d×%d" % struct.unpack(">II", d[16:24]))' "$1" 2>/dev/null || echo "?"; }
[ -d "$DIR" ] || { echo "image folder not found: ${DIR} (built-in image generation never used, or CODEX_HOME is wrong)" >&2; exit 1; }
if [ -n "$SINCE" ]; then
  [ -f "$SINCE" ] || { echo "stamp file does not exist: ${SINCE} (run sh grab_image.sh --stamp ${SINCE} first)" >&2; exit 1; }
  LIST=$(list_png -newer "$SINCE" | sort -rg || true)
  [ -n "$LIST" ] || { echo "no new image after the stamp (generation failed? or the image is still being written; wait a few seconds and retry). Old images are never taken." >&2; exit 1; }
else
  LIST=$(list_png | sort -rg || true)
  [ -n "$LIST" ] || { echo "no png at all in $DIR" >&2; exit 1; }
fi
SRC=$(echo "$LIST" | head -n 1 | cut -d' ' -f2-)
MT=$(echo "$LIST" | head -n 1 | cut -d' ' -f1)
COUNT=$(echo "$LIST" | wc -l | tr -d ' ')
# wait until the file is fully written: same size twice
S1=$(fsize "$SRC"); sleep 0.5; S2=$(fsize "$SRC")
[ "$S1" = "$S2" ] || { sleep 2; }
mkdir -p "$(dirname "$OUT")"
cp "$SRC" "$OUT"
WH=$(png_wh "$OUT")
AGE=$(( $(date +%s) - ${MT%.*} ))
echo "$OUT  $WH  (source ${SRC}, generated ${AGE} s ago)"
if [ -z "$SINCE" ] && [ "$AGE" -gt 600 ]; then echo "note: this image is ${AGE} s old and may not be the one just generated; --stamp / --since is safer" >&2; fi
if [ "$COUNT" -gt 1 ] && [ -n "$SINCE" ]; then
  echo "note: $COUNT new images after the stamp, took the newest; the others:" >&2
  echo "$LIST" | sed -n '2,6p' | cut -d' ' -f2- | sed 's/^/  /' >&2
fi
