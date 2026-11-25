# Directing: story, narration, shots, acting

**The most common failure is not technical: too little motion and one camera position for everything.** The stills look good, the film plays like a slideshow. Every section below exists to avoid those two.

## 1. Story: one through-line, several small turns

**Story skeleton (required)**: the director's plan writes the story in the parts below, each with its seconds. Lengths are the film's; with title and end cards take 6 s off first, then split.

| Film length | Skeleton |
|---|---|
| 20 s | **A gag**: setup (who, what they're up to; about a third) → the surprise → a 1–2 s reaction. No chain of tries. |
| 40 s (story ~34 s with cards) | **Setup** ~5 s: who, where, what they want and why · **Tries** ~16–18 s: three attempts, each bigger or different, each failing for a reason you can see, with a consequence · **Low point** ~3–4 s: gives up or is sad, acted in the picture · **Turn and payoff** ~6–8 s: a new idea or someone's help, the want answered, then a short button (a last laugh or a lingering look) |
| 60 s | The 40 s skeleton with more room in each try, plus **a side character with its own small line**: wants something too, crosses the hero's path, matters at the turn |
| 90 s – 2 min | **2–3 scenes**, each a small chapter with its own goal, try and setback, in a different place or time; each scene's ending causes the next; the last scene holds the low point, turn and payoff |

- **Each part is caused by the one before** ("because … so …"), never "and then". The want is set up before the first try; the payoff answers it (gets it, or finds something better).
- **A user's plot fills the skeleton**: keep their events, add the missing parts (usually the setup and the low point) as beats.

**Event density: a new event every 1–1.5 s** (a new action, a character entering, a reaction, the camera showing something new): at least story seconds ÷ 1.5 events (a 34 s story: 23); count them. A story beat in the beat sheet lasts 2–4 s and holds several events.

Useful structures (pick or combine):

| Structure | How |
|---|---|
| Rule of three | Do the same thing three times: two set the expectation, the third goes wrong |
| Try → fail → escalate → accidental success | Wants something, first try fails, tries harder another way, gets it by accident |
| Chain reaction | A bumps B, B startles C, C knocks over D |
| Contrast | Two characters differ in tempo, size, temperament |
| Reversal payoff | The last moment overturns the expectation |

- Every beat answers **who does what, why, and how others react**. Reactions are the cheapest acting: a double take, a head tilt, a blink, a look back.
- **Give the hero something to interact with**: a side character, a passing animal, something to knock over, a door that opens. A hero alone can't carry more than 5 s.
- **Pick stories the style is good at**: the style's `STYLE.md` lists what suits it and what doesn't. This method is bad at: the camera orbiting a character, two characters tangled together, long dialogue, one object continuously morphing into another. Write around them (cuts, handing things over, narration, transitions).

## 2. Narration script (if narrated)

Without narration the picture tells everything: every beat needs a readable action or reaction (pause, look back, freeze); twist and payoff get close shots; the score goes silent before the twist.

- **The narrator tells the story; characters don't speak** (no lip sync). Characters may make sounds ("Wow!", "Hey!"): put them in the narration or make them foley.
- **Narration fills at most 60% of the story time** (`sound.py vo` prints the share, `lint` warns above it). Per 30 s of story that is about **zh 60–90 characters** in 4–6 lines, 8–18 characters per line, or **en 40–55 words** in 4–6 lines, 5–12 words per line; one idea per line. A slow voice (child voice, a calm tone) speaks fewer: cut lines, never speed the voice up to fit. `sound.py vo` also measures the rate: above 5.2 characters/s (zh) or 3 words/s (en), cut words.
- **Leave the picture room**: the twist and at least one more stretch of 2 s or longer play with no narration at all; the action and sound carry them. A line on every shot means the narration is telling what the picture should show.
- **Don't narrate what's on screen** ("he jumped" is visible). Say what the picture can't: thoughts, time, cause, irony ("The third time, he closed his eyes.").
- Open with 0.5–1 s of picture and sound before the first word; leave a silent gap before the twist (score silent too; length in sound.md, `silences`); keep the payoff line short.
- Tone follows the style's `voice.tone`.

## 3. Shots and shot sizes

**Shot list** (in the director's plan, aligned to narration and beats):

| Shot | Time | Narration | Place / view | Size | Background | What we see | Why cut | In-shot move | Transition |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0–8.2s | L1, L2 | kitchen / front | wide | bg_kitchen_wide | establish kitchen, first toss, pancake flies off | — | slow pan right, small push on the toss | picture from frame one |
| 2 | 8.2–9.6s | — | kitchen / front | close-up | bg_ceiling_close | pancake stuck to the ceiling | see a detail | static | cut on the look-up drawing |
| 3 | 9.6–15s | L3 | kitchen / right | medium | bg_stove_side | the two friends exchange a look | reaction, new view | static | hard cut |
| … | | | | | | | | | |

Rules:
- **Cut only for a reason; never pad shot count or sizes.** Cut only when the story changes place, a detail must be seen (close-up), or another character's reaction must be seen (new view). Otherwise play the scene in one shot; push in slowly if you need closer. Typical shot counts per length: the asset table in SKILL.md. A static shot lasts at most 10 s (14 s while pushing or panning); busy stretches are carried by the hero and side characters acting in frame, not by cutting.
- **No zoom cuts**: a hard cut in the same place and view that only changes size (wide → medium → medium-close → medium) looks like zooming, even with separately generated backgrounds. Within one place you may only cut to a **true close-up** (filling the frame with a detail, hero more than 2× the previous shot; medium-close and medium don't count) or a **real change of view** (side, reverse, top, low, with the characters' screen position and facing changing to match). Every shot has `place` and `view`; `shots_lint` checks them and also reports a place whose shot size flips back and forth 3+ times.
- **Wides establish space and show action; close-ups show details.** A key reaction can stay in the current shot (if the face is big enough) or get a close-up; never cut to a medium-close just for a reaction.
- **Hero size** (share of the short side): wide ≥ 30%, **opening and payoff wides ≥ 33%**, medium ≥ 40%, medium-close ≥ 60% (the style's `hero_min_scale` may relax only wide and extreme-wide; a deliberate single shot sets `min=`). If even the wide can't reach it, the set is too big: shrink the stage, walk the hero on the foreground ground near the camera; don't shrink the hero.
- **Extreme-wide** (≥ 15%) only for route, map, environment; at most 2 per film, never the opening or payoff. Distant acting (recognising, waving, waking) gets an eye-level medium: put a medium generated for that place before the extreme-wide, hero ≥ 40% acts it out, cut on the action to the extreme-wide pulling back to reveal the route. The payoff's big action (puffing up, catching) also gets a medium or medium-close, ideally from the same camera where the trouble began; pushing in on a wide is no substitute.
- **New shot = new background and new view**: generate a background composed for each camera. Backgrounds of one place use **that place's main background as reference** (so ground and landmarks match); the `[shot_size]` slot states how the camera differs from the main background ("from the right of the stove at eye level, turned 90° from the reference; the big tree that was on the left is now in the back; not the same composition as the reference"; 40° usually still reads as the same view and cuts like a zoom); the `[scene]` slot names the concrete objects in that patch ("pink floral fabric in front of the seam, green check behind"). Generated backgrounds are only 1600–1900 px wide and blur when enlarged. A result that's nearly the wide's composition, only bigger, can't be hard-cut against the wide.
- **Front-only styles** (paper craft, cut paper, shadow puppets, clay relief) change camera by: another spot and distance on the surface (another patch of paper, a small area only), light direction (moon left / right / out of frame), horizon height, another layer (under water, in the sky), background colour.
- **Returning to a place several times**: generate a new background each time from another wall or angle ("another wall of the same control room"), without the old background as reference. Reusing a background one shot later is fine; returning 3+ times feels repetitive (`shots_lint` warns).
- **No jump cuts**: adjacent shots must not share an angle and only change size (same background, or two nearly identical compositions); the cut looks like a stutter. Change view (new background), cut to a true close-up, hide the cut with a transition, or don't cut and push/pull in-shot. `shots_lint` checks (background similarity, plus zoom cuts via `place` / `view`). Dark styles or styles with one backdrop colour have naturally similar backgrounds: if the cut sheet shows it isn't a jump cut, set `cut_ok='reason'` on that shot.
- **Continuity across cuts**: position, held object, prop state and expression match between adjacent shots (both sides of a cut use the same expression cell); a change of place needs setup (a close shot or reaction shot in between).
- **Subtitles sit at the bottom** in every style; with narration, frame the action above the subtitle band (compositing.md, subtitles).
- **Medium-close and close-up use 2×2 close-up sheets** (bigger cells); wide and medium use 8-cell sheets. **Medium-close shows the full body by default**: head to feet in frame, standing on the near-camera background's ground with a contact shadow, hero 60–80% of the short side, a little margin above the head and below the feet. Never crop at the chest with the cut edge mid-frame (a half-body sticker). Only face close-ups (0–2 per film) crop the body, with the edge below the bottom of the frame.
- **In-shot camera**: pans (extra-wide backgrounds), small push/pull (≤ the style's `push_max`), stepped per drawing. Big changes come from cuts.
- **Cut points**: inside an action (the take-off or impact drawing) or between narration lines; keep facing and left/right position consistent across the cut (don't cross the line).
- **Transitions**: hard cuts by default (the most authentic for stop-motion), but all hard cuts feel abrupt. No black transitions at either end (fade to black, iris in/out): the first frame is picture, the last shot holds (the sound ending is enough). Ways to smooth a cut, lightest first:
  1. **Cut on action**: cut on the throw, the fall, the run into frame, with the motion carrying across (pancake exits the top → enters the next shot from the bottom).
  2. **Carry it with camera motion**: end a shot pushing or panning toward the next one, and continue the same direction after the cut (wide pushes toward the stove → cut to a stove medium still pushing slowly).
  3. **Dissolve** (`mix=<drawings>`, 0.5–0.7 s; general, any style, so styles don't list it; `mix=dict(after=8, live=True)` keeps the outgoing shot acting instead of freezing on its last drawing): quiet moments, time passing (into closed eyes and a deep breath; the final pull-back). 1–2 per film. Both sides must show roughly the same things: no dissolve when the next shot adds a character or prop on the same background (it ghosts in); hard cut instead, or let it walk or roll into frame. Never dissolve to swap a pose or an object within a shot.
  4. **Signature style transitions** (material smear, page turn, paper-layer wipe, stitch wipe, curtain…; `tr='<id>'` in SHOTS): each style's `transitions` in `style.json` define only what its signature transitions look like and what to generate for them (`how`); whether and where to use one is your call. Typically at a change of place or section ("try again", "somewhere else"), at most once or twice per film. Entries with `kind: "move"` are in-shot tricks done in `build()` / `render()`, not `tr=`.
  A foley sound on the cut (a clay splat on a smear, a whoosh on a throw) smooths it a lot.
- **Signature transitions and textures take this film's colours and subjects**: colours and objects named in the style package (tomato red, big waves, bubbles) are examples; replace them with what's in this film (cream clay smear for a snow film, leaf paper layers in a forest). Every style has at least one signature transition that fits any story; some are conditional (bubbles only underwater, the lamp flood only when the light grows): skip one that doesn't fit the scene.
- **Portrait**: the wide becomes a medium-wide, so the hero easily reaches size; turn horizontal chases into vertical compositions.

## 4. Acting: anticipation, action, follow-through

- **Anticipation**: crouch before a jump, swing back before a throw. At least 1 drawing, held 2–4 frames.
- **Action**: fast, one drawing each.
- **Follow-through and settle**: squash on landing, tail wags twice, hat bounces. Draw it if possible; code adds decaying oscillation (`amp × exp(−k/τ) × sin(ωk)`) to dangling parts and soft materials only: on a rigid body that reads as rocking, so it tilts one way and holds.
- **The receiver reacts**: what gets hit shakes, what gets landed on sinks then wobbles, what gets startled jumps.
- Cartoon squash and stretch: draw it fully; code adds only ±4–7%.
- **Hero inside a prop** (riding a rocket, climbing into a box, driving): give them their own in-and-out acting (squeeze in, get stuck, poke the head out, pop out, tumble out and get up); otherwise the prop does all the moving and the hero is just a face.
- **Hero can't move yet at the opening** (not awake, not alive): let gravity and the environment move them (topple, spring back segment by segment, blown by wind) with the camera pushing; never open on a dead hold for seconds.
- **When the camera stops, the character carries the hold**: squash lower while charging up, blink, change expression (no per-drawing shaking).
- **Feelings read without words**: every emotional turn (tired, stuck, sad, scared, surprised, glad) shows in the picture at that moment, as if the sound were off. Change the face where the material can; otherwise, and always as well, change the pose enough to read in a wide: head drops, shoulders slump, arms hang, the body sinks or leans, steps slow down. Give that pose its own cells (write the feeling into the sheet's `[action]`: "head hanging, shoulders slumped, arms limp"). A painted or carved face that can't change means the body acts more, not less; the same smile on a character who has just run out of strength reads as happy.

## 5. Never only one thing moving

**Layered action table** (at least three columns filled in every stretch):

| Time | Hero (which sheet, which cells) | Secondary (on the hero) | Environment / side characters | Camera |
|---|---|---|---|---|
| 0–1.5s | walk 0–7 loop | apron strings swing | clouds drift past the window, pot steams | pan right |

- Secondary motion: tail, ears, scarf, hat, backpack. Draw two or three states in the sheet, or small code swings.
- Environment motion (cheap, big payoff): clouds, smoke, steam, grass, leaves, lights, water, distant small characters. Separate small layers, stepped per drawing, tied to beats. Big enough to see (at least a few pixels per drawing).
- **No dead holds and no swaying while standing**: holding a key pose 1–2 s is fine; beyond 2 s (`Timesheet.lint` reports it) make it a live hold: local detail (face-only `~b` variants: blink, open mouth; tail, ears), soft-material breathing, plus the environment moving; a slow push or pan helps but never carries a hold alone. Standing feet stay put; a reaction's poses play once and hold on the last (pose to pose, fast in slow out, `ts.act`); never cycle between front, lean-left and lean-right poses or write back-and-forth position formulas. Something moves from frame 0; end on a lingering motion.

## 6. Image list: driven by the scenes

One distinct action = one 8-cell sheet; never mix two actions in one sheet. How many of each per film length: the "asset minimums" table in SKILL.md (the only place with counts). What each kind is for:

- character sheets: hero and side characters
- backgrounds: one per camera, **a different view**, not the same composition enlarged (front wide, side or reverse, close-up); one version per state of anything that changes
- **8-cell action sheets**: one per action; 2×2 close-up sheets: key reactions and the payoff
- props, **fx sheets** (splashes, smoke, debris, transitions in the style's material) Save on **regenerations**: storyboard before action sheets, and spell out all 8 cells before generating each.

**One place, one set**: list the story's places; generate a wide main background for each, and generate every other view of that place with the main background as reference (prompts.md, "Backgrounds"). Every view of one place shares recognisable ground colour and texture and landmarks (that big tree, that rock, that path), so a cut never reads as a new place. Change sets only when the story really goes somewhere else; never borrow another place's backgrounds, not even for close shots.

**Prop-as-actor scenes** (rocket launch, wick burning down, door opening by itself) need no action sheet: rigid animation (move, rotate, shake) + a prop image of that prop (several states) + fx sheet (exhaust, smoke, flame). "One sheet per action" counts only character actions; each prop state gets a prop image, each effect an fx sheet.

**Fix facing and path before generating sheets**: for every shot state the camera height, which way the hero faces and where they go ("eye level; facing right, from bottom left to the front door on the right"). All sheets of one scene share the facing (write "facing right" in the action); carried or held things are on the same side; cuts never flip facing. Make the story's verbs happen fully on screen: a jump has visible air, "going home" reaches the door, no walking on the spot.

**Draw the payoff into the artwork**: the final moment (an apple stuck on the spines, a pancake landing on a plate) is what the audience remembers; give it a close shot and generate artwork with the character and the object together. A separate prop pasted on by code doesn't read as "stuck on" or "inside". The object's path from A to B stays continuous across cuts: it can't be back at the start after a cut.

**Characters in contact** (sharing a scarf, hiding behind the hero, sitting on a lily pad, standing in a friend's hands): draw them in the same cell of one sheet, never two layers pushed together. References: every character sheet involved plus the prop image; `[action]` says "in every cell the two characters are touching, joined as one unit" and states who is left, who is right and their height ratio. `check` and `slice` with `--group grid`.

## 7. Self-check the director's plan

- [ ] Events: a new event every 1–1.5 s; a twist and a payoff; someone or something to interact with
- [ ] Contact beats listed: every moment a character stands, steps, sits or climbs on something other than the floor, or holds, pushes or turns a part; each has its support drawn in the same cell at medium-close and closer, and a still planned to check it
- [ ] Story: the skeleton for the length, every part with its seconds, each caused by the one before; want set up first, answered by the payoff
- [ ] Narration (if any): at most 60% of the story time (per 30 s about zh 60–90 characters / en 40–55 words, 4–6 lines), not repeating the picture; the twist and one more 2 s+ stretch without narration. With or without narration: every beat and every feeling reads without words
- [ ] Shot list: every cut has a reason (new place / close-up detail / new view for a reaction); no size-only cut in the same place and view; with narration every line falls in a shot; every camera has its own background; one set per place, other views generated with the main background as reference
- [ ] Hero size: opening and payoff wides ≥ 33%; at most 2 extreme-wides, route only; distant acting has an eye-level medium; hero-in-prop scenes have in-and-out acting
- [ ] Payoff: readable (big enough in the wide, or a close-up); one artwork has the character and the key prop together
- [ ] Layered action table: at least three columns in every stretch; nothing carried by one long-held cell
- [ ] Facing and path: every shot states facing and from/to; sheets agree on facing, no flips at cuts; key verbs (jump, reach, catch) fully shown
- [ ] Image list: one sheet per distinct action; effects and state changes are all generated images
