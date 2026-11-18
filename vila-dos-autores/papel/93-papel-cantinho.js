// ============================================================
// EDIÇÃO PAPEL · Meu Cantinho (17/11/2026, noite)
// A casinha da criança ganha o mesmo acabamento das casas da Fase 1:
//  - por dentro: papel de parede mais vivo, barrado recortado, tapete com babado, móveis com detalhe,
//    mural e prateleira na parede, e os móveis se levantam ao entrar (pop-up);
//  - por fora: reboco e telhas pintados. A COR continua a que a criança escolheu (parede, telhado, porta):
//    as imagens são quase brancas e só dão a pincelada; quem pinta é o material.
// Nada aqui muda regra do jogo. Nenhuma peça nova tem colisão: o que é novo fica na parede ou em cima dos móveis.
// Entra depois de 92-papel-arte.js e antes de 99-inicio.js (ver build-papel.sh).
// ============================================================
// tom mais forte da cor que a criança escolheu: mesma matiz, com saturação e luz fixas (conta em sRGB)
function tomCor(n, sat, luz) {
  const r = ((n >> 16) & 255) / 255, g = ((n >> 8) & 255) / 255, b = (n & 255) / 255, mx = Math.max(r, g, b), mn = Math.min(r, g, b), d = mx - mn;
  let h = 0; if (d > 1e-6) { h = mx === r ? ((g - b) / d) % 6 : mx === g ? (b - r) / d + 2 : (r - g) / d + 4; h /= 6; if (h < 0) h += 1; }
  const q = luz < 0.5 ? luz * (1 + sat) : luz + sat - luz * sat, p = 2 * luz - q;
  const f = (t) => { t = ((t % 1) + 1) % 1; return t < 1 / 6 ? p + (q - p) * 6 * t : t < 1 / 2 ? q : t < 2 / 3 ? p + (q - p) * (2 / 3 - t) * 6 : p; };
  return (Math.round(f(h + 1 / 3) * 255) << 16) | (Math.round(f(h) * 255) << 8) | Math.round(f(h - 1 / 3) * 255);
}
function formaEstrela(R, r, n = 5) { return () => { const s = new T.Shape(); for (let i = 0; i < n * 2; i++) { const a = (i / (n * 2)) * Math.PI * 2 + Math.PI / 2, q = i % 2 ? r : R; if (i) s.lineTo(Math.cos(a) * q, Math.sin(a) * q); else s.moveTo(Math.cos(a) * q, Math.sin(a) * q); } s.closePath(); return s; }; }
// imagem de pincelada (quase branca) com repetição própria: a cor vem do material
function pincelada(nome, rx, ry) { const t = new T.TextureLoader().load(PAPEL_ARTE[nome].src); t.colorSpace = T.SRGBColorSpace; t.anisotropy = 4; t.wrapS = t.wrapT = T.RepeatWrapping; t.repeat.set(rx, ry); return t; }
function matPincelada(nome, rx, ry, cor) { const m = new T.MeshToonMaterial({ color: 0xffffff, map: pincelada(nome, rx, ry), gradientMap: GRAD }); m.alphaTest = 0.01; if (cor) m.color = cor; return m; } // alphaTest: ver 92-papel-arte.js

// ---------- papel de parede: a mesma estampa de coração e bolinha, com listras e cor mais viva ----------
desenhaPapelParede = function (cor) {
  const c = CANT.wpCanvas, g = c.getContext('2d');
  const base = misturaCor(cor, 0xffffff, 0.12), pat = tomCor(cor, 0.6, 0.74), lista = misturaCor(base, pat, 0.2);
  g.fillStyle = hexCss(base); g.fillRect(0, 0, 256, 256);
  g.fillStyle = hexCss(lista); for (let x = 0; x < 256; x += 64) g.fillRect(x + 18, 0, 28, 256);
  g.fillStyle = hexCss(pat);
  for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
    const px = 32 + x * 64, py = 32 + y * 64 + (x % 2) * 32;
    if ((x + y) % 2) { g.beginPath(); g.moveTo(px, py + 11); g.bezierCurveTo(px - 17, py - 2, px - 8, py - 16, px, py - 6); g.bezierCurveTo(px + 8, py - 16, px + 17, py - 2, px, py + 11); g.fill(); }
    else { g.beginPath(); g.arc(px, py, 6.5, 0, 7); g.fill(); }
  }
  g.fillStyle = 'rgba(255,255,255,.75)'; for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { g.beginPath(); g.arc(x * 64, y * 64 + (x % 2) * 32, 3, 0, 7); g.fill(); }
  if (CANT.wp) CANT.wp.forEach((t) => (t.needsUpdate = true));
  if (CANT.mats.barrado) CANT.mats.barrado.color.setHex(tomCor(cor, 0.62, 0.7));
};

