# Image generation: filling slots

`animi.py prompt <style> <asset type> <slot file>` builds the prompt: style anchor + the asset type's template + the style's notes for that type + common rules. **You only write the slot file** — never the style, the template or the rules. The final prompt is English; write slots in English.

## Syntax

**Slot file** (what you write): each slot starts with a line beginning `[name]` (ASCII square brackets, lowercase snake_case name); the text continues, across lines, up to the next header or end of file. Text after the header on the same line belongs to the slot. Old `【名字】` headers still parse via the alias table (e.g. `【角色】` = `[character]`).

```
[character] a round little clay penguin, black back, cream belly, orange beak and feet, wearing a small red-and-white gingham apron
[action] the penguin flips a pancake with a small sky-blue frying pan held in both hands (do not draw the pancake in the pan).
1 standing, both hands holding the pan, looking into it
2 knees bent, crouching to wind up, pan pushed down
3 snaps upward, pan raised above the head, heels off the ground
4 head tipped back looking up, mouth an O
5 on tiptoe leaning forward, reaching out with the pan to catch
6 at the catch the impact drops him, body squashed
7 bounces back, chest out, pleased with himself
8 turns his head to the camera and winks
[held_prop] a small sky-blue frying pan
```

**Templates** (`styles/_common/*.txt`, `styles/<id>/prompts/*.txt`; you don't edit them for a film, but read them to know what's already said):

| Syntax | Meaning |
|---|---|
| `{name}` | Variable: filled from the slot of that name, or by the builder (`{aspect}`, `{_transparent}`). An unfilled variable outside an optional segment is an error that lists the missing slots |
| `[[ … ]]` | Optional segment: kept only if every `{var}` inside is filled, otherwise dropped whole (e.g. the held-prop sentence of `sheet8` disappears when there is no `[held_prop]`) |
| `<<name>>` | Replaceable part: default text in `_common/_parts.txt`, a style's `prompts/_parts.txt` replaces it whole (an empty entry removes it). Parts: `<<view>>`, `<<held_prop>>`, `<<ground_line>>`, `<<sheet_ground_line>>`, `<<prop_view>>` |

Part files use the same `[name]` headers as slot files. `{aspect}` comes from `--size`: `landscape` → `landscape 16:9`, `portrait` → `portrait 9:16`, `square` → `square 1:1` (old 横屏 / 竖屏 / 方形 still accepted). `--set name=value` fills a slot from the command line.

## Slots per asset type

| Asset | Slots | Reference image | Slicing |
|---|---|---|---|
| `character` character sheet | `[character]` | none | 4 views in a row |
| `sheet8` 8-action sheet | `[character]` `[action]`; add `[held_prop]` when something is held (otherwise omit it and the held-prop sentence is dropped) | character sheet (plus the sheet that drew the held prop) | `--n 8 --rows 2 --cols 4` |
| `sheet4` close-up sheet | `[character]` `[framing]` `[performance]` | character sheet | `--n 4 --rows 2 --cols 2` |
| `prop` | `[prop]` | optional | `--n <count> --rows 1 --cols <count>` |
| `fx` fx sheet | `[fx]` | none | `--n 8 --rows 2 --cols 4` |
| `bg` background | `[shot_size]` `[scene]` `[margin]`; `--size` sets the aspect | from the second camera position of a place on: the main background (see "Reference images") | not sliced |
| `layer` transparent set layer | `[set_layers]` ("a full strip of foreground grass, the top edge uneven tufts of blades") | that scene's background | not sliced; read with `layers.load_layer` |
| `texture` material texture | `[material]` ("a whole sheet of flattened tomato-red clay with fingerprints and palm marks"); `--size` sets the aspect | usually none | not sliced |

## Writing good slots

**Every slot**
- Every noun may be drawn. No examples or lists ("pot, bowl, jar") in `[prop]`, `[fx]` or `[scene]`: name only what this image contains, and end with "draw only the items above".
- Gradual changes are numbers per cell ("leans 6° → 15° → 25°", "stretched to 1.5× → 2×"); turns are the silhouette the camera sees ("full face → narrower → edge-on"), never "vertical → horizontal". Vague progressions come back as identical cells or turned on the wrong axis.
- Every asset in a shot is drawn from that shot's camera height (eye level, slightly above, about 45° above, top-down). A shot from another height gets its own sheet; a reference image passes on its viewpoint, so never reference an image from another camera height.

