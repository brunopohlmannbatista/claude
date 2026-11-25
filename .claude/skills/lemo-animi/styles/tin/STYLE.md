# Tin toy stop-motion (tin)

**In one line**: retro wind-up toys of printed, stamped tinplate that move in jerks; wound up they come alive, run down they stop.

## Best for

- **Subject**: a wind-up circus, a toy shop after closing. Toys perform in turn; one runs down mid-act and gets wound up again.
- **Palette**: slightly faded retro print colours (tomato red, cream, teal, golden yellow), bare silver tin at the edges.
- **Light**: warm stage spotlights plus strings of small coloured bulbs; bright metal highlights.
- **Camera**: eye level or slightly low so the wind-up key shows; mostly medium shots, camera mostly fixed.

Not for: subtle facial acting, soft fluid motion, outdoor landscapes, water.

## Signature moves

- **Jerky motion**: the preset is on threes (`on: 3`, 1 drawing = 3 frames = 0.125 s). Every move is "snap into place, hold": the arrival pose for **2 drawings** (0.25 s), the hold for **4 drawings** (0.5 s). That means repeating the same cell for several drawings, not `Timesheet.add(holds=)`: `holds` counts frames (`holds=2` is faster than on threes) and changing it puts `P(seconds)` out of step with drawing numbers. The mechanical feel comes from the legs and rhythm in the drawings (arrive, hold), not from code bobbing or shaking each drawing. Bodies never squash: no `sy` in code. Rigid parts rotate, never bend (a tilt in a hold is a one-way `rot`: tip over and stay, no rocking).
- **Winding up and running down** (this style's best turn and payoff):
  - Wind-up = 3 turns of the key. Each turn: 1 drawing in transit (key at 45°) → hold on the quarter-turned key for 4–6 drawings; `wind` on each arrival. The toy jolts once per turn: that drawing drops 3–4 px, the next returns (one one-way jolt, no shaking). Hard cut within 1 s of the third, full turn. A butterfly key looks the same after half a turn, so cycling the cells 1 → 2 → 3 → 2 → 3… reads as continuous winding. The character's first drawing afterwards jolts in place (drop, return) before it sets off.
  - **The key is a real part, and it turns about its shaft.** It stays plugged into the same point on the back in every cell: never floating, never sticking out of a side or the chest, never moving into the helper's hand or beak. How a turn looks depends on where the shaft points, so the close-up prompt describes what the camera sees:
    - Shaft across the frame (camera beside the toy or at rear three-quarter; the usual case): the wings swing towards and away from the lens: **full face (whole butterfly) → turned 45° (narrower) → edge-on (a thin bar along the shaft line)**. Write it in those words. "Vertical → diagonal → horizontal" here makes the model spin the key flat like a propeller on a sideways shaft (failed in several tests).
    - Shaft pointing at the camera (straight from behind): the wings spin flat in the picture: upright → diagonal → horizontal. The helper then has to reach in from the side.
  - **Wind-up close-up staging**: the wound toy shows its back (rear three-quarter or profile with the back towards the helper), never its face to camera with the key out of its side. The helper stands behind it, facing it, and grips the key's wings; the grip turns with the wings. Wording that worked first time (key on top of a four-legged toy's back): "From behind-left of the elephant: its back with the gold key and half its head fill the right of the frame, facing right; the monkey stands behind it on the left, on tiptoe, both hands gripping the key on the elephant's back. Crop at the elephant's middle and the monkey's waist. 1 both hands on the key, key full face 2 twisting hard, key turned 45°, the monkey leans with it 3 key turned 90°, the monkey on tiptoe turns with it 4 fully wound: key full face again, one hand lets go, body leans back." A standing toy (key sticking straight back): camera at rear three-quarter, the shaft running back and slightly away from the lens.
  - Before slicing the close-up sheet, check each cell: key in the same spot on the back, wings at the planned angle, the helper touching the wings, no second key. Any miss: regenerate with the miss named; never ship a key that floats or turns on the wrong axis.
  - Run-down = normal mechanical waiting first (cells alternate every two, 1.5 s), then each cell holds longer: **2 → 3 → 4 → 6 → 9 drawings**. In the action sheet each cell leans more, moves less and turns the key less; on the last hold tilt 3° further, then back 1° (`rot`). `tap` / `wind` clicks get sparser and softer (volume 0.4 → 0.3, pitch 0.8), `wind_down` on the beat; at the turn the score stops for 5–6 s while the clicks keep going (a score stop over 2 s needs sound inside it, sound.md).
  - Action sheet `[action]` wording (works first time): "Running down: each cell moves less and leans further, the last cell stops. … 3 body leans forward and down about 6 degrees … 7 a last lean and stop: body leans forward and down about 25 degrees … 8 exactly the same stopped pose as cell 7, with a … balanced on its nose (payoff prop)". Cell 8 draws the payoff prop into the pose; in compositing, swap to cell 8 on the drawing where the flying prop lands.
- **Transitions**: tin curtain closing (`tin_curtain`, `kind: hinge`: two striped tin curtains draw shut from the frame edges, then open on the next scene; asset in style.json). The wind-up cut (made from a 2×2 close-up sheet with both characters in frame; no separate key fx sheet) and the run-down cut are in-shot tricks (`kind: move`), not `tr=`.
- **Chasing bulbs**: bulbs along the top of the background brighten and dim in turn (groups of three, one step every two drawings). This dims the bulbs already in the generated image; it does not draw lights: `layers.find_glints` finds them, `glints(mode='chase')` animates them. Touch only individual small bulbs: cap the size of detected bright spots (large bright areas are not bulbs), then check that whole-frame brightness between adjacent drawings differs by under 1 grey level, or the whole background flickers. Long holds are carried by this plus camera push/pull.

## Pitfalls

- Looks like smooth plastic or 3D metal → the prompt must keep "halftone print dots, folded edges, rivets, worn paint" (already in the style anchor).
- Printed faces can't emote → show feeling with head angle, body pose and the tin jaw.
- Metal highlights have a direction → never mirror assets (the light flips).
- Reflections give the set away → the set floor must be matte (already in the prompt).
- Camera judders on threes (it steps per drawing too) → move the camera little; `push_max` only 1.08.
- Sparse low-alpha red speckle around action sheets → `slice --fragments drop` removes it. Metal rim, key and rivet highlights hug the outline, so the transparent background cuts clean.
- Characters look slightly cold on the warm stage → `preset.light.tint` (1.035, 1.0, 0.95) warms them (already set).
- A 2×2 face-and-shoulders close-up sheet fails `check`'s edge-transparency test (the subject touches the cell edge) → that is the close framing, not a drawn scene; confirm transparent borders on the `check` preview.

## Sound

- **Score**: staccato trumpet, glockenspiel, oom-pah trombone, old player piano, claves and snare; straight march (~120 bpm). The score keeps its tempo when a toy runs down: use the `wind_down` hit plus silence to show the stop.
- **Foley**: winding `wind`, tin knocks `clink` (`pitch` 1.1 = cymbal, 1.6 = the "ding" of hitting a bulb), small steps `step`, landing `thud`, run-down clicks `tap`. Every wind-up needs a `wind`.
- **Narration** (optional): a proud circus ringmaster; sentences get shorter as the toy runs down.

## Reference images (`ref/`)

- `character.png`: wind-up tin elephant character sheet (front, three-quarter, side, back), key on the back
- `sheet8.png`: running down in 8 cells, each leaning further and moving less; the last cell stops with the payoff prop (a ball) balanced on the trunk
