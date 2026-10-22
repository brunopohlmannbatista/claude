// ============================================================
// Fase 2 — Meu Cantinho: o lote de cada criança
// casa com fachada, jardim com canteiro, cerca, caminho até a vila, quadro da história,
// interior "casinha de boneca", decorações, estações e visitas de colegas da turma
// ============================================================
const CANT_X = -300, CANT_Z = 0;
const CANT_AREAS = new Set(['cantinho', 'cantinhoCasa']);
const CANT_OX = 700; // interior (mesma fileira das outras salas)
const cwX = (x) => CANT_X + x, cwZ = (z) => CANT_Z + z;
const CORES_CANT = {
  parede: [['Creme', 0xfff1d6], ['Rosa', 0xffc9dc], ['Azul', 0xbfe0ff], ['Verde', 0xcdf0c0], ['Lilás', 0xdccfff], ['Pêssego', 0xffd2b0]],
  telhado: [['Vermelho', 0xe5533d], ['Azul', 0x2f5d9e], ['Roxo', 0x8a5cc2], ['Verde', 0x2e8a6e], ['Laranja', 0xf28a2e], ['Rosa', 0xff6f91]],
  porta: [['Madeira', 0x8a4b2a], ['Turquesa', 0x3aa6a0], ['Amarela', 0xffc928], ['Vermelha', 0xe5383b], ['Azul', 0x3a86ff], ['Verde', 0x4fae4c]],
};
const CASA_C = { w: 6.0, d: 4.4, h: 3.2, z: -4.8, y0: 0.4 }; CASA_C.front = CASA_C.z + CASA_C.d / 2;
const CERCA = { x0: -9, x1: 9, z0: -9.4, z1: 7, gate: 1.5 };
const CANTEIRO = { x: -4.6, z: 0.9, slots: [-1.15, 0, 1.15] };
const QUADRO_P = { x: 5.0, z: 4.3 }, CAIXA_P = { x: -2.7, z: 8.3 }, LATA_P = { x: 4.1, z: -1.5 }, VOLTA_P = { x: -7.5, z: 12.9 };
const LIMITE_DECO = 3;
const CANT = { group: null, dono: null, mats: {}, room: null, quadroCanvas: null, quadroTex: null, placa: null, portao: null, caixaPlaca: null, visita: [], trees: [], flags: [], smoke: [], butterflies: [], luzes: [], lampLight: null, lampOn: false, shade: null, shadeOff: null, shadeOn: null, bauLid: null, fotoMat: null, wp: null, wpCanvas: null, livroImg: {}, visitaFig: null, srvOff: false, pushTimer: 0, portalBub: null, miniLivro: null };
const PORTAL = { ang: 42, ix: 0, iz: 0, voltaX: 0, voltaZ: 0 };

function areaExterna(a) { return a === 'vila' || a === 'cantinho'; }
function tagS(obj, ...ss) { seasonTag(obj, ...ss); obj.visible = ss.includes(GAME.season); return obj; }
function hexCss(n) { return '#' + (n >>> 0).toString(16).padStart(6, '0'); }
function misturaCor(n, alvo, k) { const a = [(n >> 16) & 255, (n >> 8) & 255, n & 255], b = [(alvo >> 16) & 255, (alvo >> 8) & 255, alvo & 255]; return (Math.round(lerp(a[0], b[0], k)) << 16) | (Math.round(lerp(a[1], b[1], k)) << 8) | Math.round(lerp(a[2], b[2], k)); }
function corIdx(lista, i) { return lista[clamp(Math.round(+i || 0), 0, lista.length - 1)][1]; }
function planoTexto(mesh, text, opts) { const m = mesh.material; if (m.map) m.map.dispose(); m.map = canvasTex(textCanvas(text, opts)); m.needsUpdate = true; }
function linhasTexto(g, text, maxW) { const out = []; for (const par of String(text || '').split('\n')) { let ln = ''; for (const w of par.split(' ')) { const t = ln ? ln + ' ' + w : w; if (g.measureText(t).width > maxW && ln) { out.push(ln); ln = w; } else ln = t; } out.push(ln); } return out; }
const capFirst = (s) => (s ? String(s)[0].toUpperCase() + String(s).slice(1) : '');

// ---------- portal na vila: o caminho das flores até o Meu Cantinho ----------
function buildPortalCantinho(V) {
  const a = (PORTAL.ang * Math.PI) / 180, r = 25.6, x = Math.cos(a) * r, z = Math.sin(a) * r, rot = Math.atan2(-x, -z);
  PORTAL.ix = Math.cos(a) * 23.6; PORTAL.iz = Math.sin(a) * 23.6; PORTAL.voltaX = Math.cos(a) * 22.6; PORTAL.voltaZ = Math.sin(a) * 22.6;
  const g = new T.Group(); g.position.set(x, 0, z); g.rotation.y = rot; V.add(g);
  [-1.75, 1.75].forEach((s) => { part(box(0.45, 3.4, 0.45), M.wood, s, 1.7, 0, 0.05, g); part(sph(0.32, 12, 8), toon(0xff8fb8), s, 3.6, 0, 0.04, g); addCircle('vila', x + Math.cos(rot) * s, z - Math.sin(rot) * s, 0.4); });
  part(box(4.2, 0.4, 0.42), M.woodDark, 0, 3.3, 0, 0.05, g);
  signBoard('MEU CANTINHO', 3.2, 0.62, g, 0, 2.75, 0.28, { bg: '#ffd9e8', size: 70, weight: 900 });
  // telhadinho de casinha em cima do portal
  const tg = new T.Group(); tg.position.set(0, 3.55, 0); g.add(tg);
  const tsh = new T.Shape(); tsh.moveTo(-1.0, 0); tsh.lineTo(1.0, 0); tsh.lineTo(0, 0.8); tsh.closePath();
  const tgeo = new T.ExtrudeGeometry(tsh, { depth: 0.5, bevelEnabled: false }); tgeo.translate(0, 0, -0.25);
  part(tgeo, toon(0xe5533d), 0, 0, 0, 0.05, tg); part(box(0.7, 0.6, 0.45), toon(0xfff1d6), 0, -0.05, 0, 0.04, tg);
  const gar = new T.Group(); g.add(gar); seasonTag(gar, 'primavera', 'verao', 'outono');
  for (let i = 0; i < 9; i++) { const t = i / 8, px = lerp(-1.75, 1.75, t), py = 3.05 - Math.sin(t * Math.PI) * 0.3; part(sph(0.17, 8, 6), toon(i % 2 ? 0x4fae4c : 0xffd23f), px, py, 0.3, 0.025, gar); }
  const ice = new T.Group(); g.add(ice); seasonTag(ice, 'inverno');
  for (let i = 0; i < 6; i++) { const ic = part(cone(0.09, 0.45 + (i % 3) * 0.15, 5), toon(0xdff4ff), -1.4 + i * 0.56, 3.0, 0.3, 0.02, ice); ic.rotation.x = Math.PI; }
  // trilha de pedras e flores que some entre as árvores
  for (let i = 0; i < 6; i++) { const rr = r + 0.9 + i * 1.2, st = new T.Mesh(cyl(0.34, 0.38, 0.05, 9), M.stoneDark); st.position.set(Math.cos(a) * rr + Math.sin(a) * ((i % 2) - 0.5) * 0.5, 0.06, Math.sin(a) * rr - Math.cos(a) * ((i % 2) - 0.5) * 0.5); V.add(st); }
  const fl = new T.Group(); V.add(fl); seasonTag(fl, 'primavera', 'verao');
  [-1, 1].forEach((s) => { for (let i = 0; i < 4; i++) { const rr = 15 + i * 2.6, px = Math.cos(a) * rr - Math.sin(a) * s * 1.7, pz = Math.sin(a) * rr + Math.cos(a) * s * 1.7; part(cyl(0.03, 0.03, 0.45, 5), toon(0x3c9a3c), px, 0.22, pz, 0, fl); part(sph(0.15, 8, 6), toon([0xff8fb8, 0xffd23f, 0xa77bff][(i + (s > 0 ? 1 : 0)) % 3]), px, 0.5, pz, 0.025, fl); } });
  CANT.portalBub = makeBillboard(bubbleCanvas('!', '#ff8fb8'), 1.2); CANT.portalBub.sh.visible = false; CANT.portalBub.root.position.set(x, 5.4, z); CANT.portalBub.root.visible = false; scene.add(CANT.portalBub.root);
}

