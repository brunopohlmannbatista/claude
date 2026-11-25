"""lemo-animi compositing script template. Copy it to <film>/tools/film.py and edit; do not write one from scratch.

    cp <skill>/scripts/film_template.py <film>/tools/film.py

Usage (inside the film folder; $PY = the Python that setup.sh printed):
    "$PY" tools/film.py lint            checks only: long holds, shot design, jump cuts, missing images, length vs the sound
                                      sheet; writes work/shots.json (the shot list)
    "$PY" tools/film.py board           storyboard: one frame per drawing at 1/4 resolution -> work/board.jpg + work/board.mp4
                                      + work/board_p1.jpg ... (48 drawings per page, under 2000 px: open these);
                                      measures hero size and checks darkness
    "$PY" tools/film.py still 0 40 80   full-resolution stills of these drawings -> work/still_<drawing>.png
    "$PY" tools/film.py                 final film: render -> burn subtitles (when there is narration) -> mux audio/mix.wav
                                      -> out/<NAME>.mp4, then run every check

Sound first: sound.json exists before the picture. With narration, run sound.py vo first (length of each line) and time
the shot list to the narration:
    VO = vo_times()            # {'L1': (start s, length s), ...}; {} when there is no narration
    P(VO['L2'][0] - 0.3)       # seconds -> drawing: cut to the next shot 0.3 s before line 2
Without narration (sound.json has no vo, or vo is empty): time the shot list to picture and score; set cuts with P(seconds).
lint writes work/shots.json so sound.json can time cues by shot ("shot N + offset"); after moving shots, re-run lint and
rebuild the sound. When the picture is done run sound.py build (-> audio/mix.wav, plus audio/subs.json with narration);
the final render burns subtitles and muxes sound automatically.

Edit only four places (leave the rest); do 1 and 3 first (placeholder characters are enough for lint / board), then 2 and
4 once the real assets exist:
    1. Settings at the top: first set SKILL to the absolute path of the skill's scripts/, then STYLE_ID, SIZE, NAME (same as
       sound.json's name), HERO_H
    2. load(): real assets (each shot's background, every sheet's cells and anchors, set layers, environment sprites)
    3. SHOTS + build(): shot list and timesheet
    4. render(): what each drawing shows (layers, supporting characters, environment, effects)
Edit this file one place at a time with the edit tool; after bulk constant changes, read the diff, then run lint.

Already handled by the template:
- renders straight at the film resolution (landscape / portrait / square), never small-then-upscaled;
- style parameters come from styles/<id>/style.json (jitter, grade, character lighting, shadows, rigid mode; no
  whole-frame flicker or grain); do not add your own grade. put() applies the whole lighting setup (rim width on
  close-up sheets, warm light, light zones); every object jitters on its own (supporting characters and props jit=0.5);
  top-down styles have no parallax and place by body core;
- assets are transparent PNGs: sliced cells are RGBA; use kit.sprite(cells, None, name) directly;
- shots: each SHOTS entry has its own shot size, background, camera move and set layers; shots hard-cut by default; for a
  transition write tr= (style transition) or mix=; transition assets are read automatically from src/ and the sliced
  cells per style.json's params; lint reports missing ones;
- transitions are drawn before the grade (they get graded with the picture); subtitles after the grade (no grain);
- the timesheet is animi.Timesheet; shots, light and jitter all run per drawing;
- characters are placed by anchor with place_at (feet do not slide); every sheet of one character uses one standard
  height HERO_H (A.scale_ref), so switching sheets never changes size;
- missing-image fallback: images not generated yet render from <name>_bad.png or a placeholder; lint and the final
  render report them, and the final render only makes a draft;
- automatic checks: long holds, repeated actions, shots and jump cuts, push limit, transition assets, hero size (and
  whether it matches across cuts), darkness, missing images, length vs the sound sheet, liveness of the final film.

Runs unedited: without assets it uses colour-block placeholders.
"""
import os, sys, glob, math, json, shutil, subprocess
from multiprocessing import Pool
import numpy as np, cv2

SKILL_AT_INIT = '/home/user/claude/.claude/skills/lemo-animi/scripts'


def _find_skill():
    """The skill's scripts/ folder: $LEMO_ANIMI_SKILL, the path recorded at init, this file's own folder, then the usual
    install places (newest plugin version first), so a film keeps working after the skill is updated or moved."""
    home = os.path.expanduser('~')
    codex = os.environ.get('CODEX_HOME') or os.path.join(home, '.codex')
    plugins = (glob.glob(os.path.join(codex, 'plugins', 'cache', '*', 'lemo-animi', '*', 'skills', 'lemo-animi', 'scripts'))
               + glob.glob(os.path.join(home, '.claude', 'plugins', 'cache', '*', 'lemo-animi', '*', 'skills', 'lemo-animi', 'scripts')))
    cands = [os.environ.get('LEMO_ANIMI_SKILL'), SKILL_AT_INIT, os.path.dirname(os.path.abspath(__file__))]
    cands += sorted(plugins, key=os.path.getmtime, reverse=True)
    cands += [os.path.join(home, d, 'lemo-animi', 'scripts') for d in ('.agents/skills', '.codex/skills', '.claude/skills')]
    for c in cands:
        if c and os.path.exists(os.path.join(c, 'animi.py')): return c
    raise SystemExit(f'{os.path.abspath(__file__)}: cannot find the skill scripts. '
                     f'export LEMO_ANIMI_SKILL=<skill>/scripts ($S in workflow.md) and run again')


SKILL = _find_skill()
sys.path.insert(0, SKILL)
import kit, animi, layers  # noqa: E402

WK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))       # film folder (parent of tools/)
SRC, WORK, FRAMES, OUT = (os.path.join(WK, d) for d in ('src', 'work', 'frames', 'out'))
SOUND = os.path.join(WK, 'sound.json')

# =====================================================================================
# 0. Settings
# =====================================================================================
STYLE_ID = 'felt'                   # fixed style id (animi.py styles lists them all)
SIZE = 'landscape'                  # landscape 1920×1080 / portrait 1080×1920 / square 1080×1080
NAME = 'pip'                       # short name: out/<NAME>.mp4, out/<NAME>.shots.json; must equal sound.json's "name" (it sets <name>.srt)
FPS = 24

INFO = animi.style_info(STYLE_ID)
STYLE = animi.style_preset(STYLE_ID)
SUB_STYLE = INFO.get('subtitle', {})
W, H = animi.SIZES[SIZE]
SHORT = min(W, H)
ON = STYLE.get('on', 2)
LIGHT = STYLE.get('light')           # character lighting (preset.light); None = flat, pasted as is. With light.floor, brightness follows the background's light zones
RIGID = STYLE.get('rigid', False)    # rigid material: no squash, idle adds nothing
TOP_DOWN = bool(STYLE['flags'].get('top_down'))   # top-down style: no background parallax (par=1); place and measure by body core
PAR = STYLE.get('par', 1.0 if TOP_DOWN else 0.9)   # background parallax: 1 (none) for flat styles (top-down, front-on relief)
# Minimum hero height (fraction of the frame's short side): animi.MIN_HERO (extreme-wide 15%, wide 30%, medium 40%,
# medium-close 60%; opening / landing wide shots 33%). A hero that is too small is the most common "looks bad":
# the audience cannot see what it is doing.
HERO_H = int(SHORT * 0.36)          # hero's standard height in a wide shot (px). Every sheet of the same character uses it: A.scale_ref(HERO_H)


