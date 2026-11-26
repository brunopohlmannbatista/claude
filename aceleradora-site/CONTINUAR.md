# Aceleradora EDU — nova vitrine de produtos · ponto de retomada

Atualizado em 26/11/2026. Leia este arquivo primeiro para continuar o trabalho.

## Objetivo

Deixar o site https://aceleradoraedu.club mais intuitivo e visual para os leads. O ponto fraco apontado pelo Bruno é a apresentação dos produtos na home. Nada foi alterado no site que está no ar.

## Onde está cada coisa

| Item | Local |
|---|---|
| Protótipo clicável da nova vitrine (privado) | https://claude.ai/artifact/5SRCXyQRVNNKsexoo9Tcu1 |
| Cópia do código do protótipo | `aceleradora-site/prototipo/Main.dc.html` |
| Símbolos 3D originais (2048×2048, JPG) | `aceleradora-site/simbolos-3d/originais/` |
| Símbolos 3D leves para web (512×512, WebP) | `aceleradora-site/simbolos-3d/web/` |
| Folha com os 12 símbolos lado a lado | `aceleradora-site/simbolos-3d/folha-de-contato.jpg` |
| Canvas da Dreamina com os 12 símbolos | https://dreamina.capcut.com/ai-tool/ai-canvas/23ff5f4a-0841-4b4e-ab1c-366932d200c3 |
| Cópia do site no ar (baixada em 26/11/2026) | `aceleradora-site/site-atual/index.html` |
| Skill do site, com este projeto registrado | `.claude/skills/site-aceleradoraedu/` |

## O que já foi feito

