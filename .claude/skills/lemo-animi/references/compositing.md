# Compositing: turning assets into moving pictures

## 1. Assets: transparent background, slicing, anchors

- Action sheets, close-up sheets, props and fx sheets are **transparent PNGs**. `animi.py check / slice` detects this: finds subjects by alpha, slices by "territory" (each pixel goes to the nearest subject, so a tail reaching into the next cell comes along) and outputs RGBA cells.
- `kit.sprite(f'{WORK}/cells', None, 'toss_3')` -> `(C colour, a alpha, M)`, straight into `place_at`. No mask files needed.
- Image generation sometimes returns a white background: regenerate first; if that fails, install the matting model with `sh setup.sh model`, run `animi.py check/slice --birefnet`, then `cut.py` for masks and `kit.sprite(cells, masks, name)`.
- **Large semi-transparent haze in the transparent background** (the model drew shadows or backing paper as an alpha 100–200 cloud): `check` reports opaque edges and the haze ratio. The image is fine, don't regenerate: `animi.py clean in.png dehazed.png` (fx sheets add `--min-area 20`), then check / slice the de-hazed file (or `check / slice --clean`).
- Images not generated yet: `plate()` / `sheet()` in the template (backed by `animi.asset`) stand in with `<name>_bad.png` or a grey placeholder, so the storyboard still runs and can be reviewed; lint keeps reporting the missing image and the full render only writes `work/<NAME>-draft.mp4`. Deliver once they exist.
- Backgrounds are opaque: read the original with `kit.rd` and **don't pre-scale** (`cam.plate` frames from the original and resamples once).

## 2. Alignment: anchors, not bbox centres

Characters drift inside the drawings, jumping cells are drawn higher, a swinging tail changes the box. Give every cell a physical anchor and place it as "anchor at (x, y)":

