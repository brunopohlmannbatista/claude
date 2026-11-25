#!/usr/bin/env python3
"""Download the real instrument samples for the score (~1.4 GB, CC0 / CC-BY) to $LEMO_ANIMI_INSTRUMENTS or $LEMO_ANIMI_HOME/instruments.

    python fetch_instruments.py           download missing libraries (existing ones skipped; re-run resumes after an interruption)
    python fetch_instruments.py --check   check only; list what is missing, exit code 1
"""
import hashlib, json, os, shutil, subprocess, sys, tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = json.load(open(os.path.join(HERE, 'instruments.json')))
HOME = os.environ.get('LEMO_ANIMI_HOME', os.path.expanduser('~/lemo-animi-env'))
DST = os.environ.get('LEMO_ANIMI_INSTRUMENTS', os.path.join(HOME, 'instruments'))
PREFIX = 'core/audio/instruments/'


def have(lib):
    d = os.path.join(DST, lib)
    return os.path.isdir(d) and any(os.scandir(d)) and os.path.exists(os.path.join(DST, 'index.json'))


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()


def extract(tar):
    root = os.path.realpath(DST)
    with tarfile.open(tar) as t:
        for m in t.getmembers():
            name = m.name[2:] if m.name.startswith('./') else m.name
            if not name.startswith(PREFIX) or m.issym() or m.islnk() or m.isdev(): continue
            rel = name[len(PREFIX):]
            if not rel: continue
            dest = os.path.realpath(os.path.join(root, rel))
            if not dest.startswith(root + os.sep): sys.exit(f'✗ unsafe path {m.name} in the archive; not extracted')
            if m.isdir(): os.makedirs(dest, exist_ok=True); continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with t.extractfile(m) as src, open(dest, 'wb') as out: shutil.copyfileobj(src, out)


def main():
    check = '--check' in sys.argv
    miss = [l for l in MAN['packs'] if not have(l)]
    if check:
        if miss: print(f'instrument samples: missing {" ".join(miss)} ({DST}); run sh setup.sh instruments to download'); return 1
        print(f'instrument samples: {DST} (complete)'); return 0
    if not miss: print(f'instrument samples already complete: {DST}'); return 0
    if not shutil.which('curl'): sys.exit('✗ no curl, cannot download')
    os.makedirs(DST, exist_ok=True)
    for lib in miss:
        p = MAN['packs'][lib]; tmp = os.path.join(DST, p['file'] + '.download')
        need = int(p['size'] * 2.2) - (os.path.getsize(tmp) if os.path.exists(tmp) else 0)
        if shutil.disk_usage(DST).free < need: sys.exit(f'✗ not enough disk: {lib} needs about {need / 1e9:.1f} GB to download and extract')
        if not (os.path.exists(tmp) and os.path.getsize(tmp) == p['size']):
            print(f'↓ {lib}（{p["size"] / 1e6:.0f} MB）', flush=True)
            r = subprocess.run(['curl', '-L', '--fail', '--retry', '3', '--connect-timeout', '20', '-C', '-', '-#', '-o', tmp, MAN['url'] + p['file']])
            if r.returncode: sys.exit(f'✗ download interrupted (curl {r.returncode}); re-run to resume')
        if sha256(tmp) != p['sha256']: os.remove(tmp); sys.exit(f'✗ {lib} checksum mismatch; deleted, re-run to download again')
        extract(tmp); os.remove(tmp); print(f'✓ {lib}')
    print(f'instrument samples: {DST}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
