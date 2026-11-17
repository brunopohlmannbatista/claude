// ============================================================
// EDIÇÃO PAPEL · dentro das casas: cores mais vivas, barrado de papel nas paredes,
// tapete com babado, móveis com acabamento e peças novas de cartão.
// Nada aqui muda regra do jogo: só acrescenta enfeite (e colisão do que é novo no chão).
// Entra depois de 90-papel.js e antes de 99-inicio.js.
// ============================================================
Object.assign(ROOM_DEFS.pena, { wall: '#ffd98a', pat: '#f5b33a', floor: '#d68f4a' });
Object.assign(ROOM_DEFS.biblioteca, { wall: '#b9dbff', pat: '#86b9f2', floor: '#b97843' });
Object.assign(ROOM_DEFS.atelie, { wall: '#ffcce0', pat: '#ff9cc3', floor: '#e2a561' });
Object.assign(ROOM_DEFS.grafica, { wall: '#b9ead3', pat: '#7fcaa6', floor: '#a96d3e' });
Object.assign(ROOM_DEFS.correio, { wall: '#ffd2a3', pat: '#f6a25e', floor: '#cf8344' });

function corMult(hex, f) { const c = new T.Color(hex); c.multiplyScalar(f); return c.getHex(); }
// peça com rotação (atalho)
function pc(g, m, x, y, z, ol, parent, rx = 0, ry = 0, rz = 0) { const o = part(g, m, x, y, z, ol, parent); o.rotation.set(rx, ry, rz); return o; }
// faixa de papel com a beirada de cima recortada em ondas
function formaBarrado(w, h, n, r) {
  return () => { const s = new T.Shape(); s.moveTo(-w / 2, 0); s.lineTo(w / 2, 0); s.lineTo(w / 2, h); const p = w / n;
    for (let i = 0; i < n; i++) s.quadraticCurveTo(w / 2 - (i + 0.5) * p, h + r * 2, w / 2 - (i + 1) * p, h);
    s.closePath(); return s; };
}
function formaFolha(h, w) { return () => { const s = new T.Shape(); s.moveTo(0, 0); s.quadraticCurveTo(w, h * 0.35, 0, h); s.quadraticCurveTo(-w, h * 0.35, 0, 0); return s; }; }
const achaG = (room, x, z) => room.g.children.find((o) => o.isGroup && Math.abs(o.position.x - x) < 0.06 && Math.abs(o.position.z - z) < 0.06);

// ---------- pecinhas que se repetem ----------
function vasinho(parent, x, y, z, s = 1, flor = 0xff6f91) {
  const v = new T.Group(); v.position.set(x, y, z); v.scale.setScalar(s); parent.add(v);
  part(cyl(0.17, 0.12, 0.24, 10), toon(0xd9703f), 0, 0.12, 0, 0.025, v); part(cyl(0.19, 0.19, 0.06, 10), toon(0xe98a55), 0, 0.25, 0, 0.02, v);
  [0, 1].forEach((i) => { const c = new T.Group(); c.rotation.y = i * (Math.PI / 2); v.add(c); chapa('vzf', formaCopa(0, 0.52, 0.27, 0.25, 6, 0.3, 0.3), toon(0x5fb04f), c, 0, 0.05, 0.035); });
  part(sph(0.09, 8, 6), toon(flor), 0.05, 0.8, 0.04, 0.02, v);
  return v;
}
function plantaPapel(room, x, z, s = 1) {
  const p = new T.Group(); p.position.set(x, 0, z); p.scale.setScalar(s); room.g.add(p);
  part(cyl(0.4, 0.3, 0.55, 12), toon(0xd9703f), 0, 0.275, 0, 0.04, p); part(cyl(0.44, 0.44, 0.1, 12), toon(0xe98a55), 0, 0.57, 0, 0.03, p);
  for (let i = 0; i < 6; i++) { const f = new T.Group(); f.position.y = 0.6; f.rotation.y = i * 1.047; p.add(f); const l = chapa('fl' + (i % 2), formaFolha(i % 2 ? 1.55 : 1.15, i % 2 ? 0.42 : 0.36), toon(i % 2 ? 0x4fa650 : 0x6fbf5a), f, 0, 0.05, 0.04); l.rotation.x = 0.3 + (i % 3) * 0.16; }
  addCircle(room.id, rw(room.id, x), z, 0.45 * s);
  return p;
}

