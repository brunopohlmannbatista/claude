# animi.py -- high-level stop-motion tools (built on kit.py): style packages and prompts, sheet QC, slicing sheets by
#             subject (transparent background -> RGBA cells), anchors, placing by foot point, a timesheet counted in
#             drawings, contact shadows, holdout layers, cameras, transitions, subtitles, style finish.
#
# CLI:
#   python animi.py styles [--lang en]                       list the fixed styles
#   python animi.py prompt <style> <kind> <slots.txt> -o <prompt.txt> [--size landscape]   assemble one asset prompt
#   python animi.py check  <sheet.png> [--n 8] [--rows 2] [--cols 4] [--out preview.jpg] [--allow-edge bottom] [--clean] [--float]
#       QC: subject count, size spread, ground line, crossing cell lines, transparent edges, stray specks -> PASS / WARN / FAIL
#   python animi.py clean  <transparent.png> <out.png>          remove the semi-transparent haze from a transparent background
#   python animi.py slice  <sheet.png> <outdir> <prefix> [--n 8] [--rows 2] [--cols 4] [--fragments keep|drop] [--group grid]
#       slice by subject into <prefix>_0.png ... (RGBA when transparent; same canvas, bottoms aligned, neighbours' pixels removed)
#   python animi.py anchors <cells dir> [--prefix p] [--json out.json] [--preview preview.jpg]
#       per cell: foot y, body centre x, centre of the bottom 20%, bbox
#   python animi.py live <film.mp4> [--out timeline.png]       find stretches where the whole frame barely moves
#
# In a film script (full example in film_template.py):
#   A = animi.load_anchors('work/anchors_toss.json')
#   cel = {k: kit.sprite('work/cells', None, k) for k in A}       # RGBA cells, no mask needed
#   s = A.scale_ref(HERO_H, 'toss_0')                               # the standing cell sets the reference height
#   animi.place_at(frame, cel['toss_3'], x, ground_y, s, info=A['toss_3'])
# Full API: references/api.md.
import os, sys, re, json, glob, math, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import numpy as np, cv2
    import kit
except ImportError:                 # `animi.py styles` must work with the system python3 before the env exists (opening questions)
    if not (__name__ == '__main__' and sys.argv[1:2] == ['styles']): raise
    np = cv2 = kit = None

INK = (0.10, 0.10, 0.115)          # ink colour (slightly cool black)


# =====================================================================================
# Reading images and subject masks
# =====================================================================================
def _load_rgb(img):
    """path / uint8 / float -> float32 RGB 0-1"""
    if isinstance(img, str): return kit.rd(img)
    img = np.asarray(img)
    if img.dtype == np.uint8: return img[..., :3].astype(np.float32) / 255
    return img[..., :3].astype(np.float32)


def norm_alpha(a):
    """Image-model alpha (0-255 or 0-1) -> 0-1. Subject interiors are often 252-253 with 1-5 residue outside the edge:
    below 0.02 -> 0, above 0.97 -> 1, linear in between (keeps fur and soft edges)."""
    a = np.asarray(a, np.float32)
    if a.max() > 1.5: a = a / 255
    return np.clip((a - 0.02) / 0.95, 0, 1).astype(np.float32)


def clean_alpha(a, lo=225, hi=248, min_area=400):
    """Remove semi-transparent haze from a transparent background (shadows or paper drawn as alpha 100-200):
    restretch alpha (0-255 or 0-1) over [lo, hi] (0-255 scale), then drop specks smaller than min_area (fx sheets
    have small pieces: use ~20). Subjects sit around alpha 250, haze usually below 200; keeps a 1-2 px edge. -> 0-1"""
    a = np.asarray(a, np.float32)
    if a.max() <= 1.5: a = a * 255
    na = np.clip((a - lo) / max(1.0, hi - lo), 0, 1)
    m = (na > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] > int(min_area)
    k = keep[lab].astype(np.uint8)
    na *= (cv2.dilate(k, np.ones((5, 5), np.uint8)) > 0)
    return na.astype(np.float32)


def haze_ratio(a):
    """Share of semi-transparent pixels (0.15-0.85). > 0.05 is usually haze, not a bad drawing: try clean first"""
    a = np.asarray(a, np.float32)
    if a.max() > 1.5: a = a / 255
    return float(((a > 0.15) & (a < 0.85)).mean())


def load_rgba(p, clean=False):
    """-> (I colour float RGB 0-1, a 0-1). a = None when there is no alpha channel or almost nothing is transparent.
    clean=True (or dict(lo=, hi=, min_area=)): remove semi-transparent haze first (clean_alpha)."""
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im is None: raise FileNotFoundError(p)
    if im.dtype != np.uint8: im = (im / 257).astype(np.uint8)
    if im.ndim == 2: im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    I = im[:, :, 2::-1].astype(np.float32) / 255 if im.shape[2] >= 3 else im.astype(np.float32) / 255
    if im.shape[2] < 4: return I, None
    if clean:
        a = clean_alpha(im[:, :, 3], **(clean if isinstance(clean, dict) else {}))
        I = I * (a[..., None] > 0)
    else:
        a = norm_alpha(im[:, :, 3])
    if (a < 0.5).mean() < 0.05: return I, None
    return I, a


def is_transparent(p):
    """Is this PNG a transparent-background asset (has alpha and at least 5% transparent pixels)"""
    try: return load_rgba(p)[1] is not None
    except FileNotFoundError: return False


def white_norm(I):
    """Normalise paper white to 1 per channel at the 99.5th percentile (white balance)"""
    return np.clip(I / np.maximum(np.percentile(I, 99.5, axis=(0, 1)), 0.5), 0, 1)


def _lum(I): return I[..., 0] * 0.299 + I[..., 1] * 0.587 + I[..., 2] * 0.114


def ink_density(img, gain=1.12, floor=0.025, white=None):
    """Ink / pencil on white -> ink density D (0 = paper, 1 = solid ink); keeps bleeds, dry brush, translucency.
    D = clip((white - L) / white * gain - floor); white defaults to the 99.5th luminance percentile."""
    L = _lum(_load_rgb(img))
    w = float(np.percentile(L, 99.5)) if white is None else float(white)
    return np.clip((w - L) / max(w, 1e-3) * gain - floor, 0, 1).astype(np.float32)


def nonwhite_mask(I, dark=0.5, chroma=0.12, drop_shadow=True):
    """Subject candidates on a white sheet: clearly dark (luminance < dark) or clearly coloured (max-min > chroma).
    Pale grey / lilac soft shadows fail both and are dropped; white inside the subject (belly, highlights) comes back
    via hole filling. drop_shadow: also drop achromatic, mid-grey, very smooth pixels (a cartoon's grey ellipse
    shadow, no outline, no texture); equally smooth grey fills inside the subject are enclosed by lines and come back."""
    J = white_norm(I); L = _lum(J); C = J.max(2) - J.min(2)
    m = (L < dark) | (C > chroma)
    if drop_shadow:
        mu = cv2.blur(L, (7, 7)); sd = np.sqrt(np.maximum(cv2.blur(L * L, (7, 7)) - mu * mu, 0))
        core = ((C < 0.05) & (L > 0.3) & (L < 0.85) & (sd < 0.02)).astype(np.uint8)
        zone = cv2.dilate(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))) > 0   # take the shadow's soft edge too
        m &= ~(zone & (C < 0.05) & (L > 0.3))
    return m.astype(np.uint8)


def fill_holes(m):
    """Fill enclosed holes in a binary mask"""
    h, w = m.shape
    pad = np.zeros((h + 2, w + 2), np.uint8); pad[1:-1, 1:-1] = (m > 0)
    ff = pad.copy(); mask = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 2)
    return ((ff[1:-1, 1:-1] != 2)).astype(np.uint8)


def _ext_mask(mask, shape):
    if mask is None: return None
    if isinstance(mask, str):
        m = cv2.imread(mask, 0)
        if m is None: raise FileNotFoundError(mask)
    else: m = np.asarray(mask)
    if m.dtype != np.uint8: m = (np.clip(m, 0, 1) * 255).astype(np.uint8)
    if m.shape != shape: m = cv2.resize(m, (shape[1], shape[0]))
    return (m > 127).astype(np.uint8)


def birefnet_mask(img):
    """Run BiRefNet once on the whole image (needs onnxruntime and the model, see cut.py) -> uint8 0/1"""
    import cut
    I = _load_rgb(img)
    m = cut.predict(cut.session(), (np.clip(I, 0, 1) * 255).astype(np.uint8))
    return (m > 0.5).astype(np.uint8)


def subject_mask(I, mode='auto', mask=None, birefnet=False, dark=0.5, chroma=0.12, ink_th=0.05, alpha=None):
    """-> (raw subject pixels 0/1, group 0/1 used to split connected components).
    mode='alpha': transparent asset (default), raw = alpha > 0.5, holes filled; group = raw dilated 9 px (joins small detached parts).
    mode='auto': non-white threshold (| mask / BiRefNet), 7x7 close, holes filled; group = raw.
    mode='ink': ink density > ink_th; group = raw dilated 25 px (joins broken mane / dry-brush strokes).
    mode='mask': only the given mask (or BiRefNet)."""
    if mode == 'alpha':
        if alpha is None: raise ValueError("mode='alpha' needs a transparent PNG (alpha=)")
        raw = fill_holes(cv2.morphologyEx((alpha > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)))
        group = cv2.dilate(raw, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
        return raw, group
    ext = _ext_mask(mask, I.shape[:2])
    if birefnet:
        b = birefnet_mask(I); ext = b if ext is None else (ext | b)
    if mode == 'ink':
        raw = (ink_density(I) > ink_th).astype(np.uint8)
        if ext is not None: raw |= ext
        group = cv2.dilate(raw, np.ones((25, 25), np.uint8))
        return raw, group
    if mode == 'mask':
        if ext is None: raise ValueError("mode='mask' needs mask= or birefnet=True")
        raw = ext
    else:
        raw = nonwhite_mask(I, dark, chroma)
        if ext is not None: raw |= ext
    raw = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    raw = fill_holes(raw)
    if mode == 'mask': return raw, raw
    # Grouping: pale parts (white body, white belly) are not "non-white" enough and split off -> count loosely
    # not-pure-white pixels within 25 px of the subject, only to join pieces of one subject; arcs, symbols and flying
    # props separated by pure white stay separate pieces. The bbox still uses raw only (no shadow).
    J = white_norm(I)
    loose = ((1 - J.min(2)) > 0.04).astype(np.uint8)
    near = cv2.dilate(raw, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (51, 51)))
    group = fill_holes(raw | (loose & near))
    return raw, group


def _components(raw, group, min_area=40):
    """-> connected components (largest first), each with label, area (raw pixel count), bbox (raw), centroid"""
    k, lab, st, cen = cv2.connectedComponentsWithStats(group, 8)
    comps = []
    for i in range(1, k):
        sel = (lab == i)
        if group is raw:
            area = int(st[i, cv2.CC_STAT_AREA]); x, y, w, h = st[i, :4]; cx, cy = cen[i]
            if area < min_area: continue
            comps.append(dict(label=i, area=area, bbox=(int(x), int(y), int(x + w), int(y + h)), centroid=(float(cx), float(cy))))
        else:
            if st[i, cv2.CC_STAT_AREA] < min_area: continue
            ys, xs = np.nonzero(sel & (raw > 0))
            if len(xs) < min_area: continue
            comps.append(dict(label=i, area=int(len(xs)), bbox=(int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1),
                              centroid=(float(xs.mean()), float(ys.mean()))))
    comps.sort(key=lambda c: -c['area'])
    return comps, lab


def _order_rows(subs, rows, Hs):
    """Cluster into rows (split y centres at the largest gaps), sort by x within a row -> sorted list, each gets row"""
    if not subs: return []
    subs = sorted(subs, key=lambda c: c['centroid'][1])
    ys = [c['centroid'][1] for c in subs]
    medh = float(np.median([c['bbox'][3] - c['bbox'][1] for c in subs]))
    gaps = sorted(((ys[i + 1] - ys[i], i) for i in range(len(ys) - 1)), reverse=True)
    cuts = sorted(i for g, i in gaps[:max(0, rows - 1)] if g > 0.3 * medh)
    groups, s = [], 0
    for i in cuts: groups.append(subs[s:i + 1]); s = i + 1
    groups.append(subs[s:])
    out = []
    for r, g in enumerate(groups):
        for c in sorted(g, key=lambda c: c['centroid'][0]):
            c['row'] = r; out.append(c)
    return out


def _territory(lab, subs, shape):
    """Territory map: each pixel belongs to the nearest subject (1..n), via the distance transform's nearest-pixel label"""
    keep = np.zeros(shape, np.int32)
    for j, c in enumerate(subs): keep[lab == c['label']] = j + 1
    if not subs: return keep
    src = (keep == 0).astype(np.uint8)
    _, labels = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    lut = np.zeros(int(labels.max()) + 1, np.int32)
    lut[labels[keep > 0]] = keep[keep > 0]
    return lut[labels]


def _resolve(png, mode, clean=False):
    """Read a sheet; mode='auto' switches to 'alpha' for transparent PNGs. clean: remove haze first. -> (I, a, mode)"""
    if isinstance(png, str):
        I, a = load_rgba(png, clean)
    else:
        I, a = _load_rgb(png), None
    if mode == 'auto' and a is not None: mode = 'alpha'
    if mode == 'alpha' and a is None: raise ValueError(f'{png}: not a transparent PNG, cannot use mode="alpha"')
    return I, a, mode


