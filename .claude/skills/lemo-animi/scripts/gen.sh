#!/bin/zsh
# Generate one image: zsh scripts/gen.sh <prompt file> <out.png> [reference images...]
# For Claude (or any agent without built-in image generation); in Codex use the built-in image_gen instead of this script.
# Calls the Codex CLI (codex exec + its built-in image generation tool) to generate exactly one image, then fetches it
# from ~/.codex/generated_images.
# Another image tool (experimental): the user puts their own adapter at ~/lemo-animi-env/image.sh (or points
#   LEMO_ANIMI_IMAGE_CMD at one); gen.sh then calls it instead of Codex. Contract and examples: image_adapter.example.sh.
#   The agent never reads or edits the adapter or its keys, and never switches between Codex and the adapter itself.
#   Model: Codex's configured model by default; to choose one: CODEX_MODEL=<model> zsh scripts/gen.sh ...
#   Provider: CODEX_PROVIDER=<name of a [model_providers.xxx] in config.toml> zsh scripts/gen.sh ...
#   Reference images: character sheets, the previous background, etc.; Codex keeps the result consistent with them.
#   Log: <out>.log (Codex's raw output; look here on errors; not committed).
#   Timeout: waits at most GEN_TIMEOUT seconds per image (default 600); when the image service rate-limits (429) Codex
#         keeps retrying, so on timeout it stops with an error;
#         then do the parts that do not need this image first (the template renders with placeholders) and retry in a few minutes.
# Generated images are not reproducible: never delete a generated png, keep good and bad (rename bad ones with _bad).
set -e
[ $# -ge 2 ] || { echo "usage: zsh scripts/gen.sh <prompt file> <out.png> [reference images...]"; exit 2; }
P="$1"; OUT="$2"; shift 2
[ -f "$P" ] || { echo "prompt file not found: $P"; exit 2; }
mkdir -p "${OUT:A:h}"
for r in "$@"; do [ -f "$r" ] || { echo "reference image not found: $r"; exit 2; }
  case "${r:l}" in *.png|*.jpg|*.jpeg) ;; *) echo "reference must be a still PNG or JPEG: $r. Export the frame or page you mean as a PNG first."; exit 2;; esac; done
LIMIT=${GEN_TIMEOUT:-600}

# ---- the user's own image tool, when they set one up
ADAPTER="${LEMO_ANIMI_IMAGE_CMD:-${LEMO_ANIMI_HOME:-$HOME/lemo-animi-env}/image.sh}"
if [ -f "$ADAPTER" ]; then
  TR=0; grep -qi 'transparent background' "$P" && TR=1
  LOG="${OUT%.png}.log"; rm -f "$OUT"
  REFS=(); for r in "$@"; do REFS+=("${r:A}"); done
  if [ -x "$ADAPTER" ]; then RUN=("$ADAPTER"); else RUN=(sh "$ADAPTER"); fi
  LEMO_ANIMI_TRANSPARENT=$TR "${RUN[@]}" "${P:A}" "${OUT:A}" "${REFS[@]}" < /dev/null > "$LOG" 2>&1 &
  APID=$!; T=0
  while kill -0 $APID 2>/dev/null; do
    sleep 2; T=$((T + 2))
    [ $T -ge $LIMIT ] && { kill $APID 2>/dev/null; echo "image adapter: nothing after $LIMIT s, stopped (GEN_TIMEOUT adjusts it); see $LOG"; exit 1; }
  done
  wait $APID || { echo "image adapter failed (exit $?): see $LOG. Tell the user; don't open or change the adapter."; exit 1; }
  [ -s "$OUT" ] && [ "$(head -c 8 "$OUT" | od -An -tx1 | tr -d ' \n')" = "89504e470d0a1a0a" ] || { echo "image adapter wrote no PNG at $OUT: see $LOG"; exit 1; }
  CT=$(od -An -tu1 -j25 -N1 "$OUT" | tr -d ' ')
  echo "$OUT $(python3 -c 'import struct,sys; d=open(sys.argv[1],"rb").read(24); print("%d %d" % struct.unpack(">II", d[16:24]))' "$OUT" 2>/dev/null) (image adapter)"
  if [ "$TR" = 1 ] && [ "$CT" != 4 ] && [ "$CT" != 6 ]; then
    echo "warning: the prompt asks for a transparent background but this PNG has no alpha channel: cut it out with cut.py (needs sh setup.sh model) before slicing"
  fi
  exit 0
