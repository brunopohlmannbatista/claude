// ============================================================
// A vila: estações, colisões, praça, fonte, 5 casas, props sazonais, partículas
// ============================================================
const GAME = { area: 'vila', season: 'primavera', started: false, lock: false, panel: null, placing: null, dlg: null, cur: null, station: null, t: 0, entryOrbit: true };

const SEASONS = {
  primavera: { nome: 'Primavera', ic: '🌸', sky: 0xcbe9ff, ground: 0x93d46e, ground2: 0x7fc45d, path: 0xf1dcae, leafA: 0xffaccd, leafB: 0x9edd6b, pine: 0x4f9e5a, water: 0x5ec8ff, light: 0xfff4e2, amb: 1.55, dir: 1.85, flags: [0xff8fb8, 0x8fd3ff, 0xfff07a], part: { kind: 'petala', color: 0xffbfd6 }, window: 0xbfe8ff, rug: 0xff9fc0, scarf: '#ff7aa8', css: '#cbe9ff' },
  verao: { nome: 'Verão', ic: '☀️', sky: 0xa9dcff, ground: 0x7ccf55, ground2: 0x68bd45, path: 0xf5e2b0, leafA: 0x5fc24b, leafB: 0x3fa53f, pine: 0x3f8f4c, water: 0x46c2ff, light: 0xfff1cc, amb: 1.62, dir: 2.0, flags: [0xffd23f, 0xff5e5e, 0x38c6c0], part: { kind: 'brilho', color: 0xfff3a0 }, window: 0x8fd4ff, rug: 0xffd166, scarf: '#ffd23f', css: '#a9dcff' },
  outono: { nome: 'Outono', ic: '🍂', sky: 0xf8dcb6, ground: 0xc4b35a, ground2: 0xb09d47, path: 0xe9cf9b, leafA: 0xf28a2e, leafB: 0xd9502b, pine: 0x4a7d4a, water: 0x56b6e8, light: 0xffe2b8, amb: 1.5, dir: 1.8, flags: [0xf28a2e, 0x9b5a2e, 0xfff1cf], part: { kind: 'folha', color: 0xf08a2c }, window: 0xf7c98b, rug: 0xd9662b, scarf: '#ff8a3c', css: '#f8dcb6' },
  inverno: { nome: 'Inverno', ic: '❄️', sky: 0xdee8f3, ground: 0xedf2f8, ground2: 0xdde6f0, path: 0xd5dae4, leafA: 0xf2f6fb, leafB: 0xdce7f2, pine: 0x3f7a5a, water: 0xcdeeff, light: 0xf2f6ff, amb: 1.65, dir: 1.7, flags: [0xe5383b, 0xffffff, 0x3a86ff], part: { kind: 'neve', color: 0xffffff }, window: 0xd6e6f7, rug: 0x6fa8dc, scarf: '#e5383b', stripes: true, css: '#dee8f3' },
};
// Calendário do Brasil (hemisfério sul)
function seasonByDate(d = new Date()) {
  const md = (d.getMonth() + 1) * 100 + d.getDate();
  if (md >= 320 && md < 621) return 'outono';
  if (md >= 621 && md < 923) return 'inverno';
  if (md >= 923 && md < 1222) return 'primavera';
  return 'verao';
}
const SEASONAL = []; // {obj, seasons}
function seasonTag(obj, ...ss) { SEASONAL.push({ obj, seasons: ss }); return obj; }

// ---------- colisões ----------
const COLL = {}, BOUNDS = {};
function addCircle(area, x, z, r) { (COLL[area] = COLL[area] || []).push({ t: 'c', x, z, r }); }
function addBox(area, x, z, hw, hd, rot = 0) { (COLL[area] = COLL[area] || []).push({ t: 'b', x, z, hw, hd, c: Math.cos(rot), s: Math.sin(rot) }); }
function resolveColl(area, p, rad) {
  const L = COLL[area] || [];
  for (let pass = 0; pass < 2; pass++) for (const c of L) {
    if (c.t === 'c') {
      const dx = p.x - c.x, dz = p.z - c.z, d = Math.hypot(dx, dz), m = c.r + rad;
      if (d < m) { if (d < 1e-4) { p.x += m; continue; } p.x = c.x + (dx / d) * m; p.z = c.z + (dz / d) * m; }
    } else {
      const dx = p.x - c.x, dz = p.z - c.z; let lx = dx * c.c - dz * c.s, lz = dx * c.s + dz * c.c;
      const qx = clamp(lx, -c.hw, c.hw), qz = clamp(lz, -c.hd, c.hd), ex = lx - qx, ez = lz - qz, d = Math.hypot(ex, ez);
      if (d >= rad) continue;
      if (d > 1e-4) { lx = qx + (ex / d) * rad; lz = qz + (ez / d) * rad; }
      else { const px = c.hw - Math.abs(lx), pz = c.hd - Math.abs(lz); if (px < pz) lx = Math.sign(lx || 1) * (c.hw + rad); else lz = Math.sign(lz || 1) * (c.hd + rad); }
      p.x = c.x + lx * c.c + lz * c.s; p.z = c.z - lx * c.s + lz * c.c;
    }
  }
  const b = BOUNDS[area];
  if (b) {
    if (b.r) { const d = Math.hypot(p.x - b.x, p.z - b.z); if (d > b.r - rad) { p.x = b.x + ((p.x - b.x) / d) * (b.r - rad); p.z = b.z + ((p.z - b.z) / d) * (b.r - rad); } }
    else { p.x = clamp(p.x, b.x0, b.x1); p.z = clamp(p.z, b.z0, b.z1); }
  }
}
function collides(area, x, z, rad) { const p = { x, z }; resolveColl(area, p, rad); return Math.hypot(p.x - x, p.z - z) > 1e-3; }

