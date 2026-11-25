#!/bin/sh
# setup.sh -- prepare the lemo-animi runtime (POSIX sh, macOS / Linux)
#
# Usage:
#   sh setup.sh          # check ffmpeg and Python -> reuse what is already installed (a system Python that has every
#                        # dependency, an earlier venv, samples already downloaded), make the venv and install deps only if needed -> download instrument samples -> print the Python to use (no cut-out model)
#   sh setup.sh start    # check; if anything is missing, start the full install (as plain sh setup.sh)
#                        # in the background and return at once (log: $LEMO_ANIMI_HOME/setup.log). Run plain sh setup.sh to wait:
#                        # it waits for the background install, then finishes or reports what failed
#   sh setup.sh check    # check only, install / download nothing (exit 1 if something is missing; a missing cut-out model does not count)
#   sh setup.sh python   # only print the Python to use (exit 1 if the env is not ready); this is $PY in commands
#   sh setup.sh model    # download the cut-out model (optional, ~0.97 GB). Assets are generated as transparent PNGs by default
#                        # and do not need it;
#                        # only needed when transparency fails (an asset cannot be generated with a clean transparent edge)
#   sh setup.sh instruments  # only download the instrument samples for the score (~1.4 GB; plain sh setup.sh downloads them too)
#   sh setup.sh all      # all of the above
#   sh setup.sh image    # which image tool gen.sh uses (Codex, or the user's adapter), then generate one small test image
#                        # with a transparent background and check it (for agents without built-in image generation)
# Environment variables:
#   LEMO_ANIMI_HOME    env folder, default ~/lemo-animi-env (venv at $LEMO_ANIMI_HOME/venv)
#   LEMO_ANIMI_MODELS  model folder, default $LEMO_ANIMI_HOME/models
#   LEMO_ANIMI_PYTHON  Python used to make the venv (default: first of 3.13 / 3.12 / 3.11 / uv / python3)
#   LEMO_ANIMI_IMAGE_CMD  the user's image adapter for gen.sh (default $LEMO_ANIMI_HOME/image.sh when it exists)
# Deps: pillow numpy opencv-python-headless onnxruntime; cut-out model BiRefNet-general (~0.97 GB).
# Model lookup order matches cut.py: $LEMO_ANIMI_MODELS -> $LEMO_ANIMI_HOME/models -> ~/.rembg/models/birefnet-general/;
#   never downloaded twice. Downloads use curl with resume (re-running this script continues after an interruption).
# Offline: sh setup.sh still makes the venv (installing packages needs PyPI) and prints the Python, then exits 1 because
# the instrument samples are missing (the env works for everything but the score); run sh setup.sh instruments once online.
# Agents without built-in image generation (such as Claude) also need the Codex CLI (npm i -g @openai/codex, codex login)
# for gen.sh; check reports it.
set -eu

MODE="${1:-env}"
case "$MODE" in env|all|start|check|python|model|instruments|image) ;; *) echo "usage: sh setup.sh [start|check|python|model|instruments|image|all]" >&2; exit 2 ;; esac
HERE="$(cd "$(dirname "$0")" && pwd)"
HOME_DIR="${LEMO_ANIMI_HOME:-$HOME/lemo-animi-env}"
VENV="$HOME_DIR/venv"
MODELS="${LEMO_ANIMI_MODELS:-$HOME_DIR/models}"
MODEL_URL="${LEMO_ANIMI_MODEL_URL:-https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx}"
MODEL_SIZE="${LEMO_ANIMI_MODEL_SIZE:-972666916}"
PKGS="pillow numpy opencv-python-headless onnxruntime scipy soundfile soxr edge-tts"
MISSING=0

say() { printf '%s\n' "$*"; }
warn() { printf '! %s\n' "$*" >&2; }
fsize() { if stat -f %z "$1" >/dev/null 2>&1; then stat -f %z "$1"; else stat -c %s "$1"; fi; }

