---
name: site-aceleradoraedu
description: >-
  Mantém e evolui o site e a identidade visual da Aceleradora EDU (empresa de Bruno Pohlmann,
  Recife-PE, que vende soluções educacionais para colégios). Use sempre que o usuário pedir para
  editar, atualizar ou criar páginas/abas do site da aceleradora, adicionar produtos, criar peças
  de divulgação, posts, apresentações ou qualquer material com a identidade da Aceleradora EDU —
  mesmo que ele não diga "site" explicitamente (por exemplo "muda a aba de robótica", "cria uma
  página pro novo produto", "faz um banner da aceleradora", "atualiza o conteúdo do maker").
---

# Site Aceleradora EDU

Skill para manter o site da Aceleradora EDU e produzir materiais com a identidade da marca, sempre consistentes com o que já existe.

## Onde estão os arquivos

Trabalhe na pasta selecionada pelo usuário (`servicos e propaganda da aceleradora`):

- `site-aceleradora/index.html` — o site completo (arquivo único: HTML + CSS + JS)
- `site-aceleradora/assets/` — imagens dos produtos extraídas dos PDFs originais
- `CONTEUDO_SITE_ACELERADORA_EDU.md` — conteúdo aprovado de todas as abas
- PDFs dos produtos nas subpastas (`programa google for education/`, `progrma robotica 2027/`, `programa maker 2027/`, `livros paradidaticos/`, arquivos "Pão Diário")

Antes de editar, leia o `index.html` atual — toda mudança deve preservar a estrutura e os padrões abaixo.

## Identidade visual (obrigatória em tudo)

Cores (variáveis CSS já definidas no site):

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#0a0514` | fundo escuro de tudo |
| `--pink` | `#ee2a7b` | cor principal da marca |
| `--purple` | `#8a2be2` / `--violet #5b21b6` | gradiente da marca |
| `--red/--orange/--yellow` | `#ff3b5c / #ff8a2a / #ffc933` | barras de "propulsão", destaques |
| `--grad` | rosa→roxo 135° | títulos em destaque, botões |
| `--grad-fire` | vermelho→laranja→amarelo 90° | números, sublinhados, tags |

Tipografia: títulos **Sora** (800), texto **Inter** (Google Fonts). Fundo sempre escuro; nunca usar fundo branco em páginas da marca.

Logo: foguete em contorno com gradiente rosa→roxo + barras verticais pulsando (vermelho/laranja/amarelo) como propulsão. O SVG completo está no `<nav>` e no rodapé do `index.html` — reutilize-o, não recrie de memória.

## Estrutura do site (7 abas, SPA)

`home · google · livros · robotica · maker · pao · servicos` — cada aba é uma `<section class="page" id="page-NOME">`, navegação via `goTab('NOME')`.

Toda aba (exceto a home) abre com um **cabeçalho animado** ("videozinho" — exigência do Bruno): `.page-hero` com imagem de fundo em `data-bg` + zoom lento (`kenburns`) + formas 3D flutuando (`.fl-shape`) + parallax que segue o mouse + textos entrando em cascata (`riseIn`). Abaixo do hero vêm as seções de conteúdo em `.wrap`.

Padrões de animação já implementados (reutilize as classes): `.reveal` (surge ao rolar), `.tilt` (cards com inclinação 3D no hover), `.stat .num[data-count]` (contadores animados), `.btn` (gradiente animado), partículas na home, foguete da home com barras pulsando.

## Regras de conteúdo (decisões do Bruno — não mudar sem ele pedir)

1. **Sem preços no site.** Sempre "fale com a gente" / "solicite uma proposta".
2. **WhatsApp:** (81) 99536-2170 → links `https://wa.me/5581995362170?text=...` (texto pré-preenchido por produto).
3. **Robótica e Maker: 1º ao 5º ano.** Robótica = manhã/curricular; Maker = tarde/contraturno.
4. Card/aba de Robótica sempre destaca o bônus: o colégio ganha a implementação do Google for Education e cada aluno ganha sua IA Gemini.
5. Tom de voz: direto, de gestor para gestor — "validado numa escola real antes de chegar na sua", "não vendemos teoria de slide". Público: donos e diretores de colégios.
6. Rodapé: aceleradoraedu.club · @aceleradoraedu · Recife — PE · Colégio Cristão do Recife.

Resumo dos produtos e números aprovados: ver `references/produtos.md`.

## Como adicionar um novo produto/aba

1. Ler o material do produto na pasta (PDFs/PPTXs); extrair imagens reais com `pypdfium2` para `site-aceleradora/assets/`.
2. Escrever o conteúdo primeiro e mostrar ao Bruno para aprovação (ele sempre revisa antes).
3. Adicionar botão no `<nav>`, nova `<section class="page">` com `.page-hero` animado + seções `.wrap`, e card na vitrine da home.
4. Imagem de cabeçalho: gerar no Higgsfield (MCP `generate_image`, modelo `nano_banana_pro`, 16:9) com prompt no padrão: cena abstrata escura navy-black, elementos do produto em vidro/luz, glow gradiente rosa→roxo com acentos laranja/amarelo, espaço negativo à esquerda para texto, "No text, no words". Referenciar a URL gerada em `data-bg` (o sandbox não baixa do CDN).
5. Verificar: refs de assets existem, tags balanceadas, links do WhatsApp corretos.

## Trabalho em andamento: nova vitrine de produtos

Há um redesenho da vitrine de produtos da home em andamento, com protótipo e 12 símbolos 3D prontos. Antes de mexer na home ou nos cards de produto, leia `references/vitrine-simbolos-3d.md` e o arquivo `aceleradora-site/CONTINUAR.md` do repositório `brunopohlmannbatista/claude`. O protótipo usa preços e outro número de WhatsApp, em conflito com as regras de conteúdo acima; o Bruno ainda vai decidir qual vale.

## Materiais fora do site (banners, posts, apresentações)

Aplicar a mesma identidade: fundo escuro, gradientes da marca, Sora/Inter, foguete-logo, tom direto, sem preços, WhatsApp e site no rodapé da peça.