// ---------- luz, céu ----------
function initLights() {
  LIGHT_AMB = new T.AmbientLight(0xffffff, 1.55);
  LIGHT_DIR = new T.DirectionalLight(0xfff4e2, 1.85); LIGHT_DIR.position.set(-10, 22, 14);
  scene.add(LIGHT_AMB, LIGHT_DIR, LIGHT_DIR.target);
  scene.background = new T.Color(0xcbe9ff);
  scene.fog = new T.Fog(0xcbe9ff, 48, 120);
}

// ---------- a vila ----------
const HOUSE_DEFS = [
  { id: 'pena', nome: 'Casa da Pena', ang: 270, wall: 0xffd45c, roof: 0xe5533d, trim: 0xfff3d6, door: 0x8a4b2a },
  { id: 'biblioteca', nome: 'Biblioteca', ang: 226, wall: 0x86c0f0, roof: 0x2f5d9e, trim: 0xffffff, door: 0x5a3a8a },
  { id: 'atelie', nome: 'Ateliê de Desenho', ang: 314, wall: 0xf6a9cb, roof: 0x8a5cc2, trim: 0xfff3d6, door: 0x3aa6a0 },
  { id: 'grafica', nome: 'Gráfica', ang: 184, wall: 0x95dbbd, roof: 0x2e8a6e, trim: 0xfff3d6, door: 0xe5533d },
  { id: 'correio', nome: 'Correio das Histórias', ang: 356, wall: 0xffb46e, roof: 0xc23b3b, trim: 0xfff3d6, door: 0x2f5d9e },
];
const HOUSES = {};
const VILLAGE = { group: null, trees: [], drops: [], smoke: { pena: [], grafica: [] }, bang: null, coletivaArch: null, butterflies: [] };
const HOUSE_R = 20, HW = 6.4, HH = 4.2, HD = 5.2;

function buildVillage() {
  const V = new T.Group(); VILLAGE.group = V; scene.add(V);
  BOUNDS.vila = { x: 0, z: 2, r: 35 };
  // chão
  const ground = new T.Mesh(new T.CircleGeometry(90, 56), M.grass); ground.rotation.x = -Math.PI / 2; V.add(ground);
  const R0 = seeded(7);
  for (let i = 0; i < 16; i++) { const a = R0() * 6.28, r = 12 + R0() * 26, m = new T.Mesh(geo('patch', () => new T.CircleGeometry(1, 18)), M.grass2); m.rotation.x = -Math.PI / 2; m.position.set(Math.cos(a) * r, 0.01, Math.sin(a) * r); m.scale.set(1.5 + R0() * 2.5, 1 + R0() * 1.5, 1); V.add(m); }
  // tufos de grama (instanciados)
  const tg = cone(0.12, 0.5, 5), tufts = new T.InstancedMesh(tg, M.grass2, 240), dm = new T.Object3D(); let ti = 0;
  for (let i = 0; i < 400 && ti < 240; i++) { const a = R0() * 6.28, r = 10.5 + R0() * 30, x = Math.cos(a) * r, z = Math.sin(a) * r; if (Math.abs(x) < 1.8 && z > 9) continue; for (let k = 0; k < 3 && ti < 240; k++) { dm.position.set(x + (k - 1) * 0.12, 0.22, z + (k % 2) * 0.1); dm.rotation.set((k - 1) * 0.3, 0, (k - 1) * 0.25); dm.updateMatrix(); tufts.setMatrixAt(ti++, dm.matrix); } }
  tufts.count = ti; V.add(tufts);
  // praça
  part(cyl(9.6, 9.6, 0.16, 56), M.stone, 0, 0.08, 0, 0.1, V);
  [[7.6, 7.9], [4.3, 4.55]].forEach(([a, b]) => { const r = new T.Mesh(new T.RingGeometry(a, b, 56), M.stoneDark); r.rotation.x = -Math.PI / 2; r.position.y = 0.17; V.add(r); });
  for (let i = 0; i < 24; i++) { const a = (i / 24) * Math.PI * 2; const s = new T.Mesh(cyl(0.32, 0.32, 0.04, 8), M.stoneDark); s.position.set(Math.cos(a) * 6, 0.18, Math.sin(a) * 6); V.add(s); }
  // caminhos até as casas + entrada sul
  const pathTo = (angDeg, r0, r1, w = 2.6) => { const a = (angDeg * Math.PI) / 180, L = r1 - r0, cx = Math.cos(a) * (r0 + L / 2), cz = Math.sin(a) * (r0 + L / 2); const m = part(box(w, 0.06, L), M.path, cx, 0.03, cz, 0.05, V); m.rotation.y = Math.atan2(Math.cos(a), Math.sin(a)); for (let s = 0; s < L / 1.6; s++) { const rr = r0 + 0.8 + s * 1.6; const st = new T.Mesh(cyl(0.38, 0.42, 0.05, 9), M.stoneDark); st.position.set(Math.cos(a) * rr + Math.sin(a) * ((s % 2) - 0.5) * 0.7, 0.07, Math.sin(a) * rr - Math.cos(a) * ((s % 2) - 0.5) * 0.7); V.add(st); } };
  HOUSE_DEFS.forEach((d) => pathTo(d.ang, 9.4, 17.2));
  pathTo(90, 9.4, 33, 3);
  pathTo(PORTAL.ang, 9.4, 25.4, 2.2);
  buildFountain(V);
  HOUSE_DEFS.forEach((d) => buildHouse(d, V));
  // bancos
  [40, 140, 205, 335].forEach((ang) => { const a = (ang * Math.PI) / 180; buildBench(V, Math.cos(a) * 7, Math.sin(a) * 7); });
  // postes com bandeirinhas
  const lampAng = [20, 65, 115, 160, 205, 247, 292, 335], tops = [];
  lampAng.forEach((ang) => { const a = (ang * Math.PI) / 180, x = Math.cos(a) * 10.1, z = Math.sin(a) * 10.1; tops.push(buildLamp(V, x, z)); addCircle('vila', x, z, 0.3); });
  for (let i = 0; i < tops.length; i++) buildBunting(V, tops[i], tops[(i + 1) % tops.length]);
  // árvores
  const treeSpots = [[205, 23, 'r'], [247, 23.5, 'p'], [292, 23.5, 'r'], [335, 23, 'p'], [164, 21.5, 'p'], [16, 21.5, 'r']];
  for (let ang = 150; ang <= 390; ang += 17) treeSpots.push([ang, 30 + (ang % 3), ang % 34 === 0 ? 'p' : 'r']);
  treeSpots.forEach(([ang, r, k], i) => { const a = (ang * Math.PI) / 180; buildTree(V, Math.cos(a) * r, Math.sin(a) * r, 0.9 + ((i * 37) % 10) / 25, k === 'p' ? 'pine' : 'round'); });
  [[-12, 16, 'round'], [11.2, 17.4, 'pine'], [-18, 23, 'pine'], [19, 22, 'round'], [-25, 10, 'round'], [26, 8, 'pine'], [-9, 27, 'pine'], [10, 28, 'round']].forEach(([x, z, k], i) => buildTree(V, x, z, 0.95 + (i % 3) * 0.12, k));
  buildEntranceArch(V);
  buildPortalCantinho(V);
  buildSeasonalProps(V);
  buildColetiva(V);
  initParticles();
}

