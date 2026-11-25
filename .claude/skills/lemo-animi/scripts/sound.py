"""lemo-animi sound: narration, subtitles, score, foley, mix, mux into the video. Everything starts from one sound sheet, sound.json.

    python sound.py vo    sound.json        # synthesize narration (one wav per line + word timings), print each line's length; skipped without narration
    python sound.py lint  sound.json        # check the sheet: narration overlap, overrun, speaking rate, silences, hits, foley kinds, shot-based times
    python sound.py times sound.json        # list every resolved time (grouped by shot); use after moving shots
    python sound.py build sound.json        # write audio/mix.wav and stems; with narration also subtitles audio/subs.json and <name>.srt
    python sound.py mux   film.mp4 audio/mix.wav out.mp4   # mux the mix into the film (video stream not re-encoded)
    python sound.py kinds [style id]         # list the foley this style can use (with aliases and a one-line description)
    python sound.py voices                   # list available Chinese and English voices (edge-tts, needs network)

Sound sheet (sound.json, in the same film folder as film.py):
{
 "style": "clay",                 # style id: sets score instrumentation, foley material, default voice, subtitle style
 "dur": 30.0,                     # film length in seconds
 "name": "penguin-pancake",       # file name of the output srt
 "lang": "en",                                  # film language: zh / en (init_film.py --lang writes it; other codes fall back to en). Narration in this language; for bilingual subtitles the second line goes in the other language's field
 "voice": {"voice": "en-US-AvaNeural", "rate": "+0%", "pitch": "+0Hz"},   # optional, defaults to the style's; en child voice en-US-AnaNeural; zh default zh-CN-XiaoyiNeural, child zh-CN-YunxiaNeural
 "vo": [{"id": "L1", "t": 0.8, "text": "Little Penguin wanted to make the perfect pancake."},   # optional: missing or [] = no narration (no subtitles, score not ducked)
                                                                           # t = second this line starts (set it after vo gives the lengths)
        {"id": "L2", "t": 5.6, "text": "But the pan was too heavy!", "rate": "+8%"}],
                                  # bilingual subtitles: add the second language per line, "zh" in an en film, "en" in a zh film
                                  # (e.g. "zh": "可是，锅太重了！"); if the line splits into several screens write a list with one
                                  # entry per screen (sound.py lint shows the split). One line per language, no wrapping, same plate
 "music": {"bpm": 112, "sections": [...], "hits": [...], "silences": [...]},  # see audio/compose.py
 "foley": [{"t": 3.2, "kind": "thud", "v": 0.8, "pan": -0.2},                 # see audio/foley.py
           {"t": "flip+0.4", "kind": "squish"}],                               # times can be per shot: shot name + offset seconds
 "foley_rules": [{"cell": "walk_[15]", "kind": "step", "v": 0.4}]             # optional: automatic foley when the timesheet switches to a cell
}
Score and foley times (t of sections / hits / silences / foley) can be seconds or per shot, resolved from work/shots.json
(written by film.py lint; falls back to out/<name>.shots.json):
    "flip+0.4"   0.4 s after shot "flip" starts          "flip"      that shot's cut point
    "#3-0.25"    0.25 s before shot 3 starts (counted from 0, same as SHOTS[3])
    ["flip", 0.4] / [3, -0.25]   the same as lists
With narration, narration leads: write the vo text first (t can stay empty) -> sound.py vo gives each line's length ->
lay out the shot list by those lengths and set each t -> cut picture to the narration -> set score sections, hits, foley
-> sound.py lint -> sound.py build -> film.py burns subtitles while rendering -> sound.py mux.
No narration: time the shot list to picture and score, skip vo, everything else as usual (build makes score + foley only,
no subtitles).
Narration uses edge-tts online voices only; if it cannot connect and network access cannot be granted, make the version
without narration; never use local offline voices.
"""
import os, sys, re, json, hashlib, asyncio, subprocess, argparse
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from audio.sfx import SR, add, limit          # noqa: E402
from audio import compose, foley              # noqa: E402
import animi                                  # noqa: E402

PUNCT = '，。！？；：、,.!?;:…—「」“”‘’（）()《》 '
KEEP_END = '！？!?…'
MAX_CHARS = 14                    # zh subtitles: max characters per screen
EN_MAX = 42                       # bilingual subtitles: max English characters per screen (fits one line, no wrapping)
CPS_MAX = 5.2                     # zh narration rate limit (chars / s); faster is hard to hear and subtitles cannot be read
WPS_MAX = 3.0                     # en narration rate limit (words / s)
VO_SHARE_MAX = .6                 # narration may fill at most this share of the film; the rest is picture and music
EN_SCREEN = 42                    # en film: max subtitle characters per screen (fits one line, no wrapping)
VOICES = {'zh': {'lively': 'zh-CN-XiaoyiNeural', 'child': 'zh-CN-YunxiaNeural'},
          'en': {'lively': 'en-US-AvaNeural', 'child': 'en-US-AnaNeural'}}


def film_lang(d):
    """Film language (top-level lang in sound.json: zh / en; init_film.py writes it): narration, subtitles, title and end cards use it.
    Missing: zh for older films; any other language code falls back to en"""
    l = str(d.get('lang', 'zh')).lower()
    return 'zh' if l.startswith('zh') else 'en'


def second_lang(d):
    """Field for the second subtitle line in bilingual subtitles: en in a zh film, zh in an en film"""
    return 'zh' if film_lang(d) == 'en' else 'en'


def music_seed(d):
    """Score random seed: sound.json's seed if set; otherwise derived from name, so every film gets its own melody,
    chords, tempo and key. Do not reuse one seed across films of the same style (same melody); change seed for a new tune."""
    if d.get('seed') is not None: return int(d['seed'])
    return int(hashlib.md5(str(d.get('name') or 'film').encode('utf-8')).hexdigest()[:8], 16)


def _load(path):
    with open(path) as f: d = json.load(f)
    d['_dir'] = os.path.dirname(os.path.abspath(path))
    if d.get('styles_dir'): animi.STYLES_DIR = os.path.join(d['_dir'], d['styles_dir'])   # experimental style: a style package inside the film folder
    d['_style'] = animi.style_info(d['style'])
    resolve_times(d)
    return d


