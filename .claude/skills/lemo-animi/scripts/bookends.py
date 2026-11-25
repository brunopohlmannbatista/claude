#!/usr/bin/env python3
"""Title and end card text and plates, plus optional animated bookends (off by default: run only when the user asks).

Text rules (same for every style): Source Han Sans Bold only, flat colour; no material on the strokes (no cloth or paper
texture, ragged edges, outlines, offsets, per-letter colours). Style lives only on the plate behind the text (colour,
scissor-cut polygon / rounded / stitched dashes, texture). Whole-pixel placement, no rotation; Latin text is set as a
whole line, no letter spacing.
Minimum sizes for a 1080-high (short side) frame: title >= 200 px, subtitle >= 60 px, credit >= 48 px; other sizes scale
with the short side.

Command line (inside the film folder):
    $PY <skill>/scripts/bookends.py out/<name>.mp4 --title <title> [--credit <credit>] [--end <end text>] [--style <style>]
        [--lang zh|en] [--sub <subtitle>] [--hero work/cells/hop_0.png work/cells/hop_4.png]
        -> out/<name>-bookends.mp4 + .shots.json + .srt (title card + film + end card; narration subtitles shifted), plus work/bookends_head.jpg and
           bookends_tail.jpg (one tile every 3 drawings, for self-review).
           Title and end card are 3 s each by default (--sec, 2.5-4), the same animation for every style; look and entrance come from the
           style's title:
           title card: over the film's first frame the plate enters (drops or stands up), stitches sew on (stitch plate),
                 the title drops in letter by letter, the subtitle strip slides in, the character jumps onto the card
                 (with --hero), hold, the whole card is pulled up and away, and the film starts (no black, no audio fade
                 at the seam);
           end card: holding on the film's last frame, the plate enters, the end text drops in, the credit fades in. The
                 credit uses only the user's own words; there is no default credit.
           --end defaults to the film language's word for "The End" (zh 完, en The End); the language comes from --lang,
           else sound.json's lang, else the title's script.
    $PY bookends.py preview --title <title> [--credit <credit>] [--style <style>] [--lang zh|en] [--bg img.png]
        -> work/_titles.jpg (text and plates only)

In a compositing script:
    import bookends
    tag = bookends.title_tag('The Shortcut', 220, style='fabric')      # plate params come from style.json's title
    bookends.put_tag(frame, tag, W // 2, H // 2)                         # centre lands on a whole pixel

style.json title (all optional; defaults: off-white rounded plate, dark text):
    "title": {"color": [0.30, 0.17, 0.09],                    # text colour (flat)
              "plate": {"shape": "round",                     # cut scissor-cut polygon / round rounded / stitch rounded + stitched dashes / rect / none
                        "color": [0.98, 0.95, 0.88],          # plate colour
                        "texture": "ref/texture.jpg",         # plate texture: a material close-up (film folder first, then the style package);
                                                              # or a procedural texture "proc:knit" stitches / "proc:wood" wood grain / "proc:weave" cloth / "proc:paper" paper fibre
                                                              # material close-ups only, never a background: waves, stars, houses would print onto the plate
                        "texture_k": 0.5,                     # texture strength
                        "border": [0.035, [0.2, 0.3, 0.5]],   # solid border: width (times font size), colour (optional)
                        "stitch": [0.76, 0.22, 0.20],         # stitch colour (shape = stitch)
                        "rough": 7,                           # scissor-edge wobble px (shape = cut)
                        "pad": [0.45, 0.30],                  # plate margin: times font size (horizontal, vertical)
                        "shadow": [6, 8, 0.32]},              # drop shadow: offset px, blur px, strength
              "sub": {"color": [..], "plate": {..}},          # subtitle on its own strip (used by title_tag(sub=...); optional = same plate as the title)
              "motion": {"enter": "drop",                     # plate entrance: drop from above / pop stand up from the bottom edge (paper, card); default pop for cut plates
                         "step": 2, "sub_side": -1},          # interval between letters dropping (drawings); subtitle strip slides in from left (-1) / right (1)
              "sound": ["thud", "tap"]}                       # foley for the plate landing (first of these the style material has)
A missing plate texture is reported (stderr + animi.MISSING; lint and the final render report it), never silently
replaced by a flat colour.
"""
import os, re, sys, json, math, shutil, argparse, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit, fx, animi  # noqa: E402

MIN_SIZE = {'title': 200, 'sub': 60, 'credit': 48}        # minimum font sizes at a 1080 short side
END_TEXT = {'zh': '完', 'en': 'The End'}                 # default end card text per film language
INK = (0.12, 0.10, 0.09)
DEFAULT_PLATE = dict(shape='round', color=[0.97, 0.94, 0.88], texture=None, texture_k=0.5, stitch=[0.72, 0.24, 0.20],
                     rough=7, pad=[0.45, 0.30], shadow=[6, 8, 0.32])


def _is_latin(s):
    return all(ord(c) < 0x2E80 for c in s)


def film_lang(lang=None, root=None, text=None):
    """Film language for default card text: lang if given, else sound.json's lang in root, else 'en' when text is all
    Latin, else 'zh'"""
    if lang: return 'zh' if str(lang).lower().startswith('zh') else 'en'
    p = os.path.join(root, 'sound.json') if root else None
    if p and os.path.exists(p):
        try:
            v = json.load(open(p, encoding='utf-8')).get('lang')
            if v: return 'zh' if str(v).lower().startswith('zh') else 'en'
        except (OSError, ValueError): pass
    return 'en' if text and _is_latin(text) else 'zh'


def text_alpha(s, size, track=0.0):
    """Alpha of one line of text (plain Source Han Sans Bold glyphs: no bolding, outline or noise), bounding box + 2 px.
    Latin, digits and mixed text are set as a whole line (spacing left to the font); pure CJK may take track (times font
    size) to open up a little."""
    f = fx.font('siyuan', int(size))
    if track and not _is_latin(s) and all(not c.isascii() for c in s):
        xs, x = [], 0.0
        for ch in s:
            xs.append(x); x += f.getlength(ch) + size * track
        w = int(math.ceil(x - size * track)) + 4
        _, y0, _, y1 = f.getbbox(s)
        im = Image.new('L', (w, y1 - y0 + 4), 0); d = ImageDraw.Draw(im)
        for ch, cx in zip(s, xs): d.text((2 + int(round(cx)), 2 - y0), ch, font=f, fill=255)
    else:
        x0, y0, x1, y1 = f.getbbox(s)
        im = Image.new('L', (x1 - x0 + 4, y1 - y0 + 4), 0)
        ImageDraw.Draw(im).text((2 - x0, 2 - y0), s, font=f, fill=255)
    return np.asarray(im, np.float32) / 255


PROC = ('knit', 'wood', 'weave', 'paper')


