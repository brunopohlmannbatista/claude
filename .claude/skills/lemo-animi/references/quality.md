# Review and must-pass items

## 1. What good looks like

Judge the whole film by these (your own review uses the still sheets and contact frames; pacing, pronunciation and mix balance are for the user to judge during playback on the review page):
1. **Always something happening**: something new every 1–1.5 s; no stretch plays like a slideshow.
2. **Readable**: the hero is big enough; every key performance has a medium or closer shot; with the sound off you can still tell what each character feels (face or pose), and the narration doesn't tell what the picture already shows.
3. **Looks like the material**: real clay / paper / felt shot on a table, not 3D render or stickers.
4. **The camera says something**: every cut has a reason (new place, close-up detail, new view for a reaction), cuts fall inside actions or between narration lines; no cuts to fill shot sizes.
5. **Sound carries it**: clear narration, a sound for every action, music following the mood, silence before the twist.
6. **A payoff**: the ending has a moment that makes you laugh or feel something.

## 2. Check every version

1. `film.py lint` and `sound.py lint`: all pass.
2. `film.py board`: pacing, hero size, shot changes.
3. Stills of key drawings (first drawing of each shot, both sides of every sheet change, contact and occlusion moments).
4. Full film → `contact.sh` contact sheet (8 frames, overall look).
5. `motion_check.sh` consecutive frames: the 1–2 most intense seconds, sheet changes, occlusions.
6. **Frame-by-frame self-review**: `"$PY" "$S/selfcheck.py" out/<name>.mp4 --style <style>` → `work/selfcheck_frames.jpg` (every 0.5 s, too-dark cells marked red) and `work/selfcheck_cuts.jpg` (before/after every cut), plus a report of too-dark time ranges. Look at every image against the list below, a long sheet one time-labelled page at a time; when a contact, subtitle or foot is too small to judge, look at a crop of the full-size still. Log each problem in the production log, fix it, run again.
7. **Check the sound by measurement, never by loading audio into your input** (SKILL.md hard rule 14): narration text written as it should be read (heteronyms, numbers), subtitle and foley times as scheduled (`audio/subs.json`, `sound.py times` beside the cue-boundary stills and contact frames; this checks the schedule, not what is heard), loudness, true peak and dead air (`sound.py check`). If `sound.py check` reports the measurement unavailable, the sound check stays open. Measurements don't show pronunciation, intelligibility, audible sync or balance: report those as "not listened" until the user comments. For a solo check, give the user the path of the stem in `audio/stem_*.wav`.

### What a reviewer will catch