| Case | Anchor (`place_at(anchor=...)`) |
|---|---|
| Walk, run, stand | `'body'`: ground line + body centre (mean x of the top 60–70%, ignoring the tail) |
| Bike, car, vehicle | `'bottom20'`: centre of the bottom 20% of the box (the wheel row) |
| Box only | `'bbox'` |
| Standing inside a prop, leaning out of it in a close shot (person in a porthole, head out of a pot) | `'base'`: midpoint of the bottom strip (the prop's base); no jump when the box widens as the character leans out |
| Top-down or diagonally walking puppet | Body core: `animi.set_core` stores the body centre after an opening removes legs and antennae, `place_at(ref=core)`; automatic in the template with `flags.top_down`, and hero size is measured by body length |
| Floating (water, sky), particles | Box centre: `place_at(ref=(box centre))` or `layers.Sprites.put(at='center')`; ground line is meaningless, `check --float` |
| Rooted things swinging at the root (grass, seaweed) | `anchor=0–1` (position along the box bottom; `bottom_x` in the anchors is the root), same value for `pivot` |
| Held, carried, sitting on something | `ref=(point in cell)`: that point lands on (x, y) and rotation pivots on it (§3) |

- `animi.py anchors` computes all cell anchors into json; `animi.load_anchors` reads them back.
- **One scale per sheet**, and **every sheet of a character the same size**: set `HERO_H` at the top and, per sheet, use the standing-straight cell (no crouch, no jump): `A.scale_ref(HERO_H, 'walk_0')`. Close shots also multiply by the shot's `k`. Fix supporting characters at their story size ratio. Render a still before and after a sheet change; the size must not jump.
- **A 2×2 close-up sheet also gets one scale**, from its standing-straight, most neutral cell, not per-cell boxes (raised ears or a tilted hat would make it pulse).
- If a character's sheets are drawn at different sizes and their standing poses differ: match sheets by an unchanging part (eye, button, chest pattern), measuring its area with `part_center`.
- Switching sheets (walk -> stop and act): the anchor must not jump and the poses must connect — pick a last cell and first cell with similar poses, or switch during fast motion. Render the two stills side by side: position, size, facing and held items must all match.

## 3. Hand-offs and contact: back-solve positions

Passing an object from A to B: fix one side and back-solve the other so the object stays put while it changes hands. If the object differs in size between the two drawings, scale one. Draw interacting things on the same sheet when possible. Traffic and queues: back-solve from entry position + speed × time and check minimum spacing.

**Point alignment**:
- Find points: `animi.cell_tip(a, (1, -0.6))` beak tip, `(1, 0)` reaching hand, `(0, -1)` raised hand; `animi.part_center(c, colour, round_only=True)` the fruit or lantern in hand (the shape test stops a same-coloured beak or scarf from being picked).
- Place: `place_at(frame, c, X, Y, s, ref=point, rot=angle)`: the point lands on (X, Y), rotation pivots on it. Riding on a back, a lantern on a hook, pinched in fingers, held in the mouth — all written this way.
- Back-solve: `animi.to_frame(ref, pt, X, Y, s, rot)` gives another cell point's position on frame. Hand-off: compute where A's hand point is and put B's point there. If both sheets draw the object at the swap, replace it for those 1–2 drawings with a separate prop image left in place, then switch to the "held in mouth" cell, back-solve the character's position and lean from "its drawn prop = in place", and straighten over a few drawings.
- A prop jumping between close-sheet cells (the same lamp off by tens of px over 4 cells): align each cell on the prop, not the character box: `refs = animi.part_refs(cells, lamp_colour)`, then `place_at(..., ref=refs[cell])`; if the prop is a base the character stands in and leans out of, use `anchor='base'`.

**Airborne**: slicing flattens the drawn height, so code supplies it: add `lift = height × sin(π·u)` to the ground y; the contact shadow shrinks and fades with `lift` (template `put(..., lift=)` does both).

**Standing on things** (a crate, a plank, a step, a friend's hands or back: anything other than the background floor). The sole is the anchor:
- Back-solve the foot from the surface: find the support's top face at the foot's x (on a slope, the slope line at that x) and put the foot anchor or a sole point (`ref=`) on it. The sole rests on the top face: not in front of it, not behind it, not sunk into it, not hovering.
- When the support moves (a crate tips, a plank slides, hands lift), recompute every drawing: the foot rides with the support, same shift and rotation, until the story makes it slip.
- Weight moves in steps: one foot lands and holds ≥ 2 drawings, then the body rises onto it; the body sits over the supporting foot. No gliding up, no rising before a foot has landed.
- Medium-close and closer, or when the support is a character or something soft: draw the weight-bearing poses with the support in the same cell (directing.md, "Characters in contact"), never two layers pushed together.
- Hands work the same way: a push, pull, grip or lean puts the hand on the object's edge (point alignment above).
- The contact shadow and `lift` start at the support's top face (the crate lid, the plank, following its slope), not at the floor's ground line.
- The support reacts: it dips or tilts when weight lands (directing.md §4, "The receiver reacts").
- A rigid body tipping over rotates about its contact corner; compute the end angle from the cell's alpha so it ends touching the ground, not hovering above it.
- Which support gets drawn: a static, flat support (a branch, a ledge in the background) can be an invisible support line in the sheet ("standing on an invisible horizontal branch, do not draw the branch") composited on the background's real one; a support that moves, tilts, is soft or is a character is drawn in the same cell.
- Something set down or planted leaves the character: from that drawing it is a separate prop at a fixed place in the scene, and later cells no longer draw it in the hand.

**Attached parts** (a key, hat, backpack, tool in hand, wheel, propeller, lid, a door on its hinge) belong to what they're attached to:
- Same mount point in every cell and every sheet: never floating, never changing side, never moving into another hand unless the story hands it over.
- A part turning about its own shaft: the prompt says what the camera sees at each angle ("full face → turned 45°, narrower → edge-on, a thin bar"). Abstract directions ("vertical → diagonal → horizontal") make the model spin it flat on the wrong axis.
- A part placed in code pivots on its mount point (`place_at(..., ref=mount, rot=…)`), never on its centre. Effects attached to a part (exhaust, flame, sparks) anchor at it and turn with it.
- Across sheets: a carried or worn part goes into `[character]` with the side it's on; later sheets take an already-correct sheet as a second reference. A hand holding a turning part turns with it.

**Check before slicing** every sheet with contact or an attached part, cell by cell: sole on the support, hand on the object, part at its mount and at the planned angle, no second copy. A miss is regenerated with the miss named in the prompt; code can't fix a foot drawn beside the crate.

## 3½. Shadows: one kind per style

Transparent assets carry no shadow (the templates forbid it). Code draws it from the style's `preset.shadow`, shadow first, then the character (one `animi.shadow(...)` line in the template's `put()`):

| `kind` | Look | Used for | Params |
|---|---|---|---|
| `contact` (default) | Soft ellipse under the feet, smaller and fainter with height | 3D puppets (clay, felt, cloth doll, crochet) | `contact` strength, `contact_w` width (× character width, default 0.9), `contact_off` offset (share of character width) |
| `relief` | Thin hugging shadow: silhouette offset a few px, blurred, darkened; farther and fainter off the paper | Flat styles (paper cut-out, clay relief, shadow puppets), default with `flags.top_down` | `k`, `off` (offset = min(cap, base + factor × size)), `blur`, `dir` |
| `cast` | Hard-light diagonal shadow: silhouette squashed at the ground line, thrown across the floor | Hard lamp or sun light (cardboard) | `light=(kx, ky)` (a point at height h falls kx·h right, ky·h back), `cast_k`, `cast_blur` |
| `none` | Nothing | Floating in water or sky | |

Direction follows the style's light (light from top-left, shadow to bottom-right). Pass `lift` when airborne; the shadow stays on the ground and fades. Per-element override: template `put(..., shade=dict(w=0.62, off=(0.06, 0), k=0.3))`; `shade=False` draws none.

## 4. Occlusion: doors, holes, behind tables

1. Separate the occluder's **front edge** (in front of the object) from its back edge; only the front edge goes in the occlusion layer.
2. Define an entry line: outside it the object is fully visible, inside it only within the opening.
3. Check sizes first: object top < opening height − safety margin; if not, change the composition — don't expect a mask to hide it.
4. Occlusion layer = original background × front-edge mask, pasted back after the object (`animi.holdout`). With camera motion, mask and background use the same transform.
5. Self-check: `animi.occ_overlay` paints the mask red over the background; `animi.sandwich_check` finds "visible -> thin occluding strip -> visible" slivers; render the drawings where the object crosses the entry line and zoom in.

**Standing behind a prop** (character behind a stove or table): draw the occluder polygon by hand in stage coordinates (include anything standing on it, e.g. flames) and, after the character, paste the original background back with `poly_mask`. Often easier than precise placement: pouring batter with the pan on the stove drawn in front of the character hides the bottom of the stream, so it reads as pouring into the pan.

**A held prop above an occluder** (pan held over a fire): character -> occluder pasted back -> the "prop only" cell placed again. Otherwise the flames jump in front of the prop when it lowers.

**Behind something in the background** (sun between leaves, moon behind clouds): `animi.color_mask(original background, sky colour or rule)` cuts out where the object may show (the sky); draw the object on a copy of the frame, then `animi.only_in(frame, copy, cam.plate(mask))` keeps only the part in the sky, so leaves and branches stay in front; check the mask with `occ_overlay` first.

Other: rising from behind a hill = paste the hill again after the object; a sandwich (passengers in a car) = car -> passengers -> car front wall again; characters at the same depth are drawn sorted by ground y.

## 5. Making it move

- **The time unit is the drawing** (`animi.Timesheet`; on twos 1 drawing = 2 frames). Camera, light and fx all step per drawing. No interpolation.
- Hold key poses: expressions 2–4 drawings, a blink 1; fast action changes every drawing. `holds` is in **frames** (on twos `holds=4` = 2 drawings), not drawings or seconds.
- **No stiff motion: pose to pose, fast in, slow settle.** For acting use `ts.act([(cell, drawings), …], total drawings, x=…)`: transition cells pass in 1–2 drawings, key poses hold 3–8, a reaction meant to be read holds 1–2 s, and the last entry written as 0 holds to the end (holds of 6+ drawings get `idle` automatically). **Never change cells evenly over time**: `cell = f'greet_{int(t * 2)}'` flips pages at a constant rate, every pose equally long — a slideshow, the stiffest result. The 8-action sheet itself must include transitions and overshoot (prompts.md "8-action sheet").
- **Settle on arrival** (`settle`): when a pose is held (same cell ≥ 3 consecutive drawings), the template's `put()` adds it to the hero: the arrival drawing sinks 3%, the next rebounds slightly, the third is steady (vertical, volume preserved, pivot at the feet, no sideways move); not for a pose already present when the shot starts, not for rigid materials. Amount is style.json `settle` (default 0.03, 0 = off). Write long holds with `times=` (the same cell over several drawings), not one long `holds=`, or it can't settle.
- **Weight follows the action**: leaning in, reaching, touching a ball with the nose, flinching back — shift the whole body a little that way: `x` as a one-way ease that stops on arrival (`x=lambda k: 860 + 30 * kit.ease(min(1, k / 6))`, 10–40 px), never back and forth. This is not swaying.
- **Live holds**: holding one drawing 1–2 s is fine; beyond 2 s something else in frame must move. Soft materials (clay, felt, cloth, yarn): `ts.add(..., idle=True)` gives per-drawing idle breathing ±1% (`sy`, volume preserved, no sideways move); rigid materials (wood, tin, cardboard, `preset.rigid = true`) get nothing from `idle`. Beyond that: small local motion (face-only variants: blink, open mouth, named like `close_1~b`; register even a single blink drawing as a `~b` variant so `repeat_report` doesn't see open ↔ blink as two alternating cells), moving co-stars and environment, a camera push.
- **No swaying while standing**: a standing character's foot `x` is fixed; it changes only when walking, running, pushed, or shifting weight one way. No `x = a + b·sin(…)`; play a reaction once and stop on its last drawing, never carousel it (`seq[i % len(seq)]` is swaying); no `rot` rocking. Align foot anchors on pose changes (floating or flying characters without feet: align on body centroid; placing by box centre makes them hop sideways). A `~b` variant must be a separately drawn face-only change (blink, open mouth), not the same image tilted or scaled.
- `Timesheet.lint` judges long holds by everything drawn: put a co-star into the cell name (`a+b`) or state `cells=[…]`; a rigid body moving on the same cell (rocket, prop) gets `@pos` in the name; a hold you reviewed and know is live (camera push, falling snow) gets state `live='reason'`. The template board re-checks by what was actually drawn.
- Reusing a sheet: offset phases, vary scale and blur for depth; if a loop looks mechanical, reorder (0,1,2,1,3,4,5,4,3,6,7).
- **No per-drawing jitter**: all styles have `jitter_pos`, `jitter_scale`, `jitter_rot` at 0 (like `flicker`). Cold, fear or strain in the story are not random per-drawing shakes either (`ts.jitter`, alternating offsets or angles): act them with the drawn pose and face-only `~b` variants; impacts, landings and a knob clicking home get one single one-way jolt (sink one drawing, back the next). Per-drawing wobble on a large frame reads as shaking and tires the eye; liveliness comes from the action, small local motion, soft-material idle breathing, the environment and the camera.
- Change cells during fast motion; a cell change while still is spotted at once.
- **Rigid bodies** (vehicles, props, furniture) only translate, rotate and scale, never warp. Wheels turn by a fixed step (less than half the symmetry angle). A tumbling prop = several views hard-cut every 4 frames + rotation.
- **Squash and stretch**: draw it in the poses; code `sx / sy` adds only ±4–7%, volume roughly preserved `sx = 1 / sy**0.5`; choose `pivot` per action.
- Damped swing: `amp × exp(−k/τ) × sin(ωk)`.

## 6. Camera and space

```python
cam, sh = animi.cam_at(SHOTS, pic, W, H)               # camera for this drawing (eased per drawing within the shot)
frame = cam.plate(D['plates'][sh['bg']], par=0.9)      # background framed from the original
x, y = cam.xy(stage_x, sh['ground'])                   # stage -> frame
s = sheet_scale * sh['k'] * cam.k() * ts.jscale(pic, STYLE['jitter_scale'])
animi.place_at(frame, cell, x + jx, y + jy, s, info=A[cell])
```

- Each shot's stage coordinates are **its own background's coordinates**; timesheet `x` is written per shot.
- A new shot size means a new background; within a shot only pan, and push no more than `push_max`.
- Parallax: far layer 0.25–0.3, mid 0.9, character 1.0, blurred nearest foreground 1.45–1.6 (scaled up + blurred). Soft shadows between layers, matching the style's light.

**Layered sets** (foreground paper waves, a row of trees, a table edge, grass in front of the character):
- Generate the set layer as its own transparent full-width strip (`layer` type, reference = the same scene's background; `[set_layers]` like "a full strip of foreground grass, the top edge uneven tufts"), and **leave the nearest foreground out of** the background (only a thin strip at the bottom), or two foregrounds stack.
- `layers.load_layer` reads it as premultiplied RGBA (trimmed, transparent padding on top: `cam.plate` clamps to edge pixels, so an opaque top row smears vertical streaks and short ends smear horizontal ones); `tile_layer` extends it, `taper_layer` tapers the ends for sweeps.
- Template SHOTS: `layers=[dict(name='front', par=1.35, x0=, y_top=, width=, front=True, bob=(6, 20))]`: `name` is a key of `layers` in `load()` (lint reports unloaded ones); `front=True` draws in front of the character; `bob` makes each layer rise and fall slowly (period 16–22 drawings, offset phases) — ready-made environment motion.
- `sy`, `dy`, `x0` may be `lambda k: …`, k = drawing index in the shot from 0. Paper layer standing up: `sy=lambda k: min(1, 1.1 * kit.ease_out(k / 8))` (subtract a little more to overshoot past 1 and settle); set layer sliding in: `x0=lambda k: -600 + 60 * min(k, 10)`.
- Whole set drifting (underwater current, wind): shot `sway=(px, period in drawings)` moves background, layers and character together (main horizontal swing + smaller vertical). Slow and small only: period ≥ 2 s (on twos ≥ 24 drawings), amplitude ≤ 4 px; fast drift reads as a shaking background. A violent current or wind is shown by bending plants, debris streams, the character being pushed. An impact jolt is timesheet state `shake=px` on the 1–2 impact drawings, decreasing, back to rest the next drawing (one way, no back-and-forth).
- Reuse one pair of set layers across the film; just change position and width per shot.

**Transitions**:
- Default is a hard cut. SHOTS `tr='<style transition id>'` uses the style package's params (style.json `transitions[i].kind / params`), or fill your own `tr=dict(kind='page', side='r')`; `mix=drawings` dissolves. Template `draw()` draws both shots, applies the transition, **then grades**, so transition material takes the grade and vignette and doesn't look pasted on the screen.
- Transition families (`animi.cut_fx`; the only place params are listed in full): `smear` material smeared over the screen (origin in/out direction, `edge='line'` straight edge, shadow direction, all from params); `page` page turn; `slide` paper layer sweep; `stitch` stitched wipe; `curtain` clumps of material surging up from the bottom; `wipe` soft wipe; `glow` bloom (`hold` = drawings held at peak, `mix=False` blooms without dissolving and hard-cuts at peak; brightness comes from bloom only, `lift` adds an overall lift); `mix` dissolve (`live=True` keeps the outgoing shot acting instead of freezing on its last drawing); `hinge` hinge flip (`hinge='lr'/'l'/'r'/'t'/'b'`: box lid closing, door opening, sign flipping — a board swings in on a frame-edge hinge, covers, swings out). The `shake` param shakes the whole frame during the transition.
- Assets (material close-up for smears, paper layer for slides, fx cells for curtains, stitches, hinge board): name them in params; template `load()` reads them via `animi.load_tr_assets` from `src/<name>.png` and sliced `work/cells/<name>.png`; lint reports missing ones.
- `smear=(before cut, full cover, after cut)` shorthand: direction, wobble and power come from the style's `kind: smear` transition.
- style.json `transitions` also records non-transition tricks (paper layer standing up, pushing into a field, a reveal hard cut): `kind: "move"`; do them in `build()` / `render()` per their `how`; pointing `tr=` at one warns that it is not a transition.
- Covering transitions (smear, curtain) hide the cut in the 1–2 fully covered drawings; page turns and wipes push the new frame in from the cut.
- Fade/wipe at the very start or end: `out=('dip_out', drawings)` / `inn=('wipe_l_in', drawings)` in `post()` (bookends don't use black transitions).

## 6½. Environment layers and small motion: never only one thing moving

All generated assets; code only handles position, angle and timing (`layers.py`):

- **Plants** (grass, seaweed, reeds, wheat): a prop sheet of clumps "with roots level, growing upward"; `layers.plants` swings them at the root, period 20–31 drawings per clump, 2–4°, offset phases; back rows small, dark, blurred, parallax 0.9; front rows large, blurred, parallax 1.25. A rigid rotation can't show "blown bent" in strong wind or current: generate half-bent and fully bent versions (straight one as reference, "roots still firmly in place, the upper half curving left in an arc"), `bent=[half, full]` switched by wind strength, thrashing at peak.
- **Particles**: fx-sheet cells (snow clumps, petals, leaves, confetti, bubbles, fireflies); `layers.Particles(mode='fall')` falls full-screen in three layers with wind drift; `mode='rise'` rises from vents. Particle sheet prompt: "8 fully opaque X, each a different size and shape, from pea to walnut size".
- **Small things in the background** (hanging foil stars, bulb strings, lit windows): `layers.find_glints` finds the drawn bright spots, `glints(mode='sway' | 'twinkle' | 'chase')` sways, twinkles or chases them, applied to the original background before `cam.plate`. Check with `glint_board` first.
- **Looping fx at points**: `layers.loop_fx` (star twinkle, distant splash, chimney smoke), offset phase per point.
- **Groups of small things** (fish school, birds, a line of ducks, fireflies): `layers.Flock(cell cycle, n)` computes each member's position per drawing — `ring` circles (near half in front of the hero), `scatter` startles apart (acceleration + motion blur), `queue` follows in line (offset phases, optional big leader); `layers.draw_flock(..., front=False)` draws far members before the hero, `front=True` near ones after.
- **Debris rushing along the ground** (threads in a flood, leaves in wind): `layers.Stream(debris cells, n=30, dir=-1).draw(frame, spr, cam, d, amount)`; mostly hugging the ground, near ones large, blurred, fast; exit and re-enter from the other side.
- For a dozen environment sprites drawn many times per frame use `layers.Sprites` (cached per scale step), far faster than `place_at` on whole cells.
- A group circling from in front of a character to behind must not switch layers mid-way (the switch drawing jumps): stay behind, or switch only where it doesn't overlap the character. Effects surrounding a character (puffing up, bursting) go behind it, only the outer ring visible, never over the face.

## 7. Scene light on characters, relighting (day ↔ night), state changes

**Grading characters to the scene light is compositing and allowed**; drawing effects in code (colour blobs, geometric lines faking water, smoke, sparks) is still not. Generated transparent assets are flat-lit (the style anchor's lighting only takes on backgrounds), so pasted straight into night or dark scenes they look like stickers. The style package puts params in `preset.light`; compositing is one line:

```python
put(frame, D, cam, name, x, y, s, pic, ts, sh=sh, light=dict(warm=0.6, warm_side='left'))   # template: applies preset.light
# equivalent: c = animi.char_light(cel[name], STYLE['light'], scale=close_factor, warm=0.6)  # decontam -> tinted exposure -> side -> warm -> rim
#             animi.place_at(frame, c, X, Y, s, info=info, gain=animi.floor_light(plate, gy, cam, STYLE['light']))   # with light.floor: darker outside the light
```

- `decontam`: edge decontamination (semi-transparent fringes keep the generator's background colour and show a grey halo on dark scenes); on for every fuzzy-edged material.
- `tint` / `expo` / `gamma`: darken and shift to the scene's colour temperature (night cool blue, oil lamp warm). `side`: left/right multipliers (where the light comes from).
- `rim` / `rim_col` / `rim_dir`: rim light, the signature of fuzzy materials. Close-up sheets are several times larger than 8-action sheets, so pass `scale` for consistent rim width: the template's `put()` uses "reference sheet sc / this sheet sc" (a close-up sheet's sc is set from its size in the wide, times the shot's k); if wrong, set `lscale={'close': 2.2}` in `load()`.
- `warm`: the side lit by a lantern or fire. For mirrored cells pass `flip=True`; light direction follows the mirrored frame. Side light **drawn into** the image flips with the mirror, so mirror only cells lit from the top or front. Mirroring also needs a design check: held prop, accessory side and markings switch sides; if that breaks continuity, generate a sheet facing the other way. Each style says in its Compositing section whether mirroring is allowed.
- **Everything gets the scene light, not only the hero**: in styles with `preset.light`, `dark`, `light_pool` or `floor_light`, side characters, props, effects and dust go through the same light by the same position rule; all cast and contact shadows fall one way for the whole film.
- `floor_light`: measures the light zone along the ground line from the background itself and multiplies each character column by position (zone edge `floor.lo`, `floor.gamma`); `light_pool`: a light pool (flashlight, spotlight, iris closing), background and character multiplied by the same map. When closing the pool, centre it on the light-source side and keep the hero lit; lamps don't flicker either (it makes the frame flicker).
- **Darken the whole scene** (lights out, clouds): SHOTS `dark=0.6` (or `dict(k=, tint=)`); the template darkens background and characters together at the end of `render()` (`animi.darken`, cool bias); to brighten back, ease k to 1 per drawing.
- **Additive warm light** (lantern, candle, window, firefly): `animi.warm_glow(frame, X, Y, r, k)` adds a Gaussian warm glow + faint halo at the source, after darkening (not darkened); find the source with `part_center` on the lamp and map with `to_frame`. No flame flicker.
- **Self-lit effects** (flame, wick, magic light): `animi.self_glow(frame, cell, X, Y, s)` brightens it as self-lit and adds a shape-following halo. Flames and candles may animate, but **never pulse the whole background or a large light area per drawing** (summed `sin` light swells, a wick jump multiplying the frame brighter read as a shaking background): a lamp turning on or dimming is a one-time change; chases and twinkles only touch individual small spots; afterwards adjacent drawings must differ by under 1 grey level in overall brightness.
- **Light spreading** (turning a lamp up, dawn): `animi.light_flood(cam, dim, bright, src_x, src_y, R)` grows the bright version in a circle (R from small to full per drawing); the returned `mix` goes to the character: `gain=animi.floor_light(dim, gy, cam, LIGHT, plate2=bright, mix=mix)`.
- However dark, hero and action must stay visible (`dark_spans` checks).

**Relighting**: generate two backgrounds (the second with the first as reference, "exactly the same picture, only the lighting changes"); don't crossfade the whole image (the relit version often adds things): blend with a gradient from the light's side, or grow outward from the source (lamp on, sunrise), and blend character brightness by the same ratio. State changes (apple fallen, door open) likewise: switch between two backgrounds, never overlay a copy of the object.

## 7½. Containers: prop view and "inside"

Pots, bowls, baskets, cups, boat holds, pockets — any "one thing inside another" scene follows this section; examples use a pan and a pancake.

- **The prop's view matches the camera**: decide where the camera is first. Stop-motion cameras sit mostly at chest-to-eye height of the character, a bit above props on a table or in hand, so a container's opening is a very flat ellipse: the back rim and a little of the inside visible. A container drawn from above (whole bottom visible) looks fake at once; fully level with no inside visible can't hold anything. State size in the prompt ("pan about as wide as the body").
- **What makes "inside" read**: **the back rim shows behind the item, the front rim covers its front edge**. With only a front rim, the item looks behind or on top of the container. When unsure, generate a "how would this look shot for real" reference — faster than tuning by feel.
- **Method**: opening visible (above), inside in a high-contrast colour (dark grey pan coating). Four functions:
  ```python
  inner = animi.inner_mask(pan_body, coating_colour)                    # the inside
  full = animi.fill_container(pan_body, inner, pancake, fill=0.9)       # item squashed to the rim ellipse, drawn only inside (cache it)
  rim = animi.rim_to_frame(animi.prop_spot(pose_cell, pan_colour)['rim'], ref, X, Y, s, rot)   # where the held pan's rim is on frame
  animi.put_by_rim(frame, full, animi.prop_spot(pan_body, pan_colour)['rim'], rim)             # place onto the held pan
  ```
  The front rim covers the item's front edge naturally.
- **Container drawn flat in the action sheet, no inside visible**: generate a separate "slightly high angle, empty container body without handle" as the `pan_body` above; keep handle and hand from the pose drawing. Fit the replacement's width and angle to that cell's rim, align bottoms, gain-match colour to the median of the original container colour. Replace it in every shot that holds it, empty or not, so it stays consistent.
- **Which size wins**: inside the container, **the container as drawn in this cell** (measured rim width × ratio), so the item fits however big the container is drawn; outside it (flying, landed elsewhere), **one film-wide size** (median container width across action sheets), not shrinking with one small drawing. Use the same ratio for both so sizes connect when it leaves the container.
- **Look at measurements before using them**: `animi.spot_board(...)` overlays detected rims and masks on the cells. Common errors: the darker back-lit half of the container isn't detected (mask has a hole, can't cover the item); a tilted container's handle stub near the body reads as "thick" and counts as body (rim too long, centre pulled to the handle). Judge colour by hue, not just brightness; `prop_spot(body=)` is the thickness threshold for body. Widths differing wildly within one sheet (30%+) usually mean misdetection, not a changed container.
- **Container not level** (raised, a plate tilted toward camera): fit an ellipse to the container colour blob (`cv2.fitEllipse`) and squash/rotate the item by its axes and angle; if the colour threshold misses parts, restrict the search to the container's region.
- **Items lying on a table** (a pancake fallen on the counter): generate a level "lying flat" version plus a contact shadow; don't squash a top view (looks like a crumpled leaf).
- Prop drawn the wrong size: regenerate the action sheet. Enlarging in code (scale around the grip, paste back) is only a stopgap; a wrong-view prop looks worse enlarged.

## 8. Effects and text

- **Effects are always generated**: an 8-cell fx sheet in the style's material, sliced, cells switched per drawing; code only handles position, scale and timing. Edges must stay clean after rotation or scaling (RGBA is already feathered; don't hard-cut again).
- Trails and exhaust anchor at the nozzle or tail, not the body centre.
- Subtitles come from `sound.py build`, burned in by the template. Bright or busy frames behind the subtitles (patterned cloth, yarn, white foam) must have a backing plate: style.json `subtitle.plate = {"color": [..], "alpha": 0.55}`. Subtitles are always at the bottom, never moved up; in shots with narration keep characters out of the subtitle band (bottom ~12%): place roads and tabletops higher or tilt the camera down a bit. Bilingual subtitles (narration with a second-language line) are laid out automatically as two lines on one plate, no wrapping; don't build your own bilingual subtitles.
- **Titles, end cards and subtitles use only Source Han Sans (思源黑体) Bold in flat colour.** No texture on strokes (cloth, paper, fuzz, stitching, misregistration, per-glyph colours, engraving): complex characters turn to mush. Style goes on the plate behind the text (`bookends.title_tag`; plate colour, scissor-cut polygon / rounded / stitched dashes, solid `border`, texture from style.json `title.plate`; a subtitle on its own coloured strip via `title_tag(..., sub='subtitle')`, look from `title.sub`). **Textures are material close-ups only** (the style's `ref/texture.jpg`, a `texture`-type image generated for the film; falls back to the style package if the film folder has none) or procedural `proc:knit` stitches / `proc:wood` grain / `proc:weave` cloth / `proc:paper` fibres; never a background image (waves, stars, houses get printed into the plate). A missing texture is reported (lint missing image). Minimum sizes (1080 short side): title ≥ 200 px, subtitle ≥ 60 px, credit ≥ 48 px; cards land on integer pixels, unrotated (stop-motion offsets also whole pixels); Latin text set as whole lines, no letter-spacing stretch. Before delivery grab a full-size frame and zoom into the most complex glyph. The title plate sits over sky or empty set, never over a character's face or the hero's entrance: check the middle frame of the title card and move the plate or the characters if it covers them.
- No bookends by default; add them only when the user asks, with `bookends.py` (title card + end card, credit in the user's wording). All styles share one motion; the look comes from `style.json` `title` (workflow.md §7). Don't build your own title cards in a film; a new style package must fill `title` completely (text colour, plate, `motion`). Small in-scene signs use `fx.text` / `fx.put`; never let image generation draw text.

## 9. Grade last

After everything is placed and transitions are done, run `animi.finish(frame, ts, pic, STYLE)` on the whole frame: tilt-shift, `kit.grade` (tone, bloom, vignette), params all in the style's `style.json`. **No whole-frame brightness flicker and no film grain** (all styles have `flicker`, `grain` at 0): the background is a still image, and anything changing per drawing on a large static area reads as flicker; stop-motion's handmade feel comes from material texture and on-twos motion, not per-drawing wobble. Pass `glow=0–1` for glow transitions and a lamp turning on. Subtitles and fade/wipes come after finish (template `post()`). Colour changes over time (evening -> night): multiply the relevant layers before finish.
