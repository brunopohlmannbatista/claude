# Crochet stop-motion (crochet)

**In one line**: dolls and a busy little world crocheted stitch by stitch from yarn; candy colours, lively, everything gently moving.

## Best for

- **Subject**: places full of small creatures: undersea, a pond, a garden; making friends, a band of companions, a small adventure. A crowd of small side characters (little fish, bugs) serves as both ambient layer and something to interact with, saving assets and adding play. Best if the hero has one big transformation that can be drawn fully (puffing up, curling into a ball, bristling): yarn is soft and stuffed, so the change can be drawn in an 8-cell sheet.
- **Other settings**: the moves below use undersea as the example; another place changes assets, not technique. Pond: reeds = `plants`, water striders / tadpoles = `Flock`, bubbles as before. Garden: grass = `plants`, butterflies / bees = `Flock`, petals = `Particles(mode='fall')`, wind = `plants(wind=)` plus a debris `Stream`. Say where it is in `[scene]`; the background and prop prompts are written as conditionals on `[scene]`.
- **Palette**: candy colours: coral pink, lemon yellow, mint green, lavender, with a teal-blue gradient background. The hero takes the most saturated colour in the film, one absent from the set (lemon-yellow hero with pink, purple and green coral).
- **Light**: top light from above, bright high-key, very light shadows. Under top light left-right mirroring doesn't show, so side characters swimming left can simply `flip`.
- **Camera**: front, eye level, roughly symmetrical, big coral framing both sides, open space in the middle for the hero. Medium shots use a left and a right view (about 80° from the left or right, the big coral at the back of frame), each generated with the wide as reference and the prompt "this is the same seabed as the reference image, the camera moved about 80° to the left (or right); do not repeat the reference composition", so sand and coral match.

Not for: dark, tense or scary tones; crisp hard action (fights, machines); realistic water, fire, smoke; big extreme-wide spectacles.

## Signature moves

- **Everything moves**: backgrounds hold only static coral and sand; seaweed, bubbles and little fish are separate transparent props composited in layers: background → back seaweed → bubbles → rear side characters / fx around the hero → hero → front side characters → front seaweed. 2–6 clumps of seaweed per background is enough. Ambient sprites use `layers.Sprites` (cached per scale step, so a dozen sprites per drawing stays fast).
- **Seaweed**: `layers.plants`, swaying from the base, periods and phases staggered (the default). Back row small (0.12–0.22 H), darker (`lum` 0.8–0.88), blur 1–1.6, parallax 0.9; front row big (0.46–0.58 H, half the frame), blur 2.5–3, parallax 1.25. Keep front seaweed off the hero's swim path (scaled up, the hero's belly gets covered).
- **Strong current**: rigid rotation can't "bend" a plant. Generate the same seaweed set again half-bent and fully bent (`prop`, the straight one as reference; `[prop]` says "the same set as the reference, same order… roots still firmly in place, bases flush; upper half bent into an arc to the left / whole clump in a big arc, upper half flung sideways to the left"); `plants(..., wind=0–1)` with `bent=[half, full]` per clump, which whips back and forth at peak. For real force also add:
  - Debris stream: one debris prop sheet (sand-coloured fluff, coral yarn ends, small leaves, small shells), `deb = layers.Stream([f'deb_{k}' for k in range(6)], n=30, dir=-1)`, each drawing `deb.draw(frame, spr, cam, d, amount=current strength)`; it rushes along the sand, near pieces bigger, blurrier, faster.
  - The set does not shake fast (a background moving every drawing is shaking): the force comes from fully bent seaweed whipping, debris rushing along the ground, characters pushed away. To move the whole set use only slow `sway` (period ≥ 2 s, ≤ 4 px).
  - Little fish tumbling past: `Flock` can't do this; build `items = [dict(cell=, x=, y=, s=1, rot=about 20° per drawing, flip=, depth=0, motion=20), …]` and pass to `layers.draw_flock(frame, spr, cam, items, size=)`.
  Reach full current strength within 8 drawings.
- **Bubbles** (underwater films): generate one prop sheet of solid yarn bubbles (`prop`, 6 bubbles in three sizes, see the prompt); `bub = layers.Particles(cells, mode='rise', blur=3)`, 2–3 vents per background, `bub.draw(frame, spr, pic, cam=cam, vents=[(x, y), …], size=1.5)` (wide 0.04–0.09 H; `size` is an overall multiplier). Small wobble only, no full spins (highlight stays top left; the default). In medium-close multiply `size` by another 1.6 and blur with `blur=3`. In a current, `wind=` blows them sideways; don't scale them up much with the wind (they blur into big white balls).
- **School of little fish**: one prop sheet of 6 fish, "three colours × tail straight / flicked", covers the film (or generate one colour and register `animi.recolor(img, hue=)` variants as siblings `fish_0~b`). `fish = layers.Flock([['fish_0', 'fish_3'], ['fish_1', 'fish_4'], ['fish_2', 'fish_5']], n=5, hold=2)` (tail changes cell every 2 drawings). Circling the hero: `fish.ring(pic, cx, cy, rx, ry)`; draw the back half with `draw_flock(..., front=False)`, then the hero, then the front half with `front=True`. Scattering in fright: `fish.scatter(pic, t=pic - fright drawing, origin=(cx, cy))`, distance ∝ t², motion blur built in; `hold=1` while frightened.
- **Floating hero**: place by box centre (`put(..., ref=box centre)` or `Sprites.put(at='center')`), bob 8–14 px with a period of 16–26 drawings (`layers.bob`), body tilting 1–2.5° with it. `HERO_H` 0.30–0.34 × SHORT (no feet; `A.scale_ref` measures the "body level" cell); in a wide, `k` 1.0–1.15 reaches the minimum. 8-cell sheets: `check --float`.
- **Puffing up**: the growth is drawn in the sheet (8 cells from normal → spines appear → spiky ball twice the size → deflating), no code scaling; size every sheet by the "not puffed, body level" cell so switching sheets doesn't jump. On the puff the camera snaps in to 1.06, hitting `boom` and `puff`; the "poof" fx sheet is 8 cells at 2 drawings each, about 0.85 H in a medium, drawn behind the hero with only the outer ring showing.

