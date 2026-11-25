#!/bin/sh
# Image adapter (experimental): lets lemo-animi generate images with a tool other than Codex, e.g. under Claude Code.
#
# Set up by the user, not the agent:
#   cp <skill>/scripts/image_adapter.example.sh ~/lemo-animi-env/image.sh   # or point LEMO_ANIMI_IMAGE_CMD at your own
#   edit it for your tool, keep keys in your environment (never in this file), then test:
#   sh <skill>/scripts/setup.sh image
# Remove ~/lemo-animi-env/image.sh to go back to Codex.
#
# Contract (gen.sh calls it once per image):
#   image.sh <prompt file> <out.png> [reference images...]      all paths absolute
#   - generate exactly one image from the full text of the prompt file; keep the prompt's meaning
#   - reference images (character sheets, an earlier background) should steer the result when the tool supports it
#   - LEMO_ANIMI_TRANSPARENT=1 means the asset needs a transparent background: ask the tool for one (RGBA PNG);
#     without real alpha the agent has to cut it out with the optional matting model, and edges get worse
#   - write a PNG to <out.png>; exit 0 on success, non-zero with a message on stderr on failure
#   - stdout/stderr go to <out>.log next to the image
# The sample films were all made with Codex's image generation; other models have not been tuned for the styles'
# prompt templates, so results may differ.
#
# Example below: an OpenAI-compatible Images API over HTTP. Needs curl and python3, and IMAGE_API_BASE and IMAGE_API_KEY in your
# environment. Check your provider's docs for the model name, sizes and the transparent-background option.
set -eu
PROMPT_FILE=$1; OUT=$2; shift 2
: "${IMAGE_API_KEY:?set IMAGE_API_KEY in your environment}"
API=${IMAGE_API_BASE:?set IMAGE_API_BASE to the API base URL of your provider, the part before /images}
MODEL=${IMAGE_MODEL:-gpt-image-1}
SIZE=${IMAGE_SIZE:-1536x1024}
BG=opaque; [ "${LEMO_ANIMI_TRANSPARENT:-0}" = 1 ] && BG=transparent
TMP=$(mktemp); trap 'rm -f "$TMP"' EXIT

if [ $# -gt 0 ]; then
  # with reference images: the edits endpoint takes them as image[] parts
  for r in "$@"; do set -- "$@" -F "image[]=@$r"; shift; done   # each path becomes -F image[]=@path (spaces are safe)
  curl -sS --fail-with-body "$API/images/edits" -H "Authorization: Bearer $IMAGE_API_KEY" \
    -F model="$MODEL" -F size="$SIZE" -F background="$BG" -F prompt="<$PROMPT_FILE" "$@" -o "$TMP"
else
  python3 -c 'import json,sys; print(json.dumps({"model":sys.argv[1],"size":sys.argv[2],"background":sys.argv[3],"prompt":open(sys.argv[4]).read()}))' \
    "$MODEL" "$SIZE" "$BG" "$PROMPT_FILE" |
  curl -sS --fail-with-body "$API/images/generations" -H "Authorization: Bearer $IMAGE_API_KEY" \
    -H "Content-Type: application/json" --data-binary @- -o "$TMP"
fi

python3 - "$TMP" "$OUT" <<'PY'
import base64, json, sys
d = json.load(open(sys.argv[1]))
try: b = d["data"][0]["b64_json"]
except (KeyError, IndexError, TypeError): sys.exit("no image in the response: " + json.dumps(d)[:400])
open(sys.argv[2], "wb").write(base64.b64decode(b))
PY