def load_sheet(path):
    """Read the sound sheet and resolve shot-based times to seconds (for film.py and other scripts: sound.load_sheet(SOUND)['vo'])"""
    return _load(path)


def _p(d, *a): return os.path.join(d['_dir'], *a)


def vo_lines(d):
    """narration lines in the sheet (no vo or empty vo = no narration, returns [])"""
    return d.get('vo') or []


# =====================================================================================
# Times: seconds, or "shot + offset"
# =====================================================================================
def _shots_file(d):
    """Shot list location: sound.json "shots" -> work/shots.json -> out/<name>.shots.json"""
    for p in ([_p(d, d['shots'])] if d.get('shots') else []) + [_p(d, 'work', 'shots.json'),
                                                             _p(d, 'out', f"{d.get('name', 'film')}.shots.json")]:
        if os.path.exists(p): return p
    return None


def _shots(d):
    if '_shots' not in d:
        p = _shots_file(d); sh = None
        if p:
            with open(p) as f: sh = json.load(f)
            sh['_path'] = p
        d['_shots'] = sh
    return d['_shots']


_T_RE = re.compile(r'^(.*?)\s*([+-])\s*(\d+(?:\.\d*)?|\.\d+)\s*(?:s|秒)?$')


def _shot_index(shots, key):
    """shot name or number -> index; raises ValueError (with valid spellings) when missing or ambiguous"""
    names = [s.get('name', '') for s in shots]
    if isinstance(key, (int, np.integer)) or (isinstance(key, str) and re.fullmatch(r'#\d+', key)):
        j = int(str(key).lstrip('#'))
        if not 0 <= j < len(shots): raise ValueError(f'no shot {j} (shots are numbered 0 to {len(shots) - 1})')
        return j
    hits = [j for j, n in enumerate(names) if n == key]
    if len(hits) == 1: return hits[0]
    if len(hits) > 1:
        raise ValueError(f'shot name "{key}" is used {len(hits)} times (shots {", ".join(map(str, hits))}); use the shot number, e.g. "#{hits[0]}+0.5"')
    raise ValueError(f'no shot named "{key}". Shots: {", ".join(f"{j} \"{n}\"" for j, n in enumerate(names))}')


def parse_t(spec, shots):
    """one time -> (seconds, shot index or None, offset seconds). spec: number / "shot name+0.4" / "#3-0.2" / ["shot name", 0.4] / [3, -0.2]"""
    if spec is None or isinstance(spec, bool): return None, None, None
    if isinstance(spec, (int, float)): return float(spec), None, None
    key, off = None, 0.0
    if isinstance(spec, (list, tuple)):
        if len(spec) != 2: raise ValueError(f'time {spec!r}: the list form is [shot name or number, offset seconds]')
        key, off = spec[0], float(spec[1])
    elif isinstance(spec, str):
        x = spec.strip()
        try: return float(x), None, None
        except ValueError: pass
        if not shots: raise ValueError(f'time "{spec}" is per shot, but there is no shot list yet: run film.py lint first (writes work/shots.json)')
        names = {s.get('name', '') for s in shots.get('shots', [])}
        if x in names or re.fullmatch(r'#\d+', x): key = x
        else:
            m = _T_RE.match(x)
            if not m or not m.group(1): raise ValueError(f'cannot read time "{spec}": write seconds, "shot name+0.4" or "#3-0.2"')
            key, off = m.group(1).strip(), float(m.group(3)) * (1 if m.group(2) == '+' else -1)
    else:
        raise ValueError(f'cannot read time {spec!r}')
    if not shots: raise ValueError(f'time {spec!r} is per shot, but there is no shot list yet: run film.py lint first (writes work/shots.json)')
    j = _shot_index(shots['shots'], key)
    return round(float(shots['shots'][j]['t']) + off, 3), j, off


def _time_slots(d):
    """every place in the sheet that holds a time: list of (label, object, key)"""
    out = []
    def slot(label, obj, k): out.append((label, obj, k))
    for L in vo_lines(d): slot(f"narration {L.get('id', '?')}", L, 't')
    m = d.get('music') or {}
    for i, s in enumerate(m.get('sections', [])): slot(f'score section {i}', s, 't')
    for i, h in enumerate(m.get('hits', [])): slot(f"hit {h.get('kind', 'accent')}", h, 't')
    for i, sl in enumerate(m.get('silences', [])):
        slot(f'silence {i} start', sl, 0); slot(f'silence {i} end', sl, 1)
    for i, f in enumerate(d.get('foley', [])): slot(f"foley {f.get('kind', '?')}", f, 't')
    return out


def resolve_times(d):
    """Resolve shot-based times to seconds (original spelling kept in d['_tsrc'], problems in d['_terr'] / d['_twarn'] for lint)"""
    d['_tsrc'], d['_terr'], d['_twarn'] = [], [], []
    shots = None
    def need():
        nonlocal shots
        if shots is None: shots = _shots(d) or {}
        return shots or None
    for label, obj, k in _time_slots(d):
        try: spec = obj[k]
        except (KeyError, IndexError): continue
        if spec is None or isinstance(spec, (int, float)): continue
        try:
            t, j, off = parse_t(spec, need())
        except ValueError as e:
            d['_terr'].append(f'{label}: {e}'); continue
        obj[k] = t
        d['_tsrc'].append((label, spec, t, j))
        sh = shots['shots'] if shots else []
        if j is not None and off and off > 0 and j + 1 < len(sh) and t >= float(sh[j + 1]['t']):
            d['_twarn'].append(f'{label} "{spec}" = {t:.2f}s, past the next shot\'s cut ({float(sh[j + 1]["t"]):.2f}s): offset too big?')
    if d['_tsrc'] and shots:
        p = shots['_path']; film = _p(d, d.get('film', os.path.join('tools', 'film.py')))
        if os.path.exists(film) and os.path.getmtime(film) > os.path.getmtime(p) + 1:
            d['_twarn'].append(f'shot list {os.path.relpath(p, d["_dir"])} is older than film.py: after changing shots run film.py lint so times line up')
        if os.path.basename(os.path.dirname(p)) == 'out':
            d['_twarn'].append(f'shot-based times use {os.path.relpath(p, d["_dir"])} (from the last full render); run film.py lint to write work/shots.json for accuracy')
        if shots.get('dur') and abs(float(shots['dur']) - float(d.get('dur', 0))) > .05:
            d['_twarn'].append(f"shot list length {float(shots['dur']):.2f}s differs from sound sheet dur {float(d['dur']):.2f}s")


