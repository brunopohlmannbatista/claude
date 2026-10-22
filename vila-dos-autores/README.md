# Vila dos Autores (Fábrica de Autores)

Jogo 2.5D da Fase 1 ("Chegada na Vila") e da Fase 2 ("Meu Cantinho"), painel da professora e servidor no n8n.

## O que tem aqui

| Pasta / arquivo | O que é |
| --- | --- |
| `index.html` | O jogo pronto. Servido pelo n8n em `/webhook/vila`. |
| `painel.html` | Painel da professora. Servido pelo n8n em `/webhook/vila-professora`. |
| `FASE2-MEU-CANTINHO.md` | Fase 2: o lote de cada criança (casa, jardim, interior, estações, visitas) e a lista de assets. |
| `guia/Vila-dos-Autores-Guia-de-jogo.pdf` | Guia ilustrado de 23 páginas: como funciona e como jogar, Fase 1 e Fase 2 (crianças, professoras e famílias). |
| `fonte/src/` | Código do jogo em partes (`01-core.js` até `08-cantinho.js`, `99-inicio.js`, `head.html`). |
| `fonte/build.sh` | Junta as partes e gera o `index.html`. |
| `servidor/` | Os três fluxos do n8n escritos com o Workflow SDK (`paginas.js`, `api.js`, `salas.js`) e o `gen.mjs`, que expande os atalhos para o formato que o validador do n8n aceita. |

## Como mudar o jogo

1. Edite os arquivos em `fonte/src/`.
2. Rode `fonte/build.sh` para gerar o `index.html`.
3. Faça o commit e o push.
4. Teste o commit novo em `/webhook/vila?v=<sha>` (e `/webhook/vila-professora?v=<sha>`).
5. Troque o commit fixo no fluxo "Vila — páginas, vozes e imagens" (nós "Baixar o jogo" e "Baixar o painel") e publique o fluxo.

O n8n busca os arquivos por um commit fixo (jsDelivr). Por isso, mudar este branch não muda o que as crianças veem até o passo 5.

## Servidor (n8n)

- **Vila — páginas, vozes e imagens**: `/vila`, `/vila-professora`, `/vila-voz`, `/vila-desenho`, `/vila-fig`.
- **Vila — API**: `vila-entrar`, `vila-salvar`, `vila-turma`, `vila-presente`, `vila-prof-login`, `vila-prof-turma`, `vila-prof-aprovar`.
- **Vila — salas da turma (sync)**: `vila-sync` (presença, mural, baú da turma, figurinhas aprovadas, presentes), `vila-cantinho-salvar` e `vila-cantinho` (Fase 2: guardar o lote e visitar colegas; precisam das colunas `cant` e `cant_em` em `vila_salas`).

Os fluxos só leem a planilha da Bia e gravam nas tabelas da Vila. Nenhum fluxo da Bia é alterado.

**Segredos:** em `servidor/api.js` o segredo que gera o identificador das crianças aparece como `TROQUE-POR-UM-SEGREDO` e a planilha como `ID-DA-PLANILHA`. Os valores verdadeiros ficam só dentro do n8n. Não coloque códigos de alunos, códigos de acesso de colégio nem o segredo neste repositório (ele é público).

## Privacidade

- Os colegas veem só o primeiro nome.
- A figurinha de cada criança só aparece para a turma depois que a professora aprova no painel.
- Nada fica guardado no aparelho da criança: o progresso fica no servidor.
