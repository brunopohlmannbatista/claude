#!/usr/bin/env python3
"""Review page: a local web page for showing the user something and collecting notes. One page, two modes:
  - Characters (only when the user asked to see them at intake): register the character sheets and main backgrounds
    once they are generated; the user picks an image and writes notes on it.
  - Film: the user pauses on a moment and writes a note (timecode and shot are attached automatically).
The user clicks Approve or Send to agent and the notes come straight back to the agent; no export.
One page per film folder. Only the latest registered version is shown; older versions (including the character
images) and their notes and replies fold up at the bottom of the page. The page UI follows `--lang` (zh or en).

    review.py add <film.mp4> --id <entry-id> [--title "<page title>"] [--known "issue you saw and haven't fixed" ...] [--lang zh|en] [--root <film folder>]
        --lang: page language = the language you talk to the user in (user writes English -> en). Omitted: reuse this
        folder's last language; first time: zh if the title contains Chinese characters, else en.
        Registers a film. The video and its shot list <name>.shots.json are copied to <root>/review/<entry-id>/, so
        later renders don't overwrite this version. The shot list drives the shot strip and the shot of each note;
        fps comes from the shot list, else from the video.
        Same id again = update this version (notes kept); a new id (e.g. film-v2) = the new version replaces the old
        one, whose notes and replies stay folded at the bottom.
    review.py add <img1.png> [<img2.png> ...] --id chars-v1 [--title ...] [--lang zh|en] [--root <film folder>]
        Registers a few images (character sheets, main backgrounds). Prefix a label: Hero=src/char_hero.png
        (otherwise the file name is used). Write labels in the user's language.
    review.py open   [--root <dir>] [--no-browser]   start the local server (reused if running), print the URL, open
        the system browser. --no-browser = only start and print the URL: use it when the agent has its own browser
        panel (e.g. the Codex app side panel) and open the URL there instead of a system browser.
    review.py notes  [--root <dir>]     print this version's verdict and all notes (number, timecode, frame, shot, text, replies)
    review.py wait   [--root <dir>] [--timeout s]   wait until the user clicks Approve or Send to agent (30 min; --timeout can only make it longer),
        then print the notes; exit code 3 on timeout
    review.py reply  <entry-id> <number> "<what you changed>" [--done] [--root <dir>]
        reply under that note on the page; --done marks it Fixed. Number may be n3 or 3.
    review.py build  [--root <dir>]     only regenerate <root>/review.html
    review.py serve  [--root <dir>] [--port N]   run the server in the foreground (open starts it in the background)

How notes reach the agent:
  - Server running (URL http://127.0.0.1:...): notes are saved to <root>/review.notes.json; after the user clicks a
    button `wait` returns at once, or the user says so in the chat and the agent runs `notes`. Answer with `reply`;
    replies appear on the page.
  - Server can't start (e.g. a sandbox blocks listening): the page opens as a local file, notes stay in the browser,
    and the user clicks "Copy notes" and pastes them into the chat.
Page shortcuts (focus outside text fields): Space play/pause, Left/Right one frame, Enter write a note at this moment.
"""
import os, re, sys, json, time, shutil, argparse, hashlib, subprocess, threading, html as _html
from datetime import datetime

PAGE, DATA, DIR = 'review.html', 'review.json', 'review'
NOTES, REPLIES, SUBMIT, SEEN, WAIT = 'review.notes.json', 'review.replies.json', 'review.submit.json', '.review.seen', '.review.wait.json'
LANGS = ('zh', 'en')


VIDEO = ('.mp4', '.mov', '.webm', '.m4v')
IMAGE = ('.png', '.jpg', '.jpeg', '.webp')


# ---------- data ----------
def _p(root, *name): return os.path.join(root, *name)


def _rj(path, default):
    try:
        with open(path, encoding='utf-8') as f: return json.load(f)
    except (OSError, ValueError): return default


def _wj(path, d):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _probe(path):
    """(fps, duration); None when unreadable"""
    if not shutil.which('ffprobe') or not os.path.exists(path): return None, None
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                            'stream=avg_frame_rate,r_frame_rate:format=duration', '-of', 'json', path],
                           capture_output=True, text=True, timeout=30)
        j = json.loads(r.stdout or '{}')
    except (OSError, ValueError, subprocess.SubprocessError): return None, None
    fps = None
    for st in j.get('streams', []):
        for k in ('avg_frame_rate', 'r_frame_rate'):
            a, _, b = (st.get(k) or '0/0').partition('/')
            try:
                v = float(a) / float(b or 1)
                if v > 0: fps = round(v, 3); break
            except (ValueError, ZeroDivisionError): pass
        if fps: break
    try: dur = float(j.get('format', {}).get('duration'))
    except (TypeError, ValueError): dur = None
    return fps, dur


def _from_old(d):
    """Old format (several entries, with stop points): keep only the film entry"""
    items = d.get('items') or []
    if 'films' in d:
        items = [dict(id=f.get('id'), title=f.get('title'), stage='成片', known=f.get('known', []), at=f.get('at', ''),
                      panels=[dict(kind='video', src=f.get('src'), shots=f.get('shots', []), dur=f.get('dur'))])
                 for f in d.get('films') or []]
    for it in items:
        if not isinstance(it, dict) or it.get('stage') not in ('成片', '', None): continue
        vid = next((p for p in it.get('panels') or [] if isinstance(p, dict) and p.get('kind') == 'video' and p.get('src')), None)
        if vid and it.get('id'):
            return dict(id=it['id'], title=it.get('title') or it['id'], src=vid['src'], name=os.path.basename(vid['src']),
                        shots=vid.get('shots') or [], dur=vid.get('dur'), fps=None, known=list(it.get('known') or []),
                        at=it.get('at', ''), thumbs=[])
    return None


def _load(root):
    d = _rj(_p(root, DATA), None)
    if not isinstance(d, dict): d = {}
    if 'film' not in d:
        try: film = _from_old(d)
        except Exception: film = None
        d = dict(title=film['title'] if film else '', film=film, history=[])
    d.setdefault('history', [])
    d.setdefault('title', (d.get('film') or {}).get('title', ''))
    return d


def _thumbs(root, video_abs, shots, fid):
    """Middle frame of each shot as the shot-strip thumbnail"""
    if not shots or not shutil.which('ffmpeg'): return []
    out = []
    for k, s in enumerate(shots):
        t0 = float(s.get('t', 0)); t1 = float(s.get('t1', t0 + 1))
        rel = os.path.join(DIR, fid, f'shot-{k + 1:02d}.jpg')
        try:
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{(t0 + t1) / 2:.3f}', '-i', video_abs, '-frames:v', '1',
                            '-vf', 'scale=320:-2', '-q:v', '5', _p(root, rel)], capture_output=True, timeout=30)
        except (OSError, subprocess.SubprocessError): pass
        out.append(rel if os.path.exists(_p(root, rel)) else '')
    return out if any(out) else []


def _ui(lang):
    """Built-in page text: zh for any Chinese code, en for everything else (other languages get the English page)"""
    return 'zh' if str(lang or '').lower().startswith('zh') else 'en'


def _lang(d, lang, title='', known=()):
    """Page language code (any, e.g. zh, en, ja): --lang if given; else this folder's last one; else zh if the title or
    known issues contain Chinese characters, otherwise en. The page itself is Chinese or English (_ui)"""
    if lang: return str(lang).strip().lower()
    if d.get('lang'): return d['lang']
    return 'zh' if re.search(r'[\u4e00-\u9fff]', (title or '') + ''.join(known or ())) else 'en'


def add_images(paths, fid, title='', root='.', known=(), lang=None):
    """Register a few images (character sheets, main backgrounds) -> page path. Each item may be 'label=path'"""
    if not re.fullmatch(r'[^/\\]+', fid) or fid in ('.', '..'): sys.exit(f'review: the entry id must not contain a slash: {fid}')
    d = _load(root)
    os.makedirs(_p(root, DIR, fid), exist_ok=True)
    imgs = []
    for i, raw in enumerate(paths):
        label, _, path = raw.partition('=') if ('=' in raw and '/' not in raw.split('=', 1)[0]) else ('', '', raw)
        src = os.path.abspath(path)
        if not os.path.exists(src): sys.exit(f'review: not found: {path}')
        if os.path.splitext(src)[1].lower() not in IMAGE: sys.exit(f'review: images must be {", ".join(IMAGE)}; got {path}')
        rel = os.path.join(DIR, fid, f'{i + 1:02d}-' + os.path.basename(src))
        shutil.copy(src, _p(root, rel))
        imgs.append(dict(src=rel, name=label.strip() or os.path.splitext(os.path.basename(src))[0]))
    d['lang'] = _lang(d, lang, title, known)
    title = (title or '').strip() or ('Characters and backgrounds' if _ui(d['lang']) == 'en' else '角色和背景')
    film = dict(id=fid, title=title, kind='images', images=imgs, src=imgs[0]['src'] if imgs else '', shots=[], dur=None,
                fps=24, known=list(known), at=datetime.now().strftime('%m-%d %H:%M'), thumbs=[])
    old = d.get('film')
    hist = [h for h in d['history'] if h.get('id') not in (fid, (old or {}).get('id'))]
    if old and old.get('id') != fid: hist.insert(0, old)
    d.update(title=title, film=film, history=hist)
    _wj(_p(root, DATA), d)
    return build(root)


def _web_copy(root, src, rel):
    """VP9/Opus copy of the film next to it -> relative path, or '' (some built-in browsers, e.g. the Codex app's, play no H.264: sound but a black picture)"""
    if src.lower().endswith('.webm') or not shutil.which('ffmpeg'): return ''
    out = os.path.splitext(rel)[0] + '.webm'
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-c:v', 'libvpx-vp9', '-deadline', 'realtime', '-cpu-used', '8',
                        '-row-mt', '1', '-b:v', '0', '-crf', '30', '-pix_fmt', 'yuv420p', '-c:a', 'libopus', '-b:a', '128k', _p(root, out)],
                       capture_output=True, text=True)
    if r.returncode:
        print('review: no WebM copy (ffmpeg without libvpx-vp9 / libopus?); browsers without H.264 will show a black picture', file=sys.stderr)
        return ''
    return out


def add(video, fid, title='', root='.', known=(), lang=None):
    """Register a film version (copies the video and shot list) and rebuild the page -> page path"""
    title = (title or '').strip() or os.path.splitext(os.path.basename(video))[0]
    src = os.path.abspath(video)
    if os.path.splitext(src)[1].lower() not in VIDEO: sys.exit(f'review: a film must be {", ".join(VIDEO)}; got {video} (for images, pass several image files)')
    if not os.path.exists(src): sys.exit(f'review: not found: {video}')
    if not re.fullmatch(r'[^/\\]+', fid) or fid in ('.', '..'): sys.exit(f'review: the entry id must not contain a slash: {fid}')
    d = _load(root)
    d['lang'] = _lang(d, lang, title, known)
    os.makedirs(_p(root, DIR, fid), exist_ok=True)
    rel = os.path.join(DIR, fid, os.path.basename(src))
    if os.path.abspath(_p(root, rel)) != src: shutil.copy(src, _p(root, rel))
    sj = os.path.splitext(src)[0] + '.shots.json'
    s = _rj(sj, None) or {}
    if s:
        dst = os.path.splitext(_p(root, rel))[0] + '.shots.json'
        if os.path.abspath(dst) != os.path.abspath(sj): shutil.copy(sj, dst)
    else: print(f'review: no {sj} (film.py writes it when rendering the full film); the page has no shot strip and notes carry no shot name', file=sys.stderr)
    shots = [dict(t=float(x.get('t', 0)), t1=x.get('t1'), name=x.get('name', ''), size=x.get('size', ''))
             for x in s.get('shots', []) if isinstance(x, dict)]
    fps, dur = _probe(src)
    dur = s.get('dur') or dur
    for k, x in enumerate(shots):
        if x['t1'] is None: x['t1'] = shots[k + 1]['t'] if k + 1 < len(shots) else dur
    film = dict(id=fid, title=title, src=rel, name=os.path.basename(src), shots=shots, dur=dur,
                fps=s.get('fps') or fps or 24, known=list(known), at=datetime.now().strftime('%m-%d %H:%M'),
                thumbs=_thumbs(root, src, shots, fid))
    web = _web_copy(root, src, rel)
    if web: film['web'] = web
    old = d.get('film')
    hist = [h for h in d['history'] if h.get('id') not in (fid, (old or {}).get('id'))]
    if old and old.get('id') != fid: hist.insert(0, old)
    d.update(title=title, film=film, history=hist)
    _wj(_p(root, DATA), d)
    return build(root)