**Character**
- Describe looks, not personality: build, colours, clothes, accessories, one or two memorable features. For supporting characters give the size ratio to the hero ("twice the hero's height").
- Every sheet's `[character]` is copied verbatim from the character sheet's.

**8-action sheet**
- The 8 poses are **one continuous action** in order: anticipation → action → follow-through. One sentence per cell describing body pose and expression; no "then".
- **8 poses are not 8 different poses**: 2–3 key poses with transitions between them, following "anticipation (pull back the opposite way) → transition (halfway) → arrival → slight overshoot → settle". Example (wave): 1 standing straight 2 body sinks slightly, hand pulls back 3 hand halfway up, body leaning forward 4 hand at its highest, on tiptoe 5 hand swings a little past forward 6 back to raised hand, heels down 7 hand halfway down 8 standing straight, smiling.
- **Overlap body parts**: head turns first, body follows, hands arrive last; ears, tail, scarf, hem lag a beat and settle after the body (write it into the cell: "body has stopped, ears still swinging forward").
- Prompt poses are numbered from 1, sliced cells from 0 (pose 1 = `walk_0`): there is no `walk_8` in the timesheet.
- State where the prop is in every cell ("from pose 5 the pan is in the left hand"); anything that flies off is not drawn in the cells — generate it as a separate prop.
- One action per sheet. Cycles (walk, run): the 8 poses are one full cycle.
- On a QC FAIL, change one thing and regenerate: poses touching → "leave larger gaps between the 8 poses"; extra things drawn → "draw only the character".

**Close-up sheet**
- `[framing]` defaults to **full body**: "full body, from the top of the head to the soles completely inside the cell, camera close and at eye level; feet on the same line in all four cells". Only for a face close-up write "face and shoulders only", and when compositing put the cut below the frame's bottom edge. `[performance]` gives 4 expressions or small actions for close-shot reactions; keep adjacent cells close (expression changes, body moves slightly) so they chain into one continuous reaction.

**Effects**
- Describe 8 stages of the effect in this material from appearance to disappearance ("a clay splash: 1 a small blob just thrown up … 8 the last drops falling"). End with "draw only what is described above; no extra stars, pompoms or threads": material lists in the style package ("sparkles are small yellow stars") get drawn as content otherwise.
- Smoke, breath, snow, spray, thin wings: "completely opaque <material>". See-through comes from alpha in compositing (about ×0.9); asked for directly, the model draws haze that won't cut out.
- For particles (snow clumps, petals, confetti): "8 fully opaque X, each a different size and shape, from pea to walnut size"; the slices are used directly as particles.
- Transitions are also made from fx sheets (style.json `transitions` says what is needed).

**Backgrounds**
- `[shot_size]`: `wide` / `medium` / `medium-close` plus camera position ("eye level, camera at stove height"). A second background of the same place changes the camera position ("shot diagonally from front-right, turned about 40 degrees from the front view"), not just a tighter crop of the same composition — otherwise the cut is a jump cut.
- Props and props held in action sheets: same camera position as the set ("camera slightly above the pan's rim, the opening a very flat ellipse, the back rim visible, not from above") and size relative to the character ("pan about as wide as the body"). Containers that will hold something get a high-contrast inside colour ("dark grey non-stick coating inside the pan") so the code can find the inside.
- `[scene]`: what must be in the shot and where; positions and sizes of key objects are fixed at storyboard stage ("stove in the left third, half the frame height").
- `[margin]`: where the hero stands ("a flat patch of floor in front of the stove, left of centre").
- Same place, new shot size or camera position: **use the place's main background as reference** and write "this is exactly the place in the reference image; the floor, the big tree and the rock are all still there; the camera moves to … (diagonally from front-right, turned about 40 degrees / crouched at ground level), not the same composition as the reference", describing objects in `[scene]` the same way as in the wide. Compare it side by side with the main background: floor colour and landmarks must match and the composition must clearly differ; if the composition is nearly the same, increase the camera change and regenerate, or the cut is a jump cut. State changes (day / night, door shut / open): generate one version, then use it as reference for the other with "exactly the same picture, only change …" (here the same composition is the point). For relit pairs, the first version says "no light source"; the second "only change the lighting: warm yellow light from an unseen small lamp on the left (do not draw the lamp)".
- Fully dark shots: `[scene]` says "nothing lit at all (no windows, lamps, stars, moon)" — a fixed style sentence like "keep one or two warm lights" can't be negated from a slot.
- List everything code will composite into the shot (characters, props, plants, fish, bubbles, lamps, a sun or moon) and end `[scene]` with "no <each of them>"; where code attaches something, describe the bare attachment point ("bare twig tips with nothing hanging on them", "no sun, no clouds, nothing round in the sky"). The background otherwise draws them too, and the composited copy doubles them.
- The hero's colour appears nowhere in the sets: each `[scene]` says "no <hero colour> in …", and the ground the hero stands on contrasts with its body. A hero whose material matches the ground gets dark or saturated accents (ear tips, a scarf).
- Medium-close backgrounds name one surface in focus, say everything behind it blurs into patches of colour, and list the set objects that must not appear.
- For parallax with a separately composited foreground, the background's nearest foreground is only a thin strip along the bottom.
- Wide pans need extra-wide backgrounds: generate two that join left-right, or pan only slightly over one 16:9.

