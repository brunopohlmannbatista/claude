#!/bin/sh
# motion_check.sh -- tile a run of consecutive frames from a film into a grid, to review cell changes, contact, occlusion
# and effect edges (the contact sheet contact.sh only shows 8 evenly spaced points and cannot show these)
#
# Usage:
#   sh motion_check.sh <film.mp4> <start s> <length s> <out.jpg> [fps=12] [crop=w:h:x:y]
#   e.g. sh motion_check.sh out/film.mp4 2.0 1.5 review/land.jpg            # 1.5 s from 2.0 s, 12 frames per second -> 18 tiles
#        sh motion_check.sh out/film.mp4 2.0 1.0 review/feet.jpg 24 640:360:900:600   # only the area at the feet, every frame
# Notes:
#   - fps = the film's frame rate (24) shows every frame; for a film on twos 12 gives exactly one tile per drawing.
#   - crop cuts a region in source pixels before tiling (to enlarge feet, contact shadows, occlusion edges); without crop
#     each tile is scaled to 480 wide.
#   - each tile shows time and source frame number f<n> top-left (matches the render's f%04d); at most 48 tiles, more are
#     cut off with a note.
set -eu
[ $# -ge 4 ] || { echo "usage: sh motion_check.sh <film.mp4> <start s> <length s> <out.jpg> [fps=12] [crop=w:h:x:y]" >&2; exit 2; }
V="$1"; SS="$2"; DUR="$3"; OUT="$4"; FPS="${5:-12}"; CROP="${6:-}"
command -v ffmpeg >/dev/null 2>&1 || { echo "no ffmpeg (brew install ffmpeg)" >&2; exit 1; }
[ -f "$V" ] || { echo "video not found: $V" >&2; exit 1; }
N=$(awk "BEGIN{n=int($DUR*$FPS+0.5); if(n<1)n=1; print n}")
if [ "$N" -gt 48 ]; then echo "note: $N tiles is too many, taking the first 48 (shorten the length or lower fps)" >&2; N=48; fi
COLS=$(awk "BEGIN{c=int(sqrt($N*1.6)+0.999); if(c>$N)c=$N; if(c<1)c=1; print c}")
ROWS=$(awk "BEGIN{print int(($N+$COLS-1)/$COLS)}")
VF="fps=$FPS"
if [ -n "$CROP" ]; then
  VF="$VF,crop=$CROP"
  W=$(echo "$CROP" | cut -d: -f1)
  [ "$W" -gt 480 ] && VF="$VF,scale=480:-2"
else
  VF="$VF,scale=480:-2"
fi
SRCFPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$V" 2>/dev/null | head -n 1)
[ -n "$SRCFPS" ] || SRCFPS=24/1
# select by exact frame number (no fps-filter resampling, so the paired frames of twos stay aligned): start frame START, one every STEP frames
SRC=$(awk "BEGIN{split(\"$SRCFPS\",a,\"/\"); if(a[2]==\"\")a[2]=1; print a[1]/a[2]}")
START=$(awk "BEGIN{print int($SS*$SRC+0.5)}")
STEP=$(awk "BEGIN{s=int($SRC/$FPS+0.5); if(s<1)s=1; print s}")
SEL="select='gte(n\\,$START)*not(mod(n-$START\\,$STEP))'"
VF="$SEL,${VF#fps=$FPS,}"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
ffmpeg -v error -i "$V" -vf "$VF" -fps_mode passthrough -frames:v "$N" "$T/%03d.png"
GOT=$(ls "$T" | wc -l | tr -d ' ')
[ "$GOT" -gt 0 ] || { echo "no frames extracted (start time past the end of the film?)" >&2; exit 1; }
# frame labels: ffmpeg may lack drawtext, so use Python+PIL (label if available, skip otherwise)
PYBIN="${LEMO_ANIMI_PY:-}"
[ -z "$PYBIN" ] && [ -x "${LEMO_ANIMI_HOME:-$HOME/lemo-animi-env}/venv/bin/python" ] && PYBIN="${LEMO_ANIMI_HOME:-$HOME/lemo-animi-env}/venv/bin/python"
[ -z "$PYBIN" ] && PYBIN=python3
"$PYBIN" - "$T" "$START" "$STEP" "$SRC" <<'EOF' 2>/dev/null || true
import sys, os
from PIL import Image, ImageDraw
d, start, step, src = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
for i, f in enumerate(sorted(os.listdir(d))):
    p = os.path.join(d, f); im = Image.open(p).convert('RGB'); dr = ImageDraw.Draw(im)
    n = start + i * step; lab = f'{n / src:.2f}s  f{n}'
    dr.rectangle([0, 0, 8 + 7 * len(lab), 16], fill=(0, 0, 0)); dr.text((4, 2), lab, fill=(255, 255, 0))
    im.save(p)
EOF
mkdir -p "$(dirname "$OUT")"
ffmpeg -v error -y -start_number 1 -i "$T/%03d.png" -vf "tile=${COLS}x${ROWS}:padding=4:color=white" -frames:v 1 -q:v 3 "$OUT"
echo "$OUT  ($GOT tiles, ${COLS}×${ROWS}, ${FPS} fps, from ${SS}s)"
