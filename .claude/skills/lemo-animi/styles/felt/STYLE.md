# Needle-felt stop-motion (felt)

**In one line**: small animals and snowscapes in needle-felted wool; fuzzy, quiet, warm; one warm lamp in a cold blue night.

## Best for

- **Subject**: winter nights, snowfields, a cabin in the woods, the eve of a holiday. A small animal quietly does something kind for someone. Smoothest structure: **give the warm thing away → be left in the cold → the other one comes back bringing light**; warm and cool colour is itself the emotional line.
- **Palette**: large areas of cold blue, snow white, pale grey; warm red and warm yellow only in one or two spots (scarf, window light, lantern).
- **Light**: night. Cold blue moonlight from back right rims the fuzzy edges; warm yellow lamps as local fill.
- **Camera**: low, close to the snow, shallow depth of field, a blurred felt snowdrift or berry branch in the foreground.

Not for: fast slapstick or big squash-and-stretch comedy; busy scenes in bright daylight; hard shiny materials (metal, glass, water) as the lead; lots of smoke or translucent effects.

## Signature moves

- **Fuzzy rim light**: the ring of fuzz facing the light glows cold blue and pops the character off the dark blue background. Best in shots with a dark background and a bright character. Code does it by relighting through alpha (see Compositing).
- **Warm/cool colour line**: whoever holds the lamp is warm. Generate two backgrounds from one camera position (a "no light source" version and a "lighting changed only" version) and blend them with the story; the character follows the light: `put(..., light=dict(warm=…, warm_side=…))` warms the side facing the lamp.
- **Sharing the warm thing**: the landing is two characters sharing one scarf or one lamp, drawn together in one sheet (directing.md §6, characters in contact).
- **Soft materials lag a beat**: scarves, long ears, a carried lantern swing up and settle a beat after the body; draw it in the sheets.
- **Full-screen snowfall**: an fx sheet of 8 wool snow puffs of different sizes, used as particles with `layers.Particles(mode='fall')`; heavy snow `amount` 1.4–1.6, `wind` 3–4.
- **Wool smear**: a big mass of white wool presses down from the top and covers the lens, then peels away downward, like snow burying the lens. Once per film, at a section break like "time passes, the snow gets heavier".

## Compositing

- **Character relight** (`preset.light`): always relight felt characters; flat light pasted into a night scene is "white studio light" and looks like a sticker. Defringe 6 px (semi-transparent fuzz holds the generator's grey-blue background) → darken and cool (0.80, 0.86, 1.0) × 0.90 → cold blue rim light from top right 0.55. 2×2 medium-close cells are about 2.2× the size of 8-cell sheet cells, so relight `scale` must be 2.2 for an equal rim width: the template's `put()` derives it from the ratio of the two sheets' `sc`; when the medium-close-up sheet's `sc` wasn't set from the wide size, write `lscale={'close_tt': 2.2}` in `load()`. Warm light `warm` 0.3–1, side = where the lamp is (carried in front `bottom`, held in the arms `all`).
- **Shadow**: `contact`, 0.38; `lift` when airborne makes it smaller and fainter.
- **Rigid**: no (idle breathing ±1.2%).
- **Transitions**: `wool_smear` (`kind: smear`, in from the top, out at the bottom, asset `fx_smear_tex`), `tr='wool_smear'` in SHOTS. `lamp_glow` (`kind: glow`): the previous shot pushes toward a warm lamp and the scene changes at peak bloom.
- **Title plate**: cream rounded felt plate with warm red stitches (`stitch`), deep blue text; texture from the wool close-up used for the smear, plain plate if that image doesn't exist.
- **Smear asset** `src/fx_smear_tex.png`: built with the `texture` type (`animi.py prompt felt texture`, `[material]` carrying this meaning): "a landscape 16:9 macro close-up: one whole sheet of fluffy white wool pressed against a pane of glass, filling the entire frame, wool on all four edges and corners, no gaps or background showing; individual fine fibres and fluffy tufts visible, cold blue moonlight. Only wool in the frame".

## Pitfalls

- **A shot meant to be fully dark shows a cabin with lit windows or a street lamp** → name everything unwanted in `[scene]`: "no houses, windows, lanterns, street lamps, stars or moon; nothing lit and no warm light, only cold blue night".
- **The relit background adds things** (a distant house with lit windows) → make the first version "no light source"; the second takes the first as reference with "exactly the same picture, only the lighting changes: warm yellow light from a small unseen lamp to the left (do not draw the lamp itself)", so compositions align. Blend only from the side the light comes from (light from the left: blend in about the left 60%), never fade in the whole frame, so extra objects don't pop up.
- **2×2 medium-close-up sheet changes size cell to cell** (the droopy-ears cell is much shorter; per-cell box scaling enlarges it) → one scale for the whole sheet, set by the tallest cell.
- **A medium-close needs the opposite facing; mirroring the whole sheet moves the drawn-in side light to the other side** → regenerate with the needed facing (`[framing]` "three-quarter view facing left", `[performance]` "the left side of the face lit by warm yellow light from the left"), don't mirror. If mirroring is unavoidable, write the code's warm light for the mirrored image (`flip=True`).
- **White rabbit on white snow blurs into one** → keep one or two dark spots on the character (ear tips, inner ears, scarf); ground snow is a darker grey-blue.
- **Snow, smoke, breath come out as semi-transparent haze that won't cut out** → write "tufts of completely opaque wool".
- **All-over cold blue feels stuffy** → at least one warm spot in every shot.
- **Felt puppets can't do a big mouth** → act with eyes, ears and body; don't write "mouth wide open".
- **`check` reports opaque edges on a close-up sheet showing only face and shoulders** → `--allow-edge`, no regeneration.

## Sound

- **Score**: winter-night lullaby. Harp arpeggios underneath, flute on melody, long double-bass notes; at the climax add glockenspiel and sleigh bells. Slow (72–90), lots of reverb, lots of space.
- **Foley**: steps in snow `crunch` / `step` (small ones pitch 1.15–1.45, v 0.3–0.35), soft "poof" `puff`, wool rubbing `rub`, lantern set down `tap`; the smear gets `whoosh` (v 0.55, pitch 0.8) + `thud` (v 0.4, pitch 0.8); lamp lighting, bloom `sparkle`.
- **Narration** (optional): gentle, like a bedtime story, short sentences, a pause between each.

## Reference images (`ref/`)

- `character.png`: little white rabbit character sheet, clean fuzzy edges, dark accents on ears and scarf
- `sheet8.png`: two characters sharing one scarf, carrying a lamp, walking side by side; 8 cells, 8 subjects
- `sheet4.png`: 2×2 medium-close-up sheet with both characters in each cell (raise the lamp → smile → wrap the scarf → cheek to cheek)
- `bg_wide.jpg`: wide, felt cabin with lit windows on a snowy night
- `bg_mid.jpg`: medium, old tree hollow warmed by an unseen lamp (relit version)
- `bg_close.jpg`: medium-close, shallow depth of field, berry branch in front, street lamp and cabin far off
- `prop.png`: felt lantern, one carried and one set on the ground
- `fx.png`: 8 opaque wool snow puffs from small to large (snowfall particles)
