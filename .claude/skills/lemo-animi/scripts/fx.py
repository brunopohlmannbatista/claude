# fx.py -- text layer: set small in-picture text (signs) and paste it onto frame in place
#
# Usage:
#   import fx
#   t = fx.text('EXIT', 'siyuan', 60, color=(0.2, 0.15, 0.1))      # -> (P premultiplied colour, A, pad): a small sign in the picture
#   fx.put(frame, t, 960, 540, anchor='cc')                        # aligns on the glyphs' real ink box
# Title and end card text use bookends.title_tag (Source Han Sans Bold, flat colour + style plate); subtitles use animi.Subtitles.
# Fonts: a name from FONTS (song / hei / din / futura ...) or a font file path; missing fonts fall back to system fonts,
# then to PIL's default font (no CJK glyphs), printing one line; never crashes.
# Effects (glow, speed lines, star glints, debris) are always generated images (the fx sheet), not drawn here. API in
# references/api.md.
import os, sys, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

# Each name has candidates (path, ttc index); the first that exists wins; if none, fall back by CJK / Latin,
# finally PIL's built-in font (never crashes, but it has no CJK glyphs). A .ttf/.ttc/.otf path also works as a name.
_SYS = '/System/Library/Fonts/'; _SUP = _SYS + 'Supplemental/'
_OWN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts') + os.sep
FONTS = {
    'song': [(_SUP + 'Songti.ttc', 0), ('/Library/Fonts/Songti.ttc', 0)],             # Songti: titles
    'hei': [(_SYS + 'Hiragino Sans GB.ttc', 2), (_SYS + 'PingFang.ttc', 0)],          # Hiragino Sans GB W6
    'hei-l': [(_SYS + 'Hiragino Sans GB.ttc', 0), (_SYS + 'PingFang.ttc', 0)],        # Hiragino Sans GB W3
    'din': [(_SUP + 'DIN Condensed Bold.ttf', 0), (_SUP + 'DIN Alternate Bold.ttf', 0)],
    'futura': [(_SUP + 'Futura.ttc', 0)],
    'futura-b': [(_SUP + 'Futura.ttc', 2)],          # Futura Bold
    'futura-ci': [(_SUP + 'Futura.ttc', 4)],         # Futura Condensed ExtraBold
    'futura-i': [(_SUP + 'Futura.ttc', 1)],          # Futura Medium Italic
    'mincho': [(_SYS + 'ヒラギノ明朝 ProN.ttc', 0)],    # Japanese Mincho W3
    'mincho-b': [(_SYS + 'ヒラギノ明朝 ProN.ttc', 2)],  # Japanese Mincho W6
    'gothic': [(_SYS + 'ヒラギノ角ゴシック W3.ttc', 0)],
    'gothic-b': [(_SYS + 'ヒラギノ角ゴシック W8.ttc', 0)],
    'siyuan': [(_OWN + 'SourceHanSansCN-Bold.otf', 0)],    # Source Han Sans Bold (OFL, skill/fonts/): CJK subtitles in every style
}
CJK_NAMES = {'song', 'hei', 'hei-l', 'mincho', 'mincho-b', 'gothic', 'gothic-b', 'siyuan'}
FALLBACK_CJK = [(_SYS + 'Hiragino Sans GB.ttc', 0), (_SYS + 'PingFang.ttc', 0), (_SYS + 'STHeiti Medium.ttc', 0),
                (_SUP + 'Songti.ttc', 0), (_SUP + 'Arial Unicode.ttf', 0),
                ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 0),
                ('/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc', 0),
                ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 0)]
FALLBACK_LATIN = [(_SYS + 'Helvetica.ttc', 0), (_SYS + 'HelveticaNeue.ttc', 0), (_SUP + 'Arial.ttf', 0),
                  ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 0)]
_fc = {}; _tc = {}; _warned = set()


def _try(cands, size):
    for p, idx in cands:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size, index=idx)
            except Exception: pass
    return None


def font(name, size):
    """Get a PIL font (cached). name is a FONTS name or a font file path; falls back automatically if missing, never crashes."""
    k = (name, size)
    if k in _fc: return _fc[k]
    f = None
    if os.path.sep in name or name.lower().endswith(('.ttf', '.ttc', '.otf')):
        f = _try([(name, 0)], size)
    else:
        f = _try(FONTS.get(name, []), size)
    if f is None:
        f = _try(FALLBACK_CJK if (name in CJK_NAMES or name not in FONTS) else FALLBACK_LATIN, size) \
            or _try(FALLBACK_CJK + FALLBACK_LATIN, size)
        if name not in _warned:
            _warned.add(name); print(f'fx.font: font "{name}" not found, using a fallback', file=sys.stderr)
    if f is None:
        try: f = ImageFont.load_default(size)     # Pillow >= 10.1
        except TypeError: f = ImageFont.load_default()
    _fc[k] = f
    return f