def _grid_group(comps, lab, shape, rows, cols, min_area=12, raw=None):
    """Slice by equal grid cells (fx sheets, close-up sheets with two pieces per cell, subjects spanning two cells):
    pixels are first split by their grid cell; each cell keeps its largest piece (the part of a spanning subject) plus
    pieces mostly inside the cell (an fx cell has several pieces); pieces mostly in the next cell reach over and are
    cut at the cell line. -> (subs, lab2): label r*cols+c+1 in lab2 = pixels kept for that cell"""
    Hs, Ws = shape
    ys_ = (np.arange(rows + 1) * Hs / rows).round().astype(int); xs_ = (np.arange(cols + 1) * Ws / cols).round().astype(int)
    m = (raw > 0) if raw is not None else (lab > 0)
    cell_of = (np.minimum(rows - 1, np.arange(Hs) * rows // Hs)[:, None] * cols
               + np.minimum(cols - 1, np.arange(Ws) * cols // Ws)[None, :] + 1).astype(np.int64)
    L = lab.astype(np.int64); sel0 = (L > 0) & m
    cnt = np.zeros((int(L.max()) + 1, rows * cols + 1), np.int64)
    np.add.at(cnt, (L[sel0], cell_of[sel0]), 1)
    owner = cnt.argmax(1)                                  # which cell holds most of each component
    lab2 = np.zeros(shape, np.int32); subs = []
    for r in range(rows):
        for k in range(cols):
            g = r * cols + k + 1
            y0, y1, x0, x1 = ys_[r], ys_[r + 1], xs_[k], xs_[k + 1]
            n_, cl, st_, _ = cv2.connectedComponentsWithStats(m[y0:y1, x0:x1].astype(np.uint8), 8)
            if n_ < 2: continue
            big = 1 + int(np.argmax(st_[1:, 4]))
            Lc = L[y0:y1, x0:x1]
            keep = []
            for q in range(1, n_):
                if st_[q, 4] < min_area: continue
                ys0, xs0 = np.nonzero(cl == q)
                orig = int(np.bincount(Lc[ys0, xs0]).argmax())
                if q == big or owner[orig] == g: keep.append(q)
            if not keep: continue
            sel = np.isin(cl, keep)
            lab2[y0:y1, x0:x1][sel] = g
            yy, xx = np.nonzero(sel)
            subs.append(dict(label=g, area=int(sel.sum()), bbox=(int(xx.min()) + x0, int(yy.min()) + y0, int(xx.max()) + x0 + 1,
                             int(yy.max()) + y0 + 1), centroid=(float(xx.mean()) + x0, float(yy.mean()) + y0), row=r, pieces=len(keep)))
    return subs, lab2


def _grid_terr(lab2, raw, rows, cols):
    """Grid territory: each pixel belongs to its cell; pieces not kept in a cell (reaching over from next door) -> 0 (transparent)"""
    Hs, Ws = lab2.shape
    r = np.minimum(rows - 1, (np.arange(Hs) * rows // Hs))[:, None]; k = np.minimum(cols - 1, (np.arange(Ws) * cols // Ws))[None, :]
    t = (r * cols + k + 1).astype(np.int32)
    t[(raw > 0) & (lab2 == 0)] = 0
    return t


def _analyze(png, n, rows, cols, mode, mask, birefnet, dark, chroma, group_by='subject', clean=False):
    I, a, mode = _resolve(png, mode, clean)
    raw, group = subject_mask(I, mode, mask, birefnet, dark, chroma, alpha=a)
    if group_by == 'grid':
        comps, lab = _components(raw, group, min_area=12)
        subs, lab = _grid_group(comps, lab, raw.shape, rows, cols, raw=raw)
        return I, raw, group, subs, lab, subs, list(subs), [], 0.0, a, mode
    comps, lab = _components(raw, group)
    top = comps[:n]
    ref = float(np.median([c['area'] for c in top])) if top else 0.0
    sig = [c for c in comps if c['area'] >= 0.25 * ref] if ref else []
    subs = _order_rows([dict(c) for c in sig[:n]], rows, I.shape[0])
    extras = [c for c in comps if c not in sig and c['area'] >= max(60, 0.0008 * ref)]
    return I, raw, group, comps, lab, subs, sig, extras, ref, a, mode


# =====================================================================================
# Slicing by subject
# =====================================================================================
def slice_subjects(png, n=8, rows=2, cols=4, outdir='cells', prefix='cell', mode='auto', mask=None, birefnet=False,
                   pad=24, foot_pad=None, fragments='keep', dark=0.5, chroma=0.12, quiet=False, group='subject', clean=False):
    """Slice a sheet by subject ("territory slicing").
    1. Whole-sheet subject mask (mode='auto' non-white | mask/BiRefNet; 'ink' ink density); the n largest components are subjects;
    2. every pixel goes to the nearest subject (specks and tails reaching next door follow their owner);
    3. cluster into rows, sort by x, number 0..n-1 (row-major, same as kit.slice_sheet);
    4. one canvas size: bbox centred horizontally, bbox bottoms aligned, pad on all sides, foot_pad extra below for
       shadows; pixels outside the subject's territory are blanked. fragments='drop' also blanks non-subject specks
       (arcs, symbols the model drew).
    -> (paths, info). info: n_expected, n_found, ok, warnings, size=(W,H), cells=[dict per cell].
       Per cell: name, path, src_box (bbox in the sheet), box (bbox in the cell), foot_y, offset (cell = sheet + offset),
       row, col, area, height, lift_in_sheet (px above the row's ground line: drawn airborne).
    group='grid': slice by equal grid cells. Use for fx sheets (pieces in a cell form one subject), close-up sheets with
    two pieces per cell, subjects spanning two cells: each cell keeps its largest piece and pieces not touching the
    cell lines; parts reaching next door are cut at the cell line.
    clean=True: remove the semi-transparent haze first; the cells come out clean too."""
    I, raw, _, comps, lab, subs, sig, extras, ref, A, mode = _analyze(png, n, rows, cols, mode, mask, birefnet, dark, chroma,
                                                                      group_by=group, clean=clean)
    Hs, Ws = raw.shape
    warns = []
    if len(sig) != n and group == 'grid':
        warns.append(f'{len(sig)} cells have content, expected {n} (empty cells?)')
    elif len(sig) != n:
        warns.append(f'found {len(sig)} subjects, expected {n}' + (' (subjects touching or cells missing?)' if len(sig) < n else ' (extra large pieces: something extra drawn? keeping the n largest)'))
    if not subs: raise RuntimeError(f'{png}: no subject found (background not white? try mode="ink" or birefnet=True)')
    terr = _grid_terr(lab, raw, rows, cols) if group == 'grid' else _territory(lab, subs, raw.shape)
    medh = float(np.median([s['bbox'][3] - s['bbox'][1] for s in subs]))
    if foot_pad is None: foot_pad = int(round(max(16, 0.08 * medh)))
    # crop window per subject (bbox | kept specks in its territory), plus pad
    frag_lab = {}
    for c in comps:
        if c in sig[:n]: continue
        x0, y0, x1, y1 = c['bbox']; cx, cy = int((x0 + x1) // 2), int((y0 + y1) // 2)
        frag_lab[c['label']] = int(terr[min(cy, Hs - 1), min(cx, Ws - 1)])
    wins = []
    for j, s in enumerate(subs):
        x0, y0, x1, y1 = s['bbox']
        if fragments == 'keep':
            for c in comps:
                if frag_lab.get(c['label']) == j + 1:
                    bx0, by0, bx1, by1 = c['bbox']; x0, y0, x1, y1 = min(x0, bx0), min(y0, by0), max(x1, bx1), max(y1, by1)
        wins.append((x0 - pad, y0 - pad, x1 + pad, y1 + pad + foot_pad))
    up = max(s['bbox'][3] - w[1] for s, w in zip(subs, wins))
    down = max(w[3] - s['bbox'][3] for s, w in zip(subs, wins))
    half = max(max((s['bbox'][0] + s['bbox'][2]) / 2 - w[0], w[2] - (s['bbox'][0] + s['bbox'][2]) / 2) for s, w in zip(subs, wins))
    CW = int(math.ceil(half)) * 2; CH = int(up + down); CH += CH % 2
    base = up                                            # y of the subject bbox bottom inside the cell
    src8 = (np.clip(I, 0, 1) * 255 + 0.5).astype(np.uint8)[:, :, ::-1]
    drop = None
    if fragments == 'drop':
        drop = np.zeros_like(raw)
        for c in comps:
            if c not in sig[:n]: drop[lab == c['label']] = 1
        drop = cv2.dilate(drop, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))   # blank the specks' pale edges too
        drop &= (cv2.dilate(np.isin(lab, [s['label'] for s in subs]).astype(np.uint8), np.ones((3, 3), np.uint8)) == 0)
    os.makedirs(outdir, exist_ok=True)
    paths, cells = [], []
    rowbot = {}
    for s in subs: rowbot.setdefault(s['row'], []).append(s['bbox'][3])
    for j, s in enumerate(subs):
        x0, y0, x1, y1 = s['bbox']
        dx = int(round(CW / 2 - (x0 + x1) / 2)); dy = int(base - y1)
        sx0, sy0 = max(0, -dx), max(0, -dy); sx1, sy1 = min(Ws, CW - dx), min(Hs, CH - dy)
        bad = terr[sy0:sy1, sx0:sx1] != j + 1
        if drop is not None: bad |= drop[sy0:sy1, sx0:sx1] > 0
        if A is not None:                     # transparent: RGBA cell, alpha = 0 outside the territory
            cell = np.zeros((CH, CW, 4), np.uint8)
            reg = np.dstack([src8[sy0:sy1, sx0:sx1], (A[sy0:sy1, sx0:sx1] * 255 + 0.5).astype(np.uint8)])
            reg[bad] = 0
        else:                                 # white background: blank outside the territory
            cell = np.full((CH, CW, 3), 255, np.uint8)
            reg = src8[sy0:sy1, sx0:sx1].copy()
            reg[bad] = 255
        cell[sy0 + dy:sy1 + dy, sx0 + dx:sx1 + dx] = reg
        p = os.path.join(outdir, f'{prefix}_{j}.png'); cv2.imwrite(p, cell); paths.append(p)
        col = min(cols - 1, int(((x0 + x1) / 2) / (Ws / cols)))
        cells.append(dict(name=f'{prefix}_{j}', path=p, src_box=[x0, y0, x1, y1], offset=[dx, dy],
                          box=[x0 + dx, y0 + dy, x1 + dx, y1 + dy], foot_y=int(base), row=s['row'], col=col,
                          area=s['area'], height=y1 - y0, width=x1 - x0,
                          lift_in_sheet=int(np.median(rowbot[s['row']]) - y1)))
    info = dict(png=png, n_expected=n, n_found=len(sig), ok=(len(sig) == n), warnings=warns, size=[CW, CH], cells=cells,
                extras=len(extras))
    if warns and not quiet:
        for w in warns: print(f'animi.slice_subjects: {os.path.basename(png)}: {w}', file=sys.stderr)
    return paths, info


# =====================================================================================
# Sheet QC
# =====================================================================================
_SIDES = {'top': 'top', 't': 'top', '上': 'top', 'bottom': 'bottom', 'b': 'bottom', '下': 'bottom',
          'left': 'left', 'l': 'left', '左': 'left', 'right': 'right', 'r': 'right', '右': 'right'}


def _edge_sides(allow_edge):
    """allow_edge -> set of edges the subject may touch: True / 'all' = all four; 'bottom' / 'b,l' / 'bottom left' etc.
    (Chinese aliases like '下' / '下左' also work)"""
    if not allow_edge: return set()
    if allow_edge is True or allow_edge in ('all', '四边', '全部'): return {'top', 'bottom', 'left', 'right'}
    out = set()
    for tok in str(allow_edge).replace(',', ' ').replace('，', ' ').split():
        if tok.lower() in _SIDES: out.add(_SIDES[tok.lower()]); continue
        if all(ch in _SIDES for ch in tok.lower()): out |= {_SIDES[ch] for ch in tok.lower()}
    return out


def check_sheet(png, n=8, rows=2, cols=4, mode='auto', mask=None, birefnet=False, out=None,
                h_tol=0.2, area_tol=0.35, foot_tol=0.05, dark=0.5, chroma=0.12, group='subject',
                allow_edge=None, clean=False, float_=False):
    """Pose sheet QC -> dict(status='PASS'|'WARN'|'FAIL', messages=[(level, text)], subjects, extras, ...).
    Checks: subject count = n; edges pure white / transparent (catches "drew a whole scene"); coverage; height / area
    spread; same ground line per row; subjects crossing grid lines or touching the image edge; stray specks (arcs,
    symbols, flying props the model drew). out=path: write an overlay preview with boxes and numbers.
    group='grid': fx sheets, or close-up sheets with two separate pieces per cell (two characters, character + prop).
        Counts subjects per grid cell (pieces in a cell count as one); skips size spread and ground line.
    allow_edge: edges cut on purpose ('bottom' = chest-up close-up, 'left' = a hand reaching in; True = all four).
        These edges skip the transparency check, and touching them is INFO, not FAIL.
    clean: remove the semi-transparent haze first (clean_alpha). float_: floating / top-down characters, skip the ground line."""
    I, raw, _, comps, lab, subs, sig, extras, ref, A, mode = _analyze(png, n, rows, cols, mode, mask, birefnet, dark, chroma,
                                                                      group_by=group, clean=clean)
    grid = group == 'grid'
    edge_ok = _edge_sides(allow_edge)
    Hs, Ws = raw.shape
    msgs = []
    def add(level, s): msgs.append((level, s))
    # ---- edges ----
    if A is not None:
        nearw = A < 0.1                       # transparent background: edges should be transparent
    else:
        J = white_norm(I)
        nearw = (1 - J.min(2)) < 0.10
    b = max(4, int(0.015 * min(Hs, Ws)))
    sides = {'top': nearw[:b], 'bottom': nearw[-b:], 'left': nearw[:, :b], 'right': nearw[:, -b:]}
    border = {k: float(v.mean()) for k, v in sides.items()}
    checked = {k: v for k, v in border.items() if k not in edge_ok} or {'-': 1.0}
    worst = min(checked.values())
    if edge_ok: add('INFO', f'edges allowed to touch: {", ".join(sorted(edge_ok))} (no transparency check, touching is not a FAIL)')
    if A is None:
        add('WARN', 'no alpha channel: the image came back on a white background, not transparent. Regenerate as a '
                    'transparent PNG (Codex image_gen: transparent_background true). If it keeps coming back white, slice '
                    'cuts by the white background; check the cut edges for a white fringe on dark sets')
    haze = haze_ratio(A) if A is not None and not clean else 0.0
    edges_txt = lambda: ", ".join(f"{k} {v:.0%}" for k, v in checked.items())
    if worst < 0.9 and A is not None and haze > 0.05:
        add('FAIL', f'edges not transparent ({edges_txt()} transparent), but {haze:.0%} of pixels are semi-transparent: '
                    'most likely haze left by the image model, not a bad drawing. Re-check with --clean; if the cleaned '
                    'version passes, use it instead of regenerating')
    elif worst < 0.9 and A is not None:
        add('FAIL', f'edges not transparent ({edges_txt()} transparent): probably drew a whole scene. When regenerating, '
                    'write "transparent background PNG, no ground, sky or scene". Chest-up close-up or a hand reaching in: '
                    'add --allow-edge bottom / left ...')
    elif worst < 0.9:
        add('FAIL', f'edges not pure white ({edges_txt()} white): probably drew a whole scene or changed the background '
                    'colour. When regenerating, write "the background must be one flat pure white (#FFFFFF), like a studio '
                    'cut-out plate, no ground, sky or scene"')
    elif worst < 0.98:
        add('WARN', f'one edge is not fully {"transparent" if A is not None else "white"} (lowest {worst:.0%}): subject '
                    'touching the edge, greyish background or a gradient; look at the preview')
    cover = float(raw.mean())
    if cover > (0.8 if A is not None else 0.55):          # transparent close-up sheets fill the frame anyway; edges catch scenes
        add('FAIL', f'subject pixels cover {cover:.0%} of the sheet: not a pose sheet (drew a whole scene?)')
    scene = worst < 0.9 or cover > 0.55
    # ---- subject count ----
    if len(sig) != n and grid:
        add('FAIL', f'{len(sig)} cells have content, expected {n}: a cell is empty, or the fx was drawn outside its cell')
    elif len(sig) != n:
        hint = ('a cell is missing, or neighbouring subjects are joined (too close / linked by a ground line)' if len(sig) < n
                else 'large extra pieces (an extra character, prop or scene was drawn)')
        J2 = white_norm(I); grayish = float(np.median((J2.max(2) - J2.min(2))[raw > 0])) < 0.06 if raw.any() else False
        if len(sig) > n and mode != 'ink' and grayish:
            hint = 'subjects broke into many pieces; the image is mostly greyscale (ink / pencil): re-check with mode="ink" (CLI --mode ink)'
        add('FAIL', f'found {len(sig)} subjects, expected {n}: ' + hint)
    if scene or len(sig) > 2 * n:          # not a usable pose sheet at all: the detailed checks below are meaningless
        subs_ok = False
    else:
        subs_ok = True
    hs = np.array([s['bbox'][3] - s['bbox'][1] for s in subs], float)
    ar = np.array([s['area'] for s in subs], float)
    stats = {}
    if len(subs) >= 2 and subs_ok and not grid and not float_:
        mh, ma = float(np.median(hs)), float(np.median(ar))
        dh = np.abs(hs - mh) / mh; da = np.abs(ar - ma) / ma
        stats = dict(height_median=mh, height_spread=float((hs.max() - hs.min()) / mh), area_median=ma,
                     area_spread=float((ar.max() - ar.min()) / ma))
        bad = [i for i in range(len(subs)) if dh[i] > h_tol]
        if bad:
            add('WARN', 'height far from the median: ' + ', '.join(f'#{i} {hs[i] / mh - 1:+.0%}' for i in bad)
                + ' (deliberate crouch, squash, jump: ignore; otherwise sizes differ: scale the whole sheet by one factor, never per cell)')
        bad = [i for i in range(len(subs)) if da[i] > area_tol]
        if bad:
            add('WARN', 'area far from the median: ' + ', '.join(f'#{i} {ar[i] / ma - 1:+.0%}' for i in bad)
                + ' (something extra or missing, or very different poses)')
        # ---- ground line ----
        rowsd = {}
        for i, s in enumerate(subs): rowsd.setdefault(s['row'], []).append(i)
        for r, idx in rowsd.items():
            med = float(np.median([subs[i]['bbox'][3] for i in idx]))
            off = [(i, med - subs[i]['bbox'][3]) for i in idx if abs(med - subs[i]['bbox'][3]) > foot_tol * mh]
            if off:
                add('WARN', f'row {r + 1} ground line uneven: ' + ', '.join(f'#{i} {"high" if d > 0 else "low"} {abs(d):.0f}px' for i, d in off)
                    + ' (drawn airborne or drifting; when compositing always use the bbox bottom as the foot point, let code set height)')
    # ---- crossing grid lines / touching edges ----
    cw, ch = Ws / cols, Hs / rows
    over, edge, slots, over_edge_ok = [], [], {}, []
    for i, s in enumerate(subs):
        x0, y0, x1, y1 = s['bbox']; cx, cy = s['centroid']
        c, r = min(cols - 1, int(cx / cw)), min(rows - 1, int(cy / ch))
        s['slot'] = (r, c); slots.setdefault((r, c), []).append(i)
        o = max(c * cw - x0, x1 - (c + 1) * cw, r * ch - y0, y1 - (r + 1) * ch)
        if o > 2: over.append((i, o))
        touch = {k for k, hit in (('left', x0 <= 1), ('top', y0 <= 1), ('right', x1 >= Ws - 1), ('bottom', y1 >= Hs - 1)) if hit}
        if touch - edge_ok: edge.append(i)
        elif touch: over_edge_ok.append((i, touch))
    if not subs_ok: over, edge, dup_ok = [], [], False
    else: dup_ok = True
    if edge:
        add('FAIL', 'subject touches the image edge (cropped): ' + ', '.join(f'#{i}' for i in edge) + '. When regenerating, '
            'write "leave blank space around each cell, whole body visible"; edges cut on purpose (chest-up, a hand reaching in): --allow-edge')
    if over_edge_ok:
        add('INFO', 'edge contact allowed by --allow-edge: ' + ', '.join(f'#{i} ({", ".join(sorted(t))})' for i, t in over_edge_ok))
    if over:
        add('WARN', 'subject crosses the grid lines: ' + ', '.join(f'#{i} {o:.0f}px' for i, o in over) + '. Do not cut with kit.slice_sheet; use slice_subjects')
    dup = [k for k, v in slots.items() if len(v) > 1]
    if dup and dup_ok and not grid:
        add('WARN', f'some grid cells hold more than one subject; the layout is not a regular {rows}x{cols}: check the numbering by eye')
    # ---- stray specks ----
    ex_info = []
    terr_cent = [s['centroid'] for s in subs]
    for e in extras:
        x0, y0, x1, y1 = e['bbox']; w, h = x1 - x0, y1 - y0
        ecx, ecy = e['centroid']
        near = int(np.argmin([(ecx - a) ** 2 + (ecy - b) ** 2 for a, b in terr_cent])) if subs else -1
        flat = w > 4 * h and near >= 0 and ecy > subs[near]['bbox'][3] - 0.1 * h
        ex_info.append(dict(bbox=[x0, y0, x1, y1], area=e['area'], near=near, kind='shadow?' if flat else 'speck'))
    junk = [e for e in ex_info if e['kind'] == 'speck']
    if junk and subs_ok:
        add('WARN', f'{len(junk)} stray specks (nearest ' + ', '.join(sorted({f"#{e['near']}" for e in junk})) +
            '): probably motion arcs, symbols, speed lines or flying props the model drew. Slice with fragments="drop", '
            'or write "no motion arcs, speed lines or symbols" in the prompt. Detached parts of the subject itself (thin lines, ribbons): ignore')
    status = 'FAIL' if any(l == 'FAIL' for l, _ in msgs) else ('WARN' if any(l == 'WARN' for l, _ in msgs) else 'PASS')
    if status == 'PASS' and grid: add('PASS', f'all {n} fx cells present ({sum(s["pieces"] for s in subs)} pieces), edges {"transparent" if A is not None else "pure white"}')
    elif status == 'PASS': add('PASS', f'all {n} subjects present, size and ground line consistent, edges {"transparent" if A is not None else "pure white"}, no stray specks')
    res = dict(png=png, status=status, messages=msgs, n_expected=n, n_found=len(sig), border_white=border, coverage=cover,
               stats=stats, extras=ex_info,
               subjects=[dict(idx=i, bbox=list(s['bbox']), area=s['area'], height=int(s['bbox'][3] - s['bbox'][1]),
                              foot_y=int(s['bbox'][3]), row=s['row'], slot=list(s.get('slot', (0, 0)))) for i, s in enumerate(subs)])
    if out: _check_preview(I if A is None else I * A[..., None] + (1 - A[..., None]), raw, res, rows, cols, out, b)
    return res


def _cjk_font(size):
    try:
        import fx
        return fx.font('hei-l', size)
    except Exception:
        from PIL import ImageFont
        return ImageFont.load_default()


def _check_preview(I, raw, res, rows, cols, out, b):
    from PIL import Image, ImageDraw
    Hs, Ws = raw.shape
    sc = min(1.0, 1600 / Ws)
    base = (np.clip(I, 0, 1) * 255).astype(np.uint8)
    tint = base.copy(); tint[raw > 0] = (0.65 * tint[raw > 0] + 0.35 * np.array([60, 160, 255])).astype(np.uint8)
    im = cv2.resize(tint, (int(Ws * sc), int(Hs * sc)), interpolation=cv2.INTER_AREA)
    pim = Image.fromarray(im); d = ImageDraw.Draw(pim)
    W2, H2 = pim.size
    for c in range(1, cols):
        x = c * W2 / cols
        for y in range(0, H2, 12): d.line([(x, y), (x, y + 6)], fill=(150, 150, 150), width=1)
    for r in range(1, rows):
        y = r * H2 / rows
        for x in range(0, W2, 12): d.line([(x, y), (x + 6, y)], fill=(150, 150, 150), width=1)
    bw = res['border_white']
    for k, (x0, y0, x1, y1) in {'top': (0, 0, W2, b * sc), 'bottom': (0, H2 - b * sc, W2, H2), 'left': (0, 0, b * sc, H2),
                                'right': (W2 - b * sc, 0, W2, H2)}.items():
        if bw[k] < 0.98: d.rectangle([x0, y0, x1, y1], outline=(230, 30, 30), width=3)
    f = _cjk_font(max(12, int(15 * sc / 0.9)))
    flagged = set()
    for l, m in res['messages']:
        if l in ('WARN', 'FAIL'): flagged |= {int(t) for t in re.findall(r'#(\d+)', m)}
    rowsd = {}
    for s in res['subjects']: rowsd.setdefault(s['row'], []).append(s)
    for r, ss in rowsd.items():
        med = np.median([s['foot_y'] for s in ss]) * sc
        xs0 = min(s['bbox'][0] for s in ss) * sc; xs1 = max(s['bbox'][2] for s in ss) * sc
        d.line([(xs0, med), (xs1, med)], fill=(255, 0, 160), width=1)
    for s in res['subjects']:
        x0, y0, x1, y1 = [v * sc for v in s['bbox']]
        col = (230, 120, 0) if s['idx'] in flagged else (20, 170, 60)
        d.rectangle([x0, y0, x1, y1], outline=col, width=2)
        d.line([(x0, y1), (x1, y1)], fill=(230, 30, 30), width=2)
        d.text((x0 + 3, max(0, y0 - 18 * sc / 0.9 - 2)), f"#{s['idx']} h{s['height']} a{s['area'] / 1000:.0f}k", fill=col, font=f)
    for e in res['extras']:
        x0, y0, x1, y1 = [v * sc for v in e['bbox']]
        col = (120, 120, 120) if e['kind'] == 'shadow?' else (220, 0, 220)
        d.ellipse([x0 - 8, y0 - 8, x1 + 8, y1 + 8], outline=col, width=2)
    # caption area at the bottom
    lines = [f"{os.path.basename(res['png'])}   {res['status']}   subjects {res['n_found']}/{res['n_expected']}"]
    for l, m in res['messages']: lines.append(f'[{l}] {m}')
    ft = _cjk_font(18)
    wrap = []
    glen = (lambda t: ft.getlength(t)) if hasattr(ft, 'getlength') else (lambda t: 10 * len(t))
    for ln in lines:
        cur = ''
        for ch in ln:
            if glen(cur + ch) > W2 - 24: wrap.append(cur); cur = '    '
            cur += ch
        wrap.append(cur)
    th = 26 * len(wrap) + 16
    canvas = Image.new('RGB', (W2, H2 + th), (255, 255, 255)); canvas.paste(pim, (0, 0))
    d2 = ImageDraw.Draw(canvas)
    sc_col = {'PASS': (20, 150, 60), 'WARN': (210, 120, 0), 'FAIL': (210, 30, 30), 'INFO': (60, 60, 60)}[res['status']]
    d2.rectangle([0, H2, W2, H2 + 4], fill=sc_col)
    for i, ln in enumerate(wrap):
        d2.text((10, H2 + 10 + 26 * i), ln, fill=sc_col if i == 0 else (40, 40, 40), font=ft)
    dd = os.path.dirname(out)
    if dd: os.makedirs(dd, exist_ok=True)
    canvas.save(out, quality=90)


# =====================================================================================
# Anchors
# =====================================================================================
def cell_anchor(a, th=0.5, body_frac=0.65, bottom_frac=0.2):
    """alpha (or 0/1 mask) -> anchor dict:
    bbox, foot_y (bbox bottom), body_x (mean x of the top body_frac, ignoring swinging tails and legs),
    bottom_x / bottom_w (centre and width of the lowest bottom_frac band: wheels, mounts, skateboards), bbox_cx, height, width, area."""
    m = a > th
    x0, y0, x1, y1 = kit.bbox(a, th)
    h = y1 - y0
    top = m[y0:y0 + max(1, int(round(h * body_frac)))]
    ys, xs = np.nonzero(top)
    body_x = float(xs.mean()) if len(xs) else (x0 + x1) / 2
    bot = m[y1 - max(1, int(round(h * bottom_frac))):y1]
    cols = np.nonzero(bot.any(0))[0]
    bx0, bx1 = (int(cols.min()), int(cols.max()) + 1) if len(cols) else (x0, x1)
    b0, b1 = y1 - max(2, int(round(h * 0.045))), y1 - max(1, int(round(h * 0.012)))   # bottom strip (base of a prop or stand)
    bc = np.nonzero(m[max(y0, b0):max(y0 + 1, b1), x0:x1].any(0))[0]
    base_x = float((bc.min() + bc.max()) / 2 + x0) if len(bc) else (bx0 + bx1) / 2
    return dict(bbox=[x0, y0, x1, y1], foot_y=int(y1), body_x=round(body_x, 2), bottom_x=(bx0 + bx1) / 2,
                bottom_w=bx1 - bx0, bbox_cx=(x0 + x1) / 2, height=int(h), width=int(x1 - x0), area=int(m.sum()),
                size=[int(a.shape[1]), int(a.shape[0])], base_x=round(base_x, 2))


def core_anchor(a, frac=0.16, th=0.5):
    """The core of a top-down / diagonally walking paper puppet: opening removes thin legs and antennae, leaving the body
    blob -> dict(cx, cy, w, h, len) (cell coords). cx, cy are the anchor and rotation pivot (top-down has no ground line,
    and a bbox anchor jumps with the legs); len = body long axis, used for hero size (not the diagonal bbox)."""
    m = (np.asarray(a) > th).astype(np.uint8)
    ys, xs = np.nonzero(m)
    if not len(xs): return dict(cx=0.0, cy=0.0, w=0.0, h=0.0, len=0.0)
    r = max(3, int(min(np.ptp(ys), np.ptp(xs)) * frac))
    o = cv2.morphologyEx(m, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (r, r)))
    if o.any(): ys, xs = np.nonzero(o)
    w, h = float(np.ptp(xs)), float(np.ptp(ys))
    if len(xs) > 5:
        (_, _), (ew, eh), _ = cv2.minAreaRect(np.stack([xs, ys], 1).astype(np.float32)); ln = float(max(ew, eh))
    else: ln = max(w, h)
    return dict(cx=float(xs.mean()), cy=float(ys.mean()), w=w, h=h, len=ln)


def set_core(info, a, frac=0.16):
    """Store the core in a cell's anchor dict (info['core'] = core_anchor). Templates do it automatically for top-down styles (flags.top_down)"""
    info['core'] = core_anchor(a, frac)
    return info


class Anchors:
    """Result of anchors(). A['run_3'] -> that cell's anchor dict; A.order = cell names in number order;
    A.median_h = median bbox height; A.scale(target height) -> one scale for the whole sheet; A.save(path) writes JSON."""
    def __init__(self, cells, prefix=''):
        self.cells = cells; self.prefix = prefix
        self.order = list(cells.keys())
        self.median_h = float(np.median([c['height'] for c in cells.values()])) if cells else 0.0
        self.median_bottom_w = float(np.median([c['bottom_w'] for c in cells.values()])) if cells else 0.0

    def __getitem__(self, k): return self.cells[k]
    def __contains__(self, k): return k in self.cells
    def __iter__(self): return iter(self.order)
    def __len__(self): return len(self.order)

    def scale(self, target_h):
        """One scale per sheet: median bbox height -> target_h (only squashed cells come out shorter)"""
        return target_h / self.median_h

    def scale_ref(self, target_h, cell=None):
        """One scale across sheets (use this, not scale, when a character has several sheets):
        the "standard pose" cell (standing straight, no crouch or jump; default the first cell) sets the scale so its bbox
        height equals the character's standard height target_h. Pass the same target_h (HERO_H at the top of film.py)
        for every sheet of a character, or it changes size between sheets. Per-sheet medians (scale) go wrong: a sheet
        with many crouching poses has a short median and makes the character bigger."""
        cell = cell or self.order[0]
        return target_h / max(1.0, float(self.cells[cell]['height']))

    def scale_w(self, target_w):
        """Scale by the median width of the bottom 20% (vehicles, mounts: length is steadier than height)"""
        return target_w / self.median_bottom_w

    def to_dict(self):
        return dict(prefix=self.prefix, median_h=self.median_h, median_bottom_w=self.median_bottom_w,
                    order=self.order, cells=self.cells)

    def save(self, path):
        d = os.path.dirname(path)
        if d: os.makedirs(d, exist_ok=True)
        with open(path, 'w') as f: json.dump(self.to_dict(), f, ensure_ascii=False, indent=1)
        return path


def load_anchors(path):
    with open(path) as f: d = json.load(f)
    A = Anchors({k: d['cells'][k] for k in d['order']}, d.get('prefix', ''))
    return A


def _cell_files(cells_dir, prefix):
    pat = os.path.join(cells_dir, (prefix + '_*.png') if prefix else '*.png')
    fs = [f for f in glob.glob(pat) if not f.endswith('-mask.png')]
    def key(f):
        b = os.path.splitext(os.path.basename(f))[0]
        m = re.search(r'_(\d+)$', b)
        return (b[:m.start()] if m else b, int(m.group(1)) if m else -1)
    if prefix: fs = [f for f in fs if re.fullmatch(re.escape(prefix) + r'_\d+', os.path.splitext(os.path.basename(f))[0])]
    return sorted(fs, key=key)


def cell_alpha(cell_png, masks_dir=None, mode=None):
    """A cell's alpha: mode='mask' reads <masks_dir>/<name>-mask.png; 'auto' non-white threshold; 'ink' ink density.
    auto / ink keep only the largest subject (detached ground shadows and specks are dropped)."""
    name = os.path.splitext(os.path.basename(cell_png))[0]
    if mode in (None, 'alpha', 'auto'):
        _, a = load_rgba(cell_png)
        if a is not None: return a                # transparent cell: use its own alpha
    if mode is None: mode = 'mask' if masks_dir else 'auto'
    if mode == 'mask':
        p = os.path.join(masks_dir, name + '-mask.png'); m = cv2.imread(p, 0) if os.path.exists(p) else None
        if m is None:
            print(f'animi: mask missing {p}, estimating this cell with the non-white threshold (run cut.py first for accuracy)', file=sys.stderr)
            return cell_alpha(cell_png, None, 'auto')
        a = np.clip((m.astype(np.float32) / 255 - 0.03) / 0.94, 0, 1)
        b = 4; a[:b] = a[-b:] = 0; a[:, :b] = a[:, -b:] = 0       # same as kit.sprite
        return a
    I = kit.rd(cell_png)
    raw, group = subject_mask(I, mode)
    k, lab, st, _ = cv2.connectedComponentsWithStats(group, 8)
    if k > 2:                                   # keep only the largest subject (drop detached shadows and specks)
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        keep = (lab == big)
    else: keep = group > 0
    if mode == 'ink': return ink_density(I) * keep
    return (raw * keep).astype(np.float32)


def anchors(cells_dir, masks_dir=None, prefix='', mode=None, save=None, th=None, body_frac=0.65, bottom_frac=0.2):
    """Anchors for every cell of a sheet -> Anchors. Cells are found as <prefix>_<n>.png and sorted by n.
    mode: 'mask' (default when masks_dir is given; same masks as kit.sprite), 'auto' (non-white threshold), 'ink' (ink density, th 0.35).
    save=path: write JSON."""
    fs = _cell_files(cells_dir, prefix)
    if not fs: raise FileNotFoundError(f'no {prefix}_*.png in {cells_dir}')
    if th is None: th = 0.35 if mode == 'ink' else 0.5
    cells = {}
    for f in fs:
        name = os.path.splitext(os.path.basename(f))[0]
        a = cell_alpha(f, masks_dir, mode)
        info = cell_anchor(a, th, body_frac, bottom_frac); info['name'] = name
        cells[name] = info
    A = Anchors(cells, prefix)
    if save: A.save(save)
    return A


def preview_cells(cells_dir, out, masks_dir=None, prefix='', mode=None, cols=4, width=320, A=None):
    """Contact sheet of cells: each scaled to width, blue mask outline, bbox (green), ground line (red), body centre x (magenta), bottom-20% centre (orange dot)"""
    fs = _cell_files(cells_dir, prefix)
    A = A or anchors(cells_dir, masks_dir, prefix, mode)
    tiles = []
    for f in fs:
        name = os.path.splitext(os.path.basename(f))[0]
        a = cell_alpha(f, masks_dir, mode)
        I = kit.rd(f)
        if is_transparent(f): I = I * a[..., None] + 0.86 * (1 - a[..., None])   # transparent: show over light grey
        I = (np.clip(I, 0, 1) * 255).astype(np.uint8).copy()
        cnt, _ = cv2.findContours((a > (0.35 if mode == 'ink' else 0.5)).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(I, cnt, -1, (40, 120, 255), 2)
        c = A[name]; x0, y0, x1, y1 = c['bbox']
        cv2.rectangle(I, (x0, y0), (x1 - 1, y1 - 1), (20, 170, 60), 2)
        cv2.line(I, (0, c['foot_y']), (I.shape[1], c['foot_y']), (230, 30, 30), 2)
        bx = int(round(c['body_x'])); cv2.line(I, (bx, y0), (bx, y1), (220, 0, 200), 2)
        cv2.circle(I, (int(c['bottom_x']), c['foot_y']), 7, (255, 140, 0), -1)
        s = width / I.shape[1]
        t = cv2.resize(I, (width, int(I.shape[0] * s)), interpolation=cv2.INTER_AREA)
        cv2.putText(t, name, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(t)
    th = max(t.shape[0] for t in tiles)
    rows = math.ceil(len(tiles) / cols)
    G = np.full((rows * (th + 6) + 6, cols * (width + 6) + 6, 3), 255, np.uint8)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols); y, x = 6 + r * (th + 6), 6 + c * (width + 6)
        G[y:y + t.shape[0], x:x + width] = t
    kit.wr(out, G.astype(np.float32) / 255)
    return out


# =====================================================================================
# Layers (draw to a temporary layer, then clip)
# =====================================================================================
class Layer:
    """Premultiplied layer: P (HxWx3, colour x opacity), A (HxW). place_at / contact_shadow can draw straight onto a Layer."""
    def __init__(self, h, w=None):
        if w is None: h, w = h.shape[:2]          # Layer(frame) -> empty layer of the same size
        self.P = np.zeros((h, w, 3), np.float32); self.A = np.zeros((h, w), np.float32)

    @property
    def shape(self): return self.P.shape

    def composite(self, frame, alpha=1.0):
        """Composite this layer onto frame (in place)"""
        a = np.clip(self.A * alpha, 0, 1)[..., None]
        frame[:] = frame * (1 - a) + self.P * alpha
        return frame


def _as_layer(layer):
    if isinstance(layer, Layer): return layer
    if isinstance(layer, tuple):
        L = Layer(layer[1].shape[0], layer[1].shape[1]); L.P = layer[0].astype(np.float32); L.A = layer[1].astype(np.float32); return L
    arr = np.asarray(layer, np.float32)
    L = Layer(arr.shape[0], arr.shape[1]); L.A = arr[..., 3]; L.P = arr[..., :3] * arr[..., 3:4]; return L


def clip_layer(layer, keep_mask):
    """-> new Layer keeping only the part inside keep_mask (HxW, 0-1).
    E.g. a paw reaching out of a doorway: L = animi.Layer(frame); animi.place_at(L, paw, ...);
        animi.clip_layer(L, mask_left_of_doorway).composite(frame)     # whatever crosses the door edge is clipped
    layer may be a Layer, (P, A) or an HxWx4 RGBA (not premultiplied)."""
    L = _as_layer(layer); m = np.clip(np.asarray(keep_mask, np.float32), 0, 1)
    out = Layer(L.A.shape[0], L.A.shape[1]); out.P = L.P * m[..., None]; out.A = L.A * m
    return out


def holdout(frame, bg_layer, mask, x0=0, y0=0):
    """Paste foreground parts of the background (front rim of a bowl, door frame, grass) back on top (frame in place):
    frame = frame x (1 - mask) + bg_layer x mask. bg_layer and mask share a size and go at (x0, y0);
    bg_layer must be the background aligned to this frame (apply the same cam first when the camera moves).
    Call after drawing the characters -> they go behind the occluder."""
    m = np.clip(np.asarray(mask, np.float32), 0, 1)
    h, w = m.shape; FH, FW = frame.shape[:2]
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(FW, x0 + w), min(FH, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0: return frame
    sl = (slice(fy0 - y0, fy1 - y0), slice(fx0 - x0, fx1 - x0))
    mm = m[sl][..., None]
    frame[fy0:fy1, fx0:fx1] = frame[fy0:fy1, fx0:fx1] * (1 - mm) + bg_layer[sl][..., :3] * mm
    return frame


def color_mask(img, rule, tol=0.12, open_=5, close=9, min_area=3000, blur=1.2):
    """Matte a region of the background by colour (sky, water, wall: things that must hide behind its leaves, clouds,
    branches) -> 0-1, background size. rule: (r, g, b) 0-1 (distance < tol) / a list of colours / f(R, G, B) -> bool
    (R, G, B are 0-255 arrays; e.g. lambda R, G, B: (R > 195) & (G > 120) & (R >= G): bright yellow, pink, apricot sky,
    leaves with G > R excluded). Open/close removes specks, blobs below min_area are dropped, edges feathered by blur.
    Check with occ_overlay over the background first. Usage: draw on a copy of frame, then only_in(frame, copy,
    cam.plate'd mask) keeps only the masked part (a sun that shows only over the sky)."""
    I8 = np.clip(img, 0, 1) * 255
    R, G, B = I8[..., 0], I8[..., 1], I8[..., 2]
    if callable(rule): m = rule(R, G, B)
    else:
        cols = [rule] if np.ndim(rule) == 1 else list(rule)
        m = np.zeros(img.shape[:2], bool)
        for c in cols: m |= np.linalg.norm(img - np.array(c, np.float32), axis=2) < tol
    m = np.asarray(m, np.uint8) * 255
    if open_: m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((open_, open_), np.uint8))
    if close: m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((close, close), np.uint8))
    k, lab, st, _ = cv2.connectedComponentsWithStats((m > 0).astype(np.uint8), 8)
    keep = np.zeros(k, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] > min_area
    m = keep[lab].astype(np.float32)
    return np.clip(cv2.GaussianBlur(m, (0, 0), blur), 0, 1) if blur else m


def only_in(frame, drawn, mask):
    """Copy back only the masked part of drawn (a copy of frame with extra drawing) onto frame: drawn where mask = 1,
    unchanged elsewhere. mask is frame-sized (frame the background mask with the camera first:
    cam.plate(m[..., None].repeat(3, 2), par)[..., :1]). Edits and returns frame"""
    m = mask if mask.ndim == 3 else mask[..., None]
    frame[:] = frame * (1 - m) + drawn * m
    return frame


def poly_mask(shape, pts, feather=1.5):
    """Polygon mask (HxW float 0-1). shape is (H, W) or an image; pts=[(x,y),...]; feather = Gaussian px"""
    h, w = shape[:2] if not hasattr(shape, 'shape') else shape.shape[:2]
    m = np.zeros((h, w), np.float32)
    cv2.fillPoly(m, [np.round(np.asarray(pts, np.float32)).astype(np.int32)], 1.0, cv2.LINE_AA)
    if feather > 0: m = cv2.GaussianBlur(m, (0, 0), feather)
    return m


def rect_mask(shape, x0, y0, x1, y1, feather=1.5):
    return poly_mask(shape, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], feather)


# =====================================================================================
# Placing by foot point
# =====================================================================================
def _anchor_x(info, anchor):
    if anchor == 'body': return info['body_x']
    if anchor == 'bottom20': return info['bottom_x']
    if anchor == 'bbox': return info['bbox_cx']
    if anchor == 'base': return info.get('base_x', info['bottom_x'])
    if isinstance(anchor, (int, float)):
        x0, _, x1, _ = info['bbox']; return x0 + anchor * (x1 - x0)
    raise ValueError(f'anchor must be body / bottom20 / bbox / base or a number 0-1: {anchor}')


def place_at(frame, c, x, ground_y, scale, info=None, anchor='body', rot=0.0, sx=1.0, sy=1.0, pivot='foot',
             alpha=1.0, blur=0.0, shadow=False, shadow_k=0.5, flip=False, motion=0.0, vmotion=0.0,
             ref=None, gain=None, dx=0.0, dy=0.0):
    """Place a cell so the character's anchor lands at (x, ground_y). Edits frame (ndarray or Layer) in place.
    c: (C, a, M) from kit.sprite. info: the cell's anchor dict (anchors()[name]); computed when None.
    anchor: horizontal anchor 'body' (body centre, default) / 'bottom20' (centre of the bottom 20%: wheels, mounts) /
            'bbox' (bbox centre) / 'base' (middle of the bottom strip: a character standing in a prop, or reaching
            outside it in a close-up, stays registered to the prop's base) / 0-1 (position along the bbox bottom).
            Vertically it is always the foot y (bbox bottom).
    scale: cell -> frame scale (one per sheet: A.scale(target height)).
    rot: degrees, positive = counter-clockwise (as kit.cam). sx / sy: squash and stretch (keep volume with sx = 1/sy**0.5).
         Rigid styles only get affine transforms, no local deformation.
    pivot: pivot for rotation and squash. 'foot' (the anchor, default) / 'center' (bbox centre) / 0-1 (position on
           the bbox bottom, e.g. a rear wheel 0.15) / (px, py) in cell coords.
    blur: Gaussian depth of field px; motion / vmotion: horizontal / vertical motion blur length px; alpha: overall
          opacity; flip: mirror horizontally (the anchor mirrors too).
    shadow=True multiplies the drawing's own soft white-background shadow M onto the frame (strength shadow_k); turn
          off when airborne; usually use contact_shadow instead.
    ref=(px, py): register by any point in the cell; it lands at (x, ground_y) and rotation / squash pivot on it
          (held, carried, pinched, sitting on something).
    gain: brightness multiplied per column after placing: a number, or f(frame x array) -> gain (the light curve from floor_light).
    dx / dy: extra offset added to (x, ground_y).
    -> the character's bbox in the frame (x0, y0, x1, y1) (to position contact shadows and fx)."""
    C, a, M = c
    if info is None: info = cell_anchor(a)
    h, w = a.shape
    x, ground_y = x + dx, ground_y + dy
    if ref is not None: ax, fy = float(ref[0]), float(ref[1])
    else: ax = _anchor_x(info, anchor); fy = info['foot_y']
    bx0, by0, bx1, by1 = info['bbox']
    if pivot == 'foot': px, py = ax, fy
    elif pivot == 'center': px, py = (bx0 + bx1) / 2, (by0 + by1) / 2
    elif isinstance(pivot, (int, float)): px, py = bx0 + pivot * (bx1 - bx0), by1
    else: px, py = pivot
    if flip:
        C, a, M = C[:, ::-1], a[:, ::-1], M[:, ::-1]
        ax, px = w - ax, w - px; bx0, bx1 = w - bx1, w - bx0
    # first scale the whole cell close to the target size (INTER_AREA when shrinking to avoid aliasing), affine does the rest
    smax = scale * max(abs(sx), abs(sy))
    pre = smax if smax < 0.95 else 1.0
    if pre != 1.0:
        nw, nh = max(2, int(round(w * pre))), max(2, int(round(h * pre)))
        C = cv2.resize(np.ascontiguousarray(C), (nw, nh), interpolation=cv2.INTER_AREA)
        a = cv2.resize(np.ascontiguousarray(a), (nw, nh), interpolation=cv2.INTER_AREA)
        M = cv2.resize(np.ascontiguousarray(M), (nw, nh), interpolation=cv2.INTER_AREA)
        fxs, fys = nw / w, nh / h
        ax, fy, px, py = ax * fxs, fy * fys, px * fxs, py * fys
        bx0, bx1, by0, by1 = bx0 * fxs, bx1 * fxs, by0 * fys, by1 * fys
        h, w = nh, nw
    s = scale / pre
    if s > 1.05:                                       # add a little sharpening when enlarging (as kit.place)
        C = C + 0.4 * (C - cv2.GaussianBlur(C, (0, 0), 0.8 * s))
    # cell coords -> frame coords: p' = piv' + R·diag(s·sx, s·sy)·(p - piv), piv' = (x, ground_y) + s·(piv - anchor)
    pvx, pvy = x + s * (px - ax), ground_y + s * (py - fy)
    th = math.radians(rot); cs, sn = math.cos(th), math.sin(th)
    L = np.array([[cs * s * sx, sn * s * sy], [-sn * s * sx, cs * s * sy]], np.float64)
    t = np.array([pvx, pvy]) - L @ np.array([px, py])
    corners = np.array([[0, 0], [w, 0], [0, h], [w, h]], np.float64) @ L.T + t
    sub = np.array([[bx0, by0], [bx1, by0], [bx0, by1], [bx1, by1]], np.float64) @ L.T + t
    out_box = (float(sub[:, 0].min()), float(sub[:, 1].min()), float(sub[:, 0].max()), float(sub[:, 1].max()))
    FH, FW = (frame.A.shape if isinstance(frame, Layer) else frame.shape[:2])
    m = int(math.ceil(max(blur * 3, motion, vmotion))) + 2
    X0 = max(0, int(math.floor(corners[:, 0].min())) - m); Y0 = max(0, int(math.floor(corners[:, 1].min())) - m)
    X1 = min(FW, int(math.ceil(corners[:, 0].max())) + m); Y1 = min(FH, int(math.ceil(corners[:, 1].max())) + m)
    if X1 <= X0 or Y1 <= Y0: return out_box
    Mt = np.hstack([L, (t - [X0, Y0])[:, None]]).astype(np.float64)
    ow, oh = X1 - X0, Y1 - Y0
    interp = cv2.INTER_CUBIC if s > 1.05 else cv2.INTER_LINEAR
    P = cv2.warpAffine(np.ascontiguousarray(C * a[..., None]), Mt, (ow, oh), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    A2 = cv2.warpAffine(np.ascontiguousarray(a), Mt, (ow, oh), flags=interp, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    P = np.clip(P, 0, None); A2 = np.clip(A2, 0, 1)
    if blur > 0.3: P = cv2.GaussianBlur(P, (0, 0), blur); A2 = cv2.GaussianBlur(A2, (0, 0), blur)
    if motion >= 2: P = kit.hblur(P, motion); A2 = kit.hblur(A2, motion)
    if vmotion >= 2: P = kit.vblur(P, vmotion); A2 = kit.vblur(A2, vmotion)
    A2 = np.clip(A2 * alpha, 0, 1); P = P * alpha
    if gain is not None:
        g = gain(np.arange(X0, X1, dtype=np.float32)) if callable(gain) else np.float32(gain)
        P = P * (np.asarray(g, np.float32)[None, :, None] if np.ndim(g) else g)
    if isinstance(frame, Layer):
        Ar = A2[..., None]
        frame.P[Y0:Y1, X0:X1] = frame.P[Y0:Y1, X0:X1] * (1 - Ar) + P
        frame.A[Y0:Y1, X0:X1] = frame.A[Y0:Y1, X0:X1] * (1 - A2) + A2
        return out_box
    reg = frame[Y0:Y1, X0:X1]
    if shadow:
        M2 = cv2.warpAffine(np.ascontiguousarray(M), Mt, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(1, 1, 1))
        reg *= 1 - (1 - M2) * shadow_k
    reg[:] = reg * (1 - A2[..., None]) + P
    return out_box


def ink_sprite(img, ink=INK, gain=1.12, floor=0.025):
    """Ink cell on white -> (C, a, M): C is flat ink colour, a is ink density; feed to place_at (on light paper it is almost a multiply)"""
    D = ink_density(img, gain, floor)
    C = np.empty(D.shape + (3,), np.float32); C[:] = np.array(ink, np.float32)
    return C, D, np.ones_like(C)


def ink_over(frame, D, x0, y0, ink=INK, k=1.0):
    """Multiply ink density D onto frame at (x0, y0): frame *= 1 - D·k·(1 - ink) (layers of ink multiply and darken)"""
    D = np.asarray(D, np.float32) * k
    h, w = D.shape; FH, FW = frame.shape[:2]; x0, y0 = int(round(x0)), int(round(y0))
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(FW, x0 + w), min(FH, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0: return frame
    d = D[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0][..., None]
    frame[fy0:fy1, fx0:fx1] *= 1 - d * (1 - np.array(ink, np.float32))
    return frame


def multiply(frame, img, x0=0, y0=0, k=1.0):
    """Multiply an RGB image on white (paper grain, pencil drawing, watercolour strokes): frame *= lerp(1, img, k)"""
    img = _load_rgb(img); h, w = img.shape[:2]; FH, FW = frame.shape[:2]; x0, y0 = int(round(x0)), int(round(y0))
    fx0, fy0, fx1, fy1 = max(0, x0), max(0, y0), min(FW, x0 + w), min(FH, y0 + h)
    if fx1 <= fx0 or fy1 <= fy0: return frame
    frame[fy0:fy1, fx0:fx1] *= 1 - k * (1 - img[fy0 - y0:fy1 - y0, fx0 - x0:fx1 - x0])
    return frame


# =====================================================================================
# Contact shadows
# =====================================================================================
def prop_spot(c, color, tol=0.18, top_frac=1.0, body=0.75):
    """Find a held prop (pan, plate, bowl) in a cell by colour -> dict or None:
      rim=((x0, y0), (x1, y1)): the two ends of the prop's rim (cell coords). Uses only the vertically thick columns
          (the body, not a thin handle) and fits a line through each column's top point.
      depth: vertical thickness of the prop body (cell px); mask: soft prop mask (0-1, including inner details and shading)
    color: (r, g, b) 0-1 (distance < tol counts), or f(I, a) -> bool mask. top_frac: search only the top part of the cell.
    body: only columns at least body x the thickest count as the body (a tilted pan makes the handle near the body
          "thick" too; a low threshold joins a piece of handle into the rim).
    Do not match on brightness alone: the prop's shaded half is dark; miss it and the "pan only" layer will not cover
    the pancake. Usage (only the top of the pancake shows above the rim): character -> pancake (bottom sunk below the
    rim) -> the cell again as "pan only" (I, a * mask) to cover the pancake's bottom. When the pan is above an
    occluder such as a stove, draw the "pan only" layer after the occluder, or the flames end up in front of the pan."""
    I, a, _ = c
    if callable(color): m = color(I, a)
    else: m = (np.linalg.norm(I - np.array(color, np.float32), axis=2) < tol) & (a > 0.5)
    m = m.astype(np.uint8); m[int(m.shape[0] * top_frac):] = 0
    k, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if k < 2: return None
    pm = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    if pm.sum() < 300: return None
    cs, _ = cv2.findContours(pm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    fill = np.zeros_like(pm); cv2.drawContours(fill, cs, -1, 1, -1)
    h = fill.sum(axis=0); xs = np.nonzero(h >= body * h.max())[0]
    runs = np.split(xs, np.nonzero(np.diff(xs) > 3)[0] + 1); xs = max(runs, key=len)
    tops = np.array([np.argmax(fill[:, x] > 0) for x in xs], np.float32)
    k_, b_ = np.polyfit(xs.astype(np.float32), tops, 1) if len(xs) > 1 else (0.0, float(tops[0]))
    x0, x1 = float(xs[0]), float(xs[-1])
    soft = cv2.GaussianBlur(cv2.dilate(fill, np.ones((3, 3), np.uint8)).astype(np.float32), (0, 0), 0.8)
    return dict(rim=((x0, k_ * x0 + b_), (x1, k_ * x1 + b_)), depth=float(np.median(h[xs])), mask=np.clip(soft, 0, 1))


def inner_mask(c, color, tol=0.18, soft=0.8):
    """Soft mask of a container's inside (dark pan bottom, inside of a bowl): largest region of that colour with small
    holes filled -> 0-1 (cell size). color: (r, g, b) 0-1 or f(I, a) -> bool mask (do not threshold brightness only;
    include the shaded half)"""
    I, a, _ = c
    m = color(I, a) if callable(color) else (np.linalg.norm(I - np.array(color, np.float32), axis=2) < tol) & (a > 0.5)
    k, lab, st, _ = cv2.connectedComponentsWithStats(np.asarray(m, np.uint8), 8)
    if k < 2: return np.zeros(a.shape, np.float32)
    pm = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8)
    cs, _ = cv2.findContours(pm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    fill = np.zeros_like(pm); cv2.drawContours(fill, cs, -1, 1, -1)
    return np.clip(cv2.GaussianBlur(fill.astype(np.float32), (0, 0), soft), 0, 1)


def fill_container(body, inner, item, fill=1.0, sink=0.06, shade=0.35, squash=(1.0, 1.0), tint=None):
    """Put something into a container (compositing.md section 7.5): item (a top-down pancake, soup surface, a pile of
    fruit) is squashed and scaled to the ellipse of inner (the mouth), drawn only inside inner (the front rim hides its
    front edge naturally), with a ring of shade underneath -> new cell (C, a, M) for place_at / put_by_rim.
    body: the container cell (the "slightly high angle, empty pan body without handle" one, or the drawn cell);
    inner: result of inner_mask; fill: share of the mouth width (~0.9); sink: how far down (share of mouth ellipse
    height); squash=(sx, sy): extra squash (batter spreading from small to full); tint: colour multiplied onto item
    (raw batter -> cream). Cache results by parameters (it is slow per frame): key = (container, params) -> result."""
    I, a, M = body
    I = I.copy()
    ys, xs = np.nonzero(inner > 0.5)
    if len(xs) < 20: return (I, a, M)
    (ex, ey), (e1, e2), ang = cv2.fitEllipse(np.stack([xs, ys], 1).astype(np.float32))
    ew, eh = (max(e1, e2), min(e1, e2))
    PI, Pa, _ = item
    x0, y0, x1, y1 = kit.bbox(Pa, 0.5)
    PI, Pa = PI[y0:y1, x0:x1], Pa[y0:y1, x0:x1]
    if tint is not None: PI = np.clip(PI * np.asarray(tint, np.float32), 0, 1)
    w = max(4, int(ew * 0.9 * fill * squash[0])); h = max(4, int(w * (eh / max(1.0, ew)) * squash[1]))
    PI = cv2.resize(np.ascontiguousarray(PI), (w, h), interpolation=cv2.INTER_AREA)
    Pa = cv2.resize(np.ascontiguousarray(Pa), (w, h), interpolation=cv2.INTER_AREA)
    X0, Y0 = int(ex - w / 2), int(ey - h / 2 + sink * eh)
    sy_, sx_ = slice(max(0, Y0), min(I.shape[0], Y0 + h)), slice(max(0, X0), min(I.shape[1], X0 + w))
    pa = Pa[sy_.start - Y0:sy_.stop - Y0, sx_.start - X0:sx_.stop - X0] * inner[sy_, sx_]
    if shade: I[sy_, sx_] *= (1 - cv2.GaussianBlur(pa, (0, 0), 3) * shade)[..., None]
    I[sy_, sx_] = I[sy_, sx_] * (1 - pa[..., None]) + PI[sy_.start - Y0:sy_.stop - Y0, sx_.start - X0:sx_.stop - X0] * pa[..., None]
    return (I, a, M)


def put_by_rim(frame, c, rim_cell, rim_frame, info=None, **kw):
    """Cover a cell onto the frame by its rim: the rim ends in the cell rim_cell (measured by prop_spot) land on the
    frame ends rim_frame (the rim of the held pan: prop_spot on the drawn cell, then to_frame into the frame).
    Scale = ratio of rim lengths, rotation = angle difference.
    Usage: when the held pan is drawn level and its inside is hidden, generate a separate "slightly high angle, empty
    pan body without handle", put the content in with fill_container, then put_by_rim over the held pan body (handle
    and hand stay from the drawing). -> frame bbox"""
    (a0, b0), (a1, b1) = rim_cell; (A0, B0), (A1, B1) = rim_frame
    if a1 < a0: (a0, b0), (a1, b1) = (a1, b1), (a0, b0)
    if A1 < A0: (A0, B0), (A1, B1) = (A1, B1), (A0, B0)
    s = math.hypot(A1 - A0, B1 - B0) / max(1e-6, math.hypot(a1 - a0, b1 - b0))
    rot = -(math.degrees(math.atan2(B1 - B0, A1 - A0)) - math.degrees(math.atan2(b1 - b0, a1 - a0)))
    return place_at(frame, c, (A0 + A1) / 2, (B0 + B1) / 2, s, info=info, ref=((a0 + a1) / 2, (b0 + b1) / 2), rot=rot, **kw)


def rim_to_frame(rim, ref, x, y, s, rot=0.0, **kw):
    """Rim ends in the cell -> their frame positions when the cell is placed at (x, y) with place_at(ref=ref) (to_frame twice)"""
    return tuple(to_frame(ref, p, x, y, s, rot, **kw) for p in rim)


def spot_board(items, out, width=360):
    """Overlay prop_spot results on their cells in one image; look before using (mask green, rim red line).
    items: [(name, cell (I, a, M), prop_spot result or None)]. Typical mistakes: a piece of mask missing (the shaded
    half was not matched), the red line running into the handle or covering only half the pan. Rim widths that vary
    a lot across one sheet usually mean a bad measurement."""
    tiles = []
    for name, (I, a, _), sp in items:
        im = I * a[..., None] + 0.5 * (1 - a[..., None])
        im = np.ascontiguousarray((np.clip(im, 0, 1) * 255).astype(np.uint8)[..., ::-1])
        if sp:
            m = sp['mask'] > 0.5; im[m] = (im[m] * 0.5 + np.array([0, 255, 0]) * 0.5).astype(np.uint8)
            (x0, y0), (x1, y1) = sp['rim']; cv2.line(im, (int(x0), int(y0)), (int(x1), int(y1)), (0, 0, 255), 3)
        else:
            cv2.putText(im, 'none', (10, 40), 0, 1.2, (0, 0, 255), 3)
        cv2.putText(im, name, (10, im.shape[0] - 14), 0, 0.9, (255, 255, 255), 2)
        tiles.append(cv2.resize(im, (width, int(width * im.shape[0] / im.shape[1]))))
    h = max(t.shape[0] for t in tiles); tiles = [np.pad(t, ((0, h - t.shape[0]), (0, 0), (0, 0))) for t in tiles]
    tiles += [np.zeros_like(tiles[0])] * (-len(tiles) % 4)
    cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]))
    return out


def contact_shadow(frame, x, ground_y, width, lift=0.0, strength=0.45, offset=(0, 0), squash=0.16, falloff=None,
                   blur=None, tint=(0, 0, 0)):
    """Elliptical contact shadow on the ground (frame in place): the higher off the ground, the smaller, fainter, softer.
    width: shadow width on the ground (px, about the span of feet / wheels); lift: height above ground px; falloff:
    height where the shadow disappears (default 0.9 x width); squash: ellipse h / w; offset: shadow offset (papercraft
    shadows shift away from the light, e.g. (14, 6)); tint: shadow colour (0 = plain darkening)."""
    fall = falloff or 0.9 * width
    k = max(0.0, 1.0 - max(0.0, lift) / fall)
    if k <= 0.01 or strength <= 0: return frame
    ww = width * (0.55 + 0.45 * k); hh = max(2.0, ww * squash)
    sig = (blur if blur is not None else max(2.0, 0.05 * width)) * (1 + 1.5 * (1 - k))
    r = int(math.ceil(ww / 2 + 3 * sig)) + 2; rv = int(math.ceil(hh / 2 + 3 * sig)) + 2
    patch = np.zeros((2 * rv + 1, 2 * r + 1), np.float32)
    cv2.ellipse(patch, (r, rv), (max(1, int(ww / 2)), max(1, int(hh / 2))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    patch = cv2.GaussianBlur(patch, (0, 0), sig) * strength * k
    X0 = int(round(x + offset[0])) - r; Y0 = int(round(ground_y + offset[1])) - rv
    FH, FW = frame.shape[:2]
    fx0, fy0, fx1, fy1 = max(0, X0), max(0, Y0), min(FW, X0 + patch.shape[1]), min(FH, Y0 + patch.shape[0])
    if fx1 <= fx0 or fy1 <= fy0: return frame
    p = patch[fy0 - Y0:fy1 - Y0, fx0 - X0:fx1 - X0][..., None]
    frame[fy0:fy1, fx0:fx1] *= 1 - p * (1 - np.array(tint, np.float32))
    return frame


# =====================================================================================
# Scene light on characters (code may adjust light; code must not draw fx)
# =====================================================================================
# Generated transparent assets have flat studio light; pasted into night or dark scenes they look like stickers.
# Grading characters to the scene light is compositing and is allowed: edge decontamination, darkening / tinting,
# directional side light, warm light, rim light, per-column brightness from the background's light. Parameters
# live in style.json preset.light.
LIGHT = dict(decontam=0, tint=[1.0, 1.0, 1.0], expo=1.0, gamma=1.0, side=None, rim=0.0, rim_col=[1.0, 1.0, 1.0],
             rim_dir=[7, -7], rim_soft=2.0, warm_col=[1.30, 1.02, 0.62])
_LIT = {}


def decontam(C, a, r=6):
    """Edge decontamination: semi-transparent edges (alpha < 0.95) take the solid colour r px further in. Generated
    fur edges keep the backdrop colour and show as a grey fringe on dark backgrounds"""
    w = (a > 0.95).astype(np.float32)
    num = cv2.GaussianBlur(C * w[..., None], (0, 0), r); den = cv2.GaussianBlur(w, (0, 0), r)[..., None]
    num2 = cv2.GaussianBlur(C * w[..., None], (0, 0), r * 3); den2 = cv2.GaussianBlur(w, (0, 0), r * 3)[..., None]
    inner = np.where(den > 0.02, num / np.maximum(den, 1e-4), num2 / np.maximum(den2, 1e-4))
    k = np.clip((a - 0.5) / 0.45, 0, 1)[..., None]
    return C * k + inner * (1 - k)


def rim_mask(a, d=(7, -7), soft=2.0):
    """Where the rim light goes: light from direction d (upper right = (+x, -y)), the band of the subject next to transparency on the lit side -> 0-1"""
    h, w = a.shape; dx, dy = d
    sh = cv2.warpAffine(np.ascontiguousarray(a, np.float32), np.float32([[1, 0, -dx], [0, 1, -dy]]), (w, h), borderValue=0)
    return cv2.GaussianBlur(np.clip(a - sh, 0, 1), (0, 0), soft) * a


def char_light(c, cfg=None, scale=1.0, warm=0.0, warm_side='left', gain=1.0, flip=False):
    """Grade a cell to the scene light -> new (C, a, M) for place_at. Cached by (cell, params), so per-frame calls are cheap.
    cfg: style.json preset.light (missing keys from LIGHT):
      decontam edge decontamination radius px (0 = off), tint colour cast, expo exposure, gamma (> 1 deeper shadows),
      side [left, right]: multipliers at the bbox's left and right edges (light from the left = [1.28, 0.43]),
      rim rim-light strength, rim_col colour, rim_dir [dx, dy] where the light comes from (px, at 8-cell sheet size),
      rim_soft, warm_col warm-light colour.
    scale: how many times bigger the cell is than an 8-cell sheet cell (close-up sheet ~ 2); decontam and rim widths scale with it.
    warm 0-1, warm_side (left / right / bottom / all): the side lit by a lantern or fire. gain: overall multiplier (inside / outside a light pool).
    flip=True: the cell will be mirrored when placed; light direction follows the mirrored image.
    E.g. animi.place_at(frame, animi.char_light(cel['walk_3'], STYLE['light']), x, y, s, info=A['walk_3'])"""
    C0, a0, M0 = c
    q = dict(LIGHT); q.update(cfg or {})
    key = (id(C0), id(a0), json.dumps(q, sort_keys=True), round(scale, 3), round(float(warm), 3), warm_side,
           round(float(gain), 3), bool(flip))
    if key in _LIT: return _LIT[key][1]
    C, a = (C0[:, ::-1], a0[:, ::-1]) if flip else (C0, a0)
    C = np.ascontiguousarray(C, np.float32); a = np.ascontiguousarray(a, np.float32)
    if q['decontam']: C = decontam(C, a, q['decontam'] * scale)
    if q['gamma'] != 1.0: C = np.power(np.clip(C, 0, None), q['gamma'])
    C = C * (np.float32(q['tint']) * q['expo'] * gain)
    h, w = a.shape
    if q['side']:
        x0, _, x1, _ = kit.bbox(a, 0.5)
        u = np.clip((np.arange(w, dtype=np.float32) - x0) / max(1, x1 - x0), 0, 1)
        sd = q['side'][0] + (q['side'][1] - q['side'][0]) * np.clip((u - 0.15) / 0.85, 0, 1) ** 1.2
        C = C * sd[None, :, None]
    if warm > 0:
        if warm_side == 'all': g = np.ones((h, w), np.float32)
        elif warm_side == 'bottom': g = np.tile(np.linspace(0.15, 1, h, dtype=np.float32)[:, None], (1, w))
        else:
            g = np.tile(np.linspace(1, 0.1, w, dtype=np.float32)[None, :], (h, 1))
            if warm_side == 'right': g = g[:, ::-1]
        C = C * (1 + (warm * g)[..., None] * (np.float32(q['warm_col']) - 1))
    if q['rim'] > 0:
        d = (int(round(q['rim_dir'][0] * scale)), int(round(q['rim_dir'][1] * scale)))
        C = C + rim_mask(a, d, q['rim_soft'] * scale)[..., None] * np.float32(q['rim_col']) * q['rim'] * gain
    C = np.clip(C, 0, None)                  # scale pixels above 1.3 down proportionally (not per channel: clipping red but not green turns olive when darkened later)
    C = (C * np.minimum(1.0, 1.3 / np.maximum(C.max(axis=2, keepdims=True), 1e-6))).astype(np.float32)
    if flip: C, a = C[:, ::-1], a[:, ::-1]
    out = (np.ascontiguousarray(C), np.ascontiguousarray(a) if flip else a0, M0)
    if len(_LIT) > 600: _LIT.clear()
    _LIT[key] = (c, out)                     # keep a reference to the source cell so its id is not reused
    return out


_PROF = {}


def floor_light(plate, gy, cam, cfg=None, SH=None, plate2=None, mix=None):
    """Light painted into the background -> f(frame x array) -> brightness gain, for place_at(gain=).
    Measures the background's brightness along the ground line gy (stage y) (light pool centre ~ 1); a character
    walking out of the light darkens with it, naturally aligned with the background.
    cfg: preset.light floor = {lo: what is left fully in the dark (0.16), gamma: how steep the pool edge is (1.8)}. cam: current camera.
    plate2 + mix(x, y): when two versions of the background are mixed by position (light_flood), the curves mix by the
    same ratio; the bright version is normalised to the dark version's pool centre (turning the light up really
    brightens the character). The template's put() hooks this up when the style has light.floor."""
    fl = dict(lo=0.16, gamma=1.8); fl.update(((cfg or {}).get('floor') or {}) if isinstance(cfg, dict) else {})
    SH = SH or cam.SH
    if plate2 is not None and mix is not None:
        xs1, p1, _ = _profile(plate, gy, cam, SH, raw=True)
        xs2, p2, _ = _profile(plate2, gy, cam, SH, raw=True)
        ref = max(1e-3, float(np.percentile(p1, 97)))
        ccx, _, z = cam._c(1.0)
        def g(X):
            sx = (np.asarray(X, np.float32) - cam.W / 2) / z + ccx
            m = mix(sx, gy)
            v = (np.interp(sx, xs1, p1) * (1 - m) + np.interp(sx, xs2, p2) * m) / ref
            return fl['lo'] + (1 - fl['lo']) * np.clip(v, 0, 1.25) ** fl['gamma']
        return g
    xs, p, _ = _profile(plate, gy, cam, SH)
    ccx, _, z = cam._c(1.0)
    def f(X):
        sx = (np.asarray(X, np.float32) - cam.W / 2) / z + ccx
        v = np.interp(sx, xs, p)
        return fl['lo'] + (1 - fl['lo']) * np.clip(v, 0, 1.25) ** fl['gamma']
    return f


def _profile(plate, gy, cam, SH, raw=False):
    """Brightness curve along the background's ground line gy (cached by (image, gy)) -> (stage x, normalised brightness, image); raw=True: not normalised"""
    key = (id(plate), int(gy // 4))
    if key not in _PROF:
        h, w = plate.shape[:2]
        Y = plate[..., 0] * 0.3 + plate[..., 1] * 0.55 + plate[..., 2] * 0.15
        Y = cv2.GaussianBlur(np.ascontiguousarray(Y, np.float32), (0, 0), w * 0.02)
        r = int(np.clip(gy, 0, SH - 1) * h / SH); b = max(4, int(h * 0.03))
        p = Y[max(0, r - b):r + b].mean(0)
        if len(_PROF) > 64: _PROF.clear()
        ref = max(1e-3, float(np.percentile(p, 97)))
        _PROF[key] = (np.arange(w, dtype=np.float32) * cam.SW / w, p / ref, plate, ref)
    xs, p, img, ref = _PROF[key]
    return (xs, p * ref, img) if raw else (xs, p, img)


def light_pool(cam, cx, cy, r, lo=0.22, sq=0.55, par=1.0):
    """Light pool (torch, spotlight, a small lamp circle): flat ellipse of brightness centred (cx, cy) on stage, radius r
    -> frame-size multiplier HxW. Multiply background and characters by the same map: frame *= pool[..., None].
    When the pool shrinks, put its centre on the light's side and keep the hero in the light."""
    ccx, ccy, z = cam._c(par)
    xs = (np.arange(cam.W, dtype=np.float32) - cam.W / 2) / z + ccx
    ys = (np.arange(cam.H, dtype=np.float32) - cam.H / 2) / z + ccy
    d2 = ((xs[None, :] - cx) / r) ** 2 + ((ys[:, None] - cy) / (r * sq)) ** 2
    return (lo + (1 - lo) * np.exp(-d2 * 1.6)).astype(np.float32)


NIGHT = (0.92, 0.97, 1.08)


def recolor(img, hue=0.0, sat=1.0, only=None, tol=20.0, min_sat=0.3):
    """Recolour a cell by hue (siblings in a group: the same walk sheet in another colour is another character).
    img: (C, a, M) from kit.sprite, or a float RGB; returns the same type (alpha untouched).
    hue: hue rotation in degrees (+120 red -> green); sat: saturation multiplier (0.85 = paler).
    only=source hue (degrees): change only pixels near that hue and saturated enough (min_sat) (only the red scarf,
    not the yellow body); tol tolerance (degrees). Register as a variant cell in the template's load():
    cells['walk_3~b'] = animi.recolor(cells['walk_3'], hue=120), and use 'walk_3~b' in the timesheet."""
    C = img[0] if isinstance(img, tuple) else img
    hsv = cv2.cvtColor(np.ascontiguousarray(np.clip(C, 0, 1), np.float32), cv2.COLOR_RGB2HSV)     # H 0-360
    if only is None: m = hsv[..., 1] >= min_sat
    else:
        dh = np.abs((hsv[..., 0] - float(only) + 180) % 360 - 180)
        m = (dh <= tol) & (hsv[..., 1] >= min_sat)
    hsv[..., 0] = np.where(m, (hsv[..., 0] + hue) % 360, hsv[..., 0])
    hsv[..., 1] = np.where(m, np.clip(hsv[..., 1] * sat, 0, 1), hsv[..., 1])
    out = np.clip(cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB), 0, 1).astype(np.float32)
    return (out, img[1], img[2]) if isinstance(img, tuple) else out


def darken(frame, dark, tint=NIGHT):
    """Darken the whole scene (light goes out, night, a cloud passes): frame x k x cool tint. dark = number k, or
    dict(k=0.6, tint=[...]). Characters and background together (at the end of render, before grading); lantern and
    flame light is added after darkening (warm_glow / self_glow) and is not darkened.
    To brighten back, ease k from 0.6 to 1 over the drawings. Edits and returns frame"""
    if isinstance(dark, dict): k, tint = float(dark.get('k', 0.6)), dark.get('tint', tint)
    else: k = float(dark)
    if k == 1.0 and tuple(tint) == (1, 1, 1): return frame
    frame *= np.float32(k) * np.asarray(tint, np.float32)
    return frame


LAMP_COL = (1.0, 0.72, 0.32)


def warm_glow(frame, x, y, r, k=0.3, col=LAMP_COL, halo=(3.0, 0.4)):
    """Additive warm light (lantern, candle, firefly, window): a Gaussian warm glow of radius r at frame (x, y), plus a
    faint halo of halo[0] x radius at halo[1] x strength. The source may be off-frame (a lantern off the top left
    shining down). No flicker. Edits and returns frame.
    Typical: find the lamp in the lantern cell with part_center -> to_frame -> warm_glow(frame, X, Y, sqrt(area) x s x 1.1, 0.3)"""
    H, W = frame.shape[:2]
    for rr, kk in ((r, k), (r * halo[0], k * halo[1])) if halo else ((r, k),):
        if kk <= 0 or rr <= 0: continue
        R = int(rr * 3); X0, Y0 = max(0, int(x - R)), max(0, int(y - R)); X1, Y1 = min(W, int(x + R)), min(H, int(y + R))
        if X1 <= X0 or Y1 <= Y0: continue
        yy, xx = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
        g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * rr * rr)) * kk
        frame[Y0:Y1, X0:X1] += g[..., None] * np.asarray(col, np.float32)
    return frame


def self_glow(frame, c, X, Y, s, info=None, boost=1.5, add=0.08, halo=40.0, halo_k=1.2, col=(1.0, 0.62, 0.25), **kw):
    """Self-lit fx (flame, wick, firefly, magic light): a generated flame looks like a made prop and is not bright
    enough; brighten it as self-lit (C x boost + add) and add a halo in its own shape after placing (alpha blurred by
    halo px, colour col x halo_k). Other parameters as place_at (anchor, ref, rot...). Call after darkening so the
    halo is not darkened. -> frame bbox"""
    C, a, M = c
    hot = (np.clip(C * boost + add, 0, 1.4).astype(np.float32), a, M)
    L = Layer(frame)
    box = place_at(L, hot, X, Y, s, info=info, **kw)
    L.composite(frame)
    if halo > 0 and halo_k > 0:
        g = cv2.GaussianBlur(L.A, (0, 0), halo)
        frame += g[..., None] * np.asarray(col, np.float32) * halo_k
    return box


def flood_mask(cam, cx, cy, R, soft=260.0, sq=1.6, par=1.0):
    """Area lit by spreading light: a circle of radius R around the source (cx, cy) on stage (squashed vertically by sq: light on a tabletop is flat), soft px edge -> frame-size HxW 0-1"""
    ccx, ccy, z = cam._c(par)
    xs = (np.arange(cam.W, dtype=np.float32) - cam.W / 2) / z + ccx
    ys = (np.arange(cam.H, dtype=np.float32) - cam.H / 2) / z + ccy
    d = np.sqrt((xs[None, :] - cx) ** 2 + ((ys[:, None] - cy) * sq) ** 2)
    return np.clip(1 - (d - R) / soft, 0, 1).astype(np.float32)


def light_flood(cam, dim, bright, cx, cy, R, soft=260.0, sq=1.6, par=1.0):
    """Light spreading (turning up a lamp, switching on, daybreak): a dark and a bright background from the same camera;
    the bright one spreads out from the source in a circle (grow R from small to full over ~20 drawings).
    -> (frame, stage mix function mix(x, y)). Characters mix their brightness by the same mix: in put pass
    gain=floor_light(dim, gy, cam, LIGHT, plate2=bright, mix=mix). Never cross-fade the whole image (the bright version often has extra things drawn)"""
    m = flood_mask(cam, cx, cy, R, soft, sq, par)[..., None]
    frame = cam.plate(dim, par) * (1 - m) + cam.plate(bright, par) * m
    mix = lambda x, y: np.clip(1 - (np.sqrt((np.asarray(x, np.float32) - cx) ** 2 + ((np.asarray(y, np.float32) - cy) * sq) ** 2) - R) / soft, 0, 1)
    return frame.astype(np.float32), mix


# =====================================================================================
# Shadows other than contact shadows (close relief shadow, hard-light cast shadow)
# =====================================================================================
SHADOW = dict(kind=None, k=0.32, off=[2.5, 0.022, 16.0], blur=[0.8, 0.45], dir=[0.8, 1.0],
              light=[0.85, 0.13], cast_k=0.42, cast_blur=2.2, contact=0.35, contact_w=0.9, contact_off=[0.0, 0.0])


def _placed(c, x, y, s, info=None, **kw):
    """Place a cell on a temporary layer just big enough -> (A alpha, X0, Y0, frame bbox)"""
    C, a, M = c
    h, w = a.shape
    R = int(1.1 * math.hypot(h, w) * s * max(kw.get('sx', 1.0), kw.get('sy', 1.0))) + 40
    X0, Y0 = int(x) - R, int(y) - R
    L = Layer(2 * R, 2 * R)
    box = place_at(L, c, x - X0, y - Y0, s, info=info, **kw)
    return L.A, X0, Y0, (box[0] + X0, box[1] + Y0, box[2] + X0, box[3] + Y0)


def _mul_alpha(frame, A, X0, Y0, k):
    H_, W_ = frame.shape[:2]; h, w = A.shape
    fx0, fy0, fx1, fy1 = max(0, X0), max(0, Y0), min(W_, X0 + w), min(H_, Y0 + h)
    if fx1 <= fx0 or fy1 <= fy0: return frame
    frame[fy0:fy1, fx0:fx1] *= (1 - k * A[fy0 - Y0:fy1 - Y0, fx0 - X0:fx1 - X0])[..., None]
    return frame


def relief_shadow(frame, c, x, y, s, info=None, lift=0.0, cfg=None, **kw):
    """Close relief shadow (flat styles: cut paper, plasticine relief, shadow puppets, overhead shots): the character's
    silhouette shifted a few px along dir, blurred, darkened. Offset = min(off[2], off[0] + off[1] x character size);
    lift 0-1 = how far off the paper (shadow further, fainter, softer). Parameters in preset.shadow (k, off, blur, dir).
    Draw the shadow before place_at."""
    q = dict(SHADOW); q.update(cfg or {})
    A, X0, Y0, box = _placed(c, x, y, s, info, **kw)
    size = max(box[2] - box[0], box[3] - box[1])
    off = min(q['off'][2], q['off'][0] + q['off'][1] * size) * (1 + 3.0 * lift)
    dx, dy = int(round(off * q['dir'][0])), int(round(off * q['dir'][1]))
    S = np.zeros_like(A); h, w = A.shape
    S[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = A[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    S = cv2.GaussianBlur(S, (0, 0), q['blur'][0] + q['blur'][1] * off * (1 + lift))
    return _mul_alpha(frame, S, X0, Y0, q['k'] * (1 - 0.55 * lift))


def cast_shadow(frame, c, x, y, s, info=None, lift=0.0, cfg=None, **kw):
    """Hard-light cast shadow (desk lamp, sun: cardboard, puppets, tin): the cell's silhouette squashed at the ground
    line and cast diagonally on the floor. light = (kx, ky): a point at height h lands kx·h right and ky·h back
    (light at upper left = positive kx); lift: height off the ground (shadow fades and leaves the feet).
    Parameters in preset.shadow (light, cast_k, cast_blur). Draw the shadow before place_at."""
    q = dict(SHADOW); q.update(cfg or {})
    A, X0, Y0, _ = _placed(c, x, y, s, info, **kw)
    kx, ky = q['light']; Yl = y - Y0
    Mt = np.float32([[1, -kx, kx * Yl], [0, ky, Yl * (1 - ky) + lift * 0.3]])
    h, w = A.shape
    pad = int(abs(kx) * h) + 4
    big = np.zeros((h, w + 2 * pad), np.float32); big[:, pad:pad + w] = A
    S = cv2.warpAffine(big, Mt, (w + 2 * pad, h), flags=cv2.INTER_LINEAR, borderValue=0)
    S = cv2.GaussianBlur(S, (0, 0), q['cast_blur'] + lift * 0.02)
    return _mul_alpha(frame, np.clip(S, 0, 1), X0 - pad, Y0, q['cast_k'] * max(0.0, 1.0 - lift / 400.0))


def shadow_cfg(style):
    """The style's shadow settings: preset.shadow; without kind, top-down styles (flags.top_down) use relief, others contact"""
    q = dict(SHADOW); q.update((style or {}).get('shadow') or {})
    if not q.get('kind'): q['kind'] = 'relief' if ((style or {}).get('flags') or {}).get('top_down') else 'contact'
    return q


def shadow(frame, c, x, y, s, info=None, style=None, lift=0.0, shadow_w=None, shadow_off=None, shadow_k=None, **kw):
    """Draw this cell's shadow per the style (call before place_at, same parameters as place_at):
    contact elliptical contact shadow / relief close relief shadow / cast hard-light cast shadow / none. lift: px off
    the ground (relief takes 0-1). Contact width and offset: preset.shadow contact_w (shadow width = character width x
    it, default 0.9), contact_off ([x, y] offset as a share of character width, default [0, 0]; light from the left,
    shadow to the right: [0.06, 0]); shadow_w / shadow_off / shadow_k override once (feet set wide apart, two legs)"""
    q = shadow_cfg(style)
    if shadow_k is not None: q = dict(q, contact=shadow_k, k=shadow_k, cast_k=shadow_k)
    if q['kind'] == 'none': return frame
    if q['kind'] == 'relief': return relief_shadow(frame, c, x, y, s, info, min(1.0, lift / 100.0 if lift > 1 else lift), q, **kw)
    if q['kind'] == 'cast': return cast_shadow(frame, c, x, y, s, info, lift, q, **kw)
    if info is None: info = cell_anchor(c[1])
    wd = info['width'] * s
    ox, oy = shadow_off if shadow_off is not None else q.get('contact_off', (0.0, 0.0))
    return contact_shadow(frame, x + kw.get('dx', 0.0) + ox * wd, y + kw.get('dy', 0.0) + oy * wd,
                          width=wd * (shadow_w if shadow_w is not None else q.get('contact_w', 0.9)), lift=lift, strength=q['contact'])


# =====================================================================================
# Registering by any point: hand tip, beak tip, held objects
# =====================================================================================
def cell_tip(a, direction=(1.0, -0.6), th=0.5, near=6):
    """The point of the cell furthest in direction (cell coords): beak tip (1, -0.6), hand reaching forward (1, 0),
    raised hand (0, -1), toe (1, 1). Averages the points within near px of the furthest, so it does not jump between cells. -> (x, y)"""
    ys, xs = np.nonzero(np.asarray(a) > th)
    if not len(xs): return (0.0, 0.0)
    d = np.float32(direction) / max(1e-6, float(np.hypot(*direction)))
    sc = xs * d[0] + ys * d[1]
    m = sc >= sc.max() - near
    return float(xs[m].mean()), float(ys[m].mean())


def part_center(c, color, tol=0.18, round_only=False):
    """Find a part of a cell by colour (fruit in hand, lantern, button) -> (cx, cy, bbox) or None.
    color: (r, g, b) 0-1 or f(I, a) -> bool mask. round_only: only roughly round blobs (aspect 0.6-1.6), so a mouth or scarf of the same colour is not picked."""
    I, a, _ = c
    m = color(I, a) if callable(color) else (np.linalg.norm(I - np.array(color, np.float32), axis=2) < tol) & (a > 0.5)
    n, lab, st, cen = cv2.connectedComponentsWithStats(np.asarray(m, np.uint8), 8)
    best = None
    for i in range(1, n):
        x, y, w, h, area = st[i]
        if area < 30: continue
        if round_only and not (0.6 <= w / max(1, h) <= 1.6 and area > 0.5 * w * h): continue
        if best is None or area > best[0]: best = (area, float(cen[i][0]), float(cen[i][1]), [int(x), int(y), int(x + w), int(y + h)])
    return None if best is None else best[1:]


def part_refs(cells, color, tol=0.18, round_only=False, names=None):
    """Register a sheet's cells by a prop (the same lamp or brass knob drifts tens of px between close-up cells):
    find that part's centre in each cell by colour -> {cell: (cx, cy)}; place with place_at(..., ref=refs[cell]) and
    the part lands on the same frame point, no jump between cells. Cells where it is not found get the median offset
    from the bbox of the others. color as part_center (colour or f(I, a) -> mask)"""
    names = list(names or cells)
    got, rel = {}, []
    for k in names:
        r = part_center(cells[k], color, tol, round_only)
        if r is None: continue
        got[k] = (r[0], r[1])
        x0, y0, x1, y1 = kit.bbox(cells[k][1], 0.5); rel.append((r[0] - x0, r[1] - y0))
    if not got: return {}
    mx, my = float(np.median([q[0] for q in rel])), float(np.median([q[1] for q in rel]))
    for k in names:
        if k not in got:
            x0, y0, _, _ = kit.bbox(cells[k][1], 0.5); got[k] = (x0 + mx, y0 + my)
    return got


def to_frame(ref, pt, x, y, s, rot=0.0, sx=1.0, sy=1.0):
    """Where point pt of a cell lands in the frame when the cell is placed with place_at(ref=ref) at (x, y), scale s,
    rotation rot (degrees, counter-clockwise). Hand-offs: compute where the point on A's hand is, then register B's point to it."""
    dx, dy = (pt[0] - ref[0]) * s * sx, (pt[1] - ref[1]) * s * sy
    th = math.radians(rot); cs, sn = math.cos(th), math.sin(th)
    return x + cs * dx + sn * dy, y - sn * dx + cs * dy


# =====================================================================================
# Missing images: images not generated yet use a _bad version or a placeholder; the film still renders and can be reviewed, but checks keep reporting it
# =====================================================================================
MISSING = {}


def _placeholder_img(path, w=1600, h=900):
    img = np.zeros((h, w, 3), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    img[:] = 0.55 + 0.06 * (((xx // 80) + (yy // 80)) % 2)[..., None]
    try:
        import fx
        t = fx.text('placeholder: ' + os.path.basename(path), 'siyuan', 64, color=(0.9, 0.2, 0.2), shadow=0)
        fx.put(img, t, w / 2, h / 2, anchor='cc')
    except Exception: pass
    return img


def asset(path, placeholder=True):
    """Read a background / asset image (float RGB). When missing, fall back to <name>_bad.png, then a grey checker
    placeholder, and record it in MISSING. While MISSING is not empty the template's lint reports "unfinished" and the
    full render writes only a draft, not out/<NAME>.mp4."""
    if os.path.exists(path): return kit.rd(path)
    root, ext = os.path.splitext(path)
    bad = root + '_bad' + (ext or '.png')
    if os.path.exists(bad):
        MISSING[path] = '_bad version'; return kit.rd(bad)
    if not placeholder: raise FileNotFoundError(path)
    MISSING[path] = 'placeholder'
    return _placeholder_img(path)


def missing_report(quiet=False):
    """-> list of images using a _bad version or a placeholder ([(path, '_bad version' | 'placeholder')])"""
    out = sorted(MISSING.items())
    if not quiet:
        for p, k in out: print(f'missing image: {os.path.relpath(p)} not generated yet, using {k} (cannot deliver)', file=sys.stderr)
    return out


# =====================================================================================
# Cartoon shapes
# =====================================================================================
def outlined(mask, line=7, fill=0.97, line_color=0.0):
    """Binary shape (HxW, 0/1) -> (P premultiplied RGB, A): white fill + black outline (outline by dilation); used for
    1930s-cartoon Z's, smoke puffs, music notes. For line boil, redraw the shape with a new random seed per drawing.
    Paste with kit.over(frame, P, A, x0, y0) or fx.put(frame, (P, A), ...)"""
    mk = (np.asarray(mask) > 0.5).astype(np.uint8)
    pad = line + 3
    mk = np.pad(mk, pad)
    m = cv2.GaussianBlur(mk.astype(np.float32), (0, 0), 0.8)
    o = cv2.dilate(mk, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * line + 1, 2 * line + 1))).astype(np.float32)
    o = cv2.GaussianBlur(o, (0, 0), 0.8)
    a = np.clip(o, 0, 1); m = np.clip(m, 0, 1)
    col = m * fill + (1 - m) * line_color
    P = (col * a)[..., None].repeat(3, 2)
    return P.astype(np.float32), a.astype(np.float32)


# =====================================================================================
# Timesheet (counted in drawings)
# =====================================================================================
class Timesheet:
    """Timeline counted in drawings (one drawing = one pic).
      ts = Timesheet(fps=24, on=2, seed=7)
      ts.add('run_0', x=100)              # one drawing held on=2 frames (on twos)
      ts.add('jump_3', holds=4, lift=90)  # hold key poses longer: one drawing for 4 frames (holds is in frames, not drawings or seconds)
      ts.add('run_1', holds=1)            # fast action on ones
      ts.add('idle_2', times=3)           # the same pose for 3 drawings (add idle=True for idle breathing)
      ts.extend(14)                       # ending: hold the last drawing 14 frames, same drawing number (no jitter)
      for fr in ts.frames(): fr['i'] frame number, fr['pic'] drawing number, fr['cell'], fr['k'] frame within the
          drawing, fr['t'] seconds, plus the state given to add
    All random values are keyed by drawing number (the frames of one drawing are identical; they change only with
    the drawing): jitter / jscale / flicker / seed. State values may be functions f(pic) -> value (common in cycle)."""
    def __init__(self, fps=24, on=2, seed=0):
        self.fps, self.on, self.seed0 = fps, on, seed
        self.pics = []            # [(cell, holds, state)]
        self.tail = 0

    def add(self, cell, holds=None, times=1, **state):
        for _ in range(int(times)):
            p = len(self.pics)
            st = {k: (v(p) if callable(v) else v) for k, v in state.items()}
            self.pics.append((cell, int(holds or self.on), st))
        return len(self.pics) - 1

    def cycle(self, names, count, holds=None, start=0, **state):
        """Cycle: take count drawings from names in a loop (e.g. 8-cell run x 2.5 laps = 20). state may be f(k), k = drawing within this run"""
        for k in range(int(count)):
            st = {kk: (v(k) if callable(v) else v) for kk, v in state.items()}
            self.add(names[(start + k) % len(names)], holds, **st)
        return len(self.pics) - 1

    def act(self, beats, count=None, **state):
        """A piece of acting, pose to pose, fast in, slow hold: beats=[(cell, drawings), ...]. In-betweens 1-2 drawings
        (over in a flash), key poses hold 3-8, a reaction the audience must read holds 1-2 s; a last 0 = hold until
        the end of this run (count drawings). Repeats of one cell use times=; holds of 6+ drawings get idle=True
        automatically (idle breathing for soft materials). Never change cells evenly by time (int(t * speed)
        flip-book pacing is the stiffest). state as add; may be f(k), k = drawing within this run.
          ts.act([('greet_0', 1), ('greet_2', 4), ('greet_3', 1), ('greet_5', 6), ('greet_6', 1), ('greet_7', 0)], 40, x=760)"""
        left = None if count is None else int(count); k = 0
        for cell, n in beats:
            n = int(n) if n else (left if left is not None else 1)
            if left is not None: n = min(n, left)
            for _ in range(n):
                st = {kk: (v(k) if callable(v) else v) for kk, v in state.items()}
                if n >= 6: st.setdefault('idle', True)
                self.add(cell, **st); k += 1
            if left is not None:
                left -= n
                if left <= 0: break
        if left:
            last = self.pics[-1]
            for _ in range(left):
                st = {kk: (v(k) if callable(v) else v) for kk, v in state.items()}; st.setdefault('idle', True)
                self.add(last[0], **st); k += 1
        return len(self.pics) - 1

    def settle(self, pic, amp=0.03, rigid=False, min_pics=3, shot_at=0):
        """Settle into a pose that holds: on arrival the body sinks by amp, rebounds a little on the next drawing, and
        is steady on the third (vertical only, volume kept, pivot at the feet, no sideways shift). Only when the same
        cell runs >= min_pics drawings (not for walks and runs that change every drawing); not for rigid materials;
        not for a pose already there when the shot starts (shot_at = the shot's first drawing: a cut is not a pose
        change). -> dict(sy, sx) for place_at, {} when not needed. The template's put() adds it to the hero
        automatically (STYLE settle sets the amount, 0 = off)."""
        if rigid or not amp or not (0 <= pic < len(self.pics)): return {}
        base = cell_base(self.pics[pic][0])
        a = pic
        while a > 0 and cell_base(self.pics[a - 1][0]) == base: a -= 1
        b = pic
        while b + 1 < len(self.pics) and cell_base(self.pics[b + 1][0]) == base: b += 1
        k = pic - a
        if a <= shot_at or b - a + 1 < min_pics or k > 2: return {}
        sy = 1 + amp * (-1.0, 0.4, -0.12)[k]
        return dict(sy=sy, sx=1 / math.sqrt(sy))

    def extend(self, frames):
        """Hold the last drawing frames more frames without changing the drawing number (ending hold, fade-out)"""
        self.tail += int(frames)

    def frames(self):
        out, i = [], 0
        last = len(self.pics) - 1
        for p, (cell, holds, st) in enumerate(self.pics):
            n = holds + (self.tail if p == last else 0)
            for k in range(n):
                d = dict(st); d.update(i=i, pic=p, cell=cell, k=k, holds=holds, start=i - k, t=i / self.fps)
                out.append(d); i += 1
        return out

    def __len__(self): return sum(h for _, h, _ in self.pics) + self.tail
    @property
    def n_pics(self): return len(self.pics)
    def duration(self): return len(self) / self.fps

    def pic_start(self, pic):
        """First frame of drawing pic"""
        return sum(h for _, h, _ in self.pics[:pic])

    def _rng(self, pic, salt):
        h = sum((i + 1) * ord(ch) for i, ch in enumerate(str(salt))) & 0xFFFFFF
        return np.random.default_rng([self.seed0 & 0xFFFFFFFF, int(pic) & 0xFFFFFFFF, h])

    def jitter(self, pic, amp=1.0, n=2, salt='pos'):
        """Deterministic per-drawing jitter: n values N(0,1) x amp (default (dx, dy)). Always the same for the same drawing"""
        v = self._rng(pic, salt).normal(0, 1, n) * amp
        return tuple(float(x) for x in v) if n > 1 else float(v[0])

    def jscale(self, pic, amp=0.006, salt='scale'):
        """Per-drawing scale jitter multiplier: 1 + N(0,1) x amp (stop-motion's +-0.5% breathing)"""
        return 1.0 + self.jitter(pic, amp, 1, salt)

    def flicker(self, pic, amp=0.012, salt='light'):
        """Per-drawing brightness flicker multiplier: 1 + N(0,1) x amp (stop-motion light flicker +-1.2%)"""
        return 1.0 + self.jitter(pic, amp, 1, salt)

    @staticmethod
    def _key(cell, st):
        """Long holds are judged on everything drawn in the frame: cell name (including @ position, ~ variant, 'a+b' together) + the state's cells list"""
        extra = st.get('cells')
        return (cell, tuple(extra) if isinstance(extra, (list, tuple)) else extra)

    def lint(self, max_hold=2.0, quiet=False, drawn=None):
        """Check for stiffness: warn when everything drawn holds for more than max_hold seconds in a row (repeats with
        times= count as the same cell). "What this drawing shows": the cell name ('a+b' together, 'walk_3@120' with a
        position and 'close_1~b' variants all count as different) + the state's cells=[...] (cells for supporting
        characters, environment layers); drawn={drawing: what was actually drawn} (passed by the template's board)
        takes precedence. Runs whose state has live='reason' (camera pushing, environment moving, checked by eye) are
        still listed but marked as checked, not a problem.
        -> [(start s, duration s, cell), ...] (live runs excluded). Holding one drawing 1-2 s is normal (a key pose to
        read); beyond 2 s add a small local action (face-only ~b variants: blink, mouth; tail, ears), or make sure
        something else in frame moves (environment, supporting character, camera), then write live.
        Never cycle body poses back and forth to fake movement: that reads as rocking."""
        bad, i, p = [], 0, 0
        pics = self.pics
        key = (lambda q: drawn.get(q, self._key(*pics[q][::2]))) if drawn else (lambda q: self._key(pics[q][0], pics[q][2]))
        while p < len(pics):
            k0 = key(p); q = p; dur = 0; live = None
            while q < len(pics) and key(q) == k0:
                dur += pics[q][1] + (self.tail if q == len(pics) - 1 else 0); live = live or pics[q][2].get('live'); q += 1
            if dur / self.fps > max_hold:
                item = (round(i / self.fps, 2), round(dur / self.fps, 2), pics[p][0])
                if live:
                    if not quiet: print(f'Timesheet.lint: "{item[2]}" from {item[0]:.2f}s holds {item[1]:.2f}s: checked ({live})', file=sys.stderr)
                else: bad.append(item)
            i += dur; p = q
        if not quiet:
            for t0, d, c in bad: print(f'Timesheet.lint: "{c}" from {t0:.2f}s holds {d:.2f}s (> {max_hold}s): the frame may look dead', file=sys.stderr)
            if not bad: print(f'Timesheet.lint: OK (no hold longer than {max_hold}s)', file=sys.stderr)
            for t0, d, cs in self.pingpong():
                print(f'Timesheet.lint: note: from {t0:.2f}s for {d:.2f}s standing still (x unchanged), body switching back and '
                      f'forth between {", ".join(cs)}: reads as rocking. Play through once in order and hold the last drawing '
                      '(face-only ~ variants do not count)', file=sys.stderr)
        return bad

    def pingpong(self, min_sec=1.0):
        """Check for standing ping-pong: within a run where the state's x never changes, the body cell (without ~ suffix)
        switches away and back two or more times. -> [(start s, duration s, [cells...]), ...]. A walk cycle in place
        (x unchanged) is caught too: that is marching on the spot."""
        out, i, p, pics = [], 0, 0, self.pics
        num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
        while p < len(pics):
            x0 = pics[p][2].get('x'); q, dur = p, 0
            while q < len(pics) and num(x0) and pics[q][2].get('x') == x0 and '@' not in str(pics[q][0]):
                dur += pics[q][1]; q += 1
            if q == p: i += pics[p][1]; p += 1; continue
            seq = []
            for k in range(p, q):
                c = cell_base(pics[k][0])
                if not seq or seq[-1] != c: seq.append(c)
            if dur / self.fps >= min_sec and len(seq) - len(set(seq)) >= 2:
                out.append((round(i / self.fps, 2), round(dur / self.fps, 2), list(dict.fromkeys(seq))))
            i += dur; p = q
        return out

    def idle(self, pic, amp=0.012, rigid=False, per=14, salt='idle'):
        """The cheapest live hold: a little movement while one cell holds. -> parameter dict for place_at.
        Soft materials (clay, felt, fabric): breathing sy = 1 +- amp, sx = 1/sqrt(sy) (volume kept);
        rigid materials (wood, tin, cardboard; style.json preset.rigid = true): nothing (rotation or sideways shift
        reads as rocking); holds rely on environment and camera. Period per drawings, phase offset by salt (each
        character uses its own salt)."""
        ph = self._rng(0, salt).random() * 2 * math.pi
        w = math.sin(2 * math.pi * pic / max(2, per) + ph)
        if rigid: return {}
        sy = 1 + amp * w
        return dict(sy=sy, sx=1 / math.sqrt(sy))

    def carry(self, last, d, period=None):
        """Let a shot carry on: (cell, frames, state) for the d-th drawing after its last drawing last (d = 0 is the
        cut drawing). Used by mix(live=True) dissolves. Cells continue the last cycle (search back for a cell with the
        last drawing's name to get the cycle length; no cycle -> hold the last cell); numeric state (x, y, lift...)
        is extrapolated from the last two drawings (a walk keeps walking). For another continuation give the shot
        carry=f(d) -> (cell, state) in SHOTS."""
        pics = self.pics
        cell, holds, st = pics[last]
        if period is None:
            period = next((p for p in range(1, min(16, last) + 1) if pics[last - p][0] == cell), 0)
        if period: cell = pics[last - period + 1 + (d % period)][0]
        prev = pics[last - 1][2] if last > 0 else st
        num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
        out = {k: (v + (v - prev[k]) * (d + 1) if num(v) and num(prev.get(k)) else v) for k, v in st.items()}
        return cell, holds, out

    def jrot(self, pic, amp=0.7, salt='rot'):
        """Per-drawing small rotation jitter (degrees): cardboard and wooden puppets set down a little crooked each drawing. preset.jitter_rot"""
        return self.jitter(pic, amp, 1, salt)

    def seed(self, pic, salt='grain'):
        """Per-drawing integer seed: for kit.grade(seed=...) grain and random fx shapes (boil)"""
        return int(self._rng(pic, salt).integers(0, 2 ** 31 - 1))


# =====================================================================================
# Checks
# =====================================================================================

# ---------------------------------------------------------------- occlusion self-check
def sandwich_check(A_obj, occ, th=0.5, frac=0.2):
    """Occluder sandwich check. A_obj: the object's alpha in frame coords (HxW, 0-1); occ: occluder alpha (same size).
    Scan each row of the object left to right; record "visible -> narrow occluded band -> visible" (band narrower
    than the row width x frac). Returns the bad row numbers; empty = pass. A long train showing at both ends with a
    wide middle section hidden is fine."""
    bad = []
    rows = np.nonzero((A_obj > th).any(1))[0]
    for y in rows:
        xs = np.nonzero(A_obj[y] > th)[0]
        v = (occ[y, xs] < 0.5).astype(np.int8)          # 1 = visible
        if v.size < 3:
            continue
        seg = np.split(v, np.flatnonzero(np.diff(v)) + 1)
        width = len(xs)
        for a, b, c in zip(seg, seg[1:], seg[2:]):
            if a[0] == 1 and b[0] == 0 and c[0] == 1 and len(b) < frac * width:
                bad.append(int(y)); break
    return bad


def occ_overlay(bg, occ, out, color=(1.0, 0.1, 0.1), k=0.55):
    """Paint the occlusion mask semi-transparent red over the background and save; check that red covers only the occluder's front edge."""
    bg = _load_rgb(bg) if not isinstance(bg, np.ndarray) else bg
    m = np.clip(occ, 0, 1)[..., None] * k
    img = bg * (1 - m) + np.array(color, np.float32) * m
    kit.wr(out, img)
    return out


# ---------------------------------------------------------------- film liveness
def liveness(video, step=2, thr=10, scale=240, quiet_area=0.008, quiet_len=2.0, out=None):
    """Measure whether enough of the frame moves: compare consecutive drawings (one every step frames), scaled to
    scale wide and blurred; the share of pixels whose brightness changes > thr/255 = that drawing's active area
    (+-1-2 px stop-motion jitter mostly vanishes at that scale).
    -> dict(times, area, quiet=[(start s, duration s, mean active area)], median).
    quiet: stretches where the active area stays below quiet_area for more than quiet_len seconds (only a tiny part
    moves, or nothing). quiet_len defaults to 2 s, the same limit as a held drawing (Timesheet.lint): a 1-2 s hold
    after de-jitter is normal and is not reported. out=path: draw a timeline image (red = dead stretches)."""
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    prev, times, area, i = None, [], [], 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i % step == 0:
            h, w = fr.shape[:2]; sm = cv2.resize(fr, (scale, max(2, int(h * scale / w))), interpolation=cv2.INTER_AREA)
            g = cv2.GaussianBlur(cv2.cvtColor(sm, cv2.COLOR_BGR2GRAY).astype(np.float32), (0, 0), 1.0)
            if prev is not None:
                area.append(float((np.abs(g - prev) > thr).mean())); times.append(i / fps)
            prev = g
        i += 1
    cap.release()
    # rolling 75th percentile over ~1 s: a stretch counts as alive when at least a quarter of its drawings change
    # (motion on threes / fours and short holds stay alive); a single spike such as a cut does not hide a dead stretch
    nwin = max(1, int(round(1.0 * fps / step)))
    sm_area = [float(np.percentile(area[max(0, j - nwin // 2): j + nwin // 2 + 1], 75)) for j in range(len(area))]
    quiet, j = [], 0
    while j < len(area):
        if sm_area[j] < quiet_area:
            k = j
            while k < len(area) and sm_area[k] < quiet_area: k += 1
            t0 = times[j] - step / fps; dur = (k - j) * step / fps
            if dur >= quiet_len: quiet.append((round(t0, 2), round(dur, 2), round(float(np.mean(area[j:k])), 4)))
            j = k
        else: j += 1
    res = dict(times=times, area=area, quiet=quiet, median=float(np.median(area)) if area else 0.0, fps=fps)
    if out and area:
        Wd, Hd, pad = 1200, 260, 30
        img = np.full((Hd, Wd, 3), 255, np.uint8)
        T = times[-1] + step / fps; top = max(0.15, max(area))
        X = lambda t: int(pad + (Wd - 2 * pad) * t / T); Y = lambda a: int(Hd - pad - (Hd - 2 * pad) * min(a, top) / top)
        for t0, d, _ in quiet: cv2.rectangle(img, (X(t0), pad), (X(t0 + d), Hd - pad), (200, 200, 255), -1)
        cv2.line(img, (pad, Y(quiet_area)), (Wd - pad, Y(quiet_area)), (0, 0, 220), 1)
        pts = np.array([(X(t), Y(a)) for t, a in zip(times, area)], np.int32)
        cv2.polylines(img, [pts], False, (40, 40, 40), 2)
        for s_ in range(int(T) + 1):
            cv2.line(img, (X(s_), Hd - pad), (X(s_), Hd - pad + 5), (0, 0, 0), 1)
            cv2.putText(img, f'{s_}s', (X(s_) - 8, Hd - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        cv2.putText(img, f'active area per pic (median {res["median"]:.3f}); red = quiet < {quiet_area}', (pad, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        d = os.path.dirname(out)
        if d: os.makedirs(d, exist_ok=True)
        cv2.imwrite(out, img)
    return res


# =====================================================================================
# Camera: shots, shot sizes, push / pull / pan
# =====================================================================================
SIZES = {'landscape': (1920, 1080), 'portrait': (1080, 1920), 'square': (1080, 1080)}
SIZE_ALIASES = {'横屏': 'landscape', '竖屏': 'portrait', '方形': 'square', '横': 'landscape', '竖': 'portrait', '方': 'square',
                'horizontal': 'landscape', 'vertical': 'portrait', '16:9': 'landscape', '9:16': 'portrait', '1:1': 'square'}
SIZES.update({k: SIZES[v] for k, v in SIZE_ALIASES.items()})       # Chinese aliases also work: animi.SIZES['横屏']


def norm_frame(size):
    """Frame format -> 'landscape' | 'portrait' | 'square' (accepts the old 横屏 / 竖屏 / 方形). Unknown values pass through."""
    s = str(size or '').strip()
    return SIZE_ALIASES.get(s, SIZE_ALIASES.get(s.lower(), s.lower() if s.lower() in ('landscape', 'portrait', 'square') else s))


# Shot sizes (SHOTS size=) and camera directions (view=). Code works in English; Chinese values are aliases.
SHOT_SIZES = ('extreme-wide', 'wide', 'medium', 'medium-close', 'close-up')
_SHOT_ALIASES = {'远景': 'extreme-wide', '全景': 'wide', '中景': 'medium', '近景': 'medium-close', '特写': 'close-up',
                 'extreme wide': 'extreme-wide', 'extremewide': 'extreme-wide', 'xws': 'extreme-wide', 'ews': 'extreme-wide',
                 'ws': 'wide', 'full': 'wide', 'ms': 'medium', 'mid': 'medium', 'medium close': 'medium-close',
                 'medium close-up': 'medium-close', 'medium-close-up': 'medium-close', 'mcu': 'medium-close',
                 'close up': 'close-up', 'closeup': 'close-up', 'close': 'close-up', 'cu': 'close-up'}
VIEWS = ('front', 'side', 'left', 'right', 'reverse', 'top', 'low')
_VIEW_ALIASES = {'正面': 'front', '侧面': 'side', '左侧': 'left', '右侧': 'right', '反打': 'reverse', '俯': 'top', '低': 'low',
                 '左': 'left', '右': 'right', '俯拍': 'top', '俯视': 'top', '低机位': 'low', '仰拍': 'low'}


def norm_size(size):
    """Shot size -> one of SHOT_SIZES ('extreme-wide' 'wide' 'medium' 'medium-close' 'close-up'); the Chinese
    远景 / 全景 / 中景 / 近景 / 特写 map to them. None / '' -> None; unknown values pass through unchanged."""
    if size is None: return None
    s = str(size).strip()
    if not s: return None
    if s in _SHOT_ALIASES: return _SHOT_ALIASES[s]
    low = s.lower().replace('_', '-')
    if low in SHOT_SIZES: return low
    return _SHOT_ALIASES.get(low, _SHOT_ALIASES.get(low.replace('-', ' '), s))


def norm_view(view):
    """Camera direction (view=): free text; the recognised words (front side left right reverse top low and the
    Chinese 正面 侧面 左侧 右侧 反打 俯 低) are normalised to English. None / '' -> None."""
    if view is None: return None
    v = str(view).strip()
    if not v: return None
    if v in _VIEW_ALIASES: return _VIEW_ALIASES[v]
    return v.lower() if v.lower() in VIEWS else v


def _norm_shots(shots):
    """Shallow copies of SHOTS with size / view normalised (the caller's list is not changed)."""
    out = []
    for sh in shots:
        d = dict(sh)
        if 'size' in d: d['size'] = norm_size(d['size'])
        if 'view' in d: d['view'] = norm_view(d['view'])
        out.append(d)
    return out


class _SizeDict(dict):
    """dict keyed by shot size that also accepts the Chinese keys (MIN_HERO['全景'] == MIN_HERO['wide'])."""
    def __getitem__(self, k): return dict.__getitem__(self, norm_size(k))
    def get(self, k, default=None): return dict.get(self, norm_size(k), default)
    def __contains__(self, k): return dict.__contains__(self, norm_size(k))


class Cam:
    """Virtual camera (stepped per drawing, follows on-twos). World coords = stage coords; the stage defaults to the
    film size (SW x SH = W x H). cx, cy: the stage point at the frame centre; zoom: 1 = stage exactly fills the
    frame, 1.12 = pushed in 12%. par: layer parallax (far 0.3, mid 0.9, characters 1, foreground 1.5): within one
    shot far layers move and push less.
        x, y = cam.xy(char_x, foot_y)          stage -> frame coords
        s    = char_scale * cam.k()            sprite scale follows the camera
        bg   = cam.plate(background)           frame the background straight from the original (one resample, no shrink-then-enlarge)
    Keep pushes small (zoom <= 1.15): generated backgrounds are only 1600-1900 px wide and blur when pushed further.
    Change shot size (wide -> medium-close) by cutting to another shot with another background generated for that
    size, not by pushing (see SHOTS and shot_at)."""
    def __init__(self, W, H, cx=None, cy=None, zoom=1.0, SW=None, SH=None):
        self.W, self.H = int(W), int(H)
        self.SW, self.SH = float(SW or W), float(SH or H)
        self.cx = self.SW / 2 if cx is None else float(cx)
        self.cy = self.SH / 2 if cy is None else float(cy)
        self.zoom = float(zoom)
        self.k0 = max(self.W / self.SW, self.H / self.SH)

    def _c(self, par):
        return (self.SW / 2 + (self.cx - self.SW / 2) * par, self.SH / 2 + (self.cy - self.SH / 2) * par,
                (1 + (self.zoom - 1) * par) * self.k0)

    def k(self, par=1.0):
        """How many frame px one stage px is (multiply sprite scale by it)"""
        return self._c(par)[2]

    def xy(self, x, y, par=1.0):
        ccx, ccy, z = self._c(par)
        return (x - ccx) * z + self.W / 2, (y - ccy) * z + self.H / 2

    def plate(self, img, par=1.0, rect=None):
        """Frame a background with the camera into W x H. rect=(x0, y0, x1, y1): where this image lies on the stage
        (default the whole stage). For an extra-wide panning background, widen the stage (SW) and let rect cover it."""
        h, w = img.shape[:2]
        x0, y0, x1, y1 = rect or (0, 0, self.SW, self.SH)
        ccx, ccy, z = self._c(par)
        sx, sy = (x1 - x0) / w * z, (y1 - y0) / h * z
        tx, ty = (x0 - ccx) * z + self.W / 2, (y0 - ccy) * z + self.H / 2
        src = np.ascontiguousarray(img)
        if sx < 0.9 and sy < 0.9:                      # large reductions: INTER_AREA first to avoid aliasing
            nw, nh = max(2, int(round(w * sx))), max(2, int(round(h * sy)))
            src = cv2.resize(src, (nw, nh), interpolation=cv2.INTER_AREA)
            sx, sy = sx * w / nw, sy * h / nh
        M = np.array([[sx, 0, tx], [0, sy, ty]], np.float64)
        flag = cv2.INTER_CUBIC if max(sx, sy) > 1.02 else cv2.INTER_LINEAR
        out = cv2.warpAffine(src, M, (self.W, self.H), flags=flag, borderMode=cv2.BORDER_REPLICATE)
        return np.clip(out, 0, 1) if out.dtype != np.uint8 else out

    def clamp(self, rect=None):
        """Keep the camera inside the stage (or rect), so nothing outside the background shows"""
        x0, y0, x1, y1 = rect or (0, 0, self.SW, self.SH)
        z = max(self.zoom, 1.0) * self.k0
        hw, hh = self.W / 2 / z, self.H / 2 / z
        self.cx = float(np.clip(self.cx, x0 + hw, max(x0 + hw, x1 - hw)))
        self.cy = float(np.clip(self.cy, y0 + hh, max(y0 + hh, y1 - hh)))
        return self


def shot_at(shots, pic):
    """SHOTS = [dict(at=first drawing, size='wide'|'medium'|'medium-close'|'close-up', name=..., cam=[(drawing in shot,
    cx, cy, zoom), ...]), ...] -> (shot, shot index, drawing within the shot). Shots are joined by hard cuts."""
    i = 0
    for j, sh in enumerate(shots):
        if pic >= sh['at']: i = j
    return shots[i], i, pic - shots[i]['at']


def cam_at(shots, pic, W, H, SW=None, SH=None):
    """Camera for this drawing: eased interpolation between the shot's cam keys (stepped per drawing); parts beyond the stage are pulled back. -> (Cam, shot)"""
    sh, _, k = shot_at(shots, pic)
    SW = sh.get('SW', SW); SH = sh.get('SH', SH)
    keys = sh.get('cam') or [(0, None, None, 1.0)]
    keys = sorted(keys, key=lambda q: q[0])
    a = keys[0]; b = keys[-1]
    for q0, q1 in zip(keys, keys[1:]):
        if q0[0] <= k <= q1[0]: a, b = q0, q1; break
    if k >= keys[-1][0]: a = b = keys[-1]
    t = 0.0 if b[0] == a[0] else kit.ease((k - a[0]) / (b[0] - a[0]))
    def L(u, v, dflt):
        u = dflt if u is None else u; v = dflt if v is None else v
        return u + (v - u) * t
    sw, shh = float(SW or W), float(SH or H)
    c = Cam(W, H, L(a[1], b[1], sw / 2), L(a[2], b[2], shh / 2), L(a[3], b[3], 1.0), SW, SH)
    return c.clamp(sh.get('rect')), sh


def plate_similarity(a, b):
    """How alike two backgrounds are (0-1): is one a push-in / pan of the other. Scale the smaller one down by
    several factors and find the best match in the larger (greyscale, normalised correlation). >= 0.75 is basically
    the same camera position: a hard cut between them is a jump cut."""
    def g(x):
        x = np.asarray(x, np.float32)
        if x.ndim == 3: x = x[..., :3].mean(2)
        if x.max() > 1.5: x = x / 255.0
        h, w = x.shape; W_ = 240
        return cv2.GaussianBlur(cv2.resize(x, (W_, max(8, int(W_ * h / w))), interpolation=cv2.INTER_AREA), (0, 0), 1.0)
    A, B = g(a), g(b); best = -1.0
    for P, Q in ((A, B), (B, A)):
        for sc in (1.0, 1.15, 1.3, 1.5, 1.75, 2.0, 2.4):
            w, h = int(Q.shape[1] * P.shape[1] / Q.shape[1] / sc), int(Q.shape[0] * P.shape[1] / Q.shape[1] / sc)
            if w < 40 or h < 20 or h > P.shape[0] or w > P.shape[1]: continue
            q = cv2.resize(Q, (w, h), interpolation=cv2.INTER_AREA)
            best = max(best, float(cv2.matchTemplate(P, q, cv2.TM_CCOEFF_NORMED).max()))
    return best


# Minimum hero height per shot size (share of the frame's short side). A hero that is too small is the most common
# reason a film looks bad: the audience cannot read the acting
MIN_HERO = _SizeDict({'extreme-wide': 0.15, 'wide': 0.30, 'medium': 0.40, 'medium-close': 0.60, 'close-up': 0.0})
KEY_WIDE = 0.33                     # wide shots at the opening and the landing
NOMINAL_HERO = _SizeDict({'extreme-wide': 0.18, 'wide': 0.35, 'medium': 0.50, 'medium-close': 0.75, 'close-up': 1.10})   # size-gap estimate when not measured
COVER_KEYS = ('mix', 'smear', 'tr')  # these transitions cover the cut: no jump-cut comparison


def cell_base(name):
    """Cell name without suffixes -> the real cell. Convention: "@..." gives a position or state ('walk_3@120' just
    tells lint it is moving), "~..." a variant of the same cell ('close_1~b': a small change in a live hold),
    "a+b" several cells in one frame (take the first)."""
    return str(name).split('+')[0].split('@')[0].split('~')[0]


def hero_need(shots, j, style=None):
    """Minimum hero height for shot j (share of the short side).
    Rules: MIN_HERO by shot size; at the opening (first shot) and the landing (last shot, or a shot with key=True) a
    wide shot needs >= KEY_WIDE; the style's flags.hero_min_scale: a number applies only to wide and extreme-wide; a
    dict applies per size ({'extreme-wide': 0.8}, Chinese keys also accepted), medium-close is never reduced;
    a shot's own min wins (checked by eye, on purpose)."""
    sh = shots[j]; size = norm_size(sh.get('size'))
    if sh.get('min') is not None: return float(sh['min'])
    need = MIN_HERO.get(size, 0.0)
    if size == 'wide' and (j == 0 or j == len(shots) - 1 or sh.get('key')): need = max(need, KEY_WIDE)
    hs = ((style or {}).get('flags') or {}).get('hero_min_scale')
    if isinstance(hs, dict):
        hs = {norm_size(k): v for k, v in hs.items()}
        if size != 'medium-close': need *= float(hs.get(size, 1.0))
    elif hs and size in ('wide', 'extreme-wide'):
        need *= float(hs)
    return need


def hero_report(shots, heights, short, style=None, quiet=False):
    """Hero size check. heights: {drawing: hero bbox height px} (0 or missing = no hero in that drawing); shots are
    split by shots[j]['at']. -> (list of shots too small, {shot: median hero height px})"""
    bad, med = [], {}
    last = max(heights) + 1 if heights else 0
    for j, sh in enumerate(shots):
        end = shots[j + 1]['at'] if j + 1 < len(shots) else last
        hs = [heights[p] for p in heights if sh['at'] <= p < end and heights[p] > 0]
        if not hs: continue
        med[j] = float(np.median(hs))
        r = med[j] / short; need = hero_need(shots, j, style)
        ok = r >= need - 1e-6
        if not quiet:
            print(f'hero size: shot {j} "{sh.get("name", "")}" {norm_size(sh.get("size"))} fills {r:.1%} of the short side '
                  f'(needs >= {need:.1%})' + ('' if ok else '  <- too small'), file=sys.stderr)
        if not ok: bad.append(j)
    return bad, med


SIZE_ORDER = list(SHOT_SIZES)


def size_report(shots, ts, heights, med=None, same_gap=1.3, swap_jump=0.2, quiet=False, notes=None):
    """Check that hero size matches across cuts (board / full render, with measured hero heights).
    heights: {drawing: hero bbox height px}; med: {shot: median hero height px} (second return of hero_report; computed when missing).
    1) Two adjacent shots with the same size (both medium) whose hero heights differ by more than same_gap x: the
       character seems to grow or shrink at the cut.
    2) Size gets tighter (medium -> medium-close) but the hero does not get bigger (or looser but bigger): the size is
       mislabelled or the scale is wrong.
    For these two, size_ok='reason' on the shot (checked by eye, on purpose, e.g. walking towards camera) lists them as checked.
    3) Note (not a failure): within one shot, at the switch to another sheet (another pose sheet / close-up sheet),
       hero height jumps by more than swap_jump. Crouching, jumping, lying down change height anyway: compare two
       stills around the switch; if a standing pose also jumps, that sheet was not sized with scale_ref.
    -> list of problems (empty = pass)"""
    bad, info = [], []
    fps = ts.fps
    t_of = lambda p: ts.pic_start(min(p, ts.n_pics)) / fps
    if med is None: _, med = hero_report(shots, heights, 1, quiet=True)
    shots = _norm_shots(shots)
    rank = lambda j: SIZE_ORDER.index(shots[j].get('size')) if shots[j].get('size') in SIZE_ORDER else None
    for j in range(1, len(shots)):
        if j - 1 not in med or j not in med: continue
        a, b = med[j - 1], med[j]; ra, rb = rank(j - 1), rank(j)
        where = f'shot {j - 1}->{j} ({t_of(shots[j]["at"]):.1f}s)'
        msg = None
        if ra is not None and ra == rb and max(a, b) / max(1e-6, min(a, b)) > same_gap:
            msg = (f'{where} both {shots[j].get("size")}, hero height {a:.0f} -> {b:.0f} px, {max(a, b) / min(a, b):.2f}x apart: '
                   'the character seems to change size at the cut. Align with the same HERO_H x shot k, or give one of them another size')
        elif ra is not None and rb is not None and ra != rb and (rb - ra) * (b - a) <= 0:
            msg = (f'{where} cuts from {shots[j - 1].get("size")} to {shots[j].get("size")}, but hero height goes {a:.0f} -> {b:.0f} px: '
                   'a tighter size needs a bigger hero (looser, smaller). Check this shot\'s k and size')
        if not msg: continue
        if shots[j].get('size_ok'): info.append(f'{msg.split(":")[0]}: checked by eye ({shots[j]["size_ok"]})')
        else: bad.append(msg + '; if intended, write size_ok="reason"')
    for p in range(1, ts.n_pics):
        if _shot_at(shots, p) != _shot_at(shots, p - 1): continue
        if sheet_of(ts.pics[p][0]) == sheet_of(ts.pics[p - 1][0]): continue
        h0, h1 = heights.get(p - 1, 0), heights.get(p, 0)
        if h0 > 0 and h1 > 0 and abs(h1 - h0) / min(h0, h1) > swap_jump:
            info.append(f'note: {t_of(p):.1f}s sheet switch {cell_base(ts.pics[p - 1][0])} -> {cell_base(ts.pics[p][0])}, hero height '
                        f'{h0:.0f} -> {h1:.0f} px (jump {abs(h1 - h0) / min(h0, h1):.0%}). Fine if the pose really changes (crouch, jump); '
                        'if a standing pose also jumps, the sheet was not sized with scale_ref. Render the two stills and compare')
    if notes is not None: notes.extend(info)
    if not quiet:
        for m in info: print(f'size_report: {m}', file=sys.stderr)
        for m in bad: print(f'size_report: {m}', file=sys.stderr)
        if not bad: print('size_report: OK (hero size matches across adjacent shots)', file=sys.stderr)
    return bad

def hero_box(box, info, scale=None, at=None):
    """Convert a cell's character-only bbox (info['body'] = [x0, y0, x1, y1], cell coords, see set_body) into the
    frame using the frame bbox returned by place_at; returns box unchanged when there is no body. Large held props
    and hands holding the character do not count towards hero size.
    Top-down / diagonally walking characters (info has core, see set_core): with scale (cell -> frame) and at (core
    centre in the frame), returns a square centred on at with side = body long axis x scale (measures body length,
    not the bbox that grows when turned)."""
    if isinstance(info, dict) and info.get('core') and scale is not None and at is not None and box is not None:
        L = info['core']['len'] * scale / 2
        return (at[0] - L, at[1] - L, at[0] + L, at[1] + L)
    b = info.get('body') if isinstance(info, dict) else None
    if not b or box is None: return box
    x0, y0, x1, y1 = info['bbox']; X0, Y0, X1, Y1 = box
    kx = (X1 - X0) / max(1e-6, x1 - x0); ky = (Y1 - Y0) / max(1e-6, y1 - y0)
    return (X0 + (b[0] - x0) * kx, Y0 + (b[1] - y0) * ky, X0 + (b[2] - x0) * kx, Y0 + (b[3] - y0) * ky)


def set_body(info, c, drop):
    """Record the character-only bbox in a cell's anchor dict (info['body']).
    drop: what to exclude: an (r, g, b) colour (pixels within 0.18 count as prop), a cell-sized 0/1 mask, or f(I, a) -> mask."""
    I, a, _ = c
    if callable(drop): m = drop(I, a)
    elif np.ndim(drop) == 1 and len(drop) == 3: m = np.linalg.norm(I - np.array(drop, np.float32), axis=2) < 0.18
    else: m = np.asarray(drop) > 0.5
    body = (a > 0.5) & ~m
    if body.any():
        ys, xs = np.nonzero(body); info['body'] = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    return info


def _hero_ratio(shots, j, hero):
    if hero and j in hero: return hero[j]
    sh = shots[j]
    if sh.get('hero_h'): return float(sh['hero_h'])
    return None


def _size_gap(shots, j, hero=None):
    """Hero size ratio across shots j-1 and j (measured if available; else k when both shots give k; else estimated by shot size)"""
    a, b = _hero_ratio(shots, j - 1, hero), _hero_ratio(shots, j, hero)
    if a and b: return max(a, b) / max(1e-6, min(a, b)), 'measured'
    ka, kb = shots[j - 1].get('k'), shots[j].get('k')
    if ka and kb: return max(ka, kb) / max(1e-6, min(ka, kb)), 'k'
    na, nb = NOMINAL_HERO.get(shots[j - 1].get('size')), NOMINAL_HERO.get(shots[j].get('size'))
    if na and nb: return max(na, nb) / min(na, nb), 'shot size'
    return 1.0, '?'


def _covered(shots, j):
    """Is the cut at the start of shot j covered by a transition (dissolve, smear, style transition, fade / wipe)"""
    sh, pv = shots[j], shots[j - 1]
    return any(sh.get(k) for k in COVER_KEYS) or bool(sh.get('inn')) or bool(pv.get('out'))


def _zoom_cuts(shots, t_of, hero, info, total):
    """Zoom cuts and in-and-out runs (see shots_lint). place / view are the shot list's "which place" and "from which direction"."""
    bad = []
    shots = _norm_shots(shots)
    if total > 8 and len(shots) > 1 and not any(sh.get('place') for sh in shots):
        return ['the shot list has no place (which place) or view (from which direction): cannot check for zoom cuts '
                '(same place, only the size changes). Give every shot place= and view= (front / left / right / reverse / '
                'top / low); the camera direction must match the background image']
    for j in range(1, len(shots)):
        a, b = shots[j - 1], shots[j]
        if not a.get('place') or a.get('place') != b.get('place'): continue
        if a.get('view') and b.get('view') and a['view'] != b['view']: continue
        where = f'shot {j - 1}->{j} ({t_of(b["at"]):.1f}s, {a.get("size") or "?"}->{b.get("size") or "?"})'
        if b.get('cut_ok'): info.append(f'{where} same place, same direction: checked by eye ({b["cut_ok"]})'); continue
        if _covered(shots, j): info.append(f'{where} same place, same direction: cut covered by a transition'); continue
        gap, how = _size_gap(shots, j, hero)
        close = 'close-up' in (a.get('size'), b.get('size'))
        if close and gap >= 2.0: continue
        if close:
            bad.append(f'{where} marked close-up, but the hero is only {gap:.1f}x bigger ({how}): not a real close-up, reads '
                       'as the camera lurching forward. A close-up fills the frame with one detail (face, the flower curled in '
                       'a trunk, the thing in a hand), hero size at least 2x apart; if no detail is needed, do not cut, keep acting in the shot')
        elif gap < 1.15:
            bad.append(f'{where} same place "{a["place"]}", same direction, same hero size: the cut barely changes the frame. '
                       'Merge into one shot, or really change direction')
        else:
            bad.append(f'{where} same place "{a["place"]}", same direction (view={a.get("view") or "not set"}), hard cut only '
                       f'changes size ({gap:.1f}x, {how}): reads as the picture zooming. If it is not a close-up, do not cut; keep '
                       'acting in the shot (push in slowly for closer); to cut, really change direction (side, reverse: background '
                       'regenerated, staging changed with it), or go straight to a close-up')
    run, prev = [], None
    for j, sh in enumerate(shots + [{}]):
        if sh.get('place') and sh.get('place') == prev: run.append(j)
        else:
            sz = [shots[k].get('size') for k in run if shots[k].get('size') != 'close-up']
            n = sum(1 for x, y in zip(sz, sz[1:]) if x != y)
            if n >= 3: bad.append(f'shots {run[0]}-{run[-1]} are all at "{prev}" and the size changes {n} times '
                                  f'({"->".join(str(x) for x in sz)}): going in and out in one place reads as zooming. '
                                  'Merge shots and play the scene in one')
            run = [j]
        prev = sh.get('place')
    return bad


def shots_lint(shots, ts, quiet=False, plates=None, sim=0.75, hero=None, notes=None, push_max=None):
    """Check the shot design: no shots for their own sake, no sizes for variety; only checks that cuts are right.
    Zoom cut: two adjacent shots at the same place (same place) and the same camera direction (same view, or not
    set); the hard cut only changes size and reads as the picture zooming. In one place only two cuts count: change
    camera direction (different view: front / side / reverse / top / low), or go straight to a real close-up
    (size='close-up', hero size at least 2x apart). Non-close-up shots in one place changing size 3+ times
    (wide->medium->medium-close->medium...) are reported too: going in and out.
    A single shot over 10 s with a static camera is reported (14 s if it moves); at most 2 extreme-wide shots, and
    never the opening or the landing.
    Jump cut: adjacent shots with the same background, or two almost identical backgrounds (compared with
    plate_similarity when plates is given, >= sim), are reported.
    Not compared: hero size 1.5x or more apart (hero = {shot: hero height px}, passed by board / full render; else
    estimated from k or shot size), cuts covered by a transition (mix / smear / tr / inn / out), shots with
    cut_ok='looked at the cut stills: ...' (listed as checked, not a failure).
    The same background reused non-adjacently: note only (make sure returning to the place is intended).
    notes: pass a list to receive the notes and checked items too.
    push_max: in-shot push limit (the style's preset.push_max): a cam zoom above it is reported; intended ones (an
    opening pull-out) write push_ok='reason'.
    Sizes are 'extreme-wide' 'wide' 'medium' 'medium-close' 'close-up' (Chinese aliases are accepted).
    -> list of problems (empty = pass)"""
    fps = ts.fps
    bad, info = [], []
    shots = _norm_shots(shots)
    t_of = lambda p: ts.pic_start(min(p, ts.n_pics)) / fps
    total = ts.duration()
    sizes = {sh.get('size') or '?' for sh in shots}
    if total > 20 and len(shots) < 2:
        info.append(f'note: {total:.1f} s with only 1 shot. Cut when the story changes place, a detail must be seen '
                    '(close-up) or a reaction shown; never cut just to have more shots')
    far = [j for j, sh in enumerate(shots) if sh.get('size') == 'extreme-wide']
    if len(far) > 2: bad.append(f'{len(far)} extreme-wide shots (shots {far}): extreme-wide only shows route and setting, at most 2 per film')
    for j in far:
        if j in (0, len(shots) - 1):
            bad.append(f'shot {j} "{shots[j].get("name", "")}" is extreme-wide: the opening and the landing need wide or tighter (hero readable)')
    for j in range(1, len(shots)):
        a, b = shots[j - 1].get('bg'), shots[j].get('bg')
        same = a is not None and a == b
        r = None
        if not same and plates and a in plates and b in plates:
            r = plate_similarity(plates[a], plates[b])
        if not same and (r is None or r < sim): continue
        where = f'shot {j - 1}->{j} ({t_of(shots[j]["at"]):.1f}s)'
        what = f'same background "{a}"' if same else f'backgrounds "{a}" and "{b}" are almost the same camera position (similarity {r:.2f})'
        gap, how = _size_gap(shots, j, hero)
        if shots[j].get('cut_ok'):
            info.append(f'{where} {what}: checked by eye ({shots[j]["cut_ok"]})'); continue
        if _covered(shots, j):
            info.append(f'{where} {what}: cut covered by a transition, not a jump cut'); continue
        if gap >= 1.5:
            info.append(f'{where} {what}: hero size {gap:.1f}x apart ({how}), sizes far enough apart, not a jump cut'); continue
        if same:
            bad.append(f'{where} {what}: a hard cut at the same angle only changes size and looks like a stutter (jump cut). '
                       'Within one angle change size with an in-shot push; to cut, use a background from a different angle. '
                       'If you checked the cut stills and it is not a jump cut, write cut_ok="reason" on this shot')
        else:
            bad.append(f'{where} {what}, hero size only {gap:.1f}x apart ({how}): the hard cut is a jump cut. Regenerate one '
                       'of them with the angle change written in the prompt ("shot from front left, turned about 40 degrees"); '
                       'if you checked the cut stills and it is not a jump cut, write cut_ok="reason" on this shot')
    bad += _zoom_cuts(shots, t_of, hero, info, total)
    uses = {}
    for j, sh in enumerate(shots):
        if sh.get('bg') is not None: uses.setdefault(sh['bg'], []).append(j)
    for bg, js in uses.items():
        if len(js) > 1 and any(b - a > 1 for a, b in zip(js, js[1:])):
            info.append(f'note: background "{bg}" reused {len(js)} times in shots {js}. Make sure returning to this place is intended; '
                        + ('coming back 3+ times feels repetitive: generate a new one from another wall or angle' if len(js) >= 3
                           else 'props and light must match between the shots'))
    for j, sh in enumerate(shots):
        t0 = t_of(sh['at']); t1 = t_of(shots[j + 1]['at']) if j + 1 < len(shots) else total
        keys = sh.get('cam') or []
        moving = len({tuple(q[1:]) for q in keys}) > 1
        if t1 - t0 > (14 if moving else 10):
            bad.append(f'shot {j} "{sh.get("name", sh.get("size", ""))}" {t0:.1f}-{t1:.1f}s, {t1 - t0:.1f} s'
                       + ('' if moving else ' with a static camera') + ': too long')
    if push_max:
        for j, sh in enumerate(shots):
            zs = [q[3] for q in (sh.get('cam') or []) if len(q) > 3]
            if not zs or max(zs) <= push_max + 1e-6: continue
            what = f'shot {j} "{sh.get("name", "")}" camera zoom reaches {max(zs):.2f}, above the style\'s push limit {push_max}'
            if sh.get('push_ok'): info.append(f'{what}: checked by eye ({sh["push_ok"]})')
            else: bad.append(f'{what}: pushing that close blurs and shows the background edge; use a closer background, or if intended write push_ok="reason"')
    if notes is not None: notes.extend(info)
    if not quiet:
        for m in info: print(f'shots_lint: {m}', file=sys.stderr)
        for m in bad: print(f'shots_lint: {m}', file=sys.stderr)
        if not bad: print(f'shots_lint: OK ({len(shots)} shots, sizes {", ".join(sorted(str(x) for x in sizes))})', file=sys.stderr)
    return bad


def sheet_of(cell):
    """Cell name -> sheet name: 'walk_3~b@120' -> 'walk', 'toss_5+pan_0' -> 'toss'; cells without a number are returned unchanged"""
    return re.sub(r'_\d+$', '', cell_base(cell))


def _shot_at(shots, p):
    j = 0
    while j + 1 < len(shots) and shots[j + 1]['at'] <= p: j += 1
    return j


def repeat_report(shots, ts, max_same=2, max_loop_sec=6.0, flip_cells=3, flip_sec=3.0, quiet=False, notes=None):
    """Check for repeated action (the hero's cells, ts.pics names). A run of one sheet used consecutively inside a
    shot counts as one action:
    1) Replay: a non-looping action (at least 3 distinct cells in order after dedup, e.g. toss_0->1->2->3) appears
       more than max_same times in the film with the exact same cell order: it reads as the same clip played again.
       Fix: vary the timing, the in-betweens or the result (the last held drawing) each time, or generate another
       sheet for the repeat.
    2) Loop too long: a loop (walk, run, swim, flap) cycles more than max_loop_sec seconds in one shot; a small loop
       of flip_cells cells or fewer (two or three cells back and forth: pressing a button, shivering, hopping) more
       than flip_sec seconds. Long loops look mechanical. Fix: insert another action (stop and look back, stumble),
       change the timing (a few faster, a few slower), or cut away.
    Face-only changes (blink, mouth) are '<cell>~b' variants (not a cell change); a separate blink drawing counts as
    back-and-forth. When any drawing in the run has rep_ok='reason' in its state (checked, on purpose, e.g. a
    deliberate running gag, a walk across the whole frame): listed as checked only.
    -> list of problems (empty = pass)"""
    pics, fps = ts.pics, ts.fps
    bad, info = [], []
    runs, p = [], 0                      # [(first drawing, end drawing, sheet, [cell per drawing])]
    while p < len(pics):
        s, j = sheet_of(pics[p][0]), _shot_at(shots, p); q = p
        while q < len(pics) and sheet_of(pics[q][0]) == s and _shot_at(shots, q) == j: q += 1
        runs.append((p, q, s, [cell_base(pics[k][0]) for k in range(p, q)])); p = q
    t_of = lambda p: ts.pic_start(min(p, ts.n_pics)) / fps
    ok_of = lambda a, b: next((pics[k][2]['rep_ok'] for k in range(a, b) if pics[k][2].get('rep_ok')), None)
    plays = {}
    for a, b, s, cells in runs:
        seq = [c for k, c in enumerate(cells) if k == 0 or cells[k - 1] != c]
        laps = seq.count(seq[0])
        if laps >= 2 and len(set(seq)) >= 2:                     # loop: came back to the first cell and went round again
            dur, n = t_of(b) - t_of(a), len(set(seq))
            flip = n <= flip_cells and dur > flip_sec
            if flip or dur > max_loop_sec:
                what = (f'from {t_of(a):.1f}s shot {_shot_at(shots, a)} "{s}" '
                        + (f'has only {n} cells switching back and forth for {dur:.1f} s' if flip else f'loops for {dur:.1f} s ({laps} laps)'))
                ok = ok_of(a, b)
                if ok: info.append(f'{what}: checked by eye ({ok})')
                else: bad.append(f'{what}, looks mechanical: insert another action (stop, look back, stumble), change the timing, '
                                 'or cut away; if intended write rep_ok="reason"')
        elif len(set(seq)) >= 3:
            plays.setdefault(tuple(seq), []).append((a, b))
    for seq, uses in plays.items():
        if len(uses) <= max_same: continue
        where = ', '.join(f'{t_of(a):.1f}s (shot {_shot_at(shots, a)})' for a, _ in uses)
        what = f'the same action {"->".join(seq[:6])}{"..." if len(seq) > 6 else ""} plays {len(uses)} times unchanged: {where}'
        ok = next((o for o in (ok_of(a, b) for a, b in uses) if o), None)
        if ok: info.append(f'{what}: checked by eye ({ok})')
        else: bad.append(f'{what}. Vary the timing, the in-betweens or the last held drawing each time, or generate another '
                         'sheet for the repeat; a deliberate running gag writes rep_ok="reason"')
    if notes is not None: notes.extend(info)
    if not quiet:
        for m in info: print(f'repeat_report: {m}', file=sys.stderr)
        for m in bad: print(f'repeat_report: {m}', file=sys.stderr)
        if not bad: print(f'repeat_report: OK ({len(runs)} actions, no unchanged replays or overlong loops)', file=sys.stderr)
    return bad

def shot_table(shots, ts, fps=None):
    """Shot table (for sound timing per shot, the review page and selfcheck):
    {dur, fps, shots: [{i, t, t1, at, name, size, bg}]}. t / t1 are the shot's start / end seconds, at its first drawing."""
    fps = fps or ts.fps
    total = round(ts.duration(), 3)
    out = []
    for j, sh in enumerate(shots):
        t = ts.pic_start(min(sh['at'], ts.n_pics)) / fps
        t1 = ts.pic_start(min(shots[j + 1]['at'], ts.n_pics)) / fps if j + 1 < len(shots) else total
        out.append(dict(i=j, t=round(t, 3), t1=round(t1, 3), at=int(sh['at']), name=sh.get('name', ''),
                        size=sh.get('size', ''), bg=sh.get('bg', '')))
    return dict(dur=total, fps=fps, shots=out)


def write_shots(path, shots, ts, fps=None):
    """Write shot_table as JSON (creates the folder) -> path"""
    d = os.path.dirname(path)
    if d: os.makedirs(d, exist_ok=True)
    with open(path, 'w') as f: json.dump(shot_table(shots, ts, fps), f, ensure_ascii=False, indent=1)
    return path


# ---------------------------------------------------------------- frame too dark
DARK = dict(frame=0.03, hero=0.06, len=0.3)   # whole-frame mean brightness, mean brightness in the hero bbox (0-1), how long before reporting (s)


def brightness(frame, box=None):
    """-> (whole-frame mean brightness, mean brightness in the hero bbox or None). frame: float RGB 0-1 or uint8 BGR (from video)"""
    f = np.asarray(frame)
    if f.dtype == np.uint8: L = (f[..., 2] * 0.299 + f[..., 1] * 0.587 + f[..., 0] * 0.114) / 255.0
    else: L = _lum(np.clip(f, 0, 1))
    whole = float(L.mean())
    if box is None: return whole, None
    H_, W_ = L.shape
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W_, x1), min(H_, y1)
    if x1 - x0 < 2 or y1 - y0 < 2: return whole, None
    return whole, float(L[y0:y1, x0:x1].mean())


def dark_spans(samples, th=None, quiet=False):
    """samples: [(s, frame brightness, hero brightness or None), ...] (sorted by time).
    Frame < th['frame'] or hero area < th['hero'] for >= th['len'] s in a row -> [(start s, duration s, reason)].
    Dark styles set thresholds in style.json preset.dark (dict(frame=, hero=, len=))."""
    th = dict(DARK, **(th or {}))
    out, run = [], None
    step = (samples[1][0] - samples[0][0]) if len(samples) > 1 else 1 / 12
    for t, fl, hl in list(samples) + [(None, 1.0, 1.0)]:
        dark = t is not None and (fl < th['frame'] or (hl is not None and hl < th['hero']))
        if dark:
            if run is None: run = [t, t, fl, hl if hl is not None else 1.0]
            else: run[1] = t; run[2] = min(run[2], fl); run[3] = min(run[3], hl if hl is not None else 1.0)
        elif run is not None:
            d = run[1] - run[0] + step
            if d >= th['len'] - 1e-6:
                why = []
                if run[2] < th['frame']: why.append(f'frame brightness down to {run[2]:.3f}')
                if run[3] < th['hero']: why.append(f'hero area down to {run[3]:.3f}')
                out.append((round(run[0], 2), round(d, 2), ', '.join(why)))
            run = None
    if not quiet:
        for t0, d, why in out:
            print(f'too dark: from {t0:.2f}s for {d:.2f}s, {why}: hero and action may be invisible (close darkening and light pools towards the light source, keep the hero lit)', file=sys.stderr)
    return out


def darkness(video, hero=None, step=2, th=None, quiet=True):
    """Measure "too dark" on the film: one frame every step. hero: path or dict of work/hero.json (hero bbox per
    drawing, written by film.py during the full render). -> result of dark_spans"""
    boxes = None
    if isinstance(hero, str) and os.path.exists(hero):
        with open(hero) as f: hero = json.load(f)
    if isinstance(hero, dict) and hero.get('boxes'):
        boxes = sorted((float(t), b) for t, b in hero['boxes'])
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    samples, i, k = [], 0, 0
    while True:
        ok, fr = cap.read()
        if not ok: break
        if i % step == 0:
            t = i / fps; box = None
            if boxes:
                while k + 1 < len(boxes) and boxes[k + 1][0] <= t + 1e-6: k += 1
                if boxes[k][0] <= t + 1e-6: box = boxes[k][1]
            samples.append((t,) + brightness(fr, box))
        i += 1
    cap.release()
    return dark_spans(samples, th, quiet)


# =====================================================================================
# Fixed styles (styles/<id>/style.json) and prompt assembly
# =====================================================================================
STYLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'styles')


def style_ids():
    """Ids of the fixed styles (folders under styles/ with a style.json, not starting with _), sorted by style.json num"""
    ids = [d for d in os.listdir(STYLES_DIR) if not d.startswith('_') and os.path.exists(os.path.join(STYLES_DIR, d, 'style.json'))]
    def key(d):
        try: n = float(json.load(open(os.path.join(STYLES_DIR, d, 'style.json'))).get('num') or 1e9)
        except Exception: n = 1e9
        return (n, d)
    return sorted(ids, key=key)


def style_info(sid):
    """Read all of styles/<id>/style.json (menu info, best subjects, sound, narration, subtitles, transitions, preset).
    Chinese keys and values are normalised: best.题材/配色/光线/机位 -> subject/palette/light/camera,
    assets.*.aspect 横/方/竖/按成片画幅 -> landscape/square/portrait/film."""
    p = os.path.join(STYLES_DIR, sid, 'style.json')
    if not os.path.exists(p):
        raise SystemExit(f'no such style: {sid}. Fixed styles: {", ".join(style_ids())}')
    with open(p) as f: return norm_style(json.load(f))


BEST_KEYS = ('subject', 'palette', 'light', 'camera')
_BEST_ALIASES = {'题材': 'subject', '配色': 'palette', '光线': 'light', '机位': 'camera'}
ASSET_ASPECTS = ('landscape', 'square', 'portrait', 'film')
_ASPECT_ALIASES = {'横': 'landscape', '横屏': 'landscape', '方': 'square', '方形': 'square', '竖': 'portrait', '竖屏': 'portrait',
                   '按成片画幅': 'film', '成片': 'film'}


def norm_style(d):
    """style.json dict with Chinese keys / values mapped to English (in place; returns d)."""
    if isinstance(d.get('best'), dict):
        d['best'] = {_BEST_ALIASES.get(k, k): v for k, v in d['best'].items()}
    for a in (d.get('assets') or {}).values() if isinstance(d.get('assets'), dict) else ():
        if isinstance(a, dict) and isinstance(a.get('aspect'), str):
            a['aspect'] = _ASPECT_ALIASES.get(a['aspect'].strip(), a['aspect'].strip())
    return d


STYLE_ZERO = ('jitter_pos', 'jitter_scale', 'jitter_rot', 'flicker')      # 0 in every style: no per-drawing jitter, no whole-frame flicker
STYLE_NEED = ('on', 'rigid', 'idle', 'push_max', 'shadow', 'light', 'grade')


def style_lint(sid):
    """Check a style package's basic settings (one set of rules for every style) -> list of problems (empty = pass):
    preset must have every STYLE_NEED key (light is null when no relighting), STYLE_ZERO and grade.grain must be 0;
    title must be complete: color, plate (shape, color), motion (enter, step, sub_side), sound, so the bookends match
    the style; best has subject / palette / light / camera; assets.*.aspect is landscape / square / portrait / film.
    Chinese keys and values are accepted (see norm_style)."""
    i = style_info(sid); p = i.get('preset') or {}; bad = []
    for k in STYLE_NEED:
        if k not in p: bad.append(f'{sid}: preset is missing {k}')
    for k in STYLE_ZERO:
        if p.get(k, 0) != 0: bad.append(f'{sid}: preset.{k} = {p.get(k)}, must be 0 (no per-drawing jitter, no whole-frame flicker)')
        if k not in p: bad.append(f'{sid}: preset is missing {k} (write 0)')
    if (p.get('grade') or {}).get('grain', 0) != 0: bad.append(f'{sid}: preset.grade.grain must be 0 (no film grain)')
    for k in ('en', 'line_en'):                               # style name and one-liner shown to English users
        if not str(i.get(k) or '').strip() or str(i.get(k)).startswith('<'): bad.append(f'{sid}: missing {k} (English style name / one-line description)')
    best = i.get('best')
    if not isinstance(best, dict): bad.append(f'{sid}: missing best ({" / ".join(BEST_KEYS)})')
    else:
        for k in BEST_KEYS:
            if k not in best: bad.append(f'{sid}: best is missing {k}')
    for name, a in (i.get('assets') or {}).items() if isinstance(i.get('assets'), dict) else ():
        asp = (a or {}).get('aspect') if isinstance(a, dict) else None
        if asp is not None and asp not in ASSET_ASPECTS:
            bad.append(f'{sid}: assets.{name}.aspect = {asp!r}, must be one of {" / ".join(ASSET_ASPECTS)}')
    t = i.get('title') or {}
    if not t: bad.append(f'{sid}: missing title (look of the title and end cards)')
    else:
        for k in ('color', 'plate', 'motion', 'sound'):
            if k not in t: bad.append(f'{sid}: title is missing {k}')
        for k in ('shape', 'color'):
            if k not in (t.get('plate') or {}): bad.append(f'{sid}: title.plate is missing {k}')
        for k in ('enter', 'step', 'sub_side'):
            if k not in (t.get('motion') or {}): bad.append(f'{sid}: title.motion is missing {k}')
    md = os.path.join(STYLES_DIR, sid, 'STYLE.md')
    if os.path.exists(md):                                    # STYLE.md (and style.json text) hold only what the material changes
        txt = open(md, encoding='utf-8').read() + '\n' + json.dumps(i, ensure_ascii=False)
        for pat, what in GENERAL_RULES:
            m = re.search(pat, txt, re.I)
            if m: bad.append(f'{sid}: STYLE.md restates a general rule ({what}): "{m.group(0)}"; it lives in references/, write only this style\'s values')
    return bad


# Rules that are the same for every style (directing.md, sound.md); a style package must not restate or override them.
GENERAL_RULES = [
    (r'\d[\d.]*\s*(?:[–-]\s*\d[\d.]*\s*)?s(?:econds?)? of silence|silence before (?:a|the) (?:turn|twist|last)', 'score silences: sound.md'),
    (r'subtitles? (?:are |is )?always at the bottom|subtitle band', 'subtitle position: directing.md §3'),
    (r'never cut slightly closer|cut (?:reactions? )?to a close-up[^.\n]{0,30}or (?:a )?change (?:of )?view', 'cutting to reactions: directing.md §3'),
    (r'(?:≥\s*|\()3[03]\s*%|\b3[03]\s*% (?:in|for) ', 'hero size: directing.md §3'),
    (r'no per-drawing jitter', 'no jitter: SKILL.md hard rule 6'),
    (r'at most 2 extreme-wides', 'extreme-wides: directing.md §3'),
    (r'mark long holds `?idle=True', 'live holds: directing.md §5'),
]


def style_preset(sid):
    """Read a fixed style's code parameters (style.json preset: jitter, light flicker, grade, in-shot push limit...).
    At the top of film.py: STYLE = animi.style_preset('clay'), then use STYLE['jitter_pos'] etc.; never invent your own."""
    info = style_info(sid)
    return dict(info.get('preset', {}), id=info['id'], name=info['name'], en=info.get('en', info['name']), flags=info.get('flags', {}))


PROMPT_TYPES = ('character', 'sheet8', 'sheet4', 'prop', 'fx', 'bg', 'layer', 'texture')
PROMPT_REF = {'sheet8': 'the character sheet', 'sheet4': 'the character sheet',
              'layer': 'the background of the same scene'}   # reference image to attach when generating
ASPECTS = {'landscape': 'landscape 16:9', 'portrait': 'portrait 9:16', 'square': 'square 1:1'}
# Slot / part / variable names: English snake_case. Chinese names (user slot files) map here as aliases.
SLOT_ALIASES = {'角色': 'character', '动作': 'action', '场景': 'scene', '手上道具': 'held_prop', '道具视角': 'prop_view',
                '景别': 'shot_size', '取景': 'framing', '特效': 'fx', '视角': 'view', '落脚线': 'ground_line',
                '设定图落脚线': 'sheet_ground_line', '道具': 'prop', '表演': 'performance', '材料': 'material',
                '布景层': 'set_layers', '留白': 'margin', '名字': 'name', '画幅': 'aspect'}
_SIZE_PHRASE = {'extreme-wide': 'Extreme wide shot', 'wide': 'Wide shot', 'medium': 'Medium shot',
                'medium-close': 'Medium close-up', 'close-up': 'Close-up'}
_HEADER = re.compile(r'^\s*(?:\[([A-Za-z_][A-Za-z0-9_ -]*)\]|【([^】]+)】)\s*(.*)$')
_VAR = re.compile(r'\{([^{}\s]+)\}')


def slot_name(name):
    """Slot / part / variable name -> canonical English snake_case (Chinese names via SLOT_ALIASES)."""
    n = str(name).strip()
    n = SLOT_ALIASES.get(n, n)
    return re.sub(r'[\s-]+', '_', n).lower() if n.isascii() else n


def parse_slots(text):
    """Slot file (also the format of _parts.txt): each slot starts with a line beginning [name] (ASCII brackets,
    snake_case); text after the header on the same line belongs to the slot, which runs to the next header or the
    end of the file. Old 【名字】 headers still work (Chinese names via SLOT_ALIASES). -> {name: text}"""
    out, cur, buf = {}, None, []
    for line in text.splitlines():
        m = _HEADER.match(line)
        if m:
            if cur is not None: out[cur] = '\n'.join(buf).strip()
            cur, buf = slot_name(m.group(1) or m.group(2)), ([m.group(3)] if m.group(3) else [])
        elif cur is not None: buf.append(line)
    if cur is not None: out[cur] = '\n'.join(buf).strip()
    return out


def prompt_parts(sid):
    """Replaceable parts: _common/_parts.txt holds the defaults; a part with the same name in the style package's
    prompts/_parts.txt replaces it whole (empty = remove it). Same format as a slot file ([name] headers). -> {name: text}"""
    C = os.path.join(STYLES_DIR, '_common', '_parts.txt'); S = os.path.join(STYLES_DIR, sid, 'prompts', '_parts.txt')
    out = parse_slots(open(C).read()) if os.path.exists(C) else {}
    if os.path.exists(S): out.update(parse_slots(open(S).read()))
    return out


def fill_parts(text, sid):
    """Replace each <<name>> in a template with this style's part (prompt_parts); old 〔名字〕 also works"""
    P = prompt_parts(sid)
    def rep(m):
        k = slot_name(m.group(1))
        if k not in P: raise SystemExit(f'{sid}: part <<{k}>> in the template is not defined (_common/_parts.txt or the style package\'s prompts/_parts.txt)')
        return P[k]
    text = re.sub(r'<<\s*([^<>\s]+)\s*>>', rep, text)
    return re.sub(r'〔([^〔〕\s]+)〕', rep, text)


def build_prompt(sid, kind, slots=None, size='landscape'):
    """Assemble an asset's final prompt: style anchor + shared template + this style's notes + shared rules, then fill
    the slots. Missing slots raise an error listing them. size: landscape | portrait | square (old 横屏 | 竖屏 | 方形
    accepted) -> {aspect}. Template syntax: {name} variable, <<name>> replaceable part, [[ ... ]] optional segment
    (kept only if every {name} inside is filled). -> prompt text"""
    if kind not in PROMPT_TYPES: raise SystemExit(f'asset kinds: {", ".join(PROMPT_TYPES)}')
    style_info(sid)
    C = os.path.join(STYLES_DIR, '_common'); S = os.path.join(STYLES_DIR, sid, 'prompts')
    rd = lambda p: open(p).read().strip() if os.path.exists(p) else ''
    parts = [rd(os.path.join(S, 'anchor.txt')), rd(os.path.join(C, kind + '.txt'))]
    extra = rd(os.path.join(S, kind + '.txt'))
    if extra: parts[-1] += '\n' + extra
    parts.append(rd(os.path.join(C, '_rules.txt')))
    text = '\n\n'.join(x for x in parts if x)
    text = fill_parts(text, sid)
    vals = {slot_name(k): v for k, v in (slots or {}).items()}
    ss = norm_size(re.sub(r'[\s.。]+$', '', str(vals.get('shot_size') or '')))
    if ss in _SIZE_PHRASE: vals['shot_size'] = _SIZE_PHRASE[ss]      # a bare size word (wide / 全景) -> prompt wording
    vals.setdefault('_transparent', rd(os.path.join(C, '_transparent.txt')))
    vals.setdefault('aspect', ASPECTS.get(norm_frame(size), size))
    get = lambda k: vals.get(slot_name(k))
    keep = lambda m: m.group(1) if all(get(k) for k in _VAR.findall(m.group(1))) else ''
    # [[ ... ]] is optional: kept only if every slot inside is filled, otherwise dropped whole
    # (e.g. a sheet without [held_prop] drops the held-prop sentence). The old ［…］ form works too.
    text = re.sub(r'\[\[((?:(?!\[\[|\]\]).)*)\]\]', keep, text, flags=re.S)
    text = re.sub(r'［([^［］]*)］', keep, text)
    need = _VAR.findall(text)
    miss = list(dict.fromkeys(slot_name(k) for k in need if not get(k)))
    if miss: raise SystemExit(f'{sid}/{kind}: these slots are empty: {", ".join(miss)} (write [{miss[0]}] ... in the slot file, or --set {miss[0]}=...)')
    return tidy_prompt(_VAR.sub(lambda m: get(m.group(1)), text))


def tidy_prompt(text):
    """Clean up punctuation where a slot's own punctuation meets the template's: '..' ';.' ',.' ' .' -> '.',
    doubled spaces left by dropped optional segments (and the Chinese 。。 ；。 ，。 forms)."""
    text = re.sub(r'[，；、]+。', '。', text)
    text = re.sub(r'([。！？])。+', r'\1', text)
    text = re.sub(r'[ \t]*[;,:]+[ \t]*\.(?!\.)', '.', text)
    text = re.sub(r'(?<!\.)([.!?])[ \t]*\.(?!\.)', r'\1', text)
    text = re.sub(r'[ \t]+([.,;:!?])(?=\s|$)', r'\1', text)
    text = re.sub(r'(?<=\S)[ \t]{2,}', ' ', text)
    return '\n'.join(l.rstrip() for l in text.split('\n'))


_SMEAR = {}


def smear(frame, tex, k, origin=(0.9, 0.95), seed=0, wobble=0.25, edge='round', shadow=(10, 14, 0.38), fit=False):
    """Material smear (transition for material styles: clay, wool, fabric, plasticine): a lump of material smears
    onto the lens from origin (frame-relative coords, may be off-frame), with an irregular edge, thickness shading
    and a cast shadow.
    tex: a frame-filling close-up of the material (generate a big piece with the prop kind, crop the middle), float RGB.
    k: 0 none -> 1 fully covered. Usage: 3-4 drawings before the cut k rises 0.2 -> 1, 1-2 drawings at the cut k = 1
    (only material visible), 3-4 drawings after the cut with another origin (opposite corner) k falls 1 -> 0, as if
    peeled off towards that corner.
    edge: 'round' arc edge radiating from one point (a lump of clay) / 'line' straight sweeping edge (a cloth flung
    in, a finger wiping across).
    shadow=(dx, dy, depth): shadow direction and strength; edge shading follows it (lit edge bright, far edge dark).
    Light from upper left = default (10, 14, 0.38); flat front light (plasticine relief, cut paper shot head-on):
    (0, 5, 0.22): shadow only slightly down and faint, top edge slightly bright; (0, 0, 0) = no shadow or edge shading.
    fit=True: remap k by origin's nearest / farthest distance to the frame (with an off-frame origin the edge enters
    as soon as k > 0). Edits and returns frame."""
    H, W = frame.shape[:2]
    if k <= 0: return frame
    key = (id(tex), W, H, seed, tuple(origin), wobble, edge, bool(fit))
    if key not in _SMEAR:
        T = cv2.resize(tex, (W, H), interpolation=cv2.INTER_AREA) if tex.shape[:2] != (H, W) else tex
        n = np.random.default_rng(seed).random((7, 12)).astype(np.float32)
        n = cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC); n = (n - n.min()) / max(1e-6, n.max() - n.min())
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        ox, oy = origin[0] * W, origin[1] * H
        if edge == 'line':
            vx, vy = W / 2 - ox, H / 2 - oy; L = max(1e-6, math.hypot(vx, vy)); vx, vy = vx / L, vy / L
            d = (xx - ox) * vx + (yy - oy) * vy
            cs = [(cx - ox) * vx + (cy - oy) * vy for cx in (0, W) for cy in (0, H)]
        else:
            d = np.hypot(xx - ox, yy - oy)
            cs = [math.hypot(cx - ox, cy - oy) for cx in (0, W) for cy in (0, H)]
        dmax = max(cs)
        dmin = max(0.0, float(d.min())) if fit else 0.0
        _SMEAR[key] = (T.astype(np.float32), ((d - dmin) / max(1e-6, dmax - dmin) + wobble * (n - 0.5)).astype(np.float32))
    T, f = _SMEAR[key]
    r = k * (1 + wobble)
    m = np.clip((r - f) / 0.004, 0, 1)
    if m.max() <= 0: return frame
    sdx, sdy, sk = shadow
    if sk > 0:
        sh = cv2.GaussianBlur(np.roll(np.roll(m, int(sdy), 0), int(sdx), 1), (0, 0), 9)
        frame *= (1 - sk * sh * (1 - m))[..., None]
    band = np.clip((r - f) / 0.035, 0, 1)                                                # edge band 0 -> inside 1
    mb = cv2.GaussianBlur(m, (0, 0), 6)
    gy, gx = np.gradient(mb)
    if (sdx, sdy) == (10, 14): lit = np.clip(-(gx + gy) * 18, -1, 1)                    # upper-left edges bright, lower-right dark
    else: lit = np.clip(-(gx * sdx + gy * sdy) / (math.hypot(sdx, sdy) or 1.0) * 25, -1, 1)   # lit edge bright, far edge dark
    C = T * (0.82 + 0.18 * band)[..., None] + 0.22 * lit[..., None]
    frame[:] = frame * (1 - m[..., None]) + np.clip(C, 0, 1) * m[..., None]
    return frame


def transition(frame, kind, k, color=(0.0, 0.0, 0.0), center=None, soft=0.04):
    """Generic transitions between shots (style-specific ones are in style.json transitions, made from generated fx sheets).
    k: progress 0 -> 1. kind:
      'iris_out' circle closes (k=1 black) / 'iris_in' circle opens (k=0 black, k=1 open)
      'dip_out' fade to black / 'dip_in' fade up from black
      'wipe_l' / 'wipe_r' / 'wipe_u' / 'wipe_d' soft-edge wipe out (wiped part becomes color; pair with the next shot's wipe_*_in)
      'wipe_l_in' etc.: wipe in from color
    center: circle centre (default frame centre; can target the hero). Edits and returns frame."""
    H, W = frame.shape[:2]; k = float(np.clip(k, 0, 1)); col = np.array(color, np.float32)
    if kind.startswith('iris'):
        cx, cy = center if center is not None else (W / 2, H / 2)
        R = math.hypot(max(cx, W - cx), max(cy, H - cy)) * 1.02
        r = R * ((1 - k) if kind == 'iris_out' else k)
        yy, xx = np.ogrid[:H, :W]
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        m = np.clip((r - d) / max(1.0, soft * min(W, H)) + .5, 0, 1)[..., None]
    elif kind.startswith('dip'):
        m = np.float32(1 - k if kind == 'dip_out' else k)
    elif kind.startswith('wipe'):
        d = kind.split('_')[1]; inn = kind.endswith('_in')
        q = np.linspace(0, 1, W if d in 'lr' else H, dtype=np.float32)
        if d in 'ld': q = 1 - q if d == 'l' else q
        if d == 'u': q = 1 - q
        pos = (k if not inn else 1 - k) * (1 + 2 * soft) - soft
        m1 = np.clip((q - pos) / soft * .5 + .5, 0, 1)
        if inn: m1 = 1 - m1
        m = (m1[None, :, None] if d in 'lr' else m1[:, None, None])
    else:
        raise ValueError(f'no such transition: {kind}')
    frame[...] = frame * m + col * (1 - m)
    return frame


# =====================================================================================
# Style transition family: transitions that cover the cut between shots (drawn before grading, so the transition
# material gets grain and grading with the picture)
# =====================================================================================
# A style package only picks kinds and fills parameters (style.json transitions[i] = {"id", "name", "how", "kind",
# "params"}); SHOTS write tr='<id>' (the style's parameters) or tr=dict(kind=..., before=, after=, ...) (your own).
# The template's draw() does the rest.
#   kind      before/after (drawings)  assets needed                         what it does
#   smear     4 / 5 (incl. hold 1)     tex: frame-filling material close-up   material smear: covers before the cut (origin_in), peels off after (origin_out)
#   page      0 / 6                    -                                      page turn: the new picture slides in from side over the old, soft shadow on the edge
#   slide     7 / 7                    tex: a tall, wide transparent layer    layer sweep: a big paper layer sweeps across; the cut hides in the drawings it covers
#   stitch    0 / 10                   sprite: a stitched fabric edge (opt.)  stitch wipe: a line of stitches sweeps along the wipe edge, new picture behind it
#   curtain   8 / 10                   sprites: cells of a dense fx sheet     curtain: clumps of material (bubbles, snowballs, confetti) surge up across the frame
#   wipe      0 / 6                    -                                      soft-edge wipe (dir = l / r / u / d)
#   glow      8 / 8                    -                                      glow: brightens before the cut, changes scene at the brightest (hold on the brightest drawings; mix=False: no dissolve, hard cut at the brightest)
#   mix       0 / 12                   -                                      dissolve (live=True: the previous shot keeps acting instead of freezing)
#   hinge     5 / 7 (incl. hold 2)     sprite: a transparent board (box lid, door)  hinge flip: the board flips in on a frame edge to cover, then opens (hinge = lr / l / r / t / b)
# Shared parameters: shake (px, the frame shakes during the transition), seed.
# style.json entries that are not transitions between shots (in-shot actions and staging: a paper layer standing up,
# pushing into a field, a reveal hard cut) use "kind": "move" and are done in build() / render() per their how;
# pointing tr= at one gives "this is not a transition".
TR_DEFAULT = {'smear': (4, 5), 'page': (0, 6), 'slide': (7, 7), 'stitch': (0, 10), 'curtain': (8, 10),
              'wipe': (0, 6), 'glow': (8, 8), 'mix': (0, 12), 'hinge': (5, 7)}
TR_NEEDS_OLD = {'page', 'stitch', 'wipe', 'glow', 'mix'}       # need the old shot's picture after the cut (default: its last drawing held)
TR_NOT = ('move',)                                             # entries in transitions that are not transitions between shots
TR_ASSET = ('tex', 'sprite', 'sprites')                        # transition parameter keys that name assets


def tr_item(tr, style=None):
    """The transition entry with id tr in style.json; a readable error when it is missing or not a transition between shots"""
    items = (style or {}).get('transitions', [])
    item = next((t for t in items if t.get('id') == tr), None)
    if item is None:
        ok = [t['id'] for t in items if t.get('kind') in TR_DEFAULT]
        raise ValueError(f'the style has no transition "{tr}" (ids usable with tr=: {", ".join(ok) or "none"})')
    if item.get('kind') not in TR_DEFAULT:
        raise ValueError(f'"{tr}" ({item.get("name", "")}) is not a transition between shots (kind: {item.get("kind")}); do not use tr=: '
                         f'do it in build() / render() per its how in style.json')
    return item


def tr_spec(tr, style=None, assets=None):
    """A SHOTS tr (style transition id or dict) -> normalised dict(kind, before, after, params...).
    style: style_info (to look up the id); assets: {name: asset}; parameter names like tex='fx_smear_tex' are taken
    from here (the template's load() reads them with load_tr_assets). curtain without sprites uses every fx_curtain_* in assets."""
    if not tr: return None
    if isinstance(tr, str):
        item = tr_item(tr, style)
        q = dict(item.get('params') or {}); q.setdefault('kind', item.get('kind')); q.setdefault('id', tr)
    else: q = dict(tr)
    if q.get('kind') in TR_NOT: raise ValueError(f'kind "{q["kind"]}" is not a transition between shots; do not use tr=')
    if q.get('kind') not in TR_DEFAULT: raise ValueError(f'transition kinds: {", ".join(TR_DEFAULT)} (got {q.get("kind")})')
    b, a = TR_DEFAULT[q['kind']]
    q.setdefault('before', b); q.setdefault('after', a)
    if q['kind'] == 'hinge': q.setdefault('hold', 2)
    if q['kind'] == 'curtain' and not q.get('sprites') and assets:
        q['sprites'] = sorted((k for k in assets if k.startswith('fx_curtain_')), key=_natural)
    for k in TR_ASSET:
        v = q.get(k)
        if assets is not None and isinstance(v, str): q[k] = assets.get(v)
        elif assets is not None and isinstance(v, list) and v and isinstance(v[0], str): q[k] = [assets.get(x) for x in v]
    return q


def _natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(s))]


def shot_tr(sh, style=None, assets=None):
    """The transition at the start of a shot (SHOTS tr= / smear= / mix=) -> tr_spec result or None.
    smear=(before cut, fully covered, after cut) in drawings: shorthand for the material smear; direction, wobble,
    power, edge and shadow come from the style package's kind: smear transition (default: in from bottom right, out
    to top left), asset defaults to assets['fx_smear_tex'].
    mix=drawings or mix=dict(after=8, live=True): dissolve; live=True lets the previous shot keep acting (the
    template's draw() continues it with Timesheet.carry)."""
    if sh.get('tr'): return tr_spec(sh['tr'], style, assets)
    if sh.get('smear'):
        a, full, b = sh['smear']
        base = next((t for t in (style or {}).get('transitions', []) if t.get('kind') == 'smear'), None)
        q = dict((base or {}).get('params') or {}); q.setdefault('tex', 'fx_smear_tex')
        q.update(kind='smear', before=a, after=full + b, hold=full)
        return tr_spec(q, style, assets)
    m = sh.get('mix')
    if m:
        q = dict(m) if isinstance(m, dict) else dict(after=int(m))
        if sh.get('live') is not None: q.setdefault('live', sh['live'])
        q['kind'] = 'mix'
        return tr_spec(q, style, assets)
    return None


def tr_names(q):
    """Asset names referenced by one transition's parameters -> [(key, name)]"""
    out = []
    for k in TR_ASSET:
        v = q.get(k)
        if isinstance(v, str): out.append((k, v))
        elif isinstance(v, list): out += [(k, x) for x in v if isinstance(x, str)]
    return out


def load_tr_assets(style, src, cells=None, assets=None, used=None):
    """Load transition assets into assets per style.json transition params (the template's load() calls this).
    Names are looked up in assets first, then cells/<name>.png (sliced cells), then src/<name>.png (whole images):
      smear tex -> kit.rd (opaque material close-up); slide tex -> transparent set layer (layers.load_layer + taper_layer);
      sprite / sprites (stitch, curtain, hinge) -> (C, a, M) from kit.sprite. curtain without sprites reads every fx_curtain_* in cells.
    used: only these transition ids (None = all in the style). -> (assets, missing), missing = [(transition id, name)]: not found, lint reports them"""
    assets = {} if assets is None else assets
    missing = []
    for t in (style or {}).get('transitions', []):
        if t.get('kind') not in TR_DEFAULT or (used is not None and t.get('id') not in used): continue
        q = t.get('params') or {}
        names = tr_names(q)
        if t['kind'] == 'curtain' and not q.get('sprites') and cells and os.path.isdir(cells):
            names += [('sprites', os.path.splitext(f)[0]) for f in sorted(os.listdir(cells), key=_natural)
                      if f.startswith('fx_curtain_') and f.endswith('.png')]
            if len(names) == 0: missing.append((t['id'], 'fx_curtain_* (cells sliced from the curtain fx sheet)'))
        for key, nm in names:
            if nm in assets and assets[nm] is not None: continue
            pc = os.path.join(cells, nm + '.png') if cells else None
            ps = os.path.join(src, nm + '.png') if src else None
            p = pc if pc and os.path.exists(pc) else (ps if ps and os.path.exists(ps) else None)
            if p is None: missing.append((t['id'], nm)); continue
            d = os.path.dirname(p)
            if key == 'tex' and t['kind'] == 'slide':
                import layers
                assets[nm] = layers.taper_layer(layers.load_layer(p))
            elif key == 'tex': assets[nm] = kit.rd(p)
            else: assets[nm] = kit.sprite(d, None, nm)
    return assets, missing


def tr_missing(shots, style=None, assets=None):
    """Assets missing for the transitions used in SHOTS -> list of problems (reported by the template's lint)"""
    bad = []
    for j, sh in enumerate(shots):
        if j == 0: continue
        try: q = shot_tr(sh, style, None)
        except ValueError as e: bad.append(f'shot {j} "{sh.get("name", "")}" transition: {e}'); continue
        if not q: continue
        names = tr_names(q)
        if q['kind'] == 'curtain' and not q.get('sprites'):
            if not any(k.startswith('fx_curtain_') for k in (assets or {})): bad.append(
                f'shot {j} "{sh.get("name", "")}" curtain transition has no assets: slice the fx sheet into fx_curtain_0..., or list cell names in params.sprites')
        for key, nm in names:
            if (assets or {}).get(nm) is None:
                bad.append(f'shot {j} "{sh.get("name", "")}" transition {q.get("id", q["kind"])} is missing asset "{nm}" '
                           f'(put src/{nm}.png or slice it to work/cells/{nm}.png; the template\'s load() reads it)')
    return bad


def _put_center(frame, c, X, Y, s, rot=0.0, **kw):
    """Place a cell's bbox centre at frame (X, Y), rotating about the centre"""
    C, a, M = c
    x0, y0, x1, y1 = kit.bbox(a, 0.5)
    return place_at(frame, c, X, Y, s, ref=((x0 + x1) / 2, (y0 + y1) / 2), rot=rot, **kw)


def cut_fx(q, d, cur, old=None):
    """Draw one transition drawing. q: tr_spec result; d: drawings from the cut (negative before the cut, the cut drawing = 0);
    cur: this drawing's own picture (old shot before the cut, new shot after); old: for transitions that need the old
    picture after the cut (TR_NEEDS_OLD), the old shot's held picture.
    -> new picture (float RGB). Returned unchanged outside the transition window."""
    kind, b, a = q['kind'], int(q['before']), int(q['after'])
    if not (-b <= d < a): return cur
    H, W = cur.shape[:2]
    f = np.ascontiguousarray(cur, np.float32).copy()
    if kind == 'smear':
        tex = q.get('tex')
        if tex is None: return f
        hold = int(q.get('hold', 1)); pw = float(q.get('power', 2))
        kw = dict(wobble=q.get('wobble', 0.25), edge=q.get('edge', 'round'), shadow=tuple(q.get('shadow', (10, 14, 0.38))),
                  fit=q.get('fit', False))
        if d < 0: k, org = (d + b + 1) / (b + 1), q.get('origin_in', (0.92, 0.95))
        elif d < hold: k, org = 1.0, q.get('origin_in', (0.92, 0.95))
        else: k, org = 1 - (d - hold + 1) / (a - hold + 1), q.get('origin_out', (0.05, 0.02))
        f = smear(f, tex, max(0.0, k) ** pw, tuple(org), seed=q.get('seed', 3) + (0 if d < hold else 1), **kw)
    elif kind == 'page' and old is not None:
        side = q.get('side', 'r'); n = max(1, a)
        tbl = [0.84, 0.56, 0.30, 0.11, -0.018, 0.0]
        u = tbl[d] if n == 6 else (1 - kit.ease_out((d + 1) / n))
        off = int(round(u * W)) * (1 if side == 'r' else -1)
        if off == 0: return f
        out = old.copy(); edge = off if side == 'r' else W + off
        xs = np.arange(W, dtype=np.float32)
        dist = (edge - xs) if side == 'r' else (xs - edge)
        sh = np.clip(1 - dist / float(q.get('edge_px', 46)), 0, 1) * (dist > -2)
        out *= (1 - float(q.get('shadow', 0.42)) * sh ** 1.6)[None, :, None]
        if side == 'r': x0 = max(0, edge); out[:, x0:] = f[:, :W - x0]
        else: x1 = min(W, edge); out[:, :x1] = f[:, W - x1:]
        e = int(np.clip(edge, 1, W - 3)); out[:, e:e + 2] = np.clip(out[:, e:e + 2] * 0.6 + 0.42, 0, 1)
        f = out
    elif kind == 'slide':
        L = q.get('tex')
        if L is None: return f
        L = np.asarray(L, np.float32)
        if L.shape[2] == 3: L = np.dstack([L, np.ones(L.shape[:2], np.float32)])
        h, w = L.shape[:2]; n = b + a
        Hs = H * float(q.get('height', 2.6)); Ws = Hs * w / h
        u = (d + b + 0.5) / n
        x0 = -Ws + (Ws + W) * u if q.get('dir', 'r') == 'r' else W - (Ws + W) * u
        y0 = H * float(q.get('y', 1.06)) - Hs
        M = np.array([[Ws / w, 0, x0], [0, Hs / h, y0]], np.float64)
        Pp = cv2.warpAffine(np.ascontiguousarray(L), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        if q.get('blur', 40) >= 2: Pp = kit.hblur(Pp, int(q.get('blur', 40)))
        al = Pp[..., 3:4]
        sh = cv2.GaussianBlur(np.ascontiguousarray(np.roll(Pp[..., 3], -14 if q.get('dir', 'r') == 'r' else 14, 1)), (0, 0), 20)[..., None]
        f *= 1 - float(q.get('shadow', 0.45)) * sh * (1 - al)
        f = f * (1 - al) + Pp[..., :3]
    elif kind == 'stitch' and old is not None:
        k = kit.ease((d + 1) / max(1, a))
        right = q.get('dir', 'r') == 'r'
        xe = (-0.06 * W + k * 1.12 * W) if right else (1.06 * W - k * 1.12 * W)
        xx = np.arange(W, dtype=np.float32)[None, :]
        m = np.clip(((xe - xx) if right else (xx - xe)) / 3.0 + 0.5, 0, 1)[..., None]
        f = f * m + old * (1 - m)
        sh = np.clip(1 - np.abs(xx - xe - (26 if right else -26)) / 40, 0, 1)[..., None]
        f = f * (1 - float(q.get('shadow', 0.30)) * sh)
        sp = q.get('sprite')
        if sp is not None:
            ys, xs_ = np.nonzero(sp[1] > 0.5); length = max(1, xs_.max() - xs_.min())
            _put_center(f, sp, xe, H * 0.5, H * 1.12 / length, rot=90.0)
    elif kind == 'curtain':
        sps = [x for x in (q.get('sprites') or []) if x is not None]
        if not sps: return f
        rng = np.random.default_rng(q.get('seed', 5)); k = d + b; n = b + a
        lo, hi = q.get('size', (0.55, 1.45))
        for i in range(int(q.get('n', 22))):
            x = W * (rng.random() * 1.2 - 0.1); sz = H * (lo + (hi - lo) * rng.random())
            v = 0.85 + 0.5 * rng.random(); delay = rng.random() * 4
            u = (k - delay) / max(1, n - 4); y = H * 1.6 - u * H * 2.6 * v
            if y > H * 1.9 or y < -H * 0.9: continue
            sp = sps[(i + k // 3) % len(sps)]
            ys, _ = np.nonzero(sp[1] > 0.5); hh = max(1, ys.max() - ys.min())
            _put_center(f, sp, x, y, sz / hh, rot=(i * 37 + k * 2) % 360, vmotion=int(q.get('blur', 24)))
    elif kind == 'wipe' and old is not None:
        dd = q.get('dir', 'r'); kk = kit.ease((d + 1) / max(1, a))
        g = old.copy(); transition(g, {'r': 'wipe_r', 'l': 'wipe_l', 'u': 'wipe_u', 'd': 'wipe_d'}[dd], kk, soft=q.get('soft', 0.04))
        m = np.ones((H, W, 1), np.float32); transition(m, {'r': 'wipe_r', 'l': 'wipe_l', 'u': 'wipe_u', 'd': 'wipe_d'}[dd], kk,
                                                     color=(0.0,), soft=q.get('soft', 0.04))
        f = old * m + f * (1 - m)
    elif kind == 'glow':
        # brightness goes through finish(glow=tr_glow(q, d)) (bloom opened up); here only the dissolve and optional overall lift, no double brightening
        if d >= 0 and old is not None and q.get('mix', True):
            xf = int(q.get('xfade', a))
            u = kit.ease((d + 1) / max(1, xf + 1)) if d < xf else 1.0
            f = old * (1 - u) + f * u
        lift = float(q.get('lift', 0))
        if lift: f = f * (1 + lift * tr_glow(dict(q, _curve=True), d))
    elif kind == 'hinge':
        sp = q.get('sprite')
        if sp is None: return f
        hold = int(q.get('hold', 2)); pw = float(q.get('power', 1.4))
        if d < 0: u = (d + b + 1) / max(1, b)
        elif d < hold: u = 1.0
        else: u = 1 - (d - hold + 1) / max(1, a - hold + 1)
        f = hinge(f, sp, max(0.0, min(1.0, u)) ** pw, q.get('hinge', 'lr'), overlap=q.get('overlap', 60),
                  over=q.get('over', 70), focal=q.get('focal', 3.2), back=q.get('back', 0.62), cast=q.get('cast', 0.25))
    elif kind == 'mix' and old is not None:
        u = kit.ease((d + 1) / max(1, a + 1)); f = old * (1 - u) + f * u
    sk = float(q.get('shake', 0))
    if sk:
        j = np.round(np.random.default_rng([int(q.get('seed', 3)), d + 1000]).normal(0, sk, 2)).astype(int)
        f = cv2.warpAffine(f, np.float32([[1, 0, j[0]], [0, 1, j[1]]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return f


def tr_glow(q, d):
    """The glow (0-1) to give finish for this drawing of a glow transition; 0 for other transitions.
    Rises to 1 over the before drawings, holds at the brightest for hold drawings after the cut (default 0), then
    falls back to 0 over the rest. glow parameters: hold, mix (False = glow only, no dissolve: hard cut at the
    brightest), xfade (dissolve drawings, default after), lift (extra overall brightening, default 0),
    bloom (False = no bloom, only lift: a lightbox lighting up whole)"""
    if not q or q['kind'] != 'glow': return 0.0
    if q.get('bloom') is False and not q.get('_curve'): return 0.0
    b, a = int(q['before']), int(q['after']); h = int(q.get('hold', 0))
    if d < -b or d >= a: return 0.0
    if d < 0: return (d + b + 1) / (b + 1)
    if d < h: return 1.0
    return max(0.0, 1 - (d - h + 1) / (a - h + 1))


def _hinge_quad(side, L, W, H, phi, focal, over):
    """Hinge flip: a board on frame edge side, length L (from the hinge inwards), turned to phi (0 = upright facing
    camera, 90 deg = flat, covering) -> its four target corners. Perspective: upright, the outer edge is nearer the
    camera and looks bigger (f / (f - L·cos phi))"""
    f = focal * L
    z = L * math.cos(phi); r = L * math.sin(phi) * f / max(1.0, f - z); g = f / max(1.0, f - z)
    if side in ('l', 'r'):
        top, bot = -over, H + over
        et, eb = H / 2 - (H / 2 + over) * g, H / 2 + (H / 2 + over) * g
        if side == 'l': return np.float32([[0, top], [r, et], [r, eb], [0, bot]])
        return np.float32([[W, top], [W - r, et], [W - r, eb], [W, bot]])
    lt, rt = -over, W + over
    el, er = W / 2 - (W / 2 + over) * g, W / 2 + (W / 2 + over) * g
    if side == 't': return np.float32([[lt, 0], [rt, 0], [er, r], [el, r]])
    return np.float32([[lt, H], [rt, H], [er, H - r], [el, H - r]])


def hinge(frame, sprite, u, hinge='lr', overlap=60, over=70, focal=3.2, back=0.62, cast=0.25):
    """Hinge flip (a box lid closing, a door opening, a sign flipping): a board flips in with perspective, hinged on
    a frame edge; u = 0 -> 1 covers the frame. Edits and returns frame.
    sprite: the board's (C, a, M) (generate a transparent board with the prop kind; the hinge / fold edge on the
    image's left (left-right hinges) or top (top-bottom hinges));
    hinge: 'lr' two halves closing towards each other (each half the frame + overlap) / 'l' 'r' one board from the
    left / right covering all / 't' 'b' from top / bottom / 'tb';
    over: how far the board extends past the frame top and bottom (or sides) px; focal: perspective focal length
    (multiple of board length; at 3.2 the upright outer edge grows up to ~1.45x);
    back: how dark the back face gets (brightness = back + (1 - back)·sin phi); cast: darkening the board casts on the
    frame before it covers. Angle phi = 90 deg x u (cut_fx already applies power for slow-then-fast)."""
    if u <= 0: return frame
    H, W = frame.shape[:2]
    C, a, _ = sprite
    x0, y0, x1, y1 = kit.bbox(a, 0.5)
    C = np.ascontiguousarray(C[y0:y1, x0:x1]); a = np.ascontiguousarray(a[y0:y1, x0:x1])
    hh, ww = a.shape
    sides = {'lr': 'lr', 'tb': 'tb'}.get(hinge, hinge)
    phi = math.radians(90 * min(1.0, u))
    shade = back + (1 - back) * math.sin(phi)
    for side in sides:
        two = len(sides) == 2
        L = ((W if side in 'lr' else H) / (2 if two else 1)) + (overlap if two else 0)
        dst = _hinge_quad(side, L, W, H, phi, focal, over)
        src = np.float32([[0, 0], [ww, 0], [ww, hh], [0, hh]])     # left-right hinges: image's left edge on the hinge; top-bottom: its top edge
        Mp = cv2.getPerspectiveTransform(src, dst)
        P_ = cv2.warpPerspective(np.ascontiguousarray(C * a[..., None]), Mp, (W, H), flags=cv2.INTER_LINEAR)
        A_ = cv2.warpPerspective(a, Mp, (W, H), flags=cv2.INTER_LINEAR)
        if u < 1 and cast: frame *= (1 - cast * A_ * (1 - math.sin(phi)))[..., None]
        frame[:] = frame * (1 - A_[..., None]) + P_ * shade
    return frame


class Subtitles:
    """Burn audio/subs.json from sound.py build into the frame. Style from style.json "subtitle".
        SUBS = animi.Subtitles('audio/subs.json', animi.style_info(STYLE_ID)['subtitle'], W, H)
        frame = SUBS.draw(frame, t)          # at the end of draw(), after finish() (subtitles get no grain or grading)
    size is for a 1080 short side and scales with other sizes; portrait subtitles sit a little higher (clear of
    platform buttons). Each block fades in and out over 0.1 s. Font is always Source Han Sans Bold (any other font
    value is set in siyuan too).
    plate (backing bar, required over bright or busy pictures): {"color": [r, g, b], "alpha": 0.55, "pad": [30, 12]},
        a rounded bar behind the text; without plate there is only the outline.
    Bilingual: when a cue has "en" (sound.json narration with en), the main line and the second-language line (en_size
        default 0.72 of the main size) are centred on **one** plate and appear and leave together; a dark plate is added
        even without plate. Each language is one line, never wrapped; when too wide the whole block shrinks (with a
        warning: shorten the sentence; sound.py lint catches it first).
    Always at the bottom of the frame, never moved up (top is only for old scripts and does nothing)."""

    def __init__(self, path, style=None, W=1920, H=1080, top=None):
        self.cues = json.load(open(path)) if isinstance(path, str) else list(path)
        st = dict(font='siyuan', size=54, color=[1, 1, 1], outline=[0, 0, 0], outline_w=5, pos='bottom')
        st.update(style or {}); self.st = st
        self.W, self.H = W, H
        k = min(W, H) / 1080
        self.size = int(round(st['size'] * k)); self.ow = max(1, int(round(st['outline_w'] * k)))
        self.en_size = int(round(st.get('en_size', st['size'] * 0.72) * k))
        self.y = int(H * (0.885 if H <= W else 0.80))
        self.y_top = int(H * (0.10 if H <= W else 0.14))
        self.top = []                                  # subtitles always at the bottom
        self.bilingual = any(c.get('en') for c in self.cues)
        self.plate = st.get('plate') or (dict(color=[0.08, 0.08, 0.08], alpha=0.6) if self.bilingual else None)
        self._img = {}; self._warned = set()

    def _line(self, text, size):
        """One line of text (no wrapping) -> non-premultiplied RGBA"""
        from PIL import Image, ImageDraw
        import fx
        f = fx.font('siyuan', size)
        ow = max(1, int(round(self.ow * size / max(1, self.size))))
        c = tuple(int(v * 255) for v in self.st['color']); o = tuple(int(v * 255) for v in self.st['outline'])
        x0, y0, x1, y1 = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), text, font=f, stroke_width=ow)
        im = Image.new('RGBA', (x1 - x0 + 4, y1 - y0 + 4), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((2 - x0, 2 - y0), text, font=f, fill=c + (255,), stroke_width=ow, stroke_fill=o + (255,))
        return np.asarray(im).astype(np.float32) / 255

    def _render(self, text, en=None):
        key = (text, en)
        if key in self._img: return self._img[key]
        rows = [self._line(text, self.size)] + ([self._line(en, self.en_size)] if en else [])
        gap = int(round(self.size * 0.16)) if en else 0
        w = max(r.shape[1] for r in rows); h = sum(r.shape[0] for r in rows) + gap * (len(rows) - 1)
        a = np.zeros((h, w, 4), np.float32); y = 0
        for r in rows:
            x = (w - r.shape[1]) // 2; a[y:y + r.shape[0], x:x + r.shape[1]] = r; y += r.shape[0] + gap
        lim = int(self.W * 0.92) - 2 * int(round(30 * self.size / 54))
        if w > lim:                         # no wrapping: shrink the whole block
            q = lim / w
            a = cv2.resize(a, (max(1, int(w * q)), max(1, int(h * q))), interpolation=cv2.INTER_AREA)
            if key not in self._warned:
                self._warned.add(key)
                print(f'Subtitles: "{text}"{" / " + chr(34) + en + chr(34) if en else ""} does not fit on one line, block shrunk to {q:.0%}: shorten this line (subtitles never wrap)',
                      file=sys.stderr)
        if self.plate: a = self._with_plate(a)
        self._img[key] = a
        return a

    def _with_plate(self, a):
        """Put a rounded plate behind the text (non-premultiplied RGBA, may be two lines) -> new RGBA"""
        from PIL import Image, ImageDraw
        pl = self.plate; k = self.size / 54
        px, py = [int(round(v * k)) for v in pl.get('pad', [30, 12])]
        h, w = a.shape[:2]; Hh, Ww = h + 2 * py, w + 2 * px
        m = Image.new('L', (Ww + 8, Hh + 8), 0)
        rad = pl.get('radius', min(Hh // 2, int(round(self.size * 0.6))))
        ImageDraw.Draw(m).rounded_rectangle((4, 4, Ww + 3, Hh + 3), radius=int(rad), fill=255)
        m = cv2.GaussianBlur(np.asarray(m, np.float32) / 255, (0, 0), 1.5) * float(pl.get('alpha', 0.55))
        out = np.zeros((Hh + 8, Ww + 8, 4), np.float32)
        out[..., :3] = np.array(pl.get('color', [0.08, 0.08, 0.08]), np.float32); out[..., 3] = m
        ta = a[..., 3:4]; y0, x0 = 4 + py, 4 + px
        reg = out[y0:y0 + h, x0:x0 + w]
        na = ta + reg[..., 3:4] * (1 - ta)
        reg[..., :3] = (a[..., :3] * ta + reg[..., :3] * reg[..., 3:4] * (1 - ta)) / np.maximum(na, 1e-6)
        reg[..., 3:4] = na
        return out

    def draw(self, frame, t):
        top = any(a <= t < b for a, b in self.top)
        yc = self.y_top if top else self.y
        for c in self.cues:
            if not (c['t0'] <= t < c['t1']): continue
            fade = min(1.0, (t - c['t0']) / 0.1, (c['t1'] - t) / 0.1)
            try: a = self._render(c['text'], c.get('en'))
            except TypeError: a = self._render(c['text'])         # old scripts that subclass Subtitles with their own _render(self, text)
            h, w = a.shape[:2]
            x0 = (self.W - w) // 2; y0 = yc - h // 2
            y0 = max(y0, int(self.H * 0.03)) if top else min(y0, int(self.H * 0.965) - h)   # two-line blocks stay inside the safe area too
            ys, xs = slice(max(0, y0), min(self.H, y0 + h)), slice(max(0, x0), min(self.W, x0 + w))
            sub = a[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
            al = sub[..., 3:4] * fade
            frame[ys, xs] = frame[ys, xs] * (1 - al) + sub[..., :3] * al
        return frame


def tilt_shift(frame, center=0.55, band=0.12, max_blur=6.0):
    """Tilt-shift: the focal plane is a horizontal band (center = band centre as a share of frame height, band = half
    width); above and below blur in 3 steps by distance, interpolated."""
    H = frame.shape[0]
    y = np.arange(H, dtype=np.float32) / H
    d = np.clip((np.abs(y - center) - band) / max(1e-3, 0.5 - band), 0, 1)       # 0 = in focus, 1 = most blurred
    levels = [frame] + [cv2.GaussianBlur(frame, (0, 0), max_blur * q) for q in (0.45, 1.0)]
    pos = d * 2
    out = np.zeros_like(frame)
    for i in range(3):
        w = np.clip(1 - np.abs(pos - i), 0, 1)[:, None, None]
        out += levels[i] * w
    return out


def finish(frame, ts, pic, style, glow=0.0):
    """Finish the whole frame per the fixed style's preset (last line of film.py's draw(); never write your own grading):
    light flicker -> greyscale (b/w cartoon) -> tilt-shift (miniature) -> misregistration (print styles) -> kit.grade
    (grain, vignette, bloom, tone; grain changes per drawing). glow 0-1: open up the bloom for this drawing (glow
    transition, a light coming on)."""
    f = frame * ts.flicker(pic, style.get('flicker', 0))
    if style.get('gray'):
        g = f[..., 0] * 0.299 + f[..., 1] * 0.587 + f[..., 2] * 0.114
        f = np.repeat(g[..., None], 3, 2)
    if style.get('tilt'):
        f = tilt_shift(f, **style['tilt'])
    mis = style.get('misreg', 0)
    if mis:
        dx, dy = ts.jitter(pic, mis, salt='misreg')
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        f[..., 0] = cv2.warpAffine(np.ascontiguousarray(f[..., 0]), M, f.shape[1::-1], borderMode=cv2.BORDER_REPLICATE)
    g = dict(style.get('grade', {}))
    g.setdefault('bloom', 0); g.setdefault('vig', 0); g.setdefault('grain', 0)
    if glow > 0:
        g['bloom'] = g['bloom'] + (0.85 - g['bloom']) * glow
        g['bloom_th'] = g.get('bloom_th', 0.72) - 0.18 * glow
        g['bloom_r'] = g.get('bloom_r', 26) * (1 + 0.8 * glow)
    if g.get('tint'): g['tint'] = tuple(g['tint'])
    if g.get('lift'): g['lift'] = tuple(g['lift'])
    return kit.grade(np.clip(f, 0, 1.5), seed=ts.seed(pic), **g)


def _main(argv=None):
    ap = argparse.ArgumentParser(prog='animi.py', description='lemo-animi sheet, style and prompt tools')
    sp = ap.add_subparsers(dest='cmd', required=True)
    c = sp.add_parser('check', help='QC a pose sheet')
    c.add_argument('png'); c.add_argument('--n', type=int, default=8); c.add_argument('--rows', type=int, default=2)
    c.add_argument('--cols', type=int, default=4); c.add_argument('--mode', default='auto'); c.add_argument('--out')
    c.add_argument('--birefnet', action='store_true'); c.add_argument('--mask'); c.add_argument('--json', action='store_true')
    c.add_argument('--group', default='subject', choices=['subject', 'grid'],
                   help='grid: fx sheet, or a close-up sheet with two separate pieces per cell (two characters, character + prop); one cell = one subject')
    c.add_argument('--allow-edge', nargs='?', const='all', default=None,
                   help='edges cut on purpose: bottom (chest-up close-up), left / right (a hand reaching in), top; '
                        'no value = all four (old 下 / 左 / 右 / 上 also accepted)')
    c.add_argument('--clean', action='store_true', help='remove the semi-transparent haze first, then check')
    c.add_argument('--float', dest='float_', action='store_true', help='floating / top-down characters: skip the ground line')
    s = sp.add_parser('slice', help='slice a sheet by subject')
    s.add_argument('png'); s.add_argument('outdir'); s.add_argument('prefix')
    s.add_argument('--n', type=int, default=8); s.add_argument('--rows', type=int, default=2); s.add_argument('--cols', type=int, default=4)
    s.add_argument('--mode', default='auto'); s.add_argument('--fragments', default='keep'); s.add_argument('--pad', type=int, default=24)
    s.add_argument('--birefnet', action='store_true'); s.add_argument('--mask'); s.add_argument('--json')
    s.add_argument('--group', default='subject', choices=['subject', 'grid'], help='grid: fx sheet / close-up sheet with two pieces per cell; pieces in a cell form one subject')
    s.add_argument('--clean', action='store_true', help='remove the semi-transparent haze first; the cells come out clean')
    cl = sp.add_parser('clean', help='remove semi-transparent haze from a transparent background (shadows, paper drawn by the image model)')
    cl.add_argument('png'); cl.add_argument('out'); cl.add_argument('--lo', type=float, default=225)
    cl.add_argument('--hi', type=float, default=248); cl.add_argument('--min-area', type=int, default=400,
                    help='drop specks smaller than this area (about 20 for fx sheets)')
    a = sp.add_parser('anchors', help='anchor table')
    a.add_argument('cells'); a.add_argument('--masks'); a.add_argument('--prefix', default=''); a.add_argument('--mode')
    a.add_argument('--json'); a.add_argument('--preview')
    v = sp.add_parser('live', help='film liveness: find stretches where the picture is dead')
    v.add_argument('video'); v.add_argument('--out'); v.add_argument('--step', type=int, default=2)
    v.add_argument('--quiet-area', type=float, default=0.008); v.add_argument("--quiet-len", type=float, default=2.0)
    pr = sp.add_parser('prompt', help='assemble an asset prompt: style template + slot file',
                       formatter_class=argparse.RawDescriptionHelpFormatter,
                       description='Slot file: each slot starts with a line [name] (ASCII brackets, snake_case); the text runs '
                                   'to the next header.\n'
                                   'Example:\n'
                                   '[character] A round little clay penguin ...\n'
                                   '[action]\n'
                                   '1 standing ...\n\n'
                                   'Templates use {name} variables, <<name>> replaceable parts and [[ ... ]] optional segments.\n'
                                   'Chinese headers (【角色】 = [character]) still work.')
    pr.add_argument('style'); pr.add_argument('kind', choices=PROMPT_TYPES); pr.add_argument('slots', nargs='?')
    pr.add_argument('-o', '--out'); pr.add_argument('--size', default='landscape', help='landscape | portrait | square -> {aspect}')
    pr.add_argument('--set', action='append', default=[], help='name=value: fill or override one slot')
    pr.add_argument('--styles-dir', help='experimental style: a style package folder in the film folder (default: the skill\'s styles/)')
    sl = sp.add_parser('styles', help='list the fixed styles')
    sl.add_argument('--lang', choices=('zh', 'en'), default='zh', help='language of style names and one-liners (match the language you use with the user)')
    sc = sp.add_parser('stylecheck', help='check style packages\' basic settings (no jitter, no flicker, title cards complete)')
    sc.add_argument('ids', nargs='*', help='style ids (none = all)')
    g = ap.parse_args(argv)
    if g.cmd == 'styles':
        for n, sid in enumerate(style_ids(), 1):          # number = order (style.json num)
            i = style_info(sid); en = g.lang == 'en'
            print(f"{n}\t{sid}\t{i.get('en') if en else i['name']}\t{i.get('line_en') if en else i.get('line', '')}")
        return 0
    if g.cmd == 'stylecheck':
        bad = [m for sid in (g.ids or style_ids()) for m in style_lint(sid)]
        for m in bad: print(m)
        print(f'stylecheck: {"all passed" if not bad else f"{len(bad)} failed"}'); return 1 if bad else 0
    if g.cmd == 'prompt':
        if g.styles_dir:
            global STYLES_DIR; STYLES_DIR = os.path.abspath(g.styles_dir)
        slots = parse_slots(open(g.slots).read()) if g.slots else {}
        for kv in g.set:
            k, _, v = kv.partition('='); slots[slot_name(k)] = v.strip()
        text = build_prompt(g.style, g.kind, slots, g.size)
        if g.out:
            os.makedirs(os.path.dirname(g.out) or '.', exist_ok=True)
            with open(g.out, 'w') as f: f.write(text + '\n')
            ref = PROMPT_REF.get(g.kind)
            print(f'{g.out} ({len(text)} chars)' + (f'. Attach {ref} as a reference image when generating' if ref else ''))
        else: print(text)
        return 0
    if g.cmd == 'live':
        r = liveness(g.video, g.step, quiet_area=g.quiet_area, quiet_len=g.quiet_len, out=g.out)
        tot = (r['times'][-1] + g.step / r['fps']) if r['times'] else 0
        qs = sum(d for _, d, _ in r['quiet'])
        st = 'FAIL' if qs > 0.25 * tot else ('WARN' if r['quiet'] else 'PASS')
        print(f"{os.path.basename(g.video)}: {st}  median active area {r['median']:.3f}  dead {qs:.1f}s / {tot:.1f}s")
        for t0, d, m in r['quiet']: print(f'  from {t0:.2f}s for {d:.2f}s: active area {m:.3f} (only a tiny part moves, or nothing)')
        if g.out: print(f'  timeline: {g.out}')
        return 1 if st == 'FAIL' else 0
    if g.cmd == 'clean':
        im = cv2.imread(g.png, cv2.IMREAD_UNCHANGED)
        if im is None or im.ndim < 3 or im.shape[2] < 4: raise SystemExit(f'{g.png}: not a PNG with alpha')
        before = haze_ratio(im[..., 3])
        a = clean_alpha(im[..., 3], g.lo, g.hi, g.min_area)
        im = im.copy(); im[..., 3] = (a * 255).round().astype(np.uint8); im[..., :3][a == 0] = 0
        os.makedirs(os.path.dirname(g.out) or '.', exist_ok=True); cv2.imwrite(g.out, im)
        print(f'{g.out}  semi-transparent pixels {before:.1%} -> {haze_ratio(a):.1%}  opaque {(a > 0.5).mean():.1%}')
        return 0
    if g.cmd == 'check':
        r = check_sheet(g.png, g.n, g.rows, g.cols, g.mode, g.mask, g.birefnet, g.out, group=g.group,
                        allow_edge=g.allow_edge, clean=g.clean, float_=g.float_)
        if g.json: print(json.dumps(r, ensure_ascii=False, indent=1)); return 1 if r['status'] == 'FAIL' else 0
        print(f"{os.path.basename(g.png)}: {r['status']}  subjects {r['n_found']}/{r['n_expected']}  "
              f"edges {'transparent' if is_transparent(g.png) else 'white'} {min(r['border_white'].values()):.0%}  " +
              (f"height spread {r['stats']['height_spread']:.0%} area spread {r['stats']['area_spread']:.0%}" if r['stats'] else ''))
        for l, m in r['messages']: print(f'  [{l}] {m}')
        if g.out: print(f'  preview: {g.out}')
        return 1 if r['status'] == 'FAIL' else 0
    if g.cmd == 'slice':
        paths, info = slice_subjects(g.png, g.n, g.rows, g.cols, g.outdir, g.prefix, g.mode, g.mask, g.birefnet,
                                     pad=g.pad, fragments=g.fragments, group=g.group, clean=g.clean)
        print(f"{g.prefix}: {len(paths)} cells  {info['size'][0]}x{info['size'][1]}  subjects {info['n_found']}/{info['n_expected']}"
              + ('' if info['ok'] else '  ! ' + '; '.join(info['warnings'])))
        if g.json:
            os.makedirs(os.path.dirname(g.json) or '.', exist_ok=True)
            with open(g.json, 'w') as f: json.dump(info, f, ensure_ascii=False, indent=1)
        return 0 if info['ok'] else 1
    if g.cmd == 'anchors':
        A = anchors(g.cells, g.masks, g.prefix, g.mode, g.json)
        for k in A:
            c = A[k]; print(f"{k}: foot_y={c['foot_y']} body_x={c['body_x']:.1f} bottom_x={c['bottom_x']:.1f} h={c['height']} bbox={c['bbox']}")
        print(f'median bbox height {A.median_h:.1f}')
        bx = [A[k]['body_x'] - (A[k]['bbox'][0] + A[k]['bbox'][2]) / 2 for k in A]
        print(f'body-centre offset from bbox centre spans {max(bx) - min(bx):.1f} px (above 5 px, placing by bbox makes feet slide: place with place_at by anchor)')
        if g.preview: preview_cells(g.cells, g.preview, g.masks, g.prefix, g.mode, A=A); print(f'preview: {g.preview}')
        return 0


if __name__ == '__main__':
    sys.exit(_main())