def _proc_texture(kind, shape, big, seed=3):
    """Procedural texture (brightness multiplier, mean ~1): knit rows of V stitches, wood grain, weave cloth, paper fibre. big = font size (texture scales with it)"""
    h, w = shape; rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if kind == 'knit':                                       # columns of V stitches: each stitch is two slanted loops
        cw = max(6.0, big * 0.11); ch = cw * 0.8
        u = (xx % cw) / cw; v = ((yy + (np.floor(xx / cw) % 2) * ch * 0.5) % ch) / ch
        loop = np.exp(-((np.abs(u - 0.5) * 2 - (0.2 + 0.6 * v)) ** 2) / 0.05)
        T = 0.88 + 0.2 * loop
    elif kind == 'wood':                                     # growth-ring stripes: horizontally stretched noise as phase
        n = cv2.resize(rng.random((max(2, h // 60), max(2, w // 240))).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        T = 0.92 + 0.08 * np.sin((yy / max(4.0, big * 0.09) + 3 * n) * 2 * np.pi) ** 2
        T = T * (0.97 + 0.03 * cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 1.0))
    elif kind == 'weave':                                    # interlaced warp and weft
        p = max(4.0, big * 0.05)
        T = 0.93 + 0.07 * np.sign(np.sin(xx / p * np.pi) * np.sin(yy / p * np.pi)) * np.abs(np.sin(xx / p * np.pi + yy / p * np.pi))
    else:                                                    # paper: fine fibres + a few specks
        n = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 0.8)
        T = 0.96 + 0.08 * (n - 0.5) + 0.03 * cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 6) * 4
    return (T / max(1e-3, float(T.mean()))).astype(np.float32)


def find_texture(path, root=None, style=None):
    """Where the plate texture image is: absolute path -> film folder (root) -> style package (styles/<style>/). -> path or None"""
    if not path: return None
    cands = [path] if os.path.isabs(path) else []
    if root and not os.path.isabs(path): cands.append(os.path.join(root, path))
    if style and not os.path.isabs(path):
        sd = os.path.join(animi.STYLES_DIR, style); cands += [os.path.join(sd, path), os.path.join(sd, 'ref', os.path.basename(path))]
    return next((c for c in cands if os.path.exists(c)), None)


def _texture(path, shape, root=None, style=None, big=200, seed=3):
    """Plate texture: fine detail from the middle of a material close-up (brightness divided by its local mean to remove
    large shading), cropped to the plate size; proc:... is procedural.
    A missing image is reported (stderr + animi.MISSING) and returns None (flat colour)"""
    if not path: return None
    if str(path).startswith('proc:'):
        kind = path.split(':', 1)[1]
        if kind not in PROC: raise ValueError(f'procedural textures are only: {", ".join("proc:" + k for k in PROC)} ({path})')
        return _proc_texture(kind, shape, big, seed)
    p = find_texture(path, root, style)
    if p is None:
        msg = f'plate texture {path} not found (not in the film folder or style package {style or "?"})'
        print(f'bookends: {msg}; this version uses a flat plate', file=sys.stderr)
        animi.MISSING[str(path)] = msg
        return None
    I = kit.rd(p); L = cv2.cvtColor(I, cv2.COLOR_RGB2GRAY)
    L = np.clip(L / np.maximum(cv2.GaussianBlur(L, (0, 0), 8), 1e-3), 0.8, 1.2)      # keep only fine detail like paper or cloth grain
    h, w = shape; H0, W0 = L.shape
    s = max(h / (H0 * 0.6), w / (W0 * 0.6), 1.0)
    if s > 1.0: L = cv2.resize(L, (int(W0 * s) + 1, int(H0 * s) + 1), interpolation=cv2.INTER_CUBIC); H0, W0 = L.shape
    y0, x0 = (H0 - h) // 2, (W0 - w) // 2
    return L[y0:y0 + h, x0:x0 + w].astype(np.float32)


def corner(w, h):
    """Corner radius (px) of a rounded plate. Shared by the plate and its inner stitch ring; the stitch radius = this minus the inset, so both arcs are concentric"""
    return int(min(w, h) * 0.16)


def _plate_alpha(w, h, shape, rough, seed):
    """plate shape -> alpha (m px margin around the canvas)"""
    m = 24; W_, H_ = w + 2 * m, h + 2 * m
    if shape == 'cut':                                  # scissor-cut polygon: a few cuts per side, corners slightly off
        rng = np.random.default_rng(seed); pts = []
        for (ax, ay), (bx, by) in zip([(0, 0), (w, 0), (w, h), (0, h)], [(w, 0), (w, h), (0, h), (0, 0)]):
            n = 3 if abs(bx - ax) > abs(by - ay) else 2
            for k in range(n):
                t = k / n; pts.append((ax + (bx - ax) * t + rng.uniform(-rough, rough), ay + (by - ay) * t + rng.uniform(-rough, rough)))
        big = np.zeros((H_ * 4, W_ * 4), np.uint8)
        cv2.fillPoly(big, [np.round((np.array(pts, np.float32) + m) * 4).astype(np.int32)], 255, cv2.LINE_AA)
        return cv2.resize(big, (W_, H_), interpolation=cv2.INTER_AREA).astype(np.float32) / 255, m
    im = Image.new('L', (W_ * 2, H_ * 2), 0); d = ImageDraw.Draw(im)
    box = (m * 2, m * 2, (m + w) * 2 - 1, (m + h) * 2 - 1)
    if shape == 'rect': d.rectangle(box, fill=255)
    else: d.rounded_rectangle(box, radius=corner(w, h) * 2, fill=255)        # canvas is 2x
    return np.asarray(im.resize((W_, H_), Image.LANCZOS), np.float32) / 255, m


def _stitch(a, m, w, h, inset, width, dash, gap):
    """ring of dashed stitches inside a rounded rectangle -> 0–1 mask (dashes spaced by arc length along the outline)"""
    S = 2
    path = Image.new('L', (a.shape[1] * S, a.shape[0] * S), 0)
    r = max(4, corner(w, h) - inset)
    ImageDraw.Draw(path).rounded_rectangle(((m + inset) * S, (m + inset) * S, (m + w - inset) * S, (m + h - inset) * S),
                                           radius=r * S, fill=255)
    cs, _ = cv2.findContours(np.asarray(path), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    out = np.zeros((a.shape[0] * S, a.shape[1] * S), np.uint8)
    if cs:
        pts = max(cs, key=len)[:, 0, :].astype(np.float32)
        seg = np.hypot(*np.diff(np.vstack([pts, pts[:1]]), axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)])
        L, u = cum[-1], 0.0
        while u + dash * S < L:
            i0, i1 = np.searchsorted(cum, u), np.searchsorted(cum, u + dash * S)
            q = pts[i0:max(i0 + 2, i1)].astype(np.int32)
            cv2.polylines(out, [q], False, 255, max(2, int(round(width * S))), cv2.LINE_AA)
            u += (dash + gap) * S
    return cv2.resize(out, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


class Tag:
    """A plate + one or more lines of flat-colour text. P: premultiplied colour, A: opacity, S: shadow alpha (offset and blurred); all the same size."""
    def __init__(self, P, A, S, k):
        self.P, self.A, self.S, self.k = P, A, S, k

    @property
    def size(self): return self.A.shape[1], self.A.shape[0]


def style_title(style=None):
    """Read the style's title settings (text colour, plate); defaults fill the gaps"""
    t = {}
    if style:
        try: t = dict(animi.style_info(style).get('title') or {})
        except SystemExit: t = {}
    plate = dict(DEFAULT_PLATE); plate.update(t.get('plate') or {})
    return dict(color=t.get('color', INK), plate=plate, sound=t.get('sound', ['thud', 'tap', 'pop']))


def title_rows(title, W, short, role='title'):
    """Title as card rows that fit the frame (82% of the width): one line at full size if it fits, else one line
    shrunk down to the minimum size, else 2 balanced lines (Latin breaks at spaces, CJK between characters); longer titles are drawn
    smaller with a warning to shorten them."""
    size = int(230 * short / 1080); lo = int(math.ceil(MIN_SIZE.get(role, 0) * short / 1080)); room = 0.82 * W
    s = title.strip(); words = s.split(' ') if ' ' in s else list(s); sep = ' ' if ' ' in s else ''

    def split(n):                                          # n lines with the most even lengths
        best = None
        def rec(i, k, acc):
            nonlocal best
            if k == 1:
                parts = acc + [sep.join(words[i:])]
                if all(parts):
                    m = max(len(x) for x in parts)
                    if best is None or m < best[0]: best = (m, parts)
                return
            for j in range(i + 1, len(words)): rec(j, k - 1, acc + [sep.join(words[i:j])])
        rec(0, n, []); return best[1] if best else None

    for n in (1, 2):
        parts = ([s] if n == 1 else split(2)) or [s]
        w = max(text_alpha(x, size).shape[1] for x in parts)
        fit = min(size, int(size * room / w))
        if fit >= lo: return [(x, fit, role) for x in parts]
    print(f'bookends: title "{title}" is too long for the card even on two lines; shorten it '
          f'(about 10 CJK characters or 24 Latin letters at most); drawn smaller ({fit}px) to fit', file=sys.stderr)
    return [(x, fit, role) for x in parts]


def _min_size(size, role, short):
    if role not in MIN_SIZE: return int(size)
    lo = int(math.ceil(MIN_SIZE[role] * short / 1080))
    if size < lo:
        print(f'bookends: {role} size {size} is below the minimum {lo} ({MIN_SIZE[role]} px @1080); using {lo}', file=sys.stderr)
        return lo
    return int(size)


def title_tag(text, size=None, color=None, plate=None, style=None, role='title', short=1080, lines=None, root=None, seed=3,
              sub=None, bare=False):
    """Lay out a card -> Tag.
    text / size / role: one line; lines=[(text, size, role), ...] for several lines (one plate, centred). role: title /
    sub / credit (checked against minimum sizes).
    color: text colour (flat); plate: plate dict (see file header), None = the style's title.plate; False /
    {'shape': 'none'} = no plate.
    short: film short side (px); minimum sizes scale with it. root: base for relative plate texture paths (film folder;
    then the style package).
    sub: subtitle on its own coloured strip under the main plate: 'subtitle text' or dict(text=, size=66, color=, plate=,
         gap=0.1); missing colour / strip plate come from the style's title.sub (else the main plate's shape with text
         and plate colours swapped).
    bare=True: plate only (sized as if it had text), no text, no stitches -- the animated title card adds text and
    stitches one by one (see Card)."""
    if sub:
        return _with_sub(title_tag(text, size, color, plate, style, role, short, lines, root, seed), sub, style, short, root, seed)
    st = style_title(style)
    color = np.array(color if color is not None else st['color'], np.float32)
    if plate is None: plate = st['plate']
    elif plate is False: plate = dict(shape='none')
    else: plate = dict(DEFAULT_PLATE, **plate)
    if lines is None: lines = [(text, size or MIN_SIZE.get(role, 60), role)]
    rows = []
    for s, sz, rl in lines:
        sz = _min_size(sz, rl, short)
        rows.append((text_alpha(s, sz), sz))
    gap = [int(0.28 * max(rows[i][1], rows[i + 1][1])) for i in range(len(rows) - 1)]
    tw = max(a.shape[1] for a, _ in rows); th = sum(a.shape[0] for a, _ in rows) + sum(gap)
    T = np.zeros((th, tw), np.float32); y = 0
    for i, (a, _) in enumerate(rows):
        x = (tw - a.shape[1]) // 2; T[y:y + a.shape[0], x:x + a.shape[1]] = np.maximum(T[y:y + a.shape[0], x:x + a.shape[1]], a)
        y += a.shape[0] + (gap[i] if i < len(gap) else 0)
    big = max(sz for _, sz in rows)
    shape = plate.get('shape', 'round')
    if shape == 'none':
        P = T[..., None] * color; return Tag(P.astype(np.float32), T, np.zeros_like(T), 1.0)
    px, py = plate.get('pad', [0.45, 0.30])
    px, py = int(round(px * big)), int(round(py * big))
    w, h = tw + 2 * px, th + 2 * py
    a, m = _plate_alpha(w, h, shape, float(plate.get('rough', 7)) * big / 200, seed)
    C = np.empty(a.shape + (3,), np.float32); C[:] = np.array(plate.get('color', DEFAULT_PLATE['color']), np.float32)
    tex = _texture(plate.get('texture'), a.shape, root, style, big, seed)
    if tex is not None: C *= (1 + float(plate.get('texture_k', 0.5)) * (tex - 1))[..., None]
    else: C *= (0.97 + 0.03 * np.clip(cv2.GaussianBlur(a, (0, 0), big * 0.12) * 1.6 - 0.3, 0, 1))[..., None]   # slight shading at the edges
    bd = plate.get('border')
    if bd:                                                      # solid border: a ring inside the plate edge
        bw = max(2, int(round(float(bd[0]) * big))); bc = np.array(bd[1] if len(bd) > 1 else color, np.float32)
        inner = cv2.erode((a > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * bw + 1, 2 * bw + 1)))
        ring = np.clip(a - cv2.GaussianBlur(inner.astype(np.float32), (0, 0), 0.8), 0, 1)[..., None]
        C = C * (1 - ring) + bc * ring
    if shape == 'stitch' and not bare:
        sm = _stitch(a, m, w, h, inset=max(10, int(0.08 * big)), width=max(3, 0.022 * big), dash=0.09 * big, gap=0.06 * big)
        C = C * (1 - sm[..., None]) + np.array(plate.get('stitch', DEFAULT_PLATE['stitch']), np.float32) * sm[..., None]
    ox, oy = m + px, m + py                                     # text block lands on whole pixels
    sl = (slice(oy, oy + th), slice(ox, ox + tw))
    A = np.maximum(a, 0)
    if not bare:
        C[sl] = C[sl] * (1 - T[..., None]) + color * T[..., None]
        A[sl] = np.maximum(A[sl], T)
    so = plate.get('shadow', DEFAULT_PLATE['shadow'])
    S = np.zeros_like(A)
    if so and so[2] > 0:
        dx = int(round(so[0] * 0.8)); dy = int(round(so[0]))
        S[dy:, dx:] = a[:a.shape[0] - dy, :a.shape[1] - dx]
        S = cv2.GaussianBlur(S, (0, 0), max(0.5, so[1])) * so[2]
    return Tag((np.clip(C, 0, 1) * A[..., None]).astype(np.float32), A.astype(np.float32), S.astype(np.float32), 1.0)


def _with_sub(main, sub, style, short, root, seed):
    """main card + a separate coloured subtitle strip at its bottom edge -> one Tag (strip overlaps the main plate's bottom edge a little)"""
    if isinstance(sub, str): sub = dict(text=sub)
    ts = (style_title(style) if style else {})
    so = dict((animi.style_info(style).get('title') or {}).get('sub') or {}) if style else {}
    mp = ts.get('plate', DEFAULT_PLATE) if ts else DEFAULT_PLATE
    pl = dict(DEFAULT_PLATE, **dict(mp, texture=None, pad=[0.5, 0.22], rough=4))
    pl.update(so.get('plate') or {}); pl.update(sub.get('plate') or {})
    col = sub.get('color', so.get('color', mp.get('color', DEFAULT_PLATE['color'])))
    if 'color' not in (so.get('plate') or {}) and 'color' not in (sub.get('plate') or {}):
        pl['color'] = list(ts.get('color', INK)) if ts else list(INK)
    t2 = title_tag(sub['text'], sub.get('size', 66), col, pl, style, 'sub', short, root=root, seed=seed + 17)
    h1, w1 = main.A.shape; h2, w2 = t2.A.shape
    ov = int(round(h2 * float(sub.get('gap', -0.18))))             # negative = overlaps the main plate's bottom edge
    W_ = max(w1, w2); H_ = h1 + h2 + ov
    P = np.zeros((H_, W_, 3), np.float32); A = np.zeros((H_, W_), np.float32); S = np.zeros((H_, W_), np.float32)
    for t, x, y in ((main, (W_ - w1) // 2, 0), (t2, (W_ - w2) // 2, h1 + ov)):
        h, w = t.A.shape; sl = (slice(y, y + h), slice(x, x + w))
        S[sl] = np.maximum(S[sl] * (1 - t.A), t.S)
        P[sl] = P[sl] * (1 - t.A[..., None]) + t.P; A[sl] = A[sl] * (1 - t.A) + t.A
    return Tag(P, A, S * (1 - A), 1.0)


def put_tag(frame, tag, cx, cy, alpha=1.0, lift=0.0):
    """Paste the card centred at (cx, cy) (rounded to whole pixels, no scaling or rotation, so text is never blurred by
    interpolation). lift 0–1: how high the plate is above the table (shadow farther, fainter, softer); for the first one or
    two drawings of a drop. Modifies frame in place"""
    h, w = tag.A.shape; H_, W_ = frame.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(W_, x0 + w), min(H_, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0: return frame
    if tag.S.any():
        S = tag.S
        if lift > 0:
            off = int(round(12 * lift)); S = np.roll(np.roll(S, off, 0), int(off * 0.8), 1)
            S = cv2.GaussianBlur(S, (0, 0), 1 + 6 * lift) * (1 - 0.4 * lift)
        frame[fy0:fy1, fx0:fx1] *= (1 - alpha * S[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0])[..., None]
    sl = (slice(fy0 - y0, fy1 - y0), slice(fx0 - x0, fx1 - x0))
    A = tag.A[sl][..., None] * alpha
    frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1] * (1 - A) + tag.P[sl] * alpha
    return frame


# =====================================================================================
# Animated card: plate enters -> stitches sew on one by one -> letters drop one by one -> subtitle strip slides in
# Text still only translates, landing on whole pixels (no scaling, no rotation); only the bare plate may "stand up"
# (squashed from the bottom edge, then unfolded).
#   card = bookends.Card([('Title', 230, 'title')], style='fabric', short=H, root=film_folder)
#   bookends.draw_card(frame, card, cx, cy, p, plate_at=3, sew=(6, 15), glyph_at=card.stagger(8, 2))
#   rib = bookends.ribbon('Subtitle', style='fabric', short=H, root=film_folder)
#   bookends.draw_ribbon(frame, rib, card, cx, cy, p, 19, side=-1)
# Paste on every drawing after the grade (text stays flat colour). p is the drawing number (on twos).
# =====================================================================================
DROP = {0: (-0.13, 1.0), 1: (-0.035, 0.45), 2: (0.012, 0.0)}        # first three drawings of a letter drop: height (times frame height), lift off the plate
PLATE_DROP = {0: (-0.55, 1.0), 1: (-0.10, 0.5), 2: (0.010, 0.0)}   # plate drops from above
PLATE_POP = {0: 0.12, 1: 0.55, 2: 1.06}                          # plate stands up from its bottom edge (paper, stiff card): height fraction
SLIDE = {0: -0.36, 1: -0.12, 2: -0.025, 3: 0.008}                 # strip slides in from the side: distance from its landing point (times frame width)


class Card:
    """An animated card: tag = plate only (bare), glyphs = each letter (CJK split per character, Latin one block per line), dashes = stitches (stitch plate)"""
    def __init__(self, lines, style=None, short=1080, root=None, seed=3, color=None):
        st = style_title(style); pl = dict(st['plate'])
        self.color = np.array(color if color is not None else st['color'], np.float32)
        self.stitch_color = np.array(pl.get('stitch', DEFAULT_PLATE['stitch']), np.float32)
        self.tag = title_tag(None, lines=lines, style=style, short=short, root=root, seed=seed, bare=True)
        rws = []
        for s, sz, rl in lines:
            sz = _min_size(sz, rl, short); rws.append((s, sz, text_alpha(s, sz)))
        gap = [int(0.28 * max(rws[i][1], rws[i + 1][1])) for i in range(len(rws) - 1)]
        tw = max(a.shape[1] for *_, a in rws); th = sum(a.shape[0] for *_, a in rws) + sum(gap)
        big = max(sz for _, sz, _ in rws)
        px, py = [int(round(v * big)) for v in pl.get('pad', [0.45, 0.30])]
        m = 24; w, h = tw + 2 * px, th + 2 * py
        self.h, self.w = self.tag.A.shape
        self.top = m                                       # y of the plate's top edge in the card image (for a character standing on it)
        self.glyphs = []
        y = 0
        for i, (s, sz, a) in enumerate(rws):
            x = (tw - a.shape[1]) // 2
            f = fx.font('siyuan', sz); bx0 = f.getbbox(s)[0]
            if _is_latin(s) or len(s) == 1: pieces = [(a, 0)]
            else:                                          # lay out the whole line, then split by glyph width: positions match the full line
                cuts = [0] + [int(round(2 - bx0 + f.getlength(s[:k]))) for k in range(1, len(s))] + [a.shape[1]]
                pieces = [(a[:, cuts[k]:cuts[k + 1]], cuts[k]) for k in range(len(s))]
            for k, (g, gx) in enumerate(pieces):
                self.glyphs.append(dict(row=i, k=k, a=g, x=m + px + x + gx, y=m + py + y))
            y += a.shape[0] + (gap[i] if i < len(gap) else 0)
        self.dashes, self._sm, self.sw = [], {}, max(3, 0.022 * big)
        if pl.get('shape') == 'stitch':                    # stitches: a ring inside the rounded corners, dashes ordered by arc length from the top-left
            inset = max(10, int(0.08 * big)); dash, gp = 0.09 * big, 0.06 * big; S = 2
            path = Image.new('L', (self.w * S, self.h * S), 0)
            r = max(4, corner(w, h) - inset)
            ImageDraw.Draw(path).rounded_rectangle(((m + inset) * S, (m + inset) * S, (m + w - inset) * S, (m + h - inset) * S),
                                                   radius=r * S, fill=255)
            cs, _ = cv2.findContours(np.asarray(path), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            pts = max(cs, key=len)[:, 0, :].astype(np.float32)
            pts = np.roll(pts, -int(np.argmin(pts[:, 0] + pts[:, 1] * 3)), 0)
            seg = np.hypot(*np.diff(np.vstack([pts, pts[:1]]), axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)])
            u = 0.0
            while u + dash * S < cum[-1]:
                a0, a1 = np.searchsorted(cum, u), np.searchsorted(cum, u + dash * S)
                self.dashes.append(pts[a0:max(a0 + 2, a1)].astype(np.int32)); u += (dash + gp) * S

    def stagger(self, p0, step=2, rows=None):
        """drawing where each letter starts dropping: one every step drawings from p0; rows limits it to these lines (other lines None = fade in)"""
        out, k = [], 0
        for g in self.glyphs:
            if rows is None or g['row'] in rows: out.append(p0 + step * k); k += 1
            else: out.append(None)
        return out

    def stitch(self, n):
        n = max(0, min(len(self.dashes), int(n)))
        if n not in self._sm:
            S = 2; out = np.zeros((self.h * S, self.w * S), np.uint8)
            for q in self.dashes[:n]: cv2.polylines(out, [q], False, 255, max(2, int(round(self.sw * S))), cv2.LINE_AA)
            self._sm[n] = cv2.resize(out, (self.w, self.h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        return self._sm[n]

    def origin(self, cx, cy):
        return int(round(cx - self.w / 2)), int(round(cy - self.h / 2))


def paste(frame, a, x, y, color, alpha=1.0):
    """paste a flat-colour alpha at whole pixel (x, y) (top-left), in place"""
    h, w = a.shape; Hh, Ww = frame.shape[:2]
    fx0, fy0, fx1, fy1 = max(0, x), max(0, y), min(Ww, x + w), min(Hh, y + h)
    if fx1 <= fx0 or fy1 <= fy0: return
    A = a[fy0 - y:fy1 - y, fx0 - x:fx1 - x][..., None] * alpha
    frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1] * (1 - A) + np.asarray(color, np.float32) * A


def _shade(frame, a, x, y, k):
    h, w = a.shape; Hh, Ww = frame.shape[:2]
    fx0, fy0, fx1, fy1 = max(0, x), max(0, y), min(Ww, x + w), min(Hh, y + h)
    if fx1 <= fx0 or fy1 <= fy0: return
    frame[fy0:fy1, fx0:fx1] *= (1 - k * a[fy0 - y:fy1 - y, fx0 - x:fx1 - x])[..., None]


def _drop(p, p0, table):
    k = p - p0
    if k < 0: return None
    return table.get(k, (0.0, 0.0))


def _pop_tag(tag, k):
    """squash the bare plate from its bottom edge to k times its height"""
    h, w = tag.A.shape; nh = max(2, int(round(h * k)))
    r = lambda x: cv2.resize(x, (w, nh), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR)
    P, A, S = np.zeros_like(tag.P), np.zeros_like(tag.A), np.zeros_like(tag.S)
    if nh <= h: P[h - nh:], A[h - nh:], S[h - nh:] = r(tag.P), r(tag.A), r(tag.S)
    else: P[:], A[:], S[:] = r(tag.P)[nh - h:], r(tag.A)[nh - h:], r(tag.S)[nh - h:]
    return Tag(P, A, S, 1.0)


def draw_card(frame, card, cx, cy, p, plate_at, sew=None, glyph_at=None, glyph_alpha=None, enter='drop'):
    """The card at drawing p. plate_at: drawing where the plate enters; enter='drop' from above / 'pop' stands up from
    the bottom edge; sew=(start drawing, done drawing): stitches sew on one by one (stitch plate); glyph_at[i]: drawing
    where letter i starts dropping, None = fade in by glyph_alpha(p).
    -> card top-left (x0, y0), None before it appears. Modifies frame in place"""
    H_ = frame.shape[0]
    k = p - plate_at
    if k < 0: return None
    if enter == 'pop':
        put_tag(frame, _pop_tag(card.tag, PLATE_POP[k]) if k in PLATE_POP else card.tag, cx, cy)
        dy = 0
    else:
        dy, lift = PLATE_DROP.get(k, (0.0, 0.0)); dy = int(round(dy * H_))
        put_tag(frame, card.tag, cx, cy + dy, lift=lift)
    x0, y0 = card.origin(cx, cy + dy)
    if sew and card.dashes and p >= sew[0]:
        n = len(card.dashes) * min(1.0, (p - sew[0] + 1) / max(1, sew[1] - sew[0] + 1))
        paste(frame, card.stitch(n), x0, y0, card.stitch_color)
    if enter == 'pop' and k < 3: return x0, y0                     # plate not upright yet: no text
    glyph_at = glyph_at or [plate_at + 3] * len(card.glyphs)
    for i, g in enumerate(card.glyphs):
        if glyph_at[i] is None:
            al = glyph_alpha(p) if glyph_alpha else 1.0
            if al > 0: paste(frame, g['a'], x0 + g['x'], y0 + g['y'], card.color, al)
            continue
        d = _drop(p, glyph_at[i], DROP)
        if d is None: continue
        gy, gl = int(round(d[0] * H_)), d[1]
        if 0 < gl < 1:                                             # the drawing just before landing: faint shadow under the letter (not while high, or it reads as a double image)
            sh = cv2.GaussianBlur(np.pad(g['a'], 30), (0, 0), 6)
            _shade(frame, sh, x0 + g['x'] - 25, y0 + g['y'] - 22, 0.16)
        paste(frame, g['a'], x0 + g['x'], y0 + g['y'] + gy, card.color)
    return x0, y0


def ribbon(text, size=76, style=None, short=1080, root=None, seed=3, stitch=None):
    """subtitle strip (colours from the style's title.sub; on a stitch plate the strip stitches use the stitch colour, default off-white)"""
    st = style_title(style); so = dict((animi.style_info(style).get('title') or {}).get('sub') or {}) if style else {}
    pl = dict(st['plate'], texture=None, pad=[0.5, 0.22], rough=4)
    pl.update(so.get('plate') or {}); pl['stitch'] = stitch or [0.99, 0.96, 0.88]
    col = so.get('color', st['plate'].get('color', DEFAULT_PLATE['color']))
    if 'color' not in (so.get('plate') or {}): pl['color'] = list(st['color'])     # no title.sub: strip uses the title's text colour and text uses the plate colour (swapped, same as preview)
    return title_tag(text, size, col, pl, style, 'sub', short, root=root, seed=seed + 17)


def draw_ribbon(frame, rib, card, cx, cy, p, p0, side=-1, overlap=0.18):
    """strip slides in at drawing p0 from left (side=-1) / right (1) onto the card's bottom edge (overlapping by overlap times strip height)"""
    k = p - p0
    if k < 0: return
    dx = int(round(SLIDE.get(k, 0.0) * frame.shape[1])) * (1 if side < 0 else -1)
    h2 = rib.A.shape[0]
    put_tag(frame, rib, cx + dx, cy + card.h / 2 - overlap * h2 + h2 / 2, lift=0.3 if k < 2 else 0.0)


# =====================================================================================
# Bookends
# =====================================================================================
def _probe(mp4):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height,r_frame_rate',
                        '-of', 'json', mp4], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout); v = next(s for s in d['streams'] if s['codec_type'] == 'video')
    num, den = v['r_frame_rate'].split('/')
    return float(d['format']['duration']), int(v['width']), int(v['height']), float(num) / float(den), \
        any(s['codec_type'] == 'audio' for s in d['streams'])


def _grab(mp4, t, tmp):
    p = os.path.join(tmp, 'grab.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0.0, t):.3f}', '-i', mp4, '-frames:v', '1', p], check=True)
    return kit.rd(p)


def _scene(bg, pic, n, zoom0, zoom1, W, H, seed):
    """bookend background: one picture slowly pushing in or out (no per-drawing jitter)"""
    u = kit.ease(pic / max(1, n - 1))
    cam = animi.Cam(W, H, W / 2, H / 2, zoom0 + (zoom1 - zoom0) * u, bg.shape[1], bg.shape[0])
    cam.k0 = max(W / bg.shape[1], H / bg.shape[0])
    return np.ascontiguousarray(cam.plate(bg), np.float32)


def _land(pic, p0):
    """plate drop: highest above the table at drawing p0 (lift 1), settled two drawings later; not drawn before -> lift or None"""
    k = pic - p0
    if k < 0: return None
    return {0: 1.0, 1: 0.35}.get(k, 0.0)


def _sound(style, events, dur, tail, music_hits):
    """Bookend sound: foley in the style's material for the plate landing, with a hit in the style's instrumentation
    and a tonic chord. A foley sound sits on the seam with the film (the title card being pulled away); no silent gap."""
    from audio.sfx import SR, add
    from audio import foley
    buf = np.zeros((int((dur + 2) * SR), 2), np.float32)
    info = animi.style_info(style) if style else {}
    mat = (info.get('foley') or {}).get('material')
    for kinds, t, v, pitch in events:
        for k in kinds:
            try: x = foley.make(k, mat, v=v, pitch=pitch)
            except KeyError: continue
            add(buf, x, t, 1.0); break
    mus = info.get('music')
    if mus and music_hits:
        try:
            from audio import compose
            # no bars (energy -1): a tonic chord lands on the hit and rings until just before the clip ends; foley sits around the seam separately
            plan = dict(sections=[dict(t=0, energy=-1), dict(t=music_hits[0][1], end=True)],
                        hits=[dict(t=t, kind=k) for k, t in music_hits])
            m, _ = compose.render(plan, mus, dur)
            n = min(len(m), len(buf)); buf[:n] += m[:n] * 0.8
        except Exception as e:
            print(f'bookends: score hit failed ({e}); foley only', file=sys.stderr)
    buf = buf[:int(round(dur * SR))]
    if tail:
        f = int(0.6 * SR); buf[-f:] *= np.linspace(1, 0, f)[:, None]
    pk = float(np.abs(buf).max())
    if pk > 0.9: buf *= 0.9 / pk
    return buf, SR


def _write(frames, on, fps, audio, sr, out, tmp, name):
    d = os.path.join(tmp, name); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    i = 0
    for f in frames:
        for _ in range(on): kit.wr(f'{d}/f{i:04d}.png', np.clip(f, 0, 1)); i += 1
    import soundfile as sf
    wav = os.path.join(tmp, name + '.wav'); sf.write(wav, audio, sr)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(fps), '-i', f'{d}/f%04d.png', '-i', wav,
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
                    '-ac', '2', '-shortest', out], check=True)
    shutil.rmtree(d, ignore_errors=True)
    return i / fps