- **Jump cut**: same camera on both sides of a cut, only the size changes; looks like a stutter. In the cut sheet: same background composition on both sides.
- **Zoom cut**: several shots with the same blocking and facing (hero left, friend right, big tree on the same side), only the hero's size changes; reads as zooming. A "medium-close" that still shows the whole body and the whole set is not a close-up either. In the cut sheet: hero on the same side and facing the same way on both sides = same view.
- **Broken continuity**: positions or states change across a cut (apple back on the tree, the pot in hand gone). Check the cut sheet.
- **Unreadable payoff**: you can't tell what happened (the apple looks balanced on the head, not stuck on the spines; the pancake looks behind the pan). Give the payoff a close shot and generated artwork.
- **Wrong prop view**: prop and set from different cameras (a top-down pan in an eye-level set), or you can't see inside a container holding something.
- **Inconsistent size**: the same object changes size between shots.
- **Medium-close as a half-body sticker**: cropped at the chest with the edge mid-frame. Medium-close shows the full body (head to feet, on the ground, with shadow); a close-up's crop edge is below the bottom of the frame.
- **Stiff motion**: poses swap evenly, each held equally long, like flipping slides; no weight in pose changes. Use `ts.act` fast in slow out, breakdowns and overshoot in 8-cell sheets, settle on arrival, weight following the action (compositing.md §5).
- **Bilingual subtitles not on one plate**: separate plates per language, or a line wrapped to two rows. One row per language, no wrapping, one shared plate (sound.md).
- **Character changes between shots**: after a sheet change or a cut, colour, proportions, accessories or markings differ (scarf colour, missing belly button, head-body ratio). Compare every sheet side by side with the character sheet; regenerate mismatches (character sheet as reference, `[character]` slot identical to the character sheet's).
- **Jump at a sheet change**: position, pose or facing pops when switching sheets. Check stills around the change: no foot-anchor jump, similar poses, or the change sits in fast motion.
- **Per-drawing jitter**: a still character shifts or tilts a pixel or two every drawing. The style's `jitter_*` must be 0; your own code adds no per-drawing random offsets.
- **Swaying while standing**: a character not walking cycles between front, lean-left and lean-right drawings, or slides back and forth in place. Causes: poses cycled to avoid holds, back-and-forth position formulas, small rotations/wobbles on rigid materials. Standing feet stay fixed; a reaction plays once and holds on the last pose.
- **Things popping in on a dissolve**: dissolving to the next shot on the same background fades a character or prop in from nowhere. Check the dissolve drawings: new things must walk or roll in, or use a hard cut.
- **Black at start or end**: iris in/out, fade to black. Start and end on picture.
- **Abrupt transitions**: hard cuts only. Cut on action, carry with camera motion, dissolve at quiet moments, one signature transition.
- **Sound breaks**: a narration line cut in the middle, the score stumbling at a section change.
- **Flat**: one camera cut back and forth, long stretches with no new action. Something new every 1–1.5 s.
- **Action not shown**: the story says "jump" but the feet barely leave the ground; it says "goes home" but the character walks on the spot. Key verbs must be obvious in consecutive frames: a jump has clear air (falling short by a visible margin if it misses); a walk has displacement toward the goal and arrives.
- **One place, mismatched sets**: shots at the same spot (under the same tree, by the same mushroom) have different ground colours, a different tree, a new path. In the cut sheet, ground and landmarks of one place must be recognisably the same. See directing.md, "One place, one set".
- **Not on one ground**: things on the same ground (hero, props, side characters) have inconsistent ground lines: the one in front has higher feet, or one stands mid-ground while another sits on the very front edge, so they look pasted on. The front one's feet are lower (nearer the camera); side-by-side feet are level; all stand inside the background's ground, not on its edge; everything on the ground casts a shadow (styles with shadow `none` get contact shadows with `put(..., shade=dict(k=0.3))`). Check feet and shadows in full-size stills.
- **Not standing on it**: feet hover in front of, above or inside the crate, step, plank or helper's hands they stand on; the support tilts and the foot doesn't follow; the body rises before a foot has landed. Check full-size stills at every step-on and step-off and while the support moves: sole on the top face, foot moving with the support (compositing.md §3, "Standing on things").
- **Wandering attached part**: a key, hat, tool or wheel drifts off its mount, changes side between cells, doubles, or turns on the wrong axis. Check every cell before slicing and stills of the moving part (compositing.md §3, "Attached parts").
- **Mismatched camera height**: a character drawn at eye level on a set seen from 45° above (or the reverse) never looks like it's standing there. Every asset in a shot shares the shot's camera height (prompts.md, "Every slot").
- **Hero lost in the set**: the hero's colour or material repeats in the background or ground and the silhouette dissolves. Check stills at full size and as thumbnails.
- **Pasted-on light**: a character, prop or effect brighter than the set or lit from another side, or its shadow falls the other way. Everything composited gets the scene light (compositing.md §7).
- **Floating hung props**: leaves, lanterns, signs, swings hang in mid-air with no visible attachment. Draw the attachment (leaf stem, rope end, hook), place it on its branch or rope, move with that layer's parallax; if it swings, pivot only around the attachment, never drift as a whole. Check full-size stills: the attachment must be findable.
- **Hero stuck in place**: in a scene only rain, grass and camera move; the hero doesn't travel, only changes expression. Compare first and last frames of each shot: how far did the hero move, did the pose change? Anything over 3 s without travel gets movement or a reaction (a few steps, a startled flinch, leaning in to look).
- **Facing flipped**: hero faces right before the cut, left after (usually two sheets drawn facing opposite ways). Keep facing within a scene; to flip, have the character turn on screen, or mirror the sheet where the style allows mirroring (compositing.md §7; carried things switch sides; check that it's right).
- **Hero too small**: wides count too: 23–29% in a wide already looks small; opening and payoff wides need ≥ 33%. The closing wide after the payoff must show what's carried or held. If the wide can't reach it, walk the hero on the foreground ground near the camera (perspective makes them bigger) or frame tighter on them.
- **Acting in an extreme-wide**: "looks down and recognises", "waves" at 15% of the frame don't read and lean on narration. Extreme-wides only show route and environment; acting goes to an eye-level medium.
- **Too dark**: in dark styles the hero and action disappear (iris closing to the edge, cutting from a push into darkness). Neither side of a cut in a dark style may be all black; cut on an eyeline (hero looks up → cut to what they see).
- **The same prop differs between wide and close shot**: lamp, knob or door in the close shot has a different design, position or attachment from the wide. Generate the close shot with the wide's original as reference and "the very same lamp from the reference…" in the prompt (prompts.md, "References").
- **Unreadable text**: title or subtitle letters made as fabric patches, cut paper or fuzzy edges, complex glyphs blurring; white subtitles dissolving into bright busy frames. Text is Source Han Sans Bold, flat colour, style on the plate; subtitles get a backing plate (compositing.md §8).

## 3. Must-pass items (any failure blocks delivery)

| # | Item | How to check |
|---|---|---|
| 1 | Enough shots (directing.md §3 rules), wide, medium and medium-close/close-up all present, no overlong shot | `shots_lint` |
| 2 | Hero size: extreme-wide ≥ 15%, wide ≥ 30%, opening and payoff wides ≥ 33%, medium ≥ 40%, medium-close ≥ 60% (share of the short side, measuring the character, not big props in hand); at most 2 extreme-wides, neither the opening nor the payoff; consistent across shots: adjacent same-size shots differ by less than 1.3×, a tighter size means a bigger hero | `film.py board` / the film's hero size check (`size_report`) |
| 3 | No dead holds, no swaying: every hold over 2 s has been looked at and is live (local detail, side character or environment moving; camera motion alone doesn't count); the hero never goes over 3 s without a new action; standing feet don't move, no cycling between poses; no unchanged replays (one action identical at most 2 times in the film); loops not too long (a cycle ≤ 6 s, a two- or three-cell loop ≤ 3 s) | `film.py lint` warnings, the render's `liveness` warnings (whole frame nearly still for over 2 s; fix each or list it with `--known`), `repeat_report` + `selfcheck.py` + consecutive frames |
| 4 | All effects are generated images; no code-drawn shapes, rectangles or geometric lines | consecutive frames |
| 5 | No glitches: things appearing or vanishing, duplicates, size pops or jumps at sheet changes, the character changing look, per-drawing jitter, swaying while standing, interpenetration, foot sliding, feet not on what they stand on, attached parts off their mount, floating hung props, effects over the face, whole-frame brightness flicker, pasted-on light | consecutive frames, stills around sheet changes, full-size stills at every contact |
| 6 | Sound: score and foley present (narration too if requested), no FAIL from `sound.py lint`, the film has an audio track; every landing and impact is scheduled on its drawing; `sound.py check` on the delivered file passes (measured; listening is the user's) | `ffprobe out/<name>.mp4` shows audio; `sound.py times` beside the contact drawings |
| 7 | Subtitles (if narrated): every line subtitled, in sync, inside the frame, not over the hero's face; bilingual: one row per language, no wrapping, one shared plate | subtitle timestamps (`audio/subs.json`), stills at line starts and ends, `sound.py lint` |
| 8 | Length: the story = sound sheet `dur`, picture and sound equal; with cards, the delivered file = the length the user asked for | `film.py lint`, `ffprobe` on the delivered file |
| 9 | No AI-drawn text, logos, or characters resembling existing works | contact sheet |
| 10 | Reviewed and fixed: every version has a timecoded review record; problems found were fixed and re-reviewed; anything not watched or heard is "not checked" | production log |
| 11 | No jump cuts, no zoom cuts (no size-only cut in the same place and view), continuity holds; views of one place are recognisably the same place; things on one ground have consistent ground lines and shadows; every asset in a shot from the shot's camera height | `shots_lint` (background similarity, zoom cuts via place / view) + `selfcheck.py` cut sheet |
| 12 | Payoff readable: visible (big enough or a close-up), character and key prop in the same generated artwork | cut sheet, stills |
| 13 | Enough assets: SKILL.md asset minimums met (background views, one sheet per action, close-up sheets) | image log in the production log |
| 14 | Visible: no stretch too dark to see the hero | full-film check, `selfcheck.py` too-dark report |
| 15 | Text: title, end card, subtitles in Source Han Sans Bold flat colour only, sizes at or above the minimums, the most complex glyph legible when enlarged | full-size stills |
| 16 | No placeholders: lint reports no missing images; the film is not a draft (`work/<name>-draft.mp4`) | `film.py lint` |

### Handling check reports

Tools point at places to look, not all of them need redoing:

| Report | Must fix | May pass after checking the image (log timecode + reason in the production log) |
|---|---|---|
| `check` edges not transparent | drew a whole scene, changed background colour | translucent haze (the hint gives its share): use the `--clean` version if it passes; close-up (face and shoulders only), hand reaching into frame: `--allow-edge` |
| `check` wrong subject count | merged figures, missing cells, extra characters or scenery | a cell legitimately has two pieces (two characters, character + prop, fx fragments): recheck with `--group grid` |
| `check` touches frame edge | a full-body sheet cut off | deliberate edge crop: `--allow-edge` |
| `check` ground line / height spread WARN | — | deliberate crouch, jump, puff-up; floating or top-down characters (`--float`) |
| Jump cut | adjacent shots from the same camera with hero size differing by less than 1.5× | the cut sheet shows it isn't (different angle, just similar tones): `cut_ok='reason'` on the shot |
| Zoom cut | hard cut in the same place and same `view` that only changes size; a close-up whose hero is under 2× the previous; one place flipping shot size 3+ times | the cut sheet shows a real change of view and `view` was just missing: add it; otherwise `cut_ok='reason'` on the shot |
| Long hold | dead hold (nothing moves) | a side character or the environment visibly moving (camera motion alone doesn't count): `live='reason'` on the state |
| Repeated action | the same action replayed unchanged a third time, a walk running too long in one shot, a two- or three-cell back-and-forth | a deliberate repeat gag, a walk crossing the whole frame: `rep_ok='reason'` on that state |
| Size mismatch across shots | same size jumping, tighter size without a bigger hero | character walking toward camera, deliberate framing: `size_ok='reason'` on the shot; for height-jump warnings at sheet changes, look at both stills first; crouch, jump and similar pose changes need no fix |
| Hero too small | fix by default | deliberate distant framing that isn't the opening or payoff: `min=` on the shot, reason in the production log |
| Too dark | hero or action invisible | a deliberate black moment under 0.3 s; dark styles adjust the threshold with `preset.dark` |
| Missing image | must be generated before delivery | never |

## 4. Production log `production-log.md`

- Director's plan (logline, beat sheet, narration script, shot list, layered action table, image list)
- Image log: each image's name, regenerations and why
- Problems found in each review round and how they were fixed
- **A verdict for each must-pass item** (all 16 in §3, each "pass / fixed / known issue / not checked" + evidence)
- Self-assessment (1–5) and what you're least happy with
