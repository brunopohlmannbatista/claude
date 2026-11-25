# Papercraft stop-motion (papercraft)

**In one line**: a cut, carved and folded paper lightbox, layers set one behind another, glowing in backlight; quiet and dreamy.

## Best for

- **Subject**: fairy tales, bedtime stories. A small character travels through layered sets (night sea, forest, starry sky) and meets something far bigger (a whale, the moon, a great tree).
- **Palette**: graded cool tones of one family (deep blue, indigo, teal), lighter far, darker near; focal points in cream and warm yellow (moon, sail, lamp).
- **Light**: backlight; every paper edge glows, clear shadows between layers; lamps in frame are warm light sources.
- **Camera**: front, eye level, paper layers parallel to the frame; parallax comes from lateral moves within the shot. A new view comes not from turning the camera but from moving the light source (moon left / right / off-screen with only a corner of moonlight), raising or lowering the horizon, or going underwater or into the sky.

Not for: fast slapstick, scenes that orbit a character, fine deformation of cloth, fur or water.

## Signature moves

- **Multi-layer parallax** (signature): back `bg` (opaque: sky, moon, distance; parallax 0.85, `preset.par`) → character (1.0) → mid paper layer (a full-width transparent strip, 1.0–1.05; covers the lower half of a vehicle and the unseen body of a big thing) → front paper layer (1.3–1.4, along the bottom edge). Generate the mid and front strips once each as type `layer` and reuse them all film (with the wide bg as reference so paper and colour match); read them in `load()` with `layers.load_layer`, use `tile_layer` if too narrow. For a landscape shot, copy this line into SHOTS and adjust positions:
  `layers=[dict(name='mid', par=1.0, x0=-W*0.55, y_top=H*0.735, width=W*2.6, bob=(4, 22), phase=2.0), dict(name='front', par=1.4, x0=-W*0.7, y_top=H*0.865, width=W*2.8, front=True, bob=(6, 18))]`
  Each layer's own `bob` (amplitude 4–7 px, period 16–22 drawings, phases offset) is ready-made ambient motion.
- **Layers pop up** (`pop_up` in `transitions`, not a real transition): in the opening shot the set layers stand up one by one, hinged on their bottom edge. The first frame already shows layers at 15%, never black. Make that layer's `sy` in SHOTS a function of the in-shot drawing number k (from 0), each layer starting 3 drawings later:
  ```python
  pop = lambda q: (lambda k: min(1.0, max(0.15, 1.1 * kit.ease_out((k - q) / 8))))   # from drawing q, full height in 8 drawings; 15% before that
  layers=[dict(name='mid', ..., sy=pop(0)), dict(name='front', ..., front=True, sy=pop(3))]
  ```
  Only in the opening shot; leave `sy` out elsewhere (= 1).