def build(root='.'):
    d = _load(root)
    f = d.get('film')
    if f and not f.get('fps') and f.get('kind') != 'images':
        f['fps'] = _probe(_p(root, f['src']))[0] or 24
    key = 'review-' + hashlib.md5(os.path.abspath(root).encode()).hexdigest()[:10]
    lang = _ui(d.get('lang'))
    page = (TEMPLATE.replace('__TITLE__', _html.escape(d.get('title') or ('Review' if lang == 'en' else '审片台')))
            .replace('__SUFFIX__', 'Review' if lang == 'en' else '审片').replace('__LANG__', 'en' if lang == 'en' else 'zh-CN')
            .replace('__DATA__', json.dumps(d, ensure_ascii=False).replace('</', '<\\/'))
            .replace('__KEY__', key))
    out = _p(root, PAGE)
    with open(out, 'w', encoding='utf-8') as fh: fh.write(page)
    print(out)
    return out


# ---------- notes ----------
def _fmt(t):
    m = int(t // 60); return f'{m}:{t - 60 * m:05.2f}'


def _shot(film, t):
    k = -1
    for i, s in enumerate(film.get('shots') or []):
        if t + 1e-3 >= s['t']: k = i
    return k


def _nkey(n):
    t = n.get('t') if n.get('t') is not None else n.get('img')
    return (t is None, t or 0, int(re.sub(r'\D', '', n.get('nid', '')) or 0))


def _status(root, fid):
    st = (_rj(_p(root, NOTES), {}).get('items') or {}).get(fid) or {}
    sub = _rj(_p(root, SUBMIT), {})
    at = sub.get('at') or 0
    sent = bool(at) and sub.get('id', fid) == fid and at >= (st.get('saved_at') or 0)
    return st, sub, sent


def markdown(root='.'):
    d = _load(root); f = d.get('film')
    if not f: return 'Nothing registered on the review page yet (run review.py add <film.mp4> --id film-v1 first).\n'
    st, sub, sent = _status(root, f['id'])
    rep = _rj(_p(root, REPLIES), {})
    ns = sorted([n for n in st.get('notes') or [] if (n.get('text') or '').strip()], key=_nkey)
    fps = f.get('fps') or 24
    if sent:
        when = datetime.fromtimestamp(sub['at']).strftime('%m-%d %H:%M')
        verdict = ('approved' if st.get('verdict') == 'ok' else 'needs changes') + f' (sent {when})'
    elif ns: verdict = f'not sent yet ({len(ns)} notes on the page; the user has not clicked Approve or Send to agent)'
    else: verdict = 'no verdict yet'
    out = [f'# {f["title"]} ({f["id"]})', f'Verdict: {verdict}', f'Page language: {d.get("lang") or "zh"} (reply in this language)']
    if ns: out.append(f'{len(ns)} notes, in time order. Reply: review.py reply {f["id"]} <number> "what you changed" --done')
    else: out.append('No notes.')
    imgs = f.get('images') or []
    for n in ns:
        t = n.get('t')
        if n.get('img') is not None:
            k = int(n['img']); where = f'image {k + 1}' + (f' "{imgs[k]["name"]}"' if 0 <= k < len(imgs) else '')
        elif t is None: where = '(no time)'
        else:
            k = _shot(f, t); s = (f.get('shots') or [None])[k] if k >= 0 else None
            where = f'{_fmt(t)} · frame {int(t * fps + 1e-3) + 1}' + (f' · shot {k + 1} "{s["name"]}"' if s else '')
        out += ['', f'{n["nid"]} · {where}', f'  {n["text"].strip()}']
        r = rep.get(f'{f["id"]}/{n["nid"]}')
        if r: out.append(f'  ↳ {"fixed" if r.get("done") else "replied"}: {r["text"]}')
    return '\n'.join(out).rstrip() + '\n'


def notes(root='.'):
    if not os.path.exists(_p(root, NOTES)) and (_load(root).get('film')):
        print('No notes file yet: either the page was opened as a local file (notes are in the browser; ask the user to click Copy notes and paste them into the chat) or the user has not written any.')
        return None
    md = markdown(root); print(md)
    sub = _rj(_p(root, SUBMIT), {})
    if sub.get('at'):
        with open(_p(root, SEEN), 'w') as fh: fh.write(str(sub['at']))
    return md


def wait(root='.', timeout=1800, poll=2.0):
    timeout = max(float(timeout), 1800.0)   # --timeout can only lengthen the wait: the user gets at least 30 min
    try: seen = float(open(_p(root, SEEN)).read() or 0)
    except (OSError, ValueError): seen = 0
    import signal
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))   # a host killing the command still clears the "waiting" marker
    t0 = time.time()
    _wj(_p(root, WAIT), dict(pid=os.getpid(), since=t0, until=t0 + timeout))   # the page shows "the agent is waiting"
    try:
        while time.time() - t0 < timeout:
            if (_rj(_p(root, SUBMIT), {}).get('at') or 0) > seen:
                notes(root); return 0
            time.sleep(poll)
    finally:
        if (_rj(_p(root, WAIT), {}) or {}).get('pid') == os.getpid():
            try: os.remove(_p(root, WAIT))
            except OSError: pass
    print(f'The user did not click a button within {timeout:.0f} s. Tell the user (in their language): when done, click Approve or Send to agent on the page, or say so in the chat; then run review.py notes.')
    return 3


def reply(fid, nid, text, done=False, root='.'):
    nid = f'n{nid}' if str(nid).isdigit() else str(nid)
    st = (_rj(_p(root, NOTES), {}).get('items') or {}).get(fid) or {}
    if not any(n.get('nid') == nid for n in st.get('notes') or []):
        sys.exit(f'review: no note {nid} in {fid} (run review.py notes to see entry ids and numbers)')
    rep = _rj(_p(root, REPLIES), {})
    rep[f'{fid}/{nid}'] = dict(text=text, done=bool(done), at=time.time())
    _wj(_p(root, REPLIES), rep)
    print(f'replied {fid}/{nid}' + (' (fixed)' if done else ''))


def _waiting(root):
    """{since, until} while `review.py wait` runs for this folder, else None"""
    w = _rj(_p(root, WAIT), None)
    if not isinstance(w, dict) or (w.get('until') or 0) < time.time(): return None
    try: os.kill(int(w.get('pid')), 0)
    except (OSError, ValueError, TypeError): return None
    return dict(since=w.get('since'), until=w.get('until'))


# ---------- local server ----------
def _port(root):
    return 8700 + int(hashlib.md5(os.path.abspath(root).encode()).hexdigest(), 16) % 250


def _alive(port, root):
    import urllib.request
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/ping', timeout=1) as r:
            return json.load(r).get('root') == os.path.abspath(root)
    except Exception:
        return False


def serve(root='.', port=None):
    from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
    root = os.path.abspath(root); port = port or _port(root)
    lock = threading.Lock()

    def merge(fid, obj, now):
        st = _rj(_p(root, NOTES), {})
        if not isinstance(st, dict): st = {}
        items = st.setdefault('items', {})
        cur = items.get(fid) or {}
        notes = [dict(nid=str(n.get('nid')), t=n.get('t'), text=str(n.get('text', ''))[:4000],
                      **({'img': int(n['img'])} if isinstance(n.get('img'), int) else {}))
                 for n in obj.get('notes') or [] if isinstance(n, dict) and n.get('nid')]
        items[fid] = dict(notes=notes, verdict=cur.get('verdict', ''), seq=max(int(obj.get('seq') or 0), len(notes)), saved_at=now)
        st['saved_at'] = now
        _wj(_p(root, NOTES), st)

    class H(SimpleHTTPRequestHandler):
        def __init__(s, *a, **k): super().__init__(*a, directory=root, **k)
        def log_message(s, *a): pass

        def _json(s, obj, code=200):
            b = json.dumps(obj, ensure_ascii=False).encode()
            s.send_response(code); s.send_header('Content-Type', 'application/json; charset=utf-8')
            s.send_header('Cache-Control', 'no-store'); s.send_header('Content-Length', str(len(b))); s.end_headers(); s.wfile.write(b)

        def do_GET(s):
            u = s.path.split('?')[0]
            if u == '/': s.path = '/' + PAGE; u = s.path
            if u == '/api/ping': return s._json(dict(root=root))
            if u == '/api/state': return s._json(_rj(_p(root, NOTES), {}))
            if u == '/api/replies': return s._json(_rj(_p(root, REPLIES), {}))
            if u == '/api/ver':
                mt = lambda n: os.path.getmtime(_p(root, n)) if os.path.exists(_p(root, n)) else 0
                return s._json(dict(data=mt(PAGE), replies=mt(REPLIES), submit=_rj(_p(root, SUBMIT), {}), wait=_waiting(root)))
            rng = s.headers.get('Range')
            fp = s.translate_path(s.path)
            if rng and os.path.isfile(fp):                       # video seeking needs Range
                size = os.path.getsize(fp)
                m = re.match(r'bytes=(\d*)-(\d*)', rng)
                a = int(m.group(1)) if m and m.group(1) else 0
                b = int(m.group(2)) if m and m.group(2) else size - 1
                b = min(b, size - 1)
                s.send_response(206); s.send_header('Content-Type', s.guess_type(fp))
                s.send_header('Content-Range', f'bytes {a}-{b}/{size}')
                s.send_header('Content-Length', str(b - a + 1)); s.end_headers()
                with open(fp, 'rb') as f:
                    f.seek(a); left = b - a + 1
                    while left > 0:
                        chunk = f.read(min(1 << 20, left))
                        if not chunk: break
                        try: s.wfile.write(chunk)
                        except (BrokenPipeError, ConnectionResetError): return
                        left -= len(chunk)
                return
            try: return super().do_GET()
            except (BrokenPipeError, ConnectionResetError): return

        def end_headers(s):
            if s.path.endswith('.html'): s.send_header('Cache-Control', 'no-store')
            s.send_header('Accept-Ranges', 'bytes'); super().end_headers()

        def do_POST(s):
            n = int(s.headers.get('Content-Length', 0)); body = s.rfile.read(n) if n else b'{}'
            try: obj = json.loads(body or b'{}')
            except ValueError: return s._json(dict(error='bad json'), 400)
            if not isinstance(obj, dict): return s._json(dict(error='bad json'), 400)
            now = time.time()
            if s.path == '/api/state':
                with lock:
                    if obj.get('id'): merge(str(obj['id']), obj, now)
                return s._json(dict(ok=True, saved_at=now))
            if s.path == '/api/submit':
                with lock:
                    fid, verdict = str(obj.get('id') or ''), 'ok' if obj.get('verdict') == 'ok' else 'fix'
                    st = _rj(_p(root, NOTES), {})
                    if fid:
                        st.setdefault('items', {}).setdefault(fid, dict(notes=[], seq=0, saved_at=0))['verdict'] = verdict
                        _wj(_p(root, NOTES), st)
                    sub = _rj(_p(root, SUBMIT), {})
                    sub.update(at=time.time(), n=sub.get('n', 0) + 1, id=fid, verdict=verdict, waited=bool(_waiting(root)))
                    _wj(_p(root, SUBMIT), sub)
                return s._json(dict(ok=True, **sub))
            return s._json(dict(error='not found'), 404)

    httpd = ThreadingHTTPServer(('127.0.0.1', port), H)
    print(f'http://127.0.0.1:{port}/', flush=True)
    httpd.serve_forever()


