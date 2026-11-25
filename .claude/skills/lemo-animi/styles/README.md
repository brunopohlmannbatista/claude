# Built-in styles

`python ../scripts/animi.py styles --lang en` lists them with their one-liners, in the order of `num` in each `style.json`. Each folder is a style package (structure: `../references/new-style.md`, section 2):

- `_common/`: prompt templates and bans shared by every style
- `_template/`: template for a new style package
- `<id>/`: one built-in style. `STYLE.md` holds only what this material changes; rules shared by every style live in `../references/`.
