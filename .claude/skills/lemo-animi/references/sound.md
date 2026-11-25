# Sound: one sound sheet produces all of it

`sound.json` lives in the film folder; `sound.py` turns it into narration, subtitles, score, foley and the mix. You don't write notes or set levels: instrumentation, foley material, narration voice and subtitle style all come from the style's `style.json`.

```json
{
 "style": "clay",
 "dur": 30.0,
 "name": "pancake",
 "lang": "en",
 "vo": [
  {"id": "L1", "t": 0.8,  "text": "A little clay penguin wants to make the perfect pancake."},
  {"id": "L2", "t": 5.2,  "text": "First try: the pancake hits the ceiling."},
  {"id": "L3", "t": 19.6, "text": "Third try... he closes his eyes."}
 ],
 "music": {
  "bpm": 112,
  "sections": [{"t": 0, "energy": 0.3}, {"t": 5.0, "energy": 0.6}, {"t": 12.0, "energy": 0.8},
               {"t": 19.4, "energy": 0.15}, {"t": 24.6, "energy": 0.95}, {"t": 28.0, "energy": 0.4, "end": true}],
  "hits": [{"t": 8.1, "kind": "accent"}, {"t": 24.6, "kind": "boom"}, {"t": 25.0, "kind": "sparkle"}],
  "silences": [[22.4, 24.5]]
 },
 "foley": [{"t": 2.0, "kind": "step"}, {"t": 7.6, "kind": "squish"}, {"t": 8.0, "kind": "pop", "pan": 0.2},
           {"t": 24.6, "kind": "thud", "v": 1.0}]
}
```

`name` is the short name; it sets `<name>.srt` and must equal `NAME` in `tools/film.py` (`out/<NAME>.mp4`).

## Order

1. Write only `style`, `dur`, `name` and each `vo` line's `text`; run `sound.py vo sound.json` to get each line's duration and pace.
2. Lay out the shot list by those durations (`references/directing.md` §3) and write each `t` back. Leave ≥ 0.15 s between lines (usually 0.3–1 s); the last line ends ≥ 0.4 s before the end.
3. Once the picture reaches board stage, write `music` and `foley` to the picture. Shots are fixed by then: write times relative to shots where possible (next section) so moving shots in revisions needs no re-timing.
4. `sound.py lint sound.json` → `sound.py build sound.json` → the full render burns subtitles and muxes sound automatically.

## Times: seconds or shot-relative

Times in `sections`, `hits`, `silences` and `foley` may be "shot + offset"; `sound.py` converts them via the shot list: `work/shots.json` (written by `film.py lint`) first, else `out/<name>.shots.json` (from the last full render).

| Form | Meaning |
|---|---|
| `3.2` | 3.2 s |
| `"flip"` | the cut into shot "flip" |
| `"flip+0.4"` | 0.4 s after the cut into "flip" |
| `"#5-0.3"` | 0.3 s before shot 5 cuts in (shot numbers from 0, same as `SHOTS[5]` and `shots_lint`) |
| `["flip", 0.4]`, `[5, -0.3]` | the same, list form |

- After moving shots: `film.py lint` (rewrites the shot list), then `sound.py build`; shot-relative sounds follow. Times in seconds don't move.
- Use shot numbers when names repeat. `lint` warns when an offset passes the next cut, the shot list is older than `film.py`, or the shot list duration doesn't match `dur`.
- `sound.py times sound.json` lists all converted times grouped by shot, with their original form; check it after moving shots. Without a shot list, shot-relative times can't convert and `lint` / `times` tell you to run `film.py lint` first.
- Narration stays in seconds: with narration the shot list is laid out from it (`film.py` reads narration seconds via `vo_times()`), so shot-relative narration would be circular.

## Narration (vo)