- **Layer slide** (`layer_slide`, `cut_fx` `slide`) and **glow mix** (`glow_mix`, `glow`): usage and parameters are in `transitions` in style.json.
- **Lamps are light sources**: lanterns, candles, fireflies use `animi.warm_glow(frame, x, y, r, k=0.3)` (core and halo included), called at the end of the template's `render()`, after `darken`; strength constant across drawings. Lamp position: `animi.part_center(cell, lamp colour)` finds the lamp (returns centre and box); feed the `ref`, position, scale and angle you used in `place_at(ref=…)` to `animi.to_frame` to map it to the frame; radius `√(box width × height) × s × 1.1`.
- **"The lamp goes out" darkens the whole scene**: no separate dark background; write `dark=0.55–0.62` in SHOTS (the template's `render()` already applies `animi.darken`, cool by default). The character darkens too; lamp glow is added after darkening. Lamp back on: in `render()` ease k from 0.6 to 1 per drawing (about 8 drawings) and call `animi.darken`.
- **Small life in the sky**: stars painted in the background: `layers.find_glints(bg, rule='bright')` finds them, save a `glint_board` to check, then `layers.loop_fx` plays the star fx sheet on those points with offset phases.

## Compositing

- **Hero size**: when the character sits in a boat or car, measure hero height **including the vehicle** (`HERO_H` and `scale_ref` by "character + vehicle"), no relaxing (`hero_min_scale` 1.0). The bigness of "small character meets big thing" comes from showing only part of the big thing: in a wide, a small far-off patch of back or a corner of moon; in medium and medium-close, a back, an eye, a piece of tail. Never fit the whole thing in frame.
- **Character in a vehicle**: `put(..., anchor='base')` (midpoint of the bottom band); when you need to back-compute the lamp position, place with `place_at(ref=boat-bottom point)` instead. Set the ground line low so the mid paper layer covers the lower half of the vehicle (a fully visible vehicle bottom floats).
- **Character relight**: none (`preset.light` empty). Paper puppets are light warm paper and already pop against cool night scenes.
- **Shadow**: `contact`. Characters and props standing on paper ground need contact shadows or they look pasted on; films that float on water or fly use `none`. Set layers have their own soft shadow (`put_layer` `shadow` 0.38).
- **Rigid**: `rigid`; no squash, no small turns or wobble; `~b` variant cells change only the face (blink, open mouth).
- **Transitions**: `layer_slide` = `slide` (a full-screen front paper layer sweeps across: a big wave at sea, a drift of leaves in a forest; the cut hides in the fully covered drawings); `glow_mix` = `glow` (brighten overall then mix, no bloom); `pop_up` is not a transition, see "Layers pop up".
- **Title plate**: `cut`, cream card plate, deep indigo text, shadow offset 8 px.

## Pitfalls

- **Paper puppet drawn round and 3D** → describe the character as "flat paper pieces, folds, cut edges"; paper is stiff, motion comes from turning and folding, no squash and stretch.
- **Vehicle differs between sheets** (mast left in one, right in another; cuts give it away) → put the vehicle in `[character]`; `[action]` states which side behind the character upright parts are; later sheets take an already-correct action sheet as second reference.
- **Big side character unrecognisable** → keep its most recognisable part (the eye) in frame at every shot size, or a medium is just a big body. A medium-close "cropped inside the cell" (face only) has a straight cut edge; put that edge outside the frame when compositing.
- **Background already has a full foreground near the lens; adding the front paper layer doubles it** → keep only a very thin strip at the bottom edge of the bg's foreground (`prompts/bg.txt` covers it).
- **Layer's top row or ends are opaque; sliding pulls vertical or horizontal streaks** → `layers.load_layer` (trim edges, premultiply, pad transparent top); trim the ends of the transition wave with `taper_layer`, or it looks like a wall.
- **Transition wave comes out as a thin strip and blurs when scaled** → generate it taller per `how` in `layer_slide` (height at least half the width); keep the fully covered time short.
- **Character swallowed by the cool night** → light-coloured paper for the character, darken layers behind it (`mul` in `layers`); the backlit rim is the outline, the cut-out must not remove it.
- **Pushing in too far blurs and exposes the layering** → push ≤ `push_max` (1.1); for a new shot size generate a new background.

## Sound

- **Score**: soft handbells on melody, glass harp arpeggios, long cello notes, ocarina answering phrases, Nepalese hand bells; slow, lots of reverb. Hits: glass harp glissando, timpani + suspended cymbal. Even the lowest level keeps the cello drone, so it never drops out.
- **Foley**: paper flutter `flap`, rustle `rustle`, soft landing `tap`, scene change `whoosh`; water `drip` `splash` `flow` `bubble`. Deep undersea rumble: `rustle` pitched down (pitch 0.45).
- **Narration** (optional): gentle bedtime story, short sentences, generous pauses.

## Reference images (`ref/`)

`character.png` origami fox character sheet · `sheet8.png` 8 cells sitting in a boat, holding up a lamp, looking around · `sheet4.png` 2×2 medium-close: holding the lamp / hugging the tail · `bg_wide.jpg` wide of moonlit paper waves · `bg_mid.jpg` medium, low camera, moon moved to the right · `bg_close.jpg` medium-close of night sky, tilted up, moon off-screen · `prop.png` origami whale (eyes open / closed) · `layer.png` transparent mid paper-wave layer · `fx.png` paper splash in 8 stages
