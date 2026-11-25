# Wooden puppet stop-motion (wood)

**In one line**: varnished, carved jointed wooden puppets coming alive joint by joint under one oil lamp late at night.

## Best for

- **Subject**: a workshop at night, an attic, old toys coming alive; maker and creation, standing up for the first time, quiet companionship. The easiest structure is **the light is the plot**: wake in the light → step out, get scared back by the dark → the light shrinks (crisis) → make the light grow → the light reveals something new (payoff). Plant the setup in the dark of the first wide shot (another puppet lying at the far end of the bench, only a shadow).
- **Palette**: honey, walnut, dark brown, a touch of brass; nothing bright, the background sinks into the dark.
- **Light**: one oil lamp low on the left; an oval pool of light on the bench that falls off fast; small highlights on the varnish, wood grain still readable in the dark.
- **Camera**: low, at bench level, lens at the puppet's chest height, shallow depth of field, foreground shavings blurred; the hero stands in the lamp's pool.

Not for: bright outdoors, busy crowd scenes, comedy built on soft deformation and big expressions, soft things (water, fire, cloth) as the hero.

## Signature moves

- **The light pool leads**: most of the frame is dark and the eye follows the light. Leaving the pool = danger, loneliness; returning = safety. Eyelines follow the light too (wake and look at the lamp, startled and look back at it, look at it together at the payoff). Characters light up wherever they walk, done in compositing (see Compositing).
- **Jointed puppet motion**: parts only rotate on their wooden pins; the body is rigid. Fast moments on ones; quiet moments on twos with longer holds, like testing the joints. Show unsteadiness with leaning cells in the drawings (lean and hold), never code wobble. A fall onto the bottom is one one-way jolt (that drawing drops a few px, the next returns) plus `thud`, no shaking.
- **Lifeless puppets can move too**: rotate a slumped puppet rigidly about the bottom-right corner of its box (`place_at(pivot=1.0, rot=…)`): slowly tip, fall with a thump (a seated L-shaped puppet needs about 97° for the head to touch the bench; 80° leaves it in mid-air; compute the angle from alpha so it touches), lie a moment, then spring back to sitting click by click (2–3 drawings per click, slight overshoot), shadow following the body. No new images needed, and the opening stillness becomes the first sign of life.
- **The lamp is a character**: its mood comes from the flame fx sheet (wick lowering = each flame smaller) and the size of the pool (pool shrinking, light spreading), **never whole-frame brightness jumps**.
- **Payoff: the light grows**: generate dark and bright versions of the same wide shot from the same camera; after the lamp is turned up, the bright version spreads out ring by ring from the lamp, revealing what was hidden in the dark (transition `lamp_flood`).

## Compositing

- **Character lighting** (`preset.light`, always on): transparent assets are flat front-lit and look like stickers in a dark set, so all light and shade comes from compositing. `char_light`: `gamma` 1.12 plus a little contrast → warm tint (1.08, 0.93, 0.74) → side light left ×1.28, right ×0.43 → warm rim light on the left 0.55; edges are clean, no edge decontamination. **Leaving the pool**: when the template's `put()` sees `light.floor` it chains `animi.floor_light` (pass the shot's `sh=`), which measures brightness along the background's own ground line and scales each character column by position (`floor.lo` 0.16 = what is left fully in the dark, `floor.gamma` 1.8 = how steep the pool edge is). It lines up with the background's pool by construction; no hand-drawn pool.
- **Close-up sheets** skip the pool curve: one brightness per cell (0.8–1.05 to match the shot), side light [1.2, 0.5]: `put(..., light=dict(floor=False, side=[1.2, 0.5], gain=…))`.
- **Pool shrinking**: `animi.light_pool(cam, cx, cy, r, lo=0.32, sq=0.55)`; multiply background and characters by the same map, radius shrinking per drawing. Centre it **on the lamp's side** (lamp off-frame → at the frame edge) so a hero running toward the lamp gets brighter. Keep about 0.3 outside; at 0.22 a hero near the edge is nearly black.
- **Light spreading**: blend the dark and bright wide shots by distance from the lamp: `m = clip(1 - (d - R) / 260, 0, 1)`, `d` = distance to the lamp in stage coordinates (vertical ×1.6, the pool on the bench is flat), `R` grows from 200 to 2100 over about 20 drawings. Blend the characters' pool curve between the two versions with the same `m`, and **normalise both versions to the dark version's pool centre** (normalising each separately leaves characters no brighter after the lamp is turned up). No whole-frame fade: the bright version often has extra things drawn in.
- **Flame**: step the fx sheet per drawing, one scale for the whole sheet (from the largest flame); brighten about 1.5× as self-lit, then add a warm glow (1.0, 0.62, 0.25) by blurring the flame's alpha (~40 px); the glow shrinks with the flame.
- **Supporting-character wood tone**: light-wood supporting characters often come out as dark as the hero on the action sheet; restore brightness per the character sheet (`put(..., light=dict(gain=1.35))`).
- **Shadows**: `contact` shadow 0.45, `lift` when airborne; in the dark the shadow is invisible anyway, no extra darkening.
- **Rigid material** (`preset.rigid`): yes. No idle breathing, no small turns or sways; long holds rely on small local moves, the environment and the camera. Wood never squashes or stretches: no `sx/sy` anywhere.
- **Transitions**: hard cut by default. Into a lamp close-up use an **eyeline cut** (hero looks up at the lamp → close-up of the lamp, already facing it). `panel_slide` (`kind: slide`): a varnished wooden panel passes close in front of the lens and hides the cut; fits any story (asset in style.json). `lamp_flood` (`kind: glow`) only for the moment the light grows, with `sparkle`; a 6-drawing dissolve is fine before the payoff. Never push the camera into solid black and cut there (both sides of the cut end up nearly black).
- **Title plate**: a honey-coloured rectangular wooden board, dark walnut lettering, `knock` as it drops.

