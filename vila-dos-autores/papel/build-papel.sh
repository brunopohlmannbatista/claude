#!/bin/bash
# Gera papel/index.html: o MESMO jogo de ../fonte/src + a camada visual (90-papel.js, 91-papel-salas.js) + o piloto de arte ilustrada (arte-dados.js, 92-papel-arte.js).
# Não toca em ../index.html (o jogo que as crianças usam).
set -e
cd "$(dirname "$0")"
SRC=../fonte/src
TMP=$(mktemp -d)
cat $SRC/01-core.js $SRC/02-engine.js $SRC/03-world.js $SRC/04-interiors.js $SRC/05-items.js $SRC/06-game.js $SRC/07-escola.js $SRC/08-cantinho.js 90-papel.js 91-papel-salas.js arte-dados.js 92-papel-arte.js $SRC/99-inicio.js > "$TMP/game.mjs"
node --check "$TMP/game.mjs"
{ echo '<!doctype html>'; echo '<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#f2e2c2"><meta name="robots" content="noindex">'; echo '<style>[hidden]{display:none!important}body{margin:0}</style></head><body>'; cat $SRC/head.html; cat head-papel.html; echo '<script type="module">'; cat "$TMP/game.mjs"; echo '</script>'; echo '</body></html>'; } > index.html
rm -rf "$TMP"
wc -c index.html
