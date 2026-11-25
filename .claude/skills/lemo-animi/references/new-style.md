# Styles outside the list

## 1. The user names a style that isn't listed

1. Tell them it is experimental and results aren't guaranteed. If a fixed style is close, recommend it (embroidery → crochet or cloth doll; Lego → cardboard box or tin).
2. If they insist, create a temporary style package in the film folder, `styles-local/<id>/`, with the structure of `styles/clay/` (§2); in `film.py` and `sound.py` switch the style id to it and point `animi.STYLES_DIR` there: `animi.STYLES_DIR = os.path.join(WK, 'styles-local')`.
3. Do it only if all four hold:
   - the medium is inherently "assembled piece by piece, shot frame by frame": on twos and pose-by-pose changes are part of its character;
   - image generation keeps characters consistent in this style (simple design, fixed palette, clear material texture);
   - assets come out with clean transparent backgrounds (fine fur, translucency, glowing bodies: test one image first);
   - the story doesn't depend on the camera orbiting a character, fine motion of hair or cloth, or real water and fire.
4. Generate one character sheet and one 8-action sheet first and get through QC → slicing → anchors → still frame before generating the rest.
5. Every rule for fixed styles still applies.

## 2. Style package structure

```
styles/<id>/
  STYLE.md        one page: one-liner; best subject, palette, light, camera; good and bad stories; unique tricks; pitfalls; sound.
                  Only what this material changes. Cutting, shot sizes, hero size, acting, live holds, subtitle position,
                  narration length and pace, score structure (silences, energy curve) and loudness are the same for every
                  style (directing.md, sound.md): don't restate them. `stylecheck` flags common restatements
  style.json      the machine-read part (fields below)
  prompts/
    anchor.txt    style anchor: material, light, palette (prepended to every image, transparent assets included). Describe light only
                  in terms that take on the set ("the set's key light comes from the top left"); no "soft shadows" or "cast shadows":
                  transparent-asset templates forbid shadows and the two would conflict
    character.txt sheet8.txt sheet4.txt prop.txt fx.txt bg.txt layer.txt texture.txt
                  what this style needs for each asset type (appended to the common template; delete files you don't need)
    _parts.txt    replaces template parts whole: <<view>> <<held_prop>> <<ground_line>> <<sheet_ground_line>> <<prop_view>>
                  ([name] headers; see styles/_common/README.md; delete parts you don't replace)
  ref/            one example per asset type: character, sheet8, sheet4, prop, fx, layer (styles with layered sets),
                  texture (material close-up: title plate, smear transition texture), bg_wide / bg_mid / bg_close
  poster.jpg      poster (menu and catalogue)
```

`styles/_template/` has this structure; copy it to start. Fill or delete every `<…>` in it.

`style.json` fields:

| Field | Content |
|---|---|
| `id` `num` `name` `en` `line` `line_en` | Menu info: `name` / `line` Chinese display name and one-liner, `en` / `line_en` English ones; `num` only sets the order in `animi.py styles` |
| `best` | Best `subject`, `palette`, `light`, `camera` (what sets styles apart; English values) |
| `good_for` / `bad_for` | Stories it suits / doesn't suit |
| `assets` | Per asset type: `aspect` (`landscape` / `square` / `portrait` / `film` = the film's aspect) and cell count |
| `preset` | Compositing params: `on` (on ones/twos), `jitter_pos`, `jitter_scale`, `jitter_rot`, `flicker` (all always 0: per-drawing wobble and flicker are tiring), `push_max`, `grade` (`tint`, `lift`, `bloom`, `vig`, `sat` …; `grain` always 0: per-drawing grain on a static background is flicker), optional `tilt` (tilt-shift), `gray`, `misreg`; plus the entries below |
| `preset.light` | Character lighting (`animi.char_light`): `decontam`, `tint`, `expo`, `gamma`, `side`, `rim`, `rim_col`, `rim_dir`, `warm_col`, light zone `floor: {lo, gamma}`. Omitted = flat, pasted as is |
| `preset.shadow` | Shadow: `kind` (contact / relief / cast / none; omitted = chosen by `top_down`) and its params (`contact`, `contact_w`, `contact_off` …, compositing.md §3½) |
| `preset.par` | Background parallax (omitted = 0.9; `top_down` defaults to 1; frontal flat styles without depth, such as relief, use 1) |
| `preset.rigid` / `preset.idle` | Rigid materials (wood, tin, cardboard): `true` — no squash, `idle` adds nothing; soft materials: `idle` is the breathing amplitude (default 0.012) |
| `preset.dark` | Too-dark thresholds `{frame, hero, len}` (dark styles may lower them a little, but the hero must stay visible) |
| `flags` | `profile_only` (profile views only), `top_down` (overhead, no perspective; shadow defaults to thin hugging), `tilt_shift`, `hero_min_scale` (discount on minimum hero size: a number applies to wide and extreme-wide only; a dict per shot size, `{"extreme-wide": 0.8}`; never to medium-close) |
| `music` | Instrumentation: `bpm`, `key`, `mode`, `swing`, `progressions`, `roles` (instrument `inst`, octave `oct`, velocity `vel`, rhythm `pattern` for melody / counter / bass / comp / perc, optional `pan` and `legato` ratio), `energy` (which roles join at which energy), `hits` (what each accent uses), `reverb` |
| `foley` | `material`: foley looks up "material_action" first; `kinds` (optional): the style's most-used foley names, starred as recommended by `sound.py kinds <id>`; unknown names warn |
| `voice` | `voice`, `rate`, `pitch`, `tone` (narration tone, for whoever writes the narration) |
| `subtitle` | `font` (siyuan only), `size` (at 1080 short side), `color`, `outline`, `outline_w`, `pos`, `plate` (backing plate `{color, alpha, pad}`; required for bright or busy styles), `en_size` (English size in bilingual subtitles, default 0.72 × the Chinese size) |
| `title` | Title and end cards: `color` (text colour, flat), `plate` (plate `shape` cut / round / stitch / rect / none, `color`, `texture` (material close-up such as the style's `ref/texture.jpg`, or `proc:knit` / `proc:wood` / `proc:weave` / `proc:paper`; never a background image), `texture_k`, `border` (solid border `[width (× text size), colour]`, optional), `stitch`, `rough`, `pad`, `shadow`), `sub` (`color`, `plate` of the separate subtitle strip; omitted = same plate as the title), `sound` (foley when the plate lands), `motion` (how bookends enter: `enter` drop / pop (stands up from its bottom edge: paper, cardboard), `step` interval between letters dropping, `sub_side` side the strip slides in from). Lettering is always Source Han Sans Bold; the style only owns the plate. `title` must be complete so bookends match the style |
| `transitions` | Transitions unique to this style: `id`, `name`, `how` (what to generate and how to use it), `kind` (family: smear / page / slide / stitch / curtain / wipe / glow / mix / hinge; tricks that are not between-shot transitions — action or blocking inside a shot — use `move`), `params` (in/out direction, drawings, wobble, asset names, loaded by name from `src/` and sliced cells by the template). SHOTS `tr='<id>'` uses these params |

When the package is done run `"$PY" "$S/animi.py" stylecheck <style>`: every style shares the same basics (no per-drawing jitter, no whole-frame flicker, complete title cards); a style that fails can't be used.

The common templates and rules live in `styles/_common/`, shared by all styles; don't copy them into a style package.