function buildFountain(V) {
  const g = new T.Group(); V.add(g);
  part(cyl(3.2, 3.45, 0.8, 36), M.stone2, 0, 0.4, 0, 0.09, g);
  const rim = part(tor(3.1, 0.24, 8, 44), M.stone, 0, 0.82, 0, 0.05, g); rim.rotation.x = Math.PI / 2;
  part(cyl(2.9, 2.9, 0.1, 36), M.water, 0, 0.72, 0, 0, g);
  part(cyl(0.45, 0.62, 1.9, 14), M.stone2, 0, 1.6, 0, 0.06, g);
  part(cyl(1.45, 0.75, 0.48, 26), M.stone, 0, 2.6, 0, 0.07, g);
  part(cyl(1.28, 1.28, 0.06, 26), M.water, 0, 2.83, 0, 0, g);
  // escultura: livro aberto
  const book = new T.Group(); book.position.set(0, 3.25, 0); g.add(book);
  [-1, 1].forEach((s) => { const cv = part(box(0.95, 0.1, 1.25), toon(0xe5533d), s * 0.47, 0, 0, 0.04, book); cv.rotation.z = s * 0.28; const pg = part(box(0.86, 0.12, 1.12), M.paper, s * 0.45, 0.07, 0, 0.03, book); pg.rotation.z = s * 0.28; });
  part(box(0.12, 0.3, 1.25), toon(0xb83a2c), 0, -0.08, 0, 0.03, book);
  const mark = part(box(0.08, 0.7, 0.16), toon(0xffd23f), 0.1, -0.35, 0.5, 0.02, book); mark.rotation.z = 0.15;
  // gotas
  for (let i = 0; i < 10; i++) { const d = new T.Mesh(sph(0.09, 8, 6), M.water); d.userData = { a: (i / 10) * Math.PI * 2, p: i / 10 }; g.add(d); VILLAGE.drops.push(d); }
  VILLAGE.fountain = g;
  addCircle('vila', 0, 0, 3.55);
}

