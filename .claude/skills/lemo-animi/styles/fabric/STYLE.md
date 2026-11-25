# Fabric patchwork stop-motion (fabric)

**In one line**: puppets and countryside sewn from print fabric, buttons and stitches; a walk under warm sun, soft and homespun.

## Best for

- **Subject**: countryside, farm, country lanes, market day, moving house: **a walk** across a big patchwork field. A line of small animals sets off, one gets separated and finds the way, someone takes a shortcut. Smoothest structure: set off → separated / something blocks the way → recognises a path and walks it alone → arrives first (twist landing). Stitches, buttons and the ribbon stream in the set can be plot props (stitches are paths, buttons are stepping stones).
- **Palette**: soft country colours: wheat yellow, apple green, sky blue, floral pink, off-white; floral and gingham prints. The hero is plain fabric plus one bright red accessory.
- **Light**: warm afternoon sun, low from the side-back; weave and seams cast tiny shadows; warm overall, soft contrast.
- **Camera**: medium, medium-close and wide at eye level, close to the ground; the extreme-wide (showing the route) looks down from above at an angle, like seeing a patchwork map from a hillside.

Not for: night, dark tones, tension and thrills; city, tech, machines; fast fights or big squash-and-stretch comedy; stories confined to one small room (wastes the fields).

## Signature moves

- **Open on an eye-level wide**: the starting place (road outside the barn, pond side) as an eye-level wide, a line of small animals walking in from one side so the hero is clear in the first second; the map extreme-wide comes later.
- **Writing the map extreme-wide**: the background is a patchwork map seen from above at an angle. In `[scene]` place things one by one: who is in which corner, where paths run from and to, where they cross ("bottom left is the barn… an off-white fabric-strip road runs right along the bottom edge, then up the right edge to the pond at top right… a thick dark-brown stitch line runs diagonally from beside the barn to the pond… a sky-blue ribbon stream crosses the stitches in the middle"); image generation follows it. Size houses and trees to the hero's scale: the hero must still reach the extreme-wide minimum (the template measures it), so the barn is over 1/4 of frame height and trees are about the hero's height, or the hero ends up bigger than the house. Don't shrink the hero to fit the map.
- **Where the two map shots go**: use one map at most twice. First after "recognises the path", to show the route; second in the cross-cutting, to show the result (the hero further along the route, "how far" readable at a glance). Recognising and pointing play in the eye-level medium before it, cutting on the action to the map as the camera pulls back.
- **Eye-level backgrounds are generated separately, from the same fabric as the map**: generate each eye-level background on its own without the map as reference; `[scene]` names which two fabrics of the map it is ("in front of the seam is pale-pink floral cotton, behind it apple-green and white gingham") so fabric and light match (the map is top-down; using it as reference makes eye-level backgrounds top-down too). A second eye-level background of the same place takes the first eye-level background as reference and states the new camera position. To say "this path leads there", let the path recede: "the stitch line starts close at the bottom left of the frame (beginning at a knotted lump of thread) and runs stitch by stitch toward the far upper right, stitches getting smaller with distance, all the way to the distant pond"; reads better than a path straight across the frame.
- **Push into a patch** (`patch_push`): on the map extreme-wide the camera slowly pushes toward the patch the hero is on; at the tightest drawing, hard cut to an eye-level shot on the same patch, with whoosh. Top-down to eye level on the same fabric is a change of view, not a jump cut. Only on the two map shots above, never the opening.
- **Stitches are paths**: the hero walks and runs along stitches, camera tracking; always facing the destination.
- **A line of siblings**: siblings reuse the hero's walk sheet with a recoloured accessory: in `load()` `cells['walk_3~b'] = animi.recolor(cells['walk_3'], hue=205, sat=0.85)`, sharing the original cell's anchors (`info['walk_3~b'] = info['walk_3']`), one suffix per sibling (`~b`, `~c`); only the saturated red shifts hue, blush and mouth are unaffected. Timesheet and `put()` use cell names like `walk_3~b`. Line positions come from `layers.Flock` (`cycles` one loop per member: `[[f'walk_{k}~b' for k in range(8)], [f'walk_{k}~c' …]]`, `hold=1`) via `queue(pic, x0, y, gap, speed, lead=the big one's cell loop, lead_s=1.6)`: one after another, phases offset, same speed, no sliding. Each computed member (`cell / x / y / s / flip`) goes to `put(..., main=False, jit=0.5)` so shadow and jitter follow the style. The hero is the one with the different accessory colour, placed with its own `put()` (which measures size).
- **Extreme-wide walk sheet**: every character who walks in an extreme-wide gets a top-down-angled walk sheet (see `ref/sheet8_top.png`); `[action]` says "camera above looking down (about 45°, like standing on a hill looking down at small animals), so the top of the head, back and top of the accessory are visible, feet under the belly barely showing; body facing front right (three-quarter view facing right)". Cells that only stand or point in an extreme-wide may use the eye-level sheet.
- **2×2 full-body sheet**: sheet4's `[framing]` says "full body, top of head to soles fully inside the cell, camera at eye level at the character's height; soles on the same line in all four cells" to get four full-body performance cells for medium shots (see `ref/sheet4_full.png`; check / slice with `--n 4 --rows 2 --cols 2`). The generic layout's "medium-close" doesn't conflict with "full body" here; generation follows `[framing]`. If check warns about the ground line, align on the "standing straight" cell.

## Compositing

