// ============================================================
// EDIÇÃO PAPEL · piloto de arte ilustrada (17/11/2026)
// Troca a pintura de cor lisa por arte pintada à mão (guache em papel) em 4 peças:
// Casa da Pena, árvore redonda, pinheiro e poste. Só o desenho muda: colisão,
// portas, missões e estações continuam as do jogo.
// As imagens ficam em arte-dados.js (PAPEL_ARTE), embutidas, para a cópia seguir num arquivo só.
// Entra depois de 91-papel-salas.js e antes de 99-inicio.js (ver build-papel.sh).
// ============================================================
const ARTE = { tex: {}, mats: {} };
function arteTex(nome, repete) {
  if (ARTE.tex[nome]) return ARTE.tex[nome];
  const t = new T.TextureLoader().load(PAPEL_ARTE[nome].src);
  t.colorSpace = T.SRGBColorSpace; t.anisotropy = 4;
  if (repete) t.wrapS = t.wrapT = T.RepeatWrapping;
  return (ARTE.tex[nome] = t);
}
// cartão pintado: recebe a luz e a sombra do jogo, recorte pelo alfa da imagem
function arteMat(nome, { recorte = true, repete = false, brilho = 0 } = {}) {
  if (ARTE.mats[nome]) return ARTE.mats[nome];
  const tx = arteTex(nome, repete);
  const m = new T.MeshToonMaterial({ color: 0xffffff, map: tx, gradientMap: GRAD, side: recorte ? T.DoubleSide : T.FrontSide });
  m.alphaTest = recorte ? 0.5 : 0.01; // 0.01 nas peças inteiras: sem isso o motor WebGPU pinta de preto a imagem que não tem transparência
  if (brilho) { m.emissive = new T.Color(brilho, brilho, brilho); m.emissiveMap = tx; }
  // motor WebGPU: a sombra precisa ser avisada do recorte (no WebGL2 isso já é automático)
  if (recorte && ENGINE !== 'WebGL2' && T.Fn && T.texture) { try { m.shadowNode = T.Fn(() => { T.texture(tx, T.uv()).a.lessThan(0.5).discard(); return T.vec4(0, 0, 0, 1); })(); } catch (e) {} }
  return (ARTE.mats[nome] = m);
}
function cartaoArte(nome, altura, parent, { brilho = 0, espelha = false } = {}) {
  const a = PAPEL_ARTE[nome], w = (altura * a.w) / a.h;
  const g = geo('arte-' + nome, () => { const p = new T.PlaneGeometry(1, 1); p.translate(0.5 - (a.cx || 0.5), 0.5, 0); return p; }); // o pé do desenho fica em (0,0)
  const m = new T.Mesh(g, arteMat(nome, { brilho })); m.scale.set(espelha ? -w : w, altura, 1); m.castShadow = true; m.receiveShadow = true; parent.add(m); return m;
}
// Um cartão só, de frente para a câmera (que no jogo não gira) e um pouco deitado para trás, como figura de livro pop-up.
function figuraArte(g, nome, altura, opt) {
  const c = new T.Group(); c.rotation.order = 'YXZ'; c.rotation.set(-0.13, -g.rotation.y + Math.sin(g.position.x * 2.1 + g.position.z * 1.3) * 0.1, 0); g.add(c);
  cartaoArte(nome, altura, c, opt); return c;
}

// ---------- árvores ----------
// A arte foi pintada para a primavera (árvore em flor). Nas outras estações volta o cartão liso, que troca de cor sozinho.
const ARTE_ESTACOES = ['primavera', 'verao', 'outono', 'inverno'];
const _arvorePapel0 = arvorePapel;
arvorePapel = function (g, kind) {
  const pinho = kind === 'pine', com = pinho ? ['primavera', 'verao', 'outono'] : ['primavera'];
  const liso = new T.Group(); g.add(liso); _arvorePapel0(liso, kind); seasonTag(liso, ...ARTE_ESTACOES.filter((s) => !com.includes(s)));
  const espelha = Math.sin(g.position.x * 3.1 + g.position.z * 1.7) > 0;
  seasonTag(figuraArte(g, pinho ? 'pinho' : 'arvore', pinho ? 5.0 : 4.8, { espelha }), ...com);
};