fi

# ---- default: Codex CLI
command -v codex >/dev/null || { echo "no codex command: install the Codex CLI (npm i -g @openai/codex) and log in (codex login), or set up an image adapter (image_adapter.example.sh)"; exit 2; }
M_ARGS=(); [ -n "${CODEX_MODEL:-}" ] && M_ARGS=(-m "$CODEX_MODEL")
[ -n "${CODEX_PROVIDER:-}" ] && M_ARGS+=(-c "model_provider=\"$CODEX_PROVIDER\"")
IMG_ARGS=(); for r in "$@"; do IMG_ARGS+=("--image=${r:A}"); done
REF=""; [ $# -gt 0 ] && REF=" The attached images are references; use them as the prompt says."
INSTR="You are an image generation runner. Do exactly one thing: call your built-in image generation tool once and generate exactly one image from the prompt below.${REF} Do not change the prompt's meaning, do not save, copy or process files, do not run commands; stop as soon as the image is generated.

Prompt:
$(cat "$P")"
LOG="${OUT%.png}.log"
STAMP=$(mktemp); trap 'rm -f "$STAMP"' EXIT
codex exec --json "${M_ARGS[@]}" --skip-git-repo-check -s read-only -C "${OUT:A:h}" "${IMG_ARGS[@]}" "$INSTR" < /dev/null > "$LOG" 2>&1 &
CPID=$!; T=0
while kill -0 $CPID 2>/dev/null; do
  sleep 2; T=$((T + 2))
  if [ $T -ge $LIMIT ]; then
    kill $CPID 2>/dev/null; sleep 1; kill -9 $CPID 2>/dev/null
    if grep -q '429\|Too Many Requests\|rate limit' "$LOG"; then echo "image service rate-limited (429), nothing after $LIMIT s, stopped. Do something else and generate this one in a few minutes: $P"
    else echo "nothing after $LIMIT s, stopped (GEN_TIMEOUT adjusts it); see $LOG"; fi
    exit 1
  fi
done
wait $CPID 2>/dev/null || true
TID=$(grep -o '"thread_id":"[^"]*"' "$LOG" | head -1 | cut -d'"' -f4)
SRC=""
if [ -n "$TID" ]; then
  GOT=("${CODEX_HOME:-$HOME/.codex}"/generated_images/"$TID"/*.png(N))
  [ ${#GOT} -gt 0 ] && SRC=$(ls -t "${GOT[@]}" | head -1)
fi
# If the session id is missing, fall back to the newest image that appeared after this run started
# (only when the session id is missing, so run one gen.sh at a time, not in parallel)
# When running in parallel set GEN_PARALLEL=1: a missing session id is an error instead of a guess (a guess could grab another process's image)
if [ -z "$TID" ] && [ -z "$SRC" ] && [ -z "${GEN_PARALLEL:-}" ]; then
  NEW=(${(f)"$(find "${CODEX_HOME:-$HOME/.codex}"/generated_images -name '*.png' -newer "$STAMP" 2>/dev/null)"})
  [ ${#NEW} -gt 0 ] && SRC=$(ls -t "${NEW[@]}" | head -1)
fi
[ -n "$SRC" ] || { echo "no image generated, see $LOG (common causes: not logged in, wrong model name, quota used up, prompt refused)"; exit 1; }
cp "$SRC" "$OUT"; echo "$OUT $(python3 -c 'import struct,sys; d=open(sys.argv[1],"rb").read(24); print("%d %d" % struct.unpack(">II", d[16:24]))' "$OUT" 2>/dev/null)"