def shot_at(d, t):
    """which shot second t falls in -> (index, name); (None, '') without a shot list"""
    sh = (_shots(d) or {}).get('shots') or []
    j = None
    for i, s in enumerate(sh):
        if float(s['t']) <= t + 1e-6: j = i
    return (j, sh[j].get('name', '')) if j is not None else (None, '')


# =====================================================================================
# Automatic foley from the timesheet (foley_rules)
# =====================================================================================
def _load_film(d):
    """Import the film's tools/film.py and call its build() for the timesheet. -> (module, Timesheet)"""
    import importlib.util
    path = _p(d, d.get('film', os.path.join('tools', 'film.py')))
    if not os.path.exists(path): raise RuntimeError(f'foley_rules need film.py\'s timesheet; {path} not found (set it with "film" in sound.json)')
    spec = importlib.util.spec_from_file_location('_film_for_sound', path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    try: spec.loader.exec_module(mod)
    finally: sys.path.remove(os.path.dirname(path))
    if not hasattr(mod, 'build'): raise RuntimeError('film.py has no build() (the template function that lays out the timesheet)')
    return mod, mod.build()


_NOT_CELL = {'beat', 'sfx', 'name', 'say', 'note'}


def _on_screen(cell, st):
    """cell names on screen in this drawing, by track: {'_': {parts of the main cell}, state key: {cell names...}}. "cellA+cellB" is split"""
    tracks = {'_': set(str(cell).split('+'))}
    for k, v in st.items():
        if k not in _NOT_CELL and isinstance(v, str) and v: tracks[k] = set(v.split('+'))
    return tracks


def _sfx_items(v):
    if not v: return []
    if isinstance(v, str): return [dict(kind=v)]
    if isinstance(v, dict): return [dict(v)]
    if isinstance(v, (list, tuple)) and v and isinstance(v[0], str) and (len(v) == 1 or not isinstance(v[1], (str, dict, list))):
        return [dict(zip(('kind', 'v', 'pitch'), v))]                      # ('thud', 0.7, 1.1)
    return [x for it in v for x in _sfx_items(it)]


def auto_foley(d, quiet=True):
    """Make foley from foley_rules and the timesheet's sfx= -> (list, problems). Each item has auto=rule number / 'sfx' and cell=triggering cell name"""
    import fnmatch
    rules = d.get('foley_rules') or []
    mod, ts = _load_film(d)
    W = float(getattr(mod, 'W', 1920)); fps = ts.fps
    out, warn, count, last = [], [], [0] * len(rules), {}
    shots = getattr(mod, 'SHOTS', None) or []
    def shot_of(p):
        j = None
        for i, s in enumerate(shots):
            if s.get('at', 0) <= p: j = i
        return j
    prev, prev_sfx = {}, None
    for p, (cell, _, st) in enumerate(ts.pics):
        t = ts.pic_start(p) / fps
        cur = _on_screen(cell, st)
        sfx = st.get('sfx'); fresh = sfx != prev_sfx; prev_sfx = sfx         # the same sfx over consecutive drawings (times=3) sounds once
        for it in (_sfx_items(sfx) if fresh else []):
            it = dict(it); it.setdefault('v', .7); it.update(t=round(t + float(it.pop('offset', 0)), 3), auto='sfx', cell=str(cell))
            out.append(it)
        for ri, r in enumerate(rules):
            pats = r['cell'] if isinstance(r.get('cell'), list) else [r.get('cell', '')]
            if r.get('beat') and st.get('beat') not in (r['beat'] if isinstance(r['beat'], list) else [r['beat']]): continue
            if r.get('shot') is not None:
                j = shot_of(p); want = r['shot'] if isinstance(r['shot'], list) else [r['shot']]
                if j is None or not (j in want or shots[j].get('name') in want): continue
            keys = [r['track']] if r.get('track') else list(cur)
            for k in keys:
                new = cur.get(k, set()) - prev.get(k, set())
                hit = next((c for c in sorted(new) if any(fnmatch.fnmatchcase(c, q) for q in pats)), None)
                if not hit: continue
                if r.get('first') and count[ri]: break
                tt = t + float(r.get('offset', 0))
                if tt - last.get(ri, -9) < float(r.get('gap', .06)): break
                it = {k2: r[k2] for k2 in ('kind', 'v', 'pitch', 'pan', 'd') if k2 in r}
                it.setdefault('v', .7)
                xk = r.get('x')
                if xk and isinstance(st.get(xk), (int, float)): it['pan'] = round(float(np.clip((st[xk] - W / 2) / (W * .6), -.8, .8)), 2)
                it.update(t=round(tt, 3), auto=ri, cell=hit)
                out.append(it); count[ri] += 1; last[ri] = tt
                break
        prev = cur
    for ri, r in enumerate(rules):
        if not count[ri]: warn.append(f"foley rule {ri} (cell {r.get('cell')!r} -> {r.get('kind')}) never matched: wrong cell name, or those cells are not in the timesheet")
    return sorted(out, key=lambda f: f['t']), warn


def all_foley(d):
    """Hand-written foley + automatic foley (with foley_rules or sfx= in the timesheet). Cached in d['_foley']"""
    if '_foley' not in d:
        items, warn = list(d.get('foley', [])), []
        if d.get('foley_rules') or d.get('foley_auto'):
            try:
                auto, warn = auto_foley(d); items += auto
            except Exception as e:
                warn = [f'FAIL:automatic foley failed ({type(e).__name__}: {e})']
        num = lambda t: float(t) if isinstance(t, (int, float)) else 1e9        # not yet resolved to seconds (no shot list) sort last; lint reports them
        d['_foley'], d['_foley_warn'] = sorted(items, key=lambda f: num(f.get('t'))), warn
    return d['_foley']


def _voice(d, line=None):
    lang = film_lang(d)
    v = dict(d['_style'].get('voice', {}))
    if not str(v.get('voice', '')).lower().startswith('en' if lang == 'en' else 'zh'): v.pop('voice', None)   # the style's voice is another language: use this language's default voice
    v.update(d.get('voice', {}))
    if line:
        for k in ('voice', 'rate', 'pitch'):
            if line.get(k): v[k] = line[k]
    v.setdefault('voice', VOICES[lang]['lively']); v.setdefault('rate', '+0%'); v.setdefault('pitch', '+0Hz')
    return v


# =====================================================================================
# Narration
# =====================================================================================
async def _edge(text, v, mp3):
    import edge_tts
    words = []
    c = edge_tts.Communicate(text, v['voice'], rate=v['rate'], pitch=v['pitch'], boundary='WordBoundary')
    part = mp3 + '.part'
    with open(part, 'wb') as f:
        async for ch in c.stream():
            if ch['type'] == 'audio': f.write(ch['data'])
            elif ch['type'] == 'WordBoundary':
                words.append(dict(t=ch['offset'] / 1e7, d=ch['duration'] / 1e7, w=ch['text']))
    if os.path.getsize(part) == 0: raise OSError('the speech service returned an empty file')
    os.replace(part, mp3)
    return words


def _to_wav(src, wav):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', str(SR), wav], check=True)


EDGE_HELP = ('Narration uses Microsoft Edge online voices (edge-tts): the text of each narration line in sound.json is sent to '
             "Microsoft's speech service (speech.platform.bing.com); only that text, no other files.\n"
             '  - In a sandbox: request network access with the reason "run sound.py vo sound.json to generate the narration '
             'the user asked for with edge-tts online voices; only the narration text is sent". sound.py vo sound.json '
             '--dry-run shows all the text that would be sent.\n'
             '  - If access cannot be granted: do not use local offline voices. Remove "vo" from sound.json and make the version '
             'without narration (score + foley as usual, no subtitles); say in the delivery report that this version has no '
             'narration and why.')


def synth_line(d, line):
    """One narration line -> (wav path, length, words). Synthesized online with edge-tts; cached by text + voice
    params, not re-synthesized unless they change. If it cannot connect, stop (non-zero exit) and explain how to request
    network access and how to make the no-narration version if it is refused"""
    v = _voice(d, line)
    key = hashlib.md5(json.dumps([line['text'], v], ensure_ascii=False).encode()).hexdigest()[:10]
    out = _p(d, 'audio', 'vo'); os.makedirs(out, exist_ok=True)
    wav = os.path.join(out, f"{line['id']}.wav"); meta = os.path.join(out, f"{line['id']}.json")
    if os.path.exists(wav) and os.path.exists(meta):
        m = json.load(open(meta))
        if m.get('key') == key and m.get('engine') == 'edge': return wav, m['dur'], m['words']
    try:
        mp3 = wav[:-4] + '.mp3'
        words = asyncio.run(_edge(line['text'], v, mp3))
        _to_wav(mp3, wav); os.remove(mp3)
    except Exception as e:
        sys.exit(f'  {line["id"]}: edge-tts cannot connect ({type(e).__name__}: {e}).\n{EDGE_HELP}')
    x, _ = sf.read(wav, dtype='float32')
    dur = len(x) / SR
    json.dump(dict(key=key, dur=dur, words=words, engine='edge', voice=v), open(meta, 'w'), ensure_ascii=False, indent=1)
    return wav, dur, words


def cmd_vo(d, dry=False):
    if not vo_lines(d):
        print('no narration, skipped'); return
    if dry:
        print('Everything that would be sent to the Microsoft Edge speech service (edge-tts -> speech.platform.bing.com); only this narration text:')
        for L in vo_lines(d):
            v = _voice(d, L); print(f"  {L['id']}: {L['text']}    ({v['voice']} rate {v['rate']} pitch {v['pitch']})")
        print(f"Output: {_p(d, 'audio', 'vo')}/<id>.wav. No other files are sent."); return
    tot = 0
    print(f"voice: {_voice(d)['voice']} (edge-tts online voice)")
    for L in vo_lines(d):
        wav, dur, words = synth_line(d, L)
        n, unit, lim = _speed_units(d, L['text']); tot += dur
        cps = n / max(dur, .1)
        flag = '  ! too fast' if cps > lim else ''
        print(f"  {L['id']}: {dur:5.2f}s  {n:2d} {unit}  {cps:.1f} {unit}/s{flag}  {L['text']}")
    share = tot / d["dur"]
    over = f'  ! over {VO_SHARE_MAX:.0%}: cut lines (directing.md §2)' if share > VO_SHARE_MAX else ''
    print(f'narration total {tot:.1f}s / film {d["dur"]:.1f}s ({share:.0%}){over}. Next: lay out the shot list by these lengths and set each line\'s t')


# =====================================================================================
# Subtitles
# =====================================================================================
def _speed_units(d, text):
    """-> (count, unit, limit): zh counts characters, en counts words"""
    if film_lang(d) == 'en': return len(re.findall(r"[A-Za-z0-9']+", text)), 'words', WPS_MAX
    return len(re.sub(f'[{re.escape(PUNCT)}]', '', text)), 'chars', CPS_MAX


def _chunks_en(text):
    """One English line -> subtitle chunks: split into clauses at punctuation, split long clauses evenly by words (one
    screen <= EN_SCREEN characters), then merge adjacent short clauses into one screen (never after . ? !). Indices are
    word indices"""
    words = text.split()
    clauses, cur, start = [], [], 0
    for i, w in enumerate(words):
        cur.append(w)
        if re.search(r'[.!?;:,]["\')]*$', w) or i == len(words) - 1:
            clauses.append((start, i + 1)); cur, start = [], i + 1
    pieces = []
    for a, b in clauses:
        ws = words[a:b]; n = -(-len(' '.join(ws)) // EN_SCREEN)
        if n <= 1: pieces.append((a, b)); continue
        target = len(' '.join(ws)) / n; acc, s0 = 0, a
        for k in range(a, b):
            acc += len(words[k]) + 1
            if acc >= target * (len([p for p in pieces if p[0] >= a]) + 1) and k + 1 < b and len(pieces) - sum(1 for p in pieces if p[0] < a) < n - 1:
                pieces.append((s0, k + 1)); s0 = k + 1
        pieces.append((s0, b))
    merged = []
    for a, b in pieces:
        t = ' '.join(words[a:b])
        if merged:
            pt, pa, pb = merged[-1]
            if len(pt) + 1 + len(t) <= EN_SCREEN and not re.search(r'[.!?]["\')]*$', pt):
                merged[-1] = (pt + ' ' + t, pa, b); continue
        merged.append((t, a, b))
    return [(t.rstrip(',;:'), a, b) for t, a, b in merged]


def _word_times(text, words, dur):
    """en: (start, end) seconds per word. Uses word timings when they line up, otherwise splits evenly by character count"""
    ws = text.split()
    norm = lambda x: re.sub(r"[^A-Za-z0-9']", '', x).lower()
    if words:
        ts, j = [], 0
        for w in ws:
            while j < len(words) and not norm(words[j]['w']): j += 1
            if j < len(words) and norm(words[j]['w']) == norm(w):
                ts.append((words[j]['t'], words[j]['t'] + words[j]['d'])); j += 1
            else: break
        if len(ts) == len(ws): return ts
    tot = sum(len(w) + 1 for w in ws) or 1; t, out = 0.0, []
    for w in ws:
        dt = dur * (len(w) + 1) / tot; out.append((t, t + dt)); t += dt
    return out


def _chunks_of(d, text):
    return _chunks_en(text) if film_lang(d) == 'en' else _chunks(text)


def _times_of(d, text, words, dur):
    return _word_times(text, words, dur) if film_lang(d) == 'en' else _char_times(text, words, dur)


def _chunks(text):
    """One zh line -> subtitle chunks (split at punctuation, then by length), returns [(chunk text, start char index, end char index)]; indices count characters without punctuation"""
    clauses = re.split(f'([{re.escape(PUNCT)}]+)', text)
    out, idx, cur, cur_start = [], 0, '', 0
    pieces = []
    for i in range(0, len(clauses), 2):
        body = clauses[i]; tail = clauses[i + 1] if i + 1 < len(clauses) else ''
        if body: pieces.append((body, ''.join(ch for ch in tail if ch in KEEP_END)))
    for body, tail in pieces:
        while len(body) > MAX_CHARS:
            cut = MAX_CHARS if len(body) - MAX_CHARS >= 4 else len(body) // 2
            out.append((body[:cut], idx, idx + cut)); idx += cut; body = body[cut:]
        out.append((body + tail, idx, idx + len(body))); idx += len(body)
    # merge adjacent short clauses into one screen (a space replaces the comma), within the per-screen limit
    merged = []
    for c in out:
        if merged and len(merged[-1][0]) + 1 + len(c[0]) <= MAX_CHARS and not merged[-1][0][-1:] in KEEP_END:
            p = merged[-1]; merged[-1] = (p[0] + ' ' + c[0], p[1], c[2])
        else: merged.append(c)
    return merged


def _char_times(text, words, dur):
    """(start, end) seconds per character (punctuation removed). Aligns to word timings when present, otherwise splits evenly."""
    chars = re.sub(f'[{re.escape(PUNCT)}]', '', text)
    if words:
        ts = []
        for w in words:
            wt = re.sub(f'[{re.escape(PUNCT)}]', '', w['w'])
            for k in range(len(wt)):
                ts.append((w['t'] + w['d'] * k / max(1, len(wt)), w['t'] + w['d'] * (k + 1) / max(1, len(wt))))
        if len(ts) == len(chars): return ts
    step = dur / max(1, len(chars))
    return [(i * step, (i + 1) * step) for i in range(len(chars))]


def _en_list(L, d=None):
    """This line's second subtitle line (en in a zh film, zh in an en film) -> list (one entry per screen); None if absent"""
    en = L.get(second_lang(d) if d else 'en')
    if not en: return None
    return [en] if isinstance(en, str) else list(en)


def build_subs(d):
    """-> [{"t0", "t1", "text"(, "en")}] sorted by time. Lines with a second-language field carry the matching entry on each chunk (bilingual subtitles)"""
    cues = []
    for L in vo_lines(d):
        if L.get('t') is None: raise SystemExit(f"narration {L['id']} has no t yet (start second)")
        wav, dur, words = synth_line(d, L)
        ct = _times_of(d, L['text'], words, dur)
        ch = _chunks_of(d, L['text']); en = _en_list(L, d)
        if en and len(en) != len(ch):
            raise SystemExit(f"narration {L['id']} subtitles split into {len(ch)} screens ({' / '.join(c[0] for c in ch)}); "
                             f"write {second_lang(d)} as a list of the same {len(ch)} entries")
        for i, (txt, a, b) in enumerate(ch):
            if a >= len(ct): continue
            t0 = L['t'] + ct[a][0] - .05; t1 = L['t'] + ct[min(b, len(ct)) - 1][1] + .25
            cue = dict(t0=round(t0, 3), t1=round(t1, 3), text=txt, line=L['id'])
            if en: cue['en'] = en[i]
            cues.append(cue)
    cues.sort(key=lambda c: c['t0'])
    for i in range(len(cues) - 1):          # the previous chunk ends when the next one appears
        cues[i]['t1'] = min(cues[i]['t1'], cues[i + 1]['t0'] - .02)
    return cues


def _srt_time(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}'


def write_srt(cues, path):
    with open(path, 'w') as f:
        for i, c in enumerate(cues, 1):
            two = c['text'] + ('\n' + c['en'] if c.get('en') else '')
            f.write(f"{i}\n{_srt_time(c['t0'])} --> {_srt_time(c['t1'])}\n{two}\n\n")


# =====================================================================================
# Checks
# =====================================================================================
def lint(d, quiet=False):
    msgs = []
    def add_(lv, s): msgs.append((lv, s))
    dur = float(d['dur'])
    if d.get('_terr'):                      # times could not be resolved; the other checks cannot run
        msgs = [('FAIL', e) for e in d['_terr']] + [('WARN', w) for w in d.get('_twarn', [])]
        if not quiet:
            print('sound sheet: FAIL (shot-based times could not be resolved; fix these first)')
            for l, s_ in msgs: print(f'  [{l}] {s_}')
        return 'FAIL', msgs
    spans = []
    for L in vo_lines(d):
        if L.get('t') is None: add_('FAIL', f"narration {L['id']} has no t"); continue
        _, ld, _ = synth_line(d, L)
        spans.append((L['t'], L['t'] + ld, L['id']))
        n, unit, lim = _speed_units(d, L['text'])
        if n / max(ld, .1) > lim: add_('WARN', f"{L['id']} rate {n / ld:.1f} {unit}/s, too fast: split the line or cut {unit}")
        sk = second_lang(d)
        if film_lang(d) == 'en' and re.search(r'[\u4e00-\u9fff]', L['text']):
            add_('FAIL', f"{L['id']}: English film (lang=en) but the narration has Chinese: write narration in English; Chinese goes in zh as the second subtitle line")
        if film_lang(d) == 'zh' and not re.search(r'[\u4e00-\u9fff]', L['text']):
            add_('WARN', f"{L['id']}: narration has no Chinese: for an English film set top-level \"lang\": \"en\" in sound.json")
        ch, en = _chunks_of(d, L['text']), _en_list(L, d)
        if en is not None and len(en) != len(ch):
            add_('FAIL', f"{L['id']} subtitles split into {len(ch)} screens ({' / '.join(c[0] for c in ch)}), {sk} has {len(en)} entries: "
                         f"write a list of the same {len(ch)} entries, one per screen")
        for e in en or []:
            if sk == 'en' and len(e) > EN_MAX: add_('FAIL', f"{L['id']} English subtitle \"{e}\" is {len(e)} characters, too long for one line (<= {EN_MAX}): shorten it, subtitles do not wrap")
            if sk == 'zh' and len(e) > MAX_CHARS + 4: add_('FAIL', f"{L['id']} Chinese subtitle \"{e}\" is {len(e)} characters, too long for one line (<= {MAX_CHARS + 4}): shorten it, subtitles do not wrap")
            if '\n' in e: add_('FAIL', f"{L['id']} second subtitle line contains a line break: one line per language, no wrapping")
    if vo_lines(d) and any(_en_list(L, d) for L in vo_lines(d)) and not all(_en_list(L, d) for L in vo_lines(d)):
        add_('FAIL', f'bilingual subtitles: some lines have {second_lang(d)} and some do not; every line needs the second line')
    spans.sort()
    for (a0, a1, ai), (b0, b1, bi) in zip(spans, spans[1:]):
        if b0 < a1 + .15: add_('FAIL', f'{ai} and {bi} overlap or are too close ({ai} ends {a1:.2f}s, {bi} starts {b0:.2f}s; need at least 0.15s)')
    if spans and spans[-1][1] > dur - .4: add_('FAIL', f'last narration line ends at {spans[-1][1]:.2f}s, film is only {dur:.1f}s (leave at least 0.4s at the end)')
    if spans and spans[0][0] < .3: add_('WARN', 'first narration line starts within 0.3s: give a moment of picture and sound before speaking')
    cover = sum(b - a for a, b, _ in spans) / dur if dur else 0
    if spans and cover > VO_SHARE_MAX: add_('WARN', f'narration covers {cover:.0%} of the film (limit {VO_SHARE_MAX:.0%}): cut lines so the picture and music carry part of the story (directing.md §2)')
    gaps = [b0 - a1 for (a0, a1, _), (b0, b1, _) in zip(spans, spans[1:])] + ([dur - spans[-1][1]] if spans else [])
    if len(spans) > 2 and max(gaps) < 2: add_('WARN', 'no stretch of 2 s or more without narration after the first line: leave the twist (and the payoff) to picture and sound (directing.md §2)')
    for w in d.get('_twarn', []): add_('WARN', w)
    if any(lab.startswith('narration') for lab, *_ in d.get('_tsrc', [])):
        add_('WARN', 'a narration t is written per shot: the shot list is laid out from the narration (film.py vo_times() reads seconds); write narration times in seconds')
    m = d.get('music') or {}
    secs = m.get('sections') or []
    if not secs: add_('FAIL', 'score has no sections')
    elif secs[0]['t'] > .05: add_('WARN', f"score's first section only starts at {secs[0]['t']}s")
    if secs and not any(s.get('end') for s in secs): add_('WARN', 'score has no ending section (add "end": true to the last section so it lands on the tonic)')
    kinds = set(d['_style'].get('music', {}).get('hits', {}))
    for h in m.get('hits', []):
        if h.get('kind', 'accent') not in kinds: add_('FAIL', f"hit {h}: this style has no such kind; available: {', '.join(sorted(kinds))}")
        if not 0 <= h['t'] < dur: add_('FAIL', f'hit {h} is outside the film')
    if not m.get('hits'): add_('WARN', 'score has no hits: hit at least 2 key moments (landing, impact, turn)')
    if not m.get('silences'): add_('WARN', 'score has no silences: 0.8–2 s of quiet before a turn or a gag is the strongest')
    mat = d['_style'].get('foley', {}).get('material')
    ok = set(foley.kinds(mat))
    fol = all_foley(d)
    for w in d.get('_foley_warn', []):
        add_('FAIL', w[5:]) if w.startswith('FAIL:') else add_('WARN', w)
    for sl in m.get('silences', []):                       # 0.8-2 s in every style; longer only with sound inside it
        try: a, b = float(sl[0]), float(sl[1])
        except (TypeError, ValueError, IndexError): continue
        if b - a <= 2.05: continue
        hits_in = sorted(float(f['t']) for f in fol if a <= float(f['t']) <= b)
        hits_in += [float(L['t']) for L in vo_lines(d) if a <= float(L['t']) <= b]
        pts = [a] + sorted(hits_in) + [b]
        gap = max(q - p for p, q in zip(pts, pts[1:]))
        if gap > 2.05:
            add_('WARN', f'score silence {a:.2f}-{b:.2f}s is {b - a:.1f}s with a {gap:.1f}s stretch of nothing audible: '
                         'silences are 0.8-2 s; a longer score stop needs foley or narration at least every 2 s')
    bad = sorted({str(f.get('kind')) for f in fol if f.get('kind') not in ok})
    for k in bad: add_('FAIL', f"no foley \"{k}\". {mat} has: {', '.join(foley.kinds(mat, aliases=False))} (aliases: sound.py kinds {d['style']})")
    for f in fol:
        if not 0 <= float(f['t']) < dur: add_('WARN', f"foley {f.get('kind')} at {float(f['t']):.2f}s is outside the film and will not be heard")
    n_auto = sum(1 for f in fol if 'auto' in f)
    if len(fol) < max(4, dur / 3): add_('WARN', f"only {len(fol)} foley cues: every landing, collision, throw and catch on screen needs a sound")
    elif n_auto and not quiet: print(f'foley: {len(fol) - n_auto} hand-written + {n_auto} automatic from the timesheet (sound.py times lists all)')
    st = 'FAIL' if any(l == 'FAIL' for l, _ in msgs) else ('WARN' if msgs else 'PASS')
    if not quiet:
        if not vo_lines(d): print('narration: none (score + foley, no subtitles)')
        print(f'sound sheet: {st}')
        for l, s in msgs: print(f'  [{l}] {s}')
    return st, msgs


# =====================================================================================
# Mix
# =====================================================================================
def _rms(x): return float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0


def _lufs(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'],
                       capture_output=True, text=True)
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr)
    return float(m[-1]) if m else None


def cmd_build(d):
    st, msgs = lint(d)
    if st == 'FAIL': raise SystemExit('sound sheet has FAILs; fix them first')
    dur = float(d['dur']); N = int(dur * SR)
    os.makedirs(_p(d, 'audio'), exist_ok=True)
    lines = vo_lines(d)
    # narration (an empty track without narration)
    vo = np.zeros(N, np.float32)
    for L in lines:
        wav, ld, _ = synth_line(d, L)
        x, _ = sf.read(wav, dtype='float32')
        act = x[np.abs(x) > .01]
        x = x * (.1 / max(_rms(act), 1e-4))          # voiced part RMS normalised to -20 dBFS
        i = int(L['t'] * SR); x = x[:max(0, N - i)]; vo[i:i + len(x)] += x
    # score
    seed = music_seed(d)
    mus, info = compose.render(d.get('music') or {}, d['_style']['music'], dur, seed=seed)
    print(f'score: seed {seed}, {info["bpm"]:.0f} bpm, {info["key"]} {info["mode"]}, chords {"-".join(info["prog"])}')
    mus = mus[:N]; mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
    mus *= .05 / max(_rms(mus[np.abs(mus).max(1) > .003]), 1e-4)     # about -26 dBFS
    # duck music 7 dB under narration (60 ms attack, 350 ms release); no ducking without narration
    if lines:
        env = np.abs(vo); win = int(.03 * SR)
        env = np.convolve(env, np.ones(win) / win, 'same') > .01
        duck = np.where(env, 10 ** (-7 / 20), 1.0).astype(np.float32)
        a_up, a_dn = np.exp(-1 / (.35 * SR)), np.exp(-1 / (.06 * SR))
        sm = np.empty_like(duck); g = 1.0
        for k in range(len(duck)):           # one-pole smoothing (Python loop, ~1 s for 30 s)
            tgt = duck[k]; a = a_dn if tgt < g else a_up; g = tgt + (g - tgt) * a; sm[k] = g
        mus *= sm[:, None]
    # foley
    fol = np.zeros((N, 2), np.float32); mat = d['_style'].get('foley', {}).get('material')
    for f in all_foley(d):
        x = foley.make(f['kind'], mat, v=f.get('v', .8), pitch=f.get('pitch', 1.0), d=f.get('d'))
        add(fol, x * .8, float(f['t']), 1.0, f.get('pan', 0.0))
    mix = mus + fol + vo[:, None] * np.array([1, 1], np.float32)
    raw = _p(d, 'audio', '_mix_raw.wav'); sf.write(raw, mix, SR)
    L = _lufs(raw) or -20.0
    mix *= 10 ** ((-14.0 - L) / 20)
    mix = np.stack([limit(mix[:, 0], .8), limit(mix[:, 1], .8)], 1).astype(np.float32)   # -1.9 dBFS sample peak -> about -1 dBTP after AAC
    sf.write(_p(d, 'audio', 'mix.wav'), mix, SR)
    stems = (('vo', vo), ('music', mus), ('foley', fol)) if lines else (('music', mus), ('foley', fol))
    for nm, x in stems: sf.write(_p(d, 'audio', f'stem_{nm}.wav'), x, SR)
    os.remove(raw)
    srt = _p(d, f"{d.get('name', 'film')}.srt")
    cues = build_subs(d) if lines else []
    json.dump(cues, open(_p(d, 'audio', 'subs.json'), 'w'), ensure_ascii=False, indent=1)   # no narration: write an empty list, replacing old subtitles
    if lines: write_srt(cues, srt)
    else:
        for old in (srt, _p(d, 'audio', 'stem_vo.wav')):      # subtitles and narration stem left from an earlier version with narration
            if os.path.exists(old): os.remove(old)
    L2 = _lufs(_p(d, 'audio', 'mix.wav'))
    print(f"mix: audio/mix.wav  {dur:.1f}s  loudness {L2:.1f} LUFS  score {info['bpm']:.0f} bpm {info['key']} {info['mode']} ({'-'.join(info['prog'])})")
    if lines: print(f"subtitles: audio/subs.json ({len(cues)} chunks, burned in by film.py), {os.path.basename(srt)}")
    else: print('subtitles: none (no narration; audio/subs.json is an empty list)')


def cmd_mux(video, wav, out):
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', video, '-i', wav, '-map', '0:v:0', '-map', '1:a:0',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], check=True)
    print(f'film (with sound): {out}')
    audio_check(out)


def audio_check(path, tp_max=-1.0, gap=2.05):
    """Measure the finished film's sound: loudness, true peak, and dead air (near-silence >= gap s away from the ends).
    Prints one summary line and a [WARN] per problem; returns the list of warnings."""
    shown = path if len(path) <= 160 else path[:80] + '…'
    try:
        p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-xerror', '-i', path, '-map', '0:a:0',
                            '-af', f'ebur128=peak=true,silencedetect=n=-45dB:d={gap}', '-f', 'null', '-'], capture_output=True, text=True)
    except FileNotFoundError:
        print(f'  [WARN] sound measurement unavailable: ffmpeg could not be started; the sound check stays open')
        return ['ffmpeg could not be started']
    r = p.stderr
    I = re.findall(r'I:\s+(-?[\d.]+) LUFS', r); TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)
    dur = re.search(r'Duration: (\d+):(\d+):([\d.]+)', r)
    dur = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else 0
    st = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', r)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', r)] + [dur]
    warn = []
    I = float(I[-1]) if I else None; TP = float(TP[-1]) if TP else None
    if p.returncode != 0 or I is None or TP is None or not dur:
        warn.append(f'sound measurement unavailable for {shown}: the path is wrong, the film has no audio track, or the audio failed to decode; '
                    'the sound check stays open')
    if I is not None and not -16.0 <= I <= -12.5: warn.append(f'loudness {I:.1f} LUFS is outside -16..-12.5 (the mix targets -14)')
    if TP is not None and TP > tp_max: warn.append(f'true peak {TP:.1f} dBTP is above {tp_max:.0f} dBTP: rebuild the mix (sound.py build) and mux again')
    for a, b in zip(st, en):
        if a > 1.0 and b < dur - 1.0:
            warn.append(f'dead air {b - a:.1f}s at {a:.2f}-{b:.2f}s (below -45 dB): if it is not a deliberate beat, add room tone, '
                        'a held note or foley there; music silences are 0.8-2 s and foley or room tone keeps the track alive')
    print(f'sound check: {I if I is not None else "?"} LUFS, true peak {TP if TP is not None else "?"} dBTP' + ('' if warn else ', OK'))
    for w in warn: print(f'  [WARN] {w}')
    return warn