// ---------- móveis que aparecem em várias salas ----------
const _armchair0 = armchair;
armchair = function (parent, x, z, rot, color) {
  const c = _armchair0(parent, x, z, rot, color), m = toon(color);
  [-1, 1].forEach((s) => pc(cyl(0.2, 0.2, 1.34, 12), m, s * 0.76, 1.14, 0, 0.045, c, Math.PI / 2)); // braços roliços
  pc(cyl(0.2, 0.2, 1.5, 12), m, 0, 1.77, -0.5, 0.045, c, 0, 0, Math.PI / 2); // encosto roliço
  [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([a, b]) => part(cyl(0.07, 0.1, 0.22, 8), M.woodDark, a * 0.6, 0.1, b * 0.48, 0.02, c)); // pezinhos
  pc(box(0.62, 0.52, 0.16), toon(0xfff3d6), 0, 1.2, -0.24, 0.03, c, -0.22); // almofada
  part(box(1.5, 0.07, 0.07), toon(corMult(color, 0.78)), 0, 0.68, 0.66, 0.015, c); // vivo do assento
  return c;
};
const _craftBench0 = craftBench;
craftBench = function (room, x, z, station) {
  _craftBench0(room, x, z, station); const b = room.g.children[room.g.children.length - 1];
  part(box(2.0, 0.08, 0.9), M.wood, 0, 0.34, 0, 0.03, b); // prateleira de baixo
  part(box(0.95, 0.24, 0.06), M.woodDark, 0.5, 0.82, 0.57, 0.025, b); part(sph(0.06, 8, 6), M.gold, 0.5, 0.82, 0.63, 0.015, b); // gaveta
  pc(cyl(0.13, 0.13, 0.95, 10), M.paper, -0.4, 0.51, -0.1, 0.02, b, 0, 0, Math.PI / 2); pc(cyl(0.11, 0.11, 0.8, 10), toon(0xffd23f), -0.35, 0.49, 0.2, 0.02, b, 0, 0.2, Math.PI / 2); // rolos de papel
  part(box(0.6, 0.3, 0.42), toon(0xe5533d), 0.55, 0.53, 0, 0.03, b); part(box(0.3, 0.05, 0.08), M.ink, 0.55, 0.72, 0, 0.015, b); // caixa de ferramentas
};
const _bookcase0 = bookcase;
bookcase = function (room, x, z, w = 2.6, hh = 3.6, interact = true) {
  const sh = _bookcase0(room, x, z, w, hh, interact);
  part(box(w + 0.34, 0.1, 1.0), M.woodDark, 0, hh + 0.13, 0, 0.03, sh); // cimalha
  const v = chapa('estbar', formaBarrado(2.3, 0.12, 9, 0.07), M.woodDark, sh, 0, 0.05, 0, (w - 0.3) / 2.3); v.rotation.z = Math.PI; v.position.set(0, hh - 0.08, 0.43); // sanefa recortada
  vasinho(sh, -w / 2 + 0.45, hh + 0.18, 0.05, 0.9);
  pc(box(0.7, 0.14, 0.5), toon(0x3a86ff), w / 2 - 0.6, hh + 0.25, 0, 0.025, sh, 0, 0.2); pc(box(0.6, 0.12, 0.44), toon(0xffd23f), w / 2 - 0.62, hh + 0.38, 0, 0.025, sh, 0, -0.15);
  return sh;
};
const _roomWindow0 = roomWindow;
roomWindow = function (g, x) {
  _roomWindow0(g, x); const w = g.children[g.children.length - 1];
  pc(cyl(0.05, 0.05, 3.1, 8), M.woodDark, 0, 1.12, 0.3, 0.02, w, 0, 0, Math.PI / 2); [-1, 1].forEach((s) => part(sph(0.1, 8, 6), M.gold, s * 1.58, 1.12, 0.3, 0.02, w)); // varão
  const v = chapa('janbar', formaBarrado(2.9, 0.3, 8, 0.11), toon(0xff6f9f), w, 0, 0.06, 0.04); v.rotation.z = Math.PI; v.position.set(0, 1.1, 0.34); // bandô recortado
  vasinho(w, -0.8, -0.92, 0.2, 0.85, 0xffd23f);
};