// ---------- o lote (área ao ar livre "cantinho") ----------
function buildCantinho() {
  const g = new T.Group(); g.position.set(CANT_X, 0, CANT_Z); g.visible = false; scene.add(g); CANT.group = g;
  BOUNDS.cantinho = { x0: cwX(-29), x1: cwX(29), z0: cwZ(-13.5), z1: cwZ(14.2) };
  const mt = CANT.mats;
  mt.parede = toon(0xfff1d6, { unique: true }); mt.telhado = toon(0xe5533d, { unique: true }); mt.porta = toon(0x8a4b2a, { unique: true });
  mt.trim = toon(0xfff3d6); mt.terra = toon(0x6b4a2b); mt.vidro = new T.MeshBasicMaterial({ color: 0xbfe8ff });
  mt.colcha = toon(0xff8fb8, { unique: true }); mt.cortina = toon(0xff8fb8, { unique: true });
  // chão, manchas de grama e tufos
  const ground = new T.Mesh(new T.CircleGeometry(80, 48), M.grass); ground.rotation.x = -Math.PI / 2; g.add(ground);
  const R0 = seeded(31);
  for (let i = 0; i < 14; i++) { const m = new T.Mesh(geo('patch', () => new T.CircleGeometry(1, 18)), M.grass2); m.rotation.x = -Math.PI / 2; m.position.set(R0() * 56 - 28, 0.01, R0() * 26 - 13); m.scale.set(1.2 + R0() * 2, 0.9 + R0() * 1.2, 1); g.add(m); }
  const tufts = new T.InstancedMesh(cone(0.12, 0.5, 5), M.grass2, 160), dm = new T.Object3D(); let ti = 0;
  for (let i = 0; i < 300 && ti < 160; i++) { const x = R0() * 56 - 28, z = R0() * 26 - 13; if (Math.abs(z - 11.2) < 2 || (Math.abs(x) < 9.5 && z > -10 && z < 7.6)) continue; dm.position.set(x, 0.22, z); dm.rotation.set((R0() - 0.5) * 0.5, 0, (R0() - 0.5) * 0.5); dm.updateMatrix(); tufts.setMatrixAt(ti++, dm.matrix); }
  tufts.count = ti; g.add(tufts);
  // gramado do lote (um pouco mais verdinho) e a rua dos cantinhos
  const lawn = part(box(17.6, 0.04, 16.2), M.grass2, 0, 0.02, -1.2, 0, g); lawn.scale.y = 1;
  part(box(70, 0.06, 3.2), M.path, 0, 0.03, 11.2, 0.05, g);
  for (let i = 0; i < 26; i++) { const st = new T.Mesh(cyl(0.38, 0.42, 0.05, 9), M.stoneDark); st.position.set(-32 + i * 2.6, 0.07, 11.2 + ((i % 2) - 0.5) * 0.9); g.add(st); }
  // caminho de entrada: da rua até a porta
  part(box(1.9, 0.06, 13.2), M.path, 0, 0.04, 4.0, 0.05, g);
  for (let i = 0; i < 8; i++) { const st = new T.Mesh(cyl(0.34, 0.38, 0.05, 9), M.stoneDark); st.position.set(((i % 2) - 0.5) * 0.6, 0.08, -1.6 + i * 1.5); g.add(st); }
  cantCasaExterna(g);
  cantCerca(g, CERCA.x0, CERCA.x1, CERCA.z0, CERCA.z1, CERCA.gate, true);
  cantPortao(g);
  cantCanteiro(g);
  cantQuadro(g);
  cantCaixaCorreio(g);
  cantLata(g);
  cantPlacaVolta(g);
  // postes e bandeirinhas sobre o portão
  const L1 = buildLamp(g, -10.4, 9.3), L2 = buildLamp(g, 10.4, 9.3); addCircle('cantinho', cwX(-10.4), cwZ(9.3), 0.3); addCircle('cantinho', cwX(10.4), cwZ(9.3), 0.3);
  const nf = VILLAGE.flags ? VILLAGE.flags.length : 0; buildBunting(g, L1, L2); if (VILLAGE.flags) CANT.flags.push(...VILLAGE.flags.splice(nf));
  // vizinhos (outras casinhas da rua) e árvores
  cantVizinho(g, -21, 0xffd2b0, 0x2e8a6e, 3); cantVizinho(g, 21, 0xbfe0ff, 0x8a5cc2, 5);
  [[-7.3, -7.9, 'round', 0.85], [7.5, -8.0, 'pine', 0.8], [-12.5, -1.5, 'pine', 1], [12.6, 2.4, 'round', 0.95], [-13.6, 6.2, 'round', 0.9], [14.2, -6.4, 'pine', 1.05], [-27, -4, 'round', 1], [27.5, -2, 'pine', 1], [0.8, -12.4, 'pine', 1.1], [-5.6, -12.6, 'round', 1], [6.4, -12.9, 'round', 0.95], [-29, 6, 'pine', 0.95], [29, 7, 'round', 0.9]].forEach(([x, z, k, s]) => cantArvore(g, x, z, s, k));
  cantMorroVila(g);
  cantSazonais(g);
  buildCantinhoRoom();
  // interações do lado de fora
  const F = Cantinho.fachadas();
  inter({ area: 'cantinho', x: cwX(0), z: cwZ(CASA_C.front + 1.4), r: 2.0, y: 3.2, label: () => (CANT.dono ? `🚪 Entrar · casa de ${CANT.dono.n}` : '🚪 Entrar em casa'), act: () => Cantinho.entrarCasa() });
  inter({ area: 'cantinho', x: cwX(CANTEIRO.x), z: cwZ(CANTEIRO.z + 1.3), r: 1.8, y: 1.6, obj: CANT.canteiroObj, hopH: 0.08, label: () => Cantinho.rotuloCanteiro(), act: () => Cantinho.plantar() });
  inter({ area: 'cantinho', x: cwX(QUADRO_P.x), z: cwZ(QUADRO_P.z + 1.3), r: 1.7, y: 3.4, obj: CANT.quadroObj, hopH: 0.1, label: () => (CANT.dono ? '🖼 Ver o quadro' : '🖼 Quadro da história'), act: () => Cantinho.abrirQuadro() });
  inter({ area: 'cantinho', x: cwX(CAIXA_P.x), z: cwZ(CAIXA_P.z + 1.1), r: 1.6, y: 2.2, obj: CANT.caixaObj, hopH: 0.15, label: () => (CANT.dono ? '🏡 Voltar para o meu cantinho' : '📬 Visitar colegas'), act: () => (CANT.dono ? Cantinho.ir(null) : Cantinho.abrirVisitas()) });
  inter({ area: 'cantinho', x: cwX(LATA_P.x), z: cwZ(LATA_P.z + 0.9), r: 1.5, y: 1.4, obj: CANT.lataObj, hopH: 0.2, label: () => (CANT.dono ? null : '🎨 Pintar a casa'), act: () => Cantinho.abrirPintar() });
  inter({ area: 'cantinho', x: cwX(VOLTA_P.x), z: cwZ(VOLTA_P.z - 1.3), r: 1.8, y: 2.8, label: () => '🏘 Voltar para a praça', act: () => Cantinho.voltarPraca() });
  inter({ area: 'cantinho', x: F.janela.x, z: F.janela.z + 1.3, r: 1.2, y: 3.4, prio: -1, label: () => '🪟 Espiar pela janela', act: () => { Snd.chirp(); toast(CANT.lampOn ? 'A luminária está acesa lá dentro. Que cantinho aconchegante!' : 'Lá dentro está tudo arrumadinho. Entre pela porta!'); } });
}
function cantCasaExterna(g) {
  const { w, d, h, z, y0 } = CASA_C, mt = CANT.mats, zf = d / 2;
  const casa = new T.Group(); casa.position.set(0, 0, z); g.add(casa); CANT.casa = casa;
  part(box(w + 0.6, y0, d + 0.6), toon(0xa59aa8), 0, y0 / 2, 0, 0.06, casa);
  part(box(w, h, d), mt.parede, 0, y0 + h / 2, 0, 0.09, casa);
  [-1, 1].forEach((s) => part(box(0.26, h, 0.26), mt.trim, s * (w / 2), y0 + h / 2, zf, 0.04, casa));
  const sh = new T.Shape(); sh.moveTo(-w / 2 - 0.55, 0); sh.lineTo(w / 2 + 0.55, 0); sh.lineTo(0, 2.3); sh.closePath();
  const rg = new T.ExtrudeGeometry(sh, { depth: d + 0.8, bevelEnabled: false }); rg.translate(0, 0, -(d + 0.8) / 2);
  part(rg, mt.telhado, 0, y0 + h, 0, 0.1, casa);
  part(box(0.34, 0.34, d + 1.0), mt.trim, 0, y0 + h + 2.26, 0, 0.05, casa);
  const slope = Math.atan2(2.3, w / 2 + 0.55), sl = Math.hypot(2.3, w / 2 + 0.55);
  [-1, 1].forEach((s) => { const sn = part(box(sl * 0.92, 0.2, d + 0.9), M.snow, s * (w / 4 + 0.28), y0 + h + 1.24, 0, 0.04, casa); sn.rotation.z = -s * slope; tagS(sn, 'inverno'); });
  const ice = new T.Group(); casa.add(ice); tagS(ice, 'inverno');
  for (let i = 0; i < 9; i++) { const ic = part(cone(0.08, 0.35 + (i % 3) * 0.14, 5), toon(0xdff4ff), -w / 2 - 0.3 + i * ((w + 0.6) / 8), y0 + h - 0.1, zf + 0.42, 0.015, ice); ic.rotation.x = Math.PI; }
  // chaminé com fumacinha (outono e inverno)
  part(box(0.8, 1.9, 0.8), toon(0xc9694a), -1.7, y0 + h + 1.35, -0.8, 0.06, casa);
  part(box(1.0, 0.26, 1.0), toon(0x6f5b6e), -1.7, y0 + h + 2.4, -0.8, 0.04, casa);
  for (let i = 0; i < 4; i++) { const p = part(sph(0.28, 10, 8), toon(0xf4f1f6), -1.7, y0 + h + 2.7, -0.8, 0.035, casa); p.userData.ph = i / 4; CANT.smoke.push(p); }
  // porta
  part(box(1.55, 2.3, 0.2), mt.trim, 0, y0 + 1.15, zf + 0.05, 0.05, casa);
  part(box(1.15, 2.05, 0.22), mt.porta, 0, y0 + 1.03, zf + 0.12, 0.05, casa);
  const pj = part(cyl(0.2, 0.2, 0.06, 18), mt.vidro, 0, y0 + 1.55, zf + 0.25, 0.03, casa); pj.rotation.x = Math.PI / 2;
  part(sph(0.08, 10, 8), toon(0xffd23f), 0.36, y0 + 0.95, zf + 0.27, 0.02, casa);
  part(box(1.9, 0.4, 0.9), M.stone2, 0, 0.2, zf + 0.65, 0.04, casa);
  // telhadinho da porta
  const tp = new T.Group(); tp.position.set(0, y0 + 2.42, zf + 0.35); casa.add(tp);
  [-1, 1].forEach((s) => { const t = part(box(1.05, 0.12, 0.8), mt.telhado, s * 0.46, 0.18, 0, 0.035, tp); t.rotation.z = -s * 0.42; });
  // janela da fachada (fica quentinha quando a luminária está acesa)
  const wx = 1.85, wy = y0 + 1.75;
  part(box(1.45, 1.35, 0.2), mt.trim, wx, wy, zf + 0.04, 0.05, casa);
  part(box(1.12, 1.02, 0.22), mt.vidro, wx, wy, zf + 0.07, 0, casa);
  part(box(1.12, 0.09, 0.27), mt.trim, wx, wy, zf + 0.1, 0, casa); part(box(0.09, 1.02, 0.27), mt.trim, wx, wy, zf + 0.1, 0, casa);
  part(box(1.55, 0.34, 0.44), M.woodDark, wx, wy - 0.88, zf + 0.28, 0.045, casa);
  const fl = new T.Group(); casa.add(fl); tagS(fl, 'primavera', 'verao');
  [-0.5, 0, 0.5].forEach((o, i) => part(sph(0.16, 10, 8), toon([0xff8fb8, 0xffd23f, 0xa77bff][i]), wx + o, wy - 0.62, zf + 0.3, 0.025, fl));
  tagS(part(box(1.5, 0.12, 0.4), M.snow, wx, wy - 0.66, zf + 0.28, 0.025, casa), 'inverno');
  // lanterna e plaquinha com o nome
  part(box(0.12, 0.5, 0.12), M.ink, -1.25, y0 + 2.05, zf + 0.15, 0.02, casa);
  part(box(0.32, 0.4, 0.32), M.lamp, -1.25, y0 + 1.72, zf + 0.25, 0.04, casa);
  const pb = part(box(2.7, 0.62, 0.12), M.wood, -0.4, y0 + h - 0.34, zf + 0.08, 0.04, casa);
  CANT.placa = new T.Mesh(new T.PlaneGeometry(2.5, 0.5), new T.MeshBasicMaterial({ color: 0xffffff })); CANT.placa.position.set(-0.4, y0 + h - 0.34, zf + 0.15); casa.add(CANT.placa); void pb;
  // vasos e abóboras ao lado da porta
  [-1, 1].forEach((s) => {
    const vp = new T.Group(); vp.position.set(s * 1.25, 0, zf + 0.75); casa.add(vp); tagS(vp, 'primavera', 'verao');
    part(cyl(0.26, 0.2, 0.42, 12), toon(0xd9774a), 0, 0.21, 0, 0.03, vp); [0, 1, 2].forEach((i) => part(sph(0.12, 8, 6), toon([0xff8fb8, 0xffd23f, 0xffffff][i]), Math.cos(i * 2.1) * 0.12, 0.56, Math.sin(i * 2.1) * 0.1, 0.02, vp));
    const ab = new T.Group(); ab.position.set(s * 1.25, 0, zf + 0.8); casa.add(ab); tagS(ab, 'outono');
    const pu = part(sph(0.34, 14, 10), toon(0xf28a2e), 0, 0.27, 0, 0.04, ab); pu.scale.y = 0.75; part(cyl(0.04, 0.05, 0.18, 6), toon(0x5a7a2e), 0, 0.56, 0, 0.015, ab);
  });
  addBox('cantinho', cwX(0), cwZ(z), w / 2 + 0.35, d / 2 + 0.35);
  addBox('cantinho', cwX(0), cwZ(z + zf + 0.65), 0.95, 0.4);
}
function cantCerca(g, x0, x1, z0, z1, gate, colide, area = 'cantinho') {
  const posts = [], rails = [];
  const lado = (ax, az, bx, bz) => {
    const L = Math.hypot(bx - ax, bz - az), n = Math.max(1, Math.round(L / 1.25)), rot = Math.atan2(bx - ax, bz - az);
    for (let i = 0; i <= n; i++) { const t = i / n; posts.push([lerp(ax, bx, t), lerp(az, bz, t)]); }
    [0.42, 0.82].forEach((y) => { const r = part(box(0.08, 0.12, L), M.wood, (ax + bx) / 2, y, (az + bz) / 2, 0.025, g); r.rotation.y = rot; rails.push(r); });
    const sn = part(box(0.14, 0.06, L), M.snow, (ax + bx) / 2, 0.92, (az + bz) / 2, 0.015, g); sn.rotation.y = rot; tagS(sn, 'inverno');
    if (colide) { const cxm = (ax + bx) / 2, czm = (az + bz) / 2; addBox(area, CANT_X + cxm, CANT_Z + czm, 0.15, L / 2, rot); }
  };
  const gm = (x0 + x1) / 2; lado(x0, z1, gm - gate, z1); lado(gm + gate, z1, x1, z1); lado(x0, z0, x0, z1); lado(x1, z0, x1, z1); lado(x0, z0, x1, z0);
  const seen = new Set();
  for (const [x, z] of posts) { const k = x.toFixed(2) + ',' + z.toFixed(2); if (seen.has(k)) continue; seen.add(k); part(box(0.2, 1.05, 0.2), M.white, x, 0.52, z, 0.03, g); part(cone(0.15, 0.22, 4), M.white, x, 1.15, z, 0.02, g).rotation.y = Math.PI / 4; }
}
function cantPortao(g) {
  const pg = new T.Group(); pg.position.set(0, 0, CERCA.z1); g.add(pg);
  [-1, 1].forEach((s) => { part(box(0.34, 2.9, 0.34), M.wood, s * (CERCA.gate + 0.1), 1.45, 0, 0.045, pg); part(sph(0.24, 10, 8), toon(0xffd23f), s * (CERCA.gate + 0.1), 3.05, 0, 0.03, pg); addCircle('cantinho', cwX(s * (CERCA.gate + 0.1)), cwZ(CERCA.z1), 0.3); });
  part(box(3.6, 0.3, 0.3), M.woodDark, 0, 2.75, 0, 0.04, pg);
  part(box(2.75, 0.6, 0.1), M.wood, 0, 2.25, 0.08, 0.035, pg);
  CANT.portao = new T.Mesh(new T.PlaneGeometry(2.6, 0.5), new T.MeshBasicMaterial({ color: 0xffffff })); CANT.portao.position.set(0, 2.25, 0.15); pg.add(CANT.portao);
  const gar = new T.Group(); pg.add(gar); seasonTag(gar, 'primavera', 'verao');
  for (let i = 0; i < 9; i++) { const t = i / 8; part(sph(0.13, 8, 6), toon(i % 2 ? 0x4fae4c : 0xff8fb8), lerp(-1.6, 1.6, t), 2.95 - Math.sin(t * Math.PI) * 0.18, 0.18, 0.02, gar); }
  const au = new T.Group(); pg.add(au); seasonTag(au, 'outono');
  for (let i = 0; i < 7; i++) { const l = part(sph(0.15, 8, 5), toon([0xf28a2e, 0xe0502a, 0xffb13b][i % 3]), lerp(-1.5, 1.5, i / 6), 2.95, 0.2, 0.02, au); l.scale.set(1, 0.45, 0.6); l.rotation.z = i; }
  const wi = new T.Group(); pg.add(wi); seasonTag(wi, 'inverno');
  part(box(3.7, 0.14, 0.4), M.snow, 0, 2.97, 0, 0.02, wi);
  for (let i = 0; i < 7; i++) part(sph(0.07, 6, 5), new T.MeshBasicMaterial({ color: [0xff4f6d, 0xffd23f, 0x3a86ff][i % 3] }), lerp(-1.5, 1.5, i / 6), 2.6 - Math.sin((i / 6) * Math.PI) * 0.12, 0.2, 0.012, wi);
}
function cantCanteiro(g) {
  const c = new T.Group(); c.position.set(CANTEIRO.x, 0, CANTEIRO.z); g.add(c); CANT.canteiroObj = c;
  part(box(3.7, 0.3, 0.16), M.wood, 0, 0.15, 0.72, 0.03, c); part(box(3.7, 0.3, 0.16), M.wood, 0, 0.15, -0.72, 0.03, c);
  part(box(0.16, 0.3, 1.6), M.wood, 1.85, 0.15, 0, 0.03, c); part(box(0.16, 0.3, 1.6), M.wood, -1.85, 0.15, 0, 0.03, c);
  part(box(3.55, 0.2, 1.3), CANT.mats.terra, 0, 0.12, 0, 0.02, c);
  CANTEIRO.slots.forEach((sx) => { const m = part(cyl(0.3, 0.34, 0.06, 12), toon(0x5a3d22), sx, 0.23, 0, 0, c); m.scale.z = 0.8; });
  tagS(part(box(3.5, 0.06, 1.25), M.snow, 0, 0.25, 0, 0, c), 'inverno');
  const pl = new T.Group(); pl.position.set(-2.25, 0, 0.95); c.add(pl);
  part(cyl(0.04, 0.04, 0.9, 5), M.woodDark, 0, 0.45, 0, 0.015, pl);
  const pp = part(box(0.62, 0.36, 0.06), M.paper, 0, 0.92, 0, 0.02, pl); pp.rotation.z = 0.06;
  const tx = textPlane('Canteiro', 0.56, 0.28, { bg: '#fff8ec', size: 62, weight: 900 }); tx.position.set(0, 0.92, 0.04); pl.add(tx);
  addBox('cantinho', cwX(CANTEIRO.x), cwZ(CANTEIRO.z), 1.95, 0.85);
}
function cantQuadro(g) {
  const q = new T.Group(); q.position.set(QUADRO_P.x, 0, QUADRO_P.z); q.rotation.y = -0.38; g.add(q); CANT.quadroObj = q;
  [-1.35, 1.35].forEach((s) => part(box(0.18, 2.95, 0.18), M.woodDark, s, 1.48, 0, 0.035, q));
  part(box(2.95, 2.2, 0.14), M.wood, 0, 1.95, 0.02, 0.045, q);
  CANT.quadroCanvas = mkCanvas(640, 480); CANT.quadroTex = canvasTex(CANT.quadroCanvas);
  const pl = new T.Mesh(new T.PlaneGeometry(2.7, 2.02), new T.MeshBasicMaterial({ map: CANT.quadroTex })); pl.position.set(0, 1.95, 0.1); q.add(pl);
  [-1, 1].forEach((s) => { const t = part(box(1.75, 0.12, 0.62), CANT.mats.telhado, s * 0.78, 3.28, 0.05, 0.03, q); t.rotation.z = -s * 0.32; });
  const fl = new T.Group(); q.add(fl); tagS(fl, 'primavera', 'verao');
  for (let i = 0; i < 5; i++) { part(cyl(0.025, 0.025, 0.4, 5), toon(0x3c9a3c), -1.0 + i * 0.5, 0.2, 0.25, 0, fl); part(sph(0.12, 8, 6), toon([0xff8fb8, 0xffd23f, 0xa77bff, 0xffffff, 0xff5e5e][i]), -1.0 + i * 0.5, 0.45, 0.25, 0.02, fl); }
  tagS(part(box(3.0, 0.1, 0.3), M.snow, 0, 3.08, 0.05, 0.015, q), 'inverno');
  addCircle('cantinho', cwX(QUADRO_P.x - 1.2), cwZ(QUADRO_P.z + 0.45), 0.3); addCircle('cantinho', cwX(QUADRO_P.x + 1.2), cwZ(QUADRO_P.z - 0.45), 0.3);
}
function cantCaixaCorreio(g) {
  const m = new T.Group(); m.position.set(CAIXA_P.x, 0, CAIXA_P.z); g.add(m); CANT.caixaObj = m;
  part(cyl(0.09, 0.09, 1.3, 8), M.woodDark, 0, 0.65, 0, 0.025, m);
  part(box(0.75, 0.55, 1.0), CANT.mats.porta, 0, 1.5, 0, 0.045, m);
  const top = part(cyl(0.375, 0.375, 1.0, 14), CANT.mats.porta, 0, 1.78, 0, 0.045, m); top.rotation.x = Math.PI / 2;
  part(box(0.06, 0.5, 0.2), toon(0xe5383b), 0.42, 1.85, 0.2, 0.02, m);
  const pl = part(box(0.8, 0.3, 0.05), M.paper, 0, 1.0, 0.1, 0.02, m); void pl;
  CANT.caixaPlaca = new T.Mesh(new T.PlaneGeometry(0.74, 0.25), new T.MeshBasicMaterial({ color: 0xffffff })); CANT.caixaPlaca.position.set(0, 1.0, 0.135); m.add(CANT.caixaPlaca);
  tagS(part(box(0.8, 0.1, 1.05), M.snow, 0, 2.14, 0, 0.015, m), 'inverno');
  addCircle('cantinho', cwX(CAIXA_P.x), cwZ(CAIXA_P.z), 0.45);
}
function cantLata(g) {
  const l = new T.Group(); l.position.set(LATA_P.x, 0, LATA_P.z); g.add(l); CANT.lataObj = l;
  part(cyl(0.34, 0.3, 0.6, 14), toon(0xc9ced8), 0, 0.3, 0, 0.035, l);
  CANT.tintaLata = part(cyl(0.3, 0.3, 0.06, 14), CANT.mats.telhado, 0, 0.6, 0, 0.015, l);
  const al = part(tor(0.3, 0.03, 5, 14, Math.PI), M.ink, 0, 0.62, 0, 0, l); void al;
  const br = new T.Group(); br.position.set(0.15, 0.66, 0.05); br.rotation.z = -0.6; l.add(br);
  part(box(0.07, 0.6, 0.07), M.wood, 0, 0.3, 0, 0.015, br); part(box(0.18, 0.18, 0.1), CANT.mats.parede, 0, 0.0, 0, 0.015, br);
  [[0xff6f91, -0.5, 0.2], [0x6ec6ff, 0.45, 0.3], [0xffd23f, 0.1, -0.45]].forEach(([c, x, z]) => { const s = part(cyl(0.18, 0.2, 0.02, 10), toon(c), x, 0.015, z, 0.01, l); s.scale.z = 0.7; });
  addCircle('cantinho', cwX(LATA_P.x), cwZ(LATA_P.z), 0.42);
}
function cantPlacaVolta(g) {
  const p = new T.Group(); p.position.set(VOLTA_P.x, 0, VOLTA_P.z); g.add(p);
  part(box(0.18, 2.6, 0.18), M.woodDark, 0, 1.3, 0, 0.03, p);
  const sh = new T.Shape(); sh.moveTo(-1.3, -0.3); sh.lineTo(1.0, -0.3); sh.lineTo(1.3, 0); sh.lineTo(1.0, 0.3); sh.lineTo(-1.3, 0.3); sh.closePath();
  const ag = new T.ExtrudeGeometry(sh, { depth: 0.1, bevelEnabled: false }); ag.translate(0, 0, -0.05);
  const arrow = part(ag, M.wood, 0, 2.1, 0, 0.035, p); arrow.rotation.y = Math.PI;
  const tx = textPlane('Praça da Vila', 2.1, 0.46, { bg: '#f6deb2', size: 64, weight: 900 }); tx.position.set(0.1, 2.1, 0.06); p.add(tx);
  const a2 = part(ag, M.wood, 0, 1.45, 0, 0.035, p); a2.scale.set(0.85, 0.85, 1);
  const tx2 = textPlane('Rua dos Cantinhos', 1.8, 0.4, { bg: '#ffd9e8', size: 60, weight: 900 }); tx2.position.set(-0.05, 1.45, 0.06); p.add(tx2);
  addCircle('cantinho', cwX(VOLTA_P.x), cwZ(VOLTA_P.z), 0.3);
}
function cantArvore(g, x, z, s, kind) {
  const t = new T.Group(); t.position.set(x, 0, z); t.scale.setScalar(s); g.add(t);
  if (kind === 'pine') {
    part(cyl(0.25, 0.32, 1.2, 8), M.trunk, 0, 0.6, 0, 0.05, t);
    [[1.9, 2.2, 1.75], [1.5, 1.9, 2.9], [1.0, 1.5, 3.95]].forEach(([r, hh, y]) => part(cone(r, hh, 10), M.pine, 0, y, 0, 0.08, t));
    [[1.55, 0.5, 2.55], [1.1, 0.5, 3.6], [0.6, 0.5, 4.5]].forEach(([r, hh, y]) => seasonTag(part(cone(r, hh, 10), M.snow, 0, y, 0, 0.04, t), 'inverno'));
  } else {
    part(cyl(0.28, 0.42, 2.3, 8), M.trunk, 0, 1.15, 0, 0.06, t);
    const f1 = part(sph(1.65, 14, 10), M.leafA, 0, 3.2, 0, 0.09, t); f1.scale.set(1, 0.92, 1);
    part(sph(1.15, 12, 9), M.leafB, -1.15, 2.65, 0.35, 0.08, t); part(sph(1.0, 12, 9), M.leafA, 1.05, 2.85, -0.25, 0.08, t);
    const fr = new T.Group(); t.add(fr); seasonTag(fr, 'primavera', 'verao');
    for (let i = 0; i < 5; i++) { const a = i * 1.3; part(sph(0.16, 8, 6), toon(i % 2 ? 0xffffff : 0xff4f6d), Math.cos(a) * 1.35, 3.0 + Math.sin(i * 2) * 0.6, Math.sin(a) * 1.35 + 0.3, 0.025, fr); }
  }
  t.userData.ph = x * 0.3 + z * 0.17; CANT.trees.push(t);
  addCircle('cantinho', cwX(x), cwZ(z), 0.65 * s);
}
function cantVizinho(g, x, parede, telhado, seed) {
  const v = new T.Group(); v.position.set(x, 0, -4.6); g.add(v);
  part(box(5.6, 0.4, 4.4), toon(0xa59aa8), 0, 0.2, 0, 0.05, v);
  part(box(5.0, 3.0, 3.8), toon(parede), 0, 1.9, 0, 0.08, v);
  const sh = new T.Shape(); sh.moveTo(-3.0, 0); sh.lineTo(3.0, 0); sh.lineTo(0, 2.1); sh.closePath();
  const rg = new T.ExtrudeGeometry(sh, { depth: 4.5, bevelEnabled: false }); rg.translate(0, 0, -2.25); part(rg, toon(telhado), 0, 3.4, 0, 0.09, v);
  const slope = Math.atan2(2.1, 3.0), sl = Math.hypot(2.1, 3.0);
  [-1, 1].forEach((s) => { const sn = part(box(sl * 0.92, 0.18, 4.4), M.snow, s * 1.55, 4.55, 0, 0.035, v); sn.rotation.z = -s * slope; seasonTag(sn, 'inverno'); });
  part(box(1.1, 1.9, 0.2), toon(misturaCor(telhado, 0x221a2b, 0.25)), 0, 1.35, 1.95, 0.04, v);
  [-1.6, 1.6].forEach((wx) => { part(box(1.0, 0.95, 0.18), toon(0xfff3d6), wx, 2.3, 1.93, 0.04, v); part(box(0.78, 0.72, 0.2), ROOM_WIN, wx, 2.3, 1.96, 0, v); });
  const R = seeded(seed); for (let i = 0; i < 3; i++) { part(cyl(0.03, 0.03, 0.42, 5), toon(0x3c9a3c), -1.0 + i * 1.0 + R() * 0.3, 0.21, 3.2, 0, v); part(sph(0.14, 8, 6), toon([0xff8fb8, 0xffd23f, 0xa77bff][i]), -1.0 + i * 1.0, 0.45, 3.2, 0.02, v); }
  addBox('cantinho', cwX(x), cwZ(-4.6), 2.9, 2.3);
  cantCerca(g, x - 5.5, x + 5.5, -9.4, 5.6, 1.2, true);
}
function cantMorroVila(g) {
  // a vila lá no morro, ao fundo: a criança sabe onde está a praça
  const R = 14, hx = -12, hz = -27, hy = -9.2;
  const morro = part(sph(R, 28, 16), M.grass2, hx, hy, hz, 0.12, g); morro.scale.z = 0.8;
  const altura = (dx, dz) => hy + Math.sqrt(Math.max(0, R * R - dx * dx - (dz / 0.8) * (dz / 0.8)));
  const mini = (dx, dz, wall, roof, s = 0.42) => {
    const c = new T.Group(); c.position.set(hx + dx, altura(dx, dz) - 0.1, hz + dz); c.scale.setScalar(s); g.add(c);
    part(box(3.0, 2.4, 2.4), toon(wall), 0, 1.2, 0, 0.12, c);
    const r = part(cone(2.4, 1.8, 4), toon(roof), 0, 3.3, 0, 0.12, c); r.rotation.y = Math.PI / 4; r.scale.z = 0.8;
    seasonTag(part(cone(1.4, 0.6, 4), M.snow, 0, 3.95, 0, 0.06, c), 'inverno');
    part(box(0.8, 1.2, 0.1), M.woodDark, 0, 0.6, 1.22, 0.06, c);
  };
  const defs = Object.fromEntries(HOUSE_DEFS.map((d) => [d.id, d]));
  mini(0, -2.2, defs.pena.wall, defs.pena.roof, 0.5); mini(-4.2, -0.8, defs.biblioteca.wall, defs.biblioteca.roof); mini(4.0, -0.6, defs.atelie.wall, defs.atelie.roof);
  mini(-6.6, 1.8, defs.grafica.wall, defs.grafica.roof, 0.38); mini(6.4, 2.0, defs.correio.wall, defs.correio.roof, 0.38);
  const f = new T.Group(); f.position.set(hx, altura(0, 1.8) - 0.05, hz + 1.8); f.scale.setScalar(0.5); g.add(f);
  part(cyl(1.4, 1.5, 0.5, 18), M.stone2, 0, 0.25, 0, 0.1, f); part(cyl(0.25, 0.3, 1.2, 10), M.stone2, 0, 1.0, 0, 0.06, f);
  [-1, 1].forEach((s) => { const b = part(box(0.6, 0.08, 0.8), toon(0xe5533d), s * 0.3, 1.75, 0, 0.06, f); b.rotation.z = s * 0.3; });
  [[-2, -6.5, 'round'], [2.5, -6.0, 'pine'], [-9, -2, 'pine'], [9.5, -2.5, 'round']].forEach(([dx, dz, k]) => { const tg = new T.Group(); tg.position.set(hx + dx, altura(dx, dz) - 0.2, hz + dz); tg.scale.setScalar(0.55); g.add(tg); if (k === 'pine') { part(cyl(0.25, 0.32, 1.2, 8), M.trunk, 0, 0.6, 0, 0.08, tg); part(cone(1.6, 2.6, 10), M.pine, 0, 2.3, 0, 0.12, tg); } else { part(cyl(0.28, 0.4, 2.0, 8), M.trunk, 0, 1.0, 0, 0.08, tg); part(sph(1.5, 12, 9), M.leafA, 0, 2.8, 0, 0.12, tg); } });
  const m2 = part(sph(12, 24, 14), M.grass2, 17, -8.5, -29, 0.12, g); m2.scale.z = 0.75;
}
function cantSazonais(g) {
  const sp = { primavera: new T.Group(), verao: new T.Group(), outono: new T.Group(), inverno: new T.Group() };
  for (const k in sp) { g.add(sp[k]); tagS(sp[k], k); }
  const flor = (grp, x, z, c) => { part(cyl(0.03, 0.03, 0.42, 5), toon(0x3c9a3c), x, 0.21, z, 0, grp); part(sph(0.14, 8, 6), toon(c), x, 0.47, z, 0.025, grp); };
  // primavera: flores pela cerca e borboletas
  for (let i = 0; i < 12; i++) { const z = -8.6 + i * 1.3; flor(sp.primavera, -8.55, z, [0xff8fb8, 0xffffff, 0xa77bff, 0xffd23f][i % 4]); flor(sp.primavera, 8.55, z + 0.4, [0xffd23f, 0xff8fb8, 0xffffff][i % 3]); }
  for (let i = 0; i < 3; i++) { const b = new T.Group(); const c = [0xffd23f, 0x8fd3ff, 0xff8fb8][i]; const w1 = part(box(0.3, 0.02, 0.24), toon(c), -0.16, 0, 0, 0.02, b), w2 = part(box(0.3, 0.02, 0.24), toon(c), 0.16, 0, 0, 0.02, b); b.userData = { w1, w2, ph: i * 2.1, cx: [-4, 3, 6][i], cz: [3, -0.5, 2.5][i] }; sp.primavera.add(b); CANT.butterflies.push(b); }
  // verão: girassóis, boia e baldinho
  [[-8.2, -3.4], [8.2, -2.4], [-7.8, 2.6]].forEach(([x, z]) => { const s = new T.Group(); s.position.set(x, 0, z); sp.verao.add(s); part(cyl(0.05, 0.07, 2.0, 6), toon(0x3c9a3c), 0, 1.0, 0, 0.025, s); const fl = part(cyl(0.48, 0.48, 0.1, 16), toon(0xffd23f), 0, 2.05, 0.08, 0.04, s); fl.rotation.x = Math.PI / 2 - 0.3; const ce = part(cyl(0.24, 0.24, 0.12, 14), toon(0x8b5a2b), 0, 2.05, 0.12, 0.02, s); ce.rotation.x = Math.PI / 2 - 0.3; });
  const boia = part(tor(0.42, 0.16, 8, 18), toon(0xff5e5e), 7.4, 0.17, 6.0, 0.03, sp.verao); boia.rotation.x = Math.PI / 2;
  part(cyl(0.2, 0.16, 0.36, 10), toon(0x38c6c0), 6.6, 0.18, 6.3, 0.025, sp.verao);
  // outono: folhas no chão e um monte de folhas
  const R = seeded(77);
  for (let i = 0; i < 26; i++) { const x = R() * 16 - 8, z = R() * 14 - 7.5; if (Math.abs(x) < 3.6 && z < -2) continue; const l = part(sph(0.17, 7, 4), toon([0xf28a2e, 0xe0502a, 0xffb13b][i % 3]), x, 0.04, z, 0.015, sp.outono); l.scale.set(1, 0.18, 0.6); l.rotation.y = R() * 6; }
  const mt = part(sph(0.95, 12, 8), toon(0xd9502b), 7.0, 0.05, -6.6, 0.04, sp.outono); mt.scale.y = 0.42;
  // inverno: bonequinho de neve e montinhos
  const bn = new T.Group(); bn.position.set(7.3, 0, 6.0); sp.inverno.add(bn);
  part(sph(0.55, 14, 10), M.snow, 0, 0.5, 0, 0.05, bn); part(sph(0.4, 14, 10), M.snow, 0, 1.25, 0, 0.045, bn); part(sph(0.3, 12, 9), M.snow, 0, 1.85, 0, 0.04, bn);
  const n = part(cone(0.07, 0.32, 8), toon(0xff8a3c), 0, 1.85, 0.36, 0.015, bn); n.rotation.x = Math.PI / 2;
  part(cyl(0.42, 0.42, 0.13, 14), toon(0xe5383b), 0, 1.55, 0, 0.025, bn); part(cyl(0.22, 0.22, 0.3, 12), M.ink, 0, 2.22, 0, 0.025, bn);
  [[-6.5, -6.0], [6.8, -6.5], [-7.4, 5.5], [3.0, 5.6], [-12, 9], [13, 9.4]].forEach(([x, z]) => { const m = part(sph(0.8, 12, 8), M.snow, x, 0, z, 0.035, sp.inverno); m.scale.y = 0.4; });
}

