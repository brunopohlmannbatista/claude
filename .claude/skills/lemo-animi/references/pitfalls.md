# Pitfalls

Format: **symptom** | cause | fix.

## Image generation

- **An asset sheet draws a whole scene** | the reference image contained a scene, or a slot named a location | action sheets take only the character sheet as reference; no scene in `[action]`
- **The hero appears in a background** | `[scene]` mentioned the hero | background slots name only the place and objects
- **Text-like strokes despite "no text"** | model habit | ignore small ones; blur obvious ones locally or hide with depth of field; all text is set by code
- **Resembles a real brand or existing character** | features too close | change palette and proportions; describe shapes, never "looks like X"
- **A key object's position in the background blocks later scenes** | not decided before generating | at storyboard time, write key objects' position and size into `[scene]`
- **Result differs from expectation** | generation isn't controllable | look first and use it if it works; keep every png, add `_bad` to rejects
- **A held prop is unrecognisable** | wrong view | held or carried props use a view that shows their silhouette
- **A trunk or tail holding something gets drawn as an extra hand** | the model assumes "hold = hand" | write "the tip of the long trunk curls around the flower stem; the trunk is one continuous tube; no hands or fingers; only four legs", and zoom in on the grip afterwards
- **A pot on the stove looks wrong, whole bottom visible** | prop drawn top-down | state the camera: slightly above the pot rim, the rim a very flat ellipse, not top-down (3D styles have this in `prompts/_parts.txt` `<<held_prop>>` and `<<prop_view>>`); also state prop size in action sheets
- **A large translucent haze in the transparent area; check reports edges not transparent** | shadows or backing paper rendered semi-transparent | not broken: `animi.py clean`, recheck, use the cleaned version if it passes
- **fx sheet sprouts unrequested stars or pompoms** | the style's material list was read as things to draw | end `[fx]` with "draw only the things listed above"
- **Two backgrounds of one place cut like a jump cut** | the second copied the first's layout | when using the main background as reference, state the new camera and "not the same composition as the reference"; compare side by side and regenerate with a bigger camera change if nearly identical (prompts.md, "Backgrounds")
- **A cut within one place reads as a new place** | each view generated alone without reference, ground and landmarks differ | one place, one set: main background first, other views with it as reference (directing.md §6)
- **A prop in the close shot doesn't match the one in the wide** | generated separately without reference | use the wide's original as reference: "the very same … from the reference, attached at …"
- **A prop is missing a piece** (edge flattened) | broken at generation, far from the frame edge so QA misses it | zoom the prop sheet preview after generating; prompt "complete, with wide empty margins all around"
- **Breath puffs, arrows, sweat drops in close-up sheets** | symbols added by the model | the close-sheet template forbids them; regenerate that sheet if they appear

## Action sheets

- **The character shifts position and size between cells** | not guaranteed by the model | place by anchor (`place_at`), not by bounding box; one scale per sheet
- **Drawn motion arcs or speed lines** | comic habit | forbidden in the layout; if still there, `animi.py slice --fragments drop`
- **The same object differs in size between two sheets** | generated separately | rescale one; draw interacting objects on the same sheet
- **Adjacent cells too far apart** | 8 cells can't hold the whole action | generate a finer sheet for slow passages; a 4-cell transition sheet at the join
- **8-cell cells too small, close shots blur** | not enough resolution | use 2×2 close-up sheets for close shots
- **Medium-close shows only the upper body with the crop edge in frame** | close-up sheet drawn "chest up" and placed mid-frame | close-up sheets draw full bodies by default; only close-ups crop, edge below the bottom of the frame (the template warns about a half-body sticker)
- **Stiff, slideshow-like motion** | cells swapped evenly over time (`int(t * speed)`), 8 cells all key poses with no breakdowns | `ts.act` fast in slow out; draw anticipation, breakdowns, overshoot; settle on arrival (`settle`); shift weight one way
- **Bilingual subtitles on two plates or wrapped** | a custom subtitle setup | write `en` on the narration line; the template sets one row per language on one plate
- **Squash drawn in the art, squashed twice more in code** | double processing | code adds only ±4–7%
- **An 8-cell loop feels mechanical over time** | too few drawings | reorder for variation, or generate another sheet