// ---------- por dentro ----------
function cantSalaDetalhes(room) {
  const g = room.g, mt = CANT.mats;
  // cama
  const bed = achaG(room, -5.2, -0.9);
  if (bed) {
    [-1, 1].forEach((s) => part(sph(0.17, 10, 8), M.woodDark, -1.72, 1.84, s * 0.95, 0.03, bed)); // bolinhas da cabeceira
    pc(cyl(0.11, 0.11, 2.1, 10), M.woodDark, -1.72, 1.72, 0, 0.03, bed, Math.PI / 2); // travessa roliça
    part(box(0.2, 0.62, 2.06), M.wood, 1.72, 0.55, 0, 0.045, bed); [-1, 1].forEach((s) => part(sph(0.13, 10, 8), M.woodDark, 1.72, 0.94, s * 0.95, 0.025, bed)); // peseira
    part(box(0.34, 0.2, 1.97), toon(0xfffdf5), -0.62, 0.97, 0, 0.03, bed); // dobra do lençol
    const bab = chapa('camabab', formaBarrado(3.3, 0.2, 10, 0.07), mt.colcha, bed, 0, 0.05, 0.03); bab.rotation.z = Math.PI; bab.position.set(0, 0.72, 1.03); // babado da colcha
    [[0.15, -0.5, 0xffd23f], [0.95, 0.4, 0x8fd3ff], [1.3, -0.45, 0xffffff]].forEach(([x, z, c], i) => pc(box(0.44, 0.03, 0.44), toon(c), x, 1.07, z, 0.012, bed, 0, 0.3 + i * 0.5)); // retalhos
    const u = new T.Group(); u.position.set(-1.18, 1.2, 0.42); u.rotation.y = 0.35; bed.add(u); // ursinho no travesseiro
    const mu = toon(0xc98a4b); part(sph(0.2, 10, 8), mu, 0, 0.18, 0, 0.03, u); part(sph(0.16, 10, 8), mu, 0, 0.47, 0, 0.03, u);
    [-1, 1].forEach((s) => { part(sph(0.065, 8, 6), mu, s * 0.12, 0.61, 0, 0.015, u); part(sph(0.07, 8, 6), mu, s * 0.2, 0.22, 0.08, 0.015, u); part(sph(0.022, 6, 5), M.ink, s * 0.06, 0.5, 0.145, 0, u); });
    part(sph(0.065, 8, 6), toon(0xfff3d6), 0, 0.44, 0.13, 0.012, u);
  }
  // baú
  const ch = achaG(room, 0.3, -4.3);
  if (ch) {
    part(box(1.74, 0.12, 1.12), M.woodDark, 0, 0.06, 0, 0.03, ch); // rodapé
    [[-0.68, 0.24], [0.68, 0.24], [-0.68, 0.7], [0.68, 0.7]].forEach(([x, y]) => part(sph(0.05, 8, 6), M.gold, x, y, 0.52, 0.012, ch)); // tachinhas
    [-1, 1].forEach((s) => part(box(0.07, 0.2, 0.38), M.ink, s * 0.84, 0.5, 0, 0.015, ch)); // alças
    if (CANT.bauLid) { part(box(1.66, 0.06, 1.06), M.woodDark, 0, 0.34, 0.5, 0.02, CANT.bauLid); [-0.5, 0.5].forEach((x) => part(box(0.13, 0.34, 1.04), M.gold, x, 0.16, 0.5, 0, CANT.bauLid)); }
  }
  // escrivaninha: luminária de mesa
  const dk = achaG(room, 5.2, -4.2);
  if (dk) {
    const lm = new T.Group(); lm.position.set(-0.92, 1.12, -0.28); dk.add(lm);
    part(cyl(0.16, 0.18, 0.06, 12), M.ink, 0, 0.03, 0, 0.02, lm); pc(cyl(0.025, 0.025, 0.56, 6), M.ink, 0.08, 0.3, 0, 0.012, lm, 0, 0, -0.3);
    pc(cone(0.2, 0.26, 12), toon(0x38c6c0), 0.22, 0.6, 0, 0.025, lm, 0, 0, -0.55); part(sph(0.07, 8, 6), M.lamp, 0.25, 0.53, 0, 0, lm);
    part(sph(0.06, 8, 6), M.gold, -0.55, 0.78, 0.53, 0.015, dk); // segundo puxador
  }
  // cadeira: almofadas da cor da colcha
  const cd = achaG(room, 5.2, -2.95);
  if (cd) { part(box(0.7, 0.08, 0.64), mt.colcha, 0, 0.72, -0.02, 0.025, cd); part(box(0.62, 0.5, 0.07), mt.colcha, 0, 1.08, 0.27, 0.025, cd); }
  // estantinha
  const es = achaG(room, 6.5, 1.3);
  if (es) {
    part(box(2.34, 0.1, 0.84), M.woodDark, 0, 2.56, 0.02, 0.03, es); // cimalha
    const sv = chapa('estbar', formaBarrado(2.3, 0.12, 9, 0.07), M.woodDark, es, 0, 0.05, 0, 1.9 / 2.3); sv.rotation.z = Math.PI; sv.position.set(0, 2.41, 0.35); // sanefa recortada
    pc(box(0.7, 0.14, 0.5), toon(0x3a86ff), -0.5, 2.68, 0.02, 0.025, es, 0, 0.2); pc(box(0.6, 0.12, 0.44), toon(0xffd23f), -0.52, 2.81, 0.02, 0.025, es, 0, -0.15);
    vasinho(es, 0.62, 2.61, 0.05, 0.9);
  }
  // janela: varão, bandô recortado da cor da cortina, presilhas e vasinho
  const w = achaG(room, 2.5, -4.95);
  if (w) {
    pc(cyl(0.05, 0.05, 3.9, 8), M.woodDark, 0, 1.42, 0.3, 0.02, w, 0, 0, Math.PI / 2); [-1, 1].forEach((s) => part(sph(0.1, 8, 6), M.gold, s * 1.98, 1.42, 0.3, 0.02, w));
    const bd = chapa('janbarC', formaBarrado(3.5, 0.34, 10, 0.11), mt.cortina, w, 0, 0.06, 0.04); bd.rotation.z = Math.PI; bd.position.set(0, 1.44, 0.36);
    [-1, 1].forEach((s) => part(sph(0.09, 8, 6), M.gold, s * 1.62, -0.35, 0.34, 0.02, w));
    vasinho(w, 0.92, -1.12, 0.2, 0.85, 0xffd23f);
  }
  // luminária de pé
  const lp = CANT.lampG;
  if (lp) { part(sph(0.09, 8, 6), M.gold, 0, 1.3, 0, 0.02, lp); part(cyl(0.63, 0.63, 0.07, 16), toon(0xfff3d6), 0, 2.46, 0, 0.02, lp); part(cyl(0.012, 0.012, 0.34, 5), M.gold, 0.24, 2.22, 0.12, 0, lp); part(sph(0.05, 6, 5), M.gold, 0.24, 2.03, 0.12, 0.012, lp); }
  // quadro: cordinha até o prego
  const qf = CANT.quadroIn;
  if (qf) [-1, 1].forEach((s) => pc(cyl(0.014, 0.014, 1.02, 5), M.ink, s * 0.5, 1.1625, 0.03, 0, qf, 0, 0, s * 1.398));
  // mural de recados em cima da escrivaninha
  const mu = new T.Group(); mu.position.set(5.55, 3.2, -4.95); g.add(mu);
  part(box(1.8, 1.3, 0.1), M.woodDark, 0, 0, 0, 0.04, mu); part(box(1.62, 1.12, 0.12), toon(0xd9a066), 0, 0, 0.01, 0, mu);
  [[-0.48, 0.24, 0xfff3a8, 0.1], [0.12, 0.27, 0xffc9dc, -0.08], [0.5, -0.12, 0xbfe0ff, 0.12], [-0.38, -0.26, 0xcdf0c0, -0.1]].forEach(([x, y, c, r], i) => {
    pc(box(0.36, 0.36, 0.02), toon(c), x, y, 0.08, 0.01, mu, 0, 0, r); part(sph(0.035, 6, 5), toon([0xe5383b, 0x3a86ff, 0xffc928, 0x4fae4c][i]), x, y + 0.13, 0.1, 0, mu);
  });
  const st = chapa('estrelinhaC', formaEstrela(0.2, 0.09), M.gold, mu, 0, 0.03, 0.02); st.position.set(0.1, -0.3, 0.09); st.rotation.z = 0.2;
  // prateleira de brinquedos na parede do fundo, em cima do baú
  const pr = new T.Group(); pr.position.set(-0.04, 2.75, -4.95); g.add(pr);
  part(box(1.32, 0.1, 0.45), M.wood, 0, 0, 0.22, 0.03, pr); [-0.5, 0.5].forEach((x) => part(box(0.08, 0.3, 0.3), M.woodDark, x, -0.18, 0.16, 0.015, pr));
  [[-0.52, 0xe5533d, 0.5], [-0.37, 0x3a86ff, 0.42], [-0.22, 0xffd23f, 0.55]].forEach(([x, c, hh]) => part(box(0.14, hh, 0.32), toon(c), x, 0.05 + hh / 2, 0.2, 0.02, pr)); // livros em pé
  part(cyl(0.1, 0.13, 0.08, 10), M.woodDark, 0.44, 0.09, 0.22, 0.015, pr); part(cyl(0.02, 0.02, 0.1, 6), M.ink, 0.44, 0.18, 0.22, 0, pr); part(sph(0.19, 12, 9), toon(0x3a86ff), 0.44, 0.4, 0.22, 0.025, pr); // globo
  [[0.1, 0.06], [-0.08, -0.05]].forEach(([a, b]) => part(sph(0.07, 6, 5), toon(0x4fae4c), 0.44 + a, 0.42 + b, 0.38, 0, pr));
  const bq = chapa('barquinhoC', () => { const s = new T.Shape(); s.moveTo(-0.22, 0.11); s.lineTo(0.22, 0.11); s.lineTo(0.13, 0); s.lineTo(-0.13, 0); s.closePath(); return s; }, M.paper, pr, 0, 0.16, 0.02); bq.position.set(0.05, 0.05, 0.22);
  const vl = chapa('velaC', () => { const s = new T.Shape(); s.moveTo(0, 0); s.lineTo(0.15, 0); s.lineTo(0, 0.28); s.closePath(); return s; }, toon(0xff6f91), pr, 0, 0.03, 0.015); vl.position.set(0.05, 0.17, 0.22);
}
function cantSalaEstrutura(room) {
  const g = room.g;
  const mb = (CANT.mats.barrado = toon(tomCor(0xfff1d6, 0.62, 0.7), { unique: true }));
  const b = chapa('bar14', formaBarrado(14, 1.1, 28, 0.085), mb, g, 0, 0.05, 0); b.position.set(0, 0.34, -4.975); b.castShadow = false;
  [-1, 1].forEach((s) => { const l = chapa('bar10', formaBarrado(10, 1.1, 20, 0.085), mb, g, 0, 0.05, 0); l.rotation.y = s * (Math.PI / 2); l.position.set(-s * 6.975, 0.34, 0); l.castShadow = false; });
  const rug = g.children.find((o) => o.material === M.rug);
  if (rug) {
    const k = 2.4 / 2.6, x = rug.position.x, z = rug.position.z;
    const u = chapa('tapbab', formaCopa(0, 0, 2.84, 2.84, 24, 0.09), PAPEL.borda, g, 0, 0.03, 0); u.rotation.x = -Math.PI / 2; u.scale.set(k, 0.61 * k, 1); u.position.set(x, 0.02, z); u.castShadow = false;
    [[1.95, 2.08], [1.0, 1.07]].forEach(([a, c]) => { const r = new T.Mesh(geo('tapr' + a, () => new T.RingGeometry(a, c, 48)), PAPEL.borda); r.rotation.x = -Math.PI / 2; r.scale.set(k, 0.6 * k, 1); r.position.set(x, 0.064, z); r.receiveShadow = true; g.add(r); });
  }
}
const _buildCantinhoRoom0 = buildCantinhoRoom;
buildCantinhoRoom = function () {
  _buildCantinhoRoom0();
  const room = CANT.room; if (!room) return;
  const n0 = Math.max(0, room.g.children.findIndex((o) => o.isGroup)); // tudo antes do primeiro grupo é chão, parede e rodapé
  try { cantSalaDetalhes(room); } catch (e) { console.warn('papel: detalhes do cantinho', e); }
  try { coletaDobras(room.g, room.id, n0); } catch (e) { console.warn('papel: dobras do cantinho', e); } // os móveis se levantam ao entrar
  try { cantSalaEstrutura(room); desenhaPapelParede(0xfff1d6); } catch (e) { console.warn('papel: estrutura do cantinho', e); }
};

