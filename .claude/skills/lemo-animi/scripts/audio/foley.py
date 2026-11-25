"""lemo-animi foley: action sounds synthesized per material (numpy, no downloads). Every function returns mono float32 @ SR.

In the sound sheet sound.json: "foley": [{"t": 3.2, "kind": "thud", "v": 0.8, "pan": -0.2, "pitch": 1.0, "d": 0.6}, ...]
kind looks up "<style material>_<kind>" first (e.g. clay_thud), then the generic kind (e.g. whoosh), then aliases (e.g. snow -> crunch).
d (seconds) applies only to sustained sounds (flow, rub, smear, creak, whoosh, rip, rustle); ignored otherwise.
kinds(material) lists every name this material can use (aliases included); describe(material) adds a one-line description.
"""
import numpy as np
from .sfx import SR, t_, env_exp, bp, lp, hp, noise, norm

_rng = np.random.default_rng(11)


def _tone(f, d, tau, v=1.0):
    t = t_(d); return np.sin(2 * np.pi * f * t) * np.exp(-t / tau) * v


def _sweep(f0, f1, d, tau):
    t = t_(d); f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau)


def _fade(x, ms=4):
    n = min(len(x), int(ms * SR / 1000)); x = x.copy(); x[-n:] *= np.linspace(1, 0, n); return x


# ---------------- generic ----------------
def whoosh(d=.35, v=1.0, pitch=1.0):
    n = noise(d); t = t_(d); env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    lo = 400 * pitch; out = np.zeros_like(n)
    for k, (a, b) in enumerate([(lo, lo * 2.5), (lo * 2, lo * 5)]):
        out += bp(n, a, min(b, SR / 2 - 100)) * (1 - .4 * k)
    return norm(out * env, .5 * v)


def step(v=1.0, pitch=1.0):
    d = .09; return norm(lp(noise(d), 900 * pitch) * env_exp(d, .018) + _tone(110 * pitch, d, .02, .6), .45 * v)


def tap(v=1.0, pitch=1.0):
    d = .05; return norm(bp(noise(d), 1500 * pitch, 4500 * pitch) * env_exp(d, .006), .4 * v)


def sparkle(v=1.0, pitch=1.0):
    out = np.zeros(int(.7 * SR))
    for k in range(6):
        f = 2400 * pitch * (1.12 ** k); s = int(k * .06 * SR); x = _tone(f, .3, .08, .5)
        out[s:s + len(x)] += x[:len(out) - s]
    return norm(out, .3 * v)


# ---------------- clay ----------------
def clay_thud(v=1.0, pitch=1.0):
    """dull clay landing "pff": soft low-frequency impact + a little wet squelch noise"""
    d = .22; body = _sweep(140 * pitch, 60 * pitch, d, .05)
    sq = lp(noise(d), 700 * pitch) * env_exp(d, .03) * .5
    return _fade(norm(body + sq, .7 * v))


def clay_squish(v=1.0, pitch=1.0):
    """squash: resonant wet squelch, pitch sliding down"""
    d = .28; n = noise(d); t = t_(d)
    f = 900 * pitch * (1 - .5 * t / d)
    out = np.zeros_like(n)
    for i in range(0, len(n), 256):          # sweep a band-pass block by block for the "squelch"
        seg = n[i:i + 256]; out[i:i + len(seg)] = bp(seg, f[i] * .7, f[i] * 1.4)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** .7
    return _fade(norm(lp(out, 2500) * env, .5 * v))


def clay_pop(v=1.0, pitch=1.0):
    """bounce "pop": short upward-sliding sine"""
    return _fade(norm(_sweep(300 * pitch, 900 * pitch, .09, .03), .55 * v))


def clay_boing(v=1.0, pitch=1.0):
    """springy "boing": downward slide with vibrato"""
    d = .55; t = t_(d); f = 220 * pitch * (1 + .5 * np.exp(-t / .08)) * (1 + .04 * np.sin(2 * np.pi * 16 * t))
    return _fade(norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .2), .5 * v))