// ---------- estrutura de toda sala: barrado nas paredes e tapete com babado ----------
function salaEstrutura(room) {
  const g = room.g, mb = toon(corMult(new T.Color(room.d.pat).getHex(), 0.94));
  const b = chapa('bar14', formaBarrado(14, 1.1, 28, 0.085), mb, g, 0, 0.05, 0); b.position.set(0, 0.34, -4.975); b.castShadow = false;
  [-1, 1].forEach((s) => { const l = chapa('bar10', formaBarrado(10, 1.1, 20, 0.085), mb, g, 0, 0.05, 0); l.rotation.y = s * (Math.PI / 2); l.position.set(-s * 6.975, 0.34, 0); l.castShadow = false; });
  const rug = g.children.find((o) => o.material === M.rug);
  if (rug) {
    const u = chapa('tapbab', formaCopa(0, 0, 2.84, 2.84, 24, 0.09), PAPEL.borda, g, 0, 0.03, 0); u.rotation.x = -Math.PI / 2; u.scale.y = 0.63; u.position.set(0, 0.02, 1.2); u.castShadow = false;
    [[1.95, 2.08], [1.0, 1.07]].forEach(([a, c]) => { const r = new T.Mesh(geo('tapr' + a, () => new T.RingGeometry(a, c, 48)), PAPEL.borda); r.rotation.x = -Math.PI / 2; r.scale.y = 0.62; r.position.set(0, 0.064, 1.2); r.receiveShadow = true; g.add(r); });
  }
}