// ---------- interior: a casinha de boneca ----------
function vistaCanvas(k) {
  const c = mkCanvas(512, 400), g = c.getContext('2d'); g.lineWidth = 6; const P2 = painter(g); g.lineWidth = 6;
  const V = { primavera: ['#bfe6ff', '#8fd16c', '#7cc25c'], verao: ['#8fd4ff', '#7ccf55', '#68bd45'], outono: ['#f8dcb6', '#c4b35a', '#b09d47'], inverno: ['#dee8f3', '#f4f7fb', '#e3eaf3'] }[k];
  g.fillStyle = V[0]; g.fillRect(0, 0, 512, 400);
  if (k !== 'inverno') P2.c(410, 86, k === 'verao' ? 52 : 42, '#ffd23f');
  [[110, 80, 60, 26, 2], [300, 120, 48, 22, 5]].forEach(([x, y, rx, ry, s]) => P2.blob(x, y, rx, ry, s, '#ffffff', 0.12));
  if (k === 'verao') { g.fillStyle = '#46c2ff'; g.fillRect(0, 238, 512, 56); P2.l([0, 238, 512, 238], 5); g.save(); g.strokeStyle = '#ffffff'; g.lineWidth = 5; for (let i = 0; i < 6; i++) { g.beginPath(); g.arc(40 + i * 90, 262, 16, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); } g.restore(); }
  P2.blob(130, 400, 250, 140, 3, V[1], 0.06); P2.blob(420, 420, 240, 160, 6, V[2], 0.06);
  const arvore = (x, y, s, cor, pine) => { if (pine) { P2.p([x, y - 90 * s, x - 34 * s, y, x + 34 * s, y], cor); P2.r(x - 6 * s, y, 12 * s, 22 * s, 3, '#8b5a2b'); } else { P2.r(x - 7 * s, y - 20 * s, 14 * s, 44 * s, 4, '#8b5a2b'); P2.blob(x, y - 50 * s, 44 * s, 40 * s, Math.round(x), cor, 0.1); } };
  if (k === 'primavera') { arvore(110, 300, 1, '#ffa9c9'); arvore(380, 310, 0.9, '#ffa9c9'); P2.ns = true; [[60, 340], [210, 330], [300, 352], [450, 340]].forEach(([x, y], i) => P2.c(x, y, 8, ['#ff8fb8', '#ffffff', '#a77bff', '#ffd23f'][i])); P2.ns = false; }
  if (k === 'verao') { arvore(120, 320, 1, '#5fc24b'); arvore(400, 330, 0.9, '#3fa53f'); }
  if (k === 'outono') { arvore(110, 300, 1, '#f28a2e'); arvore(390, 310, 0.95, '#d9502b'); P2.ns = true; for (let i = 0; i < 10; i++) P2.e(40 + i * 48, 120 + ((i * 53) % 150), 10, 5, i, ['#f28a2e', '#e0502a', '#ffb13b'][i % 3]); P2.ns = false; }
  if (k === 'inverno') { arvore(110, 310, 1.1, '#3f7a5a', true); arvore(400, 320, 1.0, '#3f7a5a', true); g.save(); g.fillStyle = '#ffffff'; for (let i = 0; i < 26; i++) { g.beginPath(); g.arc((i * 97) % 512, (i * 61) % 300, 5 + (i % 3) * 2, 0, 7); g.fill(); } g.restore(); }
  return c;
}
function desenhaPapelParede(cor) {
  const c = CANT.wpCanvas, g = c.getContext('2d'), base = misturaCor(cor, 0xffffff, 0.45), pat = misturaCor(cor, 0x221a2b, 0.12);
  g.fillStyle = hexCss(base); g.fillRect(0, 0, 256, 256); g.fillStyle = hexCss(pat);
  for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
    const px = 32 + x * 64 + (y % 2) * 32, py = 32 + y * 64;
    if ((x + y) % 2) { g.beginPath(); g.moveTo(px, py + 9); g.bezierCurveTo(px - 14, py - 2, px - 7, py - 13, px, py - 5); g.bezierCurveTo(px + 7, py - 13, px + 14, py - 2, px, py + 9); g.fill(); }
    else { g.beginPath(); g.arc(px, py, 5, 0, 7); g.fill(); }
  }
  if (CANT.wp) CANT.wp.forEach((t) => (t.needsUpdate = true));
}
function buildCantinhoRoom() {
  const id = 'cantinhoCasa', ox = CANT_OX, g = new T.Group(); g.position.set(ox, 0, 0); g.visible = false; scene.add(g);
  const room = { id, ox, g, d: { floor: '#d9a066' } }; ROOMS[id] = room; CANT.room = room;
  BOUNDS[id] = { x0: ox - 6.3, x1: ox + 6.3, z0: -4.25, z1: 4.75 };
  CANT.wpCanvas = mkCanvas(256, 256); desenhaPapelParede(0xfff1d6);
  const wp = canvasTex(CANT.wpCanvas); wp.wrapS = wp.wrapT = T.RepeatWrapping; wp.repeat.set(3, 1.2);
  const wpS = canvasTex(CANT.wpCanvas); wpS.wrapS = wpS.wrapT = T.RepeatWrapping; wpS.repeat.set(2.2, 1.2); CANT.wp = [wp, wpS];
  const wallM = new T.MeshToonMaterial({ color: 0xffffff, map: wp, gradientMap: GRAD }), wallS = new T.MeshToonMaterial({ color: 0xf2ece4, map: wpS, gradientMap: GRAD });
  const floorM = new T.MeshToonMaterial({ color: 0xffffff, map: planks('#d9a066'), gradientMap: GRAD });
  part(box(14, 0.4, 10), floorM, 0, -0.2, 0, 0.07, g);
  part(box(14.4, 5.8, 0.4), wallM, 0, 2.9, -5.2, 0.08, g);
  part(box(0.4, 5.8, 10.4), wallS, -7.2, 2.9, 0, 0.08, g); part(box(0.4, 5.8, 10.4), wallS, 7.2, 2.9, 0, 0.08, g);
  part(box(14, 0.35, 0.16), M.woodDark, 0, 0.17, -4.94, 0.03, g); [-1, 1].forEach((s) => part(box(0.16, 0.35, 10), M.woodDark, s * 6.94, 0.17, 0, 0.03, g));
  part(box(14.8, 0.55, 0.5), M.wood, 0, 0.0, 5.25, 0.06, g);
  const rug = part(cyl(2.4, 2.4, 0.05, 36), M.rug, 0.4, 0.03, 1.5, 0.04, g); rug.scale.z = 0.6;
  part(box(2.2, 0.05, 0.9), toon(0xb5651d), 0, 0.03, 4.45, 0.03, g);
  const mt = textPlane('SAIR', 1.9, 0.6, { bg: '#c8783a', fg: '#fff8ec', size: 70, weight: 900 }); mt.rotation.x = -Math.PI / 2; mt.position.set(0, 0.06, 4.45); g.add(mt);
  inter({ area: id, x: ox, z: 4.45, r: 1.6, y: 1.4, label: () => '🚪 Sair para o jardim', act: () => Cantinho.sairCasa() });
  // janela com vista da estação
  const w = new T.Group(); w.position.set(2.5, 3.25, -4.95); g.add(w);
  part(box(2.75, 2.25, 0.2), toon(0xfff3d6), 0, 0, 0, 0.06, w);
  for (const k of Object.keys(SEASONS)) { const pl = new T.Mesh(new T.PlaneGeometry(2.35, 1.85), new T.MeshBasicMaterial({ map: canvasTex(vistaCanvas(k)) })); pl.position.z = 0.115; w.add(pl); seasonTag(pl, k); }
  part(box(2.35, 0.09, 0.26), toon(0xfff3d6), 0, 0, 0.04, 0, w); part(box(0.09, 1.85, 0.26), toon(0xfff3d6), 0, 0, 0.04, 0, w);
  part(box(3.0, 0.16, 0.5), M.wood, 0, -1.2, 0.18, 0.04, w);
  [-1, 1].forEach((s) => { const c = part(box(0.5, 2.5, 0.12), CANT.mats.cortina, s * 1.62, 0.05, 0.26, 0.04, w); c.rotation.z = s * 0.06; });
  seasonalDecor(w, -0.85, -1.12, 0.22);
  inter({ area: id, x: rw(id, 3.1), z: -3.35, r: 1.4, y: 4.6, label: () => '🪟 Olhar pela janela', act: () => Cantinho.olharJanela() });
  // quadro da história na parede
  const qf = new T.Group(); qf.position.set(-2.15, 3.2, -4.96); g.add(qf); CANT.quadroIn = qf;
  part(box(2.8, 2.15, 0.16), M.woodDark, 0, 0, 0, 0.05, qf);
  const qp = new T.Mesh(new T.PlaneGeometry(2.55, 1.91), new T.MeshBasicMaterial({ map: CANT.quadroTex })); qp.position.z = 0.09; qf.add(qp);
  part(sph(0.08, 8, 6), M.gold, 0, 1.25, 0.05, 0.02, qf);
  inter({ area: id, x: rw(id, -2.15), z: -3.25, r: 1.4, y: 5.0, label: () => (CANT.dono ? '🖼 Ver o quadro' : '🖼 Quadro da história'), act: () => Cantinho.abrirQuadro() });
  // cama (dá para deitar)
  const bed = new T.Group(); bed.position.set(-5.2, 0, -0.9); g.add(bed);
  part(box(3.4, 0.45, 2.0), M.wood, 0, 0.42, 0, 0.05, bed);
  [[-1.55, -0.85], [1.55, -0.85], [-1.55, 0.85], [1.55, 0.85]].forEach(([x, z]) => part(box(0.18, 0.25, 0.18), M.woodDark, x, 0.12, z, 0.02, bed));
  part(box(3.2, 0.3, 1.85), M.white, 0.05, 0.8, 0, 0.04, bed);
  part(box(2.2, 0.16, 1.95), CANT.mats.colcha, 0.55, 0.98, 0, 0.04, bed);
  part(box(0.7, 0.26, 1.3), toon(0xfffdf5), -1.15, 1.07, 0, 0.035, bed);
  part(box(0.24, 1.7, 2.1), M.wood, -1.72, 0.85, 0, 0.05, bed);
  const cor = part(sph(0.2, 10, 8), toon(0xff6f91), -1.58, 1.4, 0, 0.03, bed); cor.scale.set(0.4, 1, 1);
  addBox(id, rw(id, -5.2), -0.9, 1.75, 1.05);
  inter({ area: id, x: rw(id, -4.2), z: 0.75, r: 1.5, y: 2.2, obj: bed, hopH: 0.08, label: () => (P.sitting ? null : '🛏 Deitar na cama'), act: () => { sitAt(rw(id, -5.0), -0.9, 0.85, 1); Snd.boing(); } });
  // luminária (acende e apaga)
  const lp = new T.Group(); lp.position.set(-6.15, 0, -3.75); g.add(lp); CANT.lampG = lp;
  part(cyl(0.38, 0.42, 0.12, 14), M.ink, 0, 0.06, 0, 0.03, lp); part(cyl(0.05, 0.05, 2.5, 8), M.ink, 0, 1.3, 0, 0.02, lp);
  CANT.shadeOff = toon(0xffd23f); CANT.shadeOn = new T.MeshBasicMaterial({ color: 0xfff0b0 });
  CANT.shade = part(cone(0.6, 0.62, 16), CANT.shadeOff, 0, 2.75, 0, 0.04, lp);
  part(sph(0.13, 10, 8), M.lamp, 0, 2.45, 0, 0, lp);
  const lt = new T.PointLight(0xffc46b, 0, 11, 1.4); lt.position.set(ox - 6.0, 2.6, -3.3); scene.add(lt); CANT.lampLight = lt;
  addCircle(id, rw(id, -6.15), -3.75, 0.45);
  inter({ area: id, x: rw(id, -5.3), z: -2.75, r: 1.4, y: 3.5, obj: lp, hopH: 0.1, label: () => (CANT.lampOn ? '💡 Apagar a luminária' : '💡 Acender a luminária'), act: () => Cantinho.luz() });
  // baú (criações e selos)
  const ch = new T.Group(); ch.position.set(0.3, 0, -4.3); g.add(ch);
  part(box(1.6, 0.85, 1.0), toon(0xb5651d), 0, 0.43, 0, 0.055, ch); [-0.5, 0.5].forEach((x) => part(box(0.13, 0.87, 1.04), M.gold, x, 0.43, 0, 0, ch));
  const lid = new T.Group(); lid.position.set(0, 0.85, -0.5); ch.add(lid);
  part(box(1.6, 0.32, 1.0), toon(0xc8752a), 0, 0.16, 0.5, 0.045, lid); part(box(0.28, 0.28, 0.1), M.gold, 0, 0.0, 1.02, 0.02, lid);
  CANT.bauLid = lid;
  addBox(id, rw(id, 0.3), -4.3, 0.9, 0.6);
  inter({ area: id, x: rw(id, 0.3), z: -3.05, r: 1.4, y: 1.9, obj: ch, hopH: 0.18, label: () => (CANT.dono ? null : '🧰 Baú do cantinho'), act: () => Cantinho.abrirBau() });
  // escrivaninha com cadeira
  const dk = new T.Group(); dk.position.set(5.2, 0, -4.2); g.add(dk);
  part(box(2.4, 0.14, 1.15), M.wood, 0, 1.05, 0, 0.045, dk);
  [[-1.08, -0.45], [1.08, -0.45], [-1.08, 0.45], [1.08, 0.45]].forEach(([x, z]) => part(box(0.14, 1.0, 0.14), M.woodDark, x, 0.5, z, 0.025, dk));
  part(box(1.0, 0.32, 0.9), M.woodDark, 0.55, 0.78, 0.05, 0.03, dk); part(sph(0.06, 8, 6), M.gold, 0.55, 0.78, 0.53, 0.015, dk);
  const its = new T.Group(); dk.add(its);
  part(box(0.62, 0.05, 0.46), toon(0xe5533d), -0.45, 1.15, 0.15, 0.02, its); part(box(0.56, 0.02, 0.4), M.paper, -0.45, 1.19, 0.15, 0.01, its);
  part(cyl(0.13, 0.11, 0.3, 10), toon(0x6ec6ff), 0.75, 1.27, -0.2, 0.02, its);
  [0xff4f6d, 0xffd23f, 0x4fae4c].forEach((c, i) => { const p = part(cyl(0.03, 0.03, 0.45, 6), toon(c), 0.7 + i * 0.05, 1.45, -0.2, 0.012, its); p.rotation.z = (i - 1) * 0.2; });
  const fr = new T.Group(); fr.position.set(0.15, 1.12, -0.35); fr.rotation.x = -0.15; its.add(fr);
  part(box(0.44, 0.54, 0.05), M.woodDark, 0, 0.27, 0, 0.02, fr);
  CANT.fotoMat = new T.MeshBasicMaterial({ color: 0xffffff, transparent: true, alphaTest: 0.1 }); const ft = new T.Mesh(new T.PlaneGeometry(0.36, 0.44), CANT.fotoMat); ft.position.set(0, 0.27, 0.03); fr.add(ft);
  seasonalDecor(g, 6.05, 1.12, -4.45);
  const cd = new T.Group(); cd.position.set(5.2, 0, -2.95); g.add(cd);
  part(box(0.8, 0.12, 0.75), M.wood, 0, 0.62, 0, 0.03, cd); part(box(0.8, 0.85, 0.1), M.wood, 0, 1.05, 0.34, 0.03, cd);
  [[-0.32, -0.3], [0.32, -0.3], [-0.32, 0.3], [0.32, 0.3]].forEach(([x, z]) => part(box(0.08, 0.6, 0.08), M.woodDark, x, 0.3, z, 0.015, cd));
  addBox(id, rw(id, 5.2), -4.2, 1.25, 0.62); addBox(id, rw(id, 5.2), -2.95, 0.42, 0.4);
  inter({ area: id, x: rw(id, 5.2), z: -1.85, r: 1.5, y: 2.6, obj: its, hopH: 0.12, label: () => (P.sitting ? null : CANT.dono ? '🪑 Sentar na cadeira' : '✏️ Escrivaninha'), act: () => Cantinho.escrivaninha() });
  // estantinha na parede da direita
  const es = new T.Group(); es.position.set(6.5, 0, 1.3); es.rotation.y = -Math.PI / 2; g.add(es);
  part(box(2.1, 2.4, 0.1), M.woodDark, 0, 1.2, -0.32, 0.04, es);
  [-1, 1].forEach((s) => part(box(0.12, 2.4, 0.7), M.wood, s * 1.0, 1.2, 0, 0.04, es));
  [0.1, 0.9, 1.7, 2.45].forEach((y) => part(box(2.12, 0.1, 0.72), M.wood, 0, y, 0, 0.03, es));
  const books = new T.Group(); es.add(books); const RB = seeded(9);
  [0.15, 0.95].forEach((y) => { let bx = -0.85; while (bx < 0.75) { const bw = 0.14 + RB() * 0.12, bh = 0.45 + RB() * 0.25; part(box(bw, bh, 0.45), toon([0xe5533d, 0x3a86ff, 0x4fae4c, 0xffd23f, 0xa77bff, 0xff8fb8][Math.floor(RB() * 6)]), bx + bw / 2, y + 0.05 + bh / 2, 0, 0.02, books); bx += bw + 0.03; } });
  const ml = new T.Group(); ml.position.set(-0.3, 1.78, 0.05); ml.rotation.y = 0.3; es.add(ml); CANT.miniLivro = ml;
  part(box(0.5, 0.62, 0.16), toon(0xffd23f), 0, 0.31, 0, 0.025, ml); part(box(0.04, 0.7, 0.02), toon(0xff4f6d), 0.12, 0.3, 0.09, 0.01, ml);
  part(cyl(0.16, 0.12, 0.26, 10), toon(0xd9774a), 0.55, 1.88, 0, 0.02, es); part(sph(0.22, 10, 8), toon(0x5cc05a), 0.55, 2.13, 0, 0.025, es);
  addBox(id, rw(id, 6.5), 1.3, 0.42, 1.1);
  inter({ area: id, x: rw(id, 5.3), z: 1.3, r: 1.5, y: 3.0, obj: books, hopH: 0.12, label: () => (CANT.dono ? `📚 Estante de ${CANT.dono.n}` : '📚 Minha estante'), act: () => Cantinho.estante() });
  // enfeites da estação no chão e luzinhas de inverno
  const sp = { primavera: new T.Group(), verao: new T.Group(), outono: new T.Group(), inverno: new T.Group() };
  for (const k in sp) { sp[k].position.set(-5.7, 0, 3.0); g.add(sp[k]); tagS(sp[k], k); }
  part(cyl(0.45, 0.32, 0.7, 14), toon(0x6ec6ff), 0, 0.35, 0, 0.04, sp.primavera); for (let i = 0; i < 7; i++) { const a = (i / 7) * Math.PI * 2; part(cyl(0.03, 0.03, 0.6, 5), toon(0x3c9a3c), Math.cos(a) * 0.2, 0.95, Math.sin(a) * 0.2, 0, sp.primavera); part(sph(0.14, 8, 6), toon([0xff8fb8, 0xffd23f, 0xffffff, 0xa77bff][i % 4]), Math.cos(a) * 0.24, 1.28, Math.sin(a) * 0.24, 0.02, sp.primavera); }
  const bola = new T.Group(); bola.position.y = 0.5; sp.verao.add(bola); part(sph(0.5, 16, 10), M.white, 0, 0, 0, 0.04, bola); [0xff5e5e, 0x3a86ff].forEach((c, i) => part(new T.SphereGeometry(0.506, 16, 10, (i / 2) * Math.PI * 2, Math.PI / 2), toon(c), 0, 0, 0, 0, bola));
  part(cyl(0.25, 0.2, 0.42, 10), toon(0x38c6c0), 0.9, 0.21, 0.3, 0.025, sp.verao);
  [[-0.2, 0, 0.55], [0.45, 0.25, 0.42]].forEach(([x, z, r]) => { const p = part(sph(r, 14, 10), toon(0xf28a2e), x, r * 0.75, z, 0.04, sp.outono); p.scale.y = 0.75; part(cyl(0.04, 0.05, 0.16, 6), toon(0x5a7a2e), x, r * 1.5, z, 0.015, sp.outono); });
  part(cyl(0.12, 0.15, 0.4, 8), M.trunk, 0, 0.2, 0, 0.025, sp.inverno);
  [[0.8, 1.1, 0.85], [0.6, 0.9, 1.5], [0.38, 0.7, 2.05]].forEach(([r, hh, y]) => part(cone(r, hh, 10), M.pine, 0, y, 0, 0.04, sp.inverno));
  part(new T.OctahedronGeometry(0.16), M.gold, 0, 2.5, 0, 0.02, sp.inverno);
  for (let i = 0; i < 10; i++) { const a = i * 1.9, y = 0.7 + (i / 10) * 1.6, r = 0.75 - (i / 10) * 0.5; const m = new T.MeshBasicMaterial({ color: [0xff4f6d, 0xffd23f, 0x3a86ff, 0x7dffb0][i % 4] }); part(sph(0.07, 6, 5), m, Math.cos(a) * r, y, Math.sin(a) * r, 0.012, sp.inverno); CANT.luzes.push({ m, c: m.color.getHex(), ph: i }); }
  part(box(0.5, 0.4, 0.5), toon(0xe5383b), 0.75, 0.2, 0.35, 0.03, sp.inverno); part(box(0.52, 0.08, 0.1), toon(0xffd23f), 0.75, 0.41, 0.35, 0, sp.inverno);
  addCircle(id, rw(id, -5.7), 3.0, 0.7);
  const fio = new T.Group(); g.add(fio); tagS(fio, 'inverno');
  const pts = []; for (let i = 0; i <= 14; i++) { const t = i / 14; pts.push(new T.Vector3(lerp(-6.8, 6.8, t), 4.85 - Math.sin(t * Math.PI * 3) ** 2 * 0.3, -4.92)); }
  const tube = new T.Mesh(new T.TubeGeometry(new T.CatmullRomCurve3(pts), 40, 0.025, 4), OUTLINE.clone()); tube.material.side = T.FrontSide; fio.add(tube);
  for (let i = 1; i < 14; i++) { const m = new T.MeshBasicMaterial({ color: [0xff4f6d, 0xffd23f, 0x3a86ff, 0x7dffb0][i % 4] }); const p = pts[i]; part(sph(0.09, 6, 5), m, p.x, p.y - 0.1, p.z + 0.04, 0.015, fio); CANT.luzes.push({ m, c: m.color.getHex(), ph: i * 0.7 }); }
  const band = new T.Group(); g.add(band); tagS(band, 'primavera', 'verao');
  const shape = geo('flagC', () => { const s = new T.Shape(); s.moveTo(-0.18, 0); s.lineTo(0.18, 0); s.lineTo(0, -0.4); s.closePath(); return new T.ExtrudeGeometry(s, { depth: 0.02, bevelEnabled: false }); });
  for (let i = 0; i < 12; i++) { const t = (i + 0.5) / 12, x = lerp(-6.6, 6.6, t); part(shape, M.flag[i % 3], x, 4.95 - Math.sin(t * Math.PI) * 0.3, -4.9, 0.02, band); }
}

