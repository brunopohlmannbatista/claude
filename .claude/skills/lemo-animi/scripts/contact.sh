#!/bin/sh
# contact.sh -- take 8 evenly spaced frames from a film and tile them into a 4×2 contact sheet (make one for every version:
# check the whole first: hero in every tile, different actions, nobody leaving frame)
#
# Usage:
#   sh contact.sh <film.mp4> <out.jpg>
# 8 frames evenly between 0.2 s and end-0.2 s, each 640 wide, tiled with white gaps. For cell changes, contact and
# occlusion details use motion_check.sh.
set -eu
[ $# -eq 2 ] || { echo "usage: sh contact.sh <film.mp4> <out.jpg>"; exit 2; }
V="$1"; OUT="$2"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
for i in 0 1 2 3 4 5 6 7; do
  t=$(awk "BEGIN{printf \"%.2f\", 0.2 + ($D - 0.4) * $i / 7}")
  ffmpeg -v error -ss "$t" -i "$V" -frames:v 1 -vf scale=640:-2 "$T/$i.png"
done
ffmpeg -v error -y -start_number 0 -i "$T/%d.png" -vf tile=4x2:padding=6:color=white -frames:v 1 -q:v 4 "$OUT"
echo "$OUT"