def P(t):
    """seconds -> drawing number (on twos, 1 drawing = 2 frames)"""
    return int(round(t * FPS / ON))


def sound_sheet():
    return json.load(open(SOUND)) if os.path.exists(SOUND) else None


def vo_times():
    """-> {narration id: (start s, length s)}; {} when there is no narration (no sound.json, no vo, or vo empty).
    Lengths need sound.py vo to have run; otherwise length is None.
    Times written per shot in sound.json ("shot name+0.4") are converted to seconds by sound.load_sheet; None while
    there is no shot list yet."""
    d = sound_sheet(); out = {}
    try:
        import sound
        d = sound.load_sheet(SOUND) if d else d
    except Exception:
        pass
    for L in (d or {}).get('vo') or []:
        m = os.path.join(WK, 'audio', 'vo', f"{L['id']}.json")
        t = L.get('t')
        out[L['id']] = (t if isinstance(t, (int, float)) else None, json.load(open(m))['dur'] if os.path.exists(m) else None)
    return out


DUR = float((sound_sheet() or {}).get('dur', 30.0))     # film length comes from the sound sheet


# =====================================================================================
# 1. Assets: replace with your real assets
# =====================================================================================
def _placeholder_cell(k, n=8):
    """placeholder: a colour-block character that breathes and lifts its head (C, a, M); shape varies with k"""
    h, w = 420, 360
    a = np.zeros((h, w), np.float32)
    lift = int(18 * math.sin(k / n * 2 * math.pi))
    cv2.ellipse(a, (180, 300 - lift // 2), (120, 90 + lift // 3), 0, 0, 360, 1, -1)              # body
    cv2.circle(a, (270, 190 - lift), 55, 1, -1)                                                  # head
    cv2.line(a, (140, 380), (140, 410), 1, 14); cv2.line(a, (220, 380), (220, 410), 1, 14)      # legs
    a = cv2.GaussianBlur(a, (0, 0), 1.2)
    C = np.zeros((h, w, 3), np.float32); C[:] = (0.85, 0.42, 0.25)
    return C, a, np.ones_like(C)


def _placeholder_plate(w, h, hill_y, amp, seed):
    """placeholder background: sky + rolling hills + ground (in a real film, the background generated for this shot size)"""
    img = np.zeros((h, w, 3), np.float32)
    img[:] = np.linspace([0.62, 0.78, 0.92], [0.98, 0.92, 0.80], h)[:, None, :]
    xs = np.arange(w)
    top = (hill_y + amp * np.sin(xs / (w / 7) + seed)).astype(int)
    for x in range(w): img[top[x]:, x] = (0.45, 0.62, 0.48)
    img[int(h * 0.80):] = (0.55, 0.48, 0.36)
    return img


def plate(name):
    """Load one background at source size (do not pre-scale). Until generated, src/<name>_bad.png or a placeholder
    stands in, and lint keeps reporting it"""
    return animi.asset(f'{SRC}/{name}.png')


def sheet(prefix, n=8):
    """Load one sheet's sliced cells and anchors -> (cells, info). Until sliced, colour blocks stand in and lint keeps
    reporting it. Top-down styles also record each cell's body core (animi.set_core): place by core, measure body length"""
    jp = f'{WORK}/anchors_{prefix}.json'
    if os.path.exists(jp):
        A = animi.load_anchors(jp)
        cells, info = {k: kit.sprite(f'{WORK}/cells', None, k) for k in A}, {k: A[k] for k in A}
    else:
        animi.MISSING[jp] = 'placeholder'
        cells = {f'{prefix}_{k}': _placeholder_cell(k, n) for k in range(n)}
        info = {k: animi.cell_anchor(c[1]) for k, c in cells.items()}
    if TOP_DOWN:
        for k in cells: animi.set_core(info[k], cells[k][1])
    return cells, info


def load():
    """Pip Flies: real assets. Stage = frame coordinates (1920x1080) for every shot; each background fills the stage."""
    plates = {k: plate(f'bg_{k}') for k in ('class_wide', 'class_corner', 'class_floor', 'class_window', 'hill_wide', 'hill_bottom')}
    cells, info = {}, {}
    for p in ('owl', 'look', 'flap', 'jump', 'run', 'slide', 'sad', 'joy', 'puff', 'spray', 'snow', 'stoolprop'):
        c, i = sheet(p, 4 if p in ('sad', 'joy') else (1 if p == 'stoolprop' else 8)); cells.update(c); info.update(i)
    H_ = lambda k: info[k]['height']
    sc = {'look': HERO_H / H_('look_0'), 'flap': HERO_H / H_('flap_0'), 'jump': HERO_H / H_('jump_0'),
          'run': HERO_H / H_('look_0') * 1.0, 'owl': 1.35 * HERO_H / H_('owl_0'),
          'sad': 0.68 * SHORT / H_('sad_3'), 'joy': 0.64 * SHORT / H_('joy_1')}
    sc['run'] = sc['look']                       # same drawing scale as the look sheet (checked on stills)
    sc['slide'] = sc['run']
    sc['stoolprop'] = 0.46 * HERO_H * MEDIUM_K / H_('stoolprop_0')
    sc['puff'] = 0.55 * HERO_H / info['puff_2']['width'] * 1.4
    sc['spray'] = 0.9 * HERO_H / info['spray_2']['height']
    env = layers.Sprites({k: v for k, v in cells.items() if k.startswith('snow_')},
                         {k: v for k, v in info.items() if k.startswith('snow_')})
    snow = layers.Particles([f'snow_{k}' for k in range(8)], mode='fall', n=170, seed=11)
    # window panes: where falling snow may show inside the classroom shots (dark-blue night seen through the glass)
    win = {}
    for k, box in (('class_wide', (1440, 150, 1760, 470)), ('class_floor', (1560, 220, 1860, 640)),
                   ('class_window', (1460, 0, 1860, 820))):
        pl = D_plate = plates[k]; h, w = pl.shape[:2]; sx, sy = w / W, h / H
        m = np.zeros(pl.shape[:2], np.float32)
        x0, y0, x1, y1 = int(box[0] * sx), int(box[1] * sy), int(box[2] * sx), int(box[3] * sy)
        reg = pl[y0:y1, x0:x1]
        blue = (reg[..., 2] > reg[..., 0] * 1.35) & (reg[..., 2] > 0.12) & (reg.mean(2) < 0.55)
        m[y0:y1, x0:x1] = blue.astype(np.float32)
        m = cv2.GaussianBlur(m, (0, 0), 2.0)
        win[k] = np.repeat(m[..., None], 3, 2)
    assets, _ = animi.load_tr_assets(INFO, SRC, f'{WORK}/cells')
    return dict(plates=plates, cells=cells, info=info, sc=sc, ref='look', lscale={}, layers={}, env=env, snow=snow,
                win=win, assets=assets, flat_ok={'jump', 'slide', 'joy', 'run', 'look', 'flap', 'sad'})


# =====================================================================================
# 2. Shot list + timesheet
# =====================================================================================
# One entry per shot:
#   at: first drawing (use P(seconds) to line up with narration or score); size: shot size (extreme-wide / wide / medium /
#   medium-close / close-up); name; bg: which background;
#   place: which location (same set = same name); view: camera direction (front / side / left / right / reverse / top /
#   low; must match what this background really shows);
#   k: how much bigger the character is than in the wide shot; ground: ground line y; SW: stage width (bigger than W when
#   panning an extra-wide background);
#   cam: camera move inside the shot [(drawing within shot, cx, cy, zoom), ...], eased per drawing; zoom must not exceed
#   STYLE['push_max'] (lint checks; if intended write push_ok='reason').
# Transitions (optional; hard cut by default):
#   tr='<style transition id>' (style.json transitions, params there) or tr=dict(kind='page', side='r', ...) (animi.cut_fx);
#   style.json entries with kind move are not transitions (a paper layer standing up, pushing into a field): do them in
#   build() / render() as their how says, no tr=;
#   mix=drawings: dissolve from the previous shot (quiet moments, time passing; 0.5–0.7 s); live=True: the previous shot keeps
#   acting during the dissolve (instead of freezing on its last drawing; by default continued with Timesheet.carry: cells
#   keep cycling, x keeps moving; for another continuation write carry=lambda d: (cell name, state));
#   smear=(4, 1, 4): shorthand for a material smear (drawings before the cut, fully covered, after the cut; direction and
#   wobble come from the style's kind: smear entry, asset assets['fx_smear_tex']);
#   carrying a camera move through the cut (previous shot ends on a push / pan, next shot continues the same way) also
#   smooths a hard cut a lot.
#   No fade-to-black or iris at the start or end: the first frame is picture, the film ends holding on the last picture.
# Checks (optional):
#   min=0.35: lower bound for hero size in this shot (checked, intended); key=True: landing shot (wide shot minimum 33%);
#   cut_ok='checked the cut sheet: ...': this cut was flagged as a jump cut but checked and is not; the report says
#   "checked by hand";
#   size_ok='reason': hero size does not match the previous shot (same shot size differing by 1.3x or more, or a tighter
#   shot size without a bigger hero) but it was checked and is intended (the character walks toward camera);
# Darken the whole scene (optional): dark=0.6 or dark=dict(k=0.6, tint=[0.92, 0.97, 1.08]) (lights out, night; characters
#   darken too; lamp light is added after the darkening).
# Set layers (optional): layers=[dict(name='front', par=1.35, x0=-100, y_top=760, width=2300, front=True, bob=(6, 20)), ...]
#   front=True draws in front of the characters; bob=(amplitude px, period in drawings) bobs up and down; sy / dy / x0 may be
#   lambda k: ... (k = drawing within the shot, from 0):
#   paper layer standing up sy=lambda k: min(1, 1.1 * kit.ease_out(k / 8)), set layer sliding in x0=lambda k: -600 + 60 * min(k, 10).
#   name must be loaded in load()'s layers; lint reports unloaded ones.
# Set sway (optional): sway=(pixels, period in drawings): the whole set (background + set layers) sways slowly; for
#   underwater or wind (amplitude <= 4 px, period >= 2 s; lint checks).
# Cut only for a reason: a new place, a detail (close-up, hero at least 2x bigger), someone else's reaction (camera really
# changes direction). Hard-cutting in the same place from the same direction while only the size changes (wide -> medium ->
# medium-close) looks like the picture zooming in and out; shots_lint reports it (zoom cut). Do not pad shot counts or shot
# sizes; one shot can play 6–10 s.
N = P(DUR)
MEDIUM_K = 1.5                      # the stool shot (medium): Pip 1.33x his wide-shot size
T1, T2, T3, T4, T5 = P(10.5), P(15.8), P(23.0), P(31.0), P(37.5)
# ground lines measured on the backgrounds (stage = frame coords)
G0, G1, G2, G3, G5 = 905, 990, 960, 1012, 985
STOOL_X = 560

SHOTS = [
    dict(at=0, size='wide', name='lesson', bg='class_wide', place='classroom', view='front', k=1.0, ground=G0, key=True,
         cam=[(0, 960, 540, 1.0), (P(6.0), 960, 540, 1.0), (T1 - 1, 900, 600, 1.08)]),
    dict(at=T1, size='medium', name='stool', bg='class_corner', place='classroom', view='reverse', k=MEDIUM_K, ground=G1, min=0.33,
         size_ok='the hero lies flat on his belly for half the shot (standing he is ~54% of the frame height)',
         cam=[(0, 960, 540, 1.0), (P(2.6), 960, 540, 1.0), (P(4.2), 1010, 570, 1.05)]),
    dict(at=T2, size='medium', name='run', bg='class_floor', place='classroom', view='side', k=1.5, ground=G2, min=0.30,
         size_ok='the hero runs bent forward then slides lying flat (standing he would be ~54%)',
         cam=[(0, 889, 540, 1.08), (T3 - T2 - 1, 1031, 560, 1.08)],
         cut_ok='real change of view: front wall -> back corner -> side view along the floor -> close under the window; '
                'each a different camera direction, hero side and set'),
    dict(at=T3, size='medium-close', name='window', bg='class_window', place='classroom', view='window', k=1.0, ground=G3,
         cam=[(0, 960, 540, 1.0), (T4 - T3 - 1, 900, 580, 1.08)]),
    dict(at=T4, size='wide', name='hill', bg='hill_wide', place='hill', view='front', k=1.15, ground=900,
         cam=[(0, 873, 491, 1.1), (T5 - T4 - 1, 1047, 589, 1.1)]),
    dict(at=T5, size='medium-close', name='landing', bg='hill_bottom', place='hill', view='bottom', k=1.0, ground=G5, key=True,
         cam=[(0, 960, 540, 1.0), (N - T5 - 1, 960, 560, 1.04)],
         cut_ok='checked the cut sheet: hero goes from a small slider on the slope to a big lying close-up (about 2x), '
                'camera down at snow level at the bottom; reads as arriving, not a zoom'),
]


def _seq(items):
    """[(cell, drawings, extra state or f(i) -> state), ...] -> one dict per drawing"""
    out = []
    for cell, n, ex in items:
        for i in range(max(1, n)):                      # n = 0: one drawing here, _fit holds it to the end of the shot
            st = dict(ex(i) if callable(ex) else (ex or {})); st['c'] = cell; out.append(st)
    return out


def _fit(track, n):
    track = track[:n]
    while len(track) < n: track.append(dict(track[-1], sfx=None))
    return track


def hill_path(u):
    """Pip's belly-slide path down the slope in the hill shot: u 0..1 -> (x, y)"""
    x = 230 + 1560 * u
    return x, 600 + (x - 230) * 0.265


def build():
    ts = animi.Timesheet(fps=FPS, on=ON, seed=7)
    _add0 = ts.add
    ts.add = lambda c, **st: _add0(c, **{k: v for k, v in st.items() if v is not None})
    # ---------------- shot 0: lesson (wide). Owl on the right (mirrored, facing left), Pip on the left facing right
    PX, OX = 700, 1290
    pip = _seq([('look_0', 15, {}), ('look_1', 2, {}), ('look_2', 2, dict(lift=15)), ('look_3', 1, dict(lift=50)),
                ('look_3', 2, dict(lift=40)), ('look_4', 3, dict(sfx=('step', 0.3, 1.4))), ('look_0', 26, {}),
                ('look_5', 8, {}), ('look_6', 6, {}), ('look_7', 4, {}), ('look_6', 4, {}),
                ('flap_0', 6, {}), ('flap_1', 4, {}), ('flap_2', 2, dict(lift=10)), ('flap_3', 2, dict(lift=30, sfx=('rub', 0.3, 1.3))),
                ('flap_4', 2, dict(lift=36)), ('flap_3', 2, dict(lift=24, sfx=('rub', 0.3, 1.4))), ('flap_4', 2, dict(lift=12)),
                ('flap_5', 2, dict(sfx=('step', 0.35, 1.3))), ('flap_6', 8, dict(sfx=('thud', 0.55, 1.3))), ('flap_7', 0, {})])
    hov = lambda i: dict(ol=60 + 80 * kit.ease(min(1.0, i / 10)), sfx=('whoosh', 0.18, 1.6) if i % 4 == 0 else None)
    owl = _seq([('owl_0', 4, {}), ('owl_1', 3, {}), ('owl_2', 2, dict(ol=25, sfx=('whoosh', 0.25, 1.3)))]
               + [(f'owl_{3 + (j // 2) % 2}', 1, (lambda j: (lambda i: hov(j)))(j)) for j in range(30)]
               + [('owl_5', 1, dict(ol=90)), ('owl_5', 1, dict(ol=45)), ('owl_5', 1, dict(ol=15)),
                  ('owl_6', 4, dict(sfx=('thud', 0.35, 0.9))), ('owl_0', 2, {}), ('owl_7', 19, {}), ('owl_0', 27, {}),
                  ('owl_1', 3, {}), ('owl_0', 7, {}), ('owl_6', 2, {}), ('owl_7', 14, dict(sfx=('rub', 0.25, 0.9))), ('owl_0', 0, {})])
    n0 = T1
    pip = _fit(pip, n0)
    owl = _fit(owl, n0)
    for k in range(n0):
        p, o = pip[k], owl[k]
        st = dict(x=PX, lift=p.get('lift', 0), o=o['c'], ox=OX, ol=o.get('ol', 0), oflip=True, cells=[o['c']],
                  beat='setup' if k < P(5.5) else 'try1', warm=0.35,
                  rep_ok='watching the owl twice, around one bounce; not a loop')
        sfx = p.get('sfx') or o.get('sfx')
        if sfx: st['sfx'] = sfx
        ts.add(p['c'], **st)
    # ---------------- shot 1: stool (medium). Pip on the stool, leaps right, belly-flops on the rug
    n1 = T2 - T1
    jump = [('jump_0', 10, dict(x=STOOL_X, on_stool=1)), ('jump_1', 6, dict(x=STOOL_X, on_stool=1)),
            ('jump_2', 2, lambda i: dict(x=STOOL_X + 50 + 40 * i, air=1.0, lift=0, sfx=('whoosh', 0.3, 1.2) if i == 0 else None)),
            ('jump_3', 3, lambda i: dict(x=STOOL_X + 150 + 70 * i, air=1.0, lift=40 - 15 * i)),
            ('jump_4', 2, lambda i: dict(x=STOOL_X + 360 + 60 * i, air=0.45 - 0.35 * i, lift=0)),
            ('jump_5', 3, lambda i: dict(x=1060, shake=[7, 3, 0][i], puff=i, sfx=('thud', 0.7, 1.15) if i == 0 else None)),
            ('jump_5', 3, lambda i: dict(x=1060, puff=3 + i, sfx=('puff', 0.4, 1.2) if i == 0 else None)),
            ('jump_6', 14, lambda i: dict(x=1060, puff=6 + i if i < 2 else None)), ('jump_7', 0, dict(x=1060))]
    for st in _fit(_seq(jump), n1):
        c = st.pop('c'); st['beat'] = 'try2'; ts.add(c, **st)
    # ---------------- shot 2: run (wide). Run right, leap, belly-land, slide to the wall under the window
    n2 = T3 - T2
    run = [('look_6', 6, dict(x=150)), ('look_7', 4, dict(x=150, sfx=('rub', 0.25, 1.4)))]
    run += [(f'run_{j % 2}', 1, (lambda j: (lambda i: dict(x=150 + 15 * j, sfx=('step', 0.32, 1.35) if True else None)))(j))
           for j in range(30)]
    run += [('run_2', 2, lambda i: dict(x=600 + 20 * i)), ('run_3', 2, lambda i: dict(x=650 + 40 * i, lift=40 + 40 * i)),
            ('run_4', 3, lambda i: dict(x=730 + 40 * i, lift=[110, 125, 112][i])),
            ('run_5', 2, lambda i: dict(x=850 + 40 * i, lift=[70, 25][i])),
            ('run_6', 2, lambda i: dict(x=930 + 35 * i, puff=i, shake=[5, 0][i], sfx=('thud', 0.6, 1.2) if i == 0 else None))]
    x = 965.0
    for j in range(18):
        v = 34 - 27 * j / 17; x += v
        run.append(('run_6', 1, (lambda x, j: (lambda i: dict(x=x, puff=2 + j if j < 6 else None,
                                                             sfx=('rub', 0.35, 1.2) if j in (0, 6) else None)))(x, j)))
    run += [('run_6', 1, dict(x=x + 4, shake=4, sfx=('tap', 0.5, 0.9))), ('run_7', 0, dict(x=x + 4))]
    for st in _fit(_seq(run), n2):
        c = st.pop('c'); st['beat'] = 'try3'; st['rep_ok'] = 'run-up crossing the whole floor'; ts.add(c, **st)
    # ---------------- shot 3: window (medium-close). Low point, then the idea
    n3 = T4 - T3
    win = [('sad_0', 16, {}), ('sad_1', 3, {}), ('sad_0', 12, {}), ('sad_1', 24, dict(sfx=('rub', 0.25, 0.8))), ('sad_2', 8, {}), ('sad_3', 0, {})]
    for st in _fit(_seq(win), n3):
        c = st.pop('c'); ts.add(c, x=600, beat='low' if c in ('sad_0', 'sad_1') else 'turn', warm=0.55, live='snow falling past the window, slow push',
                   rep_ok='one sigh-blink then a long sigh; not a loop')
    # ---------------- shot 4: hill (wide). Belly slide down the slope, owl flying above
    n4 = T5 - T4
    for k in range(n4):
        u = (k / (n4 - 1)) ** 1.25
        x, y = hill_path(u)
        oc = f'owl_{3 + (k // 2) % 2}' if k < 34 else 'owl_4'
        st = dict(x=x, gy=y, o=oc, ox=420 + 12.0 * k, oy=600 + (420 + 12.0 * k - 230) * 0.265 - 60, ol=250 - 0.8 * k, os=0.62,
                  oflip=False, cells=[oc],
                  spray=k % 8, beat='payoff', rep_ok='slide cycle: travelling across the whole slope',
                  sfx=('rub', 0.45, 1.0) if k % 12 == 0 else (('whoosh', 0.2, 1.4) if k % 4 == 1 and k < 34 else None))
        ts.add(f'slide_{[0, 1, 2, 5, 3, 6, 4, 7][k % 8]}', **st)
    # ---------------- shot 5: landing (medium-close). Lying in the snow beaming; owl lands behind on the left
    n5 = N - T5
    joy = _seq([('joy_0', 8, {}), ('joy_1', 6, {}), ('joy_2', 6, {}), ('joy_3', 0, {})])
    owl5 = _seq([('owl_5', 1, dict(ol=260)), ('owl_5', 1, dict(ol=190)), ('owl_5', 1, dict(ol=130)), ('owl_5', 1, dict(ol=80)),
                 ('owl_5', 1, dict(ol=40)), ('owl_5', 1, dict(ol=12)), ('owl_6', 4, dict(sfx=('puff', 0.4, 0.8))), ('owl_0', 0, {})])
    joy, owl5 = _fit(joy, n5), _fit(owl5, n5)
    for k in range(n5):
        st = dict(x=1130, o=owl5[k]['c'], ox=520, oy=760, ol=owl5[k].get('ol', 0), oflip=False, os=0.62, cells=[owl5[k]['c']],
                  beat='button')
        if k == 0: st['sfx'] = ('puff', 0.6, 1.0)
        elif owl5[k].get('sfx'): st['sfx'] = owl5[k]['sfx']
        ts.add(joy[k]['c'], **st)
    return ts


# =====================================================================================
# 3. Draw one drawing: every random value, camera and environment is keyed by drawing number pic
# =====================================================================================
def put(frame, D, cam, name, x, y, s, pic, ts, hero=None, main=True, idle=False, lift=0.0, sh=None, light=None, jit=1.0,
        salt=None, shade=None, rot=0.0, **kw):
    """Place one character: shadow per style (contact shadow / thin close shadow / hard-light cast shadow) -> lighting per
    style -> paste by anchor.
    name: cell name; with a suffix like "~b", uses the same-named variant in D['cells'] (recoloured with animi.recolor in
          load()) if there is one, else the base cell (it only tells lint this is a different picture).
    x, y: stage coordinates (foot point); s: cell -> stage scale (camera excluded; close-ups also times the shot's k);
    lift: height above ground px (airborne: shadow smaller and fainter);
    rot: extra tilt for this drawing in degrees (for falls, hits; not rocking back and forth as a fake "live hold").
    idle=True: this drawing is part of a long hold; soft materials breathe (rigid ones do not). hero: dict passed in by
    draw(), records what this drawing shows (long-hold check); for main=True (the hero) the bounding box is recorded too
    (size and darkness checks); supporting characters use main=False.
    sh: current shot (when the style has light.floor, brightness follows this shot's background light zones).
    light: this drawing's lighting, overriding the automatic values: dict(warm=0.6, warm_side='left', gain=0.8,
           scale=2.2, floor=False); preset.light keys can be changed too (side=[1.2, 0.5], rim=0.3); False = no lighting.
           scale defaults to the reference sheet's sc / this sheet's sc (close-up sheets drawn N times bigger get N times
           wider rim and defringe).
    jit: jitter multiplier (props, supporting characters 0.5: less tilt; 0 no jitter). salt: jitter seed, by sheet name by
    default (each character, each paper piece jitters on its own).
    shade: this cell's shadow, overriding the style's: dict(w=0.62, off=(0.06, 0), k=0.3) (contact shadow width and offset
    as a fraction of character width; k darkness); False = no shadow.
    -> bounding box in the frame"""
    base = animi.cell_base(name); sheet_ = base.rsplit('_', 1)[0]
    key = name if name in D['cells'] else base                        # variant cell ('walk_3~b'): use it if registered
    c, info = D['cells'][key], D['info'].get(key, D['info'].get(base))
    salt = salt or sheet_
    if rot: kw['rot'] = kw.get('rot', 0.0) + rot
    X, Y = cam.xy(x, y)
    jx, jy = ts.jitter(pic, STYLE.get('jitter_pos', 0) * jit, salt=f'pos:{salt}')
    s = s * cam.k() * ts.jscale(pic, STYLE.get('jitter_scale', 0) * jit, salt=f'scale:{salt}')
    if idle: kw.update(ts.idle(pic, STYLE.get('idle', 0.012), rigid=RIGID, salt=sheet_))
    if main and 0 <= pic < ts.n_pics and animi.cell_base(ts.pics[pic][0]) == base:      # landing on a held pose: settle (soft materials)
        st = ts.settle(pic, STYLE.get('settle', 0.03), rigid=RIGID, shot_at=sh['at'] if sh else 0)
        if st: kw['sy'] = kw.get('sy', 1.0) * st['sy']; kw['sx'] = kw.get('sx', 1.0) * st['sx']
    if STYLE.get('jitter_rot') and jit: kw['rot'] = kw.get('rot', 0.0) + ts.jrot(pic, STYLE['jitter_rot'] * jit, salt=f'rot:{salt}')
    if TOP_DOWN and info.get('core') and 'ref' not in kw:
        kw['ref'] = (info['core']['cx'], info['core']['cy'])         # top-down: place by body core and rotate around it
    if shade is not False:
        sk = dict(shadow_w=(shade or {}).get('w'), shadow_off=(shade or {}).get('off'), shadow_k=(shade or {}).get('k'))
        animi.shadow(frame, c, X + jx, Y + jy, s, info, style=STYLE, lift=lift, **sk, **kw)
    if LIGHT and light is not False:
        q = dict(scale=None, warm=0.0, warm_side='left', gain=1.0, floor=True); q.update(light or {})
        cfg = dict(LIGHT, **{k: v for k, v in q.items() if k in animi.LIGHT})     # e.g. light=dict(side=[1.2, 0.5]): change this drawing's lighting params
        if q['scale'] is None:
            ref = D['sc'].get(D.get('ref')) if D.get('ref') else None
            q['scale'] = (D.get('lscale') or {}).get(sheet_) or (ref / D['sc'][sheet_] if ref and D['sc'].get(sheet_) else 1.0)
        c = animi.char_light(c, cfg, scale=float(np.clip(q['scale'], 0.25, 6)), warm=q['warm'], warm_side=q['warm_side'],
                             gain=q['gain'], flip=kw.get('flip', False))
        if LIGHT.get('floor') and q['floor'] and sh is not None and 'gain' not in kw:
            kw['gain'] = animi.floor_light(D['plates'][sh['bg']], sh['ground'], cam, LIGHT)
    box = animi.place_at(frame, c, X + jx, Y + jy - lift * cam.k(), s, info=info, **kw)
    if main: _cut_check(sheet_, c, info, box, frame.shape[0], D)
    if hero is not None:
        if main: hero['box'] = animi.hero_box(box, info, scale=s, at=(X + jx, Y + jy - lift * cam.k())) if TOP_DOWN \
            else animi.hero_box(box, info)
        hero.setdefault('drawn', []).append(name)
    return box


_CUT_WARNED = set()


def _cut_check(sheet_, c, info, box, H_, D):
    """A cut edge on the hero's body (a close-up sheet cropped at the chest: the bottom is one flat strip) showing inside
    the frame looks like a cut-out half-body sticker. The edge must sit outside the bottom of the frame (at least 3%
    below), otherwise shoot the full body. Flat-bottomed characters (a box, a pot) standing on the ground are fine: let
    them through with D['flat_ok'] = {'sheet name'} in load()."""
    if sheet_ in _CUT_WARNED or sheet_ in D.get('flat_ok', ()): return
    a = c[1]; x0, y0, x1, y1 = [int(v) for v in info['bbox']]
    if y1 - y0 < 8 or x1 - x0 < 8: return
    yb = int(np.nonzero((a[y0:y1 + 1, x0:x1 + 1] > 0.5).any(1))[0].max()) + y0
    flat = (a[max(y0, yb - 2):yb + 1, x0:x1 + 1] > 0.5).any(0).mean()
    if flat >= 0.35 and box[3] < H_ * 1.03:
        _CUT_WARNED.add(sheet_)
        print(f'medium-close: "{sheet_}" has a flat cut edge at the bottom inside the frame (bottom {box[3]:.0f} / frame height {H_}); '
              f'it looks like a cut-out half-body sticker. Shoot medium-close shots full body (head to feet in frame, standing on '
              f'the ground); for a real close-up put the cut edge below the frame. Flat-bottomed character standing on the ground: '
              f"D['flat_ok'] = {{'{sheet_}'}} in load()", file=sys.stderr)


def draw_layers(frame, D, cam, sh, pic, front):
    """This shot's set layers from SHOTS (layers=[dict(name=, par=, x0=, y_top=, width=, front=, bob=, sy=, dy=, phase=), ...]).
    sy, dy, x0 may be functions lambda k: ..., k = drawing within the shot (from 0): paper layer standing up
    sy=lambda k: min(1, 1.1 * kit.ease_out(k / 8)), set layer sliding in x0=lambda k: -600 + 60 * min(k, 10).
    bob=(amplitude, period) is added on top of dy.
    Layers not loaded in load() (name not in D['layers']) are skipped here; lint reports them."""
    k = pic - sh['at']
    f = lambda v: v(k) if callable(v) else v
    for L in sh.get('layers', []):
        if bool(L.get('front')) != front or L['name'] not in D['layers']: continue
        amp, per = L.get('bob', (0, 20))
        dy = f(L.get('dy', 0.0)) + (layers.bob(pic, amp, per, L.get('phase', 0.0)) if amp else 0.0)
        layers.put_layer(frame, cam, D['layers'][L['name']], L.get('par', 1.0), f(L['x0']), L['y_top'], L['width'],
                         sy=f(L.get('sy', 1.0)), dy=dy, shadow=L.get('shadow', 0.38), mul=L.get('mul', 1.0))


def sway_cam(cam, sway, k):
    """The whole set (background + set layers; characters move with the ground) sways gently: the camera centre drifts per
    drawing. sway=(amplitude px, period in drawings): main horizontal swing + a smaller vertical one (offset periods), not
    a regular sine. For a current-pushed seabed or a windy meadow; 4–10 px amplitude is enough."""
    amp, per = float(sway[0]), float(sway[1])
    dx = amp * (math.sin(2 * math.pi * k / per) + 0.4 * math.sin(2 * math.pi * k / (0.61 * per) + 1.0))
    dy = 0.35 * amp * math.sin(2 * math.pi * k / (0.73 * per) + 2.0)
    cam.cx += dx / cam.k(); cam.cy += dy / cam.k()


def shake_cam(cam, amp, pic):
    """Impact / landing jolt: the frame drops amp px (once, one direction, not side to side or back and forth). Write it
    in the timesheet state: ts.add('land_0', shake=8), only on the 1–2 impact drawings with decreasing amplitude (8, 3);
    the next drawing is back in place. Never on a whole segment, never alternating direction."""
    cam.cy -= float(amp) / cam.k()


def _pip_sc(D, cell):
    return D['sc'][animi.cell_base(cell).rsplit('_', 1)[0]]


def render(pic, st, shots, ts, D, hero=None):
    """Pip Flies: background -> snow seen through windows -> owl -> props -> Pip -> fx -> snowfall (outdoors)."""
    cell, _, s = st
    cam, sh = animi.cam_at(shots, pic, W, H)
    if s.get('shake'): shake_cam(cam, s['shake'], pic)
    frame = cam.plate(D['plates'][sh['bg']], par=PAR)
    name, K = sh['name'], sh.get('k', 1.0)
    if sh['bg'] in D['win']:                                        # snow falling outside, only inside the window panes
        big = sh['name'] == 'window'
        cp = D['snow'].draw(frame.copy(), D['env'], pic, amount=1.5 if big else 0.9, wind=1.6 if big else 1.2, cam=cam,
                            size=1.1 if big else 0.55)
        m = cam.plate(D['win'][sh['bg']], par=PAR)[..., :1]
        frame = frame * (1 - m) + cp * m
    if s.get('o'):                                                  # the owl teacher (supporting character)
        oy = s.get('oy', sh['ground'])
        put(frame, D, cam, s['o'], s['ox'], oy, D['sc']['owl'] * K * s.get('os', 1.0), pic, ts, hero, main=False,
            lift=s.get('ol', 0.0), sh=sh, jit=0.5, flip=s.get('oflip', False), anchor='body',
            light=dict(warm=0.25 if name == 'lesson' else 0.0, warm_side='left', flip=s.get('oflip', False)))
    gy, lift = s.get('gy', sh['ground']), s.get('lift', 0.0)
    rot = 0.0
    if name == 'stool':
        sc_st = D['sc']['stoolprop']; st_h = D['info']['stoolprop_0']['height'] * sc_st
        put(frame, D, cam, 'stoolprop_0', STOOL_X, sh['ground'], sc_st, pic, ts, None, main=False, jit=0, anchor='body',
            shade=dict(k=0.3), light=dict(warm=0.0))
        seat = sh['ground'] - st_h * 0.93
        if s.get('on_stool'): gy = seat
        elif s.get('air') is not None: lift = lift + s['air'] * (sh['ground'] - seat)
    if name == 'hill':
        rot = 15.0
        sp = f"spray_{s.get('spray', 0)}"
        put(frame, D, cam, sp, s['x'] - 150 * K, gy + 10, D['sc']['spray'] * K, pic, ts, None, main=False, shade=False,
            anchor=0.5, jit=0)
    put(frame, D, cam, cell, s.get('x', 0), gy, _pip_sc(D, cell) * K, pic, ts, hero, idle=s.get('idle', False),
        anchor='body', lift=lift, sh=sh, rot=rot,
        light=dict(warm=s.get('warm', 0.0), warm_side='left'))
    if s.get('puff') is not None and 0 <= s['puff'] < 8:
        put(frame, D, cam, f"puff_{s['puff']}", s.get('x', 0), sh['ground'] + 6, D['sc']['puff'] * K, pic, ts, None,
            main=False, shade=False, anchor=0.5, jit=0)
    if sh['place'] == 'hill':                                       # full-screen snowfall outdoors
        frame = D['snow'].draw(frame, D['env'], pic, amount=1.1 if name == 'hill' else 0.8, wind=2.5, cam=cam)
    return frame


def _shot_of(pic):
    return max(i for i, s in enumerate(SHOTS) if s['at'] <= pic)


def _tr(j, D):
    """transition at the start of shot j -> tr_spec (tr= / smear= / mix= all map to transition families, see animi.shot_tr)"""
    return None if j == 0 else animi.shot_tr(SHOTS[j], INFO, D.get('assets'))


def _old(i, d, ts, D):
    """the old shot's picture for drawing d after the cut: holds on the old shot's last drawing by default; with
    mix(live=True) the old shot keeps acting"""
    pic = SHOTS[i]['at'] + d; last = SHOTS[i]['at'] - 1
    q = _tr(i, D)
    if q and q.get('live'):
        f = SHOTS[i - 1].get('carry')
        st = (lambda r: (r[0], 0, r[1]))(f(d)) if f else ts.carry(last, d)
    else: st = ts.pics[last]
    return np.ascontiguousarray(render(pic, st, SHOTS[:i], ts, D), np.float32)


def draw(pic, ts, D, hero=None):
    """One final drawing: this shot -> transition (before the grade) -> style finish -> shot in / out wipes + subtitles.
    Usually no need to edit."""
    pic = min(pic, ts.n_pics - 1)
    j = _shot_of(pic)
    frame = np.ascontiguousarray(render(pic, ts.pics[pic], SHOTS, ts, D, hero), np.float32)
    glow = 0.0
    for i in (j, j + 1):                                               # transition after a cut belongs to this shot; before a cut, to the next shot
        if i >= len(SHOTS) or i == 0: continue
        q = _tr(i, D)
        if not q: continue
        d = pic - SHOTS[i]['at']
        if not (-q['before'] <= d < q['after']): continue
        old = _old(i, d, ts, D) if d >= 0 and q['kind'] in animi.TR_NEEDS_OLD else None
        frame = animi.cut_fx(q, d, frame, old)
        glow = max(glow, animi.tr_glow(q, d))
    frame = np.clip(animi.finish(frame, ts, pic, STYLE, glow=glow), 0, 1)
    return post(frame, pic, ts, D)


def post(frame, pic, ts, D):
    """shot in / out transitions (inn / out, animi.transition) + subtitles (usually no need to edit)"""
    j = _shot_of(pic)
    sh = SHOTS[j]; end = SHOTS[j + 1]['at'] if j + 1 < len(SHOTS) else ts.n_pics
    if sh.get('inn') and pic - sh['at'] < sh['inn'][1]:
        animi.transition(frame, sh['inn'][0], (pic - sh['at'] + 1) / sh['inn'][1])
    if sh.get('out') and end - pic <= sh['out'][1]:
        animi.transition(frame, sh['out'][0], 1 - (end - pic - 1) / sh['out'][1])
    if D.get('subs') is not None:
        frame = D['subs'].draw(frame, ts.pic_start(pic) / FPS)
    return frame


# =====================================================================================
# 4. Render and check (usually no need to edit)
# =====================================================================================
_G = {}
def _init():
    cv2.setNumThreads(1)
    _G['ts'] = build(); _G['D'] = load()
    sp = os.path.join(WK, 'audio', 'subs.json')
    d = sound_sheet()
    cues = json.load(open(sp)) if os.path.exists(sp) and (d is None or d.get('vo')) else []   # no narration: no subtitles (ignore a leftover subs.json)
    _G['D']['subs'] = animi.Subtitles(cues, SUB_STYLE, W, H) if cues else None


def _render_pic(args):
    pic, mode = args
    hero = {}
    f = draw(pic, _G['ts'], _G['D'], hero)
    box = hero.get('box')
    hh = (box[3] - box[1]) if box else 0.0
    lum = animi.brightness(f, box)
    stat = dict(h=hh, box=[round(float(v), 1) for v in box] if box else None, lum=lum, drawn=tuple(hero.get('drawn', [])))
    if mode == 'board':
        f = cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
        f8 = np.ascontiguousarray((np.clip(f, 0, 1) * 255).astype(np.uint8))
        cv2.putText(f8, str(pic), (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        return pic, (f8.astype(np.float32) / 255, stat)
    starts = [fr['i'] for fr in _G['ts'].frames() if fr['pic'] == pic]
    for i in starts: kit.wr(f'{FRAMES}/f{i:04d}.png', f)                # on twos: one drawing written as two frames
    return pic, (None, stat)


def lint(ts, hero=None, drawn=None):
    """-> failed items. hero / drawn: measurements passed in after board and final renders (median hero height, what
    each drawing shows)"""
    print(f'length {ts.duration():.2f}s, {ts.n_pics} drawings, {W}×{H}, style {STYLE.get("en") or STYLE["name"]}', file=sys.stderr)
    beats = {}
    for cell, holds, st in ts.pics: beats.setdefault(st.get('beat', '?'), []).append(cell)
    for b, cs in beats.items(): print(f'  beat "{b}": {len(cs)} drawings, {len(set(cs))} distinct cells', file=sys.stderr)
    D_ = {}
    try: D_ = _G.get('D') or load(); plates = D_['plates']      # backgrounds go to shots_lint too: a renamed, near-identical background still counts as a jump cut
    except Exception as e: plates = None; print(f'shots_lint: backgrounds failed to load ({e})', file=sys.stderr)
    holds = ts.lint(drawn=drawn)     # long holds are reminders: code cannot see a "live hold" (camera push, steam); after checking write live='reason'
    if holds: print(f'lint reminder: {len(holds)} places hold the same picture over 2 s; check each for something else moving '
                    f'(small local move, supporting character, environment, camera); fix dead holds', file=sys.stderr)
    bad = animi.shots_lint(SHOTS, ts, plates=plates, hero=hero, push_max=STYLE.get('push_max'))
    bad += animi.style_lint(STYLE_ID)                            # style package basics (no jitter, no flicker, cards filled in)
    bad += animi.repeat_report(SHOTS, ts)                       # same action replayed unchanged, cycle running too long; after checking write rep_ok='reason'
    trb = animi.tr_missing(SHOTS, INFO, D_.get('assets'))      # wrong transition, missing assets
    for m in trb: print(f'transition: {m}', file=sys.stderr)
    bad += trb
    for j, sh in enumerate(SHOTS):                              # set sway must be slow and small: fast back-and-forth reads as a shaking background
        if sh.get('sway') and (float(sh['sway'][0]) > 4 or float(sh['sway'][1]) * ON / FPS < 2.0):
            m = f"set sway: shot {j} \"{sh.get('name', '')}\" sway={tuple(sh['sway'])} too fast or too big (need <= 4 px, period >= 2 s = {int(2 * FPS / ON)} drawings)"
            print(m, file=sys.stderr); bad.append(m)
    for j, sh in enumerate(SHOTS):                              # set layers named in SHOTS must be loaded in load() (otherwise silently not drawn)
        for L in sh.get('layers', []):
            if L.get('name') not in (D_.get('layers') or {}):
                m = f"set layer: shot {j} \"{sh.get('name', '')}\" names layers name='{L.get('name')}', but load()'s layers lacks it (not drawn)"
                print(m, file=sys.stderr); bad.append(m)
    if plates is None: bad.append('not checked: background similarity (jump cuts); make load() read the backgrounds, then lint')
    miss = animi.missing_report()
    if miss: bad.append(f'missing images: {len(miss)} still _bad versions or placeholders (see above); generate them before delivery')
    d = sound_sheet()
    if d is None:
        print('sound: no sound.json (films have sound by default; only without it if the user explicitly asked for silent)', file=sys.stderr)
    elif abs(ts.duration() - float(d['dur'])) > 0.15:
        bad.append(f"timesheet {ts.duration():.2f}s and sound sheet {float(d['dur']):.2f}s differ in length")
        print(f'sound: {bad[-1]}', file=sys.stderr)
    p = animi.write_shots(f'{WORK}/shots.json', SHOTS, ts, FPS)
    print(f'shot list: {os.path.relpath(p, WK)} (sound.json can time cues by shot)', file=sys.stderr)
    return bad


def checks(ts, stats):
    """checks after rendering: hero size (big enough, matching across cuts), darkness, jump cuts and long holds re-checked
    on measurements"""
    heights = {p: stats[p]['h'] for p in stats}
    small, med = animi.hero_report(SHOTS, heights, SHORT, STYLE)
    drawn = {p: stats[p]['drawn'] for p in stats if stats[p]['drawn']}
    bad = lint(ts, hero=med, drawn=drawn or None)
    bad += animi.size_report(SHOTS, ts, heights, med)           # hero size matches across adjacent shots; after checking write size_ok='reason'
    samples = [(ts.pic_start(p) / FPS,) + tuple(stats[p]['lum']) for p in sorted(stats)]
    dark = animi.dark_spans(samples, STYLE.get('dark'))
    bad += [f'hero too small: shot {j}' for j in small] + [f'too dark: {d:.2f}s from {t0:.2f}s' for t0, d, _ in dark]
    if bad: print(f'checks: {len(bad)} failed (see above)', file=sys.stderr)
    return bad


def main(argv):
    mode = argv[0] if argv else 'film'
    ts = build()
    if mode == 'lint':
        bad = lint(ts)
        if bad: print(f'lint: {len(bad)} failed (see above); fix before rendering', file=sys.stderr); sys.exit(1)
        print('lint: all passed', file=sys.stderr); return
    os.makedirs(WORK, exist_ok=True); os.makedirs(FRAMES, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    if mode == 'still':
        _init()
        for p in map(int, argv[1:] or ['0']):
            kit.wr(f'{WORK}/still_{p:03d}.png', draw(p, _G['ts'], _G['D'])); print(f'{WORK}/still_{p:03d}.png')
        return
    if mode != 'board':
        for f in os.listdir(FRAMES):
            if f.endswith('.png'): os.remove(os.path.join(FRAMES, f))
    jobs = [(p, mode) for p in range(ts.n_pics)]
    with Pool(max(1, (os.cpu_count() or 4) - 1), initializer=_init) as pool:
        res = dict(pool.map(_render_pic, jobs, chunksize=4))
    stats = {p: res[p][1] for p in res}
    load()                                              # load assets again in the main process: missing images are recorded here
    if mode == 'board':
        tiles = [res[p][0] for p in range(ts.n_pics)]
        cols = 8; rows = math.ceil(len(tiles) / cols)
        grid = np.ones((rows * (H // 4), cols * (W // 4), 3), np.float32)
        for k, t in enumerate(tiles): grid[(k // cols) * (H // 4):(k // cols + 1) * (H // 4), (k % cols) * (W // 4):(k % cols + 1) * (W // 4)] = t
        kit.wr(f'{WORK}/board.jpg', grid)
        for old in glob.glob(f'{WORK}/board_p*.jpg'): os.remove(old)
        tw = 320; th = int(round(H * tw / W)); pages = []          # pages under 2000 px for agents that can't open the big sheet
        for i in range(0, len(tiles), 48):
            chunk = tiles[i:i + 48]; pr = math.ceil(len(chunk) / 6)
            pg = np.ones((pr * th, 6 * tw, 3), np.float32)
            for k, t in enumerate(chunk): pg[(k // 6) * th:(k // 6 + 1) * th, (k % 6) * tw:(k % 6 + 1) * tw] = cv2.resize(t, (tw, th), interpolation=cv2.INTER_AREA)
            pages.append(f'{WORK}/board_p{len(pages) + 1}.jpg'); kit.wr(pages[-1], pg)
        tmp = f'{WORK}/board_frames'; os.makedirs(tmp, exist_ok=True)
        for k, t in enumerate(tiles): kit.wr(f'{tmp}/f{k:04d}.png', t)
        kit.encode(tmp, f'{WORK}/board.mp4', fps=FPS / ON, crf=23)
        print(f'{WORK}/board.jpg  {WORK}/board.mp4  pages: {WORK}/board_p1.jpg ... board_p{len(pages)}.jpg (48 drawings each, under 2000 px)'); checks(ts, stats); return
    draft = bool(animi.MISSING)                         # missing images: draft only, no official out/<NAME>.mp4
    silent = f'{WORK}/_silent.mp4'; mp4 = f'{WORK}/{NAME}-draft.mp4' if draft else f'{OUT}/{NAME}.mp4'
    kit.encode(FRAMES, silent, fps=FPS, crf=18)
    mix = os.path.join(WK, 'audio', 'mix.wav')
    if os.path.exists(mix):
        subprocess.run([sys.executable, os.path.join(SKILL, 'sound.py'), 'mux', silent, mix, mp4], check=True)
    else:
        shutil.copy(silent, mp4)
        print('sound: no audio/mix.wav, the film is silent (run sound.py build first; silent only if the user asked for it)', file=sys.stderr)
    animi.write_shots(os.path.splitext(mp4)[0] + '.shots.json', SHOTS, ts, FPS)     # shot list: for the review page and selfcheck
    boxes = [[round(ts.pic_start(p) / FPS, 3), stats[p]['box']] for p in sorted(stats)]
    json.dump(dict(fps=FPS, boxes=boxes), open(f'{WORK}/hero.json', 'w'))             # hero box per drawing: for selfcheck's darkness check
    print(mp4)
    if draft: print(f'draft: {len(animi.MISSING)} images not generated yet (see above); this version cannot be delivered', file=sys.stderr)
    checks(ts, stats)
    r = animi.liveness(mp4, out=f'{WORK}/liveness.png')
    for t0, d, m in r['quiet']:
        print(f'liveness: [WARN] {d:.2f}s from {t0:.2f}s the picture barely moves ({m:.3f}); see work/liveness.png. '
              'Over 2 s needs a local move (blink, ear, tail), a supporting character or the environment (a slow push alone does not count); fix it or list it with review.py add --known', file=sys.stderr)


if __name__ == '__main__':
    main(sys.argv[1:])
