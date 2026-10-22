# Vila dos Autores (Fábrica de Autores)

Jogo 2.5D da Fase 1 ("Chegada na Vila") e painel da professora.

- `index.html`: o jogo. Servido pelo n8n em `/webhook/vila`.
- `painel.html`: painel da professora. Servido pelo n8n em `/webhook/vila-professora`.

O n8n busca estes arquivos por um commit fixo (jsDelivr), então mudar este branch não muda o que as crianças veem até o fluxo "Vila — páginas, vozes e imagens" apontar para o commit novo. Para testar um commit antes: `/webhook/vila?v=<sha>`.