// ---------- por fora: reboco e telhas pintados, na cor que a criança escolheu ----------
const _cantCasaExterna0 = cantCasaExterna;
cantCasaExterna = function (g) {
  _cantCasaExterna0(g);
  try {
    const { w, d, h, y0 } = CASA_C, mt = CANT.mats, casa = CANT.casa;
    const parede = casa.children.find((o) => o.isMesh && o.material === mt.parede);
    if (parede) parede.material = matPincelada('pedra', 2, 1.1, mt.parede.color); // a MESMA cor do material original (objeto compartilhado): muda junto quando a criança pinta
    const base = casa.children[0]; if (base && base.isMesh) { base.material = matPincelada('pedra', 3, 0.4); base.material.color.setHex(0xb9aebb); }
    // telhas: duas águas e os dois oitões, um fio acima do telhado original (que continua dando o volume e a sombra)
    const Wb = w / 2 + 0.55, Hr = 2.3, D = (d + 0.8) / 2, yb = y0 + h, sl = Math.hypot(Wb, Hr), e = 0.03, lado = 2.3, mtl = matPincelada('telhaNeutra', 1, 1, mt.telhado.color);
    const folha = (pts, uv) => {
      const bg = new T.BufferGeometry(); bg.setAttribute('position', new T.Float32BufferAttribute(pts.flat(), 3)); bg.setAttribute('uv', new T.Float32BufferAttribute(uv.flat(), 2));
      bg.setIndex(pts.length === 4 ? [0, 1, 2, 0, 2, 3] : [0, 1, 2]); bg.computeVertexNormals();
      const m = new T.Mesh(bg, mtl); m.receiveShadow = true; casa.add(m);
    };
    [1, -1].forEach((s) => {
      const ox = (s * Hr * e) / sl, oy = (Wb * e) / sl, z1 = s * D, z2 = -s * D, u = (2 * D) / lado, v = sl / lado;
      folha([[s * Wb + ox, yb + oy, z1], [s * Wb + ox, yb + oy, z2], [ox, yb + Hr + oy, z2], [ox, yb + Hr + oy, z1]], [[0, 0], [u, 0], [u, v], [0, v]]);
      folha([[-s * Wb, yb, s * (D + e)], [s * Wb, yb, s * (D + e)], [0, yb + Hr, s * (D + e)]], [[0, 0], [(2 * Wb) / lado, 0], [Wb / lado, Hr / lado]]);
    });
    CANT.mats.telhaPintada = mtl;
  } catch (err) { console.warn('papel: casa do cantinho', err); }
};