def text(s, fname, size, color=(1, 1, 1), track=0.0, shadow=0.45, glow=0.0):
    """-> (P premultiplied colour, A) with a soft drop shadow; track = letter spacing (fraction of font size)"""
    k = (s, fname, size, color, track, shadow, glow)
    if k in _tc: return _tc[k]
    f = font(fname, size); pad = int(size * 0.6)
    ws = [f.getbbox(ch)[2] if ch != ' ' else size * 0.35 for ch in s]
    tw = int(sum(ws) + track * size * max(0, len(s) - 1)) + 2 * pad; th = int(size * 1.5) + 2 * pad
    im = Image.new('L', (tw, th), 0); d = ImageDraw.Draw(im); x = pad
    for ch, w in zip(s, ws):
        d.text((x, pad), ch, font=f, fill=255); x += w + track * size
    A = np.asarray(im).astype(np.float32) / 255
    ys, xs = np.nonzero(A > 0.01)
    if len(xs) == 0:                                 # empty / all spaces: return a small transparent layer
        A = np.zeros((2 * pad + 1, 2 * pad + 1), np.float32)
        _tc[k] = (np.zeros(A.shape + (3,), np.float32), A, pad)
        return _tc[k]
    A = A[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    A = np.pad(A, pad)
    col = np.array(color, np.float32)
    P = A[..., None] * col
    if shadow > 0:                                   # drop shadow: low, soft
        S = cv2.GaussianBlur(np.roll(A, int(size * 0.04) + 1, 0), (0, 0), size * 0.06 + 1) * shadow
        Aout = A + S * (1 - A); P = P  # dark shadow = alpha only, no colour
        A = Aout
    if glow > 0:
        G = cv2.GaussianBlur(P, (0, 0), size * 0.25) * glow
        P = P + G; A = np.clip(A + G.mean(2) * 0.0, 0, 1)
    _tc[k] = (P.astype(np.float32), np.clip(A, 0, 1).astype(np.float32), pad)
    return _tc[k]


def put(frame, layer, x, y, anchor='lt', alpha=1.0, scale=1.0, motion=0.0, blur=0.0, add=False):
    """(x, y) aligns to the text's real bounding box (padding excluded)"""
    if alpha <= 0.005: return
    P, A, m = layer if len(layer) == 3 else (*layer, 0)
    if scale != 1.0:
        nw, nh = max(2, int(A.shape[1] * scale)), max(2, int(A.shape[0] * scale))
        P = cv2.resize(P, (nw, nh), interpolation=cv2.INTER_LINEAR); A = cv2.resize(A, (nw, nh), interpolation=cv2.INTER_LINEAR)
    if blur > 0.3: P = cv2.GaussianBlur(P, (0, 0), blur); A = cv2.GaussianBlur(A, (0, 0), blur)
    if motion >= 2:
        L = int(motion); k = np.ones((1, L), np.float32) / L
        P = cv2.filter2D(np.pad(P, ((0, 0), (L, L), (0, 0))), -1, k); A = cv2.filter2D(np.pad(A, ((0, 0), (L, L))), -1, k)
    h, w = A.shape; ms = m * scale
    if motion >= 2: w -= 2 * int(motion)
    ax = {'l': 0, 'c': 0.5, 'r': 1}[anchor[0]]; ay = {'t': 0, 'c': 0.5, 'b': 1}[anchor[1]]
    iw, ih = w - 2 * ms, h - 2 * ms
    x0, y0 = int(x - ax * iw - ms - (int(motion) if motion >= 2 else 0)), int(y - ay * ih - ms)
    h, w = A.shape
    H, W = frame.shape[:2]
    fx0, fy0 = max(0, x0), max(0, y0); fx1, fy1 = min(W, x0 + w), min(H, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0: return
    sl = (slice(fy0 - y0, fy1 - y0), slice(fx0 - x0, fx1 - x0))
    reg = frame[fy0:fy1, fx0:fx1]
    if add: reg += P[sl] * alpha
    else:
        Ar = (A[sl] * alpha)[..., None]; reg[:] = reg * (1 - Ar) + P[sl] * alpha


def size(layer):
    P, A, m = layer; return A.shape[1] - 2 * m, A.shape[0] - 2 * m