// ---------- modelos: a florzinha plantada no canteiro e os enfeites que mudam com a estação ----------
function decorSazonal(m, item) {
  if (item === 'florPlantada' && m.userData.topo != null) { const s = part(sph(0.14, 10, 6), M.snow, 0, m.userData.topo + 0.08, 0, 0.015, m); s.scale.y = 0.45; tagS(s, 'inverno'); }
  if (item === 'guirlanda') {
    const au = new T.Group(); m.add(au); tagS(au, 'outono');
    for (let i = 0; i < 6; i++) { const a = (i / 6) * Math.PI * 2 + 0.3, l = part(sph(0.1, 7, 4), toon([0xf28a2e, 0xe0502a, 0xffb13b][i % 3]), Math.cos(a) * 0.42, Math.sin(a) * 0.42, 0.14, 0.015, au); l.scale.set(1, 0.5, 0.4); l.rotation.z = a; }
    const wi = new T.Group(); m.add(wi); tagS(wi, 'inverno');
    for (let i = 0; i < 7; i++) { const a = (i / 7) * Math.PI + 0.2; part(sph(0.07, 6, 5), M.snow, Math.cos(a) * 0.42, Math.sin(a) * 0.42 + 0.06, 0.12, 0.012, wi); }
    for (let i = 0; i < 4; i++) { const a = -0.6 - i * 0.55; part(sph(0.05, 6, 5), toon(0xe5383b), Math.cos(a) * 0.4, Math.sin(a) * 0.4, 0.16, 0.01, wi); }
  }
  if (item === 'enfeiteJanela') { const ic = new T.Group(); m.add(ic); tagS(ic, 'inverno'); for (let i = 0; i < 5; i++) { const c = part(cone(0.05, 0.2 + (i % 2) * 0.1, 5), toon(0xdff4ff), -0.36 + i * 0.18, 0.82, 0.04, 0.012, ic); c.rotation.x = Math.PI; } }
  if (item === 'bonecoNeve') { const ou = new T.Group(); m.add(ou); tagS(ou, 'verao'); part(box(0.12, 0.06, 0.03), M.ink, -0.07, 0.69, 0.19, 0.01, ou); part(box(0.12, 0.06, 0.03), M.ink, 0.07, 0.69, 0.19, 0.01, ou); }
  if (item === 'lembrancinha') { tagS(part(cone(0.12, 0.16, 8), M.snow, 0, 0.54, 0, 0.01, m), 'inverno'); }
  return m;
}

