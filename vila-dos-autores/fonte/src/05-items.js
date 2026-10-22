// ============================================================
// Itens, modelos 2.5D, receitas, inventário, coletáveis
// ============================================================
const ITEMS = {
  flor: { nome: 'Flor', tipo: 'ing', desc: 'Brota pela praça. Mais comum na primavera.' },
  folha: { nome: 'Folha', tipo: 'ing', desc: 'Uma folhinha verde da vila.' },
  dourada: { nome: 'Folha Dourada', tipo: 'ing', desc: 'Rara e brilhante. A Pena esconde algumas nas casas.' },
  folhaColorida: { nome: 'Folha Colorida', tipo: 'ing', desc: 'Cai das árvores no outono.' },
  graveto: { nome: 'Graveto', tipo: 'ing', desc: 'Um galhinho seco, ótimo para enfeites.' },
  papel: { nome: 'Papel', tipo: 'ing', desc: 'Sai fresquinho da impressora da Gráfica.' },
  tinta: { nome: 'Tinta', tipo: 'ing', desc: 'Potes de cor no Ateliê de Desenho.' },
  fita: { nome: 'Fita', tipo: 'ing', desc: 'Achada no cesto do Correio e pela praça.' },
  botao: { nome: 'Botão', tipo: 'ing', desc: 'Redondinho. Aparece no cesto de achados.' },
  concha: { nome: 'Concha', tipo: 'ing', desc: 'Aparece na praça, principalmente no verão.' },
  pedra: { nome: 'Pedra', tipo: 'ing', desc: 'Uma pedrinha lisa do caminho.' },
  semente: { nome: 'Semente', tipo: 'ing', desc: 'Plante com água e veja crescer.' },
  agua: { nome: 'Água', tipo: 'ing', desc: 'Pegue na fonte da praça.' },
  algodao: { nome: 'Algodão', tipo: 'ing', desc: 'Fofinho, aparece no inverno.' },
  areia: { nome: 'Areia', tipo: 'ing', desc: 'Aparece na praça no verão.' },
  ideia: { nome: 'Ideia de História', tipo: 'livro', desc: 'Guardada a partir do Caderno de Ideias da Pena.' },
  desenho: { nome: 'Desenho', tipo: 'livro', desc: 'Uma cópia do seu desenho, do cavalete do Ateliê.' },
  capa: { nome: 'Capa em Branco', tipo: 'livro', desc: 'Das caixas da Gráfica (depois do selo de Autor).' },
  nomePers: { nome: 'Nome do Personagem', tipo: 'livro', desc: 'Escrito no quadro de nomes do Ateliê.' },
  pagina: { nome: 'Página Ilustrada', tipo: 'deco', desc: 'Sua ideia com seu desenho. Junte 5 para um mini-livro.' },
  guirlanda: { nome: 'Guirlanda', tipo: 'deco', door: true, groundY: 0.55, desc: 'Enfeite de porta. Coloque perto de uma porta da vila.' },
  selo: { nome: 'Selo Personalizado', tipo: 'deco', desc: 'Um carimbo de cera só seu.' },
  marcador: { nome: 'Marcador de Página', tipo: 'deco', desc: 'Para nunca perder onde parou a leitura.' },
  enfeiteJanela: { nome: 'Enfeite de Janela', tipo: 'deco', desc: 'Um móbile de conchas que balança.' },
  florPlantada: { nome: 'Flor Plantada', tipo: 'deco', desc: 'Coloque no chão: ela cresce com o tempo.' },
  capaLivro: { nome: 'Capa do Livro', tipo: 'deco', desc: 'A capa do seu livro, com o nome do personagem.' },
  miniLivro: { nome: 'Mini-livro Encadernado', tipo: 'deco', desc: 'Seu primeiro livrinho de verdade!' },
  buque: { nome: 'Buquê de Outono', tipo: 'deco', desc: 'Folhas coloridas num vaso. Receita de outono.' },
  bonecoNeve: { nome: 'Boneco de Neve Pequeno', tipo: 'deco', desc: 'Receita de inverno.' },
  coroa: { nome: 'Coroa de Flores', tipo: 'deco', wear: true, desc: 'Dá para vestir! Receita de primavera.' },
  lembrancinha: { nome: 'Lembrancinha de Praia', tipo: 'deco', desc: 'Um potinho de areia e concha. Receita de verão.' },
};
const RECIPES = [
  { id: 'guirlanda', ing: { flor: 3, graveto: 1 }, grupo: 'vila' },
  { id: 'selo', ing: { dourada: 2, tinta: 1 }, grupo: 'vila' },
  { id: 'marcador', ing: { papel: 1, botao: 1, fita: 1 }, grupo: 'vila' },
  { id: 'enfeiteJanela', ing: { concha: 2, pedra: 1 }, grupo: 'vila' },
  { id: 'florPlantada', ing: { semente: 1, agua: 1 }, grupo: 'vila' },
  { id: 'pagina', ing: { ideia: 1, desenho: 1 }, grupo: 'livro', onde: 'atelie' },
  { id: 'capaLivro', ing: { capa: 1, nomePers: 1, tinta: 1 }, grupo: 'livro', onde: 'grafica' },
  { id: 'miniLivro', ing: { pagina: 5, fita: 1 }, grupo: 'livro', onde: 'grafica' },
  { id: 'buque', ing: { folhaColorida: 4, graveto: 1 }, grupo: 'estacao', estacao: 'outono' },
  { id: 'bonecoNeve', ing: { algodao: 2, botao: 1 }, grupo: 'estacao', estacao: 'inverno' },
  { id: 'coroa', ing: { flor: 2, fita: 1 }, grupo: 'estacao', estacao: 'primavera' },
  { id: 'lembrancinha', ing: { concha: 2, areia: 1 }, grupo: 'estacao', estacao: 'verao' },
];
const STATION_NOME = { pena: 'Mesa da Casa da Pena', atelie: 'Mesa do Ateliê', grafica: 'Mesa da Gráfica' };
const SPAWN_TABLE = {
  primavera: { flor: 6, folha: 2, graveto: 3, pedra: 2, semente: 2, concha: 1, botao: 1, fita: 1, dourada: 0.35 },
  verao: { flor: 3, concha: 4, areia: 3, graveto: 2, pedra: 2, semente: 1, folha: 2, dourada: 0.35 },
  outono: { folhaColorida: 6, graveto: 4, pedra: 2, semente: 2, flor: 1, folha: 1, botao: 1, dourada: 0.5 },
  inverno: { algodao: 5, graveto: 3, pedra: 2, botao: 2, fita: 1, flor: 1, semente: 1, dourada: 0.35 },
};

