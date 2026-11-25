# Pip Flies — production log

Style: felt (Needle-felt Stop-motion) · 40 s · landscape 1920×1080 · no narration · no title/end cards · no preview.
User request: "faça um desenho de um pinguim aprendendo dentro da sala de aula" (a penguin learning in a classroom).
Image tool: Higgsfield `gpt_image_2_6` via MCP (user's choice; experimental, styles not tuned for it). Prompts still come
from `animi.py prompt`; transparent assets requested with `background: transparent`.

## 1. Director's plan

**Logline**: On a snowy night at a little felt school, a penguin chick tries again and again to fly in the owl
teacher's flying lesson, fails, and then finds his own way to fly: belly-sliding down the moonlit hill.

**Want**: Pip wants to fly like the teacher (set up in the first 5 s). **Payoff**: he "flies" his own way — faster than
the owl — answering the want with something better.

### Story skeleton (40 s, no cards)

| Part | Seconds | What happens | Caused by |
|---|---|---|---|
| Setup | 0–5.5 | Owl teacher flaps and hovers in front of the blank chalkboard; Pip watches, bouncing with excitement; owl lands and points at Pip: your turn | — |
| Try 1 | 5.5–10.5 | Pip flaps as hard as he can: tiny hop, plops down on his bottom | the owl's demonstration |
| Try 2 | 10.5–17.5 | Pip climbs onto a stool and leaps off, wings out — belly-flop on the rug, wool puff | flapping on the floor wasn't enough height |
| Try 3 | 17.5–24 | Pip takes a long run, flapping, leaps — lands on his belly and slides fast across the polished floor to the window wall | the stool wasn't enough speed |
| Low point | 24–28 | Sitting under the window, head hanging, wings limp | three failures |
| Turn | 28–31 | He looks up through the window at the moonlit snowy hill, eyes go wide: an idea | the fast belly slide of try 3 |
| Payoff | 31–37.5 | Outside: Pip belly-slides down the snowy hill, wings spread like flying, the owl flies above trying to keep up | the idea |
| Button | 37.5–40 | At the bottom Pip lies in the snow beaming, wings spread; the owl lands beside him with a nod | the slide |

Events (target ≥ 27, one per 1–1.5 s): owl flaps up (0.3), Pip looks up (0.8), owl hovers (1.5), Pip bounces (2.2),
snow drifts past window (all through), owl lands (3.2), owl points (4.2), Pip nods/gets ready (5.0), crouch (5.8),
flaps (6.4), hop (7.2), plops down (8.0), owl reacts (8.6), Pip blinks (9.6), cut: standing on stool (10.5), crouch
(11.5), leap (12.2), airborne (12.8), belly flop + puff (13.4), lies flat (14.5), lifts head (15.8), cut: run start
(17.5), run flapping (18.4), leap (19.6), belly landing (20.2), slide (20.8), bump into wall (22.6), cut: sits head down
(24.0), sigh/droop (25.5), blink (27.0), looks up (28.0), eyes wide (29.0), determined (30.2), cut: slide downhill (31.0),
snow spray (31.6), owl flies above (32.5), owl looks surprised (34.0), Pip passes camera (35.5), cut: lying in snow
beaming (37.5), owl lands beside (38.4), nod (39.2). ≈ 40 events.

### Shot list

| # | Name | Time | Place / view | Size | Background | What we see | Why cut | In-shot move | Transition |
|---|---|---|---|---|---|---|---|---|---|
| 0 | lesson | 0–10.5 s | classroom / front | wide | bg_class_wide | owl demonstrates, Pip watches, owl points, try 1 | — | very slow push toward Pip from 6 s | picture from frame one |
| 1 | stool | 10.5–17.5 s | classroom / reverse | medium | bg_class_corner | try 2: stool leap and belly-flop | new view (back corner of the room) | static, tiny push on the flop | hard cut on the leap start |
| 2 | run | 17.5–24 s | classroom / side | wide | bg_class_floor | try 3: run, leap, belly slide to the window wall | new view along the floor | slow pan right following the slide | hard cut |
| 3 | window | 24–31 s | classroom / window | medium-close | bg_class_window | low point and the idea, snowy hill seen through the window | true close-up (hero > 2× previous) | slow push in | hard cut |
| 4 | hill | 31–37.5 s | hill / front | wide | bg_hill_wide | the slide down the hill, owl above, snowfall | new place | pan following Pip | hard cut on action (eyes wide → he's already sliding) |
| 5 | landing | 37.5–40 s | hill / bottom | medium-close | bg_hill_bottom | lying in the snow beaming, owl lands beside | new view at the bottom of the hill | still | hard cut |

Facing and path: Pip faces **right** in every shot and travels left → right (shot 2 slides to the right wall; shot 4
slides from upper left down to lower right). The owl is always on the left of Pip. Camera at Pip's eye level (low,
tabletop), except the hill wide which looks slightly up the slope.

### Layered action table

| Time | Hero | Secondary on hero | Environment / side characters | Camera |
|---|---|---|---|---|
| 0–5.5 | pip_look: watch → bounce → ready | red scarf ends swing | owl_fly flap/hover/land/point; snow falling outside window | static |
| 5.5–10.5 | pip_flap: crouch, flap, hop, plop | scarf flips up and settles | owl idle breathing, owl reaction cell | slow push in |
| 10.5–17.5 | pip_stool: stand on stool, leap, flop, lift head | scarf lags | wool puff fx at the flop; snow behind the window | static, jolt on flop |
| 17.5–24 | pip_run: run flapping, leap, belly slide, bump | scarf streams back | puff fx on landing; snow beyond window | pan right |
| 24–31 | close_sad: head down → looks up → eyes wide → determined | breathing idle | snow falling past the window (particles), moonlit hill outside | slow push in |
| 31–37.5 | pip_slide: belly-slide cycle | scarf streaming | owl_fly above; snow spray fx; heavy snowfall | pan right |
| 37.5–40 | close_joy: lying beaming, owl beside | breathing idle | snowfall | static |

### Image list (target 20–26)

| Image | Kind | Notes |
|---|---|---|
| char_pip | character | hero: small felt penguin chick, red knitted scarf |
| char_owl | character | teacher: round felt owl, 1.5× Pip's height, small round spectacles, mustard-yellow knitted vest |
| bg_class_wide | bg wide (main, classroom) | front: blank dark chalkboard left, teacher's little wooden desk, window right with snowy night, warm lamp |
| bg_class_corner | bg medium (ref: class wide) | back corner: bookshelf, rug, a small wooden stool |
| bg_class_floor | bg wide (ref: class wide) | side view along the polished wooden floor to the window wall on the right |
| bg_class_window | bg medium-close (ref: class wide) | under the window, moonlit snowy hill outside |
| bg_hill_wide | bg wide (main, hill) | moonlit snowy slope from upper left to lower right, school cabin with a lit window at the top |
| bg_hill_bottom | bg medium-close (ref: hill wide) | bottom of the hill, soft snow, the slope rising behind |
| sheet_owl_fly | sheet8 | owl flap / hover / land / point |
| sheet_pip_look | sheet8 | Pip watching, bouncing, getting ready |
| sheet_pip_flap | sheet8 | try 1 |
| sheet_pip_stool | sheet8 | try 2, stool drawn in every cell |
| sheet_pip_run | sheet8 | try 3 run → leap → belly slide |
| sheet_pip_slide | sheet8 | belly-slide cycle downhill |
| close_sad | sheet4 | low point → idea |
| close_joy | sheet4 | payoff, Pip and owl together |
| fx_snow | fx | 8 opaque wool snow puffs (particles) |
| fx_puff | fx | wool puff burst for landings, 8 stages |
| fx_spray | fx | snow spray behind the slide, 8 stages |

## 2. Image log

All generated with Higgsfield `gpt_image_2_6` (quality high, 2k), prompts from `animi.py prompt felt …`; job ids in
`work/jobs.txt`. 21 images generated, 1 regenerated as a different design (stool).

| Image | Result |
|---|---|
| char_pip, char_owl | first try; clean alpha, on-model |
| bg_class_wide, bg_hill_wide | first try (main backgrounds) |
| bg_class_corner, bg_class_floor, bg_class_window (ref bg_class_wide) | first try; same walls/floor, clearly different camera |
| bg_hill_bottom (ref bg_hill_wide) | first try; composition close to the wide (similarity 0.86) but camera at snow level, hero ~2× bigger — cut_ok |
| sheet_owl_fly, sheet_pip_look, sheet_pip_flap, sheet_pip_run, sheet_pip_slide | first try; only "airborne" ground-line warnings (intended) |
| sheet_pip_stool → `_bad` | stool drawn into every cell at a different size/place → it would jump between cells. Replaced by sheet_pip_jump (invisible stool) + prop_stool (one fixed stool), the documented "static support" method |
| sheet_pip_jump, prop_stool | first try |
| close_sad, close_joy | first try (Pip stands rather than sits in close_sad — reads fine) |
| fx_snow, fx_puff, fx_spray | first try |

Notes: the look sheet draws Pip facing right, so the owl stands on Pip's right (owl sheet mirrored, front-lit, so the
mirror is safe) and Pip faces right in every shot.

