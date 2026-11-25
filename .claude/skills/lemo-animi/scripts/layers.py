# layers.py -- layered sets and environment: transparent set layers (foreground, multi-plane parallax), environment
#              sprite cache, swaying plants, particles (snow, petals, bubbles), small things in the background moving on
#              their own (sway, twinkle, chase lights), fx sheets played with offset phases at given points.
#
# Everything runs per drawing (pic); random values are keyed by drawing number. Assets are all generated images
# (transparent paper layers, prop sheets, fx sheets); code only handles position, angle and timing.
#   import layers
#   L = layers.load_layer(f'{SRC}/layer_front.png')                   # transparent set layer -> premultiplied RGBA
#   layers.put_layer(frame, cam, L, par=1.35, x0=-100, y_top=760, width=2300)
#   spr = layers.Sprites(cells, info)                                 # environment sprites: cached per scale step
#   layers.plants(frame, spr, cam, PLANTS, pic, wind=0.2)             # clumps sway around their roots
#   SNOW = layers.Particles([f'snow_{k}' for k in range(8)], mode='fall', n=150)
#   SNOW.draw(frame, spr, pic, amount=1.0, wind=2.0)
# API in references/api.md, "layers.py".
import os, sys, math
import numpy as np, cv2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit, animi  # noqa: E402


# =====================================================================================
# Transparent set layers (foreground, multi-plane parallax, paper layers)
# =====================================================================================
def load_layer(path, trim=6, pad_top=6, flat_bottom=True):
    """A transparent full-width set layer -> premultiplied RGBA (h, w, 4): crop to the alpha box, shave trim columns of
    ragged edge left and right, add pad_top transparent rows on top (cam.plate replicates edges: opaque pixels in the top
    row would stretch upward into streaks); flat_bottom: the bottom is a straight cut, fill it solid"""
    I, a = animi.load_rgba(path)
    if a is None: raise ValueError(f'{path}: not a transparent image')
    cols = np.where(a.max(0) > 0.5)[0]; rows = np.where(a.max(1) > 0.5)[0]
    c0, c1 = cols[0] + trim, cols[-1] + 1 - trim
    I = I[rows[0]:rows[-1] + 1, c0:c1]; a = a[rows[0]:rows[-1] + 1, c0:c1].copy()
    if flat_bottom: a[-4:] = np.maximum(a[-4:], a[-5:-4])
    L = np.dstack([I * a[..., None], a]).astype(np.float32)
    return np.concatenate([np.zeros((pad_top, L.shape[1], 4), np.float32), L], 0)


def tile_layer(L, n=2, overlap=0.06):
    """Tile one set layer horizontally n times (each overlapping the previous one's right end) so pans and strong
    parallax never show an edge"""
    h, w = L.shape[:2]; step = int(w * (1 - overlap))
    out = np.zeros((h, step * (n - 1) + w, 4), np.float32)
    for i in range(n):
        reg = out[:, i * step:i * step + w]; reg[:] = reg * (1 - L[..., 3:4]) + L
    return out


def taper_layer(L, frac=0.07):
    """A set layer with vertical cuts at both ends looks like a wall when panned: cut both ends at a slant and add a short fade"""
    h, w = L.shape[:2]; e = frac * w
    y = np.linspace(0, 1, h, dtype=np.float32)[:, None]; x = np.arange(w, dtype=np.float32)[None, :]
    m = np.clip((x - e * (1 - y) * 0.9) / (e * 0.25), 0, 1) * np.clip(((w - 1 - x) - e * y) / (e * 0.25), 0, 1)
    return L * m[..., None]


def put_layer(frame, cam, L, par, x0, y_top, width, sy=1.0, dy=0.0, shadow=0.38, shadow_dy=-9, mul=1.0):
    """Frame a transparent set layer with parallax and composite it onto the picture (in place). The layer spans the
    stage from (x0, y_top), width wide;
    par: parallax (far 0.3, mid 0.9, same plane as the characters 1.0, foreground 1.3–1.6); sy < 1: squash with the bottom
    edge as pivot (the drawings where a paper layer stands up);
    dy: vertical bob (environment motion: dy = amp × sin(2π·pic/period + phase)); shadow: a soft shadow cast under the layer
    (offset up by shadow_dy px);
    mul: brightness multiplier for the whole layer (darken far layers a little)."""
    h, w = L.shape[:2]; hh = width * h / w; y1 = y_top + hh + dy; y0 = y1 - hh * max(sy, 0.02)
    Pp = cam.plate(L, par, rect=(x0, y0, x0 + width, y1))
    a = Pp[..., 3:4]
    if shadow:
        sh = cv2.GaussianBlur(np.ascontiguousarray(np.roll(Pp[..., 3], shadow_dy, 0)), (0, 0), 13)[..., None]
        frame *= 1 - shadow * sh * (1 - a)
    frame[:] = frame * (1 - a) + Pp[..., :3] * mul
    return frame