function buildHouse(d, V) {
  const g = new T.Group(); const a = (d.ang * Math.PI) / 180, x = Math.cos(a) * HOUSE_R, z = Math.sin(a) * HOUSE_R, rot = Math.atan2(-x, -z);
  g.position.set(x, 0, z); g.rotation.y = rot; V.add(g);
  part(box(HW + 0.7, 0.5, HD + 0.7), toon(0xa59aa8), 0, 0.25, 0, 0.07, g);
  part(box(HW, HH, HD), toon(d.wall), 0, 0.5 + HH / 2, 0, 0.1, g);
  // cantoneiras
  [-1, 1].forEach((s) => part(box(0.3, HH, 0.3), toon(d.trim), s * (HW / 2), 0.5 + HH / 2, HD / 2, 0.04, g));
  const roofG = geo('roof', () => { const sh = new T.Shape(); sh.moveTo(-HW / 2 - 0.65, 0); sh.lineTo(HW / 2 + 0.65, 0); sh.lineTo(0, 2.9); sh.closePath(); const e = new T.ExtrudeGeometry(sh, { depth: HD + 0.9, bevelEnabled: false }); e.translate(0, 0, -(HD + 0.9) / 2); return e; });
  part(roofG, toon(d.roof), 0, 0.5 + HH, 0, 0.11, g);
  part(box(0.4, 0.4, HD + 1.1), toon(d.trim), 0, 0.5 + HH + 2.85, 0, 0.05, g);
  // neve no telhado (inverno)
  const slope = Math.atan2(2.9, HW / 2 + 0.65), sl = Math.hypot(2.9, HW / 2 + 0.65);
  [-1, 1].forEach((s) => { const sn = part(box(sl * 0.92, 0.22, HD + 1.0), M.snow, s * (HW / 4 + 0.32), 0.5 + HH + 1.55, 0, 0.04, g); sn.rotation.z = -s * slope; seasonTag(sn, 'inverno'); });
  // porta
  part(box(1.75, 2.6, 0.24), toon(d.trim), 0, 0.5 + 1.3, HD / 2 + 0.06, 0.06, g);
  part(box(1.32, 2.3, 0.26), toon(d.door), 0, 0.5 + 1.15, HD / 2 + 0.15, 0.05, g);
  part(sph(0.1, 10, 8), toon(0xffd23f), 0.44, 0.5 + 1.15, HD / 2 + 0.32, 0.03, g);
  part(box(2.2, 0.16, 1.1), M.stone2, 0, 0.58, HD / 2 + 0.6, 0.04, g);
  // janelas com floreira
  [-1, 1].forEach((s) => {
    const wx = s * 2.1, wy = 0.5 + 2.35;
    part(box(1.45, 1.45, 0.2), toon(d.trim), wx, wy, HD / 2 + 0.04, 0.06, g);
    part(box(1.12, 1.12, 0.22), WINDOW_MAT, wx, wy, HD / 2 + 0.07, 0, g);
    part(box(1.12, 0.1, 0.27), toon(d.trim), wx, wy, HD / 2 + 0.1, 0, g); part(box(0.1, 1.12, 0.27), toon(d.trim), wx, wy, HD / 2 + 0.1, 0, g);
    part(box(1.55, 0.36, 0.46), M.woodDark, wx, wy - 0.95, HD / 2 + 0.3, 0.05, g);
    const fl = new T.Group(); g.add(fl); seasonTag(fl, 'primavera', 'verao');
    [-0.5, 0, 0.5].forEach((o, i) => part(sph(0.17, 10, 8), toon([0xff8fb8, 0xffd23f, 0xa77bff][(i + (s > 0 ? 1 : 0)) % 3]), wx + o, wy - 0.68, HD / 2 + 0.32, 0.03, fl));
    const sn = part(box(1.5, 0.12, 0.42), M.snow, wx, wy - 0.72, HD / 2 + 0.3, 0.03, g); seasonTag(sn, 'inverno');
  });
  signBoard(d.nome, 3.4, 0.66, g, 0, 0.5 + HH - 0.5, HD / 2 + 0.14, { bg: '#f6deb2', size: 60 });
  // detalhes de cada casa
  const extra = { pena: housePena, biblioteca: houseBiblio, atelie: houseAtelie, grafica: houseGrafica, correio: houseCorreio }[d.id];
  extra && extra(g, d);
  addBox('vila', x, z, HW / 2 + 0.4, HD / 2 + 0.4, rot);
  const nx = Math.sin(rot), nz = Math.cos(rot);
  HOUSES[d.id] = { id: d.id, nome: d.nome, def: d, group: g, x, z, rot, nx, nz, doorX: x + nx * (HD / 2 + 1.7), doorZ: z + nz * (HD / 2 + 1.7), wreathX: x + nx * (HD / 2 + 0.34), wreathZ: z + nz * (HD / 2 + 0.34) };
}
function chimney(g, x, z, color, key) {
  part(box(0.9, 2.2, 0.9), toon(color), x, 0.5 + HH + 1.9, z, 0.06, g);
  part(box(1.1, 0.3, 1.1), toon(0x6f5b6e), x, 0.5 + HH + 3.05, z, 0.05, g);
  for (let i = 0; i < 4; i++) { const p = part(sph(0.32, 10, 8), toon(0xf4f1f6), x, 0.5 + HH + 3.4, z, 0.04, g); p.userData.ph = i / 4; p.visible = false; VILLAGE.smoke[key].push(p); }
}
function housePena(g) {
  chimney(g, -1.8, -0.9, 0xc9694a, 'pena');
  const rw = part(cyl(0.6, 0.6, 0.2, 24), toon(0xfff3d6), 0, 0.5 + HH + 1.05, HD / 2 + 0.47, 0.05, g); rw.rotation.x = Math.PI / 2;
  const gl = part(cyl(0.44, 0.44, 0.22, 24), WINDOW_MAT, 0, 0.5 + HH + 1.05, HD / 2 + 0.5, 0, g); gl.rotation.x = Math.PI / 2;
  // cata-vento de pena
  part(cyl(0.05, 0.05, 1.2, 6), M.ink, 1.6, 0.5 + HH + 2.5, 0, 0.02, g);
  const f = part(sph(0.3, 12, 8), M.white, 1.6, 0.5 + HH + 3.1, 0, 0.04, g); f.scale.set(0.5, 1.4, 0.2); f.rotation.z = 0.5; VILLAGE.vane = f;
}
function houseBiblio(g) {
  [-1, 1].forEach((s) => { part(cyl(0.3, 0.34, HH, 14), M.white, s * 3.0, 0.5 + HH / 2, HD / 2 + 0.5, 0.05, g); part(box(0.8, 0.3, 0.8), M.white, s * 3.0, 0.5 + HH, HD / 2 + 0.5, 0.04, g); });
  part(box(6.8, 0.3, 1.2), M.white, 0, 0.5 + HH + 0.12, HD / 2 + 0.4, 0.05, g);
  const cols = [0xe5533d, 0x4fae4c, 0xffd23f];
  cols.forEach((c, i) => { const b = part(box(1.9 - i * 0.2, 0.5, 1.4 - i * 0.1), toon(c), HW / 2 + 1.4, 0.25 + i * 0.52, 0.6, 0.05, g); b.rotation.y = i * 0.25 - 0.2; part(box(1.7 - i * 0.2, 0.4, 0.05), M.paper, 0, 0, 0.7 - i * 0.05, 0, b); });
}
function houseAtelie(g) {
  const pen = new T.Group(); pen.position.set(HW / 2 + 0.55, 0, 0.6); pen.rotation.z = 0.22; g.add(pen);
  part(cyl(0.38, 0.38, 4.4, 6), toon(0xffd23f), 0, 2.6, 0, 0.06, pen);
  part(cyl(0.4, 0.4, 0.5, 6), toon(0xc9ced8), 0, 4.95, 0, 0.04, pen);
  part(cyl(0.38, 0.38, 0.5, 12), toon(0xff8fb8), 0, 5.4, 0, 0.05, pen);
  const tip = part(cone(0.38, 0.9, 6), toon(0xf3c99a), 0, -0.05, 0, 0.05, pen); tip.rotation.x = Math.PI;
  const lead = part(cone(0.13, 0.3, 6), M.ink, 0, -0.42, 0, 0.02, pen); lead.rotation.x = Math.PI;
  pen.position.y = 0.55;
  [[-1.6, 3.4, 0xff6f91], [1.4, 1.4, 0x6ec6ff], [-2.5, 1.2, 0x7ed36b], [2.6, 3.8, 0xa77bff]].forEach(([px, py, c]) => { const s = part(sph(0.3, 10, 8), toon(c), px, py, HD / 2 + 0.02, 0.03, g); s.scale.set(1, 0.8, 0.15); });
}
function houseGrafica(g) {
  chimney(g, 1.9, -1.0, 0x6f8a80, 'grafica');
  const gear = new T.Group(); gear.position.set(-HW / 2 - 0.2, 0.5 + 2.6, 0.2); gear.rotation.z = Math.PI / 2; g.add(gear);
  part(cyl(1.0, 1.0, 0.3, 20), toon(0xffc93c), 0, 0, 0, 0.05, gear);
  part(cyl(0.35, 0.35, 0.36, 12), toon(0x7a6b85), 0, 0, 0, 0.03, gear);
  for (let i = 0; i < 8; i++) { const t = part(box(0.38, 0.3, 0.38), toon(0xffc93c), 0, 0, 0, 0.04, gear); const a = (i / 8) * Math.PI * 2; t.position.set(Math.cos(a) * 1.12, 0, Math.sin(a) * 1.12); t.rotation.y = -a; }
  VILLAGE.gear = gear;
}
function houseCorreio(g) {
  const mb = new T.Group(); mb.position.set(-3.9, 0, HD / 2 + 1.4); g.add(mb);
  part(cyl(0.1, 0.1, 1.4, 8), M.woodDark, 0, 0.7, 0, 0.03, mb);
  part(box(0.8, 0.6, 1.1), toon(0x3a86ff), 0, 1.55, 0, 0.05, mb);
  const top = part(cyl(0.4, 0.4, 1.1, 14, 1), toon(0x3a86ff), 0, 1.85, 0, 0.05, mb); top.rotation.x = Math.PI / 2;
  const flag = part(box(0.06, 0.5, 0.2), toon(0xe5383b), 0.45, 1.95, -0.2, 0.02, mb); flag.userData.flag = true; VILLAGE.mailFlag = flag;
  const env = new T.Group(); env.position.set(0, 0.5 + HH + 1.0, HD / 2 + 0.48); g.add(env);
  part(box(1.4, 0.9, 0.08), M.white, 0, 0, 0, 0.05, env);
  const fl1 = part(box(0.85, 0.06, 0.1), M.ink, -0.33, 0.18, 0.04, 0, env); fl1.rotation.z = -0.55; const fl2 = part(box(0.85, 0.06, 0.1), M.ink, 0.33, 0.18, 0.04, 0, env); fl2.rotation.z = 0.55;
  part(cyl(0.15, 0.15, 0.1, 12), toon(0xe5383b), 0, 0.02, 0.06, 0.02, env).rotation.x = Math.PI / 2;
}
function buildBench(V, x, z) {
  const g = new T.Group(); g.position.set(x, 0, z); g.rotation.y = Math.atan2(-x, -z); V.add(g);
  part(box(2.2, 0.16, 0.7), M.wood, 0, 0.62, 0, 0.05, g);
  part(box(2.2, 0.55, 0.14), M.wood, 0, 1.05, -0.32, 0.05, g);
  [-0.9, 0.9].forEach((s) => { part(box(0.14, 0.62, 0.6), M.woodDark, s, 0.31, 0, 0.04, g); part(box(0.14, 0.5, 0.14), M.woodDark, s, 0.95, -0.32, 0.03, g); });
  const sn = part(box(2.1, 0.08, 0.6), M.snow, 0, 0.73, 0.02, 0.02, g); seasonTag(sn, 'inverno');
  addBox('vila', x, z, 1.15, 0.4, g.rotation.y);
  inter({ x, z, r: 1.8, y: 1.6, label: () => (P.sitting ? null : '🪑 Sentar'), act: () => sitAt(x + Math.sin(g.rotation.y) * 0.1, z + Math.cos(g.rotation.y) * 0.1, 0.45, 1) });
}
function buildLamp(V, x, z) {
  const g = new T.Group(); g.position.set(x, 0, z); V.add(g);
  part(cyl(0.12, 0.18, 3.4, 8), toon(0x3b3355), 0, 1.7, 0, 0.04, g);
  part(cyl(0.3, 0.3, 0.12, 8), toon(0x3b3355), 0, 0.06, 0, 0.03, g);
  part(box(0.55, 0.6, 0.55), M.lamp, 0, 3.6, 0, 0.06, g);
  part(cone(0.45, 0.35, 4), toon(0x3b3355), 0, 4.08, 0, 0.04, g).rotation.y = Math.PI / 4;
  const sn = part(cone(0.42, 0.18, 4), M.snow, 0, 4.3, 0, 0.02, g); sn.rotation.y = Math.PI / 4; seasonTag(sn, 'inverno');
  return new T.Vector3(x, 3.35, z);
}
function buildBunting(V, a, b) {
  const n = 9, sag = 0.75;
  const shape = geo('flag', () => { const s = new T.Shape(); s.moveTo(-0.22, 0); s.lineTo(0.22, 0); s.lineTo(0, -0.5); s.closePath(); return new T.ExtrudeGeometry(s, { depth: 0.03, bevelEnabled: false }); });
  const dir = Math.atan2(b.x - a.x, b.z - a.z);
  for (let i = 1; i < n; i++) {
    const t = i / n, x = lerp(a.x, b.x, t), z = lerp(a.z, b.z, t), y = lerp(a.y, b.y, t) - Math.sin(t * Math.PI) * sag;
    const f = part(shape, M.flag[i % 3], x, y, z, 0.035, V); f.rotation.y = dir + Math.PI / 2; f.userData.sw = i * 0.7; VILLAGE.flags = VILLAGE.flags || []; VILLAGE.flags.push(f);
  }
  // cordão
  const pts = []; for (let i = 0; i <= 12; i++) { const t = i / 12; pts.push(new T.Vector3(lerp(a.x, b.x, t), lerp(a.y, b.y, t) - Math.sin(t * Math.PI) * sag + 0.02, lerp(a.z, b.z, t))); }
  const tube = new T.Mesh(new T.TubeGeometry(new T.CatmullRomCurve3(pts), 16, 0.025, 4), OUTLINE.clone()); tube.material.side = T.FrontSide; V.add(tube);
}
function buildTree(V, x, z, s, kind) {
  const g = new T.Group(); g.position.set(x, 0, z); g.scale.setScalar(s); V.add(g);
  if (kind === 'pine') {
    part(cyl(0.25, 0.32, 1.2, 8), M.trunk, 0, 0.6, 0, 0.05, g);
    [[1.9, 2.2, 1.75], [1.5, 1.9, 2.9], [1.0, 1.5, 3.95]].forEach(([r, hh, y]) => part(cone(r, hh, 10), M.pine, 0, y, 0, 0.08, g));
    [[1.55, 0.5, 2.55], [1.1, 0.5, 3.6], [0.6, 0.5, 4.5]].forEach(([r, hh, y]) => seasonTag(part(cone(r, hh, 10), M.snow, 0, y, 0, 0.04, g), 'inverno'));
  } else {
    part(cyl(0.28, 0.42, 2.3, 8), M.trunk, 0, 1.15, 0, 0.06, g);
    const f1 = part(sph(1.65, 14, 10), M.leafA, 0, 3.2, 0, 0.09, g); f1.scale.set(1, 0.92, 1);
    part(sph(1.15, 12, 9), M.leafB, -1.15, 2.65, 0.35, 0.08, g);
    part(sph(1.0, 12, 9), M.leafA, 1.05, 2.85, -0.25, 0.08, g);
    const fr = new T.Group(); g.add(fr); seasonTag(fr, 'primavera', 'verao');
    for (let i = 0; i < 5; i++) { const a = i * 1.3; part(sph(0.16, 8, 6), toon(i % 2 ? 0xffffff : 0xff4f6d), Math.cos(a) * 1.35, 3.0 + Math.sin(i * 2) * 0.6, Math.sin(a) * 1.35 + 0.3, 0.025, fr); }
  }
  g.userData.ph = x * 0.3 + z * 0.17; VILLAGE.trees.push(g);
  addCircle('vila', x, z, 0.65 * s);
}
function buildEntranceArch(V) {
  const g = new T.Group(); g.position.set(0, 0, 20); V.add(g);
  [-2.4, 2.4].forEach((s) => { part(box(0.6, 4.4, 0.6), M.wood, s, 2.2, 0, 0.06, g); addCircle('vila', s, 20, 0.45); part(sph(0.4, 12, 8), toon(0xffd23f), s, 4.6, 0, 0.05, g); });
  part(box(5.6, 0.5, 0.5), M.woodDark, 0, 4.2, 0, 0.06, g);
  signBoard('VILA DOS AUTORES', 4.6, 0.9, g, 0, 3.5, 0.32, { bg: '#ffc93c', size: 70, weight: 900 });
  const gar = new T.Group(); g.add(gar); seasonTag(gar, 'primavera', 'verao', 'outono');
  for (let i = 0; i < 11; i++) { const t = i / 10, x = lerp(-2.4, 2.4, t), y = 4.5 - Math.sin(t * Math.PI) * 0.35; part(sph(0.2, 8, 6), toon(i % 2 ? 0x4fae4c : 0xff8fb8), x, y, 0.35, 0.03, gar); }
  const ice = new T.Group(); g.add(ice); seasonTag(ice, 'inverno');
  for (let i = 0; i < 8; i++) { const ic = part(cone(0.1, 0.5 + (i % 3) * 0.2, 5), toon(0xdff4ff), -2.0 + i * 0.57, 3.75, 0.3, 0.02, ice); ic.rotation.x = Math.PI; }
}

