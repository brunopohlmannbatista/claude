# Cardboard stop-motion (cardboard)

**In one line**: a kid's imaginary world built from shipping boxes, tape and markers, a bit wonky, played dead serious for laughs; at the end it's revealed it was the bedroom floor all along.

## Best for

- **Subject**: a kid's pretend game: a box becomes a rocket, a submarine, a castle, and carries out a grand mission with total seriousness. **Three gags, each bigger than the last** (small failure → overdoing it → the reveal); the reveal is the landing, and at the end the hero refuses to give up and points to the next "mission".
- **Palette**: mostly kraft-paper brown, accents of marker red and blue and foil silver; the real room is dark, cool grey-blue.
- **Light**: one desk lamp, warm hard light from the top left; crisp shadows all falling the same way all film.
- **Camera**: low camera, eye level, medium, slightly looking up, so small cardboard looks epic.

Not for: lyrical, pretty or dreamy subjects; nature or realistic animals; scenes needing cloth, water, fur or other soft materials.

## Signature moves

- **Comedy timing** (on twos, 1 drawing = 1/12 s): setup (narration says it straight; without narration, the hero's solemn preparation) → pause 0.8–1 s (`silences`; only the prop's small jolts move: every few drawings it dips and returns, each with a `tap`; no per-drawing shake) → the gag lands in 2–3 drawings ("poof": flame 2 drawings, cotton 1, prop hops up and lands) → cut straight to the reaction. Hold the reaction cell about 1.5 s with the body still; to keep it alive, insert one face-only cell (eyes closed, or `close_1~b`) and mark the status `live='reaction'`; time the cell change to the key word of the narration.
- **Imagined and real sets; the landing is the reveal cut** (`reality_cut`: hard cut, no `tr=`): the imagined version shows only the cardboard set, backdrop filling the frame; the real version is shot at floor level in the bedroom, bed legs and desk lamp far bigger than the cardboard. Before the cut, pause 0.7–1 s with the hero on their proudest cell; same pose, same side of frame, hard cut to the real wide at the same moment, `stop` on the cut. Hold the wide 1.5–2 s (`idle=True`, stars swaying, slow pull-back, `live='reveal wide'`); after the reveal line (without narration, after the full 1.5 s) cut to a close-up for the reaction. The real background takes the prop image as reference; `[scene]` gives the prop's real state ("lying on its side on the rug") with a size anchor; `[shot_size]` says "camera on the rug at floor level, eye level, very close to the prop". The hero must still be big enough; "small" reads from the bed legs.
- **When the hero climbs into the prop, give them their own performance**: a cardboard puppet can only squeeze and fall, which is exactly the gag. One 2×2 medium-close-up sheet plays "stuck → head squeezes out → upper body out → pops out" (prop image as reference; `[framing]` says "the prop is the same size and in the same place in all four cells"), then one 8-cell sheet for the reaction after landing.
- **Hero in the foreground of the wide**: in the opening wide the hero walks on the ground close to the lens and the camera pulls back from them (1.12 → 1.0; to pull further write `push_ok='opening pull-back from the hero'`, or lint stops it at `push_max`).
- **Hanging foil stars**: the cheapest ambient motion, but `bg.txt` won't add them: in the imagined background's `[scene]` write "a few crumpled foil stars hang on thin threads in front of the backdrop" (upper half, clear of the standing area). After generating, find them with `layers.find_glints` (check with `glint_board` first); `glints(mode='sway', amp=3)` sways them per drawing and twinkles them, each with its own phase.
- **Jets and smoke**: exhaust flames and splashes use `place_at(..., ref=(midpoint of cell top edge), rot=prop angle)`, placed slightly inside the nozzle and turning with the prop; draw onto an `animi.Layer` first and `clip_layer` everything below the ground line, or the flame hangs down in front of the table. Cotton smoke goes **behind** the prop and lower than it.
- **Box flaps close** (`tr='box_flaps'`): two box flaps swing in, hinged on the left and right frame edges, cover the frame, then open on the next scene; once per film, for "somewhere else". The asset (one box flap) is generated as type prop (prompt in `how` in style.json), saved as `src/prop_flap.png`; the template's `load()` reads it.

## Compositing

- **Character relight**: none (`preset.light` empty); warm flat-lit assets sit right in the warm lamp-lit set.
- **Shadow** (`cast`, parameters in `preset.shadow`): characters, grounded props and things stuck in the ground all cast; pass `lift` when airborne. Assets carry no shadows; code casts them all.
- **Rigid**: `rigid`; no squash, no small turns or wobble, no per-drawing random tilt (`jitter_rot` 0).
- **Character and prop on one sheet** (character with the console in front of it): `check` flagging too many subjects is correct; add `--group grid` to both `check` and `slice`. Register by the prop: `animi.part_refs(cells, red)` finds each cell's button → `place_at(ref=)`; the prop stays put and the character moves as drawn. When the character reaches outside the prop the box widens; use `anchor='base'` (midpoint of the bottom band).
- **Things planted in the ground that stay** (flags, signs): keep them out of the action sheet (`[action]` says "after the flag is planted it no longer appears in the cells"); generate a separate prop image and place it at a fixed position.
- **Transitions**: only `box_flaps` uses `tr=`; `reality_cut` is a hard cut (`kind: move`); other scene changes are hard cuts too.
- **Title plate**: `cut`, kraft-coloured plate with pinking-shear edges, texture `ref/texture.jpg` (in the style package, no need to generate), dark text, lands with `thud`.

## Pitfalls

- **A real room shows up in the imagined background** → `[shot_size]` must say "imagined world" or "real version" (`prompts/bg.txt` draws them differently by these words); the imagined `[scene]` also says "the backdrop extends past the left, right and top of the frame; its edges are not visible".
- **Medium-close background comes out as a full set** → imagined: "pure material close-up: the whole frame is filled by one piece of corrugated cardboard painted deep blue, no edges of the cardboard visible, the hanging foil stars blurred into bokeh"; real: "everything behind is the real bedroom blurred into patches of colour".
- **Cardboard puppet drawn as a real child** → describe the character as "built from cardboard boxes, face drawn in marker", not "a little boy".
- **Shadow directions disagree** → never mirror any asset (hard-light shadows and painted shading flip); for the other direction, regenerate facing that way.
- **Brown character melts into brown cardboard** → keep blue marker stripes and red bottle caps on the character; darken and cool the real room.

## Sound

- **Score**: a budget space epic, around bpm 104. Energy follows the three gags: setup 0.45–0.6, pause before a gag 0.2, big action 0.9 or more, reveal 0.12, ending 0.6. Hits: big action `boom`, side character knocked over `accent`, small win `sparkle`, landing `thud`, reveal `stop`.
- **Foley**: cardboard knock `tap` (each prop jolt = one `tap`, v 0.25, pitch 1.4); "poof" = `whoosh` (pitch 1.8) + small `thud` (pitch 1.6); walking `step`, waving `whoosh`, tearing tape `rip`, cardboard squeezed `creak`; box flaps close `thud`, open `whoosh`.
- **Narration** (optional): a deadpan broadcast voice that treats small things on the floor as a grand mission, no jokes (the gags are in the picture); the reveal line said flat.

## Reference images (`ref/`)

`character.png` character sheet · `sheet8.png` character and prop on one sheet · `sheet4.png` medium-close-up sheet of the character in the prop's porthole · `prop.png` one prop in two states · `bg_wide.jpg` real-version wide · `bg_mid.jpg` imagined-version medium · `bg_close.jpg` imagined-version pure-material medium-close · `fx.png` fx sheet · `texture.jpg` title plate texture