# =====================================================================================
# Environment sprites: cached per scale step when one cell is drawn many times (seaweed, bubbles, small fish, snow clumps)
# =====================================================================================
class Sprites:
    """cells: {cell name: kit.sprite's (C, a, M)}; info: {cell name: anchor dict} (animi.anchors / cell_anchor).
    Each cell is cropped to its box, then pre-scaled once per 6% step and cached; put() only does a small affine, so a dozen
    environment sprites per drawing stay fast."""
    def __init__(self, cells, info=None, step=1.06):
        self.cells, self.step, self._c = cells, step, {}
        self.info = info or {k: animi.cell_anchor(c[1]) for k, c in cells.items()}

    def __contains__(self, k): return k in self.cells

    def get(self, name, s):
        """-> ((C, a, M), anchor, remaining scale)"""
        q = round(math.log(max(s, 1e-3)) / math.log(self.step))
        key = (name, q)
        if key not in self._c:
            C, a, M = self.cells[name]; inf = self.info[name]
            x0, y0, x1, y1 = [int(v) for v in inf['bbox']]
            x0, y0 = max(0, x0 - 4), max(0, y0 - 4); x1, y1 = min(a.shape[1], x1 + 4), min(a.shape[0], y1 + 4)
            C, a = C[y0:y1, x0:x1], a[y0:y1, x0:x1]
            sq = self.step ** q
            if sq < 0.97:
                nw, nh = max(2, int(round(C.shape[1] * sq))), max(2, int(round(C.shape[0] * sq)))
                C = cv2.resize(np.ascontiguousarray(C), (nw, nh), interpolation=cv2.INTER_AREA)
                a = cv2.resize(np.ascontiguousarray(a), (nw, nh), interpolation=cv2.INTER_AREA)
            else: sq = 1.0
            if len(self._c) > 2000: self._c.clear()
            self._c[key] = ((np.ascontiguousarray(C), np.ascontiguousarray(a), np.ones_like(C)), animi.cell_anchor(a), sq)
        c, inf, sq = self._c[key]
        return c, inf, s / sq

    def height(self, name): return self.info[name]['height']

    def put(self, frame, name, X, Y, s, rot=0.0, at='center', **kw):
        """Paste one cell at (X, Y). at: 'center' box centre (floating things, particles) / 'root' bottom-centre of the box
        (things growing from the ground, rotating around the root) / 0–1 position along the box's bottom edge (a bent
        plant whose root is off centre) / 'foot' stand on the anchor. Other arguments go to place_at"""
        c, inf, r = self.get(name, s)
        x0, y0, x1, y1 = inf['bbox']
        if at == 'center': ref = ((x0 + x1) / 2, (y0 + y1) / 2)
        elif at == 'root': ref = ((x0 + x1) / 2, y1)
        elif isinstance(at, (int, float)): ref = (x0 + at * (x1 - x0), y1)
        else: return animi.place_at(frame, c, X, Y, r, info=inf, rot=rot, **kw)
        return animi.place_at(frame, c, X, Y, r, info=inf, ref=ref, rot=rot, **kw)


def sway(pic, amp, per, phase=0.0, second=0.35):
    """Back-and-forth sway angle (degrees): main swing + a small one at double speed, so it does not look mechanical.
    per: period (drawings); offset per and phase between clumps"""
    return amp * math.sin(2 * math.pi * pic / per + phase) + second * amp * math.sin(2 * math.pi * pic / (0.47 * per) + 1.7 * phase)


def bob(pic, amp, per, phase=0.0):
    """vertical bob (px): floating things, paper layers rising and falling"""
    return amp * math.sin(2 * math.pi * pic / per + phase)