// ---------- props sazonais da praça ----------
function buildSeasonalProps(V) {
  const sp = { primavera: new T.Group(), verao: new T.Group(), outono: new T.Group(), inverno: new T.Group() };
  for (const k in sp) { V.add(sp[k]); seasonTag(sp[k], k); }
  const flowerClump = (grp, x, z, cols) => { for (let i = 0; i < 5; i++) { const ox = x + Math.cos(i * 1.7) * 0.5, oz = z + Math.sin(i * 1.7) * 0.4; part(cyl(0.03, 0.03, 0.5, 5), toon(0x3c9a3c), ox, 0.25, oz, 0, grp); part(sph(0.15, 8, 6), toon(cols[i % cols.length]), ox, 0.55, oz, 0.03, grp); } };
  // primavera: canteiros e borboletas
  [[-11.5, 4], [11.5, 4.5], [-8, -12], [8.5, -12.5], [-15, -6], [15, -5]].forEach(([x, z]) => flowerClump(sp.primavera, x, z, [0xff8fb8, 0xffffff, 0xa77bff, 0xffd23f]));
  for (let i = 0; i < 5; i++) { const b = new T.Group(); const c = [0xffd23f, 0x8fd3ff, 0xff8fb8][i % 3]; const w1 = part(box(0.32, 0.02, 0.26), toon(c), -0.17, 0, 0, 0.02, b), w2 = part(box(0.32, 0.02, 0.26), toon(c), 0.17, 0, 0, 0.02, b); b.userData = { w1, w2, ph: i * 1.3, cx: rnd(-12, 12), cz: rnd(-10, 12) }; sp.primavera.add(b); VILLAGE.butterflies.push(b); }
  // verão: guarda-sol, toalha, girassóis, conchas na areia
  const um = new T.Group(); um.position.set(13, 0, 6); sp.verao.add(um);
  part(cyl(0.07, 0.07, 3, 8), M.white, 0, 1.5, 0, 0.03, um); part(cone(1.9, 0.9, 8), toon(0xff5e5e), 0, 3.1, 0, 0.07, um);
  const sand = part(cyl(2.6, 2.8, 0.08, 20), toon(0xf3d48b), 0.3, 0.04, 0.6, 0.04, um); sand.scale.z = 0.75;
  part(box(1.0, 0.05, 1.8), toon(0x38c6c0), -0.6, 0.1, 0.6, 0.03, um);
  part(sph(0.35, 14, 10), toon(0xffd23f), 1.3, 0.35, 1.2, 0.04, um);
  addCircle('vila', 13, 6, 0.3);
  [[-12, 3], [-13.5, 5.5], [12.5, -4], [-7, -13]].forEach(([x, z]) => { const s = new T.Group(); s.position.set(x, 0, z); sp.verao.add(s); part(cyl(0.06, 0.08, 2.2, 6), toon(0x3c9a3c), 0, 1.1, 0, 0.03, s); const fl = part(cyl(0.55, 0.55, 0.12, 16), toon(0xffd23f), 0, 2.25, 0.08, 0.05, s); fl.rotation.x = Math.PI / 2 - 0.3; const ce = part(cyl(0.28, 0.28, 0.14, 14), toon(0x8b5a2b), 0, 2.25, 0.12, 0.02, s); ce.rotation.x = Math.PI / 2 - 0.3; });
  // outono: abóboras, montes de folhas, fardo de feno
  [[-11, 5], [11.5, 3.5], [-6.5, -12.5], [6.5, -13], [3.2, 15], [-3.5, 15.5]].forEach(([x, z], i) => { const p = new T.Group(); p.position.set(x, 0, z); sp.outono.add(p); const pu = part(sph(0.55, 14, 10), toon(0xf28a2e), 0, 0.42, 0, 0.05, p); pu.scale.y = 0.75; part(cyl(0.06, 0.08, 0.3, 6), toon(0x5a7a2e), 0, 0.9, 0, 0.02, p); if (i % 2) { const lp = part(sph(0.9, 12, 8), toon(0xd9502b), 1.0, 0.1, 0.4, 0.05, p); lp.scale.y = 0.35; } });
  const hay = part(cyl(0.8, 0.8, 1.6, 16), toon(0xe9c46a), 13, 0.8, 5.5, 0.06, sp.outono); hay.rotation.z = Math.PI / 2; addCircle('vila', 13, 5.5, 0.9);
  // inverno: bonecos de neve e montes de neve
  [[12.5, 5], [-12, 4]].forEach(([x, z]) => { const s = new T.Group(); s.position.set(x, 0, z); sp.inverno.add(s); part(sph(0.85, 14, 10), M.snow, 0, 0.8, 0, 0.06, s); part(sph(0.6, 14, 10), M.snow, 0, 2.0, 0, 0.05, s); part(sph(0.42, 12, 9), M.snow, 0, 2.85, 0, 0.05, s); const n = part(cone(0.09, 0.4, 8), toon(0xff8a3c), 0, 2.85, 0.5, 0.02, s); n.rotation.x = Math.PI / 2; part(cyl(0.6, 0.6, 0.18, 14), toon(0xe5383b), 0, 2.45, 0, 0.03, s); part(cyl(0.32, 0.32, 0.4, 12), M.ink, 0, 3.35, 0, 0.03, s); part(cyl(0.5, 0.5, 0.06, 12), M.ink, 0, 3.17, 0, 0.02, s); addCircle('vila', x, z, 0.8); });
  [[-6, -12.5], [6.5, -12.8], [3.4, 15], [-3.6, 15.4], [-15, -5], [15.5, -4]].forEach(([x, z]) => { const m = part(sph(0.95, 12, 8), M.snow, x, 0, z, 0.04, sp.inverno); m.scale.y = 0.45; });
}