// ---------- acabamento de cada casa ----------
function detPena(room) {
  const fp = achaG(room, -3.8, -4.45), chest = achaG(room, 4.6, 2.3), tb = achaG(room, 2.6, -0.9);
  if (fp) {
    const q = new T.Group(); q.position.set(-0.55, 4.15, -0.42); fp.add(q); // quadro em cima da lareira
    part(box(1.5, 1.15, 0.08), M.woodDark, 0, 0, 0, 0.035, q); part(box(1.26, 0.92, 0.04), toon(0x9fd8ff), 0, 0, 0.04, 0, q);
    const m1 = chapa('qm1', formaTronco(0.45, 0.03, 0.62), toon(0x4fa650), q, 0, 0.02, 0); m1.position.set(-0.15, -0.46, 0.07);
    const m2 = chapa('qm2', formaTronco(0.33, 0.03, 0.42), toon(0x6fbf5a), q, 0, 0.02, 0); m2.position.set(0.3, -0.46, 0.085);
    pc(cyl(0.13, 0.13, 0.02, 14), toon(0xffd23f), 0.38, 0.22, 0.07, 0, q, Math.PI / 2);
    [-1.45, -1.15].forEach((cx, i) => { part(cyl(0.09, 0.11, 0.06, 8), M.gold, cx, 3.29, 0.3, 0.015, fp); part(cyl(0.045, 0.045, 0.34 - i * 0.08, 8), toon(0xfff3d6), cx, 3.48 - i * 0.04, 0.3, 0.012, fp); part(cone(0.04, 0.1, 6), M.fire2, cx, 3.71 - i * 0.08, 0.3, 0, fp); }); // castiçais
    [[1.5, 0.13, 0.82], [1.76, 0.13, 0.82], [1.63, 0.36, 0.82]].forEach(([lx, ly, lz]) => pc(cyl(0.13, 0.13, 0.62, 8), M.trunk, lx, ly, lz, 0.025, fp, Math.PI / 2)); // lenha
  }
  if (chest) {
    [[-1, 0.14], [1, 0.14], [-1, 0.76], [1, 0.76]].forEach(([s, y]) => part(sph(0.07, 8, 6), M.gold, s * 0.76, y, 0.56, 0.012, chest)); // tachinhas
    [-1, 1].forEach((s) => pc(tor(0.14, 0.035, 6, 14), M.ink, s * 0.88, 0.5, 0, 0.01, chest, 0, Math.PI / 2)); // alças
    [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([a, b]) => part(box(0.22, 0.1, 0.22), M.woodDark, a * 0.82, 0.05, b * 0.5, 0.02, chest)); // pés
  }
  if (tb) {
    part(cyl(0.1, 0.13, 0.17, 10), M.ink, -0.95, 1.22, -0.4, 0.02, tb); pc(cyl(0.014, 0.014, 0.5, 5), M.white, -0.88, 1.5, -0.4, 0, tb, 0, 0, -0.3); // tinteiro e pena
    part(cyl(0.16, 0.18, 0.05, 10), M.ink, -0.9, 1.155, 0.35, 0.015, tb); part(cyl(0.025, 0.025, 0.55, 6), M.ink, -0.9, 1.42, 0.35, 0.01, tb); part(cone(0.22, 0.26, 10), toon(0xffd23f), -0.9, 1.78, 0.35, 0.03, tb); // luminária
    [-1, 1].forEach((s) => part(box(2.1, 0.07, 0.07), M.woodDark, 0, 0.3, s * 0.6, 0.02, tb)); // travessas
  }
  plantaPapel(room, 5.95, -2.1, 0.95);
}
function detBiblio(room) {
  const id = room.id, lamp = achaG(room, -5.4, -0.4);
  if (lamp) { part(cyl(0.32, 0.38, 0.08, 12), M.ink, 0, 0.04, 0, 0.02, lamp); pc(tor(0.45, 0.035, 6, 20), toon(0xff8a3c), 0, 2.27, 0, 0.01, lamp, Math.PI / 2); part(sph(0.13, 8, 6), M.lamp, 0, 2.2, 0, 0, lamp); }
  const esc = new T.Group(); esc.position.set(-2.0, 0, -3.35); room.g.add(esc); const ld = new T.Group(); ld.rotation.x = -0.2; esc.add(ld); // escada encostada na estante
  [-0.32, 0.32].forEach((lx) => part(box(0.09, 3.7, 0.09), M.wood, lx, 1.85, 0, 0.025, ld));
  for (let i = 0; i < 7; i++) part(box(0.64, 0.07, 0.09), M.woodDark, 0, 0.4 + i * 0.5, 0, 0.02, ld);
  addBox(id, rw(id, -2.0), -3.55, 0.4, 0.3);
  const mt = new T.Group(); mt.position.set(-5.6, 0, 2.4); room.g.add(mt); // mesinha ao lado da poltrona
  part(cyl(0.34, 0.4, 0.07, 12), M.woodDark, 0, 0.035, 0, 0.02, mt); part(cyl(0.06, 0.06, 0.8, 8), M.wood, 0, 0.45, 0, 0.02, mt); part(cyl(0.55, 0.55, 0.08, 16), M.wood, 0, 0.88, 0, 0.035, mt);
  pc(box(0.5, 0.09, 0.36), toon(0xe5533d), -0.12, 0.965, -0.08, 0.02, mt, 0, 0.3); pc(box(0.44, 0.08, 0.32), toon(0x4fae4c), -0.1, 1.05, -0.08, 0.02, mt, 0, -0.2);
  part(cyl(0.09, 0.08, 0.16, 10), M.white, 0.25, 1.0, 0.15, 0.02, mt); part(tor(0.05, 0.018, 5, 10), M.white, 0.35, 1.0, 0.15, 0, mt);
  addCircle(id, rw(id, -5.6), 2.4, 0.6);
  plantaPapel(room, 5.9, 3.9, 0.95);
}
function detAtelie(room) {
  const id = room.id, sh = achaG(room, -5.9, -3.6);
  if (sh) {
    [0.3, 0.84].forEach((y) => { part(box(1.22, 0.44, 0.04), toon(0xfff3d6), 0, y, 0.46, 0.02, sh); part(sph(0.06, 8, 6), M.gold, 0, y, 0.5, 0.012, sh); }); // gavetas
    part(cyl(0.11, 0.09, 0.22, 10), toon(0x6ec6ff), 0.52, 1.31, 0.3, 0.02, sh); // pote de pincéis
    [0xff4f6d, 0x4fae4c, 0xa77bff].forEach((c, i) => { pc(cyl(0.018, 0.018, 0.42, 5), M.wood, 0.48 + i * 0.04, 1.55, 0.3, 0, sh, 0, 0, (i - 1) * 0.22); part(sph(0.04, 6, 5), toon(c), 0.48 + i * 0.04 - (i - 1) * 0.045, 1.76, 0.3, 0, sh); });
  }
  // respingos de tinta no chão, em volta do cavalete
  [[-0.3, -1.4, 0xff4f6d, 0.48], [-2.9, -1.3, 0x3a86ff, 0.4], [-0.9, -0.85, 0xffd23f, 0.3], [-3.4, -2.6, 0x4fae4c, 0.34], [0.4, -2.6, 0xa77bff, 0.28]].forEach(([x, z, c, r], i) => {
    const m = chapa('resp' + i, formaCopa(0, 0, 1, 0.8, 7, 0.45, i), toon(c), room.g, 0, 0.02, 0); m.rotation.x = -Math.PI / 2; m.rotation.z = i * 1.3; m.scale.set(r, r, 1); m.position.set(x, 0.022 + i * 0.002, z); m.castShadow = false; });
  const bn = new T.Group(); bn.position.set(5.85, 0, -3.85); room.g.add(bn); // cesto com rolos de papel
  part(cyl(0.42, 0.34, 0.8, 12), toon(0x8a5cc2), 0, 0.4, 0, 0.04, bn);
  [[-0.12, 0.05, 0.1, 0xfff6e4], [0.14, -0.08, -0.14, 0x8fd3ff], [0.02, 0.14, 0.2, 0xffd23f]].forEach(([x, z, rz, c], i) => pc(cyl(0.1, 0.1, 1.3 + i * 0.15, 10), toon(c), x, 0.95 + i * 0.05, z, 0.02, bn, 0, 0, rz));
  addCircle(id, rw(id, 5.85), -3.85, 0.5);
}
function detGrafica(room) {
  const id = room.id, pr = achaG(room, -2.8, -3.4), bx = achaG(room, 4.8, -3.7), lec = achaG(room, 1.5, -0.6);
  if (pr) {
    part(box(3.5, 0.2, 1.9), toon(corMult(0x3aa6a0, 0.72)), 0, 0.1, 0, 0.05, pr); // base
    const vol = new T.Group(); vol.position.set(-1.72, 1.15, 0.1); vol.rotation.y = Math.PI / 2; pr.add(vol); // volante
    part(tor(0.52, 0.07, 8, 26), M.ink, 0, 0, 0, 0.02, vol); pc(cyl(0.12, 0.12, 0.16, 10), M.gold, 0, 0, 0, 0.02, vol, Math.PI / 2);
    [0, 1, 2].forEach((i) => pc(box(1.0, 0.07, 0.05), M.ink, 0, 0, 0, 0, vol, 0, 0, (i * Math.PI) / 3));
    part(box(0.6, 0.72, 0.06), toon(0xfff3d6), -1.25, 0.62, 0.82, 0.03, pr); // painel de botões
    [0xe5383b, 0xffd23f, 0x4fae4c].forEach((c, i) => pc(cyl(0.07, 0.07, 0.06, 10), toon(c), -1.25, 0.4 + i * 0.17, 0.87, 0.012, pr, Math.PI / 2));
    pc(cyl(0.11, 0.11, 0.04, 14), M.white, -1.25, 0.86, 0.86, 0.015, pr, Math.PI / 2);
    [0, 1, 2].forEach((i) => part(box(0.5, 0.06, 0.03), toon(corMult(0x3aa6a0, 0.6)), 1.25, 0.42 + i * 0.17, 0.81, 0, pr)); // respiros
    signBoard('PRENSA', 1.3, 0.3, pr, 0, 2.15, 0.52, { bg: '#ffc93c', size: 44, weight: 900 });
    part(box(1.3, 0.16, 0.8), M.paper, 0.2, 2.48, -0.1, 0.025, pr); pc(box(1.3, 0.02, 0.8), M.paper, 0.25, 2.58, -0.08, 0.015, pr, 0, 0.12); // papel de entrada
    part(box(0.8, 0.1, 0.45), M.paper, 0.45, 1.0, 1.34, 0.02, pr); // pilha pronta na bandeja
    part(cyl(0.2, 0.28, 0.36, 10), M.ink, -1.0, 2.58, -0.1, 0.02, pr); part(cyl(0.26, 0.26, 0.06, 10), toon(0xe5383b), -1.0, 2.79, -0.1, 0.02, pr); // funil de tinta
  }
  if (bx) [[0, 0.55, 0, 1.4, 1.1], [0.15, 1.55, 0.05, 1.1, 0.9], [-1.1, 0.4, 0.4, 0.8, 0.8]].forEach(([x, y, z, w, hh], i) => {
    const c = new T.Group(); c.position.set(x, y, z); c.rotation.y = i * 0.2; bx.add(c); const d = w * 0.8, fita = toon(0xf6e2b8);
    part(box(w * 0.16, 0.02, d + 0.02), fita, 0, hh / 2 + 0.011, 0, 0, c); part(box(w * 0.16, hh * 0.3, 0.02), fita, 0, hh / 2 - hh * 0.15, d / 2 + 0.011, 0, c); // fita
    part(box(w * 0.36, hh * 0.3, 0.02), M.paper, -w * 0.26, -hh * 0.12, d / 2 + 0.012, 0.012, c); // etiqueta
    [0, 1].forEach((k) => part(box(w * 0.26, 0.025, 0.02), M.ink, -w * 0.26, -hh * 0.07 - k * hh * 0.09, d / 2 + 0.024, 0, c));
    if (i === 1) [-1, 1].forEach((s) => pc(box(w * 0.5, 0.03, d), toon(0xc9955a), s * w * 0.68, hh / 2 + 0.12, 0, 0.02, c, 0, 0, s * 0.55)); // abas abertas
  });
  if (lec) part(cyl(0.42, 0.5, 0.1, 12), M.woodDark, 0, 0.05, 0, 0.03, lec);
  const pl = new T.Group(); pl.position.set(-5.85, 0, -0.5); room.g.add(pl); // palete com resmas de papel colorido
  part(box(1.3, 0.12, 1.1), M.wood, 0, 0.16, 0, 0.03, pl); [-0.5, 0, 0.5].forEach((px) => part(box(0.14, 0.1, 1.1), M.woodDark, px, 0.05, 0, 0.02, pl));
  [[-0.3, 0.27, 0xfff6e4, 0.5], [0.33, 0.27, 0x8fd3ff, 0.34], [0.33, -0.27, 0xffd23f, 0.22], [-0.3, -0.27, 0xff8fb8, 0.4]].forEach(([px, pz, c, ph]) => part(box(0.56, ph, 0.48), toon(c), px, 0.22 + ph / 2, pz, 0.025, pl));
  addBox(id, rw(id, -5.85), -0.5, 0.7, 0.6);
}
function detCorreio(room) {
  const id = room.id, mb = achaG(room, -3.4, -3.4), bf = achaG(room, 3.4, -3.8), esc = toon(corMult(0xe5383b, 0.75));
  if (mb) {
    part(cyl(0.74, 0.8, 0.14, 18), esc, 0, 0.07, 0, 0.03, mb); pc(tor(0.62, 0.05, 6, 24), esc, 0, 1.9, 0, 0.01, mb, Math.PI / 2); // base e aro
    part(box(0.56, 0.38, 0.03), toon(0xfff6e4), 0, 0.62, 0.64, 0.02, mb); [-1, 1].forEach((s) => pc(box(0.34, 0.025, 0.02), M.ink, s * 0.13, 0.7, 0.66, 0, mb, 0, 0, -s * 0.5)); // envelope
  }
  if (bf) { [-0.9, 0.9].forEach((x) => part(box(0.5, 0.12, 0.7), M.woodDark, x, 0.06, 0, 0.025, bf)); part(cyl(0.02, 0.02, 1.4, 5), toon(0xe5383b), 0.72, 2.25, 0.05, 0, bf); part(sph(0.08, 8, 6), toon(0xe5383b), 0.72, 1.5, 0.05, 0.012, bf); } // pés e cordinha do sino
  const pk = new T.Group(); pk.position.set(-5.6, 0, -3.75); room.g.add(pk); // pilha de encomendas amarradas
  [[0, 0.4, 0, 1.2, 0.8, 0.9, 0.1, 0xc9955a], [0.1, 1.05, 0, 0.8, 0.5, 0.7, -0.25, 0xe9c46a], [-0.15, 1.45, 0.02, 0.5, 0.3, 0.4, 0.3, 0x8fd3ff]].forEach(([x, y, z, w, hh, d, r, c]) => {
    const b = new T.Group(); b.position.set(x, y, z); b.rotation.y = r; pk.add(b);
    part(box(w, hh, d), toon(c), 0, 0, 0, 0.04, b); part(box(0.05, hh + 0.02, d + 0.02), toon(0xe5383b), 0, 0, 0, 0, b); part(box(w + 0.02, hh + 0.02, 0.05), toon(0xe5383b), 0, 0, 0, 0, b); });
  addBox(id, rw(id, -5.6), -3.75, 0.7, 0.55);
  plantaPapel(room, 5.95, -2.3, 0.95);
}
function salaPapel(room, orig, detalhes) {
  try { salaEstrutura(room); } catch (e) { console.warn('papel: estrutura da sala', room.id, e); }
  const n0 = room.g.children.length; orig(room);
  try { detalhes(room); } catch (e) { console.warn('papel: detalhes da sala', room.id, e); }
  coletaDobras(room.g, room.id, n0); // os móveis também se levantam ao entrar
}
const _roomPena0 = roomPena, _roomBiblio0 = roomBiblio, _roomAtelie0 = roomAtelie, _roomGrafica0 = roomGrafica, _roomCorreio0 = roomCorreio;
roomPena = (room) => salaPapel(room, _roomPena0, detPena);
roomBiblio = (room) => salaPapel(room, _roomBiblio0, detBiblio);
roomAtelie = (room) => salaPapel(room, _roomAtelie0, detAtelie);
roomGrafica = (room) => salaPapel(room, _roomGrafica0, detGrafica);
roomCorreio = (room) => salaPapel(room, _roomCorreio0, detCorreio);

