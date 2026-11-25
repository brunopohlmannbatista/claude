#!/usr/bin/env python3
"""Create a film folder: make the subfolders, copy the compositing template to tools/film.py (skill path, style, size and
short name filled in), and write the start of sound.json.

    "$PY" "$S/init_film.py" <film folder> --style <style id> --dur <story seconds> [--size landscape|portrait|square] [--name <short name>] [--lang zh|en]

Existing tools/film.py or sound.json are never overwritten (safe when resuming an old film). The short name defaults to
the folder name.
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import animi  # noqa: E402

OLD_SIZES = {'横屏': 'landscape', '竖屏': 'portrait', '方形': 'square'}   # Chinese aliases also accepted
SIZE_CHOICES = ['landscape', 'portrait', 'square'] + list(OLD_SIZES)


def main():
    ap = argparse.ArgumentParser(description='Create a lemo-animi film folder')
    ap.add_argument('dir')
    ap.add_argument('--style', required=True, help='fixed style id (animi.py styles lists them all)')
    ap.add_argument('--dur', type=float, default=40.0, help='story length in seconds: the film length, minus 6 with title and end cards (14–120)')
    ap.add_argument('--size', default='landscape', choices=SIZE_CHOICES)
    ap.add_argument('--name', help='short name: out/<name>.mp4; defaults to the folder name')
    ap.add_argument('--lang', default='en', help='film language for narration, subtitles and cards: zh or en (any other code falls back to en)')
    a = ap.parse_args()
    a.size = OLD_SIZES.get(a.size, a.size)

    if not os.path.isfile(os.path.join(animi.STYLES_DIR, a.style, 'style.json')):
        sys.exit(f'init_film: no style {a.style} (animi.py styles lists them all)')
    if not 14 <= a.dur <= 120:
        sys.exit('init_film: story length must be 14–120 seconds (films of 20 s to 2 min)')
    wk = os.path.abspath(a.dir)
    name = a.name or os.path.basename(wk)
    if not re.fullmatch(r'[\w.-]+', name):
        sys.exit(f'init_film: short name may only use letters, digits, - _ . : {name} (set it with --name)')
    for d in ('prompts', 'src', 'work', 'audio', 'tools', 'frames', 'out'):
        os.makedirs(os.path.join(wk, d), exist_ok=True)

    film = os.path.join(wk, 'tools', 'film.py')
    if os.path.exists(film):
        print(f'{film} exists, not overwritten')
    else:
        s = open(os.path.join(HERE, 'film_template.py'), encoding='utf-8').read()
        for pat, new in ((r"^SKILL_AT_INIT = .*$", f"SKILL_AT_INIT = {HERE!r}"),
                         (r"^STYLE_ID = '[^']*'", f"STYLE_ID = {a.style!r}"),
                         (r"^SIZE = '[^']*'", f"SIZE = {a.size!r}"),
                         (r"^NAME = '[^']*'", f"NAME = {name!r}")):
            s, n = re.subn(pat, lambda m: new, s, count=1, flags=re.M)
            if not n: sys.exit(f'init_film: template has no line matching "{pat}"')
        open(film, 'w', encoding='utf-8').write(s)
        print(f'wrote {film} (style {a.style}, {a.size}, short name {name})')

    snd = os.path.join(wk, 'sound.json')
    if os.path.exists(snd):
        print(f'{snd} exists, not overwritten')
    else:
        with open(snd, 'w', encoding='utf-8') as f:
            json.dump({'style': a.style, 'dur': a.dur, 'name': name, 'lang': 'zh' if a.lang.lower().startswith('zh') else 'en'}, f, ensure_ascii=False, indent=1)
        print(f'wrote {snd} (add score, foley and narration as references/sound.md describes)')


if __name__ == '__main__':
    main()