// ---------- modelos 2.5D (origem no chão) ----------
let PLAYER_CANVAS = null;
function coverCanvas(color = '#ff6f91', mini = false, tituloOverride) {
  const c = mkCanvas(256, 320), g = c.getContext('2d'); g.fillStyle = color; g.fillRect(0, 0, 256, 320);
  g.fillStyle = 'rgba(0,0,0,.12)'; g.fillRect(0, 0, 14, 320);
  g.fillStyle = 'rgba(255,255,255,.9)'; g.beginPath(); g.roundRect(26, 22, 204, 158, 16); g.fill();
  if (PLAYER_CANVAS) { const k = Math.min(180 / PLAYER_CANVAS.width, 140 / PLAYER_CANVAS.height); const w = PLAYER_CANVAS.width * k, hh = PLAYER_CANVAS.height * k; g.drawImage(PLAYER_CANVAS, 128 - w / 2, 101 - hh / 2, w, hh); }
  g.fillStyle = '#fff8ec'; g.textAlign = 'center'; g.textBaseline = 'middle';
  const t = String(tituloOverride != null && tituloOverride !== '' ? tituloOverride : S.titulo || S.nomePers || 'Minha história').slice(0, 60);
  let s = 30, lines = [t];
  const split = (sz) => { g.font = `900 ${sz}px Grandstander, sans-serif`; const words = t.split(' '), out = []; let ln = ''; for (const w of words) { const tt = ln ? ln + ' ' + w : w; if (g.measureText(tt).width > 222 && ln) { out.push(ln); ln = w; } else ln = tt; } out.push(ln); return out; };
  for (; s >= 14; s -= 2) { lines = split(s); if (lines.length <= 2 && lines.every((l) => g.measureText(l).width <= 226)) break; }
  lines = lines.slice(0, 2); lines.forEach((l, i) => g.fillText(l, 128, 222 + (i - (lines.length - 1) / 2) * (s + 4)));
  g.font = '700 18px Andika, sans-serif'; g.fillText('por ' + (S.nome || 'Autor(a)'), 128, 284);
  return c;
}
function pictureMesh(w, hh, canvasMaker) { const m = new T.Mesh(new T.PlaneGeometry(w, hh), new T.MeshBasicMaterial({ map: canvasTex(canvasMaker()) })); return m; }
function pageCanvas() {
  const c = mkCanvas(200, 256), g = c.getContext('2d'); g.fillStyle = '#fffdf5'; g.fillRect(0, 0, 200, 256); g.fillStyle = '#d9efff'; g.fillRect(14, 14, 172, 140);
  if (PLAYER_CANVAS) { const k = Math.min(150 / PLAYER_CANVAS.width, 130 / PLAYER_CANVAS.height); g.drawImage(PLAYER_CANVAS, 100 - (PLAYER_CANVAS.width * k) / 2, 84 - (PLAYER_CANVAS.height * k) / 2, PLAYER_CANVAS.width * k, PLAYER_CANVAS.height * k); }
  const fr = String(S.frase || '').trim();
  if (fr) {
    g.fillStyle = INK; g.font = '700 14px Andika, sans-serif'; g.textAlign = 'left'; g.textBaseline = 'top';
    const words = fr.split(' '), out = []; let ln = '';
    for (const w of words) { const tt = ln ? ln + ' ' + w : w; if (g.measureText(tt).width > 168 && ln) { out.push(ln); ln = w; } else ln = tt; } out.push(ln);
    const L = out.slice(0, 5); if (out.length > 5) L[4] = L[4].replace(/\s*\S*$/, '') + '…';
    L.forEach((l, i) => g.fillText(l, 16, 164 + i * 17));
  } else { g.fillStyle = '#9aa3b8'; for (let i = 0; i < 4; i++) g.fillRect(18, 172 + i * 18, i === 3 ? 100 : 164, 6); }
  return c;
}
function starMesh(size = 0.22, color = 0xfff6a0) {
  const s = new T.Shape(); for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2 - Math.PI / 2, r = i % 2 ? size * 0.38 : size; i ? s.lineTo(Math.cos(a) * r, Math.sin(a) * r) : s.moveTo(Math.cos(a) * r, Math.sin(a) * r); }
  const m = new T.Mesh(geo('star' + size, () => new T.ShapeGeometry(s)), new T.MeshBasicMaterial({ color, side: T.DoubleSide })); return m;
}
const MODEL = {
  flor(o = {}) { const g = new T.Group(); part(cyl(0.035, 0.035, 0.5, 5), toon(0x3c9a3c), 0, 0.25, 0, 0.02, g); const c = o.c || pick([0xff8fb8, 0xffffff, 0xa77bff, 0xff5e5e]); for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2; part(sph(0.1, 8, 6), toon(c), Math.cos(a) * 0.12, 0.56, Math.sin(a) * 0.12, 0.025, g); } part(sph(0.08, 8, 6), toon(0xffd23f), 0, 0.58, 0, 0.02, g); return g; },
  folha(o = {}) { const g = new T.Group(); const l = part(sph(0.26, 10, 6), o.m || toon(0x6cc657), 0, 0.12, 0, 0.03, g); l.scale.set(1, 0.2, 0.55); l.rotation.y = 0.4; part(box(0.4, 0.02, 0.03), M.ink, 0, 0.18, 0, 0, g).rotation.y = 0.4; return g; },
  folhaColorida() { return MODEL.folha({ m: toon(pick([0xf28a2e, 0xe0502a, 0xffb13b])) }); },
  dourada() { const g = MODEL.folha({ m: M.gold }); g.scale.setScalar(1.15); return g; },
  graveto() { const g = new T.Group(); const a = part(cyl(0.05, 0.06, 0.85, 6), M.trunk, 0, 0.12, 0, 0.025, g); a.rotation.z = Math.PI / 2; const b = part(cyl(0.035, 0.035, 0.35, 5), M.trunk, 0.12, 0.2, 0.08, 0.02, g); b.rotation.set(0.6, 0, 1.0); return g; },
  papel() { const g = new T.Group(); const p = part(box(0.5, 0.03, 0.65), M.paper, 0, 0.1, 0, 0.025, g); p.rotation.y = 0.3; for (let i = 0; i < 3; i++) { const l = part(box(0.32, 0.01, 0.03), toon(0x6ec6ff), 0, 0.12, -0.15 + i * 0.13, 0, p); l.position.y = 0.02; } return g; },
  tinta() { const g = new T.Group(); part(cyl(0.17, 0.17, 0.3, 12), toon(0xe8f6ff), 0, 0.15, 0, 0.03, g); part(cyl(0.15, 0.15, 0.18, 12), toon(0x4a7dff), 0, 0.11, 0, 0, g); part(cyl(0.19, 0.19, 0.08, 12), toon(0xff6b6b), 0, 0.33, 0, 0.025, g); return g; },
  fita() { const g = new T.Group(); [-1, 1].forEach((s) => { const t = part(tor(0.12, 0.045, 6, 14), toon(0xff4f6d), s * 0.12, 0.25, 0, 0.02, g); t.scale.y = 0.7; const tail = part(box(0.06, 0.24, 0.03), toon(0xff4f6d), s * 0.06, 0.1, 0, 0.015, g); tail.rotation.z = s * 0.4; }); part(sph(0.06, 8, 6), toon(0xff8aa0), 0, 0.25, 0, 0.015, g); return g; },
  botao() { const g = new T.Group(); const b = part(cyl(0.18, 0.18, 0.06, 16), toon(0x38c6c0), 0, 0.12, 0, 0.025, g); b.rotation.x = 1.1; [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([x, z]) => { const hl = new T.Mesh(sph(0.025, 5, 4), M.ink); hl.position.set(x * 0.05, 0.035, z * 0.05); b.add(hl); }); return g; },
  concha() { const g = new T.Group(); const c = part(new T.SphereGeometry(0.22, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), toon(0xffb3c7), 0, 0.04, 0, 0.025, g); c.scale.set(1, 0.6, 0.85); return g; },
  pedra() { const g = new T.Group(); const p = part(geo('dodeca', () => new T.DodecahedronGeometry(0.2)), toon(0xa9a6b8), 0, 0.12, 0, 0.025, g); p.scale.y = 0.7; return g; },
  semente() { const g = new T.Group(); [[-0.07, 0x8a5a2b], [0.08, 0xc48542]].forEach(([x, c]) => { const s = part(sph(0.08, 8, 6), toon(c), x, 0.1, 0, 0.02, g); s.scale.set(0.7, 1, 0.7); }); return g; },
  algodao() { const g = new T.Group(); [[0, 0.2, 0, 0.14], [-0.14, 0.12, 0.02, 0.11], [0.14, 0.13, -0.02, 0.12], [0, 0.1, 0.12, 0.1]].forEach(([x, y, z, r]) => part(sph(r, 10, 8), M.white, x, y, z, 0.025, g)); return g; },
  areia() { const g = new T.Group(); part(cone(0.3, 0.22, 12), toon(0xf3d48b), 0, 0.11, 0, 0.025, g); return g; },
  agua() { const g = new T.Group(); part(sph(0.15, 10, 8), M.water, 0, 0.15, 0, 0.025, g); part(cone(0.11, 0.2, 10), M.water, 0, 0.32, 0, 0.02, g); return g; },
  ideia() { const g = new T.Group(); part(sph(0.2, 12, 8), toon(0xfff3a0, { p: { emissive: 0x554400 } }), 0, 0.45, 0, 0.03, g); part(cyl(0.1, 0.1, 0.16, 10), toon(0xc4c9d6), 0, 0.2, 0, 0.02, g); return g; },
  desenho() { const g = new T.Group(); const p = pictureMesh(0.5, 0.64, pageCanvas); p.position.y = 0.4; g.add(p); return g; },
  capa() { const g = new T.Group(); part(box(0.5, 0.65, 0.05), toon(0xd9ccff), 0, 0.35, 0, 0.025, g); return g; },
  nomePers() { const g = new T.Group(); const p = textPlane(S.nomePers || 'Nome', 0.8, 0.3, { bg: '#ffffff', size: 70 }); p.position.y = 0.4; g.add(p); return g; },
  guirlanda() { const g = new T.Group(); part(tor(0.42, 0.13, 8, 22), toon(0x4fae4c), 0, 0, 0, 0.04, g); for (let i = 0; i < 7; i++) { const a = (i / 7) * Math.PI * 2; part(sph(0.08, 8, 6), toon(i % 2 ? 0xff8fb8 : 0xffd23f), Math.cos(a) * 0.42, Math.sin(a) * 0.42, 0.12, 0.02, g); } [-1, 1].forEach((s) => { const b = part(sph(0.12, 8, 6), toon(0xff4f6d), s * 0.11, -0.44, 0.12, 0.02, g); b.scale.set(1.2, 0.8, 0.5); }); return g; },
  selo() { const g = new T.Group(); part(box(0.34, 0.12, 0.26), M.wood, 0, 0.06, 0, 0.025, g); const d = part(cyl(0.3, 0.3, 0.08, 18), toon(0xd6334a), 0, 0.42, 0, 0.03, g); d.rotation.x = Math.PI / 2; const st = starMesh(0.17, 0xffd23f); st.position.set(0, 0.42, 0.05); g.add(st); return g; },
  marcador() { const g = new T.Group(); part(box(0.3, 0.06, 0.2), M.woodDark, 0, 0.03, 0, 0.02, g); part(box(0.16, 0.62, 0.03), toon(0x7a5cff), 0, 0.37, 0, 0.02, g); part(sph(0.06, 8, 6), toon(0x38c6c0), 0, 0.55, 0.03, 0.015, g); part(box(0.03, 0.25, 0.02), toon(0xff4f6d), 0, 0.8, 0, 0.01, g); return g; },
  enfeiteJanela() { const g = new T.Group(); [-0.35, 0.35].forEach((x) => part(box(0.05, 0.9, 0.05), M.woodDark, x, 0.45, 0, 0.02, g)); part(box(0.85, 0.06, 0.06), M.trunk, 0, 0.92, 0, 0.02, g); [[-0.22, 'c'], [0, 'p'], [0.22, 'c']].forEach(([x, k], i) => { part(box(0.01, 0.3, 0.01), M.ink, x, 0.76, 0, 0, g); const o = k === 'c' ? MODEL.concha() : MODEL.pedra(); o.scale.setScalar(0.6); o.position.set(x, 0.48, 0); g.add(o); o.userData.sw = i; }); return g; },
  florPlantada(o = {}) {
    // com vaso (enfeite) ou direto na terra do canteiro (o.solo); cresce em estágios: semente, brotinho, flor, flor cheia
    const g = new T.Group(), dy = o.solo ? -0.24 : 0;
    if (o.solo) { const mt = part(sph(0.22, 10, 6), toon(0x5a3d22), 0, 0.02, 0, 0.02, g); mt.scale.set(1, 0.4, 0.85); }
    else { part(cyl(0.22, 0.16, 0.32, 12), toon(0xd9774a), 0, 0.16, 0, 0.03, g); part(cyl(0.2, 0.2, 0.04, 12), toon(0x6b4a2b), 0, 0.31, 0, 0, g); }
    const st = o.stage == null ? 2 : o.stage, c = o.c || 0xffd23f;
    const flor = (x, y, z, s) => { for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2; part(sph(0.1 * s, 8, 6), toon(c), x + Math.cos(a) * 0.13 * s, y, z + Math.sin(a) * 0.13 * s, 0.02, g); } part(sph(0.08 * s, 8, 6), toon(0xff8a3c), x, y + 0.01, z, 0.015, g); };
    if (st === 0) part(sph(0.05, 6, 5), toon(0xa8692e), 0, 0.34 + dy, 0, 0.015, g);
    if (st >= 1) part(cyl(0.025, 0.025, st === 1 ? 0.2 : 0.55, 5), toon(0x3c9a3c), 0, (st === 1 ? 0.42 : 0.6) + dy, 0, 0.015, g);
    if (st === 1) { const l = part(sph(0.07, 6, 5), toon(0x5cc05a), 0.05, 0.5 + dy, 0, 0.015, g); l.scale.set(1, 0.4, 0.6); }
    if (st >= 2) { flor(0, 0.92 + dy, 0, 1); const l = part(sph(0.1, 8, 6), toon(0x5cc05a), 0.1, 0.55 + dy, 0, 0.015, g); l.scale.set(1, 0.35, 0.6); g.userData.topo = 0.92 + dy; }
    if (st >= 3) { part(cyl(0.022, 0.022, 0.4, 5), toon(0x3c9a3c), -0.16, 0.5 + dy, 0.05, 0.012, g).rotation.z = 0.35; flor(-0.24, 0.72 + dy, 0.06, 0.75); const l2 = part(sph(0.09, 8, 6), toon(0x5cc05a), -0.12, 0.42 + dy, -0.04, 0.012, g); l2.scale.set(1, 0.35, 0.6); }
    return g;
  },
  pagina() { const g = new T.Group(); [[-0.2, 0.25], [0.2, -0.25]].forEach(([x, r]) => { const l = part(box(0.05, 0.9, 0.05), M.wood, x, 0.45, 0, 0.015, g); l.rotation.z = r; }); part(box(0.62, 0.78, 0.03), M.paper, 0, 0.75, 0.04, 0.02, g); const p = pictureMesh(0.55, 0.7, pageCanvas); p.position.set(0, 0.75, 0.06); g.add(p); return g; },
  capaLivro() { const g = new T.Group(); part(box(0.62, 0.8, 0.12), toon(0xff6f91), 0, 0.42, 0, 0.03, g); const p = pictureMesh(0.56, 0.7, () => coverCanvas('#ff6f91')); p.position.set(0, 0.42, 0.065); g.add(p); return g; },
  miniLivro() { const g = new T.Group(); const b = new T.Group(); b.position.y = 0.4; b.rotation.y = -0.4; g.add(b); part(box(0.64, 0.8, 0.22), toon(0xffd23f), 0, 0, 0, 0.03, b); part(box(0.58, 0.74, 0.2), M.paper, 0.03, 0, 0, 0, b); const p = pictureMesh(0.56, 0.7, () => coverCanvas('#ffb000', true)); p.position.set(0, 0, 0.115); b.add(p); part(box(0.04, 0.95, 0.02), toon(0xff4f6d), 0.15, -0.05, 0.12, 0.01, b); return g; },
  buque() { const g = new T.Group(); part(cyl(0.18, 0.13, 0.4, 10), M.wood, 0, 0.2, 0, 0.03, g); [0xe0502a, 0xffb13b, 0xf28a2e, 0xd9502b].forEach((c, i) => { const l = part(sph(0.14, 8, 6), toon(c), (i - 1.5) * 0.1, 0.62 + (i % 2) * 0.08, 0, 0.02, g); l.scale.set(0.5, 1.2, 0.3); l.rotation.z = (i - 1.5) * 0.3; }); part(box(0.38, 0.06, 0.38), toon(0xff4f6d), 0, 0.36, 0, 0.01, g); return g; },
  bonecoNeve() { const g = new T.Group(); part(sph(0.28, 12, 9), M.snow, 0, 0.26, 0, 0.03, g); part(sph(0.2, 12, 9), M.snow, 0, 0.64, 0, 0.03, g); const n = part(cone(0.04, 0.16, 6), toon(0xff8a3c), 0, 0.66, 0.22, 0.01, g); n.rotation.x = Math.PI / 2; part(cyl(0.18, 0.18, 0.06, 10), toon(0xe5383b), 0, 0.5, 0, 0.015, g); part(cyl(0.11, 0.11, 0.16, 10), M.ink, 0, 0.88, 0, 0.015, g); return g; },
  coroa() { const g = new T.Group(); const r = part(tor(0.3, 0.06, 6, 20), toon(0x4fae4c), 0, 0, 0, 0.02, g); r.rotation.x = Math.PI / 2; for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2; part(sph(0.08, 8, 6), toon([0xff8fb8, 0xffd23f, 0xa77bff][i % 3]), Math.cos(a) * 0.3, 0.06, Math.sin(a) * 0.3, 0.015, g); } return g; },
  lembrancinha() { const g = new T.Group(); part(cyl(0.18, 0.18, 0.42, 12), toon(0xe8f6ff), 0, 0.21, 0, 0.03, g); part(cyl(0.16, 0.16, 0.2, 12), toon(0xf3d48b), 0, 0.12, 0, 0, g); part(cyl(0.2, 0.2, 0.08, 12), toon(0x38c6c0), 0, 0.46, 0, 0.02, g); const c = MODEL.concha(); c.scale.setScalar(0.45); c.position.y = 0.22; g.add(c); return g; },
};