def open_page(root='.', port=None, browser=True):
    root = os.path.abspath(root)
    if not os.path.exists(_p(root, PAGE)): build(root)
    port = port or _port(root)
    url = f'http://127.0.0.1:{port}/'
    if not _alive(port, root):
        log = open(_p(root, '.review.log'), 'a')
        subprocess.Popen([sys.executable, os.path.abspath(__file__), 'serve', '--root', root, '--port', str(port)],
                         stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True)
        for _ in range(30):
            if _alive(port, root): break
            time.sleep(0.2)
    if _alive(port, root):
        if browser: _browser(url)
        print(url)
        if not browser: print('(No system browser opened: open the URL above in your own browser panel.)')
        print('Notes are saved back to the film folder. `review.py wait` returns when the user clicks Approve or Send to agent; or run `review.py notes` after the user says so in the chat.')
        return url
    page = _p(root, PAGE)
    _browser(page)
    print(page)
    print(f'The local server did not start (see {_p(root, ".review.log")}; usually a sandbox blocks listening on a port: ask for permission and run open again). '
          'The page is open as a local file: notes stay in the browser; ask the user to click Copy notes and paste them into the chat.')
    return page


def _browser(target):
    if os.environ.get('REVIEW_NO_BROWSER'): return
    cmd = ['open', target] if sys.platform == 'darwin' else (['xdg-open', target] if shutil.which('xdg-open') else None)
    if cmd:
        try: subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError: pass