// ---------- decoração coletiva da praça ----------
const COLETIVA_META = { flor: 12, fita: 6, graveto: 8 };
function buildColetiva(V) {
  // Baú da Turma
  const b = new T.Group(); b.position.set(-6.4, 0, 0.6); b.rotation.y = 1.2; V.add(b);
  part(box(1.5, 0.85, 1.0), toon(0x3aa6a0), 0, 0.45, 0, 0.06, b);
  part(box(1.55, 0.35, 1.05), toon(0x2e8a85), 0, 1.05, 0, 0.05, b);
  part(box(0.25, 0.3, 0.1), toon(0xffd23f), 0, 0.85, 0.53, 0.03, b);
  signBoard('Baú da Turma', 1.6, 0.4, b, 0, 1.7, 0, { bg: '#fff3d6', size: 50 });
  addCircle('vila', -6.4, 0.6, 0.9);
  VILLAGE.bauTurma = b;
  // Arco da Turma (aparece quando a meta é cumprida)
  const a = new T.Group(); a.position.set(0, 0, 9.9); a.visible = false; V.add(a);
  [-1.9, 1.9].forEach((s) => part(cyl(0.2, 0.24, 3.8, 10), M.white, s, 1.9, 0, 0.05, a));
  const ar = part(new T.TorusGeometry(1.9, 0.22, 10, 30, Math.PI), toon(0x4fae4c), 0, 3.8, 0, 0.05, a);
  for (let i = 0; i <= 12; i++) { const t = (i / 12) * Math.PI; part(sph(0.22, 8, 6), toon([0xff8fb8, 0xffd23f, 0xa77bff, 0xff5e5e][i % 4]), Math.cos(t) * 1.9, 3.8 + Math.sin(t) * 1.9, 0.18, 0.03, a); }
  for (let i = 0; i < 6; i++) { const f = part(box(0.08, 1.2, 0.04), toon([0xff4f6d, 0x3a86ff, 0xffd23f][i % 3]), -1.5 + i * 0.6, 3.6 - (i % 2) * 0.25, 0.2, 0.02, a); f.userData.sw = i; VILLAGE.flags.push(f); }
  VILLAGE.coletivaArch = a;
}