// ---------- inventário ----------
function addItem(id, n = 1, opts = {}) {
  S.inv[id] = (S.inv[id] || 0) + n;
  const first = !S.seen[id]; S.seen[id] = 1; save();
  if (!opts.silent) floatText(`+${n} ${ITEMS[id] ? ITEMS[id].nome : id}`, iconURL(id));
  if (first) { checkDiscoveries(); checkAlbum(); }
  refreshQuest(); checkTutorial(); updateBadges();
}
function hasItems(ing) { return Object.entries(ing).every(([k, v]) => (S.inv[k] || 0) >= v); }
function takeItems(ing) { for (const [k, v] of Object.entries(ing)) { S.inv[k] = (S.inv[k] || 0) - v; if (S.inv[k] <= 0) delete S.inv[k]; } save(); updateBadges(); }
function recipeState(r) {
  const disc = !!S.flags['rec_' + r.id];
  const lockBook = r.grupo === 'livro' && !S.selos.autor;
  const seasonOk = !r.estacao || r.estacao === GAME.season;
  const stationOk = !r.onde || GAME.station === r.onde;
  return { disc, lockBook, seasonOk, stationOk, has: hasItems(r.ing), can: disc && !lockBook && seasonOk && stationOk && hasItems(r.ing) };
}
function checkDiscoveries(silent) {
  for (const r of RECIPES) {
    if (S.flags['rec_' + r.id]) continue;
    const ok = (r.id === 'guirlanda' && S.tut >= 2) || (Object.keys(r.ing).every((k) => S.seen[k]) && (r.grupo !== 'livro' || S.selos.autor));
    if (ok) { S.flags['rec_' + r.id] = 1; save(); if (!silent) toast(`📖 Nova receita: ${ITEMS[r.id].nome}!`, iconURL(r.id)); }
  }
}