// ---------- poste: cartão pintado no lugar das peças lisas ----------
const _buildLamp0 = buildLamp;
buildLamp = function (V, x, z) {
  const n0 = V.children.length, topo = _buildLamp0(V, x, z), g = V.children[n0];
  g.children.slice().forEach((o) => { if (!SEASONAL.some((e) => e.obj === o)) g.remove(o); }); // fica só a neve do inverno
  figuraArte(g, 'poste', 4.35, { brilho: 0.1 });
  return topo;
};

// ---------- Casa da Pena: mesma casa, com fachada, reboco e telhas pintados ----------
function casaArte(g) {
  const zF = HD / 2, y0 = 0.5 + HH, roofG = geo('roof'), wallG = box(HW, HH, HD), stepG = box(2.2, 0.16, 1.1);
  let parede = null;
  g.children.slice().forEach((o) => {
    if (o.geometry === wallG) { parede = o; return; }
    if (o.geometry === roofG || o.geometry === stepG) return;
    if (o.isGroup && Math.abs(o.position.y - HH) < 0.01) return; // a placa com o nome fica
    const p = o.isGroup && o.children[0] && o.position.lengthSq() === 0 ? o.children[0].position : o.position;
    if (p.z >= zF - 0.01) g.remove(o); // porta, janelas, floreiras, cantoneiras e olho-de-boi agora estão pintados
  });
  const plano = (nome, w, h, x, y, z, opt) => { const m = new T.Mesh(new T.PlaneGeometry(w, h), arteMat(nome, opt)); m.position.set(x, y, z); m.receiveShadow = true; g.add(m); return m; };
  if (parede) parede.material = arteMat('parede', { recorte: false });
  plano('fachada', HW + 0.3, HH + 0.1, 0, 0.5 + HH / 2, zF + 0.03);
  plano('base', HW + 0.8, 0.52, 0, 0.26, (HD + 0.7) / 2 + 0.02, { recorte: false });
  // telhas: duas águas e os dois oitões, um fio acima do telhado original (que continua dando o volume e a sombra)
  const Wb = HW / 2 + 0.65, Hr = 2.9, D = (HD + 0.9) / 2, sl = Math.hypot(Wb, Hr), e = 0.03, lado = 2.5, mt = arteMat('telha', { recorte: false, repete: true });
  const folha = (pts, uv) => {
    const bg = new T.BufferGeometry(); bg.setAttribute('position', new T.Float32BufferAttribute(pts.flat(), 3)); bg.setAttribute('uv', new T.Float32BufferAttribute(uv.flat(), 2));
    bg.setIndex(pts.length === 4 ? [0, 1, 2, 0, 2, 3] : [0, 1, 2]); bg.computeVertexNormals();
    const m = new T.Mesh(bg, mt); m.receiveShadow = true; g.add(m);
  };
  [1, -1].forEach((s) => {
    const ox = (s * Hr * e) / sl, oy = (Wb * e) / sl, z1 = s * D, z2 = -s * D, u = (2 * D) / lado, v = sl / lado;
    folha([[s * Wb + ox, y0 + oy, z1], [s * Wb + ox, y0 + oy, z2], [ox, y0 + Hr + oy, z2], [ox, y0 + Hr + oy, z1]], [[0, 0], [u, 0], [u, v], [0, v]]);
    folha([[-s * Wb, y0, s * (D + e)], [s * Wb, y0, s * (D + e)], [0, y0 + Hr, s * (D + e)]], [[0, 0], [(2 * Wb) / lado, 0], [Wb / lado, Hr / lado]]);
  });
  plano('olho', 1.3, 1.3, 0, y0 + 1.08, D + 0.07);
}
const _buildHouse0 = buildHouse;
buildHouse = function (d, V) {
  _buildHouse0(d, V);
  if (d.id === 'pena') casaArte(HOUSES.pena.group);
};