# ---------------- ffmpeg ----------------
check_ffmpeg() {
  if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
    say "ffmpeg: $(ffmpeg -version 2>/dev/null | head -n 1 | cut -d' ' -f1-3)"
  else
    warn "no ffmpeg / ffprobe: brew install ffmpeg on macOS, the package manager on Linux (needed for encoding films, contact sheets, review)"
    MISSING=1
  fi
}

# ---------------- Python ----------------
py_ver() { "$1" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || true; }
pick_python() {
  if [ -n "${LEMO_ANIMI_PYTHON:-}" ]; then echo "$LEMO_ANIMI_PYTHON"; return; fi
  for c in python3.13 python3.12 python3.11; do
    if command -v "$c" >/dev/null 2>&1; then command -v "$c"; return; fi
  done
  if command -v uv >/dev/null 2>&1; then echo "uv"; return; fi
  if command -v python3 >/dev/null 2>&1; then
    v=$(py_ver python3)
    case "$v" in 3.1[1-3]) command -v python3; return ;; esac
    warn "python3 is $v: onnxruntime may have no wheel for it; install 3.11–3.13 or uv (brew install uv)"
    command -v python3; return
  fi
  echo ""
}

has_deps() { [ -n "$1" ] && "$1" -c 'import cv2, numpy, PIL, onnxruntime, scipy, soundfile, soxr, edge_tts' >/dev/null 2>&1; }
venv_ok() { [ -x "$VENV/bin/python" ] && has_deps "$VENV/bin/python"; }
# a Python already on this system with every dependency is used as is: nothing is installed for it
system_py() {
  if [ -n "${LEMO_ANIMI_PYTHON:-}" ] && has_deps "$LEMO_ANIMI_PYTHON"; then echo "$LEMO_ANIMI_PYTHON"; return 0; fi
  for c in python3.13 python3.12 python3.11 python3; do
    p=$(command -v "$c" 2>/dev/null) || continue
    if has_deps "$p"; then echo "$p"; return 0; fi
  done
  return 1
}
# the Python every command uses: the lemo-animi venv when it is complete, else a complete system Python
env_py() { if venv_ok; then echo "$VENV/bin/python"; else system_py; fi; }

make_venv() {
  P=$(pick_python)
  [ -n "$P" ] || { warn "no Python 3 (and no uv): install python3.12 or uv and re-run"; exit 1; }
  mkdir -p "$HOME_DIR"
  if [ ! -x "$VENV/bin/python" ]; then
    if [ "$P" = "uv" ]; then
      say "making venv with uv (Python 3.12): $VENV"
      uv venv -q -p 3.12 "$VENV"
    else
      say "making venv with ${P} ($(py_ver "$P")): $VENV"
      "$P" -m venv "$VENV"
    fi
  fi
  say "installing deps: $PKGS"
  if command -v uv >/dev/null 2>&1; then
    uv pip install -q --python "$VENV/bin/python" $PKGS
  else
    "$VENV/bin/python" -m pip install -q --upgrade pip
    "$VENV/bin/python" -m pip install -q $PKGS
  fi
  venv_ok || { warn "deps installed but import fails; see the errors above (common: Python too new, no onnxruntime wheel)"; exit 1; }
}

# ---------------- model ----------------
find_model() {
  for p in ${LEMO_ANIMI_MODELS:+"$LEMO_ANIMI_MODELS/birefnet-general.onnx"} \
           "$HOME_DIR/models/birefnet-general.onnx" \
           "$HOME/.rembg/models/birefnet-general/birefnet-general.onnx"; do
    if [ -f "$p" ]; then echo "$p"; return; fi
  done
  echo ""
}