// ---------- coletáveis no mundo ----------
const WITEMS = []; let SPAWN_PTS = [], spawnT = 0;
const GOLD_SPOTS = [];
function initGoldSpots() {
  const add = (id, area, lx, y, z) => GOLD_SPOTS.push({ id, area, x: area === 'vila' ? lx : ROOMS[area].ox + lx, y, z });
  add('p1', 'pena', -5.1, 0, -2.1); add('p2', 'pena', 2.0, 3.6, -4.45); add('p3', 'pena', 6.2, 0, -3.7);
  add('b1', 'biblioteca', 3.4, 0, -2.5); add('a1', 'atelie', -1.6, 0, -3.0); add('g1', 'grafica', 6.1, 0, -2.6); add('c1', 'correio', -4.3, 0, -4.1);
  add('v1', 'vila', -9.4, 0, -22.7); add('v2', 'vila', -6.5, 0, -3.35);
}
function spawnFixedGold() { for (const s of GOLD_SPOTS) if (!S.found[s.id] && !WITEMS.some((w) => w.fixed === s.id)) spawnWorldItem('dourada', s.area, s.x, s.z, { fixed: s.id, y: s.y }); }
function goldCount() { return GOLD_SPOTS.filter((s) => S.found[s.id]).length; }
function spawnWorldItem(item, area, x, z, opt = {}) {
  const m = MODEL[item](opt); m.position.set(x, opt.y || 0, z); scene.add(m);
  const w = { item, area, x, z, m, ph: rnd(6.28), fixed: opt.fixed || null, gold: item === 'dourada', y0: opt.y || 0, tut: !!opt.tut };
  if (w.gold) { const st = starMesh(0.2); st.position.set(0.25, 0.55, 0); m.add(st); w.star = st; }
  WITEMS.push(w); return w;
}
function initSpawnPoints() {
  const R = seeded(21);
  for (let i = 0; i < 400 && SPAWN_PTS.length < 46; i++) {
    const a = R() * Math.PI * 2, r = 4.6 + R() * 25, x = Math.cos(a) * r, z = Math.sin(a) * r + 2;
    if (Math.hypot(x, z - 2) > 32) continue; if (collides('vila', x, z, 0.9)) continue;
    SPAWN_PTS.push({ x, z });
  }
}
function pickSpawnItem() { const tb = SPAWN_TABLE[GAME.season]; let tot = 0; for (const k in tb) tot += tb[k]; let r = Math.random() * tot; for (const k in tb) { r -= tb[k]; if (r <= 0) return k; } return 'flor'; }
function seedTutorialItems() {
  if (S.tut > 1) return;
  [[-3.6, 11.6, 'flor'], [4.3, 12.6, 'flor'], [-6.2, 7.6, 'flor'], [6.8, 9.6, 'flor'], [1.9, 15.6, 'graveto'], [-2.0, 16.6, 'graveto']].forEach(([x, z, it]) => spawnWorldItem(it, 'vila', x, z, { tut: true }));
}
function updateWorldItems(dt, t) {
  for (let i = WITEMS.length - 1; i >= 0; i--) {
    const w = WITEMS[i], vis = w.area === GAME.area; w.m.visible = vis; if (!vis) continue;
    w.m.position.y = w.y0 + 0.18 + Math.sin(t * 2.2 + w.ph) * 0.07; w.m.rotation.y += dt * 0.8;
    if (w.star) { w.star.rotation.z += dt * 2; w.star.scale.setScalar(0.8 + 0.35 * Math.sin(t * 4 + w.ph)); w.star.lookAt(camera.position); }
    if (!GAME.started || GAME.lock || GAME.placing) continue;
    const d = Math.hypot(P.pos.x - w.x, P.pos.z - w.z);
    if (d < (w.gold ? 1.25 : 0.95)) collect(w, i);
  }
  spawnT += dt;
  if (spawnT > 5 && GAME.started) {
    spawnT = 0; const n = WITEMS.filter((w) => w.area === 'vila' && !w.fixed).length;
    if (n < 14 && SPAWN_PTS.length) { const p = pick(SPAWN_PTS); if (Math.hypot(p.x - P.pos.x, p.z - P.pos.z) > 4 && !WITEMS.some((w) => Math.hypot(w.x - p.x, w.z - p.z) < 1.6)) spawnWorldItem(pickSpawnItem(), 'vila', p.x + rnd(-0.4, 0.4), p.z + rnd(-0.4, 0.4)); }
  }
}
function collect(w, i) {
  WITEMS.splice(i, 1);
  if (w.fixed) { S.found[w.fixed] = 1; save(); }
  addItem(w.item, 1);
  w.gold ? Snd.gold() : Snd.pickup();
  const m = w.m, y0 = m.position.y; let k = 0;
  anim((dt) => { k += dt / 0.35; m.position.x = lerp(m.position.x, P.pos.x, 0.25); m.position.z = lerp(m.position.z, P.pos.z, 0.25); m.position.y = y0 + Math.sin(Math.min(1, k) * Math.PI) * 1.4 + k; m.scale.setScalar(Math.max(0.01, 1 - k)); if (k >= 1) { scene.remove(m); return true; } });
  if (w.fixed) { const n = goldCount(); toast(`✨ Folha dourada escondida! ${n} de ${GOLD_SPOTS.length}`, iconURL('dourada')); if (n >= GOLD_SPOTS.length) award('douradas'); }
}