## Pitfalls

- **Generated characters are studio flat-lit, not low-left lit** → don't expect the anchor's strong chiaroscuro to appear in assets; always use `char_light` + `floor_light` (see Compositing).
- **Mirrored assets put the bright side on the right** → the light is fixed on the left: lamp on the left of the background, no asset is ever mirrored; to face the other way generate another sheet (`[action]`: "first 3 cells face right, last 5 turn to face left").
- **Hero or action unreadable in the dark** → darkness is fine, but the hero and any action to be read must be in the light or at the pool's edge; shrink the pool toward the lamp. `selfcheck.py`'s too-dark check (`preset.dark`: frame 0.03, hero 0.06) applies as usual; fix whatever it reports.
- **A prop built into the set (lamp knob, door handle, switch) doesn't match between close-up and wide** → use the background containing that prop as reference for the close-up background; `[scene]`: "it is the small oil lamp from the reference image (the same lamp: same A, B, C), now seen very close", and say how it connects ("at the right end of the brass neck a small round hole facing right, ringed by a brass collar; do not draw the knob").
- **A prop drawn in a close-up sheet jumps tens of px between the 4 cells** → measure the prop edge in each cell in code and shift the whole cell to align; fade the protruding shaft end by alpha (~14 px) into the set's collar; zoom so the collar sits at the character's hand height. When the prop is attached to the set, don't rigid-sway that character cell.
- **`check` counts 5–6 subjects on a 2×2 close-up sheet of two characters, or character plus prop** → if every cell looks right on the preview, slice with `--group grid`. A face-and-shoulders sheet that fails the edge-transparency test → `--allow-edge bottom`.
- **Background generated too dark, crushed to black by grading** → grading already darkens and adds contrast; dark areas of the background must keep wood grain (already in the template).
- **The light pool lands in the wrong place** → give the lamp and pool exact positions in `[scene]`: "a small oil lamp at the far left (taking only the left fifth of the frame) … casting an oval pool of light on the bench, centred one third from the left edge, about a third of the frame wide, falling off quickly from the centre"; it follows the stated position.
- **Relit background versions don't line up** → generate the bright version with the dark one as reference: "exactly the same workbench, oil lamp, tools and shavings in the same places; change only the light: the wick has been turned up, the flame is twice as tall; warm yellow light covers most of the bench … the wall and tool rack stay dark".
- **Hero too small in the wide** → put the hero in the centre of the pool.
- **Puppet expressions won't render** → swap only carved mouth shapes and eyelids: eyes closed "the two eyeballs replaced by two carved curved lines", effort "mouth replaced by a tight straight line", curious "mouth replaced by a small O", smiling "mouth replaced by a curved smile".
- **Sawdust kicked up by a fall hides the body** → draw the dust behind the character, scaled to 1.3× body height, spreading out on both sides; the dust also gets the local light and warm tint.
- **`shots_lint` flags two different backgrounds as near-identical framing** → the whole style is "dark ground + one warm pool", so grey levels naturally match; check the cut frames for a change of shot size or subject, then set `cut_ok`.

## Sound

- **Score**: oboe carries the slow melody, marimba (wooden) answers behind it, harp arpeggios, pizzicato cello, a woodblock ticking like a pendulum. Handbell arpeggio (`wake`) for waking and standing up, log drum (`thud`) on hits, `sparkle` as the light spreads. When the hero leaves the pool or the lamp sinks, energy drops to its lowest (harp arpeggio only).
- **Foley**: steps `step` (small characters pitch 1.2–1.5), joints `click`, wood on wood `knock`, light touch `tap`, falls and landings `thud`, turning a knob `ratchet`, wood creak `creak` (d seconds); `sparkle` as the light rises. All hard and short; joint sounds follow the cells, written into `foley_rules`.
- **Narration** (optional): warm, like a bedtime story told at the bedside; short sentences, a pause before key words.

## Reference images (`ref/`)

- `character.png`: jointed wooden bear character sheet; pins, knife marks and walnut muzzle clear, clean edges
- `sheet8.png`: walks to the pool's edge and is scared back; first 3 cells face right, last 5 turn to face left
- `sheet4.png`: 2×2 close-up sheet with two puppets per cell (reach → hold hands → look at the lamp together → smile)
- `bg_wide.jpg`: wide; lamp at far left, pool in the left third, right half in darkness
- `bg_mid.jpg`: medium; workbench seen at an angle from front right, tool rack and mallet
- `bg_close.jpg`: close-up; the same oil lamp, only a pea-sized flame left on the wick
- `fx.png`: 8 stages of sawdust kicked up by a fall
