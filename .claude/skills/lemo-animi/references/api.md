# Function reference

Images are float32 RGB numpy arrays in 0–1; coordinates are pixels; a "drawing" is one entry in the timesheet (on twos: 1 drawing = 2 frames).
Details are in each function's docstring (`$PY -c "import sys; sys.path.insert(0,'$S'); import animi; help(animi.place_at)"`).

## animi.py: assets

| Function / command | Does |
|---|---|
| `load_rgba(p, clean=False)` -> `(I, a)` | Read a PNG; `a` is the 0–1 alpha on a transparent background, else `None`. `clean=True` removes haze first |
| `check_sheet(png, n=8, rows=2, cols=4, out=None, group='subject', allow_edge=None, clean=False, float_=False)` | QC a action sheet: subject count, transparent edges, size spread, ground line, edge contact, stray fragments -> `{'status', 'messages', ...}` |
| `slice_subjects(png, n, rows, cols, outdir, prefix, fragments='keep', group='subject', clean=False)` | Slice by each subject's "territory" into RGBA cells on one canvas, ground lines aligned -> `(paths, info)`. `fragments='drop'` removes stray symbol fragments the model drew |
| `clean_alpha(a, lo=225, hi=248, min_area=400)` / `animi.py clean in.png out.png` | Remove semi-transparent haze (shadows or backing paper the model drew): stretch alpha over [lo, hi], drop small fragments (fx sheets: `--min-area 20`) |
| `haze_ratio(a)` | Share of semi-transparent pixels; > 5% is usually haze |
| `anchors(cells_dir, prefix=, save=)` -> `Anchors` | Per-cell anchors: `foot_y`, `body_x`, `bottom_x`, `bbox`, `height`, `width` |
| `load_anchors(path)` | Read back the saved anchors json |
| `A.scale_ref(target_h, cell)` | Scale that makes one cell (the standing-straight one) `target_h` tall; use it for every sheet of a character |
| `preview_cells(cells_dir, out, prefix=, A=)` | Preview of cells and anchors |
| `asset(path)` / `MISSING` / `missing_report()` | Read an image; if missing use `<name>_bad.png`, else a grey placeholder, and record it in `MISSING` (lint reports it; the film renders as draft only) |

`check` flags (same names on the command line):

| Flag | When |
|---|---|
| `--allow-edge bottom` (`left` `right` `top`; no value = all four) | Subject cut by the image edge on purpose: close-up (face and shoulders only), a hand reaching in from off-frame. Those edges skip the transparency check and touching them is not a FAIL |
| `--clean` | Reports opaque edges but the preview has a transparent background and mentions haze: check again after de-hazing; if it passes, slice the de-hazed file from `animi.py clean` |
| `--group grid` | Slice by equal grid: fx sheets (several pieces per cell), close-up sheets with two separate pieces per cell (two characters, character + prop), subjects reaching into the next cell. Each cell keeps its largest piece plus fragments mostly inside it; parts crossing into a neighbour are cut at the grid line |
| `--float` | Floating or top-down characters: skip the ground-line check |

## animi.py: timesheet

```python
ts = animi.Timesheet(fps=24, on=STYLE['on'], seed=7)
ts.add('toss_2', holds=4, x=900, beat='stop')                 # one drawing: cell, hold in frames (default on), any state
ts.cycle([f'walk_{k}' for k in range(8)], 24, x=lambda k: 200 + k * 18, beat='walk')   # 24-drawing cycle; state may be a function of k
ts.add('close_1~b', holds=6, idle=True, cells=['friend_act_2'], live='slow push-in')    # variant cell, co-star in frame, reviewed live hold
ts.extend(12)                                                 # 12 extra frames at the end
```