def clay_clink(v=1.0, pitch=1.0):
    """metal spatula in a clay world: a duller ting"""
    d = .4; out = sum(_tone(f * pitch, d, tau, a) for f, tau, a in [(1180, .12, 1), (2650, .07, .5), (4100, .04, .3)])
    return norm(lp(out, 5000), .35 * v)


def clay_step(v=1.0, pitch=1.0): return norm(clay_thud(.6, 1.4 * pitch)[:int(.12 * SR)], .35 * v)
def clay_tap(v=1.0, pitch=1.0): return norm(lp(tap(v, pitch), 2500), .3 * v)


# ---------------- paper ----------------
def paper_rustle(d=.4, v=1.0, pitch=1.0):
    n = noise(d); grains = (np.random.default_rng(3).random(len(n)) < .002).astype(float)
    g = np.convolve(grains, np.exp(-np.arange(200) / 30), 'same')
    return norm(hp(bp(n, 2000 * pitch, 9000), 1500) * (g * .7 + .3) * np.sin(np.pi * t_(d) / d), .35 * v)


def paper_flap(v=1.0, pitch=1.0):
    d = .12; return _fade(norm(bp(noise(d), 600 * pitch, 3500 * pitch) * env_exp(d, .025), .45 * v))


def paper_step(v=1.0, pitch=1.0): return norm(paper_flap(.6, .7 * pitch)[:int(.08 * SR)], .3 * v)
def paper_thud(v=1.0, pitch=1.0): return norm(paper_flap(v, .5 * pitch) + _tone(90 * pitch, .12, .03, .4), .45 * v)
def paper_whoosh(v=1.0, pitch=1.0): return norm(whoosh(.35, v, pitch * 1.6) + paper_rustle(.35, .4, pitch), .45 * v)


# ---------------- tin ----------------
def tin_clink(v=1.0, pitch=1.0):
    d = .6; out = sum(_tone(f * pitch, d, tau, a) for f, tau, a in [(1650, .25, 1), (2480, .18, .7), (3900, .12, .5), (5200, .08, .3)])
    return norm(out, .4 * v)


def tin_wind(v=1.0, pitch=1.0, clicks=8):
    """winding a key: a string of clicks"""
    out = np.zeros(int(clicks * .07 * SR + .1 * SR))
    for k in range(clicks):
        x = bp(noise(.015), 2500 * pitch, 7000) * env_exp(.015, .003); s = int(k * .07 * SR)
        out[s:s + len(x)] += x * (.8 + .2 * _rng.random())
    return norm(out, .4 * v)


def tin_thud(v=1.0, pitch=1.0): return norm(tin_clink(.5, .6 * pitch) + _tone(120 * pitch, .6, .05), .5 * v)
def tin_step(v=1.0, pitch=1.0): return norm(tin_clink(.4, 1.3 * pitch)[:int(.1 * SR)], .3 * v)


# ---------------- wood ----------------
def wood_knock(v=1.0, pitch=1.0):
    d = .18; out = sum(_tone(f * pitch, d, tau, a) for f, tau, a in [(520, .04, 1), (1250, .025, .5), (2300, .015, .3)])
    return norm(out + bp(noise(d), 800, 3000) * env_exp(d, .01) * .3, .5 * v)


def wood_thud(v=1.0, pitch=1.0): return wood_knock(v, .55 * pitch)
def wood_step(v=1.0, pitch=1.0): return norm(wood_knock(.6, 1.2 * pitch), .3 * v)


# ---------------- felt / fabric / yarn ----------------
def soft_pat(v=1.0, pitch=1.0):
    d = .12; return _fade(norm(lp(noise(d), 500 * pitch) * env_exp(d, .02), .4 * v))


felt_thud = felt_step = fabric_thud = fabric_step = crochet_thud = crochet_step = soft_pat


# ---------------- cardboard ----------------
def cardboard_thud(v=1.0, pitch=1.0):
    d = .2; return norm(_tone(95 * pitch, d, .045) + bp(noise(d), 200, 1400) * env_exp(d, .03) * .7, .55 * v)