## Compositing

- **Character floats** | placed by cell bottom | place by the anchor's ground line
- **Hero doesn't look like it's standing on the crate / plank / hands** | placed on the floor's ground line, or support and hero moved separately | back-solve the sole from the support's top face every drawing; draw weight-bearing poses with the support in the same cell (compositing.md §3)
- **Key, hat or tool drifts or spins on the wrong axis** | each cell drawn freely; abstract rotation words | same mount point in every cell; describe each angle as the camera sees it; check every cell before slicing (compositing.md §3)
- **Character changes size between sheets** | each sheet scaled by its own median | `A.scale_ref(HERO_H, <standing cell>)`
- **Cell swaps are obvious** | swapped while still | swap during fast motion, or hide in a cut or occlusion
- **Pasted things break occlusion** | missing foreground layer | cover with the front-edge occlusion layer (compositing.md §4)
- **Blurry after a push-in** | scaling the finished frame, resampling twice | `cam.plate` crops from the original, sprites scale by `cam.k()`, one resample only
- **Light direction wrong after mirroring** | side-lit asset, or warm light from one side drawn into the art | mirror only top- or front-lit assets; code light uses `char_light(flip=True)` for the mirrored direction
- **Transparent character looks pasted into night or dark scenes** | asset has flat studio light | `animi.char_light` (defringe, darken and tint, rim light, warm light), parameters in the style's `preset.light`; leaving a light pool: `floor_light`
- **Character size pops between close-sheet cells** | scaled per cell bounding box | one scale per sheet (set from the most ordinary cell)
- **Renders slow with many environment layers** | each sprite rescales the whole cell every time | `layers.Sprites` caches per scale step
- **A group of small things jumps when passing from in front of the character to behind** | layer changed mid-way | keep them behind, or switch only where they don't overlap the character
- **Wheels seem to turn backwards** | rotation per drawing over half the symmetry period | small fixed step
- **Camera jitters every frame in an on-twos film** | camera steps per frame | camera steps per drawing too (the template already does)
- **In an old film script, `shake` jolts in a random direction every drawing** | `film.py` copied from an old template implements shake with `ts.jitter(pic, st['shake'])` | switch to the current template's `shake_cam` (one downward jolt, single direction) and hook `style_lint`, `repeat_report` into `lint()`
- **Character sways while standing** | poses cycled to avoid long holds; `sin` back-and-forth position; small rotations/wobbles on rigid materials | fix standing foot `x`, play the reaction once and hold the last pose; for holds over 2 s add face-only variants or environment motion (camera motion alone is not enough)
- **Things appear from nowhere** (apple on the tree and the falling apple both visible) | a duplicate layered over the same object | state changes use two background versions
- **Flame jumps in front of the pot when it's lowered** | the occlusion layer covers everything | paste the held prop again after the occlusion layer (compositing.md §4)
- **Something lying flat looks like a crumpled leaf** | a top-down image squashed | generate an eye-level "lying flat" version
- **Contents look behind the container or like a lid** (pancake in a pan, fruit in a basket) | container drawn fully eye-level, only the front rim, no back rim | the rim must be visible (slightly higher camera); draw contents only inside the rim (compositing.md §7½, "Containers")
- **Contents change size in the container** | rim measured wrong (handle included, back-lit half missed), or after leaving the container they follow a container drawn smaller | overlay the measured rim on the art to verify; inside, follow that cell's container; after leaving, use one film-wide size (compositing.md §7½)
- **A round thing on a tilted tray looks square** | placed as a level flat ellipse | squash and rotate to the ellipse fitted to the tray

## Pacing