- **No narration by default**: write `vo` only when the user asks. No `vo` (or `[]`) = no-narration version: score and foley as usual, no subtitles, score not ducked.
- **Needs network**: `sound.py vo` uses Microsoft Edge online voices (edge-tts) and sends the narration text to Microsoft's speech service — that is the narration the user asked for. If it can't connect it **stops** and prints the reason to request network access. Request it with the reason "generate the narration the user asked for with edge-tts online voices; only the narration text is sent". If access is denied, drop `vo`, make the no-narration version, and say in the delivery report that network access was denied, the film has no narration, and adding `vo` and rerunning `sound.py vo` and `build` once allowed will add it. Don't substitute local offline voices (too robotic). `sound.py vo --dry-run` only lists the text that would be sent.
- One item per line: `id`, `t` (start, seconds), `text`. Pace and voice are uniform for the film, never per line.
- **Film language**: top-level `"lang"` in `sound.json`, `zh` (default) or `en`, matching the language you speak with the user.
  - `zh`: default voice `zh-CN-XiaoyiNeural` (lively female), normal pace; if the user picks a child voice, top-level `"voice": {"voice": "zh-CN-YunxiaNeural"}`. `sound.py voices` lists all Chinese voices; don't use the others. Subtitles split at punctuation into one block per screen (max 14 characters; short clauses merged).
  - `en`: narration in English; default voice `en-US-AvaNeural` (lively female), child voice `en-US-AnaNeural` (the style package's Chinese voice is not used). Subtitles split by words, ≤ 42 characters per screen; pace measured in words (≤ 3 words / s).
- Write numbers and foreign words as they should be spoken (zh: 「三次」, not 「3 次」).
- With narration, subtitles come from it automatically, timed to per-word pronunciation. Don't write subtitles separately.
- **Bilingual subtitles** (only when the user asks): in a `zh` film add `en` to each narration line, in an `en` film add `zh`; it becomes the second line. If the line fits one screen, write one string; if it splits into several screens, write a list with one entry per screen (`sound.py lint` shows how the primary language splits and FAILs on a mismatch). Rules: **one line per language, no wrapping, both on the same plate**, appearing and leaving together (the template does it; styles without a `plate` get a dark plate automatically). English lines ≤ 42 characters — shorten the translation rather than wrap; translate the meaning in short, spoken phrases.

## Score (music)

- `sections`: from `t`, `energy` 0–1 sets how many instruments play (the style's `music.energy` table). Put section boundaries on cuts; the score runs on one continuous bar grid, and instrumentation changes land on the bar line nearest the cut (at most half a bar off), so the music never breaks at a cut. `hits` and `silences` are what lock to picture. The last section has `"end": true` and resolves on the tonic there.
- Energy follows the story: low at the start, rising with attempts, dropping hard on failure, space before the turn, highest at the climax, easing at the landing.
- `hits`: accents on key moments (landing, impact, success). `kind` must exist in the style's `music.hits` (clay: `accent` glissando, `boom` bass drum + cymbal, `stop` wood block, `sparkle` glockenspiel arpeggio, `thud` timpani). 3–6 per 30 s.
- `silences`: no music at all, [start, end] in seconds. Leave 0.8–2 s before a turn or a gag, the same in every style; the first sound after a silence is one of the most important in the film. A longer score stop is allowed only when foley keeps sounding inside it, never more than 2 s with nothing audible.
- `bpm`, `key` optional: if omitted they're derived from the film name (a tempo within the style's bpm range, the style's key or a closely related one), and melody and progression also vary by name — **every film gets a new piece**. Don't write a fixed `seed`, and never copy `seed` and `music` from another film: same style + same seed = same melody. To get a different piece, put a new top-level `seed` (any integer) in sound.json and build again.
- Instrument velocity (`vel` in the style's instrumentation) is continuous across sample velocity layers: louder is brighter, no jump between layers.

When writing a style's instrumentation: the lowest energy tier must not contain only decaying instruments (marimba, ukulele, plucks) — every half bar there's a gap where nothing sounds and it feels broken. Put at least one sustaining instrument in the lowest tier (string pads, organ, `sustain` comping), or let the comping use `arp` (eighth-note arpeggio) to fill the gaps.

## Foley

- Each item: `t`, `kind`, optional `v` (volume 0–1), `pan` (-1 left … 1 right, following the character's screen position), `pitch` (1.0 normal, small character 1.3, large 0.7), `d` (duration for sustained sounds, seconds).
- `kind` is looked up as "style material_action" first (wood `thud` = wood landing), then generic actions, then aliases. `sound.py kinds <style>` lists every name the style can use with a description and aliases; ★ marks the style's recommended ones (`style.json` `foley.kinds`); a wrong name FAILs `lint`.
- Generic (any style):

| Group | Names (aliases) |
|---|---|
| Action | `step` footstep, `tap` light touch, `whoosh` swing (d), `sparkle` glint |
| Water | `drip` drop (drop), `bubble` bubbling (gurgle), `splash` falling into / splashing water (plop), `flow` running water (d, water / stream) |
| Snow, soft things | `crunch` crunching snow (snow), `puff` soft "pff": snow flop, yarn puffing up, `flop` doll falling / yarn ball hitting the floor (soft_thud), `rub` cloth / yarn rubbing (d, cloth / wool) |
| Small mechanisms | `click` joint click (joint), `button` button tick, `ratchet` knob ratcheting (knob), `creak` wood creak (d), `rip` tape tearing (d, tape) |
| Mud | `smear` long finger smear through clay (d, wipe) |

- Material versions: clay `thud squish pop boing clink step tap`; paper `rustle flap thud step whoosh`; wood `knock thud step click`; felt, cloth, yarn `thud step` (soft and muffled), felt and yarn also a duller `rub`; cardboard `thud step`; tin `clink wind thud step`.
- **Every landing, impact, toss, catch, switch on screen needs a sound**, timed to that drawing (`ts.pic_start(pic) / 24`, or shot-relative). Every walking step gets a `step`. Usually 15–40 per 30 s.

### Automatic foley from the timesheet (steps, joints — sounds tied to cells)

Footsteps, joint clicks and wing beats follow which cell is shown; computing seconds by hand is tedious and error-prone. Write rules in `sound.json`; `lint` / `build` read the timesheet from `build()` in `tools/film.py` and emit one sound each time a matching cell comes in:

```json
"foley_rules": [
 {"cell": "walk_[15]", "kind": "step", "v": 0.35, "pitch": 1.2, "x": "x"},
 {"cell": ["hop_3", "land_*"], "kind": "thud", "v": 0.7},
 {"cell": "turn_knob_2", "kind": "ratchet", "first": true, "offset": -0.03},
 {"cell": "friend_walk_[04]", "track": "m", "kind": "step", "pitch": 1.5}
]
```

- `cell`: cell name with wildcards (`*` anything, `[15]` 1 or 5), or a list. Every cell drawn in a timesheet entry counts (main cell, the parts of `"a+b"`, co-star cells in state like `ts.add(..., m='friend_walk_2')`); the sound fires on the drawing that switches into the cell, not again while it holds.
- Optional: `track` watches only one state key (only the co-star's steps); `beat` / `shot` limit to a beat / shot; `first` fires only once; `offset` shifts earlier or later (s); `gap` minimum seconds between hits (default 0.06); `x` = state key used as horizontal position to compute `pan`; `v` `pitch` `pan` `d` as above.
- Or write it in the timesheet: `ts.add('stand_4', sfx='thud')`, `sfx={'kind': 'thud', 'v': 0.8}`, `sfx=('tap', 0.3, 1.6)` fires on that drawing. With `sfx` but no rules, enable it with `"foley_auto": true` in `sound.json`.
- Automatic and hand-written `foley` mix together; `sound.py times` lists all (automatic ones show their rule and cell); `lint` warns about a rule that never matched.
- If `film.py` isn't at `tools/film.py`, set `"film": "path"` in `sound.json`. One-off big actions (a fall, slamming a door) are still written by hand in `foley`.

## Mix (automatic)

With narration: narration at a uniform level, score about 6 dB below it and ducked another 7 dB while narration plays; foley by `v`; overall loudness −14 LUFS. Stems in `audio/stem_music.wav`, `stem_foley.wav` (plus `stem_vo.wav` with narration) The user hears the finished mix on the review page; for a solo check, give the user the stem's path. You never load audio into your own input (SKILL.md hard rule 14).

After muxing, `sound.py check` runs on the film by itself (or run `sound.py check out/<name>.mp4`): it prints loudness and true peak and warns when loudness is outside −16…−12.5 LUFS, the true peak is above −1 dBTP, or there is dead air (below −45 dB) longer than 2 s away from the ends. Score `silences` follow the rule above; a longer score stop must have foley or narration inside it. Treat every warning as a review item: fix it or say why it stays.

## Silent

If the user explicitly asks for no sound: don't write `sound.json`; `film.py` renders a silent film and says so. Titles and other text are still set in code.
