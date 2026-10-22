#!/bin/bash
# Junta os arquivos de src/ e gera ../index.html (o jogo que o n8n serve em /webhook/vila).
# Uso: ./build.sh   (precisa de Node para checar o código)
set -e
cd "$(dirname "$0")"
TMP=$(mktemp -d)
cat src/01-core.js src/02-engine.js src/03-world.js src/04-interiors.js src/05-items.js src/06-game.js src/07-escola.js src/08-cantinho.js src/99-inicio.js > "$TMP/game.mjs"
node --check "$TMP/game.mjs"
{ echo '<!doctype html>'; echo '<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#cdeaff"><meta name="robots" content="noindex">'; echo '<style>[hidden]{display:none!important}body{margin:0}</style></head><body>'; cat src/head.html; echo '<script type="module">'; cat "$TMP/game.mjs"; echo '</script>'; echo '</body></html>'; } > ../index.html
rm -rf "$TMP"
wc -c ../index.html