def tape_rip(v=1.0, pitch=1.0, d=.45):
    n = noise(d); t = t_(d); crack = (np.random.default_rng(5).random(len(n)) < .02) * 1.0
    return norm(hp(n * (.3 + crack), 1800 * pitch) * np.sin(np.pi * t / d) ** .5, .4 * v)


def cardboard_step(v=1.0, pitch=1.0): return norm(cardboard_thud(.6, 1.3 * pitch)[:int(.1 * SR)], .3 * v)




# ---------------- water (any material) ----------------
_rng2 = np.random.default_rng(29)          # own random stream for newer sounds: keeps older sounds' random sequence intact


def _blip(f0, f1, d, tau, v=1.0):
    """resonance of one bubble / drop: a very short exponentially rising sine (a drop hitting water and a bubble bursting both sound like this)"""
    t = t_(d); f = f0 * (f1 / f0) ** np.clip(t / max(d * .45, 1e-3), 0, 1)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau) * v
    k = min(len(x), 48); x[:k] *= np.linspace(0, 1, k)
    return x


def _place(out, x, s):
    s = int(s); e = min(len(out), s + len(x))
    if 0 <= s < len(out): out[s:e] += x[:e - s]


def drip(v=1.0, pitch=1.0):
    """drip "plink": one drop falling into water"""
    x = _blip(650 * pitch, 1900 * pitch, .12, .022)
    c = hp(noise(.006), 2500) * env_exp(.006, .0012) * .15
    x[:len(c)] += c
    return _fade(norm(x, .4 * v))


def bubble(v=1.0, pitch=1.0, n=7):
    """bubbling "blub blub": a string of bubbles of mixed sizes, speeding up"""
    d = .62; out = np.zeros(int(d * SR) + int(.1 * SR)); s = .0
    for k in range(n):
        f0 = _rng2.uniform(260, 620) * pitch
        _place(out, _blip(f0, f0 * _rng2.uniform(1.8, 2.6), .07, _rng2.uniform(.01, .02), _rng2.uniform(.5, 1.0)), s * SR)
        s += _rng2.uniform(.05, .11) * (1 - .5 * k / n)
    out += lp(noise(len(out) / SR), 500 * pitch) * np.exp(-np.arange(len(out)) / (.25 * SR)) * .08
    return _fade(norm(out, .38 * v))


def splash(v=1.0, pitch=1.0):
    """splash / falling in "plop, splash": the dull hit of entering water + spray + a few flying drops"""
    d = .75; out = np.zeros(int(d * SR))
    body = _sweep(240 * pitch, 95 * pitch, .25, .06) * .8
    spray = hp(bp(noise(.45), 800 * pitch, min(8000 * pitch, SR / 2 - 500)), 600) * env_exp(.45, .09)
    spray[:144] *= np.linspace(0, 1, 144)
    _place(out, body, 0); _place(out, spray * .7, int(.004 * SR))
    for _ in range(5):
        f0 = _rng2.uniform(900, 1700) * pitch
        _place(out, _blip(f0, f0 * 2, .06, .012, _rng2.uniform(.15, .35)), _rng2.uniform(.12, .55) * SR)
    return _fade(norm(out, .6 * v))