// ---------- o cantinho: estado, regras e painéis ----------
const Cantinho = {
  norm() {
    const c = S.cant && typeof S.cant === 'object' ? S.cant : {};
    const cores = Array.isArray(c.cores) ? c.cores.slice(0, 3).map((v) => clamp(Math.round(+v || 0), 0, 5)) : [0, 0, 0]; while (cores.length < 3) cores.push(0);
    const q = c.quadro && typeof c.quadro === 'object' ? c.quadro : {};
    S.cant = { cores, luz: !!c.luz, quadro: { img: String(q.img || 'pers'), txt: String(q.txt || 'abertura'), livre: String(q.livre || '').slice(0, 140) } };
  },
  liberado() { return S.tut >= 7 || !!S.selos.autor; },
  donoVid() { return CANT.dono ? CANT.dono.v : S.vid || 'eu'; },
  fachadas() {
    const { z, y0, d } = CASA_C, zf = z + d / 2;
    return { porta: { x: cwX(0), y: y0 + 1.6, z: cwZ(zf + 0.36) }, janela: { x: cwX(1.85), y: y0 + 1.55, z: cwZ(zf + 0.33) } };
  },
  posCanteiro(i) { return { x: cwX(CANTEIRO.x + CANTEIRO.slots[i]), z: cwZ(CANTEIRO.z) }; },
  meus(area) { return S.placed.filter((p) => (area ? p.area === area : CANT_AREAS.has(p.area))); },
  livres(area) { return this.meus(area).filter((p) => !p.fach && p.slot == null); },
  slotsLivres() { return CANTEIRO.slots.map((_, i) => i).filter((i) => !S.placed.some((p) => p.area === 'cantinho' && p.slot === i)); },
  tarefas() {
    const crafted = this.meus().some((p) => p.slot == null && ITEMS[p.item] && ITEMS[p.item].tipo === 'deco');
    const flor = this.meus('cantinho').some((p) => p.slot != null);
    return [['Colocar um enfeite criado por você', crafted], ['Plantar uma flor no canteiro', flor]];
  },
  checkMissao() { if (S.selos.cantinho) return; if (this.tarefas().every((t) => t[1])) { award('cantinho'); setTimeout(() => say([24], () => refreshQuest()), 700); } },
  aoMudar() { save(); refreshQuest(); this.checkMissao(); this.agendar(); },
  // ----- ir e vir -----
  ir(dono) {
    if (GAME.panel) closePanel();
    if (!this.liberado() && !dono) { say(['O seu cantinho abre quando você ganhar o selo de Autor(a) da Vila, na Casa da Pena!'], null, 'Placa do caminho'); return; }
    irisTo(() => {
      CANT.dono = dono || null; this.aplicarDono(); setArea('cantinho');
      P.pos.set(cwX(0), 0, cwZ(12.2)); P.vel.set(0, 0, 0); P.target = null; P.sitting = null; P.dir.set(0, 0, -1); snapCam(); Snd.gate();
      if (dono) toast(`🏡 Você está visitando o cantinho de ${dono.n}. Os enfeites são de ${dono.n}!`);
      else if (!S.flags.cantVisto) { S.flags.cantVisto = 1; save(); Voz.preload([21, 22, 23]); setTimeout(() => say([21, 22, 23], () => refreshQuest()), 500); }
      refreshQuest();
    });
  },
  voltarPraca() { irisTo(() => { CANT.dono = null; this.aplicarDono(); setArea('vila'); P.pos.set(PORTAL.voltaX, 0, PORTAL.voltaZ); P.vel.set(0, 0, 0); P.sitting = null; P.target = null; snapCam(); Snd.gate(); refreshQuest(); }); },
  entrarCasa() { irisTo(() => { setArea('cantinhoCasa'); P.pos.set(CANT_OX, 0, 3.4); P.vel.set(0, 0, 0); P.target = null; P.sitting = null; snapCam(); Snd.door(); if (CANT.bauLid) CANT.bauLid.rotation.x = 0; refreshQuest(); }); },
  sairCasa() { irisTo(() => { setArea('cantinho'); P.pos.set(cwX(0), 0, cwZ(CASA_C.front + 1.6)); P.vel.set(0, 0, 0); P.sitting = null; P.target = null; snapCam(); Snd.door(); refreshQuest(); }); },
  // ----- aparência conforme o dono (eu ou um colega visitado) -----
  aplicarDono() {
    const d = CANT.dono, cores = d ? d.dados.c : S.cant.cores, mt = CANT.mats;
    if (!mt.parede) return;
    const parede = corIdx(CORES_CANT.parede, cores[0]), telhado = corIdx(CORES_CANT.telhado, cores[1]), porta = corIdx(CORES_CANT.porta, cores[2]);
    mt.parede.color.setHex(parede); mt.telhado.color.setHex(telhado); mt.porta.color.setHex(porta);
    mt.colcha.color.setHex(misturaCor(telhado, 0xffffff, 0.35)); mt.cortina.color.setHex(misturaCor(telhado, 0xffffff, 0.5));
    desenhaPapelParede(parede);
    const nome = d ? d.n : S.nome || 'Autor(a)';
    planoTexto(CANT.placa, `Cantinho de ${nome}`, { bg: '#fff8ec', size: 64, weight: 900 });
    planoTexto(CANT.portao, d ? `CANTINHO DE ${String(nome).toUpperCase()}` : 'MEU CANTINHO', { bg: '#ffd9e8', size: 70, weight: 900 });
    planoTexto(CANT.caixaPlaca, String(nome).slice(0, 14), { bg: '#fffdf5', size: 70, weight: 900 });
    CANT.lampOn = d ? !!d.dados.l : !!S.cant.luz;
    if (CANT.miniLivro) CANT.miniLivro.visible = d ? false : !!(S.selos.livro || S.inv.miniLivro);
    if (CANT.fotoMat) { const c = d ? CANT.visitaFig || placeholderSticker(d.n) : PLAYER_CANVAS; if (c) { if (CANT.fotoMat.map) CANT.fotoMat.map.dispose(); CANT.fotoMat.map = canvasTex(c); CANT.fotoMat.needsUpdate = true; } }
    this.montarVisita();
    this.desenharQuadro();
  },
  // enfeites do colega visitado (só leitura)
  montarVisita() {
    CANT.visita.forEach((v) => { scene.remove(v.m); }); CANT.visita = [];
    const d = CANT.dono; if (!d) return;
    const F = this.fachadas();
    for (const e of d.dados.i) {
      const [a, item, x, z, r, f, s, t] = e, area = a ? 'cantinhoCasa' : 'cantinho';
      let px = a ? CANT_OX + x : cwX(x), pz = a ? z : cwZ(z), py = ITEMS[item].groundY || 0;
      if (!a && f === 1) { px = F.porta.x; py = F.porta.y; pz = F.porta.z; }
      if (!a && f === 2) { px = F.janela.x; py = F.janela.y; pz = F.janela.z; }
      const rec = { item, area, slot: !a && s >= 0 ? s : null, t: t * 60000, c: 0xffd23f };
      if (rec.slot != null) { const p = this.posCanteiro(rec.slot); px = p.x; pz = p.z; py = 0; }
      const m = placedModel(rec, plantStage(rec)); m.position.set(px, py, pz); m.rotation.y = f ? 0 : r; scene.add(m);
      CANT.visita.push({ m, area });
    }
  },
  exportar() {
    const ox = { cantinho: [CANT_X, CANT_Z], cantinhoCasa: [CANT_OX, 0] }, r2 = (v) => Math.round(v * 100) / 100;
    const i = this.meus().slice(0, 12).map((p) => [p.area === 'cantinho' ? 0 : 1, p.item, r2(p.x - ox[p.area][0]), r2(p.z - ox[p.area][1]), r2(p.r || 0), p.fach === 'porta' ? 1 : p.fach === 'janela' ? 2 : 0, p.slot == null ? -1 : p.slot, Math.round((p.t || Date.now()) / 60000)]);
    return { v: 1, c: S.cant.cores.slice(0, 3), l: S.cant.luz ? 1 : 0, i };
  },
  agendar() {
    if (!Srv.on || CANT.srvOff) return; clearTimeout(CANT.pushTimer);
    CANT.pushTimer = setTimeout(async () => {
      const cant = JSON.stringify(this.exportar()); if (cant === S.flags.cantEnviado) return;
      try { const r = await apiPost('vila-cantinho-salvar', { c: S.codigo, vid: S.vid, cant }); if (r && r.ok) { S.flags.cantEnviado = cant; save(); } }
      catch (e) { if (/HTTP 404/.test(String(e && e.message))) CANT.srvOff = true; }
    }, 1500);
  },
  // ----- regras para colocar enfeites -----
  regra(pl, x, z, y, ry) {
    pl.fach = null; pl.slot = null; pl.bad = false;
    if (GAME.area === 'cantinhoCasa') { const b = BOUNDS.cantinhoCasa; return { x: clamp(x, b.x0 + 0.3, b.x1 - 0.3), z: clamp(z, b.z0 + 0.2, b.z1 - 0.6), y, ry }; }
    const F = this.fachadas(), it = pl.item;
    if (it === 'guirlanda' && Math.hypot(F.porta.x - P.pos.x, F.porta.z + 1.2 - P.pos.z) < 2.8) { pl.fach = 'porta'; return { x: F.porta.x, y: F.porta.y, z: F.porta.z, ry: 0 }; }
    if (it === 'enfeiteJanela' && Math.hypot(F.janela.x - P.pos.x, F.janela.z + 1.2 - P.pos.z) < 2.6) { pl.fach = 'janela'; return { x: F.janela.x, y: F.janela.y, z: F.janela.z, ry: 0 }; }
    if (it === 'florPlantada' && Math.hypot(cwX(CANTEIRO.x) - P.pos.x, cwZ(CANTEIRO.z + 1.2) - P.pos.z) < 2.6) { const ls = this.slotsLivres(); if (ls.length) { pl.slot = ls[0]; const p = this.posCanteiro(ls[0]); return { x: p.x, y: 0, z: p.z, ry: 0 }; } }
    const lx = clamp(x - CANT_X, CERCA.x0 + 0.6, CERCA.x1 - 0.6), lz = clamp(z - CANT_Z, CERCA.z0 + 0.6, CERCA.z1 - 1.4);
    const dentro = (cx0, cx1, cz0, cz1) => lx > cx0 && lx < cx1 && lz > cz0 && lz < cz1;
    if (dentro(-3.7, 3.7, CASA_C.z - CASA_C.d / 2 - 0.5, CASA_C.front + 1.2) || dentro(-1.25, 1.25, -2.6, 8) || dentro(CANTEIRO.x - 2.1, CANTEIRO.x + 2.1, CANTEIRO.z - 1.0, CANTEIRO.z + 1.0)) pl.bad = true;
    for (const [px, pz] of [[QUADRO_P.x, QUADRO_P.z], [LATA_P.x, LATA_P.z]]) if (Math.hypot(lx - px, lz - pz) < 1.5) pl.bad = true;
    for (const p of this.livres('cantinho')) if (Math.hypot(p.x - cwX(lx), p.z - cwZ(lz)) < 1.0) pl.bad = true;
    return { x: cwX(lx), y, z: cwZ(lz), ry };
  },
  msgColocar(pl) {
    if (pl.fach === 'porta') return 'Pendurar na porta do seu cantinho';
    if (pl.fach === 'janela') return 'Pendurar na janela do seu cantinho';
    if (pl.slot != null) return 'Plantar no canteiro';
    if (pl.bad) return 'Aqui não dá: escolha um lugar livre na grama';
    const n = this.livres(GAME.area).length; return `Decoração ${Math.min(n + 1, LIMITE_DECO)} de ${LIMITE_DECO} ${GAME.area === 'cantinho' ? 'no jardim' : 'dentro de casa'}`;
  },
  pode(pl) {
    if (CANT.dono) { toast('Você está visitando: decore o seu próprio cantinho! 🏡'); Snd.nope(); return false; }
    if (pl.bad) { toast('Aqui não dá. Escolha um lugar livre na grama, longe do caminho e da casa.'); Snd.nope(); return false; }
    if (pl.fach) { const velho = S.placed.find((p) => p.area === 'cantinho' && p.fach === pl.fach); if (velho) { pickUpPlaced(velho); toast('Trocou! O enfeite antigo voltou para a mochila.'); } return true; }
    if (pl.slot != null) return true;
    if (this.livres(GAME.area).length >= LIMITE_DECO) { toast(`Já tem ${LIMITE_DECO} decorações ${GAME.area === 'cantinho' ? 'no jardim' : 'dentro de casa'}. Guarde uma (✋) para colocar outra.`); Snd.nope(); return false; }
    return true;
  },
  // ----- canteiro -----
  rotuloCanteiro() {
    if (CANT.dono) return `🌼 Canteiro de ${CANT.dono.n}`;
    const livre = this.slotsLivres().length;
    if (!livre) return '🌼 Canteiro cheio';
    return S.inv.florPlantada > 0 ? '🌱 Plantar uma flor' : '🌱 Canteiro';
  },
  plantar() {
    if (CANT.dono) { toast(`As flores de ${CANT.dono.n} estão lindas! 🌼`); return; }
    const ls = this.slotsLivres();
    if (!ls.length) { toast('O canteiro está cheio! Guarde uma flor (✋) para plantar outra.'); return; }
    if (!(S.inv.florPlantada > 0)) { say(['Para plantar aqui, crie uma Flor Plantada no Livro de Receitas: 1 Semente + 1 Água. A água fica na fonte da praça!'], null, 'Canteiro'); return; }
    takeItems({ florPlantada: 1 });
    const p = this.posCanteiro(ls[0]);
    const rec = { id: uid(), item: 'florPlantada', area: 'cantinho', x: p.x, y: 0, z: p.z, r: 0, door: null, fach: null, slot: ls[0], t: Date.now(), c: pick([0xffd23f, 0xff8fb8, 0xa77bff, 0xff5e5e, 0xffffff]) };
    S.placed.push(rec); spawnPlaced(rec); Snd.plant(); burst(p.x, 0.8, p.z, 0xc8ffb0);
    toast('🌱 Flor plantada! Volte daqui a pouquinho para ver ela crescer.'); this.aoMudar();
  },
  // ----- luminária -----
  luz() { CANT.lampOn = !CANT.lampOn; Snd.lamp(CANT.lampOn); if (!CANT.dono) { S.cant.luz = CANT.lampOn; this.aoMudar(); } },
  olharJanela() { const s = GAME.season; Snd.chirp(); toast({ primavera: '🌸 Lá fora as árvores estão cor-de-rosa e tem borboleta no jardim!', verao: '☀️ Que sol! Dá até para ver o mar lá longe.', outono: '🍂 As folhas estão caindo, laranjinhas, laranjinhas…', inverno: '❄️ Está nevando lá fora. Que bom estar quentinho aqui dentro!' }[s]); },
  // ----- quadro da história -----
  imagemQuadro() {
    const q = S.cant.quadro;
    if (q.img === 'capa') return coverCanvas('#ff6f91');
    if (q.img === 'pagina') return pageCanvas();
    if (q.img.startsWith('livro:')) { const s = +q.img.slice(6); if (CANT.livroImg[s]) return CANT.livroImg[s]; this.carregarLivro(s); }
    return PLAYER_CANVAS;
  },
  async carregarLivro(s) {
    if (CANT.livroImg[s] || CANT.livroImg[s] === null || !S.codigo) return Promise.resolve(); CANT.livroImg[s] = null;
    try { CANT.livroImg[s] = await loadImgCanvas(apiURL('vila-desenho', { c: S.codigo, s })); this.desenharQuadro(); } catch (e) { delete CANT.livroImg[s]; }
  },
  trecho() {
    const q = S.cant.quadro, hs = S.hist || {}, tit = S.titulo || S.tituloLivro || 'Minha história';
    if (q.txt === 'personagem' && hs.personagem) return { t: hs.personagem.nome, b: `Gosta ${hs.personagem.gosta} e tem medo ${hs.personagem.medo}.` };
    if (q.txt === 'cenario' && hs.cenario) return { t: 'Onde acontece', b: `${capFirst(hs.cenario.lugar)}, de cor ${hs.cenario.cor}, com som de ${hs.cenario.som} e cheiro ${hs.cenario.cheiro}.` };
    if (q.txt === 'problema' && hs.problema) return { t: 'O problema', b: `${capFirst(hs.problema.oque)}. Quem ajuda: ${hs.problema.ajuda}.` };
    if (q.txt === 'final' && hs.final) return { t: 'Como termina', b: hs.final.frase };
    if (q.txt === 'livre' && q.livre) return { t: tit, b: q.livre };
    return { t: tit, b: S.frase || 'Escreva a primeira frase da sua história no Caderno de Ideias, na Casa da Pena!' };
  },
  desenharQuadro() {
    const c = CANT.quadroCanvas; if (!c) return; const g = c.getContext('2d'), W = c.width, H = c.height, d = CANT.dono;
    g.fillStyle = '#fff8ec'; g.fillRect(0, 0, W, H);
    g.fillStyle = 'rgba(34,26,43,.06)'; for (let y = 10; y < H; y += 22) for (let x = 10; x < W; x += 22) { g.beginPath(); g.arc(x, y, 1.6, 0, 7); g.fill(); }
    g.strokeStyle = INK; g.lineWidth = 8; g.beginPath(); g.roundRect(6, 6, W - 12, H - 12, 22); g.stroke();
    // a foto
    g.fillStyle = '#d9efff'; g.beginPath(); g.roundRect(28, 28, 284, 380, 18); g.fill(); g.lineWidth = 5; g.stroke();
    const img = d ? CANT.visitaFig || placeholderSticker(d.n) : this.imagemQuadro();
    if (img) { const k = Math.min(256 / img.width, 352 / img.height); const w = img.width * k, hh = img.height * k; g.drawImage(img, 170 - w / 2, 218 - hh / 2, w, hh); }
    g.save(); g.globalAlpha = 0.75; g.fillStyle = '#ffc93c'; [[60, 20, -0.25], [280, 20, 0.25]].forEach(([x, y, r]) => { g.save(); g.translate(x, y); g.rotate(r); g.fillRect(-36, -12, 72, 24); g.restore(); }); g.restore();
    // o texto
    g.fillStyle = INK; g.textAlign = 'left'; g.textBaseline = 'top';
    const tx = 336, maxW = W - tx - 30;
    const tr = d ? { t: `Cantinho de ${d.n}`, b: 'Bem-vindo(a)! Fique à vontade, mas não mexa nos enfeites, tá?' } : this.trecho();
    let ts = 40, tl; for (; ts >= 22; ts -= 2) { g.font = `900 ${ts}px Grandstander, sans-serif`; tl = linhasTexto(g, tr.t, maxW); if (tl.length <= 3) break; }
    tl = tl.slice(0, 3); tl.forEach((l, i) => g.fillText(l, tx, 40 + i * (ts + 6)));
    let y = 40 + tl.length * (ts + 6) + 14; g.strokeStyle = '#ffc93c'; g.lineWidth = 6; g.beginPath(); g.moveTo(tx, y); g.lineTo(tx + 110, y); g.stroke(); y += 18;
    let bs = 28, bl; for (; bs >= 18; bs -= 2) { g.font = `700 ${bs}px Andika, sans-serif`; bl = linhasTexto(g, tr.b, maxW); if (y + bl.length * (bs + 6) < H - 70) break; }
    const maxL = Math.max(1, Math.floor((H - 70 - y) / (bs + 6))); if (bl.length > maxL) { bl = bl.slice(0, maxL); bl[maxL - 1] = bl[maxL - 1].replace(/\s*\S*$/, '') + '…'; }
    g.fillStyle = '#4a3d57'; bl.forEach((l, i) => g.fillText(l, tx, y + i * (bs + 6)));
    g.fillStyle = INK; g.textAlign = 'right'; g.font = '800 24px Grandstander, sans-serif'; g.fillText(d ? 'Rua dos Cantinhos' : 'por ' + (S.nome || 'Autor(a)'), W - 32, H - 52);
    if (CANT.quadroTex) CANT.quadroTex.needsUpdate = true;
  },
  abrirQuadro() {
    if (CANT.dono) { const d = CANT.dono; openPanel(`Quadro de ${d.n}`, (body) => { body.append(h('img', { src: CANT.quadroCanvas.toDataURL(), alt: '', class: 'quadroPrev' }), h('p', { style: 'font-size:14px;color:var(--muted);margin-top:8px' }, 'A figurinha aparece depois que a professora aprova.')); }, { eyebrow: 'Visita' }); return; }
    const q = Object.assign({}, S.cant.quadro);
    openPanel('Quadro da história', (body) => {
      const prev = h('img', { alt: 'Prévia do quadro', class: 'quadroPrev' });
      const upd = () => { const old = S.cant.quadro; S.cant.quadro = q; this.desenharQuadro(); prev.src = CANT.quadroCanvas.toDataURL(); S.cant.quadro = old; this.desenharQuadro(); };
      body.append(h('p', {}, 'Escolha o desenho e o pedacinho da história que vão aparecer no quadro da entrada e na parede da sua casa.'), prev);
      body.append(h('div', { class: 'sec' }, '🖼 O desenho'));
      const imgs = h('div', { class: 'figs' }), opImg = [['pers', 'Meu personagem'], ['capa', 'Capa do livro'], ['pagina', 'Página ilustrada']];
      (Array.isArray(S.livroDesenhos) ? S.livroDesenhos : []).slice(0, 8).forEach((dd) => opImg.push(['livro:' + dd.s, String(dd.r || 'Desenho').slice(0, 14) + ' (livro)']));
      const bImg = opImg.map(([k, nm]) => { const b = h('button', { type: 'button', class: 'btn sm ' + (q.img === k ? 'leaf' : 'plain'), onclick: () => { q.img = k; bImg.forEach((x) => x.classList.replace('leaf', 'plain')); b.classList.replace('plain', 'leaf'); if (k.startsWith('livro:')) Promise.resolve(this.carregarLivro(+k.slice(6))).then(upd); upd(); Snd.pop(); } }, nm); return b; });
      bImg.forEach((b) => imgs.append(b)); body.append(imgs);
      body.append(h('div', { class: 'sec' }, '✏️ O trecho'));
      const hs = S.hist || {}, opTx = [['abertura', 'Título e primeira frase', true], ['personagem', 'Personagem', !!hs.personagem], ['cenario', 'Cenário', !!hs.cenario], ['problema', 'Problema', !!hs.problema], ['final', 'Final', !!hs.final], ['livre', 'Escrever outro trecho', true]];
      const livre = h('textarea', { rows: 2, maxlength: 140, placeholder: 'Ex.: E o dragão descobriu que bolhas de sabão também iluminam a noite.' }); livre.value = q.livre || '';
      const lf = h('label', { class: 'field' }, h('span', {}, 'Seu trecho (até 140 letras)'), livre); lf.hidden = q.txt !== 'livre';
      livre.addEventListener('input', () => { q.livre = livre.value.replace(/\s+/g, ' ').slice(0, 140); upd(); });
      const tx = h('div', { class: 'figs' }), bTx = [];
      opTx.forEach(([k, nm, ok]) => { const b = h('button', { type: 'button', class: 'btn sm ' + (q.txt === k ? 'leaf' : 'plain'), disabled: !ok, title: ok ? '' : 'Faça a missão dessa casa para liberar', onclick: () => { q.txt = k; bTx.forEach((x) => x.classList.replace('leaf', 'plain')); b.classList.replace('plain', 'leaf'); lf.hidden = k !== 'livre'; if (k === 'livre') setTimeout(() => livre.focus(), 30); upd(); Snd.pop(); } }, nm); bTx.push(b); tx.append(b); });
      body.append(tx, lf);
      body.append(h('div', { class: 'row', style: 'margin-top:12px' }, h('button', { class: 'btn leaf', onclick: () => { q.livre = String(q.livre || '').trim().slice(0, 140); if (q.txt === 'livre' && !q.livre) q.txt = 'abertura'; S.cant.quadro = q; this.desenharQuadro(); save(); Snd.pop(); burst(cwX(QUADRO_P.x), 2.5, cwZ(QUADRO_P.z)); closePanel(); toast('🖼 Quadro atualizado!'); } }, '💾 Pendurar no quadro'), h('span', { style: 'font-size:13px;color:var(--muted)' }, 'Só você vê o trecho. Quem visita vê seu nome e a figurinha aprovada.')));
      upd();
    }, { eyebrow: 'Meu Cantinho' });
  },
  // ----- pintar a casa -----
  abrirPintar() {
    if (CANT.dono) return;
    openPanel('Pintar a casa', (body) => {
      body.append(h('p', {}, 'Escolha as cores do seu cantinho. Dá para trocar quando quiser!'));
      [['parede', 'Parede', 0], ['telhado', 'Telhado', 1], ['porta', 'Porta e caixa de correio', 2]].forEach(([k, nm, i]) => {
        body.append(h('div', { class: 'sec' }, nm)); const row = h('div', { class: 'figs' }), bs = [];
        CORES_CANT[k].forEach(([cn, cor], j) => { const b = h('button', { type: 'button', class: 'btn sm ' + (S.cant.cores[i] === j ? 'leaf' : 'plain'), onclick: () => { S.cant.cores[i] = j; bs.forEach((x) => x.classList.replace('leaf', 'plain')); b.classList.replace('plain', 'leaf'); this.aplicarDono(); Snd.brush(); this.aoMudar(); } }, h('i', { class: 'cor', style: `background:${hexCss(cor)}` }), cn); bs.push(b); row.append(b); });
        body.append(row);
      });
    }, { eyebrow: 'Meu Cantinho', onClose: () => burst(cwX(0), 4, cwZ(CASA_C.front)) });
  },
  // ----- baú, estante, escrivaninha -----
  abrirBau() {
    if (CANT.dono) return;
    const lid = CANT.bauLid; if (lid) { let k = 0; Snd.chestOpen(); anim((dt) => { k += dt / 0.4; lid.rotation.x = -Math.min(1, k) * 1.6; return k >= 1; }); }
    setTimeout(() => openPanel('Baú do cantinho', (body) => {
      body.append(h('div', { class: 'sec' }, 'Meus selos'));
      const m = h('div', { class: 'medals' }); const got = Object.entries(SELOS).filter(([k]) => S.selos[k]);
      got.forEach(([, s]) => m.append(h('div', { class: 'medal got' }, h('div', { class: 'm' }, s.ic), h('div', {}, h('b', {}, s.nome), s.desc))));
      if (!got.length) m.append(h('p', {}, 'Ainda nenhum selo. Eles aparecem aqui!'));
      body.append(m);
      const decos = Object.keys(S.inv).filter((k) => S.inv[k] > 0 && ITEMS[k] && ITEMS[k].tipo === 'deco');
      body.append(h('div', { class: 'sec' }, 'Criações para decorar'));
      if (!decos.length) body.append(h('p', {}, 'Nenhuma criação na mochila. Faça uma no Livro de Receitas (🔨)!'));
      else { const grid = h('div', { class: 'inv' }); decos.forEach((k) => grid.append(h('button', { class: 'slot', onclick: () => startPlace(k) }, h('span', { class: 'n' }, '×' + S.inv[k]), h('img', { src: iconURL(k), alt: '' }), ITEMS[k].nome, h('small', { style: 'color:var(--muted)' }, '📍 colocar')))); body.append(grid); }
      const no = this.meus();
      body.append(h('div', { class: 'sec' }, `No meu cantinho (${no.length})`));
      const ul = h('div', { class: 'list' });
      no.forEach((p) => ul.append(h('div', { class: 'it' }, h('img', { src: iconURL(p.item), alt: '' }), h('span', { style: 'flex:1' }, `${ITEMS[p.item].nome} · ${p.slot != null ? 'no canteiro' : p.fach === 'porta' ? 'na porta' : p.fach === 'janela' ? 'na janela' : p.area === 'cantinho' ? 'no jardim' : 'dentro de casa'}`), h('button', { class: 'btn plain sm', onclick: () => { pickUpPlaced(p); closePanel(); this.abrirBau(); } }, '✋ Guardar'))));
      if (!no.length) ul.append(h('div', { class: 'it' }, `Até ${LIMITE_DECO} decorações no jardim, ${LIMITE_DECO} dentro de casa, uma guirlanda na porta, um enfeite na janela e 3 flores no canteiro.`));
      body.append(ul);
    }, { eyebrow: 'Meu Cantinho', icon: iconURL('selo') }), 380);
  },
  estante() {
    Snd.page();
    if (CANT.dono) { say(['Dica de escrita: ' + pick(DICAS)], null, `Estante de ${CANT.dono.n}`); return; }
    const n = S.inv.miniLivro || 0, mh = minhaHistoria();
    openPanel('Minha estante', (body) => {
      body.append(h('div', { class: 'list' }, h('div', { class: 'it' }, h('img', { src: iconURL('miniLivro'), alt: '' }), S.selos.livro ? `Seu mini-livro está aqui na estante! ${n > 1 ? `(${n} na mochila)` : ''}` : 'Encaderne um Mini-livro na Gráfica e ele aparece aqui na estante.'), h('div', { class: 'it' }, h('img', { src: iconURL('pagina'), alt: '' }), `Páginas ilustradas na mochila: ${S.inv.pagina || 0}`), h('div', { class: 'it' }, h('img', { src: iconURL('ideia'), alt: '' }), `Ideias guardadas: ${S.ideas.length}`)));
      if (mh.length) { body.append(h('div', { class: 'sec' }, 'Minha história')); const hl = h('div', { class: 'list' }); mh.forEach(([k, v]) => hl.append(h('div', { class: 'it' }, h('b', { style: 'min-width:110px' }, k), h('span', {}, v)))); body.append(hl); }
      body.append(h('p', { style: 'margin-top:12px' }, '📖 Dica de escrita: ' + pick(DICAS)));
    }, { eyebrow: 'Meu Cantinho' });
  },
  escrivaninha() {
    sitAt(rw('cantinhoCasa', 5.2), -2.95, 0.55, -1);
    if (CANT.dono) return;
    setTimeout(() => openPanel('Escrivaninha', (body) => {
      const mh = minhaHistoria();
      body.append(h('p', {}, 'Aqui é o seu cantinho de escrever. O que você escrever aparece na Capa, na Página Ilustrada e no quadro da história.'));
      if (mh.length) { const hl = h('div', { class: 'list' }); mh.forEach(([k, v]) => hl.append(h('div', { class: 'it' }, h('b', { style: 'min-width:110px' }, k), h('span', {}, v)))); body.append(hl); }
      body.append(h('div', { class: 'row', style: 'margin-top:12px' },
        h('button', { class: 'btn leaf', onclick: () => { closePanel(); openPanel('Título e primeira frase', abaEscrita, { eyebrow: 'Escrivaninha', onClose: () => this.desenharQuadro() }); } }, '✏️ Título e primeira frase'),
        h('button', { class: 'btn sky', onclick: () => { closePanel(); this.abrirQuadro(); } }, '🖼 Mudar o quadro')));
    }, { eyebrow: 'Meu Cantinho' }), 250);
  },
  // ----- visitas -----
  abrirVisitas() {
    Snd.mailbox();
    if (!Srv.on) { say(['Entrando com o código do livro, você visita o cantinho dos colegas da sua turma!'], null, 'Caixa de correio'); return; }
    openPanel('Visitar colegas', (body) => {
      const st = h('p', {}, 'Procurando os cantinhos da sua turma…'); body.append(st);
      apiPost('vila-cantinho', { c: S.codigo, vid: S.vid }, { timeout: 9000 }).then((r) => {
        if (!GAME.panel || !st.isConnected) return;
        if (!r || !r.ok || !Array.isArray(r.lista)) { st.textContent = 'Não consegui abrir a lista agora. Tente de novo daqui a pouco.'; return; }
        const lista = r.lista.filter((p) => p && p.v && p.v !== S.vid).sort((a, b) => (b.casa ? 2 : b.on ? 1 : 0) - (a.casa ? 2 : a.on ? 1 : 0) || String(a.n).localeCompare(String(b.n)));
        st.textContent = lista.length ? 'Escolha um colega. Os enfeites de cada cantinho são de quem mora lá: dá para olhar, sentar e conversar!' : 'Ninguém da turma arrumou o cantinho ainda. Volte mais tarde!';
        const ul = h('div', { class: 'list' });
        lista.forEach((p) => ul.append(h('div', { class: 'it' }, h('b', { style: 'flex:1' }, String(p.n || 'Colega').slice(0, 16)), p.casa ? h('span', { class: 'chip ok' }, '🏡 em casa agora') : p.on ? h('span', { class: 'chip st' }, '👋 na vila') : null, h('button', { class: 'btn grape sm', disabled: !p.tem, onclick: () => this.visitar(p) }, p.tem ? 'Visitar' : 'arrumando…'))));
        body.append(ul);
      }).catch((e) => { if (st.isConnected) st.textContent = /HTTP 404/.test(String(e && e.message)) ? 'As visitas ainda vão ser ligadas no servidor da escola. Logo, logo!' : 'Sem conexão agora. Tente de novo daqui a pouco.'; });
    }, { eyebrow: 'Rua dos Cantinhos' });
  },
  async visitar(p) {
    try {
      const r = await apiPost('vila-cantinho', { c: S.codigo, vid: S.vid, de: p.v }, { timeout: 9000 });
      if (!r || !r.ok) throw new Error('recusado');
      const dados = normCantDados(parseJSON(r.cant || '{}', {}));
      const dono = { v: p.v, n: String(r.n || p.n || 'Colega').slice(0, 16), a: +r.a || 0, dados };
      CANT.visitaFig = null;
      if (dono.a) { try { CANT.visitaFig = await loadImgCanvas(apiURL('vila-fig', { v: dono.v, fv: dono.a })); } catch (e) { CANT.visitaFig = null; } }
      this.ir(dono);
    } catch (e) { toast('Não deu para visitar agora. Tente de novo daqui a pouco.'); Snd.nope(); }
  },
  // ----- animação -----
  update(dt, t) {
    const pb = CANT.portalBub; if (pb) { pb.root.visible = GAME.started && GAME.area === 'vila' && this.liberado() && !S.flags.cantVisto; if (pb.root.visible) pb.root.position.y = 5.4 + Math.sin(t * 3) * 0.22; }
    for (const v of CANT.visita) v.m.visible = v.area === GAME.area;
    if (!CANT.mats.vidro) return;
    CANT.mats.vidro.color.setHex(CANT.lampOn ? 0xffd27a : ROOM_WIN.color.getHex());
    if (GAME.area === 'cantinho') {
      for (const tr of CANT.trees) tr.rotation.z = Math.sin(t * 0.8 + tr.userData.ph) * 0.018;
      for (const f of CANT.flags) f.rotation.x = Math.sin(t * 2.2 + f.userData.sw) * 0.25;
      const fumaca = GAME.season === 'outono' || GAME.season === 'inverno' || CANT.lampOn;
      for (const p of CANT.smoke) { p.visible = fumaca; if (!fumaca) continue; const u = (t * 0.25 + p.userData.ph) % 1; p.position.y = CASA_C.y0 + CASA_C.h + 2.7 + u * 2.3; p.position.x = -1.7 + Math.sin(u * 5 + p.userData.ph * 6) * 0.25 + u * 0.5; p.scale.setScalar(0.45 + u * 0.8); }
      for (const b of CANT.butterflies) { if (!b.parent.visible) break; const u = b.userData; b.position.set(u.cx + Math.sin(t * 0.5 + u.ph) * 2.2, 1.2 + Math.sin(t * 1.7 + u.ph) * 0.35, u.cz + Math.cos(t * 0.37 + u.ph) * 1.6); u.w1.rotation.z = Math.sin(t * 18 + u.ph) * 0.9; u.w2.rotation.z = -u.w1.rotation.z; b.rotation.y = t * 0.5 + u.ph; }
    }
    if (GAME.area === 'cantinhoCasa') {
      const lt = CANT.lampLight; lt.intensity = lerp(lt.intensity, CANT.lampOn ? 14 + Math.sin(t * 2.3) * 0.6 : 0, 1 - Math.exp(-dt * 8));
      const want = CANT.lampOn ? CANT.shadeOn : CANT.shadeOff; if (CANT.shade.material !== want) CANT.shade.material = want;
      for (const l of CANT.luzes) { const on = Math.sin(t * 2.4 + l.ph) > -0.3; l.m.color.setHex(on ? l.c : misturaCor(l.c, 0x221a2b, 0.55)); }
    }
  },
};
function normCantDados(c) {
  const ITENS = new Set(Object.keys(ITEMS).filter((k) => ITEMS[k].tipo === 'deco'));
  const n = (v, a, b, d) => { v = Number(v); return Number.isFinite(v) ? clamp(v, a, b) : d; };
  const cores = (Array.isArray(c.c) ? c.c : []).slice(0, 3).map((v) => Math.round(n(v, 0, 5, 0))); while (cores.length < 3) cores.push(0);
  const i = (Array.isArray(c.i) ? c.i : []).slice(0, 12).filter((x) => Array.isArray(x) && ITENS.has(x[1])).map((x) => [x[0] ? 1 : 0, x[1], n(x[2], -12, 12, 0), n(x[3], -12, 12, 0), n(x[4], -7, 7, 0), Math.round(n(x[5], 0, 2, 0)), Math.round(n(x[6], -1, 2, -1)), Math.round(n(x[7], 0, 1e8, 0))]);
  return { c: cores, l: c.l ? 1 : 0, i };
}