# =====================================================================================
# Plant layer: grass, seaweed, reeds, wheat, swaying around the root; in strong wind switch to more bent drawings
# =====================================================================================
def plants(frame, spr, cam, items, pic, wind=0.0, front=None):
    """items: one dict per clump:
        cell cell name; x, y root position on stage; h height (fraction of frame height); par parallax (back row 0.9,
        front row 1.25);
        blur depth of field px; lum brightness (back row 0.8–0.9); amp swing (degrees, default 2.2–3.8 staggered); per
        period (drawings, default 20–31 staggered);
        bent=[half-bent cell, fully bent cell] (optional): more bent drawings in strong wind (rotating a rigid drawing
        cannot look "blown over").
    wind 0–1: blows left (negative: right); front=True / False draws only the front row (par > 1) / back row; None draws all.
    Draw the back row before the characters and the front row after them."""
    for i, it in enumerate(items):
        par = it.get('par', 1.0)
        if front is not None and (par > 1.0) != front: continue
        name, lean, shake = it['cell'], abs(wind) * 22, abs(wind) * 4.5
        bent = it.get('bent') or []
        w = abs(wind)
        if bent and w >= 0.3:
            if w < 0.65 or len(bent) < 2: name, lean, shake = bent[0], 4 + 8 * (w - 0.3), 3.0
            else:
                flap = ((pic + i * 2) // (2 + i % 2)) % 3
                name, lean, shake = (bent[1] if flap < 2 else bent[0]), 2.0 * w, 3.5 * w
        straight = it['cell']
        s = cam.H * it.get('h', 0.3) / spr.height(straight) * cam.k(par)
        if name != straight: s *= math.sqrt(spr.info[straight]['area'] / spr.info[name]['area'])   # match bent drawings to the straight one by area
        per = it.get('per', 20 + (i * 7) % 12); amp = it.get('amp', 2.2 + (i % 3) * 0.8)
        calm = max(0.0, 1 - 1.5 * w)
        rot = calm * sway(pic, amp, per, it.get('phase', i * 1.9))
        rot += (lean + shake * math.sin(pic * 2.1 + i * 1.3)) * (1 if wind >= 0 else -1)
        c, inf, r = spr.get(name, s)
        bx0, _, bx1, _ = inf['bbox']
        root = min(0.98, max(0.02, (inf['bottom_x'] - bx0) / max(1, bx1 - bx0)))      # root position along the box's bottom edge
        X, Y = cam.xy(it['x'], it['y'], par)
        lum = it.get('lum', 1.0)
        if lum != 1.0: c = (c[0] * np.array([lum, lum * 1.02, lum * 1.06], np.float32), c[1], c[2])
        animi.place_at(frame, c, X, Y, r, info=inf, anchor=root, pivot=root, rot=rot, blur=it.get('blur', 0.0) * cam.k(par))


# =====================================================================================
# Particles: fx sheet cells used as particles (snow clumps, petals, leaves, confetti, bubbles, fireflies)
# =====================================================================================
class Particles:
    """mode='fall': full-screen fall (snow, petals, leaves, confetti). Three planes: far (small, faint, slow), mid, near
    (big, blurred, fast); wind pushes one way, particles drift side to side.
       mode='rise': rising from vents (bubbles, puffs of steam, fireflies), one per vent every per drawings; floats up,
       drifts side to side, turns slowly, until it leaves the frame.
    cells: list of fx sheet cell names (each particle picks one at random); size: size of the three planes (fraction of
    the frame's short side); speed: px per drawing for the three planes (1080p).
    blur: blur px. One number = the whole layer gets that blur (close-up bubbles, snow: blur=3; rise mode uses it too);
    fall mode also accepts
    a triple (far, mid, near) per plane.
    draw(frame, spr, pic, amount=1, wind=0, cam=None, vents=None): amount 0–1.6 is density (> 1 heavy snow); wind is
    horizontal px per drawing;
    vents=[(stage x, stage y), ...] (rise mode's vents); with cam, particles follow the camera (parallax par)."""
    def __init__(self, cells, mode='fall', n=150, seed=5, size=(0.009, 0.019, 0.043), speed=(5, 9, 15),
                 alpha=(0.55, 0.9, 0.85), blur=(0.6, 0.0, 3.0), per=12, rise=8.0, par=0.95):
        self.cells, self.mode, self.n = list(cells), mode, n
        self.size, self.speed, self.alpha = size, speed, alpha
        if isinstance(blur, (int, float)): self.blur, self.blur_all = (float(blur),) * 3, float(blur)
        else: self.blur, self.blur_all = tuple(blur), 0.0
        self.per, self.rise, self.par = per, rise, par
        r = np.random.default_rng(seed); self.p = []
        for i in range(n):
            layer = 0 if i < n * 0.55 else (1 if i < n * 0.9 else 2)
            self.p.append((r.uniform(-0.1, 1.1), r.uniform(-0.1, 1.1), r.uniform(0.8, 1.25), r.uniform(0, 6.28), layer,
                           int(r.integers(0, max(1, len(self.cells))))))

    def draw(self, frame, spr, pic, amount=1.0, wind=0.0, cam=None, vents=None, size=1.0):
        if amount <= 0 or not self.cells: return frame
        H, W = frame.shape[:2]; sc = min(W, H) / 1080
        if self.mode == 'rise':
            for i, (vx, vy) in enumerate(vents or []):
                per = self.per + (i * 5) % 7
                for k in range(9):
                    age = (pic + i * 13) % per + k * per
                    if age > 75: continue
                    seed = (int((pic + i * 13) // per) - k) * 7 + i * 31
                    rr = 0.55 + 0.45 * ((seed * 37) % 11) / 10
                    X = vx + 22 * math.sin(age * 0.23 + seed) - wind * age * (0.8 + 0.4 * rr)
                    Y = vy - age * (self.rise + 3 * rr)
                    x, y = cam.xy(X, Y, self.par) if cam is not None else (X, Y)
                    if y < -80 or x < -80 or x > W + 80: continue
                    name = self.cells[(seed % len(self.cells) + len(self.cells)) % len(self.cells)]
                    s = (min(W, H) * self.size[1] * 3 * rr * size) / spr.height(name) * (cam.k(self.par) if cam else 1)
                    spr.put(frame, name, x, y, s * min(1.0, 0.4 + age / 10), rot=sway(age, 12, 30, seed), alpha=0.95,
                            motion=min(30, abs(wind) * 2.2), blur=self.blur_all)
            return frame
        n = int(len(self.p) * min(1.0, amount / 1.6))
        cx = (cam.cx - cam.SW / 2) if cam is not None else 0.0
        for (x0, y0, v, ph, layer, ci) in self.p[:n]:
            sp = self.speed[layer] * v * sc * (1 + 0.35 * max(0, amount - 1))
            y = (y0 * H + sp * pic) % (H + 200) - 100
            x = (x0 * W + wind * (1 + layer * 0.6) * pic + 14 * sc * (layer + 1) * math.sin(pic * 0.21 + ph)
                 - cx * (0.3, 0.8, 1.4)[layer]) % (W + 400) - 200
            name = self.cells[ci % len(self.cells)]
            s = min(W, H) * self.size[layer] * size * (0.7 + 0.08 * (ci % 8)) / max(1, spr.info[name]['width'])
            spr.put(frame, name, x, y, s, alpha=self.alpha[layer], blur=self.blur[layer],
                    vmotion=(2, 4, 8)[layer] * (1 + 0.5 * max(0, amount - 1)))
        return frame


# =====================================================================================
# Small things in the background move on their own: hanging stars sway, bulbs twinkle, chase lights (moving what the
# generated image already shows, not drawing new things in code)
# =====================================================================================
def find_glints(plate, region=(0, 0, 1, 0.62), rule='bright', min_area=60, max_frac=(0.12, 0.2)):
    """Find "small bright spots" in a background (foil stars, bulbs, fairy lights, lit windows) -> [(x0, y0, x1, y1, soft
    mask, phase), ...] (background source coordinates).
    region: search area (fractional x0, y0, x1, y1); rule: 'bright' bright and unsaturated (foil, white lights) / 'warm'
    warm yellow bright spots (bulbs, candlelight) /
    f(hsv) -> boolean mask; spots that are too big (moon, paper plates) are dropped by max_frac. Afterwards look at
    glint_board to confirm the right spots were found."""
    h, w = plate.shape[:2]
    X0, Y0, X1, Y1 = int(region[0] * w), int(region[1] * h), int(region[2] * w), int(region[3] * h)
    hsv = cv2.cvtColor((np.clip(plate[Y0:Y1, X0:X1], 0, 1) * 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    if callable(rule): m = rule(hsv)
    elif rule == 'warm': m = (hsv[..., 2] > 200) & (hsv[..., 0] > 10) & (hsv[..., 0] < 35) & (hsv[..., 1] > 80)
    else: m = (hsv[..., 2] > 150) & (hsv[..., 1] < 90)
    m = cv2.morphologyEx(np.asarray(m, np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n_, lab, st_, _ = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n_):
        x, y, bw, bh, area = st_[i]
        if area < min_area or bw > w * max_frac[0] or bh > h * max_frac[1] or area < 0.25 * bw * bh: continue
        pad = int(max(bw, bh) * 0.35) + 6
        a0, b0 = max(0, x - pad), max(0, y - pad); a1, b1 = min(X1 - X0, x + bw + pad), min(Y1 - Y0, y + bh + pad)
        blob = (lab[b0:b1, a0:a1] == i).astype(np.float32)
        blob = np.clip(cv2.GaussianBlur(cv2.dilate(blob, np.ones((7, 7), np.uint8)), (0, 0), 3) * 1.6, 0, 1)
        out.append((a0 + X0, b0 + Y0, a1 + X0, b1 + Y0, blob, (i * 2.399) % (2 * math.pi)))
    return out


def glints(img, spots, pic, mode='sway', amp=3.0, gain=0.22, period=0.55):
    """Animate the spots found -> new background image (call before cam.plate; camera moves as usual).
    mode: 'sway' hanging things swing ±amp px and twinkle / 'twinkle' twinkle only (brightness 1 -> 1+gain) /
    'chase' chase lights (step every 2 drawings, groups of three light in turn). Each spot uses its own phase."""
    if not spots: return img
    if mode == 'chase':
        g = np.ones(img.shape[:2], np.float32)
        for i, (x0, y0, x1, y1, blob, _) in enumerate(spots):
            g[y0:y1, x0:x1] += blob * (0.45 if (i + pic // 2) % 3 == 0 else -0.28)
        return img * g[..., None]
    out = img.copy()
    for x0, y0, x1, y1, blob, ph in spots:
        g = 1.0 + gain * max(0.0, math.sin(pic * 0.9 + ph * 1.7)) ** 3
        patch = img[y0:y1, x0:x1]
        if mode == 'sway':
            dx = amp * math.sin(pic * period + ph)
            patch2 = cv2.warpAffine(np.ascontiguousarray(patch), np.float32([[1, 0, dx], [0, 1, 0]]), (x1 - x0, y1 - y0),
                                    borderMode=cv2.BORDER_REPLICATE)
        else: patch2 = patch
        b = blob[..., None]
        out[y0:y1, x0:x1] = patch * (1 - b) + np.clip(patch2 * g, 0, 1) * b
    return out


def glint_board(plate, spots, out):
    """Circle the spots found and save an image; look at it before using them"""
    im = (np.clip(plate, 0, 1) * 255).astype(np.uint8)[..., ::-1].copy()
    for x0, y0, x1, y1, _, _ in spots: cv2.rectangle(im, (x0, y0), (x1, y1), (0, 0, 255), 2)
    cv2.imwrite(out, im); return out


def loop_fx(frame, spr, cam, pts, pic, cells, size, period=26, par=0.7, alpha=0.9, hold=2):
    """Loop an fx sheet at several points with offset phases (stars twinkling in the sky, distant splashes, chimney smoke):
    pts=[(stage x, stage y), ...]; cells: this fx sheet's cell names (in phase order); size: height in frame px;
    change cell every hold drawings; after playing, rest until period drawings then repeat; point i is offset by 7 drawings."""
    for i, (sx, sy) in enumerate(pts):
        ph = (pic + i * 7) % period
        if ph >= len(cells) * hold: continue
        name = cells[min(len(cells) - 1, ph // hold)]
        x, y = cam.xy(sx, sy, par)
        spr.put(frame, name, x, y, size / spr.height(name) * cam.k(par), alpha=alpha)
    return frame


# =====================================================================================
# Flock: a group of small things moving together (fish circling, scattering in fright, ducks in a line, birds, fireflies)
# =====================================================================================
class Flock:
    """A group of small things. Each member gets this drawing's position, facing and size from mode, then is drawn in
    front of or behind the hero by depth.
        fish = layers.Flock([[f'fish_{k}' for k in (0, 3)], [f'fish_{k}' for k in (1, 4)]], n=4, hold=2)
        items = fish.ring(pic, cx=900, cy=600, rx=420, ry=160)            # circle around (cx, cy)
        items = fish.scatter(pic, t=pic - motion_start_pic, origin=(900, 600))   # scatter in fright: accelerate out of frame
        items = fish.queue(pic, x0=300, y=820, gap=150, speed=9)             # line: one behind another, offset phases
        layers.draw_flock(frame, spr, cam, items, size=120, front=False)    # before the hero: the back half (depth < 0)
        ...draw the hero...
        layers.draw_flock(frame, spr, cam, items, size=120, front=True)     # after the hero: the front half
    cycles: cell cycles the members take turns using (a list of lists; one list = everyone shares one cycle); member i
    uses cycles[i % len], with offset phase;
    hold: drawings per cell (swimming, walking usually 2). All coordinates are stage coordinates; size is height in frame
    px (cached by Sprites).
    Each item is dict(cell, x, y, s relative size, rot, flip, depth, motion); depth > 0 is near (drawn in front of the hero)."""
    def __init__(self, cycles, n=4, hold=2, seed=3):
        cycles = list(cycles)
        self.cycles = cycles if cycles and isinstance(cycles[0], (list, tuple)) else [cycles]
        self.n, self.hold = n, hold
        r = np.random.default_rng(seed)
        self.ph = [float(x) for x in r.uniform(0, 2 * math.pi, n)]
        self.off = [int(x) for x in r.integers(0, 8, n)]

    def _cell(self, i, pic, fast=False):
        cyc = self.cycles[i % len(self.cycles)]
        h = max(1, self.hold // (2 if fast else 1))
        return cyc[(pic // h + self.off[i]) % len(cyc)]

    def ring(self, pic, cx, cy, rx, ry, speed=0.07, wobble=10.0, depth_size=0.12, ccw=True):
        """Circle: members evenly spaced on an ellipse; the lower half is near (a bit bigger, depth > 0). speed: radians per drawing"""
        out = []
        for i in range(self.n):
            th = pic * speed * (1 if ccw else -1) + i * 2 * math.pi / self.n + 0.4 * math.sin(pic * 0.05 + i)
            x = cx + rx * math.cos(th); y = cy + ry * math.sin(th) + bob(pic, wobble, 13, self.ph[i])
            vx = -math.sin(th) * (1 if ccw else -1)
            dep = math.sin(th)
            out.append(dict(cell=self._cell(i, pic), x=x, y=y, s=1 + depth_size * dep, rot=bob(pic, 4, 11, i),
                            flip=vx < 0, depth=dep, motion=0.0))
        return out

    def scatter(self, pic, t, origin, dirs=None, accel=26.0, spread=70.0):
        """Scatter in fright: for t < 0 jiggle in place near origin; from t >= 0 each accelerates out in its own direction
        (with motion blur).
        dirs: each member's direction [(dx, dy), ...] (default right, up-right, down-right, ...)"""
        dirs = dirs or [(1.0, -0.55), (1.0, 0.1), (0.85, 0.55), (0.6, -0.95), (-0.9, -0.4), (-0.8, 0.5)]
        out = []
        for i in range(self.n):
            ox, oy = origin[0] + 120 * (i % 2) + 60 * i - 90, origin[1] + (i - (self.n - 1) / 2) * spread
            if t < 0:
                x, y = ox + bob(pic, 30, 20, self.ph[i]), oy + bob(pic, 14, 13, self.ph[i]); mot = 0.0; fast = False
                rot = bob(pic, 5, 9, i); flip = False
            else:
                u = t + 1.2; dx, dy = dirs[i % len(dirs)]; dist = accel * u * u
                x, y = ox + dx * dist, oy + dy * dist; mot = min(60.0, 7 * u); fast = True
                rot = -math.degrees(math.atan2(dy, abs(dx))) * 0.6; flip = dx < 0
            out.append(dict(cell=self._cell(i, pic, fast), x=x, y=y, s=1.0, rot=rot, flip=flip, depth=0.0, motion=mot))
        return out

    def queue(self, pic, x0, y, gap, speed, dy=0.0, lead=None, lead_s=1.0, lead_gap=None, lead_hold=None):
        """Line: one behind another walking in speed's direction (speed < 0 goes left), spaced gap, cell phases offset;
        lead: the leader's cell cycle (mother duck, lead_s times bigger than the line, lead_gap from the first member,
        lead_hold drawings per cell, default same as hold).
        dy: how much further back (farther) each member is than the one before"""
        out = []; d = 1 if speed >= 0 else -1
        if lead:
            x = x0 + speed * pic + d * (lead_gap or gap * 1.3)
            out.append(dict(cell=lead[(pic // max(1, lead_hold or self.hold)) % len(lead)], x=x, y=y, s=lead_s, rot=0.0, flip=d < 0, depth=0.0, motion=0.0))
        for i in range(self.n):
            out.append(dict(cell=self._cell(i, pic), x=x0 + speed * pic - d * gap * i, y=y + dy * i, s=1.0, rot=0.0, flip=d < 0,
                            depth=-0.01 * i, motion=0.0))
        return out


def draw_flock(frame, spr, cam, items, size, par=1.0, front=None, at='center', dark=1.0, **kw):
    """Draw the group computed by Flock, far to near by depth; front=True only near ones (depth > 0, drawn after the hero),
    False only far ones, None all.
    size: one member's height in frame px (in a wide shot); dark: darken farther members overall (< 1). at: which point to
    paste by ('center' floating, 'root' walking on the ground)"""
    for it in sorted(items, key=lambda q: q['depth']):
        if front is not None and (it['depth'] > 0) != front: continue
        name = it['cell']
        if name not in spr: continue
        X, Y = cam.xy(it['x'], it['y'], par)
        s = size * it['s'] / spr.height(name) * cam.k(par)
        c, inf, r = spr.get(name, s)
        if dark != 1.0: c = (c[0] * np.array([dark, dark * 1.02, dark * 1.07], np.float32), c[1], c[2])
        x0, y0, x1, y1 = inf['bbox']
        ref = ((x0 + x1) / 2, (y0 + y1) / 2) if at == 'center' else ((x0 + x1) / 2, y1)
        animi.place_at(frame, c, X, Y, r, info=inf, ref=ref, rot=it['rot'], flip=it['flip'], motion=it['motion'], **kw)
    return frame


# =====================================================================================
# Debris stream rushing along the ground: threads swept up by a flood, leaves blown by wind, pebbles in a dust storm
# =====================================================================================
class Stream:
    """n pieces of debris rush across the frame from one side, mostly along the ground; near ones (the near fraction) are
    big, blurred and fast; they re-enter from the other side after leaving the frame.
        deb = layers.Stream([f'deb_{k}' for k in range(6)], n=30, dir=-1)        # right to left
        deb.draw(frame, spr, cam, d=pic_in_shot, amount=flow_0_to_1, t0=10)
    band: which band of frame height the debris occupies (fraction; (0.5, 0.92) = lower half, along the ground); size:
    fraction of frame height (min, max); speed: px per drawing (1080p).
    amount < 0.05 draws nothing; small amounts are translucent (the flow just starting)."""
    def __init__(self, cells, n=30, dir=-1, speed=52.0, band=(0.5, 0.92), size=(0.042, 0.077), near=0.25, gap=0.9):
        self.cells, self.n, self.dir, self.speed = list(cells), n, dir, speed
        self.band, self.size, self.near, self.gap = band, size, near, gap

    def draw(self, frame, spr, cam, d, amount=1.0, t0=0, par=1.0):
        if amount < 0.05 or not self.cells: return frame
        H, W = frame.shape[:2]; sc = H / 1080
        for i in range(self.n):
            r1, r2, r3 = ((i * 37) % 17) / 16, ((i * 53) % 13) / 12, ((i * 29) % 11) / 10
            near = r3 > 1 - self.near
            v = self.speed * sc * (0.7 + 0.6 * r1) * (1.5 if near else 1.0)
            start = t0 + i * self.gap
            if d < start: continue
            span = W * 1.5; run = ((d - start) * v) % span
            x = (W * 1.2 - run) if self.dir < 0 else (-W * 0.2 + run)
            y = H * (self.band[0] + (self.band[1] - self.band[0]) * r2 ** 0.7) + 40 * sc * math.sin(d * 0.35 + i) \
                - ((d - start) * v * 0.06) % (H * 0.2)
            name = self.cells[i % len(self.cells)]
            if name not in spr: continue
            sz = H * (self.size[0] + (self.size[1] - self.size[0]) * r1) * (1.8 if near else 1.0)
            spr.put(frame, name, x, y, sz / spr.height(name), rot=d * (14 + 20 * r2) + i * 40, alpha=min(1.0, amount * 1.4),
                    motion=min(40, v * 0.55), blur=(2.5 if near else 0.0))
        return frame