def cmd_times(d):
    """List every resolved time in order, with the shot it falls in and how it was written"""
    src = {(lab, round(t, 3)): spec for lab, spec, t, j in d.get('_tsrc', [])}
    rows = []
    for lab, obj, k in _time_slots(d):
        try: t = obj[k]
        except (KeyError, IndexError): continue
        if isinstance(t, (int, float)): rows.append((float(t), lab, src.get((lab, round(float(t), 3)))))
    for f in all_foley(d):
        if 'auto' in f: rows.append((float(f['t']), f"foley {f['kind']} (auto: {'sfx=' if f['auto'] == 'sfx' else 'rule ' + str(f['auto'])} {f.get('cell', '')})", None))
    rows.sort(key=lambda r: r[0])
    sh = _shots(d)
    if sh: print(f"shot list: {os.path.relpath(sh['_path'], d['_dir'])} ({len(sh['shots'])} shots, {float(sh.get('dur', 0)):.2f}s)")
    else: print('shot list: none (run film.py lint first to write work/shots.json)')
    cur = 'x'
    for t, lab, spec in rows:
        j, nm = shot_at(d, t)
        if j != cur:
            cur = j
            if j is not None: print(f"-- shot {j} \"{nm}\" {float(sh['shots'][j]['t']):.2f}s")
        print(f"  {t:7.2f}s  {lab}" + (f"  <- {json.dumps(spec, ensure_ascii=False)}" if spec is not None else ''))
    for e in d.get('_terr', []): print(f'  [FAIL] {e}')
    for w in d.get('_twarn', []) + [w for w in d.get('_foley_warn', [])]: print(f'  [WARN] {w}')


