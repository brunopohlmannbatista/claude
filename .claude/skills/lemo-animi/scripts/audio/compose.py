"""lemo-animi score: the style's instrumentation (style.json "music") + a very short score plan -> notes -> stereo wav.

The agent writes no notes, only the score plan ("music" in the sound sheet sound.json):
    {"bpm": 112, "key": "F",                       # optional: by seed, bpm within the style's range, key = the style's key or a related key
     "sections": [{"t": 0, "energy": 0.3},          # section: from t seconds; energy 0–1 sets how many instruments play
                  {"t": 6.2, "energy": 0.6},
                  {"t": 21.0, "energy": 0.9},
                  {"t": 27.5, "energy": 0.3, "end": true}],   # end: land on the tonic chord here
     "hits": [{"t": 9.5, "kind": "accent"}, {"t": 21.0, "kind": "boom"}],   # hits: the moment of a key action
     "silences": [[18.2, 19.4]]}                    # silence: no music at all here (before a turn or a gag)

Style instrumentation (style.json "music"): bpm range, mode, chord progression, the instrument and rhythm pattern of each
role (melody / counter / bass / comp / perc), which roles join at which energy, which instrument plays each hit kind. One
bar grid for the whole film and the music runs continuously; sections only choose the bar where the instrumentation
changes (the bar line nearest the section start, at most half a bar off); what lines up with the picture is the hits and
silences.
"""
import numpy as np
from . import sampler as S
from .sfx import SR, add, limit

PC = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7,
      'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
SCALES = {'major': [0, 2, 4, 5, 7, 9, 11], 'minor': [0, 2, 3, 5, 7, 8, 10], 'dorian': [0, 2, 3, 5, 7, 9, 10],
          'mixolydian': [0, 2, 4, 5, 7, 9, 10], 'pentatonic': [0, 2, 4, 7, 9], 'minor_pent': [0, 3, 5, 7, 10]}
ROMAN = {'I': 0, 'II': 1, 'III': 2, 'IV': 3, 'V': 4, 'VI': 5, 'VII': 6}

# melody rhythms within one bar (4 beats): onset beat positions
MEL_RHYTHMS = [[0, 1, 1.5, 2, 3], [0, .5, 1, 2, 2.5, 3], [0, 1, 2, 2.5, 3.5], [0, 1.5, 2, 3],
               [0, .5, 1.5, 2, 3], [0, 1, 1.5, 2.5, 3]]
CADENCE_RHYTHM = [0, 1, 2]          # last bar of a phrase: fewer notes, the last one held


