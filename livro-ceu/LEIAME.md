# Fábrica de Autores · arte do livro formato Céu

Fundos fixos (200 x 200 mm, 2362 px) que a **Bia 07 — Montar o livro** coloca atrás de cada página no Google Slides.
Os textos, desenhos, fotos e o logo do colégio entram por cima, nas caixas definidas em `fundos.py`.

- `capa`, `contra`, `p01`: páginas cheias (céu, estrelas, nuvens).
- `pNN_dig` / `pNN_let`: páginas de texto para a opção digitada e para a opção com a letra da criança.
- Os demais: miolo em fundo branco com mini desenhos.

Refazer: `python3 -I fundos.py <saida> <pasta de fontes> <pasta do arte_ceu.py>`.