## Reference images

- Action sheets and close-up sheets: **always** the character sheet. In Codex, pass them to image_gen as absolute paths in `referenced_image_paths`; with `gen.sh`, append them after the command.
- Backgrounds: **other camera positions of a place take the main background as reference** so floor and landmarks match. A reference without a stated camera change makes the model copy the layout and the hard cut becomes a jump cut, so `[shot_size]` must name the new camera position and "not the same composition as the reference", and the result is compared side by side with the main background. Relit and state-change versions write "exactly the same picture, only change …" (same composition intended).
- **A prop in the wide and in the close-up must be the same object**: the close-up (background or close-up sheet) takes the wide original containing the prop as reference, with "this is exactly the small oil lamp from the reference image (same lamp: same shade, same brass base, same handle), now seen very close", and says what attaches where ("a small round hole facing right at the right end of the brass base; a knob will be attached there later — do not draw the knob"). Align cells on the prop when compositing.
- Small props a character always holds (flag, lantern): the sheet that drew it is the second reference; `[action]` says "exactly the same flag as in the second reference image, held in the right hand in every cell".
- Character and prop on the same close-up sheet: prop image as reference, `[framing]` adds "the prop the same size and in the same place in all four cells".
- Landing sheets: character sheet + the object's prop image or fx sheet, "exactly like the last flower in the second reference image".
- Never use a background as reference for a action sheet (the scene gets drawn into it).

## When style text and slots conflict

- Fixed sentences in a style package ("keep one or two warm lights at night", "the room is visible in wides") override negations in slots. Write style sentences as conditions ("draw warm lights only if `[scene]` asks for them"), not "always X".
- Where a style differs from the common template (the character's four views, held-prop camera), replace the whole part in `prompts/_parts.txt` (`_common/README.md`); never write "this replaces the line above".
- Lighting of transparent assets is settled in compositing: generated transparent assets are flat-lit (strong lighting in the style anchor only takes on backgrounds); night and dark scenes rely on compositing light (compositing.md §7).
- Full-frame material textures (smears, covers, title plates) use the `texture` type; `prop` draws a small patch with transparent margins, `bg` turns it into scenery via the style's set text.
- Transparent set layers (foreground grass, paper waves) use the `layer` type with the scene's background as reference; the background then leaves out the nearest foreground (compositing.md §6).

## Common failures

| Symptom | Fix (change one thing in the slots) |
|---|---|
| Character doesn't match the character sheet | Check the reference was attached; `[character]` identical to the character sheet's |
| Two poses stuck together | "leave larger gaps between the 8 poses"; or split into two 4-cell sheets |
| Cells differ in size | "the character is the same size in all 8 poses, no depth change" (the template says this already; one regeneration usually fixes it) |
| Hero drawn into the background | Don't mention the hero in `[scene]`; the template already says "no main character" |
| Transparent background came out white or checkerboard | Regenerate; if it persists, install the matting model with `setup.sh model` and use `animi.py check --birefnet` |
| Looks like an existing character | Change colours and proportions, drop the too-similar features |