def chord_tones(numeral, key, mode):
    """'vi' / 'V7' / 'IV' -> chord tones as midi pitch classes (relative to C, no octave), root first"""
    seven = numeral.endswith('7'); base = numeral.rstrip('7')
    deg = ROMAN[base.upper()]
    sc = SCALES['minor' if mode in ('minor', 'minor_pent', 'dorian') else 'major']
    idx = [deg, deg + 2, deg + 4] + ([deg + 6] if seven else [])
    return [PC[key] + sc[i % 7] + 12 * (i // 7) for i in idx]


def at_oct(pc, octave):
    """place a pitch class in an octave (C4 = 60)"""
    return 12 * (octave + 1) + (pc % 12) + 12 * (pc // 12)


def _scale_notes(key, mode, lo, hi):
    sc = SCALES.get(mode, SCALES['major'])
    return [m for m in range(lo, hi + 1) if (m - PC[key]) % 12 in sc]


class _Ctx:
    def __init__(self, plan, mus, seed):
        self.mus = mus
        self.rng = np.random.default_rng(seed)
        kr = np.random.default_rng([int(seed), 1])                     # tempo and key use a separate random stream, leaving the melody stream unchanged
        r = mus.get('bpm', [100, 120])
        auto = float(kr.uniform(r[0], r[1])) if isinstance(r, list) else float(r)   # no bpm: each film picks one within the style's range
        self.bpm = float(plan.get('bpm') or round(auto))
        self.beat = 60.0 / self.bpm
        k0 = mus.get('key', 'C'); shift = [0, 2, 5, 7, -2][int(kr.integers(5))]    # no key: the style's key or a closely related key
        self.key = plan.get('key') or next(n for n, v in PC.items() if v == (PC[k0] + shift) % 12)
        self.mode = plan.get('mode') or mus.get('mode', 'major')
        self.mel_mode = mus.get('melody_scale', self.mode)
        self.swing = float(mus.get('swing', 0))
        progs = mus.get('progressions') or [['I', 'vi', 'IV', 'V']]
        self.prog = progs[int(self.rng.integers(len(progs)))]

    def bt(self, t0, b):
        """section start t0 + beat b -> seconds (off-beat eighths delayed by swing)"""
        frac = b - np.floor(b)
        if self.swing and abs(frac - .5) < 1e-6: b = np.floor(b) + .5 + self.swing * .5
        return t0 + b * self.beat


def _inst(role):
    i = role['inst']
    return i[0] if isinstance(i, list) else i


def _roles_for(mus, energy):
    """energy -> roles playing in this section"""
    table = sorted(((float(k), v) for k, v in mus.get('energy', {}).items()), key=lambda kv: kv[0])
    roles = []
    for th, rs in table:
        if energy + 1e-6 >= th: roles = rs
    return roles


def _melody(cx, role, t0, nbars, chords, events, energy):
    """Motif-based melody: write a 1-bar motif (rhythm + contour), repeat it transposed to each chord; the last bar of every 4 resolves on a chord tone."""
    o = role.get('oct', 5)
    lo, hi = at_oct(0, o) - 3, at_oct(0, o) + 14
    notes = _scale_notes(cx.key, cx.mel_mode, lo, hi)
    rh = MEL_RHYTHMS[int(cx.rng.integers(len(MEL_RHYTHMS)))]
    steps = list(cx.rng.choice([-2, -1, -1, 1, 1, 2, 0], size=len(rh)))
    vel = role.get('vel', .6) * (.85 + .3 * energy)
    for b in range(nbars):
        ch = chords[b % len(chords)]
        last = (b % 4 == 3) or (b == nbars - 1)
        rhythm = CADENCE_RHYTHM if last else rh
        # start on the chord tone nearest the middle of the range
        targets = [m for m in notes if (m % 12) in {c % 12 for c in ch}]
        cur = min(targets, key=lambda m: abs(m - (lo + hi) / 2)) if targets else notes[len(notes) // 2]
        idx = notes.index(cur) if cur in notes else len(notes) // 2
        for k, beat in enumerate(rhythm):
            if k > 0 and not last: idx = int(np.clip(idx + steps[k % len(steps)], 0, len(notes) - 1))
            elif k > 0 and last:   # cadence: move toward a chord tone
                cand = [i for i, m in enumerate(notes) if (m % 12) in {c % 12 for c in ch}]
                idx = min(cand, key=lambda i: abs(i - idx)) if cand else idx
            nxt = rhythm[k + 1] if k + 1 < len(rhythm) else 4
            d = (nxt - beat) * cx.beat * (0.95 if last and k == len(rhythm) - 1 else role.get('legato', .8))
            strong = beat in (0, 2)
            events.append(dict(t=cx.bt(t0, b * 4 + beat), inst=_inst(role), pitch=notes[idx], dur=d,
                               vel=vel * (1.0 if strong else .82), pan=role.get('pan', 0)))
        # next bar's motif transposed to the new chord, same contour; rhythm changes every 2 bars
        if b % 2 == 1:
            rh = MEL_RHYTHMS[int(cx.rng.integers(len(MEL_RHYTHMS)))]


def _bass(cx, role, t0, nbars, chords, events, energy):
    o = role.get('oct', 2); pat = role.get('pattern', 'root-fifth'); vel = role.get('vel', .7)
    for b in range(nbars):
        ch = chords[b % len(chords)]; r = at_oct(ch[0], o); f = r + 7
        if pat == 'root':
            seq = [(0, r, 4)]
        elif pat == 'walking':
            seq = [(0, r, 1), (1, at_oct(ch[1], o), 1), (2, f, 1), (3, at_oct(ch[1], o) + (2 if b % 2 else -1), 1)]
        elif pat == 'oom-pah':
            seq = [(0, r, 1), (2, f - 12 if f - 12 > 28 else f, 1)]
        else:  # root-fifth
            seq = [(0, r, 1.5), (2, f, 1.5)] if energy < .75 else [(0, r, 1), (1.5, r, .5), (2, f, 1), (3, f, .5)]
        for beat, m, d in seq:
            events.append(dict(t=cx.bt(t0, b * 4 + beat), inst=_inst(role), pitch=m, dur=d * cx.beat * .9,
                               vel=vel * (1 if beat == 0 else .85), pan=role.get('pan', 0)))


def _comp(cx, role, t0, nbars, chords, events, energy):
    o = role.get('oct', 4); pat = role.get('pattern', 'offbeat'); vel = role.get('vel', .45)
    for b in range(nbars):
        ch = [at_oct(c, o) for c in chords[b % len(chords)]]
        if pat == 'sustain':
            hits = [(0, 4)]
        elif pat == 'oom-pah':
            hits = [(1, .5), (3, .5)]
        elif pat == 'arp':
            hits = None
            arp = ch + [ch[0] + 12]
            for k in range(8):
                events.append(dict(t=cx.bt(t0, b * 4 + k * .5), inst=_inst(role), pitch=arp[k % len(arp)],
                                   dur=cx.beat * .45, vel=vel * (1 if k % 2 == 0 else .8), pan=role.get('pan', 0)))
        else:  # offbeat
            hits = [(.5, .4), (1.5, .4), (2.5, .4), (3.5, .4)] if energy >= .6 else [(1, .5), (3, .5)]
        if hits:
            for beat, d in hits:
                for j, m in enumerate(ch[:3]):
                    events.append(dict(t=cx.bt(t0, b * 4 + beat) + j * .006, inst=_inst(role), pitch=m,
                                       dur=d * cx.beat, vel=vel * .8, pan=role.get('pan', 0) + (j - 1) * .15))


def _perc(cx, role, t0, nbars, events, energy):
    insts = role['inst'] if isinstance(role['inst'], list) else [role['inst']]
    pat = role.get('pattern', 'tick'); vel = role.get('vel', .4)
    for b in range(nbars):
        if pat == 'tick':
            seq = [(0, 0), (2, 0)] + ([(k * .5, 1) for k in range(8)] if len(insts) > 1 and energy >= .7 else [])
        elif pat == 'march':
            seq = [(0, 0), (1, 1), (2, 0), (3, 1)]
        elif pat == 'gongs':      # gongs and drums: clapper every beat, gong on each downbeat, cymbal on 2 and 4
            seq = [(k, 0) for k in range(4)] + ([(0, 1)] if len(insts) > 1 else []) + \
                  ([(1, 2), (3, 2)] if len(insts) > 2 and energy >= .6 else [])
        else:
            seq = [(0, 0)]
        for beat, i in seq:
            inst = insts[min(i, len(insts) - 1)]
            events.append(dict(t=cx.bt(t0, b * 4 + beat), inst=inst, pitch=None, dur=None,
                               vel=vel * (1 if beat == 0 else .7) * (.8 + .4 * cx.rng.random()), pan=role.get('pan', 0)))


def _hit(cx, kind, t, events):
    spec = cx.mus.get('hits', {}).get(kind)
    if not spec: return
    for item in spec:
        inst, what = item[0], (item[1] if len(item) > 1 else None)
        vel = item[2] if len(item) > 2 else .8
        if what == 'gliss_up' or what == 'gliss_down':
            base = at_oct(PC[cx.key], 5); sc = _scale_notes(cx.key, 'major', base, base + 12)
            run = sc if what == 'gliss_up' else sc[::-1]
            for k, m in enumerate(run):
                events.append(dict(t=t - (len(run) - k) * .035, inst=inst, pitch=m, dur=.15, vel=vel * (.6 + .4 * k / len(run)), pan=0))
        elif what == 'arp':
            ch = chord_tones('I', cx.key, cx.mode)
            for k, c in enumerate(ch + [ch[0] + 12]):
                events.append(dict(t=t + k * .07, inst=inst, pitch=at_oct(c, 6), dur=.6, vel=vel, pan=.2))
        elif what == 'tonic':
            events.append(dict(t=t, inst=inst, pitch=at_oct(PC[cx.key], 2), dur=1.2, vel=vel, pan=0))
        else:
            events.append(dict(t=t, inst=inst, pitch=what, dur=None if what is None else 1.0, vel=vel, pan=0))


def score(plan, mus, dur, seed=7):
    """score plan + style instrumentation -> (events, ctx)"""
    cx = _Ctx(plan, mus, seed)
    roles = mus.get('roles', {})
    secs = sorted(plan.get('sections') or [{'t': 0, 'energy': .5}], key=lambda s: s['t'])
    events = []
    bar = 4 * cx.beat
    # One bar grid for the whole film: the music runs continuously; sections only choose the bar where the
    # instrumentation changes (the bar line nearest the section start). Restarting bars per section and cutting notes
    # before the next section would break the music and shift the beat at every section change.
    end_t = next((float(s['t']) for s in secs if s.get('end')), dur)
    nb = int(np.ceil(end_t / bar - 1e-6))
    def en_at(t):
        e = float(secs[0].get('energy', .5))
        for s in secs:
            if s.get('end'): break
            if float(s['t']) <= t + bar / 2: e = float(s.get('energy', .5))      # nearest bar line
        return e
    chords = [chord_tones(n, cx.key, cx.mode) for n in cx.prog]
    runs = []                                       # consecutive bars with the same instrumentation
    for b in range(nb):
        e = en_at(b * bar)
        if runs and runs[-1][2] == e: runs[-1][1] = b + 1
        else: runs.append([b, b + 1, e])
    for b0, b1, en in runs:
        t0 = b0 * bar; L = len(chords); ch = chords[b0 % L:] + chords[:b0 % L]       # chords continue from the previous section
        sec = []
        for rname in _roles_for(mus, en):
            role = roles.get(rname)
            if not role: continue
            if rname in ('melody', 'counter'):
                r2 = dict(role)
                if rname == 'counter': r2['oct'] = role.get('oct', 6)
                _melody(cx, r2, t0, b1 - b0, ch, sec, en)
            elif rname == 'bass': _bass(cx, role, t0, b1 - b0, ch, sec, en)
            elif rname == 'comp': _comp(cx, role, t0, b1 - b0, ch, sec, en)
            elif rname == 'perc': _perc(cx, role, t0, b1 - b0, sec, en)
        for e in sec:                               # cut off only before the final chord
            if e['t'] >= end_t - .01: continue
            if e.get('dur'): e['dur'] = min(e['dur'], max(.05, end_t - e['t'] - .02))
            events.append(e)
    if end_t < dur:                                 # ending: everyone lands on the tonic chord
        ch = chord_tones('I', cx.key, cx.mode)
        for rname, role in roles.items():
            if rname == 'perc': continue
            for j_, c in enumerate(ch[:3] if rname != 'bass' else ch[:1]):
                events.append(dict(t=end_t + j_ * .01, inst=_inst(role), pitch=at_oct(c, role.get('oct', 4)),
                                   dur=max(1.0, dur - end_t - .3), vel=role.get('vel', .5) * .9, pan=role.get('pan', 0)))
    for h in plan.get('hits', []):
        _hit(cx, h.get('kind', 'accent'), float(h['t']), events)
    events = [e for e in events if 0 <= e['t'] < dur]
    for sl in plan.get('silences', []):
        a, b = sl
        events = [e for e in events if not (a - .02 <= e['t'] < b)]
        for e in events:
            if e['t'] < a and e.get('dur'): e['dur'] = min(e['dur'], max(.05, a - e['t']))
    return events, cx


def _voice(e):
    inst = e['inst']
    I = S.load(inst)
    if I.kind == 'hit': return S.hit(I, e.get('pitch'), e.get('vel', .8), e.get('dur'))
    return S.note(I, e['pitch'], e.get('dur') or .5, e.get('vel', .8))


def render(plan, mus, dur, seed=7):
    """-> stereo float32 (N,2) @ SR; silences muted (60 ms fade out / in); limited to 0.9 overall"""
    events, cx = score(plan, mus, dur, seed)
    buf = np.zeros((int((dur + 3) * SR), 2), np.float32)
    for e in events:
        try: x = _voice(e)
        except Exception as ex:
            raise RuntimeError(f"score: instrument {e['inst']} failed: {ex}") from ex
        add(buf, x, e['t'], e.get('gain', 1.0) or 1.0, e.get('pan', 0.0) or 0.0)
    rv = mus.get('reverb')
    if rv: buf = S.room(buf, size=rv.get('size', .3), mix=rv.get('mix', .12))
    buf = buf[:int(dur * SR)]
    env = np.ones(len(buf), np.float32); f = int(.06 * SR)
    for a, b in plan.get('silences', []):
        i0, i1 = int(a * SR), int(b * SR)
        env[max(0, i0 - f):i0] = np.minimum(env[max(0, i0 - f):i0], np.linspace(1, 0, i0 - max(0, i0 - f)))
        env[i0:i1] = 0
        env[i1:i1 + f] = np.minimum(env[i1:i1 + f], np.linspace(0, 1, len(env[i1:i1 + f])))
    tail = int(1.2 * SR)                               # 1.2 s fade-out at the end
    env[-tail:] *= np.linspace(1, 0, tail)
    buf *= env[:, None]
    pk = np.abs(buf).max()
    if pk > .9: buf = np.stack([limit(buf[:, 0], .9), limit(buf[:, 1], .9)], 1)
    return buf.astype(np.float32), dict(bpm=cx.bpm, key=cx.key, mode=cx.mode, prog=cx.prog, n=len(events))
