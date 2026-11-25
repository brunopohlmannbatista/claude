# kit.py -- low-level tools for frame-by-frame compositing: read / write images, load cells, easing, blur, grading, encoding
#
# Usage (in a film's compositing script):
#   import sys; sys.path.insert(0, '<skill>/scripts'); import kit, fx, animi
#   bg = kit.rd('src/bg.png')                           # read the background at full size (do not pre-scale; cam.plate frames it)
#   c  = kit.sprite('work/cells', None, 'run_3')         # (C colour, a alpha, M): RGBA cells use their own alpha
#   animi.place_at(frame, c, x, ground_y, s, info=A['run_3'])   # place by anchor (animi.py), not by bbox
#   kit.wr('frames/f0000.png', frame); kit.encode('frames', 'out/film.mp4', fps=24)
# Conventions: images are float32, RGB, 0-1; placing functions edit frame in place; frame files are f%04d.png.
# Higher-level tools (placing by foot point, timesheet, slicing and sheet QC) are in animi.py. Full API: references/api.md.
# Stop-motion has no interpolated frames: no optical-flow in-betweens between cells; one drawing is one drawing.
import os, math, subprocess, sys, numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1920, 1080


def rd(p):
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    if im is None: raise FileNotFoundError(p)
    return im[:, :, ::-1].astype(np.float32) / 255


def wr(p, f):
    """Write PNG/JPG (creates the folder; raises if it cannot write, never fails silently)"""
    d = os.path.dirname(p)
    if d: os.makedirs(d, exist_ok=True)
    f = np.asarray(f)
    im = (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)
    if im.ndim == 3: im = im[:, :, ::-1]
    if not cv2.imwrite(p, im): raise IOError(f'cannot write image: {p}')


def ease(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3


def ease_in(x):
    x = min(max(x, 0.0), 1.0); return x ** 3


def lerp(a, b, t): return a + (b - a) * t


def fit(img, w=None, h=None):
    """Scale proportionally, then centre-crop to w x h"""
    w = w or W; h = h or H
    s = max(w / img.shape[1], h / img.shape[0])
    im = cv2.resize(img, (math.ceil(img.shape[1] * s), math.ceil(img.shape[0] * s)), interpolation=cv2.INTER_CUBIC)
    y0 = (im.shape[0] - h) // 2; x0 = (im.shape[1] - w) // 2
    return np.ascontiguousarray(im[y0:y0 + h, x0:x0 + w])


# ---------------- pose sheets ----------------
def slice_sheet(png, rows, cols, outdir, prefix):
    """Cut a sheet into equal cells (remainder pixels dropped). When subjects reach into the next cell use animi.slice_subjects."""
    os.makedirs(outdir, exist_ok=True)
    im = cv2.imread(png)
    if im is None: raise FileNotFoundError(png)
    Hh, Ww = im.shape[:2]
    cw, ch = Ww // cols, Hh // rows
    out = []
    for r in range(rows):
        for c in range(cols):
            p = f'{outdir}/{prefix}_{r * cols + c}.png'
            cv2.imwrite(p, im[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]); out.append(p)
    return out


_sp = {}
def sprite(cells, masks=None, name=None, white=True):
    """-> (C colour, a alpha, M white-background shadow multiplier). white=False: no shadow.
    Transparent RGBA cells (the default) use their own alpha and need no masks (pass None); M is all 1.
    Cache key includes cells, masks, name, white; returns a copy each time, so in-place edits do not touch the cache."""
    key = (cells, masks, name, white)
    if key in _sp: return tuple(x.copy() for x in _sp[key])
    raw = cv2.imread(f'{cells}/{name}.png', cv2.IMREAD_UNCHANGED)
    if raw is not None and raw.ndim == 3 and raw.shape[2] == 4:      # transparent cell: colour + own alpha, no white-background shadow
        I = raw[:, :, 2::-1].astype(np.float32) / 255
        a = np.clip((raw[:, :, 3].astype(np.float32) / 255 - 0.02) / 0.95, 0, 1)
        if (a < 0.5).mean() >= 0.05:
            _sp[key] = (I, a, np.ones_like(I))
            return tuple(x.copy() for x in _sp[key])
    I = rd(f'{cells}/{name}.png')
    mp = f'{masks}/{name}-mask.png'
    a = cv2.imread(mp, 0)
    if a is None: raise FileNotFoundError(mp)
    a = a.astype(np.float32) / 255
    if a.shape != I.shape[:2]:
        print(f'kit.sprite: mask {mp} size {a.shape[::-1]} differs from cell {I.shape[1::-1]}, resized to match (check it is the right mask)', file=sys.stderr)
        a = cv2.resize(a, (I.shape[1], I.shape[0]))
    a = np.clip((a - 0.03) / 0.94, 0, 1)
    b = 4; a[:b] = a[-b:] = 0; a[:, :b] = a[:, -b:] = 0
    if white:
        I = np.clip(I / np.maximum(np.percentile(I, 99.5, axis=(0, 1)), 0.5), 0, 1)
        aa = np.maximum(a, 0.04)[..., None]
        C = np.clip((I - (1 - a)[..., None]) / aa, 0, 1)
        C = np.where(a[..., None] < 0.04, I, C)
        M = np.where(a[..., None] > 0.02, 1.0, I).astype(np.float32)
        M = cv2.GaussianBlur(M, (0, 0), 2)
        M = np.clip(1 - (1 - M.mean(2, keepdims=True)) * 1.35, 0, 1).repeat(3, 2)
        M[:b + 3] = M[-b - 3:] = 1; M[:, :b + 3] = M[:, -b - 3:] = 1
    else:
        C = I; M = np.ones_like(I)
    _sp[key] = (C.astype(np.float32), a.astype(np.float32), M.astype(np.float32))
    return tuple(x.copy() for x in _sp[key])


def bbox(a, th=0.5):
    """bbox (x0, y0, x1, y1) of alpha > th; x1/y1 exclusive. Raises when the mask is empty."""
    ys, xs = np.nonzero(a > th)
    if len(xs) == 0: raise ValueError('bbox: the mask is empty (no pixel above the threshold)')
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def hblur(img, L):
    L = int(round(L))
    if L < 2: return img
    k = np.ones((1, L), np.float32) / L
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)