1. **Protótipo da vitrine.** A seção abre com "O que a sua escola quer resolver primeiro?" e quatro filtros: Encher as turmas, Inovar na sala de aula, Leitura e valores, Receita e operação. São 11 cards, com miniatura animada, para quem é, fatos do produto e link específico. O menu foi reduzido para Produtos, Como funciona, Fábrica de Autores e o botão de diagnóstico gratuito.
2. **Livro novo.** "O Apocalipse Zumbi Começou na Minha Escola" (https://zumbinaescola.com.br/) entrou como 11º produto, em "Leitura e valores".
3. **12 símbolos 3D gerados na Dreamina** e encaixados nos cards do protótipo, ao lado do título, flutuando. O card "E-commerce & Cantina Online" usa dois símbolos, porque no protótipo os dois produtos são um card só.

O protótipo com os símbolos não foi aberto para conferência visual. O Bruno ainda precisa olhar no computador e no celular.

## Decisões pendentes do Bruno

O protótipo contradiz as regras da skill. Não montar o bloco para o site antes destas respostas:

1. **Preços.** O protótipo mostra R$ 590/mês (Agentes IA) e R$ 150/mês + R$ 990 (E-commerce & Cantina), que é o que está no site no ar. A regra da skill é site sem preços.
2. **WhatsApp.** O protótipo usa (81) 95168-7966, que é o número do site no ar. A regra da skill é (81) 99536-2170.
3. **Aprovação do protótipo** com os símbolos, ou ajustes em algum símbolo.

## Próximos passos

1. Receber as três respostas acima.
2. Montar a nova vitrine em `aceleradora-site/site-atual/index.html`, trocando a seção de produtos da home pelo conteúdo do protótipo e apontando as imagens para os arquivos de `simbolos-3d/web/` (no site real eles ficam em `assets/`).
3. Conferir no celular os contadores animados das abas Robótica e Maker. Na leitura automática da página eles vieram como "0".
4. Entregar o arquivo ao Bruno. Só publicar com o ok dele.

## Símbolos 3D — como foram gerados

- **Ferramenta:** Dreamina, pela CLI `dreamina-canvas` (versão 1.4.0).
- **Modelo:** Nano Banana Pro (`gemini_3_image_pro`), texto para imagem, 1:1, 2K, uma imagem por nó.
- **Custo:** 210 créditos por símbolo. Total cotado: 2.520 créditos pelos 12.
- **Fundo:** escuro da marca, não transparente. No protótipo o fundo some com `mix-blend-mode: screen` e uma máscara radial (classe `.ic`).

### Prompt padrão

Início, igual em todos:

> A single premium 3D icon centered on a flat, solid, very dark navy-black background (#0a0514). Subject: 

Final, igual em todos:

> Material: thick frosted and clear glass with soft internal refraction, smooth rounded edges, subtle glossy highlights, details drawn as glowing neon light. Lighting: inner glow in a pink (#ee2a7b) to purple (#8a2be2) gradient, with small warm accent lights in orange (#ff8a2a) and yellow (#ffc933). Soft glow halo around the object, gentle reflection beneath it. Isometric three-quarter view, studio 3D render, clean, modern, high-end tech brand style, generous empty margin around the object. No text, no words, no letters, no numbers, no logos, no watermark.

### Assunto de cada símbolo

| Arquivo | Produto | Assunto (entra no lugar de "Subject") |
|---|---|---|
| `01-agentes-ia` | Agentes IA | a glossy translucent glass chat speech bubble, WhatsApp-style rounded shape with a small tail, and inside it a friendly minimal AI spark / small robot face made of glowing light, with three small floating typing dots beside it. |
| `02-primeiro-no-google` | 1º no Google | a glass magnifying glass leaning over a small stack of three glass search-result bars, the top bar glowing brightest with a small glowing star / first-place medal on it. |
| `03-google-for-education` | Google for Education | an open glass laptop with a glowing graduation cap floating above it and a few small floating glass app tiles (document, slide, video-call shapes) around it. |
| `04-ecommerce` | E-commerce | a glass shopping bag with a glowing neon cart symbol on its front, next to a small glass smartphone showing a glowing storefront shape. |
| `05-robotica` | Robótica | a cute friendly small glass robot with glowing neon eyes and antenna, standing next to two interlocking glass programming blocks shaped like puzzle pieces. |
| `06-maker` | Programa Maker | a glass electronics circuit board with a row of small glowing LEDs, with a glass wrench and a glass gear floating above it. |
| `07-livros-paradidaticos` | Livros com Projetos | a neat stack of three glass books with blank covers, the top book slightly open with soft glowing light and tiny sparkles rising from its pages. |
| `08-fabrica-de-autores` | Fábrica de Autores | an open glass book with a glowing neon pencil writing on its blank page, and small glowing sparkles and a tiny star flying out of the pages. |
| `09-pao-diario` | Meu Pão Diário com Jesus | an open glass devotional book with a small glowing neon heart floating above its pages and a soft warm sunrise glow behind it, peaceful and warm. |
| `10-fotos-360` | Fotos 360° | a glass spherical 360-degree camera on a small base, surrounded by a glowing neon orbit ring with a curved arrow circling it, with a tiny school building silhouette reflected inside the sphere. |
| `11-cantina` | Cantina | a glass lunch tray holding a glass juice cup with straw and a sandwich, next to a small glass smartphone showing a glowing checkmark for digital payment. |
| `12-apocalipse-zumbi` | O Apocalipse Zumbi | a closed glass book standing upright with a blank cover, with a playful cartoon zombie hand in glowing neon green-tinted glass bursting out from the top of the book, and a small glass school backpack beside it; fun, adventurous, kid-friendly, not scary, no gore. |

O símbolo 01 foi gerado sem o trecho "details drawn as glowing neon light" e sem "no numbers" no final.

## Como retomar a Dreamina numa sessão nova

O ambiente na nuvem é temporário: a CLI e o login somem quando a sessão acaba.

1. Instalar: `curl -fsSL https://dreamina.capcut.com/canvas-cli/install.sh | bash`. A CLI vai para `~/.local/bin/dreamina-canvas` e a skill para `~/.agents/skills/dreamina-canvas-cli`.
2. Entrar: `dreamina-canvas --format json auth login --no-browser`, mandar o link ao Bruno e rodar em seguida `dreamina-canvas --format json auth wait --device-code '<deviceCode>' --timeout 5m`.
3. Selecionar o canvas: `dreamina-canvas canvas use 23ff5f4a-0841-4b4e-ab1c-366932d200c3`.
4. Fluxo de geração: `node create image` (salva) → `node quote --node-id …` → aprovação do Bruno → `node confirm --credit-ceiling <n>` → `node run --credit-token …` → `operation wait <submitId>` → `resource download <resourceId> -o arquivo.jpg`.

Hosts que o ambiente "claude" já tem liberados para isso: `dreamina.capcut.com`, `p16-dreamina-sign-sg.ibyteimg.com` (download das imagens) e `aceleradoraedu.club` (leitura do site).

Conta Dreamina em 26/11/2026: plano Maestro até 09/11/2027, cerca de 36.700 créditos após este trabalho, a maior parte com validade até 09/12/2026.