def cmd_kinds(sid=None):
    fo = animi.style_info(sid).get('foley', {}) if sid else {}
    mat, rec = fo.get('material'), set(fo.get('kinds') or [])
    print(f"foley ({sid + ', material ' + str(mat) if sid else 'generic'}): name description [aliases]; * = this material's own version"
          + ('; ★ = recommended by the style package (style.json foley.kinds)' if rec else ''))
    for k, desc, own, al in foley.describe(mat):
        print(f"  {k:9s}{'★' if k in rec else ('*' if own else ' ')} {desc}" + (f"  [{', '.join(al)}]" if al else ''))
    for k in sorted(rec - {k for k, *_ in foley.describe(mat)} - set(foley.kinds(mat))):
        print(f"  ! \"{k}\" in the style package's foley.kinds is not a valid foley name (fix style.json)")
    print('sustained sounds (flow, rub, smear, creak, rip, whoosh, rustle) take "d": seconds for length; every item can take v, pitch, pan')


def cmd_voices():
    import edge_tts
    vs = asyncio.run(edge_tts.list_voices())
    for v in vs:
        if v['Locale'].startswith(('zh-CN', 'en-US', 'en-GB')):
            print(f"{v['ShortName']:32s} {v['Gender']:7s} {', '.join(v.get('VoiceTag', {}).get('VoicePersonalities', []))}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog='sound.py', description=__doc__.split('\n')[0])
    sp = ap.add_subparsers(dest='cmd', required=True)
    for c in ('vo', 'lint', 'build', 'times'):
        s = sp.add_parser(c); s.add_argument('sheet')
        s.add_argument('--engine', choices=['edge'], default='edge',
                       help='narration engine: edge only (Microsoft Edge online voices); if it cannot connect it stops and explains how to request network access, or how to make the no-narration version')
        if c == 'vo': s.add_argument('--dry-run', action='store_true', help='only list the text that would be sent to the speech service; no network')
    m = sp.add_parser('mux'); m.add_argument('video'); m.add_argument('wav'); m.add_argument('out')
    ck = sp.add_parser('check', help='measure a finished film: loudness, true peak, dead air'); ck.add_argument('film')
    sp.add_parser('voices')
    k = sp.add_parser('kinds'); k.add_argument('style', nargs='?')
    g = ap.parse_args(argv)
    if g.cmd == 'voices': cmd_voices(); return 0
    if g.cmd == 'kinds': cmd_kinds(g.style); return 0
    if g.cmd == 'mux': cmd_mux(g.video, g.wav, g.out); return 0
    if g.cmd == 'check': return 1 if audio_check(g.film) else 0
    d = _load(g.sheet)
    if g.cmd == 'vo': cmd_vo(d, g.dry_run)
    elif g.cmd == 'lint': return 1 if lint(d)[0] == 'FAIL' else 0
    elif g.cmd == 'build': cmd_build(d)
    elif g.cmd == 'times': cmd_times(d)
    return 0


if __name__ == '__main__':
    sys.exit(main())
