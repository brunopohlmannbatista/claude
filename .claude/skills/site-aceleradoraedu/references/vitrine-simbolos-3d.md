# Nova vitrine de produtos e símbolos 3D (em andamento desde 26/11/2026)

O estado completo, as pendências e os prompts estão em `aceleradora-site/CONTINUAR.md`, no repositório `brunopohlmannbatista/claude`. Leia aquele arquivo antes de mexer na vitrine.

## Resumo

- Protótipo privado da nova vitrine: https://claude.ai/artifact/5SRCXyQRVNNKsexoo9Tcu1 (11 cards, 4 filtros por objetivo do lead, menu enxuto).
- 12 símbolos 3D da marca, um por produto, em `aceleradora-site/simbolos-3d/` (`originais/` em JPG 2048 px e `web/` em WebP 512 px).
- Canvas da Dreamina com os símbolos: https://dreamina.capcut.com/ai-tool/ai-canvas/23ff5f4a-0841-4b4e-ab1c-366932d200c3
- Cópia do site no ar: `aceleradora-site/site-atual/index.html`.
- O site no ar ainda não foi alterado.

## Pendências que só o Bruno resolve

1. Preços na vitrine: o protótipo e o site no ar mostram preços; a regra desta skill é sem preços.
2. WhatsApp: o protótipo e o site no ar usam (81) 95168-7966; a regra desta skill é (81) 99536-2170.
3. Aprovação do protótipo com os símbolos.

## Padrão dos símbolos 3D

Para um produto novo, gerar um símbolo no mesmo padrão: objeto único em vidro fosco e translúcido, detalhes em neon, brilho em gradiente rosa `#ee2a7b` → roxo `#8a2be2`, acentos laranja `#ff8a2a` e amarelo `#ffc933`, fundo sólido `#0a0514`, vista isométrica, sem texto. Formato 1:1, 2K.

- Ferramenta usada: Dreamina (CLI `dreamina-canvas`), modelo Nano Banana Pro, 210 créditos por imagem. O Higgsfield com `nano_banana_pro` serve como alternativa.
- O prompt completo e o assunto de cada símbolo estão em `aceleradora-site/CONTINUAR.md`.
- Toda geração paga precisa da aprovação do Bruno antes.
- Na página, o fundo escuro do símbolo some com `mix-blend-mode: screen` e máscara radial (classe `.ic` do protótipo).

## Livro novo

"O Apocalipse Zumbi Começou na Minha Escola" (https://zumbinaescola.com.br/): a partir de 11 anos, 23 capítulos, 14 manuais de sobrevivência, lições 3D por QR Code, lançamento da primeira tiragem pelo Catarse. Já é o 11º card do protótipo, em "Leitura e valores".