## 3. Review rounds

- **v1**: liveness warnings at 8.5–12 s (Pip sitting, then standing on stool), 14.4–16.7 s (lying after flop),
  22.3–28.4 s (end of slide + sad window). Fix: owl "try again" gesture, shorter holds, bigger snow behind the window,
  a sigh-blink in the sad beat, determination beat before the run.
- **v2**: run shot opened with Pip cut by the left frame edge (cut sheet). Window idea held 2.4 s. Fix: start x moved
  right, window shot shortened (30.2 s), hill shot lengthened, Pip leans toward the window on the idea.
- **v3** (delivered): remaining liveness WARNs, all mild and listed as known: 8.6–11.3 s (puzzled sit, owl gesture,
  Pip on the stool), 22.0–24.0 s (stopped at the wall → sad start), 25.0–27.8 s (the deliberate quiet low point before
  the turn; score silent by design).

## 4. Must-pass verdicts (v3)

| # | Item | Verdict |
|---|---|---|
| 1 | Shots | pass — 6 shots, wide/medium/medium-close, shots_lint OK |
| 2 | Hero size | pass — 35.9 / 38.0 (min .33, lying half the shot) / 44.9 / 64.3 / 39.8 / 69.5 % |
| 3 | No dead holds | known issue — 3 mild liveness WARNs listed above; Timesheet.lint OK, repeat_report OK |
| 4 | Effects generated | pass — puff, spray, snow all fx sheets |
| 5 | No glitches | pass on selfcheck sheets (stool fixed as one prop; facing right throughout) |
| 6 | Sound | pass (measured) — -14.1 LUFS, TP -1.7 dBTP, score + 44 foley cues on contact drawings. Listening: not listened by the agent |
| 7 | Subtitles | n/a (no narration) |
| 8 | Length | pass — 40.00 s, 960 frames, audio track present |
| 9 | No AI text/logos | pass — blank chalkboard, clock without numbers |
| 10 | Reviewed and fixed | pass — 3 rounds above |
| 11 | No jump/zoom cuts | pass — hill→landing checked by eye (cut_ok), classroom views all different directions |
| 12 | Payoff readable | pass — medium-close of Pip lying in the snow beaming, owl landing behind |
| 13 | Enough assets | pass — 6 backgrounds, 7 action sheets, 2 close-up sheets, 3 fx, 1 prop (21 images) |
| 14 | Visible | pass — too dark: none |
| 15 | Text | n/a (no cards) |
| 16 | No placeholders | pass — out/pip.mp4 is the final render |

## 5. Self-assessment

4/5. Least happy with: the slide cells read a little upright (sheet drawn level, rotated 15° in code); the window low
point is quiet for ~2.8 s; the owl's flapping is a simple two-cell hover.