def style_motion(style=None):
    """Read the style's title.motion (how the card enters); defaults fill the gaps:
    enter: 'drop' plate drops from above (soft materials, cloth, yarn, wood, tin) / 'pop' plate stands up from its bottom
    edge (paper, cardboard and other stiff cards);
    step: interval between letters dropping (drawings); sub_side: side the subtitle strip slides in from (-1 left / 1 right)"""
    m = {}
    if style:
        try: m = dict((animi.style_info(style).get('title') or {}).get('motion') or {})
        except SystemExit: m = {}
    shape = style_title(style)['plate'].get('shape')
    return dict(enter=m.get('enter', 'pop' if shape == 'cut' else 'drop'), step=int(m.get('step', 2)),
                sub_side=int(m.get('sub_side', -1)))


class _Hero:
    """The character that lands on the title card: a few transparent cells (first in the air, last settled), feet aligned to the card's top edge"""
    def __init__(self, paths, h):
        self.cells = []
        for p in paths:
            raw = cv2.imread(p, cv2.IMREAD_UNCHANGED)
            if raw is None or raw.ndim != 3 or raw.shape[2] != 4: raise SystemExit(f'bookends: --hero needs a transparent png: {p}')
            a = raw[:, :, 3].astype(np.float32) / 255; ys, xs = np.nonzero(a > 0.5)
            raw = raw[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            k = h / raw.shape[0]
            raw = cv2.resize(raw, (max(1, int(raw.shape[1] * k)), int(h)), interpolation=cv2.INTER_AREA)
            self.cells.append((raw[:, :, 2::-1].astype(np.float32) / 255, raw[:, :, 3].astype(np.float32) / 255))

    def draw(self, frame, i, cx, foot, lift=0.0, sy=1.0):
        I, a = self.cells[min(i, len(self.cells) - 1)]
        if sy != 1.0:
            nh = max(2, int(round(a.shape[0] * sy))); nw = max(2, int(round(a.shape[1] / math.sqrt(sy))))
            I = cv2.resize(I, (nw, nh)); a = cv2.resize(a, (nw, nh))
        h, w = a.shape; x0, y0 = int(round(cx - w / 2)), int(round(foot - h - lift))
        sh = cv2.GaussianBlur((a > 0.3).astype(np.float32)[-max(4, h // 12):], (0, 0), 6)    # contact shadow under the feet
        _shade(frame, cv2.resize(sh, (w, max(4, h // 12))), x0, int(foot) - max(4, h // 12) // 2, 0.35 * (1 - min(1, lift / (h + 1))))
        Hh, Ww = frame.shape[:2]
        fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(Ww, x0 + w), min(Hh, y0 + h)
        if fx1 <= fx0 or fy1 <= fy0: return
        A = a[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0][..., None]
        frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1] * (1 - A) + I[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0] * A


HERO_FALL = {0: 1.0, 1: 0.55, 2: 0.18, 3: 0.0}                       # character jumping onto the card: height above the card's top edge (times character height)
EXIT_UP = {0: -0.015, 1: -0.10, 2: -0.42}                            # end of the title card: whole card pulled up and away (times frame height)


def _sheet(frames, out, every=3, cols=6):
    """one drawing every `every` drawings tiled into a small sheet (for self-review)"""
    picks = frames[::every]
    if not picks: return
    h, w = picks[0].shape[:2]; s = 320 / w
    tiles = [cv2.resize(np.clip(f, 0, 1), (320, int(h * s))) for f in picks]
    while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
    kit.wr(out, np.vstack([np.hstack(tiles[r * cols:(r + 1) * cols]) for r in range(len(tiles) // cols)]))


def make(film, title, credit=None, end=None, style=None, out=None, sec=3.0, bg_head=None, bg_tail=None, root=None, sub=None,
         hero=None, hero_side=1, rigid=None, y=None, y_tail=None, lang=None):
    """Add animated bookends to the film -> (output mp4, shot list path, title seconds, end seconds). Same rhythm for
    every style; the look comes from the style's title:
    title card (over the film's first frame, camera slowly pushing back to 1.0): plate enters (title.motion.enter: drop /
          stand up) -> stitch plate sews on -> title drops letter by letter -> subtitle strip slides in (with sub) ->
          character jumps onto the card (with hero) -> hold -> whole card pulled up and away; the last drawing is the
          film's first frame (no black);
    end card (holding on the film's last frame): plate enters -> stitches -> end text drops -> credit fades in -> hold to
          the end, sound fades out.
    end: end card first line; None = END_TEXT for the film language (lang, else sound.json's lang, else the title's script).
    hero: list of character cell pngs (transparent; first in the air, last settled; one is fine), standing on the card's
          top edge on the hero_side side; do not use it when the hero is already visible in the film's first frame
          (there would be two heroes);
    rigid: rigid materials do not squash on landing (default: the style's preset.rigid). Text only translates, whole
    pixels, no scaling or rotation.
    y / y_tail: title / end card centre height (fraction of frame height); default frame centre (same for every film);
    change only in special cases."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(film)))
    if end is None: end = END_TEXT[film_lang(lang, root, title)]
    dur, W, H, fps, has_audio = _probe(film)
    info = animi.style_info(style) if style else {}
    pre = info.get('preset') or {}
    on = int(pre.get('on', 2)); rigid = bool(pre.get('rigid')) if rigid is None else rigid
    short = min(W, H); ps = fps / on
    tmp = os.path.join(root, 'work', 'bookends'); os.makedirs(tmp, exist_ok=True)
    out = out or os.path.splitext(film)[0] + '-bookends.mp4'
    st, mo = style_title(style), style_motion(style)
    snd = st['sound']; tap = ['tap', 'pop', 'thud']
    first = _grab(film, 0.0, tmp); last = _grab(film, max(0.0, dur - 1.5 / fps), tmp)
    if bg_head: first = kit.rd(bg_head)
    if bg_tail: last = kit.rd(bg_tail)
    n = max(30, int(round(sec * ps)))
    stitch = st['plate'].get('shape') == 'stitch'
    # ---- title card ----
    card = Card(title_rows(title, W, short), style=style, short=short, root=root)
    rib_h = int(0.09 * short) if sub else 0                          # card + strip centred as one block
    cx, cy = W / 2, (H * y if y is not None else H / 2 + (0.12 * H if hero else 0) - rib_h * 0.4)
    PA = 3; sew = (PA + 3, PA + 12) if stitch and card.dashes else None
    step = mo['step'] if len(card.glyphs) * mo['step'] <= 0.4 * n else 1    # long titles drop faster so the card still holds ~1 s
    g0 = PA + (5 if sew else 4); gat = card.stagger(g0, step)
    land_g = max(gat) + 2
    rib = ribbon(sub, style=style, short=short, root=root) if sub else None
    rib_at = land_g + 1 if rib else None
    hz = None
    if hero:
        hz = _Hero(hero, 0.26 * H); hero_at = (rib_at or land_g) + 3
    ex = n - 4                                                         # pulled away from the fourth-last drawing (three drawings); the last is the clean first frame of the film
    frames, ev = [], [(snd, (PA + (2 if mo['enter'] == 'pop' else 1)) / ps, 0.7, 1.0)]
    ev += [(tap, (a + 2) / ps, 0.22, 1.25 + 0.05 * (i % 3)) for i, a in enumerate(gat) if a is not None]
    if rib: ev.append((['flap', 'whoosh', 'tap'], rib_at / ps, 0.35, 1.1))
    if hz: ev.append((['thud', 'step', 'tap'], (hero_at + 3) / ps, 0.6, 0.9))
    ev.append((['whoosh', 'flap', 'tap'], ex / ps, 0.35, 1.2))
    for p in range(n):
        f = _scene(first, p, n, 1.035, 1.0, W, H, 100)
        if p < n - 1:
            dy = int(round(EXIT_UP.get(p - ex, 0.0) * H)) if p >= ex else 0
            org = draw_card(f, card, cx, cy + dy, p, PA, sew=sew, glyph_at=gat, enter=mo['enter'])
            if rib: draw_ribbon(f, rib, card, cx, cy + dy, p, rib_at, side=mo['sub_side'])
            if hz and org and p >= hero_at:
                k = p - hero_at; foot = org[1] + card.top + 6
                hx = cx + hero_side * card.w * 0.30
                lift = HERO_FALL.get(k, 0.0) * hz.cells[0][1].shape[0]
                sy = 1.0 if rigid else {4: 0.9, 5: 1.04}.get(k, 1.0)          # soft materials squash on landing, rebound, settle
                hz.draw(f, 0 if k < 3 else len(hz.cells) - 1, hx, foot, lift=lift, sy=sy)
        frames.append(f)
    a, sr = _sound(style, ev, n * on / fps, False, [('accent', (land_g) / ps)])
    hm = os.path.join(tmp, 'head.mp4'); hd = _write(frames, on, fps, a, sr, hm, tmp, 'head')
    _sheet(frames, os.path.join(root, 'work', 'bookends_head.jpg'))
    # ---- end card ----
    rows = title_rows(end or END_TEXT[film_lang(lang, root, title)], W, short)
    if credit: rows.append((credit, int(56 * short / 1080), 'credit'))
    tc = Card(rows, style=style, short=short, root=root, seed=5)
    tsew = (PA + 3, PA + 12) if stitch and tc.dashes else None
    tg0 = PA + (5 if tsew else 4); tgat = tc.stagger(tg0, mo['step'], rows=[0])
    c0 = max(a for a in tgat if a is not None) + 4
    fade = lambda p: min(1.0, max(0.0, (p - c0 + 1) / 4))
    tcy = H * (y_tail if y_tail is not None else 0.5)
    frames = []
    for p in range(n):
        f = _scene(last, p, n, 1.0, 1.03, W, H, 200)
        draw_card(f, tc, W / 2, tcy, p, PA, sew=tsew, glyph_at=tgat, glyph_alpha=fade, enter=mo['enter'])
        frames.append(f)
    tev = [(snd, (PA + 1) / ps, 0.7, 0.9)] + [(tap, (a + 2) / ps, 0.25, 1.2) for a in tgat if a is not None]
    a, sr = _sound(style, tev, n * on / fps, True, [('stop', (max(a for a in tgat if a is not None) + 2) / ps)])
    tm = os.path.join(tmp, 'tail.mp4'); td = _write(frames, on, fps, a, sr, tm, tmp, 'tail')
    _sheet(frames, os.path.join(root, 'work', 'bookends_tail.jpg'))
    # concat: add silence when the film has no audio track
    src = film
    if not has_audio:
        src = os.path.join(tmp, 'film_a.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', film, '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
                        '-c:v', 'copy', '-c:a', 'aac', '-shortest', src], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', hm, '-i', src, '-i', tm, '-filter_complex',
                    '[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]', '-map', '[v]', '-map', '[a]',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-c:a', 'aac', '-b:a', '192k', out], check=True)
    sj = os.path.splitext(film)[0] + '.shots.json'
    base = json.load(open(sj)) if os.path.exists(sj) else dict(dur=dur, shots=[dict(t=0, name='film', size='', bg='')])
    shots = [dict(t=0, name='title card', size='title', bg='')] + [dict(x, t=round(float(x['t']) + hd, 3)) for x in base['shots']] + \
            [dict(t=round(hd + float(base['dur']), 3), name='end card', size='end', bg='')]
    for k, x in enumerate(shots):
        x['i'] = k
        if 't1' in x: x['t1'] = round(float(x['t1']) + hd, 3)
    oj = os.path.splitext(out)[0] + '.shots.json'
    json.dump(dict(dur=round(hd + float(base['dur']) + td, 3), shots=shots), open(oj, 'w'), ensure_ascii=False, indent=1)
    nm = os.path.splitext(os.path.basename(film))[0]                   # narration subtitles shifted by the title card
    for s in (os.path.join(root, nm + '.srt'), os.path.splitext(film)[0] + '.srt'):
        if os.path.exists(s):
            with open(os.path.splitext(out)[0] + '.srt', 'w', encoding='utf-8') as f: f.write(shift_srt(open(s, encoding='utf-8').read(), hd))
            break
    return out, oj, hd, td


def shift_srt(text, sec):
    """Move every SRT timestamp later by sec seconds."""
    def one(m):
        ms = ((int(m[1]) * 60 + int(m[2])) * 60 + int(m[3])) * 1000 + int(m[4]) + int(round(sec * 1000))
        return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'
    return re.sub(r'(\d+):(\d\d):(\d\d)[,.](\d{3})', one, text)


def preview(title, credit=None, style=None, bg=None, W=1920, H=1080, out='work/_titles.jpg', root=None, sub=None, end=None, lang=None):
    """Text and plates only: title card and end card side by side in one image (on bg or mid grey)"""
    if end is None: end = END_TEXT[film_lang(lang, root, title)]
    base = kit.rd(bg) if bg else np.full((H, W, 3), 0.55, np.float32)
    if base.shape[:2] != (H, W): base = kit.fit(base, W, H)
    short = min(W, H); tiles = []
    a = base.copy(); put_tag(a, title_tag(None, lines=title_rows(title, W, short), style=style, short=short, root=root, sub=sub), W / 2, H / 2)
    rows = title_rows(end, W, short) + ([(credit, int(56 * short / 1080), 'credit')] if credit else [])
    b = base.copy(); put_tag(b, title_tag(None, lines=rows, style=style, short=short, root=root, seed=5), W / 2, H / 2)
    kit.wr(out, np.hstack([a, b])); return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog='bookends.py', description='Optional bookends (off by default: run only when the user asks)')
    ap.add_argument('film', help='film mp4, or preview')
    ap.add_argument('--title', required=True, help='title')
    ap.add_argument('--credit', help="credit (the user's own words; none if not given)")
    ap.add_argument('--sub', help='subtitle under the title (optional)')
    ap.add_argument('--end', help='end card first line; default "The End" in the film language (zh 完, en The End), or the title')
    ap.add_argument('--lang', choices=['zh', 'en'], help='film language for default text; default: sound.json lang, else the title script')
    ap.add_argument('--style', help='style id (plate, text colour, foley and score hits come from its style.json)')
    ap.add_argument('--out', help='output mp4 (default <film>-bookends.mp4)')
    ap.add_argument('--sec', type=float, default=3.0, help='seconds for the title card and for the end card (2.5-4)')
    ap.add_argument('--hero', nargs='+', help='character that jumps onto the title card: transparent cell pngs (first in the air, last settled; one is fine)')
    ap.add_argument('--hero-side', type=int, default=1, help="which side of the card's top edge the character stands on: 1 right (default) / -1 left")
    ap.add_argument('--y', type=float, help='title card centre height (fraction of frame height); default frame centre, rarely changed')
    ap.add_argument('--y-tail', type=float, help='end card centre height; default frame centre, rarely changed')
    ap.add_argument('--bg', help='background image for preview')
    g = ap.parse_args(argv)
    if g.film == 'preview':
        print(preview(g.title, g.credit, g.style, g.bg, out=g.out or 'work/_titles.jpg', root=os.getcwd(), sub=g.sub, end=g.end, lang=g.lang)); return 0
    out, oj, hd, td = make(g.film, g.title, g.credit, g.end, g.style, g.out, g.sec, sub=g.sub, hero=g.hero, hero_side=g.hero_side, y=g.y, y_tail=g.y_tail, lang=g.lang)
    print(f'{out}  title card {hd:.1f}s + film + end card {td:.1f}s; shot list {oj}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
