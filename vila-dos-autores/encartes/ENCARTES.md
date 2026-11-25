# Vila dos Autores · dois encartes em PDF (24/11/2026)

Pedido do Bruno: dois encartes do jogo em PDF.
1. **Para a coordenadora**: como é o jogo, detalhado.
2. **Para a diretora**: menos técnico, com mais imagens, mostrando os benefícios, o que a professora vê e acompanha e o lugar onde as crianças da sala se encontram dentro da história.

## Arquivos

| Arquivo | Formato | Páginas | Peso |
|---|---|---|---|
| `Vila-dos-Autores-Encarte-Coordenacao.pdf` | A4 em pé | 11 | 4,9 MB |
| `Vila-dos-Autores-Encarte-Direcao.pdf` | A4 deitado | 7 | 2,0 MB |

Código para refazer: pasta `fonte/` (`coord.py`, `dir.py`, `lib.py`, `render.py`, `assets/img/` com as 36 imagens usadas).

## Encarte da coordenadora (11 páginas)

1. Capa.
2. Visão geral: o livro, a vila e o painel; números (2 fases, 5 casas, 4 missões, 12 receitas, 31 itens no álbum, 8 selos, 4 estações); o caminho da criança em 10 passos.
3. Passos 1 e 2: entrar com o QR e a senha, escolher o personagem, recorte, senha perdida, dois alunos no mesmo aparelho.
4. Passos 3 e 4: praça, Pena, primeiras criações, teclas e toques.
5. Passos 5 e 6: Casa da Pena, Caderno de Ideias, selo de Autor(a) e o que ele abre.
6. Passo 7: as 4 casas e as 4 partes da história (Biblioteca, Ateliê, Gráfica, Correio).
7. Passo 8: receitas do livro, álbum, 8 selos, como o texto vai para o livro.
8. Fase 2, Meu Cantinho (com o acabamento novo).
9. A turma na vila: salas por turma, visitas, mural, Baú da Turma, estações, privacidade.
10. Painel da professora (com o aviso de que ele não tem campo para digitar a parte de um aluno).
11. Como conduzir a primeira aula, o que observar, dúvidas rápidas, em casa, QR do jogo e do painel.

## Encarte da diretora (7 páginas)

1. Capa.
2. Do livro de papel para a tela (QR e senha, desenho vira personagem, a Pena) e da vila para o livro.
3. Uma vila de livro pop-up: as 5 casas e o que cada uma ensina.
4. Meu Cantinho, a casinha de cada criança.
5. É aqui que a turma se encontra (praça, visitas, mural, Baú da Turma) e a faixa de segurança.
6. O que a professora vê e acompanha (painel).
7. O que cada um ganha (criança, família, professora, escola) e o convite para experimentar (QR da vila e WhatsApp).

## Decisões e cuidados

- **Endereços e QR** apontam direto para `https://fabricadeautores.com.br/vila/` (jogo) e `https://fabricadeautores.com.br/vila/professora/` (painel). Não dependem do n8n para abrir a página. Contexto: `vila-dos-autores/hospedagem/QR-E-HOSPEDAGEM.md`.
- **Nenhum nome real** de criança ou escola: só Luna, Theo, Ana Souza e "Colégio Exemplo" (dados de exemplo das telas). Nunca pôr códigos de colégio ou de aluno, nem ID de planilha (repositório público).
- **Telas** vêm do Guia completo (`guia/Vila-dos-Autores-Guia-completo.pdf`, extraídas com `pdfimages -j`) e de recortes das imagens de comparação "antes e depois" (praça, salas e Meu Cantinho novos). As telas de visita entre colegas ainda mostram a casinha antes do acabamento novo.
- **Sem promessa de aparelho**: o encarte diz que funciona no navegador, sem instalar, e recomenda testar num aparelho da escola antes da primeira aula. Não foi testado em Chromebook nem celular de escola de verdade.
- **Estilo**: coral #ff5c39 e âmbar #ffb454, fundo creme, capas em #1f1530, Plus Jakarta Sans e Grandstander; sem sombras, transparências ou desfoque; ícones Lucide; telas com moldura fina.
- **Contato** na página 7 da diretora: WhatsApp (81) 95168-7966 e fabricadeautores.com.br. Sem preço e sem a palavra "gratuito".

## Como refazer

```
cd vila-dos-autores/encartes/fonte
npm i @fontsource/plus-jakarta-sans @fontsource/grandstander lucide-static
pip install qrcode[pil] playwright
mkdir -p assets/fonts && cp node_modules/@fontsource/plus-jakarta-sans/files/plus-jakarta-sans-latin-{400,600,700,800}-normal.woff2 node_modules/@fontsource/grandstander/files/grandstander-latin-{800,900}-normal.woff2 assets/fonts/
python3 coord.py && python3 render.py coord     # gera coord.pdf
python3 dir.py && python3 render.py dir         # gera dir.pdf
```

`render.py` avisa quando algum conteúdo estoura a página ou invade o rodapé (deve imprimir tudo 0).

## Pendências

- Reemitir os encartes quando o Meu Cantinho ganhar pintura à mão nas peças que ainda estão em cartão liso.
- Se o Bruno criar o subdomínio `vila.fabricadeautores.com.br`, trocar os endereços e refazer os QR.
