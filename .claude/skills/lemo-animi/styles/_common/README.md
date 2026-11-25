# Prompt pieces shared by all styles

`animi.py prompt` assembles the final prompt in this order:

1. `<style>/prompts/anchor.txt`: the style anchor (material, light, palette), identical for every image of the style
2. `_common/<asset type>.txt`: the layout for this asset type (how many cells, transparent background, arrangement)
3. `<style>/prompts/<asset type>.txt`: what this style must watch for with this asset type (optional)
4. `_common/_rules.txt`: shared bans (no text, original characters, ...)

Write slot files and prompt text in English: the final prompt sent to the image model is English.

**Slots** `{character}`: curly braces are slots the agent fills in a slot file (format: `animi.py prompt -h`). An unfilled slot is an error. `{aspect}` comes from `--size` and `{_transparent}` from `_transparent.txt`; you do not fill those. A slot file looks like:

```
[character]
a small round clay mouse in a red apron
[action]
1 standing, 2 crouching to wind up, 3 jumping, ...
```

**Optional segment** `[[ ... ]]`: included only if every slot inside it is filled, otherwise dropped entirely. `sheet8` uses it for a held prop: when the character holds something in the sheet, write `[held_prop]` ("a sky-blue frying pan"); if not, leave it out, and the `<<held_prop>>` sentence is dropped too.

**Replaceable parts** `<<view>>`: the default text lives in `_common/_parts.txt`; an entry with the same name in a style package's `prompts/_parts.txt` (`[view] ...`) replaces it entirely, and an empty entry removes it. Wherever a style differs from the shared layout (view, prop camera), replace a part this way. Never write "this rule replaces the one above" in a style package: both sentences would reach the prompt and contradict each other.

| Part | Template (only used here) | Default | Example: which styles replace it |
|---|---|---|---|
| `<<view>>` | `character` | front, three-quarter, full side profile, back in one row | profile-only styles (shadow puppets), styles shot from directly above (paper-cut bugs) |
| `<<held_prop>>` | `sheet8` (only if `[held_prop]` is filled) | held prop from the same camera as the set | 3D styles state the camera ("camera slightly above the rim; the bowl's opening is a flat ellipse"); flat styles say "flat side-profile outline" |
| `<<ground_line>>` | `sheet8` | standing soles on the same horizontal line, jumps above it | top-down (no ground line: body centres on one line), floating (not touching the ground: body centres aligned) |
| `<<sheet_ground_line>>` | `character` | feet of the four views on the same horizontal line | as above; leave empty if `<<view>>` already says how to align |
| `<<prop_view>>` | `prop` | same viewpoint as the shot it goes into | 3D styles state the camera and what a container's opening looks like ("camera slightly above the table; the pot's opening is a very flat horizontal ellipse"); top-down and flat styles as above |

`layer` (transparent set layer), `bg`, `fx`, `sheet4` and `texture` have no replaceable parts: the layer template already says the camera matches "the set in the reference image"; style-specific notes go in `prompts/layer.txt`.

`anchor.txt` (the style anchor) is prepended to every image, transparent assets included. For light, write only what acts on the set ("the key light on the set comes from ..."); do not write "soft shadows" or "cast shadows": the transparent layouts forbid cast shadows, the two contradict, and the image model adds a shadow patch under the character. Assemble one `character` prompt and read it for contradictory sentences.

| Asset type | What it is | Background | Reference image |
|---|---|---|---|
| `character` | character sheet (four views, or four states if the style replaces them) | transparent | none |
| `sheet8` | action sheet: 8 poses (2 rows × 4) | transparent | the character sheet (for a held prop, also the sheet that already shows it) |
| `sheet4` | close-up sheet: 2×2 medium-close performances (full body by default; crop only for close-ups) | transparent | the character sheet; for a prop in a medium-close shot, its wide-shot source image |
| `prop` | props (one, or several placed apart) | transparent | optional |
| `layer` | transparent set layer: one strip almost as wide as the frame (foreground grass, paper waves, a row of trees), only this layer | transparent | the background of the same scene |
| `texture` | material close-up filling the frame (smear transitions, title-card backing), material on all four edges | opaque | usually none |
| `fx` | 8-cell effect sheet (splashes, smoke, sparks ... made of the style's material) | transparent | none |
| `bg` | the background of one shot (no main character) | opaque | usually none; when a prop in a medium-close shot is the same object as in the wide shot, pass that wide |
