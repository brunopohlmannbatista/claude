# Workflow: folders and commands per step

`$S` = the absolute path of the `scripts/` folder next to the `SKILL.md` you loaded (in a plugin install it sits inside the agent's plugin cache; it may contain spaces, so always quote it); `$PY` = the Python printed by `sh "$S/setup.sh" python` (default `~/lemo-animi-env/venv/bin/python`, or a system Python that already has every dependency; never a bare `python`). Run production commands inside the film folder.

## 0. Environment (once per machine)

Run setup in the current working directory, before choosing a film folder or asking for film details.

```sh
if ! sh "$S/setup.sh" check; then
    sh "$S/setup.sh" || exit 1        # wait for an existing install, then fill any gaps
    sh "$S/setup.sh" check || exit 1
fi
```

A first install needs network access and about 1.7 GB (Python environment ~300 MB, score instrument samples ~1.4 GB). Use `~/lemo-animi-env` or the user's configured location. Request sandbox access when needed. Codex and Claude Code share the environment. Setup reuses a complete virtual or system Python and skips downloaded libraries. Wait for completion even when the host runs the command in the background. Report a failed command and its diagnostic before asking any film questions. Re-running setup resumes missing downloads.

Encoding requires ffmpeg and ffprobe (macOS: `brew install ffmpeg`, Linux: use the package manager). Claude Code also needs zsh and either the user's image adapter or an installed, signed-in Codex CLI (`npm i -g @openai/codex`, then `codex login`). Check these Claude prerequisites even if `check` exits successfully. Once ready, set `PY=$(sh "$S/setup.sh" python)` and collect the missing choices together as described in SKILL.md §1. Create the film folder only after every item has an answer or the user has explicitly delegated it.

Narration uses edge-tts and needs the network: if `sound.py vo` can't connect it stops and prints a justification; request access. If refused, drop `vo` from `sound.json`, make the film without narration and say so in the report. Never substitute a local offline voice.

## 1. Film folder

```
<film>/
  production-log.md      director's plan, process, must-pass verdicts, self-assessment
  sound.json             sound sheet: narration, score plan, hits, foley (references/sound.md)
  prompts/               per image: slot file <name>.slots.txt and built prompt <name>.txt
  src/                   generated originals: char_*.png character sheets, sheet_*.png 8-cell sheets, close_*.png 2×2 close-up sheets,
                         prop_*.png props, fx_*.png fx sheets, bg_*.png backgrounds
  work/                  cells/ (sliced RGBA cells), anchors_*.json, QA images, board, stills
  audio/                 mix.wav, stems; with narration also vo/ (one file per line), subs.json
  tools/film.py          copied from film_template.py by init_film.py, settings filled in
  frames/                rendered frames (deletable after delivery)
  out/                   <name>.mp4, contact.jpg
  review.html, review/   the review page and every registered version; review.notes.json holds the user's notes
```

## 2. Director's plan (before any image)

Write it in `production-log.md` per `references/directing.md`: logline → beat sheet → narration script (if any) → shot list → layered action table → image list. Read the style's `STYLE.md` first: best subject, palette, light, camera, and which stories it suits or not.

## 3. Timing: narration or beats

**With narration** (sound first):

```sh
# sound.json: only style, dur, name, lang (init_film.py writes them) and the vo text (t empty); name is the short name, identical to NAME in tools/film.py
"$PY" "$S/sound.py" vo sound.json     # synthesises each line, prints length and speech rate (stops with a reason if offline)
```

Lay out the shot list by line length: roughly one shot per line, 0.3–1 s between lines for picture and sound. Then write each line's `t` back into `sound.json`.

**Without narration**: `sound.json` holds only `style`, `dur`, `name`, `lang`, no `vo`. Give each shot seconds from the beat sheet (a story beat is 2–4 s and holds several events; one quiet beat before the twist); the score's sections (`energy` in `sections`) and hits carry the rise and fall.

## 3′. Compositing script (before generating images)

```sh
"$PY" "$S/init_film.py" pancake --style clay --dur 40 --size landscape --name pancake --lang en   # --lang zh or en (film text); creates ./pancake; run everything after this inside it
```

It creates the subfolders, copies the template to `tools/film.py` with `SKILL`, `STYLE_ID`, `SIZE`, `NAME` filled in, and writes `style`, `dur`, `name` into `sound.json` (existing files are not overwritten). Then set `HERO_H` and write `SHOTS` + `build()` from the shot list (placeholder blocks for characters and backgrounds):

```sh
"$PY" tools/film.py lint            # timesheet, shots, same length as the sound sheet; writes work/shots.json (the template's 3 sample shots report as too long until replaced)
```

lint and board work without assets: storyboard first, swap in real assets later (§5).

## 4. Image generation and preprocessing

**Three steps per image**: slot file → build prompt → generate.

```sh
"$PY" "$S/animi.py" prompt clay character prompts/char_hero.slots.txt -o prompts/char_hero.txt
"$PY" "$S/animi.py" prompt clay sheet8 prompts/sheet_toss.slots.txt -o prompts/sheet_toss.txt
"$PY" "$S/animi.py" prompt clay bg prompts/bg_kitchen_wide.slots.txt -o prompts/bg_kitchen_wide.txt --size landscape
```

- **Codex**: generate with built-in image_gen: prompt = full text of `prompts/<name>.txt`; reference images as absolute paths in `referenced_image_paths` (action and close-up sheets: the character sheet); `transparent_background: true` for every transparent asset (character, action and close-up sheets, props, fx). Copy the file from the path the result names to `src/<name>.png`. Only if no path comes back: `sh "$S/grab_image.sh" --stamp work/.stamp` before generating and `sh "$S/grab_image.sh" src/<name>.png --since work/.stamp` after (one image at a time).
- **Claude or other agents**: `zsh "$S/gen.sh" prompts/<name>.txt src/<name>.png [reference images...]`. It uses the Codex CLI, or the user's own image adapter when they set one up (`~/lemo-animi-env/image.sh`, experimental; `sh "$S/setup.sh" image` tests it). Don't read, edit or create the adapter and don't switch between the two yourself. If gen.sh fails, show the user its message. If it warns that a transparent asset came back without alpha, cut it out (`cut.py`) before slicing.

**Order**: character sheets + 1–2 key backgrounds (check palette and character yourself) → remaining backgrounds → backgrounds into `load()`, storyboard with `film.py board` (characters still placeholders; check the shots connect) → action sheets → close-up sheets → props → fx sheets. Action sheets cost the most: write their 8 cells only once the storyboard works.

**Preprocessing** (every transparent sheet):

```sh
"$PY" "$S/animi.py" check src/sheet_toss.png --out work/check_toss.jpg           # QA: subject count, transparent edges, size, ground line
"$PY" "$S/animi.py" slice src/sheet_toss.png work/cells toss                     # RGBA cells toss_0..7
"$PY" "$S/animi.py" anchors work/cells --prefix toss --json work/anchors_toss.json --preview work/cells_toss.jpg
# 2×2 close-up sheet: --n 4 --rows 2 --cols 2; three props in a row: --n 3 --rows 1 --cols 3
# fx sheets and close-up sheets with several pieces per cell: --group grid on check and slice; AI-drawn symbols beside an action sheet: slice --fragments drop
# deliberate edge crops (close-up, a hand reaching into frame): check --allow-edge; translucent haze in the transparent area: check / slice --clean (or animi.py clean first)
```

Check FAIL: look at the QA image and the handling table in `references/quality.md`; if it's one of the cases above, rerun with the matching flag, no regeneration. Only real defects (missing cells, merged figures, wrong proportions) get one slot-file change (clearer pose, wider gaps) and a regeneration, at most 3 times; then split into two 4-cell sheets.

**Check every cell against the plan before slicing** (a passing `check` only means the cells cut cleanly): open the sheet full size and compare each cell with its line in `[action]`: pose, facing, which hand holds what, feet on the support it stands on, attached parts present once and at their mount, no extra parts or symbols. Any miss: regenerate with the miss named in the slot ("cell 3: the key is missing; it stays on the back"). A wrong drawing is never fixed in compositing.

## 5. Compositing: swap in real assets

`tools/film.py` exists since §3′. Edit the remaining two places: `load()` (per shot: background, cells and anchors, set layers, environment sprites) and `render()` (what each drawing shows: layers, side characters, environment, fx). See `references/compositing.md`. `draw()` and `post()` assemble transitions, grading and subtitles; normally leave them alone.

```sh
"$PY" tools/film.py lint            # timesheet, shots, missing images, transitions/set layers without assets, same length as sound sheet
"$PY" tools/film.py board           # storyboard: work/board.jpg + board.mp4 + hero size
"$PY" tools/film.py still 0 60 120  # full-resolution stills of key drawings
```

## 6. Sound

Once picture timing is fixed, write the score plan (sections, hits, silences) and foley into `sound.json` (`references/sound.md`):

```sh
"$PY" "$S/sound.py" lint sound.json
"$PY" "$S/sound.py" build sound.json  # audio/mix.wav; with narration also audio/subs.json, <name>.srt
```

## 7. Full film and review

```sh
"$PY" tools/film.py                 # render → burn subtitles (if narrated) → mux audio/mix.wav → out/<name>.mp4, all checks
sh "$S/contact.sh" out/<name>.mp4 out/contact.jpg
sh "$S/motion_check.sh" out/<name>.mp4 <start s> <length s> work/motion.jpg 12   # the 1–2 most intense seconds; 12 for on twos
"$PY" "$S/selfcheck.py" out/<name>.mp4 --style <style>   # work/selfcheck_frames.jpg (every 0.5 s), work/selfcheck_cuts.jpg (around each cut); look at every image
```

Review per `references/quality.md`: write a verdict for each must-pass item into the production log, fix failures, and do at least one round of fixes before delivery. In the cut sheet, compare before/after each cut for jump cuts, continuity, prop view, occlusion order, things hidden by subtitles.

`film.py lint` writes the shot list to `work/shots.json` (per-shot sound times resolve through it); the full render also writes `out/<name>.shots.json`, which the review page uses for its shot strip. Registered films are copied to `review/<entry id>/`, so re-renders never overwrite old versions.

**Title and end cards**: only if the user asked at intake; add them before registering the film. Use the user's title and credit; never invent a credit.

```sh
"$PY" "$S/bookends.py" preview --title "<title>" --style <style>          # check text and plate first: work/_titles.jpg
"$PY" "$S/bookends.py" out/<name>.mp4 --title "<title>" [--sub "<style name: name for a Chinese film, en for an English one>"] [--credit "<credit>"] --style <style> \
    [--hero work/cells/<jump cell>.png work/cells/<landed cell>.png]          # -> out/<name>-bookends.mp4 + .srt: this is the film
```

Each card is 3 s (`--sec`, 2.5–4; plan the story as the length minus both cards), same motion for every style: the plate enters per the style (drops in or stands up), stitches sew on, title letters drop one by one, the subtitle strip slides in, the hero jumps onto the card (`--hero`, using existing hero cells; omit it if the hero is already visible in the film's first frame, or there will be two heroes), then the card pulls away into the film. The end card drops the end word (`--end`) and fades in the credit. Look and entrance come entirely from the style's `style.json` `title`; never build a separate card in the film. Cards are always centred. After rendering, check `work/bookends_head.jpg`, `bookends_tail.jpg` (every 3rd drawing).

## Review page: preview (on request) and final film

`$R` below is shorthand for `"$PY" "$S/review.py"`: type that out in every command (each tool call starts a fresh shell, so set `S` and `PY` again in each one), run in the film folder. One local page, opened at most twice; register only two things: the character sheets and main backgrounds when the user wants a preview, and the final film. Nothing else is registered or paused on.

- **Where to open**: with a built-in browser panel (Codex app, right side) `open --no-browser` and open the printed URL in the panel; otherwise (Codex CLI, terminal) `open`, which uses the system browser. One place only. The page runs a local server on a port, which a sandbox usually blocks: in Codex run `open` with escalated permission from the start (justification: open the local review page). If the panel answers `queued` (this conversation is not in front), also give the user the printed URL in chat and say the page opens when they come back to this conversation.
- **Character preview** (only if the user asked or sent their own character image), after the character sheets and 1–2 main backgrounds are generated and checked: register them (`label=path`, labels show on the page), open, tell the user in one or two lines in their language which images these are and what to look at (design, palette, likeness to their image); they click an image to write a note and press a button. `wait` as for the film. Changes requested: regenerate per the notes (old character sheet or the user's image as reference), `reply … --done`, register as `chars-v2`, wait again. Approved: work through to the final film without stopping again; once the film is registered, the character entry folds below it.
- **Final film**, after one round of self-review and fixes: register it (with cards, the `-bookends.mp4`), open, and tell the user in three to five lines in their language what this version is, what to focus on, and that they can write notes on the page (pause on a moment; timecode and shot attach automatically) and press the submit or approve button, and you will continue. Changes requested: act on every note or explain why not, reply, register a new id (`film-v2`), tell the user to refresh, wait again. Approved: deliver.

```sh
# preview (user asked, or sent their own character image): character sheets + main backgrounds, label=path
$R add hero=src/char_hero.png wide=src/bg_wide.png --id chars-v1 --title "<title or story>" --lang <the user's language code>
# final film: rendered, one round of self-review fixes done
$R add out/<name>.mp4 --id film-v1 --known "issue seen but not fixed yet" --lang <the user's language code>   # shot list attached automatically
$R open --no-browser        # built-in browser panel (Codex app, right side): start the server, print the URL, open it in the panel
$R open                     # no panel (Codex CLI, terminal): start the server, open the system browser, print the URL
```

Then describe the version and what to focus on in three to five lines, and **run `wait`** (30 min; Codex: in the foreground, command timeout above 31 min, keep polling if it returns in chunks; Claude Code: with `run_in_background: true`, carry on when it reports back). **Never pass a shorter `--timeout` and never stop waiting early**: the user may still be watching or writing notes, and anything you deliver before the wait ends skips their review:

```sh
$R wait                     # on submit or approve, prints every note with id, timecode and shot (image number for a preview) and text; exit code 3 = no answer in 30 min
# changes requested: fix each note, reply on the page, register a new version, wait again
$R reply film-v1 n3 "swapped the landing for the squashed cell, added a thud" --done
$R add out/<name>.mp4 --id film-v2   # new id per version; the page shows the latest, older notes fold below
$R wait
```

- No answer (exit code 3): the round ends; when the user replies in chat, read notes with `$R notes`. If the page won't open at all, the user pastes notes into the chat.
- If `open` prints `http://127.0.0.1:…`, notes are saved to `review.notes.json` in the film folder. If it prints a local file path, the server didn't start (usually the sandbox forbids listening on a port: request access and run `open` again); notes then live only in the browser, so ask the user to use the page's copy-notes button and paste them into the chat.

## Tools (`scripts/`)

- `setup.sh`: `start` checks and starts any missing install in the background; `check` inspects only; `python` prints the Python to use; no argument builds the Python env + downloads score instrument samples (about 1.4 GB; offline it only warns, run `setup.sh instruments` later); matting model optional (`setup.sh model`).
- `animi.py`: `styles` lists styles, `prompt` builds prompts, `check` QA for sheets, `clean` removes translucent haze from transparent backgrounds, `slice` cuts cells, `anchors` finds anchors, `live` measures liveliness of a film, `stylecheck` checks style packages; library functions in `api.md`.
- `layers.py`: foreground layers, multi-layer parallax, small environment motion (swaying plants, particles, glints). `bookends.py`: title plates and optional title/end cards (only when the user asked).
- `sound.py`: `vo` narration, `lint` checks the sound sheet, `build` mixes and makes subtitles, `mux` muxes into video, `check` loudness / true peak / dead air of a film, `voices` lists voices, `kinds [style]` lists available foley (★ = recommended by the style), `times` lists all times resolved per shot.
- `init_film.py`: creates the film folder and copies the compositing template with settings filled in. `film_template.py`: the template (shots, camera, anchored sprites, character light and shadow, set layers, transitions, subtitles, sound, all automatic checks; `lint` writes `work/shots.json`; renders without assets, but with missing images only as a draft, `work/<name>-draft.mp4`).
- `gen.sh`: for agents without built-in image generation (Claude), one image via `codex exec`. Codex uses its built-in image_gen (§4); `grab_image.sh` is the fallback when no path comes back.
- `contact.sh` contact sheet, `motion_check.sh` consecutive-frame check, `selfcheck.py` pre-delivery self-review sheets (every 0.5 s + before/after every cut, too-dark frames marked red; `--style <style>` uses the style's brightness threshold).
- `review.py`: review page (`add` registers a film or preview images, `open` opens it, `wait` waits for the user's button, `notes` reads notes, `reply` answers a note).

## 8. Delivery

The film (`out/<name>.mp4`, or `out/<name>-bookends.mp4` + `.srt` with cards), `<name>.srt`, `out/contact.jpg`, `production-log.md`, plus the report (SKILL.md §5). `ffprobe` may report a few hundredths of a second more than the length (audio padding); the frame count is what counts, don't re-encode for it. Keep every generated png; rename bad ones with `_bad`.