- `ts.pics[i]` = `(cell, frames, state dict)`; `ts.n_pics`; `ts.duration()`; `ts.pic_start(i)` (first frame of drawing i)
- `ts.jitter(pic, amp)` -> `(dx, dy)`; `ts.jscale(pic, amp)`; `ts.jrot(pic, amp)` (degrees); `ts.flicker(pic, amp)`; `ts.seed(pic)`: all per drawing
- `ts.idle(pic, amp=0.012, rigid=False, salt=)` -> `place_at` args: idle breathing for soft materials (`sy`, `sx`); empty for rigid ones (no rotation, no sideways move)
- `ts.lint(max_hold=2.0, drawn=None)`: reports when everything drawn in frame holds too long. "What is drawn" = cell name (`a+b`, `@pos`, `~variant` all count as different) + state `cells=[…]`; `drawn={pic: what}` wins (the template's board passes it); state `live='reason'` marks a hold as reviewed
- `ts.pingpong()`: finds "standing carousel" (within a stretch of constant `x`, the body cell switches away and back twice or more; `~` variants excluded); `lint` prints it as a reminder
- `ts.carry(last, d)`: keep a shot "acting": `(cell, frames, state)` of the d-th drawing after `last` (cells keep cycling, numeric state extrapolated from the last two); used by `mix(live=True)`
- `cell_base(name)`: strip `+…`, `@…`, `~…` suffixes to get the real cell name

## animi.py: placing, alignment, shadows, occlusion

| Function | Does |
|---|---|
| `place_at(frame, c, x, ground_y, scale, info=, anchor='body', rot=0, sx=1, sy=1, pivot='foot', alpha=1, blur=0, flip=False, motion=0, ref=None, gain=None, dx=0, dy=0)` | Put a cell's anchor at (x, ground_y). `anchor`: `body` / `bottom20` / `bbox` / `base` (midpoint of the bottom strip: something standing inside a prop) / 0–1. `ref=(px, py)`: any point in the cell lands on (x, y) and rotation pivots on it; `gain`: per-column brightness factor (number or a function from `floor_light`). Returns the on-frame box |
| `core_anchor(a)` / `set_core(info, a)` | Body core of a top-down or diagonally walking puppet (legs and antennae removed): `cx, cy` as anchor, `len` = body long axis (measures hero size) |
| `to_frame(ref, pt, x, y, s, rot)` | Where another cell point `pt` lands on frame when placed by `ref` (back-solve hand-offs) |
| `cell_tip(a, direction=(1, -0.6))` | Farthest cell point in a direction: beak tip, outstretched hand, raised hand |
| `part_refs(cells, color)` | Align a sheet's cells on a prop: per-cell centre of that part -> `place_at(ref=)`, no jump on cell change |
| `part_center(c, color, round_only=False)` | Find a part by colour (fruit, lantern, button) -> `(cx, cy, box)`; `round_only` keeps near-round blobs |
| `contact_shadow(frame, x, ground_y, width, lift=0, strength=0.45, offset=(0, 0))` | Elliptical contact shadow, smaller and fainter with height |
| `relief_shadow(frame, c, x, y, s, info, lift=0, cfg=)` | Thin hugging shadow (flat styles): silhouette offset a few px, blurred, darkened; lift 0–1 off the paper |
| `cast_shadow(frame, c, x, y, s, info, lift=0, cfg=)` | Hard-light cast shadow: silhouette squashed at the ground line, thrown diagonally (`light=(kx, ky)`) |
| `shadow(frame, c, x, y, s, info, style=STYLE, lift=0, shadow_w=, shadow_off=, shadow_k=)` | Shadow by the style's `preset.shadow.kind` (contact / relief / cast / none); call before `place_at`. Contact width, offset (share of character width) and strength can be overridden per call |
| `prop_spot(c, color, tol=0.18, top_frac=1, body=0.75)` | Find a held container by colour -> `rim` (rim endpoints), `depth`, `mask` (compositing.md §7½) |
| `spot_board(items, out)` | Overlay measured rims and masks on the cells in one image; look before using the numbers |
| `inner_mask(c, color)` / `fill_container(body, inner, item, fill=0.9)` | The container's inside / squash an item to the rim ellipse and draw it only inside -> new cell (compositing.md §7½) |
| `put_by_rim(frame, c, rim_cell, rim_frame)` / `rim_to_frame(rim, ref, x, y, s, rot)` | Place a cell by its rim endpoints (pan body back onto the held pan) / map a cell rim to frame |
| `color_mask(img, rule)` / `only_in(frame, drawn, mask)` | Mask from the background by colour (sky, water) / keep only what is drawn inside the mask (sun behind leaves) |
| `holdout(frame, bg_layer, mask, x0, y0)` | Paste the background's front-edge occluder back on top |
| `poly_mask(shape, pts)` / `rect_mask(...)` | Feathered polygon / rectangle mask |
| `Layer(h, w)` / `clip_layer(layer, keep_mask)` | Temp layer: draw on it, clip, then composite |
| `sandwich_check(A_obj, occ)` / `occ_overlay(bg, occ, out)` | Occlusion self-checks |
| `multiply(frame, img, x0, y0, k)` | Multiply blend (ink, shadow texture) |

## animi.py: character lighting

| Function | Does |
|---|---|
| `char_light(c, cfg, scale=1, warm=0, warm_side='left', gain=1, flip=False)` | Grade a cell to the scene light -> new `(C, a, M)` (cached): edge decontamination, tinted exposure, side light, warm light, rim light. `cfg` = `STYLE['light']` |
| `floor_light(plate, gy, cam, cfg, plate2=, mix=)` | Measure the light zone along the background's ground line -> function for `place_at(gain=)`: the character darkens leaving the light; `plate2 + mix` blends two background versions by position (light spreading) |
| `recolor(img, hue=deg, sat=factor, only=src_hue, tol=20)` | Recolour by hue (`(C, a, M)` or RGB in, same type out): rotate hue by `hue` degrees, multiply saturation by `sat`; `only=0` changes only saturated pixels near that hue (just the red scarf). Siblings in a group: in the template's `load()` write `cells['walk_3~b'] = animi.recolor(cells['walk_3'], hue=120)`, then use `'walk_3~b'` in the timesheet |
| `darken(frame, dark)` | Darken the whole scene (`dark` = number or `{k, tint}`, cool bias); in template SHOTS write `dark=0.6` |
| `warm_glow(frame, x, y, r, k=0.3, col=)` | Additive warm light: lantern, candle, window, firefly (add after darkening; no flicker) |
| `self_glow(frame, c, X, Y, s, boost=1.5, halo=40)` | Self-lit effect (flame): brighten + shape-following halo |
| `light_flood(cam, dim, bright, cx, cy, R)` / `flood_mask(...)` | Light spreading: the bright background grows in a circle from the source -> `(frame, mix)`; `mix` goes to `floor_light` |
| `light_pool(cam, cx, cy, r, lo=0.22, sq=0.55)` | Brightness map of a light pool (H×W); multiply background and character by the same one |
| `decontam(C, a, r)` / `rim_mask(a, d, soft)` | Edge decontamination and rim-light position (two steps inside `char_light`) |

The template's `put(frame, D, cam, name, x, y, s, pic, ts, sh=sh, light=dict(warm=0.6), jit=1, salt=, shade=, rot=0)` is already wired: style shadow,
`char_light` (`scale` set automatically from the sheets' sc ratio; `warm`, `gain` and any preset.light key can be overridden per call), `floor_light` when `light.floor` exists,
per-drawing jitter off by default (all style `jitter_*` are 0; the `jit` factor stays unused), body-core placement for top-down styles. `rot=deg`: extra tilt for this drawing (a `~b` variant that should "tilt a bit" uses `rot=2`; the template passes
`rot=2` from timesheet state). If `name` has a suffix like `~b` and `D['cells']` has a cell registered under that name (e.g. from `recolor`), that cell is drawn; otherwise the base cell. Using the functions directly:

```python
c = animi.char_light(cel['walk_3'], STYLE['light'], warm=0.6)               # warm on the lantern side
animi.place_at(frame, c, x, y, s, info=A['walk_3'], gain=animi.floor_light(plate, gy, cam, STYLE['light']))
```

## animi.py: camera, checks

| Function | Does |
|---|---|
| `SIZES` | `{'landscape': (1920, 1080), 'portrait': (1080, 1920), 'square': (1080, 1080)}` |
| `cam_at(SHOTS, pic, W, H)` -> `(cam, shot)` | Camera for this drawing; `cam.plate(img, par)` frames the background, `cam.xy(x, y, par)` stage -> frame, `cam.k(par)` scale. After it the template shifts `cam.cx / cy` by the shot's `sway=(px, period in drawings)` (whole set drifts gently: underwater, wind) and the timesheet state's `shake=px` (small whole-frame jolt for the 2–3 impact drawings) |
| `shots_lint(SHOTS, ts, plates=, hero=, notes=, push_max=)` | Flags: push beyond `push_max` (shot `push_ok='reason'` exempt); zoom cuts (same `place` and `view`, hard cut changing only size; a cut marked close-up whose hero is < 2× bigger; same place switching shot size back and forth 3+ times); shot length (static 10 s, moving 14 s); number and position of extreme-wides; jump cuts (same background, or two similar ones, hero size differing ≥ 1.5× — covered by a transition or `cut_ok` exempt); reusing a background in non-adjacent shots (reminder) |
| `plate_similarity(a, b)` | How alike two backgrounds are (0–1); ≥ 0.75 is basically the same camera position |
| `MIN_HERO` / `KEY_WIDE` / `hero_need(SHOTS, j, style)` | Minimum hero height: extreme-wide 15%, wide 30%, medium 40%, medium-close 60%; opening and landing wides 33%; a shot's `min` wins |
| `hero_report(SHOTS, heights, short, style)` -> `(too-small shots, per-shot median)` | Hero size check (template board / full render run it) |
| `size_report(SHOTS, ts, heights, med)` | Hero size continuity between shots: same shot size differing ≥ 1.3×, tighter shot size without a bigger hero (shot `size_ok='reason'` exempt); height jump ≥ 20% when switching sheets inside a shot (reminder). Template board / full render run it |
| `style_lint(style_id)` / `animi.py stylecheck [id…]` | Style package basics: complete preset (on, rigid, idle, push_max, shadow, light, grade), `jitter_*`, `flicker`, `grade.grain` all 0, complete `title` (color, plate, motion, sound). Template lint runs it |
| `repeat_report(SHOTS, ts)` | Action repetition: the same action (one sheet used consecutively, ≥ 3 cells in order) played verbatim more than twice in the film; a loop over 6 s, a 2–3-cell loop over 3 s (state `rep_ok='reason'` exempt). Template lint runs it |
| `hero_box(box, info, scale=, at=)` / `set_body(info, c, drop)` | Measure the character only: store a box without prop / hands in the anchors and use it for size; with `core` (top-down) measure body length |
| `shot_table(SHOTS, ts)` / `write_shots(path, SHOTS, ts)` | Shot list `{dur, fps, shots: [{i, t, t1, at, name, size, bg}]}`; template lint writes `work/shots.json`, the full render `out/<NAME>.shots.json` |
| `brightness(frame, box)` / `dark_spans(samples, th)` / `darkness(mp4, hero_json)` | Too-dark check: whole frame < 0.03 or hero region < 0.06 for ≥ 0.3 s; thresholds in `preset.dark` |
| `liveness(mp4, out=)` / `animi.py live` | Find stretches where the whole screen barely moves |

## animi.py: transitions, finishing, subtitles

| Function | Does |
|---|---|
| `transition(frame, kind, k, color, center)` | `iris_in/out`, `dip_in/out`, `wipe_l/r/u/d` (add `_in`); k = progress 0–1 |
| `tr_spec(tr, style_info, assets)` / `shot_tr(sh, style_info, assets)` | SHOTS `tr='style transition id'` or `tr=dict(kind=…)` -> normalised params (incl. before / after drawings); `shot_tr` reads a shot's `tr=` / `smear=` (uses direction and wobble of the style's smear entry) / `mix=` (`live=True` keeps acting). Entries with `kind: move` are not transitions; using one as `tr=` warns |
| `load_tr_assets(style_info, src, cells)` / `tr_missing(SHOTS, style_info, assets)` | Load transition assets named in params from `src/` and sliced cells (template `load()` calls it) / which assets the SHOTS transitions lack (template lint reports) |
| `cut_fx(q, d, cur, old)` | Draw one style transition (`smear` / `page` / `slide` / `stitch` / `curtain` / `wipe` / `glow` / `mix` / `hinge`; family params in compositing.md §6 "Transitions"); d = drawings from the cut (negative before). Template `draw()` does it automatically, before grading |
| `hinge(frame, sprite, u, hinge='lr')` | Hinge flip on its own: a board swings in in perspective, hinged on a frame edge; u = 1 fully covers |
| `TR_DEFAULT` / `TR_NEEDS_OLD` / `tr_glow(q, d)` | Default drawings per transition; kinds that still need the old frame after the cut; glow amount for `finish` at this drawing of a glow transition |
| `smear(frame, tex, k, origin, seed, wobble, edge='round', shadow=(10, 14, 0.38), fit=False)` | Material smear over the screen: `edge='line'` straight-edge sweep; `shadow` = shadow direction and strength (also edge shading; frontal flat light: `(0, 5, 0.22)`); `fit=True` remaps k when origin is off-frame |
| `finish(frame, ts, pic, STYLE, glow=0)` | Style finish: tilt-shift, grade (style flicker and grain are 0, no flicker); glow 0–1 temporarily boosts bloom |
| `Subtitles(path, style, W, H)` | Burn subtitles (template does it), always at the bottom; `style['plate']` = backing plate; a block with a second language shows two lines on one plate, each on a single line |

## animi.py: styles and prompts

| Function / command | Does |
|---|---|
| `animi.py styles [--lang en]` / `style_ids()` | List the fixed styles (sorted by style.json `num`; number = order); `--lang en` uses English names and descriptions |
| `style_info(id)` | Full style.json |
| `style_preset(id)` | Compositing params: `on`, `jitter_pos`, `jitter_scale`, `jitter_rot`, `flicker`, `push_max`, `grade`, `light`, `shadow`, `rigid`, `idle`, `dark`, `flags` |
| `animi.py prompt <style> <type> <slot file> -o <out> [--size landscape] [--set name=value]` / `build_prompt(...)` | Build one asset prompt (types: character / sheet8 / sheet4 / prop / fx / bg / layer = transparent set layer / texture = full-frame material close-up); missing slots are an error; a `[[ … ]]` optional segment with an unfilled slot is dropped whole |
| `prompt_parts(id)` / `fill_parts(text, id)` | Replaceable parts in templates (`<<view>>` `<<held_prop>>` `<<ground_line>>` `<<sheet_ground_line>>` `<<prop_view>>`): defaults in `_common/_parts.txt`, a style's `prompts/_parts.txt` replaces them whole |

## layers.py: layered sets and environment

| Function | Does |
|---|---|
| `load_layer(path)` | Transparent set layer (a full strip of foreground paper waves, a row of trees) -> premultiplied RGBA, trimmed, transparent padding on top |
| `tile_layer(L, n)` / `taper_layer(L)` | Extend sideways (no edge on pans) / taper both ends (no wall on sweeps) |
| `put_layer(frame, cam, L, par, x0, y_top, width, sy=1, dy=0, shadow=0.38, mul=1)` | Composite with parallax; `sy` stands it up (bottom edge as pivot), `dy` bobs, shadow under the layer. Template SHOTS `layers=[dict(name=, par=, x0=, y_top=, width=, front=, bob=, sy=, dy=)]` draws it; `sy` / `dy` / `x0` may be `lambda k: …` (k = drawing index in the shot from 0: paper layer standing up, set layer sliding in); `name` must be in `load()`'s `layers`, otherwise lint reports |
| `Sprites(cells, info)` / `spr.put(frame, name, X, Y, s, rot, at='center'|'root'|0–1)` | Environment sprites cached per scale step; fast for a dozen per frame; `at` = which point is placed |
| `sway(pic, amp, per, phase)` / `bob(pic, amp, per, phase)` | Swing angle / vertical bob, per drawing |
| `plants(frame, spr, cam, items, pic, wind=0, front=None)` | Clumps swing around their roots; strong wind switches to bent drawings (`bent=[half, full]`); back rows drawn before the character, front rows after |
| `Particles(cells, mode='fall'|'rise', n=150, blur=px)` / `.draw(frame, spr, pic, amount, wind, cam, vents)` | fx-sheet cells as particles: full-screen fall (snow, petals, confetti) or rising from vents (bubbles, steam, fireflies). `blur=3` blurs the whole layer (close-up bubbles, snow; also in rise mode); fall mode also takes a triple `(far, mid, near)` |
| `find_glints(plate, region, rule)` / `glints(img, spots, pic, mode)` / `glint_board(plate, spots, out)` | Find small bright spots in the background (foil stars, bulbs) and sway / twinkle / chase them; check the board first |
| `loop_fx(frame, spr, cam, pts, pic, cells, size)` | Loop an fx sheet at points with offset phases (star twinkle, distant smoke) |
| `Flock(cycles, n, hold=2)` / `.ring(pic, cx, cy, rx, ry)` / `.scatter(pic, t, origin)` / `.queue(pic, x0, y, gap, speed, lead=, lead_s=, lead_gap=, lead_hold=)` / `draw_flock(frame, spr, cam, items, size, front=)` | A group of small things: circling, scattering when startled, queueing (`lead` cycles the leader's cells; `lead_hold` = drawings per leader cell, default `hold`); split before / after the hero by depth |
| `Stream(cells, n=30, dir=-1)` / `.draw(frame, spr, cam, d, amount)` | Debris rushing along the ground (threads in a flood, leaves in wind) |

## bookends.py: title lettering, optional title and end cards

| Function / command | Does |
|---|---|
| `title_tag(text, size, color=None, plate=None, style=None, role='title', lines=None, root=None, sub=None)` -> `Tag` | One title card: Source Han Sans (思源黑体) Bold in a flat colour + style plate (`style.json` `title.plate`: `texture` material close-up (film folder -> style package) or `proc:knit/wood/weave/paper`; `border` solid border). `sub='subtitle'`: a separate coloured strip below (`title.sub`). `role` sets the minimum size (title 200, sub 60, credit 48, at 1080 short side). Missing texture is reported (`MISSING`) |
| `put_tag(frame, tag, cx, cy, alpha=1, lift=0)` | Place with its centre on an integer pixel (no scaling, no rotation); `lift` raises the plate off the table (first two drawings of a drop) |
| `bookends.py <film.mp4> --title T [--sub S] [--credit C] [--end E] [--style id]` / `make(...)` | Add title and end cards -> `<film>-bookends.mp4` + shot list; not part of the default pipeline |
| `bookends.py preview --title T [--credit] [--style] [--bg img] [--out]` | Preview lettering and plate only |

## kit.py

| Function | Does |
|---|---|
| `rd(p)` / `wr(p, f)` | Read / write an image (`wr` creates directories) |
| `sprite(cells, None, name)` | Read a cell -> `(C, a, M)`; RGBA cells use their own alpha |
| `ease(x)` / `ease_in` / `ease_out` / `lerp(a, b, t)` | Easing |
| `hblur(img, L)` / `vblur(img, L)` | Horizontal / vertical motion blur |
| `over(frame, P, A, x0, y0)` | Composite a premultiplied layer |
| `grade(f, ...)` | Grading (normally use `animi.finish` instead) |
| `encode(frames_dir, mp4, fps, crf)` | `f%04d.png` -> mp4 |

Always place cells with `animi.place_at` (by anchor). kit has no bbox placement and no optical-flow interpolation (stop-motion does not interpolate: one drawing is one drawing).

## fx.py

- `font(name, size)`: `'siyuan'` (Source Han Sans Bold: subtitles, titles, all on-screen text), `'hei'`, `'song'`, etc.
- `text(s, font, size, color)` -> text layer; `put(frame, layer, x, y, anchor='lt', alpha)`: small in-scene text such as signs. Titles use `bookends.title_tag`
- Text only. Speed lines, rays, star bursts, debris and similar effects are always generated as fx sheets; there is no code to draw them

## Checks

- `selfcheck.py out/<NAME>.mp4 [--style id]`: sampled review frames + cut-point frames + darkness check (reads `work/hero.json`)

## sound.py and audio/

- `sound.py vo / lint / build / mux / voices / times` (`references/sound.md`)
- `sound.load_sheet(path)`: read the sound sheet with shot-relative times converted to seconds; `sound.parse_t(spec, shots)`: one time (number / `"shot+0.4"` / `"#3-0.2"` / `[shot, offset]`) -> seconds; `sound.auto_foley(d)`: foley from `foley_rules` and timesheet `sfx=`
- The shot list is read from `work/shots.json` (written by `film.py lint`), falling back to `out/<NAME>.shots.json`
- `review.py add / open / notes / reply / wait`: review page (local page: pause the film and leave a note with timecode and shot attached; for characters, register images and leave notes on each; notes arrive in the conversation, no export file; `open --no-browser` only prints the URL, for the built-in browser pane; see workflow.md "Review page")
- `audio/compose.py`: score (`render(plan, style_music, dur)`); `audio/foley.py`: foley (`make(kind, material, v, pitch, d=None)`, d = duration in seconds; `kinds(material, aliases=True)` lists all names incl. aliases; `describe(material)` with descriptions); `audio/sampler.py`: sampled instruments
