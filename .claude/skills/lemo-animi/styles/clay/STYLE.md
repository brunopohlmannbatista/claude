# Clay stop-motion (clay)

**In one line**: oil-clay characters on a tabletop set; exaggerated faces, squash and stretch, the funniest of the styles.

## Best for

- **Subject**: small domestic farces at home, in a kitchen, in a little shop. A small character tries to do one thing, botches it twice, gets it on the third try; something set up early pays off at the end (the dough flung away on the first try lands in someone's bowl at the end).
- **Palette**: saturated, cheerful primaries: cream-yellow walls, tomato-red and off-white check, sky-blue crockery, grass-green plants.
- **Light**: warm, soft daylight; key light top left, one beam of window light, soft shadows.
- **Camera**: eye level, lens between the character's chest and eyes. Wide shots establish the tabletop set, medium shots carry the action.

Not for: horror, realistic or serious subjects, big crowd scenes, grand landscapes, stories that are mostly dark or at night.

## Signature moves

- **Squash and stretch**: squash hard on the wind-up, stretch hard on the release; draw it fully in the sheets (`prompts/sheet8.txt` covers it). Code `sx / sy` only adds a little.
- **Face distortion**: the mouth can open to half the face, eyes squeeze to a line or droop. Draw key reactions in a 2×2 close-up sheet, so they read big.
- **Things stick, cover, fall off**: clay comedy is softness: slapped flat against a wall and stuck, with a drip hanging; dropped over someone's head; finally falling right into a bowl. Anything covering a character is drawn into the sheet; the prompt says it covers only a small patch on top of the head with ears and face showing (otherwise those cells look like a mushroom cap). For stuck or hanging things use a squashed prop plus an fx sheet (a hanging drip is the drip fx turned upside down, hanging from the lower edge).
- **Food in a pan or bowl**: the rim tilts slightly toward the camera, back rim visible, contents showing inside (`prompts/_parts.txt` `[held_prop]` covers it and it generates reliably). Contents that stay in the pan the whole time go into `[held_prop]` and are drawn into the sheet. Contents that fly out, flip, or grow: `[held_prop]` says "the pan is empty, the dark charcoal pan bottom is visible", generate the contents as a separate prop and composite them into the pan (compositing.md, containers section).
- **Clay smear**: a lump of clay (a colour already in the film, see `how` in style.json) smears across the lens from off-screen, then peels away to reveal the next scene. Once per film, at a section break like "try again" (`tr='clay_smear'`).

## Compositing

- **Character relight**: none (`preset.light` empty). Daylight flat-lit scenes take transparent assets as they are.
- **Shadow**: `contact`, strength 0.35 (`preset.shadow`); pass `lift` when airborne so the shadow stays on the ground and gets smaller and fainter.
- **Rigid**: no (`rigid: false`); `idle=True` gives soft-material breathing.
- **Transitions**:
  - `clay_smear` (`kind: smear`): smears in from the bottom right over the 4 drawings before the cut, covers fully for 1, peels off toward the top left over 4 (`before 4`, `after 5` = full cover `hold 1` + peel 4). Texture `src/fx_smear_tex.png` is generated as type texture (prompt in `how` in style.json); the template's `load()` reads it into `assets` when it exists.
  - Everything else is a hard cut.
- **Title plate** (`title.plate`): tomato-red rounded plate, cream text, texture from the style package's `ref/texture.jpg` (a film folder's own `ref/texture.jpg` wins; the smear texture `fx_smear_tex` also works, just copy it over); landing sound `pop`.

## Pitfalls

- **Clay figures look like smooth 3D plastic** → keep "fingerprints, pinch marks, tool marks" in the anchor; write clothes and accessories as "sculpted from clay, not real fabric".
- **Food looks behind the pan, or like a lid** → draw pans, bowls and plates with the camera slightly above: rim a flat ellipse, back rim visible, inside a contrasting dark charcoal (sheets via `[held_prop]`, prop sheets via `prompts/prop.txt`, both already written). Composited contents go only inside the "interior" area, with the front rim in front of them (compositing.md, containers section).
- **The pan in a sheet is still dead level (a flat edge, no interior)** → usually `[action]` says "side" or "flat" and pulls it off; remove that and regenerate the sheet. If regenerating fails: generate a separate empty pan body with no handle, camera slightly above (like `ref/prop_body.png`); size and angle it to the sheet pan's rim, align the bottom, match its colour to the sheet pan (gain from its median colour) and lay it over the pan in the hand. Replace it in every frame where the character holds the pan, including when empty.
- **Character stands behind the stove or table** → draw the stove back over the character: `film.py still <drawing>` for a still, read coordinates along the stove edge (flames included) in an image viewer, write a polygon, and after placing the character cover it again with `poly_mask`; when stove and wall contrast strongly, `animi.color_mask` is faster. Place the held pan again on top, or the flames end up in front of it.
- **Pan contents change size** → inside the pan, size by the pan width measured in that cell; out of the pan, use one width for the whole film. Check measured rims with `spot_board` first.
- **Subtitles** → white text with dark-brown outline reads on the warm-yellow kitchen, no plate needed.

## Sound

- **Score**: cartoon band: staccato clarinet on melody, tuba oom-pah bass, pizzicato strings for harmony, woodblock and shaker on the beat. Failure `stop` (woodblock), collision `thud` (timpani), success `boom` (bass drum + cymbal) followed by a `sparkle` glockenspiel arpeggio.
- **Foley**: `step` small quick steps, `squish` squash / flatten / cover (heavy ones v 0.8–1.0), `boing` bounce up or back, `pop` peeking out and small surprises (small characters pitch 1.3), `thud` collision, `whoosh` fling, `clink` pan against spatula, `tap` small actions; `smear` for smearing, `sparkle` for things appearing. Full list: `sound.py kinds clay`. The smear transition gets two `squish`: a low one before the cut, a high one after.
- **Narration** (optional): lively, like telling a joke to a kid, rising at sentence ends; count the tries ("First try… second try…"), keep the success line short ("Splat! Done.").

## Reference images (`ref/`)

- `character.png`: character sheet, small penguin in a check apron, four views
- `sheet8.png`: 8-cell action sheet, flipping a pancake in a pan (crouch and squash → toss and stretch → look up and wait…); rim slightly toward camera with back rim and contents visible, exactly what `[held_prop]` asks for
- `sheet4.png`: 2×2 medium-close-up sheet: surprised, deflated, eyes closed deep breath, eyes closed smile
- `bg_wide.jpg`: wide, clay kitchen (stove left, jars right, window light)
- `bg_mid.jpg`: medium, same kitchen from another camera position (angled from front right of the stove)
- `bg_close.jpg`: medium-close background, shallow depth of field, blurred counter
- `prop.png`: prop sheet, three flat-lying items spaced apart at one scale (pancake, flattened pancake, plate; eye-level "lying flat" versions)
- `prop_body.png`: empty pan body with no handle, camera slightly above, back rim and dark-grey bottom visible; lay it over a sheet pan that came out level
- `fx.png`: fx sheet, clay steam in 8 stages from rising to gone
- `texture.jpg`: material close-up, tomato-red clay pressed against glass with palm prints; title plate texture