TEMPLATE = r'''<!doctype html>
<html lang="__LANG__">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · __SUFFIX__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500..700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
/* Review page · lemo-animi. The same bench as the gallery (docs/DESIGN.md): the film in a dark viewer with its
   controls on the deck below, a strip of its shots with pins stuck in it, notes on a paper pad beside it.
   Moves in steps, like the films. */
/* ---------- tokens:start (kept in sync with docs/assets/site.css) ---------- */
:root{
  --surface-0:#f4ede1; --surface-1:#ebe2d2; --surface-2:#fdf8ef;
  --ink:#1e1915; --ink-2:#645a4e; --ink-3:#6b6053; --line:#d9cdb8; --line-2:#c9bca4;
  --accent:#d2402f; --accent-ink:#b4321f; --accent-soft:#f7ddd6; --on-accent:#fff;
  --ok:#237057; --ok-soft:#d9ede3; --info:#3c5fa6; --info-soft:#dde6f6;
  --warn:#8f5b00; --warn-soft:#f8e9c4; --danger:#b02a1d; --danger-soft:#f6d9d4;
  --deck:#27211b; --deck-2:#352d25; --deck-ink:#f1e8d8; --deck-mute:#a89a86; --hole:rgba(244,237,225,.78);
  --tape:rgba(236,221,182,.85); --tape-ink:#5b4d35;
  --sh-1:0 1px 0 rgba(60,40,20,.06),0 10px 28px -14px rgba(60,40,20,.35);
  --sh-2:0 2px 0 rgba(60,40,20,.06),0 22px 44px -18px rgba(60,40,20,.45);
  --sh-hard:2px 2px 0 var(--ink); --sh-hard-up:3px 3px 0 var(--ink);
  --f-display:"Fraunces","Songti SC","Noto Serif SC","Source Han Serif SC",Georgia,serif;
  --f-sans:system-ui,-apple-system,"PingFang SC","Hiragino Sans GB","Noto Sans SC","Microsoft YaHei",sans-serif;
  --f-mono:"IBM Plex Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  --r-sm:6px; --r-md:10px; --r-lg:16px; --r-xl:22px;
  --s-1:4px; --s-2:8px; --s-3:12px; --s-4:16px; --s-5:24px; --s-6:32px; --s-7:48px; --s-8:64px; --s-9:96px;
  --t-xs:12px; --t-sm:13px; --t-md:15px; --t-lg:17px; --t-xl:20px;
  --btn-sm:32px; --btn-md:40px; --btn-lg:48px; --focus:0 0 0 2px var(--surface-0),0 0 0 4.5px var(--accent);
  --step:.12s steps(2,end);
  color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --surface-0:#15120f; --surface-1:#1d1814; --surface-2:#26201a;
    --ink:#f1e8da; --ink-2:#b3a694; --ink-3:#9a8d7e; --line:#38302a; --line-2:#4a4038;
    --accent:#ef6a56; --accent-ink:#ff8a76; --accent-soft:#3f231e; --on-accent:#15120f;
    --ok:#5fc49b; --ok-soft:#173327; --info:#8fb3ea; --info-soft:#1c2a42;
    --warn:#e9b949; --warn-soft:#3a2f12; --danger:#ff7f6c; --danger-soft:#45201b;
    --deck:#0f0d0b; --deck-2:#1c1813; --deck-ink:#efe6d6; --deck-mute:#9a8d7d; --hole:#3a332a;
    --tape:rgba(120,100,60,.45); --tape-ink:#e8d9b5;
    --sh-1:0 1px 0 rgba(0,0,0,.3),0 12px 30px -14px rgba(0,0,0,.75);
    --sh-2:0 2px 0 rgba(0,0,0,.3),0 24px 48px -18px rgba(0,0,0,.85);
    color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --surface-0:#15120f; --surface-1:#1d1814; --surface-2:#26201a;
  --ink:#f1e8da; --ink-2:#b3a694; --ink-3:#9a8d7e; --line:#38302a; --line-2:#4a4038;
  --accent:#ef6a56; --accent-ink:#ff8a76; --accent-soft:#3f231e; --on-accent:#15120f;
  --ok:#5fc49b; --ok-soft:#173327; --info:#8fb3ea; --info-soft:#1c2a42;
  --warn:#e9b949; --warn-soft:#3a2f12; --danger:#ff7f6c; --danger-soft:#45201b;
  --deck:#0f0d0b; --deck-2:#1c1813; --deck-ink:#efe6d6; --deck-mute:#9a8d7d; --hole:#3a332a;
  --tape:rgba(120,100,60,.45); --tape-ink:#e8d9b5;
  --sh-1:0 1px 0 rgba(0,0,0,.3),0 12px 30px -14px rgba(0,0,0,.75);
  --sh-2:0 2px 0 rgba(0,0,0,.3),0 24px 48px -18px rgba(0,0,0,.85);
  color-scheme:dark;
}
/* ---------- tokens:end ---------- */
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--surface-0);color:var(--ink);font:var(--t-md)/1.6 var(--f-sans);-webkit-font-smoothing:antialiased}
button{font:inherit;color:inherit;cursor:pointer;-webkit-tap-highlight-color:transparent}
.num{font-variant-numeric:tabular-nums}
:where(button,a,textarea,summary):focus-visible{outline:none;box-shadow:var(--focus);border-radius:var(--r-sm)}

/* ---------- buttons: one system, DESIGN.md ---------- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;height:var(--btn-md);padding:0 16px;border-radius:var(--r-md);border:1.5px solid var(--ink);background:var(--surface-2);color:var(--ink);font:600 14px/1 var(--f-sans);white-space:nowrap;user-select:none;box-shadow:var(--sh-hard);transition:transform var(--step),box-shadow var(--step),background-color var(--step)}
.btn:hover{transform:translate(-1px,-1px);box-shadow:var(--sh-hard-up)}
.btn:active{transform:translate(1px,1px);box-shadow:0 0 0 var(--ink)}
.btn:focus-visible{box-shadow:var(--sh-hard),var(--focus)}
.btn:disabled{opacity:.45;box-shadow:none;transform:none;cursor:not-allowed}
.btn svg{width:18px;height:18px;flex:none}
.btn.primary{background:var(--ink);color:var(--surface-0);--sh-hard:2px 2px 0 var(--accent);--sh-hard-up:3px 3px 0 var(--accent)}
.btn.primary:active{box-shadow:0 0 0 var(--accent)}
.btn.ok{border-color:var(--ok);color:var(--ok);--sh-hard:2px 2px 0 var(--ok);--sh-hard-up:3px 3px 0 var(--ok)}
.btn.ok:active{box-shadow:0 0 0 var(--ok)}
.btn.quiet{border-color:transparent;background:transparent;color:var(--ink-2);box-shadow:none}
.btn.quiet:hover{background:var(--surface-1);color:var(--ink);transform:none;box-shadow:none}
.btn.quiet:active{transform:translateY(1px)}
.btn.quiet:focus-visible{box-shadow:var(--focus)}
.btn.icon{padding:0;width:var(--btn-md)}
.btn.sm{height:var(--btn-sm);padding:0 12px;font-size:var(--t-sm);border-radius:8px}
.btn.sm svg{width:16px;height:16px}
.btn.sm.icon{width:var(--btn-sm)}
.btn.lg{height:var(--btn-lg);padding:0 22px;font-size:15px;border-radius:12px}
.btn.lg.icon{width:var(--btn-lg)}
.btn.pill{border-radius:999px}

/* pills: status, never actions */
.pill{display:inline-flex;align-items:center;gap:8px;height:28px;padding:0 12px;border-radius:999px;font:600 var(--t-sm)/1 var(--f-sans);white-space:nowrap;background:var(--surface-1);color:var(--ink-2)}
.pill::before{content:"";width:7px;height:7px;border-radius:50%;background:currentColor;flex:none}
.pill.ok{background:var(--ok-soft);color:var(--ok)}
.pill.info{background:var(--info-soft);color:var(--info)}
.pill.warn{background:var(--warn-soft);color:var(--warn)}
.pill.hollow::before{background:transparent;border:1.5px solid currentColor;box-sizing:border-box}
.pill.live::before{animation:breathe 2.4s steps(6,end) infinite}
@keyframes breathe{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.7)}}
/* a strip of masking tape */
.tape{display:inline-flex;align-items:center;gap:8px;position:relative;font:600 var(--t-xs)/1 var(--f-mono);letter-spacing:.1em;text-transform:uppercase;color:var(--tape-ink);background:var(--tape);padding:7px 12px;transform:rotate(-1.2deg);transform-origin:left center}
.tape::before,.tape::after{content:"";position:absolute;top:0;bottom:0;width:6px;background:inherit}
.tape::before{left:-4px;clip-path:polygon(100% 0,100% 100%,0 85%,45% 65%,10% 45%,55% 25%,20% 5%)}
.tape::after{right:-4px;clip-path:polygon(0 0,0 100%,100% 90%,50% 70%,85% 50%,40% 30%,80% 10%)}
:lang(zh-CN) .tape{font-family:var(--f-sans);letter-spacing:.08em}

/* ---------- header ---------- */
header{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--surface-0) 88%,transparent);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.bar{max-width:1840px;margin:0 auto;padding:12px 24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.mark{display:inline-flex;align-items:center;gap:9px;font:600 var(--t-xs)/1 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2);white-space:nowrap}
:lang(zh-CN) .mark{font-family:var(--f-sans);letter-spacing:.08em;font-size:var(--t-sm)}
.mark i{width:16px;height:16px;border-radius:50%;background:var(--accent);box-shadow:inset -3px -4px 0 rgba(0,0,0,.18)}
.mark svg{display:none}
.ttl{min-width:0;flex:1 1 260px;padding-left:14px;margin-left:2px;border-left:1px solid var(--line-2);display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.ttl h1{font:600 22px/1.2 var(--f-display);letter-spacing:-.01em;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;max-width:100%}
.ttl .ver{color:var(--ink-3);font:var(--t-xs)/1.4 var(--f-mono);white-space:nowrap}
.state{color:var(--ink-2)}
.state.ok{background:var(--ok-soft);color:var(--ok)}
.state.sent{background:var(--info-soft);color:var(--info)}
.state.draft{background:var(--warn-soft);color:var(--warn)}
.wait{cursor:help;background:transparent;color:var(--ink-3);padding:0 6px}
.wait::before{background:transparent;border:1.5px solid currentColor;box-sizing:border-box}
.wait.on{color:var(--ok);background:var(--ok-soft);padding:0 12px} .wait.on::before{background:currentColor;border:0;animation:breathe 2.4s steps(6,end) infinite}
.banner{display:none;max-width:1840px;margin:0 auto;padding:0 24px 12px}
.banner div{padding:10px 16px;border-radius:var(--r-md);font-size:14px;font-weight:600;display:flex;gap:10px;align-items:center}
.banner div::before{content:"";width:8px;height:8px;border-radius:50%;background:currentColor;flex:none}
.banner.on{display:block}
#sentBanner div{background:var(--info-soft);color:var(--info)}
#sentBanner.ok div{background:var(--ok-soft);color:var(--ok)}
#newBanner div{background:var(--warn-soft);color:var(--warn);cursor:pointer}
#newBanner div::before{animation:breathe 1.6s steps(4,end) infinite}

/* ---------- the viewer: screen on top, controls on the deck below ---------- */
.room{max-width:1840px;margin:0 auto;padding:24px;display:grid;grid-template-columns:minmax(0,1fr) clamp(340px,27vw,440px);gap:28px;align-items:stretch}
.stage{min-width:0}
.stage-in{display:grid;gap:14px}
.viewer{border-radius:var(--r-lg);background:var(--deck);box-shadow:var(--sh-2),0 0 0 1px rgba(255,255,255,.06);overflow:hidden}
.screen{position:relative;background:#000;aspect-ratio:16/9;max-height:calc(100vh - 360px);min-height:180px;width:100%;margin:0 auto}
.screen video{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;display:block;cursor:pointer}
.big{position:absolute;left:50%;top:50%;width:80px;height:80px;margin:-40px 0 0 -40px;border-radius:50%;border:0;background:rgba(253,248,239,.94);color:#1e1915;display:flex;align-items:center;justify-content:center;box-shadow:0 8px 24px rgba(0,0,0,.35);transition:opacity .15s steps(2),transform var(--step)}
.big:hover{transform:scale(1.06)}
.big svg{width:30px;height:30px;margin-left:5px}
.playing .big{opacity:0;pointer-events:none}
.screen:fullscreen{max-height:none;border-radius:0}
.ctrl{display:flex;align-items:center;gap:4px;flex-wrap:wrap;padding:8px 10px;background:var(--deck);color:var(--deck-ink);border-top:1px solid rgba(255,255,255,.08)}
.ib{border:1.5px solid transparent;background:transparent;width:38px;height:38px;border-radius:var(--r-md);display:inline-flex;align-items:center;justify-content:center;color:var(--deck-ink);transition:background-color var(--step),transform var(--step)}
.ib:hover{background:rgba(255,255,255,.1)}
.ib:active{transform:translateY(1px)}
.ib:focus-visible{box-shadow:0 0 0 2px var(--deck),0 0 0 4.5px var(--accent)}
.ib svg{width:19px;height:19px}
.ib.main{background:var(--deck-ink);color:var(--deck);width:44px;height:38px;margin-right:4px;border-radius:var(--r-md)}
.ib.main:hover{background:#fff}
.ib.main svg{width:20px;height:20px}
.tm{font:500 19px/1 var(--f-mono);margin:0 10px 0 8px;white-space:nowrap;color:var(--deck-ink)}
.tm .d{color:var(--deck-mute)}
.where{color:var(--deck-mute);font:var(--t-sm)/1.3 var(--f-mono);min-width:0;flex:1 1 160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.where b{color:var(--deck-ink);font-weight:600}
.rate{border:1.5px solid rgba(255,255,255,.22);background:transparent;color:var(--deck-ink);border-radius:8px;height:30px;padding:0 10px;font:600 var(--t-xs)/1 var(--f-mono);min-width:46px;transition:background-color var(--step)}
.rate:hover{background:rgba(255,255,255,.1)}
.rate:focus-visible{box-shadow:0 0 0 2px var(--deck),0 0 0 4.5px var(--accent)}

/* film strip: one frame per shot, width by duration; note pins stuck in above; a playhead */
.reel{position:relative;padding-top:34px;cursor:pointer;touch-action:none;user-select:none}
.film{position:relative;background:var(--deck);border-radius:var(--r-md);padding:12px 6px;box-shadow:var(--sh-1),0 0 0 1px rgba(255,255,255,.06);
  background-image:radial-gradient(circle at 50% 50%,var(--hole) 0 2.4px,transparent 2.9px),radial-gradient(circle at 50% 50%,var(--hole) 0 2.4px,transparent 2.9px);
  background-size:14px 12px,14px 12px;background-repeat:repeat-x;background-position:0 0,0 100%}
.shots{position:relative;display:flex;gap:3px;height:66px}
.shots.blank{background:var(--deck-2)}
.shot{position:relative;flex:1 1 0;min-width:0;border:none;padding:0;background:var(--deck-2);overflow:hidden;text-align:left;border-radius:4px}
.shot img{display:block;width:100%;height:100%;object-fit:cover;opacity:.5;transition:opacity var(--step)}
.shot:hover img{opacity:.8}
.shot .cap{position:absolute;left:0;right:0;bottom:0;display:flex;gap:6px;align-items:center;padding:16px 7px 5px;font:var(--t-xs)/1.2 var(--f-mono);color:#fff;background:linear-gradient(transparent,rgba(10,8,6,.85));white-space:nowrap;overflow:hidden}
.shot .cap b{flex:none;font:600 10.5px/17px var(--f-mono);min-width:17px;height:17px;border-radius:4px;background:rgba(253,248,239,.94);color:#1e1915;text-align:center;padding:0 3px}
.shot .cap span{overflow:hidden;text-overflow:ellipsis;display:none}
.shot.on .cap span,.shot:hover .cap span{display:inline}
.shot .pg{position:absolute;left:0;bottom:0;height:3px;background:var(--accent);width:0}
.shot .cnt{display:none}
.shot.on img{opacity:1}
.shot.on{box-shadow:inset 0 0 0 2px #fdf8ef}
.shot:focus-visible{box-shadow:inset 0 0 0 2.5px var(--accent)}
#ticks{display:none}
.reel .fi{position:absolute;left:0;bottom:-8px;height:3px;border-radius:2px;background:var(--accent)}
.reel .knob{position:absolute;top:26px;bottom:-8px;width:2px;margin-left:-1px;background:var(--ink);pointer-events:none;border-radius:1px}
.reel .knob::before{content:"";position:absolute;left:-5px;top:-4px;width:12px;height:12px;border-radius:50%;background:var(--ink)}
#marks{position:absolute;left:0;right:0;top:0;height:30px}
.mk{position:absolute;top:0;width:22px;height:22px;margin-left:-11px;padding:0;border:0;border-radius:50% 50% 50% 4px;transform:rotate(-45deg);background:var(--accent);color:var(--on-accent);font:600 11px/22px var(--f-mono);text-align:center;box-shadow:0 2px 6px rgba(60,20,10,.25);transition:transform var(--step)}
.mk > *{display:none}
.mk::before{content:attr(data-n);display:block;transform:rotate(45deg)}
.mk.done{background:var(--ok);color:#fff}
.mk:hover{transform:rotate(-45deg) translate(2px,-2px)}
.mk:focus-visible{border-radius:50% 50% 50% 4px}
.keys{color:var(--ink-3);font-size:var(--t-xs);line-height:1.8}
kbd{font:11px var(--f-mono);border:1px solid var(--line-2);border-bottom-width:2px;border-radius:5px;padding:0 5px;color:var(--ink-2);background:var(--surface-2)}
/* image mode: a light table */
.view{position:relative;background:var(--surface-2);border-radius:var(--r-lg);overflow:hidden;display:flex;align-items:center;justify-content:center;height:calc(100vh - 350px);min-height:240px;box-shadow:var(--sh-1),0 0 0 1px var(--line)}
.view img{max-width:100%;max-height:100%;object-fit:contain;display:block;background:repeating-conic-gradient(var(--surface-1) 0 25%,var(--surface-2) 0 50%) 0 0/20px 20px;cursor:zoom-in}
.view .nav{position:absolute;top:50%;margin-top:-20px;width:40px;height:40px;border-radius:var(--r-md);border:1.5px solid var(--ink);background:var(--surface-2);color:var(--ink);display:flex;align-items:center;justify-content:center;box-shadow:var(--sh-hard);transition:transform var(--step),box-shadow var(--step)}
.view .nav:hover{transform:translate(-1px,-1px);box-shadow:var(--sh-hard-up)}
.view .nav:active{transform:translate(1px,1px);box-shadow:0 0 0 var(--ink)}
.view .nav svg{width:20px;height:20px}
.view .nav.l{left:14px} .view .nav.r{right:14px}
.vcap{display:flex;gap:10px;align-items:baseline;font-size:var(--t-md)}
.vcap b{font:600 18px/1.3 var(--f-display)}
.vcap .d{color:var(--ink-3);font:var(--t-sm) var(--f-mono)}
.thumbs{display:flex;gap:6px;overflow-x:auto;scrollbar-width:thin}
.thumbs.film{padding:12px 8px}
.thumb{position:relative;flex:none;width:136px;border:none;padding:0;border-radius:4px;background:var(--deck-2);overflow:hidden;text-align:left}
.thumb img{display:block;width:100%;height:86px;object-fit:contain;opacity:.55;transition:opacity var(--step)}
.thumb:hover img{opacity:.85}
.thumb .cap{display:block;padding:4px 8px 5px;font-size:var(--t-xs);color:var(--deck-ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.thumb .cap b{font-family:var(--f-mono);margin-right:5px}
.thumb .cnt{position:absolute;top:5px;right:5px;min-width:20px;height:20px;padding:0 5px;border-radius:999px;background:var(--accent);color:var(--on-accent);font:600 11px/20px var(--f-mono);text-align:center}
.thumb.on{box-shadow:inset 0 0 0 2px #fdf8ef} .thumb.on img{opacity:1}
.thumb:focus-visible{box-shadow:inset 0 0 0 2.5px var(--accent)}
@media (max-width:760px){.view{height:auto;min-height:0;aspect-ratio:4/3}}

/* ---------- the notes pad ---------- */
.desk{position:relative;min-height:0}
.desk-in{position:absolute;inset:0;overflow:auto;display:flex;flex-direction:column;gap:18px;scrollbar-width:thin;border-radius:var(--r-lg);padding-top:8px}
.desk-in > .sheet{flex:1 0 auto}
@media (max-width:1000px){.room{grid-template-columns:minmax(0,1fr)} .desk-in{position:static;overflow:visible}}
.sheet{position:relative;background:var(--surface-2);border-radius:var(--r-lg);padding:22px 20px 22px;box-shadow:var(--sh-1),0 0 0 1px var(--line)}
.known{background:var(--warn-soft);border-radius:var(--r-md);padding:11px 14px 12px;margin:0 0 18px;font-size:14px;color:var(--ink)}
.known b{color:var(--warn);font-weight:600;font-size:var(--t-xs);letter-spacing:.02em}
.known ul{margin:4px 0 0;padding-left:18px}
.lh{display:flex;align-items:center;gap:10px;margin:-30px 0 16px}
.lh h2{margin:0;font:600 var(--t-xs)/1 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--tape-ink);background:var(--tape);padding:8px 14px;transform:rotate(-1.5deg);transform-origin:left center;position:relative}
:lang(zh-CN) .lh h2{font-family:var(--f-sans);font-size:var(--t-sm);letter-spacing:.1em}
.lh h2::before,.lh h2::after{content:"";position:absolute;top:0;bottom:0;width:6px;background:inherit}
.lh h2::before{left:-4px;clip-path:polygon(100% 0,100% 100%,0 85%,45% 65%,10% 45%,55% 25%,20% 5%)}
.lh h2::after{right:-4px;clip-path:polygon(0 0,0 100%,100% 90%,50% 70%,85% 50%,40% 30%,80% 10%)}
.lh .num{font:600 var(--t-xs)/22px var(--f-mono);color:var(--on-accent);background:var(--accent);border-radius:999px;min-width:22px;height:22px;text-align:center;padding:0 7px}
.lh .num:empty{display:none}
/* the compose box: an index card */
.compose{border:1.5px solid var(--line-2);border-radius:var(--r-md);background:var(--surface-0);padding:12px 14px;margin-bottom:12px;transition:border-color var(--step),box-shadow var(--step)}
.compose:focus-within{border-color:var(--ink);background:var(--surface-2);box-shadow:var(--sh-hard)}
.at{display:flex;gap:10px;align-items:center;font-size:var(--t-sm);color:var(--ink-2);margin-bottom:6px;min-width:0}
.at span:last-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tc{flex:none;border:none;background:var(--accent-soft);color:var(--accent-ink);padding:3px 9px;font:600 var(--t-xs)/1.4 var(--f-mono);font-variant-numeric:tabular-nums;border-radius:var(--r-sm);transition:background-color var(--step),color var(--step)}
button.tc:not(:disabled):hover{background:var(--accent);color:var(--on-accent)}
.tc:disabled{cursor:default}
textarea{font:inherit;font-size:var(--t-md);line-height:1.6;width:100%;border:0;border-radius:0;padding:4px 0;background:transparent;color:var(--ink);resize:none;min-height:52px;outline:none;overflow:hidden}
textarea::placeholder{color:var(--ink-3)}
.crow{display:flex;align-items:center;gap:8px;margin-top:8px}
.crow .h{flex:1;color:var(--ink-3);font-size:var(--t-xs)}
.list{list-style:none;margin:0;padding:0;counter-reset:n}
.empty{color:var(--ink-3);font-size:14px;padding:26px 10px;text-align:center}
.note{position:relative;counter-increment:n;padding:14px 8px 14px 42px;border-bottom:1px solid var(--line);transition:background-color var(--step);border-radius:0}
.note::before{content:counter(n);position:absolute;left:6px;top:14px;width:24px;height:24px;border-radius:50%;background:var(--ink);color:var(--surface-0);font:600 var(--t-xs)/24px var(--f-mono);text-align:center}
.note.hot{background:var(--accent-soft);border-radius:var(--r-md)}
.note.hot::before{background:var(--accent);color:var(--on-accent)}
.nh{display:flex;align-items:center;gap:10px;font:var(--t-xs)/1.4 var(--f-mono);color:var(--ink-2);min-width:0}
.nh .sh{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.nh .sp{flex:1}
.nb{border:none;background:none;color:var(--ink-3);font:600 var(--t-xs)/1 var(--f-sans);height:26px;padding:0 9px;border-radius:var(--r-sm);transition:background-color var(--step),color var(--step)}
.nb:hover{color:var(--ink);background:var(--surface-1)}
.nb.del:hover{color:var(--danger);background:var(--danger-soft)}
@media (hover:hover){ .note .nb{opacity:0;transition:opacity var(--step)} .note:hover .nb,.note:focus-within .nb{opacity:1} }
.nt{margin-top:6px;white-space:pre-wrap;word-break:break-word;font-size:var(--t-md)}
.edit textarea{margin-top:6px;min-height:56px;border:1.5px solid var(--line-2);border-radius:var(--r-md);padding:8px 10px;background:var(--surface-0)}
.edit textarea:focus{border-color:var(--ink)}
.edit .crow{justify-content:flex-end}
.rep{margin-top:8px;padding:8px 12px;border-radius:var(--r-md);background:var(--info-soft);font-size:14px;color:var(--ink);white-space:pre-wrap;word-break:break-word;border-left:3px solid var(--info)}
.rep .bd{display:inline-block;font:600 11.5px/1.7 var(--f-sans);background:var(--info);color:#fff;border-radius:999px;padding:0 8px;margin-right:8px}
.rep.done{background:var(--ok-soft);border-left-color:var(--ok)}
.rep.done .bd{background:var(--ok)}
:root[data-theme="dark"] .rep .bd,:root[data-theme="dark"] .mk.done{color:#15120f}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]) .rep .bd,:root:not([data-theme="light"]) .mk.done{color:#15120f} }
.hist{padding:0 4px}
.hist h2{font:600 var(--t-xs)/1 var(--f-mono);letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3);margin:0 0 10px}
:lang(zh-CN) .hist h2{font-family:var(--f-sans);font-size:var(--t-sm);letter-spacing:.1em}
details{background:var(--surface-2);border-radius:var(--r-md);margin-bottom:8px;box-shadow:var(--sh-1),0 0 0 1px var(--line)}
summary{cursor:pointer;padding:12px 16px;font-size:14px;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;list-style:none;border-radius:var(--r-md)}
summary::-webkit-details-marker{display:none}
summary::before{content:"";width:7px;height:7px;border-right:2px solid var(--ink-3);border-bottom:2px solid var(--ink-3);transform:rotate(-45deg);margin-right:2px;align-self:center;transition:transform var(--step)}
details[open] summary::before{transform:rotate(45deg)}
summary b{font-family:var(--f-mono);font-size:var(--t-sm)}
summary .m{color:var(--ink-3);font:var(--t-xs) var(--f-mono)}
details .body{padding:0 16px 14px}
details a{color:var(--accent-ink);font-size:var(--t-sm)}
.vd{font:600 11.5px/1.7 var(--f-sans);border-radius:999px;padding:0 9px;background:var(--surface-1);color:var(--ink-2)}
.vd.ok{background:var(--ok-soft);color:var(--ok)} .vd.fix{background:var(--accent-soft);color:var(--accent-ink)}
.toast{position:fixed;left:50%;bottom:24px;transform:translate(-50%,8px);background:var(--ink);color:var(--surface-0);padding:11px 18px;border-radius:var(--r-md);font-size:14px;opacity:0;transition:opacity .16s steps(2),transform .16s steps(2);pointer-events:none;max-width:calc(100vw - 32px);display:flex;gap:14px;align-items:center;z-index:20;box-shadow:var(--sh-2)}
.toast.on{opacity:1;transform:translate(-50%,0);pointer-events:auto}
.toast button{border:none;background:none;color:var(--accent);font-weight:700;padding:0}
:root[data-theme="dark"] .toast button{color:#b4321f}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]) .toast button{color:#b4321f} }
.none{max-width:520px;margin:14vh auto;text-align:center;color:var(--ink-2);font:500 22px/1.4 var(--f-display)}
@media (max-width:760px){
  .bar{gap:8px 10px;padding:10px 16px}
  .ttl{flex-basis:100%;order:-1;border-left:0;padding-left:0;margin-left:0}
  .mark{display:none}
  .state{margin-right:auto}
  .room{padding:16px;gap:20px}
  .screen{max-height:none}
  .viewer{border-radius:12px}
  .where{flex-basis:100%;order:9;padding:4px 4px 2px}
  .keys{display:none}
  .shots{height:48px}
  .shot .cap span{display:none}
}
@media (max-width:480px){
  .state,.wait{flex:1 1 40%;justify-content:center}
  .bar .btn{flex:1;justify-content:center}
  .ctrl{gap:2px}
  .ib{width:34px}
  .tm{font-size:15px;margin:0 4px}
  .note{padding-left:38px}
}
@media (prefers-reduced-motion: reduce){ .btn,.big,.shot img,.thumb img,.compose,.note,.mk,.ib,.tc{transition:none} .btn:hover,.mk:hover,.big:hover{transform:none} .wait.on::before,.pill.live::before,#newBanner div::before{animation:none} }
</style>
<script>try{const m=/[?&]theme=(dark|light)/.exec(location.search);if(m)document.documentElement.dataset.theme=m[1]}catch(e){}</script>
</head>
<body>
<header>
  <div class="bar">
    <span class="mark"><i aria-hidden="true"></i><span data-t="brand"></span></span>
    <div class="ttl"><h1 id="ttl"></h1><div class="ver num" id="ver"></div></div>
    <span class="pill wait" id="wait" hidden></span>
    <span class="pill state" id="state"></span>
    <button class="btn ok" id="pass" data-t="pass" data-tt="passTip"></button>
    <button class="btn primary" id="send" data-t="send" data-tt="sendTip"></button>
  </div>
  <div class="banner" id="sentBanner"><div id="sentText"></div></div>
  <div class="banner" id="newBanner"><div data-t="newVer"></div></div>
</header>
<main id="main"></main>
<div class="toast" id="toast"><span id="toastText"></span><button id="toastAct" hidden></button></div>
<script>
const D = __DATA__, F = D.film, H = D.history || [], KEY = '__KEY__';
const I18N = {
 zh: {brand:'审片台', pass:'通过', passTip:'这一版可以了', send:'提交给 agent', sendTip:'把意见交给 agent 去改', newVer:'登记了新的一版，点这里刷新（意见都已保存）',
  shot:k=>`镜头${k}`, img:k=>`图${k}`, frame:f=>`第 ${f} 帧`, fps:n=>`${n} 帧/秒`, imgs:n=>`${n} 张图`,
  saveFail:'保存失败：本地服务停了？意见还在这一页上，别关', noFilm:'还没有登记成片。', copyNotes:'复制意见', copyTip:'复制全部意见，贴进对话',
  play:'播放', playPause:'播放 / 暂停', prevF:'上一帧（←）', prevFa:'上一帧', nextF:'下一帧（→）', nextFa:'下一帧', rate:'播放速度', mute:'静音', full:'全屏',
  keysV:'<kbd>空格</kbd> 播放 / 暂停　<kbd>←</kbd> <kbd>→</kbd> 一帧　<kbd>回车</kbd> 在这一刻写意见　在胶片上点、拖就是跳；点图钉跳到那条意见',
  keysI:'<kbd>←</kbd> <kbd>→</kbd> 换一张　<kbd>回车</kbd> 给这一张写意见　点意见跳到那一张　点大图在新窗口看原图',
  known:'已知问题 · 制作方自己看到的，还没改', notes:'意见', add:'加上', hist:'之前的版本',
  phV:'暂停在要说的那一刻，写下看到的问题。回车加上，Shift + 回车换行', phI:'给这一张写意见（颜色、样子、哪里不像）。回车加上，Shift + 回车换行',
  prevI:'上一张', nextI:'下一张', hintI:'意见会挂在这一张图上', hintV:'意见会挂在上面这个时间点',
  edit:'改', del:'删', done:'已改', reply:'回复', noTime:'没带时间', empty:'还没有意见。看到要改的地方就暂停，按回车写。', emptyI:'还没有意见。选一张图，按回车写。',
  vOk:'通过', vFix:'要改', nNotes:n=>`${n} 条意见`, nDone:n=>`已改 ${n}`, histEmpty:'这一版没有写意见', openOld:'单独打开这一版的片子',
  savedAt:w=>`已记在 ${w}`, deleted:'已删除这条意见', undo:'撤销', cancel:'取消', save:'保存',
  draft:n=>`${n} 条意见，还没提交`, none:'还没写意见', ok:'已通过', sentN:n=>`已提交 ${n} 条`,
  okBanner:'已通过，agent 收到了。', sentBanner:'已提交，agent 收到了，正在逐条改。改好会登记新的一版，这一页会提示你刷新。',
  okIdle:'已通过。agent 现在没在等这一页：回对话说一声「通过了」。', sentIdle:'已提交，意见都存好了。agent 现在没在等这一页：回对话说一声「看完了」，它会读到这些意见接着改。',
  waiting:m=>`agent 在等你 · 还剩 ${m} 分钟`, waitTip:m=>`agent 最多等 ${m} 分钟。过了时间也不要紧：意见照样保存，提交后回对话说一声就行`,
  idle:'agent 没在等', idleTip:'意见照样保存。写完点提交或通过，再回对话说一声，agent 就会读到',
  needNotes:'还没写意见。暂停在要改的地方按回车写；没问题就点「通过」', needNotesI:'还没写意见。选一张图按回车写；没问题就点「通过」', submitFail:'提交失败：本地服务停了。意见还在页面上，回对话说一声',
  mdVerdict:v=>`结论：${v === 'ok' ? '通过' : '要改'}`, mdNoTime:'（没带时间）', mdFrame:f=>` · 第 ${f} 帧`, mdShot:(k,n)=>` · 镜头${k}「${n}」`, copied:'已复制，贴进对话就行'},
 en: {brand:'Review', pass:'Approve', passTip:'This version is good', send:'Send to agent', sendTip:'Send your notes to the agent to fix', newVer:'A new version is in. Click to reload (your notes are saved)',
  shot:k=>`Shot ${k}`, img:k=>`Image ${k}`, frame:f=>`frame ${f}`, fps:n=>`${n} fps`, imgs:n=>`${n} images`,
  saveFail:'Could not save: is the local server down? Your notes are still on this page, keep it open', noFilm:'No film has been added yet.', copyNotes:'Copy notes', copyTip:'Copy all notes and paste them into the chat',
  play:'Play', playPause:'Play / pause', prevF:'Previous frame (←)', prevFa:'Previous frame', nextF:'Next frame (→)', nextFa:'Next frame', rate:'Playback speed', mute:'Mute', full:'Full screen',
  keysV:'<kbd>Space</kbd> play / pause　<kbd>←</kbd> <kbd>→</kbd> one frame　<kbd>Enter</kbd> write a note at this moment　Click or drag the film strip to jump; click a pin to go to that note',
  keysI:'<kbd>←</kbd> <kbd>→</kbd> next image　<kbd>Enter</kbd> write a note on this image　Click a note to go to its image　Click the big image to open the original',
  known:'Known issues · seen by the maker, not fixed yet', notes:'Notes', add:'Add', hist:'Earlier versions',
  phV:'Pause on the moment and write what you see. Enter adds it, Shift + Enter for a new line', phI:'What is off in this image (colour, look, likeness)? Enter adds it, Shift + Enter for a new line',
  prevI:'Previous image', nextI:'Next image', hintI:'The note is pinned to this image', hintV:'The note is pinned to the time above',
  edit:'Edit', del:'Delete', done:'Fixed', reply:'Reply', noTime:'No time', empty:'No notes yet. Pause where something needs fixing and press Enter.', emptyI:'No notes yet. Pick an image and press Enter to write one.',
  vOk:'Approved', vFix:'Needs fixes', nNotes:n=>`${n} note${n === 1 ? '' : 's'}`, nDone:n=>`${n} fixed`, histEmpty:'No notes on this version', openOld:'Open this version of the film',
  savedAt:w=>`Noted at ${w}`, deleted:'Note deleted', undo:'Undo', cancel:'Cancel', save:'Save',
  draft:n=>`${n} note${n === 1 ? '' : 's'}, not sent yet`, none:'No notes yet', ok:'Approved', sentN:n=>`${n} note${n === 1 ? '' : 's'} sent`,
  okBanner:'Approved. The agent has it.', sentBanner:'Sent. The agent has your notes and is fixing them one by one. When the next version is in, this page will ask you to reload.',
  okIdle:'Approved. The agent is not waiting on this page right now: tell it in the chat ("approved").', sentIdle:'Sent, and your notes are saved. The agent is not waiting on this page right now: tell it in the chat ("done reviewing") and it will read them and carry on.',
  waiting:m=>`Agent is waiting · ${m} min left`, waitTip:m=>`The agent waits up to ${m} minutes. If time runs out, nothing is lost: notes stay saved; after you send, tell it in the chat`,
  idle:'Agent not waiting', idleTip:'Notes are still saved. When you are done, click Send or Approve, then tell the agent in the chat and it will read them',
  needNotes:'No notes yet. Pause where something needs fixing and press Enter; if it all looks right, click Approve', needNotesI:'No notes yet. Pick an image and press Enter to write one; if it all looks right, click Approve', submitFail:'Could not send: the local server is down. Your notes are still on the page; tell the agent in the chat',
  mdVerdict:v=>`Verdict: ${v === 'ok' ? 'approved' : 'needs fixes'}`, mdNoTime:'(no time)', mdFrame:f=>` · frame ${f}`, mdShot:(k,n)=>` · shot ${k} "${n}"`, copied:'Copied. Paste it into the chat'}
};
const T = I18N[String(D.lang || '').toLowerCase().startsWith('zh') ? 'zh' : 'en'];
document.querySelectorAll('[data-t]').forEach(el => el.textContent = T[el.dataset.t]);
document.querySelectorAll('[data-tt]').forEach(el => el.title = T[el.dataset.tt]);

const SERVER = location.protocol.startsWith('http');
const FPS = (F && F.fps) || 24, SH = (F && F.shots) || [];
let S = {items:{}}, R = {}, SUB = {}, W = null, ver = null, dur = (F && F.dur) || 0, hot = null;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const fmt = t => { if (t == null) return '—'; const m = Math.floor(t/60), s = t - m*60; return m + ':' + s.toFixed(2).padStart(5,'0'); };
const frameOf = t => Math.floor(t*FPS + 1e-3) + 1;
const shotsOf = f => (f && f.shots) || [];
function shotAt(t, shots = SH){ let k = -1; shots.forEach((s,i) => { if (t + 1e-3 >= s.t) k = i; }); return k; }
const shotName = (k, shots = SH) => k < 0 || !shots[k] ? '' : `${T.shot(k+1)} · ${shots[k].name || ''}`;
const nkey = n => { const t = n.t ?? n.img; return [t == null ? 1 : 0, t || 0, +String(n.nid).replace(/\D/g,'') || 0]; };
const IMGS = (F && F.kind === 'images' && F.images) || [];
let SEL = 0;
const imgName = (k, f = F) => { const im = ((f && f.images) || [])[k]; return T.img(k+1) + (im ? ` · ${im.name || ''}` : ''); };
const byTime = (a, b) => { const x = nkey(a), y = nkey(b); return x[0]-y[0] || x[1]-y[1] || x[2]-y[2]; };
const IC = {
  play:'<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/></svg>',
  pause:'<svg viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4.2" height="16" rx="1.2"/><rect x="13.8" y="4" width="4.2" height="16" rx="1.2"/></svg>',
  prev:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/><path d="M6 5v14"/></svg>',
  next:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/><path d="M18 5v14"/></svg>',
  chevL:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 6l-6 6 6 6"/></svg>',
  chevR:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 6l6 6-6 6"/></svg>',
  vol:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6"/><path d="M18.5 6.5a7.5 7.5 0 0 1 0 11"/></svg>',
  mute:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M16 9.5l5 5M21 9.5l-5 5"/></svg>',
  full:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>'
};

// ---------- storage ----------
function cur(){ const it = (S.items[F.id] ??= {notes:[], verdict:'', seq:0}); it.notes ??= []; it.seq ??= it.notes.length; return it; }
async function load(){
  if (SERVER) {
    try { S = await (await fetch('api/state', {cache:'no-store'})).json() || {}; } catch(e) { S = {}; }
    try { R = await (await fetch('api/replies', {cache:'no-store'})).json() || {}; } catch(e) { R = {}; }
    try { SUB = (await (await fetch('api/ver', {cache:'no-store'})).json()).submit || {}; } catch(e) { SUB = {}; }
  } else { try { S = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch(e) { S = {}; } }
  S.items ??= {};
}
let saveT = null, saving = null;
function save(){ clearTimeout(saveT); cur().saved_at = Date.now()/1000 + 1e6; drawState(); saveT = setTimeout(flush, 300); }
async function flush(){
  clearTimeout(saveT); const it = cur();
  if (!SERVER) { it.saved_at = Date.now()/1000; try { localStorage.setItem(KEY, JSON.stringify(S)); } catch(e){} drawState(); return; }
  saving = fetch('api/state', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id:F.id, notes:it.notes, seq:it.seq})})
    .then(r => r.json()).then(j => { it.saved_at = j.saved_at; drawState(); })
    .catch(() => toast(T.saveFail));
  return saving;
}

// ---------- page ----------
function render(){
  $('#ttl').textContent = F ? F.title : T.brand;
  if (!F) { $('#main').innerHTML = `<div class="none">${T.noFilm}</div>`; $('#pass').hidden = $('#send').hidden = true; return; }
  if (F.kind === 'images') { renderImages(); return; }
  $('#ver').textContent = `${F.id}${F.at ? ' · ' + F.at : ''} · ${T.fps(FPS)}`;
  if (!SERVER) { $('#send').textContent = T.copyNotes; $('#send').title = T.copyTip; }
  const known = (F.known || []).filter(k => k.trim());
  $('#main').innerHTML = `
    <div class="room"><section class="stage"><div class="stage-in">
        <div class="viewer"><div class="screen" id="screen"><video id="v" preload="auto" playsinline>${F.web ? `<source src="${esc(F.web)}" type="video/webm">` : ''}<source src="${esc(F.src)}"></video>
          <button class="big" id="big" aria-label="${T.play}">${IC.play}</button></div>
        <div class="ctrl">
          <button class="ib main" id="pp" aria-label="${T.playPause}">${IC.play}</button>
          <button class="ib" id="fb" title="${T.prevF}" aria-label="${T.prevFa}">${IC.prev}</button>
          <button class="ib" id="ff" title="${T.nextF}" aria-label="${T.nextFa}">${IC.next}</button>
          <span class="tm num"><span id="tnow">0:00.00</span> <span class="d">/ <span id="tdur">${fmt(dur)}</span></span></span>
          <span class="where num" id="where"></span>
          <button class="rate num" id="rate" title="${T.rate}">1×</button>
          <button class="ib" id="mute" aria-label="${T.mute}">${IC.vol}</button>
          <button class="ib" id="fs" aria-label="${T.full}">${IC.full}</button>
        </div></div>
        <div class="reel" id="scrub"><div id="marks"></div>
          <div class="film"><div class="shots${SH.length ? '' : ' blank'}" id="shots">${SH.map((s,i) => {
            const end = s.t1 ?? (SH[i+1] ? SH[i+1].t : dur), th = (F.thumbs || [])[i];
            return `<button class="shot" data-shot="${i}" style="flex-grow:${Math.max(0.05, end - s.t)}" title="${esc(`${T.shot(i+1)} ${s.size||''} ${s.name||''} · ${fmt(s.t)}`)}">
              ${th ? `<img src="${esc(th)}" alt="" loading="lazy" draggable="false">` : ''}<span class="cap"><b>${i+1}</b><span>${esc(s.name || '')}${s.size ? ' · ' + esc(s.size) : ''}</span></span><span class="pg"></span><span class="cnt" hidden></span></button>`; }).join('')}</div>
            <div id="ticks"></div></div>
          <div class="fi" id="fill"></div><div class="knob" id="knob"></div></div>
        <div class="keys">${T.keysV}</div>
    </div></section>
    <aside class="desk"><div class="desk-in">
      <section class="sheet">
        <div class="lh"><h2>${T.notes}</h2><span class="num" id="cnt"></span></div>
        ${known.length ? `<div class="known"><b>${T.known}</b><ul>${known.map(k => `<li>${esc(k)}</li>`).join('')}</ul></div>` : ''}
        <div class="compose">
          <div class="at"><button class="tc num" id="atT">0:00.00</button><span id="atS"></span></div>
          <textarea id="txt" placeholder="${T.phV}"></textarea>
          <div class="crow"><span class="h" id="ch"></span><button class="btn primary sm" id="addB">${T.add}</button></div>
        </div>
        <ol class="list" id="list"></ol>
      </section>
      ${H.length ? `<section class="hist"><h2>${T.hist}</h2><div id="hist"></div></section>` : ''}
    </div></aside></div>`;
  $('#ticks').innerHTML = dur ? SH.slice(1).map(s => `<span class="tick" style="left:${s.t/dur*100}%"></span>`).join('') : '';
  bindPlayer(); drawNotes(); drawHist(); drawState(); tick(true);
}
function renderImages(){
  $('#ver').textContent = `${F.id}${F.at ? ' · ' + F.at : ''} · ${T.imgs(IMGS.length)}`;
  if (!SERVER) { $('#send').textContent = T.copyNotes; $('#send').title = T.copyTip; }
  const known = (F.known || []).filter(k => k.trim());
  $('#main').innerHTML = `
    <div class="room"><section class="stage"><div class="stage-in">
        <div class="view" id="view"><img id="big" alt="">
          ${IMGS.length > 1 ? `<button class="nav l" data-step="-1" aria-label="${T.prevI}">${IC.chevL}</button><button class="nav r" data-step="1" aria-label="${T.nextI}">${IC.chevR}</button>` : ''}</div>
        <div class="vcap"><b id="vname"></b><span class="d num" id="vpos"></span></div>
        <div class="film thumbs" id="thumbs">${IMGS.map((im, i) => `<button class="thumb" data-img="${i}" title="${esc(imgName(i))}">
          <img src="${esc(im.src)}" alt="" loading="lazy"><span class="cap"><b>${i+1}</b>${esc(im.name || '')}</span><span class="cnt" hidden></span></button>`).join('')}</div>
        <div class="keys">${T.keysI}</div>
    </div></section>
    <aside class="desk"><div class="desk-in">
      <section class="sheet">
        <div class="lh"><h2>${T.notes}</h2><span class="num" id="cnt"></span></div>
        ${known.length ? `<div class="known"><b>${T.known}</b><ul>${known.map(k => `<li>${esc(k)}</li>`).join('')}</ul></div>` : ''}
        <div class="compose">
          <div class="at"><span class="tc" id="atT">${T.img(1)}</span><span id="atS"></span></div>
          <textarea id="txt" placeholder="${T.phI}"></textarea>
          <div class="crow"><span class="h" id="ch"></span><button class="btn primary sm" id="addB">${T.add}</button></div>
        </div>
        <ol class="list" id="list"></ol>
      </section>
      ${H.length ? `<section class="hist"><h2>${T.hist}</h2><div id="hist"></div></section>` : ''}
    </div></aside></div>`;
  $('#big').onclick = () => IMGS[SEL] && window.open(IMGS[SEL].src, '_blank', 'noopener');
  const ta = $('#txt');
  ta.addEventListener('focus', () => $('#ch').textContent = T.hintI);
  ta.addEventListener('blur', () => $('#ch').textContent = '');
  ta.addEventListener('input', () => grow(ta));
  ta.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && e.keyCode !== 229) { e.preventDefault(); addNote(); }
    if (e.key === 'Escape') ta.blur();
  });
  $('#addB').onclick = addNote;
  pick(0); drawNotes(); drawHist(); drawState();
}
function pick(k){
  if (!IMGS.length) return;
  SEL = (k + IMGS.length) % IMGS.length; const im = IMGS[SEL];
  $('#big').src = im.src; $('#vname').textContent = imgName(SEL); $('#vpos').textContent = `${SEL+1} / ${IMGS.length}`;
  $('#atT').textContent = T.img(SEL+1); $('#atS').textContent = im.name || '';
  document.querySelectorAll('.thumb').forEach((b, i) => b.classList.toggle('on', i === SEL));
  document.querySelector(`.thumb[data-img="${SEL}"]`)?.scrollIntoView({block:'nearest', inline:'nearest'});
  document.querySelectorAll('#list .note').forEach(li => li.classList.toggle('hot', li.dataset.img === String(SEL)));
}
const V = () => $('#v');
function tick(force){
  const v = V(); if (!v) return;
  const t = v.currentTime, d = dur || v.duration || 0;
  if (!force && t === tick.last) return; tick.last = t;
  const k = shotAt(t);
  $('#tnow').textContent = fmt(t);
  $('#where').innerHTML = T.frame(frameOf(t)) + (k >= 0 ? ` · <b>${esc(shotName(k))}</b>` : '');
  $('#atT').textContent = fmt(t); $('#atS').textContent = k >= 0 ? shotName(k) : T.frame(frameOf(t));
  const pc = d ? Math.min(100, t/d*100) : 0;
  $('#fill').style.width = pc + '%'; $('#knob').style.left = pc + '%';
  document.querySelectorAll('.shot').forEach((b, i) => {
    const on = i === k; b.classList.toggle('on', on);
    const s = SH[i], end = s.t1 ?? (SH[i+1] ? SH[i+1].t : d);
    b.querySelector('.pg').style.width = on && end > s.t ? Math.min(100, (t - s.t)/(end - s.t)*100) + '%' : '0';
  });
  if (on.k !== k && k >= 0) { on.k = k; const c = $('#shots'), b = document.querySelector(`.shot[data-shot="${k}"]`);
    if (c && b && c.scrollWidth > c.clientWidth && (b.offsetLeft < c.scrollLeft || b.offsetLeft + b.offsetWidth > c.scrollLeft + c.clientWidth)) c.scrollLeft = b.offsetLeft - 8; }
  const near = cur().notes.find(n => n.t != null && Math.abs(n.t - t) < 0.6/FPS + 0.04);
  setHot(near ? near.nid : null);
}
const on = {k:-1};
function setHot(nid){
  if (hot === nid) return; hot = nid;
  document.querySelectorAll('#list .note').forEach(li => li.classList.toggle('hot', li.dataset.nid === nid));
}
function loop(){ tick(false); requestAnimationFrame(loop); }
function seek(t, keep){
  const v = V(), d = dur || v.duration || 0;
  v.currentTime = Math.max(0, Math.min(t, d ? d - 0.5/FPS : t));
  if (!keep) v.pause();
}
function step(dir){ const v = V(); v.pause(); const f = frameOf(v.currentTime) - 1 + dir; seek((f + 0.5)/FPS); }
function togglePlay(){ const v = V(); if (v.paused) { if (v.ended || v.currentTime >= (dur || v.duration) - 0.02) v.currentTime = 0; v.play(); } else v.pause(); }
function bindPlayer(){
  const v = V(), sc = $('#screen');
  const sync = () => { const p = !v.paused; sc.classList.toggle('playing', p); $('#pp').innerHTML = p ? IC.pause : IC.play; };
  v.addEventListener('play', sync); v.addEventListener('pause', sync); v.addEventListener('ended', sync);
  v.addEventListener('loadedmetadata', () => {
    if (!dur) { dur = v.duration; $('#tdur').textContent = fmt(dur); render(); return; }
    if (v.videoWidth) sc.style.aspectRatio = v.videoWidth + '/' + v.videoHeight;
  });
  v.addEventListener('click', togglePlay); $('#big').onclick = togglePlay; $('#pp').onclick = togglePlay;
  $('#fb').onclick = () => step(-1); $('#ff').onclick = () => step(1);
  const rates = [1, 0.5, 0.25];
  $('#rate').onclick = e => { const i = (rates.indexOf(v.playbackRate) + 1) % rates.length; v.playbackRate = rates[i]; e.currentTarget.textContent = rates[i] + '×'; };
  $('#mute').onclick = e => { v.muted = !v.muted; e.currentTarget.innerHTML = v.muted ? IC.mute : IC.vol; };
  $('#fs').onclick = () => document.fullscreenElement ? document.exitFullscreen() : (sc.requestFullscreen || sc.webkitRequestFullscreen || (()=>{})).call(sc);
  const sb = $('#scrub');
  const at = e => { const r = sb.getBoundingClientRect(); return Math.max(0, Math.min(1, (e.clientX - r.left)/r.width)) * (dur || v.duration || 0); };
  sb.addEventListener('pointerdown', e => { if (e.target.closest('.mk')) return; sb.setPointerCapture(e.pointerId); sb.drag = true; seek(at(e)); });
  sb.addEventListener('pointermove', e => { if (sb.drag) seek(at(e)); });
  sb.addEventListener('pointerup', () => sb.drag = false); sb.addEventListener('pointercancel', () => sb.drag = false);
  document.querySelectorAll('.shot').forEach(b => b.onclick = e => { if (e.detail === 0) seek(SH[+b.dataset.shot].t + 0.5/FPS, !v.paused); });
  $('#atT').onclick = () => $('#txt').focus();
  const ta = $('#txt');
  ta.addEventListener('focus', () => { v.pause(); $('#ch').textContent = T.hintV; });
  ta.addEventListener('blur', () => $('#ch').textContent = '');
  ta.addEventListener('input', () => grow(ta));
  ta.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && e.keyCode !== 229) { e.preventDefault(); addNote(); }
    if (e.key === 'Escape') ta.blur();
  });
  $('#addB').onclick = addNote;
  if (!loop.on) { loop.on = true; requestAnimationFrame(loop); }
}
function grow(ta){ ta.style.height = 'auto'; ta.style.height = Math.min(240, ta.scrollHeight + 2) + 'px'; ta.style.overflowY = ta.scrollHeight > 240 ? 'auto' : 'hidden'; }

// ---------- notes ----------
function noteHTML(f, n, rep, editable){
  const shots = shotsOf(f), k = n.t == null ? -1 : shotAt(n.t, shots), r = rep[`${f.id}/${n.nid}`];
  if (n.img != null) return `<li class="note" data-nid="${esc(n.nid)}" data-img="${n.img}">
    <div class="nh"><button class="tc num" ${editable ? `data-img="${n.img}"` : 'disabled'}>${T.img(n.img+1)}</button>
      <span class="sh">${esc(((f.images || [])[n.img] || {}).name || '')}</span><span class="sp"></span>
      ${editable ? `<button class="nb" data-edit="${esc(n.nid)}">${T.edit}</button><button class="nb del" data-del="${esc(n.nid)}">${T.del}</button>` : ''}</div>
    <div class="nt">${esc(n.text)}</div>
    ${r ? `<div class="rep ${r.done ? 'done' : ''}"><span class="bd">${r.done ? T.done : T.reply}</span>${esc(r.text)}</div>` : ''}</li>`;
  return `<li class="note" data-nid="${esc(n.nid)}">
    <div class="nh">${n.t != null ? `<button class="tc num" ${editable ? `data-seek="${n.t}"` : 'disabled'}>${fmt(n.t)}</button>` : `<span class="tc">${T.noTime}</span>`}
      <span class="sh">${esc(k >= 0 ? shotName(k, shots) : (n.t != null ? T.frame(Math.floor(n.t*((f.fps)||24)+1e-3)+1) : ''))}</span><span class="sp"></span>
      ${editable ? `<button class="nb" data-edit="${esc(n.nid)}">${T.edit}</button><button class="nb del" data-del="${esc(n.nid)}">${T.del}</button>` : ''}</div>
    <div class="nt">${esc(n.text)}</div>
    ${r ? `<div class="rep ${r.done ? 'done' : ''}"><span class="bd">${r.done ? T.done : T.reply}</span>${esc(r.text)}</div>` : ''}</li>`;
}
function drawNotes(){
  const ns = [...cur().notes].sort(byTime), ul = $('#list');
  $('#cnt').textContent = ns.length || '';
  ul.innerHTML = ns.length ? ns.map(n => noteHTML(F, n, R, true)).join('')
    : `<li class="empty">${IMGS.length ? T.emptyI : T.empty}</li>`;
  if (F.kind === 'images') {
    document.querySelectorAll('.thumb').forEach((b, i) => { const c = ns.filter(n => n.img === i).length, el = b.querySelector('.cnt'); el.hidden = !c; el.textContent = c; });
    hot = undefined; pick(SEL); return;
  }
  const d = dur || 0;
  $('#marks').innerHTML = d ? ns.filter(n => n.t != null).map(n => `<button class="mk ${R[`${F.id}/${n.nid}`]?.done ? 'done' : ''}" style="left:${n.t/d*100}%" data-seek="${n.t}" data-nid="${esc(n.nid)}" data-n="${ns.indexOf(n) + 1}" title="${esc(fmt(n.t) + '  ' + n.text)}"><span>${ns.indexOf(n) + 1}</span></button>`).join('') : '';
  document.querySelectorAll('.shot').forEach((b, i) => { const c = ns.filter(n => n.t != null && shotAt(n.t) === i).length, el = b.querySelector('.cnt'); el.hidden = !c; el.textContent = c; });
  hot = undefined; tick(true);
}
function drawHist(){
  const box = $('#hist'); if (!box) return;
  box.innerHTML = H.map(h => {
    const it = S.items[h.id] || {}, ns = [...(it.notes || [])].filter(n => (n.text||'').trim()).sort(byTime);
    const vd = it.verdict === 'ok' ? `<span class="vd ok">${T.vOk}</span>` : it.verdict === 'fix' ? `<span class="vd fix">${T.vFix}</span>` : '';
    const done = ns.filter(n => R[`${h.id}/${n.nid}`]?.done).length;
    return `<details><summary><b>${esc(h.id)}</b><span>${esc(h.title || '')}</span>${vd}<span class="m num">${esc(h.at || '')} · ${T.nNotes(ns.length)}${ns.length ? ` · ${T.nDone(done)}` : ''}</span></summary>
      <div class="body"><ol class="list" style="padding:0">${ns.length ? ns.map(n => noteHTML(h, n, R, false)).join('') : `<li class="empty">${T.histEmpty}</li>`}</ol>
      ${h.src && h.kind !== 'images' ? `<a href="${esc(h.src)}" target="_blank" rel="noopener">${T.openOld}</a>` : ''}</div></details>`;
  }).join('');
}
function addNote(){
  const ta = $('#txt'), text = ta.value.trim();
  if (!text) { ta.focus(); return; }
  if (F.kind === 'images') {
    const it = cur(), n = {nid: 'n' + (++it.seq), t: null, img: SEL, text};
    it.notes.push(n); ta.value = ''; grow(ta); save(); drawNotes(); toast(T.savedAt(imgName(SEL))); return;
  }
  const v = V(), it = cur(), n = {nid: 'n' + (++it.seq), t: Math.round(v.currentTime*1000)/1000, text};
  it.notes.push(n); ta.value = ''; grow(ta); save(); drawNotes();
  toast(T.savedAt(`${fmt(n.t)}${shotAt(n.t) >= 0 ? ' · ' + shotName(shotAt(n.t)) : ''}`));
}
let undo = null;
function delNote(nid){
  const it = cur(), i = it.notes.findIndex(n => n.nid === nid); if (i < 0) return;
  undo = it.notes.splice(i, 1)[0]; save(); drawNotes();
  toast(T.deleted, T.undo, () => { if (undo) { cur().notes.push(undo); undo = null; save(); drawNotes(); } });
}
function editNote(nid){
  const li = document.querySelector(`#list .note[data-nid="${CSS.escape(nid)}"]`), n = cur().notes.find(x => x.nid === nid);
  if (!li || !n || li.querySelector('.edit')) return;
  const nt = li.querySelector('.nt'); nt.hidden = true;
  const box = document.createElement('div'); box.className = 'edit';
  box.innerHTML = `<textarea>${esc(n.text)}</textarea><div class="crow"><button class="btn sm" data-x>${T.cancel}</button><button class="btn primary sm" data-ok>${T.save}</button></div>`;
  nt.after(box); const ta = box.querySelector('textarea'); grow(ta); ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length);
  const done = ok => { if (ok) { const t = ta.value.trim(); if (!t) { delNote(nid); return; } n.text = t; save(); } drawNotes(); };
  box.querySelector('[data-ok]').onclick = () => done(true); box.querySelector('[data-x]').onclick = () => done(false);
  ta.addEventListener('input', () => grow(ta));
  ta.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing && e.keyCode !== 229) { e.preventDefault(); done(true); } if (e.key === 'Escape') done(false); });
}

// ---------- state / submit ----------
function sent(){ const it = cur(); return SUB.at && (SUB.id || F.id) === F.id && SUB.at >= (it.saved_at || 0); }
function drawState(){
  if (!F) return;
  const it = cur(), n = it.notes.length, el = $('#state'), sb = $('#sentBanner');
  let cls = '', txt = n ? T.draft(n) : T.none;
  if (SERVER && sent()) { const ok = it.verdict === 'ok'; cls = ok ? 'ok' : 'sent'; txt = ok ? T.ok : T.sentN(n); }
  else if (n) cls = 'draft';
  el.className = 'pill state ' + cls; el.textContent = txt;
  const show = SERVER && sent();
  sb.classList.toggle('on', !!show); sb.classList.toggle('ok', show && it.verdict === 'ok');
  if (show) $('#sentText').textContent = it.verdict === 'ok' ? (SUB.waited === false ? T.okIdle : T.okBanner) : (SUB.waited === false ? T.sentIdle : T.sentBanner);
  const w = $('#wait'); w.hidden = !SERVER || (show && !W) || !ver;
  if (W) { const left = Math.max(1, Math.ceil((W.until - Date.now()/1000) / 60)), all = Math.round((W.until - W.since) / 60);
    w.className = 'pill wait on'; w.textContent = T.waiting(left); w.title = T.waitTip(all); }
  else { w.className = 'pill wait'; w.textContent = T.idle; w.title = T.idleTip; }
}
async function submit(verdict){
  const it = cur();
  if (verdict !== 'ok' && !it.notes.length) { toast(IMGS.length ? T.needNotesI : T.needNotes); return; }
  if (!SERVER) { it.verdict = verdict; await flush(); copy(verdict); return; }
  try {
    await flush(); if (saving) await saving;
    const j = await (await fetch('api/submit', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({id:F.id, verdict})})).json();
    SUB = j; it.verdict = verdict; drawState();
    window.scrollTo({top:0, behavior:'smooth'});
  } catch(e) { toast(T.submitFail); }
}
function toMarkdown(verdict){
  const ns = [...cur().notes].sort(byTime);
  let md = `# ${F.title} (${F.id})\n${T.mdVerdict(verdict)}\n`;
  ns.forEach(n => { if (n.img != null) { md += `\n${n.nid} · ${imgName(n.img).replace(' · ', '「')}」\n  ${n.text}\n`; return; }
    const k = n.t == null ? -1 : shotAt(n.t);
    md += `\n${n.nid} · ${n.t == null ? T.mdNoTime : fmt(n.t) + T.mdFrame(frameOf(n.t)) + (k >= 0 ? T.mdShot(k+1, SH[k].name) : '')}\n  ${n.text}\n`; });
  return md;
}
async function copy(verdict){
  const md = toMarkdown(verdict);
  try { await navigator.clipboard.writeText(md); }
  catch(e) { const ta = document.createElement('textarea'); ta.value = md; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); }
  toast(T.copied);
}
function toast(msg, act, fn){
  const t = $('#toast'), b = $('#toastAct'); $('#toastText').textContent = msg;
  b.hidden = !act; b.textContent = act || ''; b.onclick = () => { fn && fn(); t.classList.remove('on'); };
  t.classList.add('on'); clearTimeout(toast.h); toast.h = setTimeout(() => t.classList.remove('on'), act ? 5000 : 2400);
}

// ---------- events ----------
document.addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  const d = b.dataset;
  if (d.seek != null && !b.disabled) { seek(+d.seek + 0.0005); if (d.nid) setTimeout(() => document.querySelector(`#list .note[data-nid="${CSS.escape(d.nid)}"]`)?.scrollIntoView({block:'nearest', behavior:'smooth'}), 30); }
  if (d.img != null && !b.disabled && F && F.kind === 'images') pick(+d.img);
  if (d.step) pick(SEL + (+d.step));
  if (d.edit) editNote(d.edit);
  if (d.del) delNote(d.del);
});
document.addEventListener('keydown', e => {
  if (F && F.kind === 'images') {
    const t = e.target;
    if (['INPUT','TEXTAREA','SELECT'].includes(t.tagName) || t.isContentEditable || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'ArrowLeft') { e.preventDefault(); pick(SEL - 1); }
    else if (e.key === 'ArrowRight') { e.preventDefault(); pick(SEL + 1); }
    else if (e.key === 'Enter' && !['A','SUMMARY','BUTTON'].includes(t.tagName)) { e.preventDefault(); $('#txt').focus(); }
    return;
  }
  if (!F || !V()) return;
  const t = e.target;
  if (['INPUT','TEXTAREA','SELECT'].includes(t.tagName) || t.isContentEditable) return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === ' ' || e.code === 'Space') { e.preventDefault(); togglePlay(); }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
  else if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
  else if (e.key === 'Enter' && !['A','SUMMARY','BUTTON'].includes(t.tagName)) {
    e.preventDefault(); V().pause(); $('#txt').focus();
  }
});
document.addEventListener('mousedown', e => { if (e.target.closest('button')) e.preventDefault(); });   // 点按钮不抢焦点，空格 / 回车照样管播放和写意见
$('#pass').onclick = () => submit('ok');
$('#send').onclick = () => submit('fix');
$('#newBanner').onclick = () => location.reload();
async function poll(){
  try { const v = await (await fetch('api/ver', {cache:'no-store'})).json();
    if (ver && v.data !== ver.data) $('#newBanner').classList.add('on');
    if (ver && v.replies !== ver.replies) { R = await (await fetch('api/replies', {cache:'no-store'})).json(); drawNotes(); drawHist(); }
    SUB = v.submit || SUB; W = v.wait || null; ver = v; drawState(); } catch(e) {}
}
load().then(() => { render(); if (SERVER) { poll(); setInterval(poll, 3000); } });
</script>
</body>
</html>
'''


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('add', help='register a film version, or a few images (characters)')
    a.add_argument('video', nargs='+', help='a film (.mp4 etc.; the matching .shots.json comes along) or several images (.png / .jpg), optionally label=path')
    a.add_argument('--id', required=True, help='id of this version, e.g. film-v1; a new id replaces the old version')
    a.add_argument('--title', default='', help='title on the review page (default: the video file name); unrelated to the title card')
    a.add_argument('--known', action='append', default=[], help='an issue you saw and have not fixed; repeatable')
    a.add_argument('--lang', help='the language you talk to the user in (zh, en, ja, …): Chinese codes get the Chinese page, every other language the English one; omitted = last one')
    a.add_argument('--root', default='.')
    for name in ('build', 'notes', 'open'):
        x = sub.add_parser(name); x.add_argument('--root', default='.')
        if name == 'open':
            x.add_argument('--port', type=int)
            x.add_argument('--no-browser', action='store_true', help='do not open a system browser (use when you have your own browser panel)')
    w = sub.add_parser('wait'); w.add_argument('--root', default='.'); w.add_argument('--timeout', type=float, default=1800)
    r = sub.add_parser('reply'); r.add_argument('id'); r.add_argument('nid'); r.add_argument('text')
    r.add_argument('--done', action='store_true', help='mark as Fixed'); r.add_argument('--root', default='.')
    s = sub.add_parser('serve'); s.add_argument('--root', default='.'); s.add_argument('--port', type=int)
    g = ap.parse_args()
    if g.cmd == 'add':
        isimg = [os.path.splitext(v.split('=', 1)[-1] if '=' in v else v)[1].lower() in IMAGE for v in g.video]
        if all(isimg): add_images(g.video, g.id, g.title, g.root, g.known, g.lang)
        elif len(g.video) == 1: add(g.video[0], g.id, g.title, g.root, g.known, g.lang)
        else: sys.exit('review: register one film, or several images, not both')
    elif g.cmd == 'build': build(g.root)
    elif g.cmd == 'notes': notes(g.root)
    elif g.cmd == 'open': open_page(g.root, g.port, browser=not g.no_browser)
    elif g.cmd == 'wait': sys.exit(wait(g.root, g.timeout))
    elif g.cmd == 'reply': reply(g.id, g.nid, g.text, g.done, g.root)
    else: serve(g.root, g.port)