def vblur(img, L):
    L = int(round(L))
    if L < 2: return img
    k = np.ones((L, 1), np.float32) / L
    return cv2.filter2D(img, -1, k, borderType=cv2.BORDER_REFLECT)


def over(frame, P, A, x0, y0):
    """Composite premultiplied layer P/A onto frame at (x0, y0)"""
    FH, FW = frame.shape[:2]; h, w = A.shape
    x0, y0 = int(round(x0)), int(round(y0))
    fx0, fy0 = max(0, x0), max(0, y0); fx1, fy1 = min(FW, x0 + w), min(FH, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0: return
    sl = (slice(fy0 - y0, fy1 - y0), slice(fx0 - x0, fx1 - x0))
    Ar = np.clip(A[sl], 0, 1)[..., None]
    frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1] * (1 - Ar) + P[sl]


def clear_cache():
    """Clear the sprite / vignette caches (saves memory between segments of a long film)"""
    _sp.clear(); _vig.clear()


# ---------------- camera ----------------
def cam(img, zoom=1.0, dx=0.0, dy=0.0, rot=0.0, cx=None, cy=None):
    h, w = img.shape[:2]
    cx = w / 2 if cx is None else cx; cy = h / 2 if cy is None else cy
    Mt = cv2.getRotationMatrix2D((float(cx), float(cy)), float(rot), float(zoom)); Mt[0, 2] += dx; Mt[1, 2] += dy
    return cv2.warpAffine(img, Mt, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def shake(t, amp, seed=0):
    return (amp * (0.6 * math.sin(13.1 * t + seed) + 0.4 * math.sin(29.7 * t + 2 * seed)),
            amp * (0.6 * math.sin(11.3 * t + 3 + seed) + 0.4 * math.sin(23.9 * t + 1 + seed)))


# ---------------- grading ----------------
_vig = {}
def vignette(w, h, k=0.35):
    if (w, h, k) not in _vig:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2)
        _vig[(w, h, k)] = (1 - k * np.clip(r - 0.35, 0, None) ** 1.6)[..., None].astype(np.float32)
    return _vig[(w, h, k)]


def grade(f, tint=(1, 1, 1), lift=(0, 0, 0), bloom=0.5, bloom_th=0.72, bloom_r=26, halation=0.0,
          vig=0.35, grain=0.022, seed=None, contrast=1.0, sat=1.0):
    h, w = f.shape[:2]
    f = np.clip(f, 0, 4)
    hl = np.clip(f - bloom_th, 0, None)
    if bloom: f = f + cv2.GaussianBlur(hl, (0, 0), bloom_r) * bloom
    if halation:  # film halation: red glow around highlights
        hm = cv2.GaussianBlur(hl.max(2), (0, 0), bloom_r * 0.5)
        f = f + hm[..., None] * np.array([1.0, 0.25, 0.08], np.float32) * halation
    if sat != 1:
        g = f.mean(2, keepdims=True); f = g + (f - g) * sat
    if contrast != 1:
        f = 0.5 + (f - 0.5) * contrast
    f = f * np.array(tint, np.float32) + np.array(lift, np.float32)
    f = f * vignette(w, h, vig)
    if grain:
        r = np.random.default_rng(seed)
        g = cv2.resize(r.normal(0, grain, (h // 2, w // 2)).astype(np.float32), (w, h))
        f = f + g[..., None] * (0.4 + 0.6 * np.clip(1 - f.mean(2, keepdims=True), 0, 1))
    return np.clip(f, 0, 1)


# ---------------- output ----------------
def encode(frames_dir, mp4, fps=24, crf=17):
    """<frames_dir>/f%04d.png -> H.264 mp4 (yuv420p, width and height must be even, no audio)"""
    d = os.path.dirname(mp4)
    if d: os.makedirs(d, exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', f'{frames_dir}/f%04d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(crf), '-preset', 'slow',
                    '-movflags', '+faststart', mp4], check=True)