## Compositing

- **Character relight** (`preset.light`): none; flat light as is. The top light in the sheets matches the set.
- **Shadow**: `contact`, 0.28, on the sand below the hero. Use the template's `put()`: `y` = the sand line, `ref=` box centre, `lift` = full height above the sand (the template raises the character and the shadow shrinks and fades by the same `lift`). The shadow disappears at about 0.8 body widths above the ground; higher than that, no shadow. A full-body medium-close standing on the ground still gets one; only close-ups that crop the body skip it (`shade=False`).
- **Rigid**: no (idle breathing on). In medium-close, moving bubbles and seaweed help carry the holds.
- **Transitions**: `blanket_drop` (`kind: smear`): a crocheted granny-square blanket drops over the lens and is lifted off again; fits any setting. Underwater, the `bubble_curtain` (`kind: curtain`, with whoosh + bubble) can take its place; not underwater, don't use the bubbles. Assets and parameters in style.json, `tr='<id>'` in SHOTS. All other cuts are hard cuts, on the action.
- **Title plate** (`title.plate`): `stitch`, cream rounded plate with a ring of coral-pink stitches and a shadow, deep-sea teal text; the plate lands with `puff`.
- **Subtitles**: white text, deep-sea teal outline, semi-transparent rounded teal plate (`subtitle.plate`, on).

## Pitfalls

- **Fx sheet grows yellow stars and purple pompoms** (materials listed in the prompt get drawn as objects) → `[fx]` describes only that one effect; the prompt template is written as conditionals (bubbles mentioned only when drawing bubbles, splashes only for splashes) plus "no added stars, pompoms or thread ends". Remove any that got drawn by colour.
- **Hollow yarn-ring bubbles look like donuts or life rings in a still** → bubbles are always solid flattened balls with a white crescent highlight at top left (in the prompt template). Curtain and "poof" fx also say "solid yarn bubbles" in `[fx]`, never "hollow rings".
- **Fx bursting around a character covers the face** → draw it behind the character, only the outer ring showing; `[fx]` says "each cell has an empty circular area in the middle; the effect is only around that circle".
- **Background paints its own seaweed, fish, bubbles; adding sprites doubles them** → end `[scene]` with "no seaweed, no fish, no bubbles, no animals" (the template also says only static things).
- **Hero lost among candy colours** → `[scene]` says "no <hero colour> in the coral".
- **Fish circling from in front of the hero to behind jump on the layer-switch drawing** → keep them behind and pass behind the hero, or switch layers only where they don't overlap the hero.
- **A wide-shot hero at full size gets covered by front seaweed** → clear the hero's swim path before placing seaweed; front seaweed only at the frame edges.
- **`check` warns about ground line or height spread on an 8-cell sheet** → normal for floating characters and deliberate puffing; use `--float`.
- **A transparent sheet occasionally comes back fully white** (all four edges 100% white) → regenerate once as is; yarn edges cut out cleanly (keep the anchor's "outline is the small bumps of stitches, no long stray threads").
- **Subtitles dissolve on white bubbles, pink coral, beige sand** → use `subtitle.plate` from style.json (on); title and end card text use `bookends.title_tag`.

## Sound

- **Score**: undersea bubble band. Vibraphone on a pentatonic melody, kalimba answering, ukulele offbeat strums, jazz pizzicato bass, congas and shaker with a little swing; the puff hits `boom`, bubble touches and hiding hit `sparkle`. Lowest level: double bass + vibraphone.
- **Foley**: puffing up `puff` (plus a `thud` at pitch 0.8); bubbling `bubble`; bubble touching a nose `tap` pitch 1.8; fish darting `whoosh` pitch 1.4–1.6; strong current `flow` (d seconds) + a low `whoosh` pitch 0.5–0.6 about once a second; swept into water, splashing `splash`; appearing, recognising `sparkle`.
- **Narration** (optional): curious and bouncy, like a kid pressed against a fish tank introducing their friends inside.

## Reference images (`ref/`)

- `character.png`: crocheted pufferfish character sheet (front, three-quarter, side, back), clean yarn edges
- `sheet8.png`: excited → puffs into a spiky ball → eyes darting → deflates and droops in 8 cells, size change drawn in
- `sheet4.png`: 2×2 medium-close-up sheet (envious / sad / holding breath / panicking); button eyes never change, acting with eyebrows, mouth, blush
- `bg_wide.jpg`: wide, front-on symmetrical coral reef, big open sand in the middle, no seaweed, fish or bubbles
- `bg_mid.jpg`: medium, camera 40° front left, brain coral on the left
- `bg_close.jpg`: medium-close, shallow depth of field, blurred coral wall
- `prop.png`: three seaweed clumps (bases flush, swaying from the base); `prop_weedbent.png`: the same set bent over by the current
- `prop_bubble.png`: solid yarn bubbles in three sizes, white crescent highlight top left
- `fx.png`: bubble curtain in 8 stages, all solid yarn bubbles, no stars (the `bubble_curtain` asset is a sheet like this)