get_model() {
  M=$(find_model)
  if [ -n "$M" ]; then
    s=$(fsize "$M")
    if [ "$s" != "$MODEL_SIZE" ]; then warn "model $M is $s bytes, expected $MODEL_SIZE (another version or incomplete download? use it if it works)"; fi
    say "cut-out model: $M"
    return
  fi
  if [ "$MODE" = "check" ] || [ "$MODE" = "env" ]; then say "cut-out model: none (optional; not needed when assets are generated as transparent PNGs. To use it: sh setup.sh model, ~0.97 GB)"; return; fi
  command -v curl >/dev/null 2>&1 || { warn "no curl, cannot download the model"; exit 1; }
  mkdir -p "$MODELS"
  DST="$MODELS/birefnet-general.onnx"; PART="$DST.part"
  say "downloading the cut-out model (~0.97 GB, interruptible, re-run resumes) -> $DST"
  curl -fL --retry 3 -C - -o "$PART" "$MODEL_URL" || { warn "download interrupted; re-run sh setup.sh to resume"; exit 1; }
  s=$(fsize "$PART")
  if [ "$s" != "$MODEL_SIZE" ]; then warn "downloaded size $s differs from expected $MODEL_SIZE: delete $PART and download again"; exit 1; fi
  mv "$PART" "$DST"
  say "cut-out model: $DST"
  if [ -n "${LEMO_ANIMI_MODELS:-}" ] || [ "$MODELS" = "$HOME_DIR/models" ]; then :; else
    say "(cut.py must be able to find it: export LEMO_ANIMI_MODELS=${MODELS})"
  fi
}

# ---------------- main ----------------
INSTR_OK=1
get_instruments() {
  PYI=$(env_py) || PYI=python3
  if [ "$MODE" = "check" ]; then "$PYI" "$HERE/audio/fetch_instruments.py" --check || MISSING=1; return; fi
  "$PYI" "$HERE/audio/fetch_instruments.py" || { INSTR_OK=0; warn "instrument samples (~1.4 GB) not fully downloaded: the score needs them. Once online, sh setup.sh instruments resumes"; }
}
ADAPTER="${LEMO_ANIMI_IMAGE_CMD:-$HOME_DIR/image.sh}"
check_codex() {
  if [ -f "$ADAPTER" ]; then say "images: your adapter $ADAPTER (gen.sh uses it instead of Codex; experimental; sh setup.sh image tests it)"; return; fi
  if command -v codex >/dev/null 2>&1; then say "codex: $(command -v codex) (agents without built-in image generation, such as Claude, generate images with gen.sh)"
  else say "codex: none (only agents without built-in image generation, such as Claude, need it: npm i -g @openai/codex, then codex login; not needed in Codex)"; fi
  command -v zsh >/dev/null 2>&1 || say "zsh: none (gen.sh, used by agents without built-in image generation such as Claude, needs it: install zsh; not needed in Codex)"
}
if [ "$MODE" = "python" ]; then P=$(env_py) && { echo "$P"; exit 0; }; echo "Python env not ready: run sh setup.sh check to see what is missing" >&2; exit 1; fi
if [ "$MODE" = "model" ]; then get_model; exit 0; fi
if [ "$MODE" = "image" ]; then
  check_codex
  T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
  printf '%s\n' "A small round red clay ball with a soft highlight, centred, on a transparent background, no shadow, no text." > "$T/test.txt"
  say "generating one test image (needs the network; uses your image account) ..."
  zsh "$HERE/gen.sh" "$T/test.txt" "$T/test.png" || { warn "test image failed; see the message above"; exit 1; }
  CT=$(od -An -tu1 -j25 -N1 "$T/test.png" | tr -d ' ')
  if [ "$CT" = 4 ] || [ "$CT" = 6 ]; then say "image tool works and returns transparent PNGs"; exit 0; fi
  warn "image tool works but returned no transparent background: assets will need cut-out (sh setup.sh model, ~0.97 GB) and edges get worse"
  exit 1
