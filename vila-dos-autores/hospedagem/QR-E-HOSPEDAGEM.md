# Vila dos Autores · QR dos livros e hospedagem

Atualizado em 17/11/2026.

## Como o QR do livro chega no jogo

1. O QR impresso nos livros aponta para o endereço do n8n: `https://roundrooster-n8n.cloudfy.live/webhook/vila`.
2. O n8n (fluxo "Vila — páginas, vozes e imagens") responde com um redirecionamento (302, sem cache) para `https://fabricadeautores.com.br/vila/`.
3. O navegador abre o jogo na Hostinger. O n8n só aponta o caminho; não entrega mais a página.

O painel da professora segue o mesmo caminho: `/webhook/vila-professora` encaminha para `https://fabricadeautores.com.br/vila/professora/`.

## Endereços

| O quê | Endereço |
|---|---|
| Jogo (Hostinger) | https://fabricadeautores.com.br/vila/ |
| Painel da professora (Hostinger) | https://fabricadeautores.com.br/vila/professora/ |
| QR dos livros (n8n, encaminha) | https://roundrooster-n8n.cloudfy.live/webhook/vila |
| Painel pelo endereço antigo (n8n, encaminha) | https://roundrooster-n8n.cloudfy.live/webhook/vila-professora |
| Teste de uma versão (n8n serve o commit) | `/webhook/vila?v=<sha>` |

O endereço do n8n está impresso nos livros e NÃO pode ser desligado nem mudar de nome. Se o n8n mudar de servidor ou domínio, o QR dos livros já impressos para de funcionar.

## O que ainda depende do n8n

Entrar com código, salvar progresso, turma, figurinhas, vozes e o painel da professora continuam chamando o n8n (`/webhook/vila-entrar`, `-salvar`, `-turma`, `-presente`, `-sync`, `-cantinho`, `-cantinho-salvar`, `-prof-login`, `-prof-turma`, `-prof-aprovar`, `-voz`, `-desenho`, `-fig`). A Hostinger só entrega as páginas. O n8n aceita chamadas vindas de fabricadeautores.com.br.

## Hostinger

- Pasta `public_html/vila/`: `index.html` (= `vila-dos-autores/papel/index.html`), `.htaccess` (compressão, sem cache no html, força https) e `professora/index.html` (= `vila-dos-autores/painel.html`).
- `public_html/` é a raiz do site da Fábrica de Autores. Nunca pôr o jogo ali: apagaria o site.
- Atualizar: enviar o `index.html` novo por cima em `public_html/vila/` (gerenciador de arquivos da Hostinger, "Replace all files in destination folder").
- O link direto do gerenciador vence em cerca de 1 hora (403). Reabrir por hPanel > Arquivos > Gerenciador de arquivos > "Acessar arquivos de fabricadeautores.com.br".
- Versão no ar desde 17/11/2026, 23h28: commit e0f17bf (Meu Cantinho no acabamento da Fase 1).
- Voltar atrás no arquivo: enviar de novo o `papel/index.html` do commit 5a592d3.

## Voltar atrás no encaminhamento (n8n)

No fluxo `XzGlcPT1lvAeV6RL`, publicar uma versão anterior:
- `173e456d-131f-4ef9-8166-bdcd80bc6291`: o n8n volta a servir o jogo e o painel sozinho (commit da Vila antiga fixado).
- `40efcd07-8d20-4588-acc6-4eef8f30b6a6`: encaminha só o jogo, não o painel.

## Pendências

- Subdomínio `vila.fabricadeautores.com.br` apontando para `public_html/vila` (opcional).
- Reemitir o PDF do guia com o endereço final e novos QR (os atuais seguem valendo pelo encaminhamento).
- Nos próximos livros, imprimir o QR direto em `https://fabricadeautores.com.br/vila/`, que não depende do n8n para abrir a página.

Repositório público: nunca subir senhas, códigos de aluno ou de colégio, nem IDs de planilha.