// ---------- partículas sazonais ----------
const PART = { mesh: null, n: 110, data: [], dm: null };
function initParticles() {
  const g = new T.PlaneGeometry(0.2, 0.2); PART.mat = new T.MeshBasicMaterial({ color: 0xffffff, side: T.DoubleSide });
  PART.mesh = new T.InstancedMesh(g, PART.mat, PART.n); PART.mesh.frustumCulled = false; scene.add(PART.mesh); PART.dm = new T.Object3D();
  for (let i = 0; i < PART.n; i++) PART.data.push({ x: rnd(-24, 24), y: rnd(0, 14), z: rnd(-22, 18), v: rnd(0.4, 1), ph: rnd(6.28), rs: rnd(0.6, 2) });
}
function updateParticles(dt, t) {
  if (!PART.mesh) return;
  PART.mesh.visible = areaExterna(GAME.area);
  if (!PART.mesh.visible) return;
  const k = SEASONS[GAME.season].part.kind, cx = camFocus.x, cz = camFocus.z, dm = PART.dm;
  for (let i = 0; i < PART.n; i++) {
    const d = PART.data[i];
    if (k === 'brilho') { d.y += dt * d.v * 0.35; d.x += Math.sin(t * d.rs + d.ph) * dt * 0.4; if (d.y > 5) d.y = 0.3; }
    else { d.y -= dt * d.v * (k === 'neve' ? 1.0 : k === 'folha' ? 1.2 : 0.75); d.x += Math.sin(t * d.rs + d.ph) * dt * (k === 'neve' ? 0.4 : 0.9); if (d.y < 0.05) { d.y = 13 + rnd(2); d.x = cx + rnd(-24, 24); d.z = cz + rnd(-22, 14); } }
    if (Math.abs(d.x - cx) > 26) d.x = cx + rnd(-24, 24);
    if (Math.abs(d.z - cz) > 24) d.z = cz + rnd(-22, 14);
    dm.position.set(d.x, d.y, d.z);
    if (k === 'brilho') { const s = 0.45 + 0.4 * Math.sin(t * 3 + d.ph); dm.scale.setScalar(Math.max(0.05, s)); dm.rotation.set(0, 0, t + d.ph); }
    else { dm.scale.setScalar(k === 'neve' ? 0.75 : k === 'folha' ? 1.25 : 1); dm.rotation.set(t * d.rs + d.ph, t * d.rs * 0.7, d.ph); }
    dm.updateMatrix(); PART.mesh.setMatrixAt(i, dm.matrix);
  }
  PART.mesh.instanceMatrix.needsUpdate = true;
}

