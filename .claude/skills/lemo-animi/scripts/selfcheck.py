#!/usr/bin/env python3
"""Sampled review sheets before delivery: one command, two images; look at every tile before delivering (the tool only
makes the material; record honestly whether you looked).

    python selfcheck.py out/<name>.mp4 [--step 0.5] [--out work/selfcheck]

  <out>_frames.jpg   one frame every step seconds (time top-left): check "always something happening", slips, hero size,
                     subtitles
  <out>_cuts.jpg     frame before | frame after each cut (reads out/<name>.shots.json): check jump cuts and continuity
                     across the cut (where the character is, what it holds)
Also measures "too dark": whole frame or the hero region (reads work/hero.json, written by film.py's full render) too
dark for 0.3 s or more is reported and those tiles are marked red in _frames.jpg. Dark styles set the threshold in
style.json preset.dark (pass the style id with --style).

Check against the "frame-by-frame self-review" list in section 2 of references/quality.md, write findings into the
production log, fix, and run again.
"""
import os, sys, json, argparse, subprocess, tempfile
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animi  # noqa: E402


def grab(mp4, t, w=480):
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f: p = f.name
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{max(0.0, t):.3f}', '-i', mp4, '-frames:v', '1', p], check=True)
    im = cv2.imread(p); os.remove(p)
    if im is None: return None
    return cv2.resize(im, (w, int(w * im.shape[0] / im.shape[1])), interpolation=cv2.INTER_AREA)


def label(im, s, color=(40, 40, 230)):
    cv2.putText(im, s, (8, 28), 0, 0.8, (255, 255, 255), 4); cv2.putText(im, s, (8, 28), 0, 0.8, color, 2)
    return im


def grid(tiles, cols, out):
    h, w = tiles[0].shape[:2]
    tiles = tiles + [np.zeros_like(tiles[0])] * (-len(tiles) % cols)
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85]); print(out)


def dur(mp4):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mp4'); ap.add_argument('--step', type=float, default=0.5); ap.add_argument('--out', default='work/selfcheck')
    ap.add_argument('--hero', default='work/hero.json', help="hero box per drawing (written by film.py's full render)")
    ap.add_argument('--style', help='style id: read the preset.dark threshold')
    g = ap.parse_args()
    os.makedirs(os.path.dirname(g.out) or '.', exist_ok=True)
    D = dur(g.mp4)
    th = animi.style_preset(g.style).get('dark') if g.style else None
    dark = animi.darkness(g.mp4, g.hero if os.path.exists(g.hero) else None, th=th)
    if not os.path.exists(g.hero): print(f'selfcheck: no {g.hero}; checking darkness on whole-frame brightness only', file=sys.stderr)
    for t0, d, why in dark:
        print(f'too dark: {d:.2f}s from {t0:.2f}s, {why}: hero and action may be invisible', file=sys.stderr)
    if not dark: print('too dark: none', file=sys.stderr)
    ts = list(np.arange(0.0, D - 0.05, g.step))
    isdark = lambda t: any(t0 <= t < t0 + d for t0, d, _ in dark)
    tiles = [label(grab(g.mp4, t, 320), f'{t:.1f}' + (' DARK' if isdark(t) else ''), (40, 40, 230) if not isdark(t) else (0, 0, 255))
             for t in ts]
    grid([t for t in tiles if t is not None], 6, g.out + '_frames.jpg')
    sj = os.path.splitext(g.mp4)[0] + '.shots.json'
    if not os.path.exists(sj):
        sys.exit(f'selfcheck: no {sj} (film.py writes it on the full render): no cut sheet, self-review not finished')
    shots = json.load(open(sj))['shots']; pairs = []
    for a, b in zip(shots, shots[1:]):
        t = float(b['t'])
        L = label(grab(g.mp4, t - 0.06), f'{t:.2f}s  {a.get("name", "")} ({a.get("size", "")})')
        Rr = label(grab(g.mp4, t + 0.06), f'-> {b.get("name", "")} ({b.get("size", "")})', (40, 160, 40))
        pairs.append(np.hstack([L, np.full((L.shape[0], 6, 3), 255, np.uint8), Rr]))
    if pairs: grid(pairs, 2, g.out + '_cuts.jpg')


if __name__ == '__main__':
    main()