// ---------- "Ler em voz alta": escolhe a voz mais natural que o aparelho tiver ----------
// As 24 falas gravadas da Pena não passam por aqui. Isto vale só para as falas sem gravação.
function melhorVozPt() {
  let vs = []; try { vs = speechSynthesis.getVoices(); } catch (e) {}
  const br = vs.filter((v) => /^pt[-_]BR/i.test(v.lang)), pt = br.length ? br : vs.filter((v) => /^pt/i.test(v.lang));
  const nota = (v) => (/natural|neural|online/i.test(v.name) ? 40 : 0) + (/google/i.test(v.name) ? 30 : 0) + (/francisca|thalita|luciana|fernanda|let[ií]cia|yara|maria/i.test(v.name) ? 12 : 0);
  return pt.sort((a, b) => nota(b) - nota(a))[0] || null;
}
try { if (window.speechSynthesis) { speechSynthesis.getVoices(); speechSynthesis.addEventListener('voiceschanged', () => {}); } } catch (e) {}
speak = function (txt) {
  if (!S.voz || !window.speechSynthesis) return;
  try {
    speechSynthesis.cancel(); const v = melhorVozPt(); if (!v) return; // sem voz em português, melhor ficar em silêncio do que ler com sotaque de robô
    const u = new SpeechSynthesisUtterance(txt.replace(/\p{Extended_Pictographic}/gu, '').replace(/\(a\)/g, '')); u.lang = 'pt-BR'; u.voice = v; u.rate = 0.96; u.pitch = 1.04; speechSynthesis.speak(u);
  } catch (e) {}
};