def flow(v=1.0, pitch=1.0, d=1.5):
    """water flow (lasts d seconds): undulating water sound + fine small bubbles"""
    d = max(.3, float(d)); n = len(t_(d)); t = t_(d)
    base = bp(noise(d), 280 * pitch, min(2600 * pitch, SR / 2 - 500))
    mod = .65 + .35 * np.sin(2 * np.pi * 3.1 * t + 1) * np.sin(2 * np.pi * 0.7 * t + 2)
    out = base * mod * .45
    for _ in range(int(d * 28)):
        f0 = _rng2.uniform(500, 1500) * pitch
        _place(out, _blip(f0, f0 * 1.8, .035, _rng2.uniform(.004, .009), _rng2.uniform(.2, .6)) * np.abs(base).mean() * 6,
               _rng2.uniform(0, d - .04) * SR)
    f = min(n // 2, int(.18 * SR)); env = np.ones(n); env[:f] = np.linspace(0, 1, f); env[-f:] = np.linspace(1, 0, f)
    return norm(out * env, .3 * v)


# ---------------- snow, soft things ----------------
def crunch(v=1.0, pitch=1.0):
    """snow step "crunch": many tiny cracks packed together as the foot presses down + a little thud from the sole"""
    d = .24; n = len(t_(d)); t = t_(d)
    dens = np.clip(t / .02, 0, 1) * np.exp(-t / .07)
    g = (_rng2.random(n) < .09 * dens) * _rng2.uniform(.3, 1, n)
    grains = np.convolve(g, np.exp(-np.arange(90) / 14.0), 'same')
    x = bp(grains, 1100 * pitch, min(6500 * pitch, SR / 2 - 500)) + lp(noise(d), 280 * pitch) * env_exp(d, .025) * .25
    return _fade(norm(x, .45 * v))


def puff(v=1.0, pitch=1.0):
    """soft "puff": snow hitting a face, a ball of yarn puffing up, cotton being patted"""
    d = .32; t = t_(d)
    env = np.where(t < .015, np.sin(np.pi / 2 * t / .015), np.exp(-(t - .015) / .07))
    x = lp(noise(d), 900 * pitch) * env + _sweep(170 * pitch, 85 * pitch, d, .05) * .35
    return _fade(norm(x, .45 * v))


def flop(v=1.0, pitch=1.0):
    """soft heavy thing falling "flop": a doll falling over, a ball of yarn hitting the floor; duller than thud, a bit of low end"""
    d = .3; body = _sweep(125 * pitch, 58 * pitch, d, .045)
    muff = lp(noise(d), 420 * pitch) * env_exp(d, .035)
    x = body * .8 + muff
    x[:192] *= np.linspace(0, 1, 192)
    return _fade(norm(x, .6 * v))


def rub(v=1.0, pitch=1.0, d=.5):
    """cloth / yarn rubbing "shhh" (lasts d seconds): clothes brushing past, a scarf wrapping"""
    d = max(.12, float(d)); t = t_(d)
    am = .55 + .45 * lp(_rng2.standard_normal(len(t)), 9) / (np.abs(lp(_rng2.standard_normal(len(t)), 9)).max() + 1e-9)
    x = bp(noise(d), 350 * pitch, min(3200 * pitch, SR / 2 - 500)) * np.clip(am, .1, 1) * np.sin(np.pi * t / d) ** .7
    return _fade(norm(x, .3 * v))


def felt_rub(v=1.0, pitch=1.0, d=.5): return norm(lp(rub(v, pitch, d), 1600 * pitch), .28 * v)
def crochet_rub(v=1.0, pitch=1.0, d=.5): return norm(lp(rub(v, .8 * pitch, d), 2200 * pitch), .28 * v)


# ---------------- small mechanisms: joints, buttons, knobs, tape ----------------
def _tick(d, res, hp_f=2000, taus=None, v=1.0, nz=.6):
    """one hard contact: a very short band-limited noise (the hit) + a few fast-decaying resonances (the material's "timbre")"""
    t = t_(d); taus = taus or [.006] * len(res)
    x = bp(noise(d), hp_f, min(hp_f * 3.5, SR / 2 - 500)) * env_exp(d, .0012) * nz
    x = x + sum(a * np.sin(2 * np.pi * f * t + _rng2.random() * 6) * np.exp(-t / tau) for (f, a), tau in zip(res, taus))
    return x * v


def click(v=1.0, pitch=1.0):
    """joint "click": two very short hard contacts (puppet joint, a small mechanism snapping into place)"""
    out = np.zeros(int(.07 * SR))
    _place(out, _tick(.03, [(2300 * pitch, .8), (3700 * pitch, .5)]), 0)
    _place(out, _tick(.03, [(2500 * pitch, .6), (4000 * pitch, .4)], v=.65), .018 * SR)
    return _fade(norm(out, .5 * v))


def wood_click(v=1.0, pitch=1.0):
    """wooden joint "clack": lower and woodier"""
    out = np.zeros(int(.08 * SR))
    tw = [.012, .009, .006]
    _place(out, _tick(.04, [(950 * pitch, 1), (1750 * pitch, .6), (2900 * pitch, .3)], 800, tw, nz=.35), 0)
    _place(out, _tick(.04, [(1050 * pitch, .8), (1900 * pitch, .5), (3100 * pitch, .25)], 800, tw, v=.6, nz=.35), .02 * SR)
    return _fade(norm(out, .45 * v))


def button(v=1.0, pitch=1.0):
    """button "tick": a plastic button snapping shut / stepped on; one crisp hit plus a little rebound"""
    out = np.zeros(int(.06 * SR))
    _place(out, _tick(.025, [(3300 * pitch, .9), (5100 * pitch, .5), (760 * pitch, .5)], 2500, [.004, .003, .008]), 0)
    _place(out, _tick(.02, [(3600 * pitch, .5)], 3000, [.003], v=.35), .012 * SR)
    return _fade(norm(out, .45 * v))


def ratchet(v=1.0, pitch=1.0, n=5):
    """turning a knob "click-click-click": a string of small metal teeth (brass knob, wind-up key, radio dial)"""
    out = np.zeros(int((n * .045 + .05) * SR))
    for k in range(n):
        p = pitch * _rng2.uniform(.96, 1.04)
        _place(out, _tick(.02, [(3100 * p, .7), (4700 * p, .5), (6900 * min(p, 1.3), .3)], 3000, [.006, .004, .003],
                          v=_rng2.uniform(.7, 1)), k * .045 * SR)
    return _fade(norm(out, .4 * v))


def creak(v=1.0, pitch=1.0, d=.45):
    """wood "creak" (lasts d seconds): door hinge, wood rubbing, a tight wooden knob"""
    d = max(.15, float(d)); t = t_(d)
    f0 = 60 * pitch * (1 + .25 * np.sin(2 * np.pi * 2.3 * t)) * (1 + .08 * _rng2.standard_normal(len(t)).cumsum() / np.sqrt(len(t)))
    ph = np.cumsum(f0) / SR; imp = np.diff(np.floor(ph), prepend=0) > 0
    x = imp * _rng2.uniform(.5, 1, len(t))
    x = bp(x, 500 * pitch, 2600 * pitch) + bp(x, 1100 * pitch, 1500 * pitch) * 1.5
    return _fade(norm(x * np.sin(np.pi * t / d) ** .6, .45 * v))


def rip(v=1.0, pitch=1.0, d=.45):
    """tearing tape "rrrip" (same sound as tape_rip)"""
    return tape_rip(v, pitch, d)


# ---------------- clay: smear ----------------
def smear(v=1.0, pitch=1.0, d=.6):
    """finger smearing clay (lasts d seconds): long wet rub with a little stick-and-release judder"""
    d = max(.2, float(d)); t = t_(d); n = noise(d)
    f = 500 * pitch * (1 + .35 * t / d); out = np.zeros_like(n)
    for i in range(0, len(n), 256):
        seg = n[i:i + 256]; out[i:i + len(seg)] = bp(seg, f[i] * .7, f[i] * 1.5)
    stick = .6 + .4 * np.abs(np.sin(2 * np.pi * 11 * t + _rng2.random() * 6)) ** 3
    return _fade(norm(lp(out, 2200 * pitch) * stick * np.sin(np.pi * t / d) ** .5, .4 * v))


# =====================================================================================
# Name tables: generic actions, material versions, aliases
# =====================================================================================
MATERIALS = ('clay', 'paper', 'tin', 'wood', 'felt', 'fabric', 'crochet', 'cardboard')
GENERIC = ('whoosh', 'step', 'tap', 'sparkle', 'drip', 'bubble', 'splash', 'flow', 'crunch', 'puff', 'flop',
           'rub', 'click', 'button', 'ratchet', 'creak', 'rip', 'smear')
ALIASES = {
    'drop': 'drip', 'water_drop': 'drip', 'gurgle': 'bubble', 'bubbles': 'bubble', 'plop': 'splash',
    'stream': 'flow', 'water': 'flow', 'snow': 'crunch', 'snow_step': 'crunch', 'inflate': 'puff',
    'soft_thud': 'flop', 'cloth': 'rub', 'wool': 'rub', 'joint': 'click', 'knob': 'ratchet', 'wind_up': 'ratchet',
    'squeak': 'creak', 'tape': 'rip', 'tape_rip': 'rip', 'wipe': 'smear',
}
DESC = {
    'whoosh': 'swing, fly past, fling', 'step': 'footstep', 'tap': 'light tap, light touch', 'sparkle': 'glint, appearing (a sparkly run)',
    'thud': 'landing, impact (the material\'s heavy sound)', 'squish': 'squash (clay)', 'pop': 'bounce "pop" (clay)', 'boing': 'spring "boing" (clay)',
    'clink': 'metal "ting"', 'rustle': 'paper rustle', 'flap': 'paper flipping, flapping', 'wind': 'winding a key (tin)', 'knock': 'wood knock',
    'drip': 'water drop', 'bubble': 'bubbling, gurgle', 'splash': 'falling into / splashing water', 'flow': 'water flow (d s)', 'crunch': 'snow crunch underfoot',
    'puff': 'soft "puff": snow hitting, yarn puffing up', 'flop': 'soft heavy thing falling: doll falling over, yarn ball hitting the floor', 'rub': 'cloth / yarn rubbing (d s)',
    'click': 'joint click, small mechanism snapping into place', 'button': 'button tick', 'ratchet': 'turning a knob, wind-up key clicks', 'creak': 'wood creak (d s)',
    'rip': 'tearing tape (d s)', 'smear': 'long rub of a finger smearing clay (d s)',
}


def _mat_table():
    g = globals(); out = {}
    for name, f in g.items():
        if not callable(f) or name.startswith('_') or getattr(f, '__module__', None) != __name__: continue
        m, _, k = name.partition('_')
        if m in MATERIALS and k: out.setdefault(m, {})[k] = f
    return out


def _fn(kind, material):
    """name -> function: material version -> generic -> alias (alias goes through material / generic again) -> full function name (old spelling, e.g. clay_thud)"""
    mats = _mat_table().get(material, {}) if material else {}
    for k in (kind, ALIASES.get(kind)):
        if not k: continue
        if k in mats: return mats[k]
        if k in GENERIC: return globals()[k]
    f = globals().get(kind)
    if callable(f) and not kind.startswith('_') and getattr(f, '__module__', None) == __name__ \
            and kind not in ('make', 'kinds', 'describe'):
        return f
    return None


def make(kind, material=None, v=1.0, pitch=1.0, d=None):
    """Look up "<material>_<action>", then the generic action and aliases; if none, raise listing what is available. d: length of a sustained sound (s)"""
    f = _fn(kind, material)
    if f is None: raise KeyError(f'no foley "{kind}". {material or "generic"} has: {", ".join(kinds(material))}')
    kw = dict(v=v, pitch=pitch)
    if d is not None and 'd' in f.__code__.co_varnames[:f.__code__.co_argcount]: kw['d'] = float(d)
    return np.asarray(f(**kw), np.float32)


def kinds(material=None, aliases=True):
    """every name this material can use (generic actions + material versions + aliases), sorted"""
    names = set(GENERIC) | set(_mat_table().get(material, {}) if material else ())
    if aliases: names |= {a for a, k in ALIASES.items() if _fn(a, material) is not None}
    return sorted(names)


def describe(material=None):
    """-> [(name, description, whether it is this material's own version, [aliases])], printed by sound.py kinds"""
    mats = _mat_table().get(material, {}) if material else {}
    rows = []
    for k in sorted(set(GENERIC) | set(mats)):
        al = sorted(a for a, t in ALIASES.items() if t == k)
        rows.append((k, DESC.get(k, ''), k in mats, al))
    return rows