- **First frame is dull** | starts from nothing | frame 0 already shows something interesting
- **Second half is thin** | the hero keeps doing the same thing | environment and side characters react on the beats
- **Repeated actions feel repetitive** | same cells reused, loops run too long | vary timing and outcome each time; break loops with another action or a cut (`repeat_report` checks)
- **Key acting too small to read** | key acting in wide or extreme-wide | cut to medium or medium-close for key acting (the ending gag too: cut to a medium-close of whoever catches it); extreme-wide only for routes
- **Title or subtitles unreadable** | letters made as textured lettering (fabric, cut paper, fuzzy), or no backing on bright frames | Source Han Sans Bold flat colour, style on the plate; subtitles use `subtitle.plate`
- **A stretch is almost black** | iris closed off the hero, cutting from a push into darkness | close the iris toward the light source with the hero in the light; cut on eyelines instead of through darkness (the check reports too-dark ranges)
- **A cut stutters** (small at second 5, suddenly big at second 6) | jump cut: same angle, only size changes | a background from another angle, or an in-shot push/pull (directing.md)
- **The whole film seems to zoom in and out with no scene change and no close-up** | shots padded to hit a count and all three sizes, cutting wide → medium → medium-close in one place and view; separately generated backgrounds are dissimilar enough to slip past the jump-cut check | don't pad: play a scene in one shot; cut only for a new place, a close-up detail or a new view for a reaction; give every shot `place` / `view` (directing.md, "No zoom cuts")
- **Black at start or end** | iris in/out added by default | don't; the first frame is picture, end holding the last shot
- **Abrupt transitions** | hard cuts between static frames everywhere | cut on action, carry with camera motion, dissolve at quiet moments, one signature transition at a section boundary (directing.md, "Transitions")

## Sound

- **Narration mispronounced** (heteronyms, numbers, foreign words) | TTS uses the common reading | rewrite `text` as it should be read, or use a synonym; ask the user to listen on the review page
- **Narration too dense** | lines back to back | 0.3–1 s between lines; silence before the twist; `sound.py lint` reports coverage
- **Music drowns the narration** | — | ducking is automatic; if still too loud, lower that section's `energy`
- **Foley off by a frame or two** | times estimated in seconds | compute from drawings: `ts.pic_start(<drawing>) / 24`
- **Score "breaks" at cuts, beat misaligned** (at every section change) | section boundaries treated as a restart | sections change only the arrangement; the bar grid runs continuously through the film (`audio/compose.py` does this); use `hits` and `silences` to lock to picture
- **A gap of silence where bookends join the film** | the joined segment's sound fades out | no fade on the side that joins the film; put a foley sound around the seam
- **edge-tts can't connect** | needs the network (sandboxes are offline by default) | `sound.py vo` stops and prints a justification: request access, stating that edge-tts online voices generate the narration the user asked for and only the narration text is sent; if refused, drop `vo`, make the film without narration and say so in the report; never use a local offline voice

## Process

- **Stopping to report on a QA FAIL** | treating the check as the end | a FAIL means change the plan: change one thing and regenerate, split the sheet, recompose
- **Regenerating needlessly on a QA FAIL** | close-ups, hands entering frame, character + prop on one sheet, translucent haze all trigger it | look at the preview first and follow quality.md, "Handling check reports": `--allow-edge`, `--group grid`, `--clean`
- **Delivering the first version** | no review | go through every must-pass item; at least one round of fixes
- **Script-based string replacement on film.py** | silently hits other places | edit one change at a time with the edit tool; if batch-editing constants is unavoidable, read the diff and run lint
- **Only the auto-checkable rules get followed** | too many rules | before starting, read SKILL.md's four required docs (style package, directing, quality, pitfalls), the rest at their step; before delivery run `selfcheck.py` and go through quality.md
- **Parallel generation grabs the wrong image** | took "the newest image" | `grab_image.sh --stamp / --since`; `gen.sh` fetches by session id
- **`tools/film.py` fails with ModuleNotFoundError** | `SKILL` at the top not set after copying the template | set it to the absolute path of the skill's `scripts/` (the error says so)
- **Film named `film.mp4`, subtitles under another name** | `NAME` in `film.py` differs from `name` in `sound.json` | use the same short name in both
- **A set layer is in SHOTS but not in the picture** | `load()` doesn't put that name in `layers` | lint reports the layer name missing from `load()`; add it there