- **Character relight** (`preset.light`): none; flat light as is. The warm sun in the sheets matches the backgrounds.
- **Shadow**: `contact`, 0.38; width 0.62 × character width, offset forward 0.06 (`contact_w` / `contact_off`: puppet feet are small, the default 0.9 is a size too wide). Jump height comes from code (`lift = height × sin(π·u)`, button hop about 0.17 H); the shadow shrinks and fades with it.
- **Rigid**: no (idle breathing on). In medium-close, swaying foreground plants help carry the holds.
- **Transitions**: `cloth_flap` fabric cover (`kind: smear`, in left out right, `wobble` 0.12, asset below), `tr='cloth_flap'` in SHOTS; `stitch_wipe` seam wipe (`kind: stitch`, a stitched fabric edge sweeps left to right, `sprite` is `prop_seam`), `tr='stitch_wipe'`; `patch_push` is a camera move plus hard cut, no `tr=`.
- **Fabric cover asset**: type `texture` (`[material]` "a whole sheet of pale-pink floral cotton laid flat filling the frame, warp and weft visible"), saved as `src/fx_smear_tex.png`; the template's `load()` reads it.
- **Seam wipe asset**: type `prop`, "one long strip of seam tape: a narrow off-white linen edge with a thick dark-brown stitch line down the middle, horizontal, perfectly straight", saved as `src/prop_seam.png`; the template's `load()` reads it.
- **Title plate** (`title.plate`): `stitch`, plain off-white rounded fabric plate with a ring of red dashed stitches (the hero's accessory red) and a shadow, dark-brown text; no texture (print fabric fights the text).
- **Subtitles**: warm-white text, dark-brown outline, semi-transparent dark-brown plate (`subtitle.plate`).

## Pitfalls

- **Text dissolves on print fabric and the off-white road** → subtitles must have the plate (on in style.json). The map's road often runs along the bottom, under the subtitles: in map shots with narration frame the road higher (tilt the camera down).
- **Blurred medium-close background adds a house that doesn't match** → `[scene]` states "no houses, no barn, no trees, no fences, no animals, only fields, small flowers and sky".
- **Every reaction close-up uses the same blurred background** → generate at least two (different fabric, different direction) and alternate.
- **The same barn or house looks different from another camera position** (door colour or shape changes) → describe it fully in every background's `[scene]` ("red-and-white gingham roof, off-white linen walls, one brown arched wooden door"), never just "barn".
- **Characters in the same frame from different angles** (one top-down, one eye level; perspective doesn't match) → in an extreme-wide, every character walking in frame uses the top-down sheet.
- **Wide came out top-down** → `[shot_size]` says "wide, camera at eye level close to the ground (not top-down), lens at the character's eye height".
- **Hero lost in the prints in an extreme-wide** → plain body + one big red accessory + a distinctive silhouette; the patches the hero walks on are not the hero's colour (a yellow hero doesn't walk on wheat-yellow corduroy), use plainer florals or off-white strips.
- **Check reports opaque edges on a transparent sheet though the preview is transparent** → semi-transparent haze in the background; clean it with `--clean` / `animi.py clean` and check again, no regeneration. Fabric puppet edges cut out cleanly.
- **Fx sheet adds stars or thread ends** → end `[fx]` with "draw only X itself, no stars, no thread ends, nothing else".
- **Puppet drawn as a smooth plush toy** → the prompt needs "weave, seams, stitches, buttons" (in the anchor).

## Sound

- **Score**: country folk. Recorder on melody, harmonica answering behind it, offbeat plucked zither, pizzicato double bass, cajón and tambourine one step per beat; key actions get a zither glissando and a cajón hit, cowbell to close. Lowest level: zither with long harmonica notes.
- **Foley**: walking `step` (small ones pitch 1.3–1.4, v 0.22; big one pitch 0.8), stepping on buttons and light knocks `tap` (pitch 1.1–1.3), landing `thud`, puppet falls over `flop`, buttons `button`, fabric rubbing `rub`, flapping cloth and push-ins `whoosh`, recognising / butterfly `sparkle`; the fabric cover gets whoosh + thud.
- **Narration** (optional): bright and unhurried, like talking while walking along a field edge, with a hint of a smile.

## Reference images (`ref/`)

- `character.png`: fabric duckling character sheet, plain body + red gingham neckerchief + a tuft, clean fabric edges
- `sheet8.png`: button hop in 8 cells (crouch, take off, tuck in the air, reach to land, squash, wobble, settle); soft, loose puppet motion
- `sheet8_top.png`: extreme-wide walk sheet, 8 top-down-angled cells: top of head, back and top of neckerchief visible, feet barely showing
- `sheet4.png`: 2×2 medium-close-up sheet (entranced / frozen / about to cry / determined); button eyes never change, acting with mouth, thread eyebrows and fabric tears
- `sheet4_full.png`: 2×2 full-body sheet (looking down at the path / testing a step, thinking / recognising / pointing the way), soles on one line in all four cells, for medium shots
- `bg_map.jpg`: extreme-wide, top-down-angled patchwork map (barn, the long way round by road, the diagonal stitch shortcut, ribbon stream with buttons, pond)
- `bg_wide.jpg`: wide, eye level at the pond, road running from the left to the pond
- `bg_mid.jpg`: medium, eye level, stitch line from a knotted thread end close by to the distant pond
- `bg_close.jpg`: medium-close, shallow depth of field, blurred floral fabric field, no houses
- `prop.png`: ambient props: fabric grass, daisies, reeds, cotton clouds (bases flush, swaying from the base)
- `fx.png`: cotton dust in 8 stages (only cotton puffs, no stars)