fi
LOCK="$HOME_DIR/.setup.lock"                       # two agents installing at once would fight over the same files
LOG="$HOME_DIR/setup.log"
# the lock holds the installer's pid; a lock whose installer died (machine slept, app closed) is cleared
lock_live() {
  [ -d "$LOCK" ] || return 1
  [ -f "$LOCK/pid" ] || return 0                   # just taken, pid not written yet
  kill -0 "$(cat "$LOCK/pid" 2>/dev/null)" 2>/dev/null && return 0
  rm -rf "$LOCK"; return 1
}
if [ "$MODE" = "start" ]; then
  mkdir -p "$HOME_DIR"
  if OUT=$(sh "$HERE/setup.sh" check 2>&1); then say "$OUT"; exit 0; fi
  say "$OUT"
  if lock_live; then say "already installing in the background (log: $LOG); later, sh setup.sh waits for it"; exit 0; fi
  # detach into its own session: agents (Codex) kill the command's process group when the command returns
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import os, sys
if os.fork(): sys.exit(0)
os.setsid()
if os.fork(): os._exit(0)
fd = os.open(sys.argv[2], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644); os.dup2(fd, 1); os.dup2(fd, 2)
os.dup2(os.open(os.devnull, os.O_RDONLY), 0)
os.execvp("sh", ["sh", sys.argv[1], "env"])' "$HERE/setup.sh" "$LOG"
  else
    nohup sh "$HERE/setup.sh" env > "$LOG" 2>&1 < /dev/null &
  fi
  say ""
  say "INSTALLING IN THE BACKGROUND: Python env (~300 MB) + score instrument samples (~1.4 GB) -> $HOME_DIR (log: $LOG)."
  say "Run sh setup.sh to wait for installation, then sh setup.sh check. Ask the opening questions only after the environment is ready."
  exit 0
fi
if [ "$MODE" != "check" ]; then
  mkdir -p "$HOME_DIR"; n=0
  while ! mkdir "$LOCK" 2>/dev/null; do
    lock_live || continue
    [ "$n" -eq 0 ] && say "another setup.sh is installing into $HOME_DIR (log: $LOG); waiting for it to finish ..."
    n=$((n + 1)); [ "$n" -gt 1800 ] && { warn "still locked after an hour: if no setup.sh is running, remove $LOCK and rerun"; exit 1; }
    sleep 2
  done
  echo $$ > "$LOCK/pid"
  trap 'rm -rf "$LOCK"' EXIT; trap 'exit 143' INT TERM
fi
if [ "$MODE" = "instruments" ]; then get_instruments; [ "$INSTR_OK" -eq 1 ] || exit 1; exit 0; fi
check_ffmpeg
if [ "$MODE" = "check" ]; then
  if venv_ok; then say "Python env: $VENV/bin/python ($(py_ver "$VENV/bin/python"), deps complete)"
  elif P=$(system_py); then say "Python env: $P ($(py_ver "$P"), already on this system with every dependency; nothing to install)"
  else
    P=$(pick_python)
    warn "no usable venv yet (${VENV}); it would be made with: ${P:-no Python found}"
    MISSING=1
  fi
  get_model
  get_instruments
  check_codex
  if [ "$MISSING" -ne 0 ]; then warn "something is missing; run sh setup.sh to fill it in (needs network: ~300 MB for the env, ~1.4 GB of instrument samples)"; exit 1; fi
  say "All ready. Compositing scripts use this interpreter: $(env_py)"
  exit 0
fi
[ "$MISSING" -eq 0 ] || warn "install ffmpeg before rendering films (venv and model are prepared anyway)"
if venv_ok; then say "Python env ready: $VENV"
elif P=$(system_py); then say "Python env: $P already has every dependency; using it, no venv made"
else make_venv; fi
get_instruments
get_model
say ""
say "Done. Compositing, slicing and cut-out all use this interpreter:"
PYE=$(env_py) || PYE="$VENV/bin/python"
say "  $PYE"
say "e.g. $PYE <skill>/scripts/animi.py check src/run.png --out review/run_check.jpg"
[ "$INSTR_OK" -eq 1 ] || { warn "instrument samples incomplete (no score possible): once online, sh setup.sh instruments"; exit 1; }