// ---------- aplicar estação ----------
function applySeason(key, announce) {
  const s = SEASONS[key]; if (!s) return; GAME.season = key;
  M.grass.color.setHex(s.ground); M.grass2.color.setHex(s.ground2); M.path.color.setHex(s.path);
  M.leafA.color.setHex(s.leafA); M.leafB.color.setHex(s.leafB); M.pine.color.setHex(s.pine); M.water.color.setHex(s.water); M.rug.color.setHex(s.rug);
  ROOM_WIN.color.setHex(s.window); M.flag.forEach((m, i) => m.color.setHex(s.flags[i]));
  if (PART.mat) PART.mat.color.setHex(s.part.color);
  LIGHT_AMB.intensity = s.amb; LIGHT_DIR.intensity = s.dir; LIGHT_DIR.color.setHex(s.light);
  if (areaExterna(GAME.area)) { scene.background.setHex(s.sky); scene.fog.color.setHex(s.sky); }
  document.body.style.background = s.css; $('#stage').style.background = s.css;
  SEASONAL.forEach((e) => (e.obj.visible = e.seasons.includes(key)));
  VILLAGE.drops.forEach((d) => (d.visible = key !== 'inverno'));
  if (PENA.bb) PENA.bb.setCanvas(drawPena(s.scarf, !!s.stripes));
  const ic = $('#seasonIc'), tx = $('#seasonTx'); if (ic) { ic.textContent = s.ic; tx.textContent = s.nome; }
  if (announce) { toast(`${s.ic} Chegou o ${s.nome}! A vila mudou de roupa.`); Snd.whoosh(); }
  if (typeof refreshQuest === 'function') refreshQuest();
}
