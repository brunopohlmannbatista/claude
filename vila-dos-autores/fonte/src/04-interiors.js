// ============================================================
// Interiores "casinha de boneca": parede da frente invisível, câmera mais perto
// ============================================================
const ROOM_DEFS = {
  pena: { i: 0, wall: '#ffe6a8', pat: '#ffcf5c', kind: 'dots', floor: '#d9a066', win: -0.9 },
  biblioteca: { i: 1, wall: '#d3e8ff', pat: '#b0d2f7', kind: 'stripes', floor: '#b98657', win: 1.6 },
  atelie: { i: 2, wall: '#ffe2ef', pat: '#ffc0da', kind: 'splat', floor: '#e0b483', win: null },
  grafica: { i: 3, wall: '#d9f4e8', pat: '#afdfc8', kind: 'grid', floor: '#a77a54', win: 1.6 },
  correio: { i: 4, wall: '#ffe5cb', pat: '#ffc996', kind: 'env', floor: '#c98b5a', win: null },
};
const ROOMS = {};
const ROOM_FX = { fire: null, fireLight: null, logs: null, pend: null, hands: null, clockTex: null, globe: null, globeV: 0, lever: null, sheet: null, pages: [], bell: null, bellT: 9, chest: null, chestLid: null, easelMat: null, varal: [], mural: null, chalk: null, smokeOn: false, rollers: [] };

function wallpaper(def) {
  const c = mkCanvas(256, 256), g = c.getContext('2d'); g.fillStyle = def.wall; g.fillRect(0, 0, 256, 256); g.fillStyle = def.pat; g.strokeStyle = def.pat; g.lineWidth = 10;
  if (def.kind === 'dots') { for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) { g.beginPath(); g.arc(32 + x * 64 + (y % 2) * 32, 32 + y * 64, 9, 0, 7); g.fill(); } }
  if (def.kind === 'stripes') { for (let x = 0; x < 256; x += 64) g.fillRect(x, 0, 26, 256); }
  if (def.kind === 'splat') { const R = seeded(4); for (let i = 0; i < 9; i++) { g.fillStyle = ['#ffd0e3', '#d9efff', '#fff4c2', '#e2f7da'][i % 4]; g.beginPath(); g.arc(R() * 256, R() * 256, 6 + R() * 9, 0, 7); g.fill(); } }
  if (def.kind === 'grid') { g.lineWidth = 6; for (let x = 0; x <= 256; x += 64) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 256); g.stroke(); g.beginPath(); g.moveTo(0, x); g.lineTo(256, x); g.stroke(); } }
  if (def.kind === 'env') { g.lineWidth = 6; for (let y = 0; y < 2; y++) for (let x = 0; x < 2; x++) { const ox = 30 + x * 128 + (y % 2) * 30, oy = 34 + y * 128; g.strokeRect(ox, oy, 70, 48); g.beginPath(); g.moveTo(ox, oy); g.lineTo(ox + 35, oy + 26); g.lineTo(ox + 70, oy); g.stroke(); } }
  const t = canvasTex(c); t.wrapS = t.wrapT = T.RepeatWrapping; return t;
}
function planks(color) {
  const c = mkCanvas(512, 512), g = c.getContext('2d'); g.fillStyle = color; g.fillRect(0, 0, 512, 512); g.strokeStyle = 'rgba(34,26,43,.55)'; g.lineWidth = 5;
  for (let y = 0; y <= 512; y += 64) { g.beginPath(); g.moveTo(0, y); g.lineTo(512, y); g.stroke(); const off = (y / 64) % 2 ? 140 : 330; g.beginPath(); g.moveTo(off, y); g.lineTo(off, y + 64); g.stroke(); }
  g.fillStyle = 'rgba(34,26,43,.4)'; for (let y = 0; y < 512; y += 64) for (const x of [30, 260, 480]) { g.beginPath(); g.arc(x, y + 32, 4, 0, 7); g.fill(); }
  const t = canvasTex(c); t.wrapS = t.wrapT = T.RepeatWrapping; t.repeat.set(2, 1.4); return t;
}
const rw = (id, lx) => ROOMS[id].ox + lx;

function buildRoom(id) {
  const d = ROOM_DEFS[id], ox = 400 + d.i * 60, g = new T.Group(); g.position.set(ox, 0, 0); g.visible = false; scene.add(g);
  const room = { id, ox, g, d }; ROOMS[id] = room;
  BOUNDS[id] = { x0: ox - 6.3, x1: ox + 6.3, z0: -4.25, z1: 4.75 };
  const wp = wallpaper(d); wp.repeat.set(3, 1.2);
  const wpS = wallpaper(d); wpS.repeat.set(2.2, 1.2);
  const wallM = new T.MeshToonMaterial({ color: 0xffffff, map: wp, gradientMap: GRAD });
  const wallS = new T.MeshToonMaterial({ color: 0xf2ece4, map: wpS, gradientMap: GRAD });
  const floorM = new T.MeshToonMaterial({ color: 0xffffff, map: planks(d.floor), gradientMap: GRAD });
  part(box(14, 0.4, 10), floorM, 0, -0.2, 0, 0.07, g);
  part(box(14.4, 5.8, 0.4), wallM, 0, 2.9, -5.2, 0.08, g);
  part(box(0.4, 5.8, 10.4), wallS, -7.2, 2.9, 0, 0.08, g);
  part(box(0.4, 5.8, 10.4), wallS, 7.2, 2.9, 0, 0.08, g);
  part(box(14, 0.35, 0.16), M.woodDark, 0, 0.17, -4.94, 0.03, g);
  [-1, 1].forEach((s) => part(box(0.16, 0.35, 10), M.woodDark, s * 6.94, 0.17, 0, 0.03, g));
  part(box(14.8, 0.55, 0.5), M.wood, 0, 0.0, 5.25, 0.06, g);
  const rug = part(cyl(2.6, 2.6, 0.05, 36), M.rug, 0, 0.03, 1.2, 0.04, g); rug.scale.z = 0.62;
  const mat = part(box(2.2, 0.05, 0.9), toon(0xb5651d), 0, 0.03, 4.45, 0.03, g);
  const mt = textPlane('SAIR', 1.9, 0.6, { bg: '#c8783a', fg: '#fff8ec', size: 70, weight: 900 }); mt.rotation.x = -Math.PI / 2; mt.position.set(0, 0.06, 4.45); g.add(mt);
  if (d.win !== null) roomWindow(g, d.win);
  inter({ area: id, x: ox, z: 4.45, r: 1.6, y: 1.4, label: () => '🚪 Sair para a vila', act: () => exitHouse() });
  ({ pena: roomPena, biblioteca: roomBiblio, atelie: roomAtelie, grafica: roomGrafica, correio: roomCorreio })[id](room);
}
function roomWindow(g, x) {
  const w = new T.Group(); w.position.set(x, 3.4, -4.95); g.add(w);
  part(box(2.0, 1.8, 0.2), toon(0xfff3d6), 0, 0, 0, 0.06, w);
  part(box(1.6, 1.4, 0.22), ROOM_WIN, 0, 0, 0.02, 0, w);
  part(box(1.6, 0.1, 0.26), toon(0xfff3d6), 0, 0, 0.04, 0, w); part(box(0.1, 1.4, 0.26), toon(0xfff3d6), 0, 0, 0.04, 0, w);
  part(box(2.3, 0.16, 0.5), M.wood, 0, -1.0, 0.18, 0.04, w);
  [-1, 1].forEach((s) => { const c = part(box(0.45, 2.1, 0.12), toon(0xff8fb8), s * 1.2, 0.0, 0.25, 0.04, w); c.rotation.z = s * 0.06; });
  // vista sazonal pela janela
  seasonTag(part(sph(0.22, 10, 8), toon(0xffd23f), 0.45, 0.35, 0.05, 0, w), 'verao', 'primavera');
  const fl = new T.Group(); w.add(fl); seasonTag(fl, 'inverno'); for (let i = 0; i < 5; i++) part(sph(0.06, 6, 4), M.white, -0.6 + i * 0.3, -0.3 + (i % 2) * 0.5, 0.05, 0, fl);
  const lv = new T.Group(); w.add(lv); seasonTag(lv, 'outono'); for (let i = 0; i < 4; i++) { const l = part(sph(0.12, 8, 5), toon(0xf28a2e), -0.5 + i * 0.35, 0.3 - (i % 2) * 0.5, 0.05, 0, lv); l.scale.set(1, 0.5, 0.3); }
}
function seasonalDecor(parent, x, y, z) {
  const sp = new T.Group(); sp.position.set(x, y, z); parent.add(sp); seasonTag(sp, 'primavera');
  part(cyl(0.2, 0.15, 0.45, 10), toon(0x6ec6ff), 0, 0.22, 0, 0.03, sp); [0, 1, 2, 3].forEach((i) => part(sph(0.12, 8, 6), toon([0xff8fb8, 0xffd23f, 0xffffff, 0xa77bff][i]), Math.cos(i * 1.6) * 0.14, 0.58 + (i % 2) * 0.08, Math.sin(i * 1.6) * 0.1, 0.025, sp));
  const su = new T.Group(); su.position.set(x, y, z); parent.add(su); seasonTag(su, 'verao');
  part(cyl(0.18, 0.18, 0.4, 10), toon(0xe8f6ff), 0, 0.2, 0, 0.03, su); part(cyl(0.16, 0.16, 0.18, 10), toon(0xf3d48b), 0, 0.1, 0, 0, su); const sh = part(sph(0.12, 8, 6, 0, Math.PI * 2, 0, Math.PI / 2), toon(0xffb3c7), 0, 0.45, 0, 0.02, su); sh.scale.y = 0.6;
  const au = new T.Group(); au.position.set(x, y, z); parent.add(au); seasonTag(au, 'outono');
  [-0.2, 0.15].forEach((o, i) => { const p = part(sph(0.2 - i * 0.04, 10, 8), toon(0xf28a2e), o, 0.16, 0, 0.03, au); p.scale.y = 0.75; part(cyl(0.025, 0.03, 0.12, 5), toon(0x5a7a2e), o, 0.33 - i * 0.03, 0, 0.01, au); });
  const wi = new T.Group(); wi.position.set(x, y, z); parent.add(wi); seasonTag(wi, 'inverno');
  part(cyl(0.2, 0.24, 0.12, 12), M.woodDark, 0, 0.06, 0, 0.02, wi); part(sph(0.22, 14, 10), toon(0xdff4ff), 0, 0.32, 0, 0.03, wi); part(sph(0.08, 8, 6), M.white, 0, 0.26, 0, 0, wi);
}
function armchair(parent, x, z, rot, color) {
  const c = new T.Group(); c.position.set(x, 0, z); c.rotation.y = rot; parent.add(c);
  part(box(1.5, 0.5, 1.3), toon(color), 0, 0.45, 0, 0.05, c);
  part(box(1.5, 1.3, 0.35), toon(color), 0, 1.1, -0.5, 0.05, c);
  [-1, 1].forEach((s) => part(box(0.3, 0.75, 1.3), toon(color), s * 0.76, 0.75, 0, 0.05, c));
  part(box(1.15, 0.16, 0.95), toon(0xfff3d6), 0, 0.76, 0.08, 0.03, c);
  return c;
}
function craftBench(room, x, z, station) {
  const g = room.g, b = new T.Group(); b.position.set(x, 0, z); g.add(b);
  part(box(2.3, 0.2, 1.15), M.wood, 0, 1.0, 0, 0.05, b);
  [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([sx, sz]) => part(box(0.16, 1.0, 0.16), M.woodDark, sx * 1.0, 0.5, sz * 0.42, 0.03, b));
  const tools = new T.Group(); b.add(tools);
  part(cyl(0.18, 0.16, 0.4, 10), toon(0x6ec6ff), -0.6, 1.3, -0.15, 0.03, tools);
  [0xff4f6d, 0xffd23f, 0x4fae4c].forEach((c, i) => { const p = part(cyl(0.035, 0.035, 0.55, 6), toon(c), -0.66 + i * 0.07, 1.5, -0.15, 0.015, tools); p.rotation.z = (i - 1) * 0.2; });
  const hm = part(box(0.55, 0.06, 0.08), M.woodDark, 0.35, 1.13, 0.15, 0.02, tools); hm.rotation.y = 0.4; part(box(0.14, 0.12, 0.24), M.ink, 0.6, 1.15, 0.05, 0.02, tools);
  part(box(0.6, 0.04, 0.45), M.paper, 0.1, 1.12, -0.2, 0.02, tools);
  signBoard('Mesa de Criação', 1.9, 0.42, b, 0, 1.75, -0.45, { bg: '#fff3d6', size: 52 });
  addBox(room.id, rw(room.id, x), z, 1.2, 0.65);
  inter({ area: room.id, x: rw(room.id, x), z: z + 0.9, r: 1.8, y: 2.4, obj: tools, label: () => '🔨 Mesa de Criação', act: () => openCraft(station) });
}
function bookcase(room, x, z, w = 2.6, hh = 3.6, interact = true) {
  const g = room.g, sh = new T.Group(); sh.position.set(x, 0, z); g.add(sh);
  part(box(w, hh, 0.12), M.woodDark, 0, hh / 2, -0.34, 0.05, sh);
  [-1, 1].forEach((s) => part(box(0.14, hh, 0.8), M.wood, s * (w / 2 - 0.07), hh / 2, 0, 0.05, sh));
  part(box(w + 0.16, 0.16, 0.9), M.wood, 0, hh, 0, 0.05, sh);
  part(box(w, 0.2, 0.8), M.wood, 0, 0.1, 0, 0.04, sh);
  const books = new T.Group(); sh.add(books); const R = seeded(Math.round(x * 10 + room.ox));
  const levels = Math.floor(hh / 1.0);
  for (let L = 0; L < levels; L++) {
    const y = 0.2 + L * 1.0; if (L) part(box(w - 0.2, 0.08, 0.72), M.wood, 0, y, 0, 0.03, sh);
    let bx = -w / 2 + 0.25; while (bx < w / 2 - 0.35) { const bw = 0.16 + R() * 0.14, bh = 0.5 + R() * 0.32; const b = part(box(bw, bh, 0.5), toon([0xe5533d, 0x3a86ff, 0x4fae4c, 0xffd23f, 0xa77bff, 0xff8fb8][Math.floor(R() * 6)]), bx + bw / 2, y + 0.04 + bh / 2, 0.0, 0.025, books); if (R() < 0.15) b.rotation.z = 0.2; bx += bw + 0.03; }
  }
  addBox(room.id, rw(room.id, x), z, w / 2 + 0.05, 0.45);
  if (interact) inter({ area: room.id, x: rw(room.id, x), z: z + 1.1, r: 1.7, y: hh + 0.3, obj: books, hopH: 0.18, label: () => '📚 Ler a estante', act: () => { Snd.page(); say(['Dica de escrita: ' + pick(DICAS)], null, 'Livro da estante'); } });
  return sh;
}

// ---------- Casa da Pena (completa) ----------
function roomPena(room) {
  const g = room.g, id = 'pena';
  // lareira
  const fp = new T.Group(); fp.position.set(-3.8, 0, -4.45); g.add(fp);
  part(box(3.4, 3.0, 1.1), toon(0xc9a48a), 0, 1.5, 0, 0.07, fp);
  for (let i = 0; i < 6; i++) { const st = part(box(0.6, 0.3, 0.05), toon(0xb08e76), -1.2 + (i % 3) * 1.1 + (i > 2 ? 0.5 : 0), 2.2 + (i > 2 ? 0.45 : 0), 0.56, 0, fp); st.scale.x = 0.9 + (i % 2) * 0.2; }
  part(box(2.0, 1.7, 0.3), toon(0x3b2a33), 0, 0.9, 0.45, 0.03, fp);
  part(box(3.9, 0.28, 1.4), M.woodDark, 0, 3.12, 0.1, 0.05, fp);
  part(box(2.6, 0.18, 0.9), toon(0x9b8478), 0, 0.09, 0.85, 0.04, fp);
  const logs = new T.Group(); logs.position.set(0, 0, 0.5); fp.add(logs);
  [-0.25, 0.25].forEach((o, i) => { const l = part(cyl(0.14, 0.14, 1.2, 8), M.trunk, 0, 0.32 + i * 0.12, o * 0.4, 0.03, logs); l.rotation.z = Math.PI / 2; l.rotation.y = o * 1.2; });
  const fire = new T.Group(); fire.position.set(0, 0.4, 0.5); fp.add(fire);
  [[-0.32, 0.6, 0.28], [0.3, 0.7, 0.3], [0, 1.0, 0.4]].forEach(([x, hh, r]) => part(cone(r, hh, 8), M.fire1, x, hh / 2, 0, 0.03, fire));
  [[-0.15, 0.45, 0.15], [0.15, 0.55, 0.16], [0, 0.7, 0.2]].forEach(([x, hh, r]) => part(cone(r, hh, 8), M.fire2, x, hh / 2, 0.08, 0, fire));
  ROOM_FX.fire = fire; ROOM_FX.logs = logs;
  const lt = new T.PointLight(0xff9a3c, 0, 10, 1.4); lt.position.set(room.ox - 3.8, 1.6, -3.3); scene.add(lt); ROOM_FX.fireLight = lt;
  seasonalDecor(fp, 1.3, 3.27, 0.15);
  const gar = new T.Group(); fp.add(gar); seasonTag(gar, 'inverno', 'outono');
  for (let i = 0; i < 9; i++) part(sph(0.12, 8, 6), toon(i % 2 ? 0xe5383b : 0x2f8a4c), -1.6 + i * 0.4, 3.0 - Math.sin((i / 8) * Math.PI) * 0.25, 0.82, 0.02, gar);
  addBox(id, rw(id, -3.8), -4.45, 1.8, 0.75);
  inter({ area: id, x: rw(id, -3.8), z: -3.15, r: 2.0, y: 3.5, obj: logs, label: () => (S.flags.fogoOn ? '🔥 Apagar a lareira' : '🔥 Acender a lareira'), act: toggleFire });
  // poltrona
  const ch = armchair(g, -4.3, -1.3, 0.7, 0xe5533d);
  addBox(id, rw(id, -4.3), -1.3, 0.85, 0.8, 0.7);
  inter({ area: id, x: rw(id, -4.3) + Math.sin(0.7) * 1.1, z: -1.3 + Math.cos(0.7) * 1.1, r: 1.5, y: 2.2, obj: ch, hopH: 0.12, label: () => (P.sitting ? null : '🪑 Sentar na poltrona'), act: () => sitAt(rw(id, -4.3) + Math.sin(0.7) * 0.15, -1.3 + Math.cos(0.7) * 0.15, 0.75, 1) });
  // poleiro da Pena
  const pr = new T.Group(); pr.position.set(-0.9, 0, -4.1); g.add(pr);
  part(cyl(0.5, 0.6, 0.15, 14), M.woodDark, 0, 0.08, 0, 0.03, pr); part(cyl(0.07, 0.08, 2.2, 8), M.wood, 0, 1.15, 0, 0.03, pr);
  const bar = part(cyl(0.07, 0.07, 1.3, 8), M.wood, 0, 2.25, 0, 0.03, pr); bar.rotation.z = Math.PI / 2;
  part(cyl(0.18, 0.12, 0.18, 10), toon(0x6ec6ff), 0.55, 2.38, 0, 0.02, pr);
  addCircle(id, rw(id, -0.9), -4.1, 0.55);
  room.perch = new T.Vector3(rw(id, -0.9), 2.3, -4.05);
  // relógio de pêndulo
  const ck = new T.Group(); ck.position.set(5.3, 0, -4.5); g.add(ck);
  part(box(1.3, 4.4, 0.8), M.woodDark, 0, 2.2, 0, 0.06, ck);
  part(box(1.55, 0.32, 0.95), M.wood, 0, 4.5, 0, 0.05, ck);
  part(cone(0.5, 0.4, 4), M.wood, 0, 4.85, 0, 0.04, ck).rotation.y = Math.PI / 4;
  const fc = mkCanvas(256, 256); ROOM_FX.clockCanvas = fc; ROOM_FX.clockTex = canvasTex(fc); drawClockFace();
  const face = new T.Mesh(new T.CircleGeometry(0.48, 32), new T.MeshBasicMaterial({ map: ROOM_FX.clockTex })); face.position.set(0, 3.6, 0.42); ck.add(face);
  const ring = part(tor(0.5, 0.05, 6, 30), toon(0xffc928), 0, 3.6, 0.42, 0.015, ck);
  const hands = new T.Group(); hands.position.set(0, 3.6, 0.45); ck.add(hands);
  const hH = new T.Group(), mH = new T.Group(); hands.add(hH, mH);
  part(box(0.06, 0.26, 0.02), M.ink, 0, 0.12, 0, 0, hH); part(box(0.04, 0.38, 0.02), M.ink, 0, 0.18, 0.01, 0, mH);
  ROOM_FX.hands = { hH, mH };
  part(box(0.8, 1.9, 0.1), toon(0xf6eedd), 0, 1.7, 0.4, 0.03, ck);
  const pend = new T.Group(); pend.position.set(0, 2.55, 0.47); ck.add(pend);
  part(box(0.04, 1.15, 0.02), toon(0xffc928), 0, -0.58, 0, 0, pend);
  const bob = part(cyl(0.19, 0.19, 0.06, 16), M.gold, 0, -1.25, 0, 0.02, pend); bob.rotation.x = Math.PI / 2;
  ROOM_FX.pend = pend;
  addBox(id, rw(id, 5.3), -4.5, 0.7, 0.45);
  inter({ area: id, x: rw(id, 5.3), z: -3.4, r: 1.6, y: 5.0, obj: ck, hopH: 0.1, label: () => '🕰 Ver as horas', act: () => { const d = new Date(); const hh = d.getHours(), mm = String(d.getMinutes()).padStart(2, '0'); Snd.chime(Math.min(3, (hh % 12) || 3)); say([`Tic-tac! Agora são ${hh}h${mm}. Este relógio marca a hora de verdade, igualzinho ao seu aparelho.`]); } });
  // estante
  bookcase(room, 2.0, -4.55, 2.6, 3.6, true);
  // mesa com o Caderno de Ideias
  const tb = new T.Group(); tb.position.set(2.6, 0, -0.9); g.add(tb);
  part(box(2.6, 0.16, 1.5), M.wood, 0, 1.05, 0, 0.05, tb);
  [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach(([sx, sz]) => part(cyl(0.08, 0.08, 1.0, 8), M.woodDark, sx * 1.1, 0.5, sz * 0.6, 0.03, tb));
  const nb = new T.Group(); nb.position.set(0, 1.15, 0); tb.add(nb);
  part(box(1.5, 0.05, 1.0), toon(0xe5533d), 0, 0, 0, 0.03, nb);
  [-1, 1].forEach((s) => { const pg = part(box(0.7, 0.06, 0.92), M.paper, s * 0.37, 0.04, 0, 0.02, nb); pg.rotation.z = -s * 0.06; for (let i = 0; i < 3; i++) part(box(0.5, 0.01, 0.03), toon(0x6ec6ff), s * 0.37, 0.08, -0.25 + i * 0.22, 0, nb); });
  const q = part(sph(0.12, 10, 8), M.white, 0.75, 0.32, 0.25, 0.02, nb); q.scale.set(0.5, 2.4, 0.2); q.rotation.z = -0.6;
  addBox(id, rw(id, 2.6), -0.9, 1.3, 0.75);
  inter({ area: id, x: rw(id, 2.6), z: 0.2, r: 1.8, y: 2.2, obj: nb, hopH: 0.25, label: () => '📓 Caderno de Ideias', act: openCaderno });
  // baú de conquistas
  const chest = new T.Group(); chest.position.set(4.6, 0, 2.3); chest.rotation.y = -0.55; g.add(chest);
  part(box(1.7, 0.9, 1.1), toon(0xb5651d), 0, 0.45, 0, 0.06, chest);
  [-0.55, 0.55].forEach((x) => part(box(0.14, 0.92, 1.14), M.gold, x, 0.45, 0, 0, chest));
  const lid = new T.Group(); lid.position.set(0, 0.9, -0.55); chest.add(lid);
  part(box(1.7, 0.36, 1.1), toon(0xc8752a), 0, 0.18, 0.55, 0.05, lid);
  part(box(0.3, 0.3, 0.1), M.gold, 0, 0.0, 1.12, 0.02, lid);
  ROOM_FX.chest = chest; ROOM_FX.chestLid = lid;
  addBox(id, rw(id, 4.6), 2.3, 0.95, 0.65, -0.55);
  inter({ area: id, x: rw(id, 4.6) - 0.6, z: 3.2, r: 1.8, y: 1.9, obj: chest, hopH: 0.2, label: () => '🏆 Baú de Conquistas', act: openBau });
  craftBench(room, -4.4, 2.6, 'pena');
}

// ---------- Biblioteca (inicial) ----------
function roomBiblio(room) {
  const g = room.g, id = 'biblioteca';
  bookcase(room, -4.6, -4.55, 2.8, 4.2, true); bookcase(room, -1.6, -4.55, 2.4, 4.2, false); bookcase(room, 4.7, -4.55, 2.6, 4.2, true);
  const gl = new T.Group(); gl.position.set(2.6, 0, -1.6); g.add(gl);
  part(cyl(0.5, 0.6, 0.12, 14), M.woodDark, 0, 0.06, 0, 0.03, gl); part(cyl(0.07, 0.09, 1.3, 8), M.wood, 0, 0.7, 0, 0.03, gl);
  const gc = mkCanvas(512, 256), gg = gc.getContext('2d'); gg.fillStyle = '#4aa8ff'; gg.fillRect(0, 0, 512, 256); const R = seeded(12); gg.lineWidth = 5; gg.strokeStyle = INK;
  for (let i = 0; i < 9; i++) { const P2 = painter(gg); gg.lineWidth = 5; P2.blob(R() * 512, 40 + R() * 176, 26 + R() * 44, 18 + R() * 30, i + 3, ['#7ed36b', '#5cc05a', '#f3d48b'][i % 3], 0.3); }
  const globe = new T.Mesh(sph(0.75, 24, 16), new T.MeshToonMaterial({ map: canvasTex(gc), gradientMap: GRAD })); addOutline(globe, 0.05); globe.position.y = 1.95; globe.rotation.z = 0.35; gl.add(globe);
  const mer = part(tor(0.85, 0.04, 6, 32), toon(0xffc928), 0, 1.95, 0, 0.015, gl); mer.rotation.y = Math.PI / 2;
  ROOM_FX.globe = globe;
  addCircle(id, rw(id, 2.6), -1.6, 0.7);
  inter({ area: id, x: rw(id, 2.6), z: -0.5, r: 1.6, y: 3.1, obj: gl, hopH: 0.15, label: () => '🌍 Girar o globo', act: () => { ROOM_FX.globeV += 9; Snd.whoosh(); toast('O globo gira, gira… Onde sua história vai acontecer?'); } });
  const ch = armchair(g, -3.7, 0.8, 0.6, 0x3a86ff); addBox(id, rw(id, -3.7), 0.8, 0.85, 0.8, 0.6);
  inter({ area: id, x: rw(id, -3.7) + Math.sin(0.6) * 1.1, z: 0.8 + Math.cos(0.6) * 1.1, r: 1.5, y: 2.2, obj: ch, hopH: 0.12, label: () => (P.sitting ? null : '🪑 Sentar e ler'), act: () => sitAt(rw(id, -3.7) + Math.sin(0.6) * 0.15, 0.8 + Math.cos(0.6) * 0.15, 0.75, 1) });
  const lamp = new T.Group(); lamp.position.set(-5.4, 0, -0.4); g.add(lamp); part(cyl(0.05, 0.05, 2.4, 6), M.ink, 0, 1.2, 0, 0.02, lamp); part(cone(0.45, 0.5, 12), toon(0xffd23f), 0, 2.5, 0, 0.04, lamp);
  missaoStand(room, 0.6, -2.4);
  seasonalDecor(g, 5.6, 0, 1.6);
}

// ---------- Ateliê de Desenho (inicial) ----------
function roomAtelie(room) {
  const g = room.g, id = 'atelie';
  // cavalete com o desenho da criança
  const ea = new T.Group(); ea.position.set(-1.6, 0, -2.2); g.add(ea);
  [[-0.55, 0.2], [0.55, -0.2]].forEach(([x, r]) => { const l = part(box(0.12, 3.0, 0.12), M.wood, x, 1.5, 0, 0.03, ea); l.rotation.z = r; });
  const back = part(box(0.12, 2.8, 0.12), M.wood, 0, 1.35, -0.55, 0.03, ea); back.rotation.x = -0.35;
  part(box(1.6, 0.1, 0.3), M.wood, 0, 1.0, 0.12, 0.03, ea);
  part(box(1.6, 1.8, 0.08), M.paper, 0, 2.0, 0.1, 0.04, ea);
  ROOM_FX.easelMat = new T.MeshBasicMaterial({ color: 0xffffff, transparent: true, alphaTest: 0.1 });
  const dr = new T.Mesh(new T.PlaneGeometry(1.35, 1.6), ROOM_FX.easelMat); dr.position.set(0, 2.0, 0.15); ea.add(dr);
  addCircle(id, rw(id, -1.6), -2.2, 0.7);
  inter({ area: id, x: rw(id, -1.6), z: -1.1, r: 1.6, y: 3.3, obj: ea, hopH: 0.12, label: () => '🎨 Pegar um Desenho', act: () => { const w = cooldown('desenho', 12); if (w) { toast(`O cavalete está secando a tinta… volte em ${w}s.`); Snd.nope(); return; } addItem('desenho'); Snd.pickup(); } });
  // varal da turma
  const pts = [new T.Vector3(-6.4, 4.3, -4.8), new T.Vector3(0, 3.9, -4.8), new T.Vector3(6.4, 4.3, -4.8)];
  const tube = new T.Mesh(new T.TubeGeometry(new T.CatmullRomCurve3(pts), 20, 0.03, 4), OUTLINE.clone()); tube.material.side = T.FrontSide; g.add(tube);
  for (let i = 0; i < 8; i++) {
    const x = -5.25 + i * 1.5, y = 3.15 + Math.abs(x) * 0.06, fr = new T.Group(); fr.position.set(x, y, -4.75); fr.rotation.z = (i % 2 ? 1 : -1) * 0.04; g.add(fr);
    part(box(1.1, 1.3, 0.05), M.paper, 0, 0, 0, 0.03, fr);
    const m = new T.MeshBasicMaterial({ color: 0xffffff, transparent: true, alphaTest: 0.1 }); const pl = new T.Mesh(new T.PlaneGeometry(0.95, 1.15), m); pl.position.z = 0.04; fr.add(pl);
    part(box(0.08, 0.3, 0.08), toon([0xff4f6d, 0x3a86ff, 0xffd23f][i % 3]), 0, 0.7, 0.03, 0.02, fr);
    ROOM_FX.varal.push({ m, fr });
  }
  inter({ area: id, x: rw(id, 0), z: -3.8, r: 1.4, y: 4.6, label: () => '🧵 Varal da turma', act: openVaral });
  // lápis que tocam notas
  const notes = ['Dó', 'Ré', 'Mi', 'Sol', 'Lá', 'Dó agudo'], cols = [0xff4f6d, 0xff8a3c, 0xffd23f, 0x4fae4c, 0x3a86ff, 0xa77bff];
  for (let i = 0; i < 6; i++) {
    const p = new T.Group(); p.position.set(1.4 + i * 0.85, 0, 2.0); g.add(p);
    part(cyl(0.24, 0.24, 1.7, 6), toon(cols[i]), 0, 1.15, 0, 0.04, p);
    part(cone(0.24, 0.45, 6), toon(0xf3c99a), 0, 2.22, 0, 0.03, p); part(cone(0.08, 0.15, 6), toon(cols[i]), 0, 2.4, 0, 0.015, p);
    part(cyl(0.25, 0.25, 0.25, 12), toon(0xc9ced8), 0, 0.2, 0, 0.02, p);
    addCircle(id, rw(id, 1.4 + i * 0.85), 2.0, 0.3);
    inter({ area: id, x: rw(id, 1.4 + i * 0.85), z: 2.65, r: 0.55, y: 2.9, obj: p, hopH: 0.35, label: () => `🎵 Tocar ${notes[i]}`, act: () => { Snd.note(i); it_hop(p); } });
  }
  // quadro de nomes
  const qb = new T.Group(); qb.position.set(6.95, 2.4, -0.8); qb.rotation.y = -Math.PI / 2; g.add(qb);
  part(box(2.6, 1.6, 0.1), M.wood, 0, 0, 0, 0.04, qb);
  const cc = mkCanvas(512, 300); ROOM_FX.chalkCanvas = cc; ROOM_FX.chalk = canvasTex(cc); drawChalk();
  const board = new T.Mesh(new T.PlaneGeometry(2.4, 1.4), new T.MeshBasicMaterial({ map: ROOM_FX.chalk })); board.position.z = 0.06; qb.add(board);
  inter({ area: id, x: rw(id, 6.0), z: -0.8, r: 1.4, y: 3.5, label: () => '✏️ Quadro de nomes', act: openQuadro });
  // potes de tinta
  const sh = new T.Group(); sh.position.set(-5.9, 0, -3.6); g.add(sh);
  part(box(1.4, 1.2, 0.9), M.wood, 0, 0.6, 0, 0.05, sh);
  const jars = new T.Group(); sh.add(jars);
  [0xff4f6d, 0x3a86ff, 0xffd23f, 0x4fae4c].forEach((c, i) => { part(cyl(0.16, 0.16, 0.3, 10), toon(0xe8f6ff), -0.48 + i * 0.32, 1.35, 0, 0.02, jars); part(cyl(0.14, 0.14, 0.2, 10), toon(c), -0.48 + i * 0.32, 1.3, 0, 0, jars); });
  addBox(id, rw(id, -5.9), -3.6, 0.75, 0.5);
  inter({ area: id, x: rw(id, -5.5), z: -2.6, r: 1.4, y: 2.2, obj: jars, label: () => '🖌 Pegar Tinta', act: () => { const w = cooldown('tinta', 15); if (w) { toast(`Os potes estão sendo enchidos… volte em ${w}s.`); Snd.nope(); return; } addItem('tinta'); Snd.pickup(); } });
  craftBench(room, -4.4, 2.6, 'atelie');
  missaoStand(room, 3.0, -3.3);
  seasonalDecor(g, -6.4, 1.2, -3.6);
}

// ---------- Gráfica (inicial) ----------
function roomGrafica(room) {
  const g = room.g, id = 'grafica';
  const pr = new T.Group(); pr.position.set(-2.8, 0, -3.4); g.add(pr);
  part(box(3.2, 1.9, 1.6), toon(0x3aa6a0), 0, 0.95, 0, 0.07, pr);
  part(box(2.6, 0.5, 1.2), toon(0x2e8a85), 0, 2.15, -0.1, 0.05, pr);
  [0.35, -0.05].forEach((y, i) => { const r = part(cyl(0.18, 0.18, 2.4, 12), toon(i ? 0x7a6b85 : 0xc9ced8), 0, 1.4 + y, 0.85, 0.03, pr); r.rotation.z = Math.PI / 2; ROOM_FX.rollers.push(r); });
  part(box(1.8, 0.06, 0.9), toon(0xd2c6b6), 0, 0.92, 1.15, 0.03, pr);
  const sheet = part(box(1.2, 0.03, 0.9), M.paper, 0, 0.98, 0.7, 0.02, pr); sheet.visible = false; ROOM_FX.sheet = sheet;
  const lv = new T.Group(); lv.position.set(1.7, 1.5, 0.2); pr.add(lv);
  part(cyl(0.07, 0.07, 1.2, 8), M.ink, 0, 0.6, 0, 0.02, lv); part(sph(0.18, 10, 8), toon(0xe5383b), 0, 1.25, 0, 0.03, lv); lv.rotation.z = -0.25; ROOM_FX.lever = lv;
  part(cyl(0.2, 0.2, 0.2, 10), M.ink, 1.65, 1.5, 0.2, 0.02, pr).rotation.z = Math.PI / 2;
  addBox(id, rw(id, -2.8), -3.4, 1.7, 0.85);
  inter({ area: id, x: rw(id, -1.2), z: -2.0, r: 1.8, y: 3.4, label: () => '🖨 Puxar a alavanca', act: pullLever });
  // caixas
  const bx = new T.Group(); bx.position.set(4.8, 0, -3.7); g.add(bx);
  [[0, 0.55, 0, 1.4, 1.1], [0.15, 1.55, 0.05, 1.1, 0.9], [-1.1, 0.4, 0.4, 0.8, 0.8]].forEach(([x, y, z, w, hh], i) => { const b = part(box(w, hh, w * 0.8), toon(0xc9955a), x, y, z, 0.05, bx); b.rotation.y = i * 0.2; part(box(w * 0.5, 0.06, 0.02), toon(0x8a5a33), x, y + hh * 0.2, z + w * 0.41, 0, bx); });
  addBox(id, rw(id, 4.6), -3.6, 1.3, 0.75);
  inter({ area: id, x: rw(id, 4.4), z: -2.4, r: 1.6, y: 2.8, obj: bx, hopH: 0.15, label: () => '📦 Caixas de capas', act: () => { if (!S.selos.autor) { say(['Estas caixas guardam capas em branco para livros. Elas vão servir quando você ganhar o selo de Autor(a) na Casa da Pena!'], null, 'Gráfica'); return; } const w = cooldown('capa', 20); if (w) { toast(`As capas estão sendo cortadas… volte em ${w}s.`); Snd.nope(); return; } addItem('capa'); Snd.pickup(); } });
  // livro que folheia
  const lec = new T.Group(); lec.position.set(1.5, 0, -0.6); g.add(lec);
  part(box(0.3, 1.1, 0.3), M.woodDark, 0, 0.55, 0, 0.03, lec);
  const top = new T.Group(); top.position.set(0, 1.2, 0); top.rotation.x = 0.35; lec.add(top);
  part(box(1.6, 0.1, 1.1), M.wood, 0, 0, 0, 0.04, top);
  part(box(0.72, 0.08, 0.95), toon(0x3a86ff), -0.37, 0.09, 0, 0.03, top); part(box(0.72, 0.08, 0.95), toon(0x3a86ff), 0.37, 0.09, 0, 0.03, top);
  part(box(0.68, 0.06, 0.9), M.paper, -0.36, 0.15, 0, 0.02, top);
  for (let i = 0; i < 4; i++) { const pv = new T.Group(); pv.position.set(0, 0.16 + i * 0.012, 0); top.add(pv); part(box(0.66, 0.02, 0.88), M.paper, 0.34, 0, 0, 0.015, pv); ROOM_FX.pages.push({ pv, t: -1 }); }
  addCircle(id, rw(id, 1.5), -0.6, 0.6);
  inter({ area: id, x: rw(id, 1.5), z: 0.5, r: 1.5, y: 2.4, label: () => '📖 Folhear o livro', act: () => { ROOM_FX.pages.forEach((p, i) => (p.t = -i * 0.18)); ROOM_FX.flipping = true; Snd.page(); setTimeout(() => Snd.page(), 250); setTimeout(() => Snd.page(), 500); } });
  craftBench(room, -4.4, 2.6, 'grafica');
  missaoStand(room, 4.8, 1.5);
  seasonalDecor(g, 6.2, 0, 3.4);
}

// ---------- Correio das Histórias (inicial) ----------
function roomCorreio(room) {
  const g = room.g, id = 'correio';
  const mb = new T.Group(); mb.position.set(-3.4, 0, -3.4); g.add(mb);
  part(cyl(0.6, 0.65, 1.9, 18), toon(0xe5383b), 0, 0.95, 0, 0.06, mb);
  const dome = part(new T.SphereGeometry(0.6, 18, 10, 0, Math.PI * 2, 0, Math.PI / 2), toon(0xe5383b), 0, 1.9, 0, 0.05, mb);
  part(box(0.6, 0.08, 0.1), M.ink, 0, 1.55, 0.6, 0, mb);
  part(box(0.5, 0.3, 0.05), toon(0xffd23f), 0, 1.15, 0.62, 0.02, mb);
  addCircle(id, rw(id, -3.4), -3.4, 0.8);
  inter({ area: id, x: rw(id, -3.4), z: -2.2, r: 1.6, y: 3.0, obj: mb, hopH: 0.2, label: () => `📮 Caixa de correio${S.cartas.some((c) => !c.lida) ? ' (nova!)' : ''}`, act: openCartas });
  const bf = new T.Group(); bf.position.set(3.4, 0, -3.8); g.add(bf);
  [-0.9, 0.9].forEach((x) => part(box(0.18, 3.0, 0.18), M.woodDark, x, 1.5, 0, 0.03, bf)); part(box(2.1, 0.2, 0.3), M.wood, 0, 3.0, 0, 0.04, bf);
  const bell = new T.Group(); bell.position.set(0, 2.9, 0); bf.add(bell);
  part(cyl(0.28, 0.55, 0.75, 16), M.gold, 0, -0.45, 0, 0.04, bell); part(tor(0.55, 0.06, 6, 24), M.gold, 0, -0.82, 0, 0.02, bell).rotation.x = Math.PI / 2; part(sph(0.12, 8, 6), M.ink, 0, -0.85, 0, 0.02, bell);
  ROOM_FX.bell = bell;
  addBox(id, rw(id, 3.4), -3.8, 1.05, 0.3);
  inter({ area: id, x: rw(id, 3.4), z: -2.6, r: 1.6, y: 3.6, label: () => '🔔 Tocar o sino', act: () => { ringBell(); Net.fx('sino'); } });
  const mu = new T.Group(); mu.position.set(0.3, 2.6, -4.92); g.add(mu);
  part(box(3.6, 2.2, 0.12), M.wood, 0, 0, 0, 0.05, mu);
  const mc = mkCanvas(720, 440); ROOM_FX.muralCanvas = mc; ROOM_FX.mural = canvasTex(mc); drawMural();
  const mp = new T.Mesh(new T.PlaneGeometry(3.4, 2.0), new T.MeshBasicMaterial({ map: ROOM_FX.mural })); mp.position.z = 0.07; mu.add(mp);
  inter({ area: id, x: rw(id, 0.3), z: -3.9, r: 1.5, y: 4.0, label: () => '📌 Mural da turma', act: openMural });
  const bk = new T.Group(); bk.position.set(5.2, 0, 1.6); g.add(bk);
  part(cyl(0.65, 0.5, 0.7, 14), toon(0xc9955a), 0, 0.35, 0, 0.05, bk); part(new T.TorusGeometry(0.5, 0.05, 6, 20, Math.PI), toon(0x8a5a33), 0, 0.7, 0, 0.02, bk);
  const goods = new T.Group(); bk.add(goods); [0xff4f6d, 0x38c6c0, 0xffd23f, 0xa77bff].forEach((c, i) => part(i % 2 ? cyl(0.14, 0.14, 0.05, 12) : tor(0.1, 0.04, 6, 14), toon(c), -0.25 + i * 0.17, 0.72, (i % 2) * 0.1, 0.015, goods));
  addCircle(id, rw(id, 5.2), 1.6, 0.7);
  inter({ area: id, x: rw(id, 5.2), z: 2.6, r: 1.5, y: 1.8, obj: bk, hopH: 0.2, label: () => '🧺 Cesto de achados', act: () => { const w = cooldown('achados', 18); if (w) { toast(`O cesto está vazio agora… volte em ${w}s.`); Snd.nope(); return; } const it = Math.random() < 0.5 ? 'fita' : 'botao'; addItem(it); Snd.pickup(); } });
  missaoStand(room, -4.6, 1.4);
  seasonalDecor(g, -6.3, 0, 3.6);
}

// ---------- texturas que mudam ----------
function drawClockFace() {
  const c = ROOM_FX.clockCanvas; if (!c) return; const g = c.getContext('2d'); g.fillStyle = '#fff8ec'; g.fillRect(0, 0, 256, 256);
  g.fillStyle = INK; g.font = '800 40px Grandstander, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  [[12, 0], [3, 1], [6, 2], [9, 3]].forEach(([n, i]) => { const a = (i / 4) * Math.PI * 2 - Math.PI / 2; g.fillText(String(n), 128 + Math.cos(a) * 92, 128 + Math.sin(a) * 92); });
  for (let i = 0; i < 12; i++) { if (i % 3 === 0) continue; const a = (i / 12) * Math.PI * 2; g.beginPath(); g.arc(128 + Math.cos(a) * 96, 128 + Math.sin(a) * 96, 5, 0, 7); g.fill(); }
  if (ROOM_FX.clockTex) ROOM_FX.clockTex.needsUpdate = true;
}
function drawChalk() {
  const c = ROOM_FX.chalkCanvas; if (!c) return; const g = c.getContext('2d'); g.fillStyle = '#2f5a45'; g.fillRect(0, 0, 512, 300);
  g.fillStyle = 'rgba(255,255,255,.92)'; g.textAlign = 'center'; g.font = '800 30px Grandstander, sans-serif'; g.fillText('Nome do meu personagem:', 256, 70);
  g.font = '900 56px Grandstander, sans-serif'; let txt = S.nomePers || '_____'; let s = 56; while (g.measureText(txt).width > 470 && s > 24) { s -= 4; g.font = `900 ${s}px Grandstander, sans-serif`; } g.fillText(txt, 256, 170);
  g.strokeStyle = 'rgba(255,255,255,.5)'; g.lineWidth = 4; g.beginPath(); g.moveTo(90, 215); g.lineTo(420, 215); g.stroke();
  if (ROOM_FX.chalk) ROOM_FX.chalk.needsUpdate = true;
}
function drawMural() {
  const c = ROOM_FX.muralCanvas; if (!c) return; const g = c.getContext('2d'); g.fillStyle = '#c9955a'; g.fillRect(0, 0, 720, 440);
  const R = seeded(3); g.fillStyle = 'rgba(120,70,30,.25)'; for (let i = 0; i < 160; i++) { g.beginPath(); g.arc(R() * 720, R() * 440, 2 + R() * 2, 0, 7); g.fill(); }
  const posts = muralPosts().slice(0, 9);
  if (!posts.length) { g.fillStyle = '#fff8ec'; g.font = '800 34px Grandstander, sans-serif'; g.textAlign = 'center'; g.fillText('Mural da turma', 360, 190); g.font = '700 26px Andika, sans-serif'; g.fillText('Cole a primeira figurinha!', 360, 240); }
  posts.forEach((p, i) => {
    const x = 20 + (i % 3) * 233, y = 18 + Math.floor(i / 3) * 140, rot = (R() - 0.5) * 0.1;
    g.save(); g.translate(x + 105, y + 60); g.rotate(rot); g.fillStyle = ['#fff3a0', '#ffd6e3', '#d3ecff', '#dff5d1'][i % 4]; g.strokeStyle = INK; g.lineWidth = 4; g.beginPath(); g.roundRect(-100, -56, 200, 116, 12); g.fill(); g.stroke();
    g.fillStyle = INK; g.textAlign = 'center'; g.font = '800 22px Grandstander, sans-serif'; wrapText(g, FIGURINHAS[p.fig] || '', 0, -16, 180, 26);
    g.font = '700 18px Andika, sans-serif'; g.fillStyle = '#4a3d57'; g.fillText('— ' + String(p.nome || 'Colega').slice(0, 16), 0, 40);
    g.fillStyle = '#e5383b'; g.beginPath(); g.arc(0, -56, 8, 0, 7); g.fill(); g.stroke(); g.restore();
  });
  if (ROOM_FX.mural) ROOM_FX.mural.needsUpdate = true;
}
function wrapText(g, text, x, y, maxW, lh) { const words = String(text).split(' '); let line = '', lines = []; for (const w of words) { const t = line ? line + ' ' + w : w; if (g.measureText(t).width > maxW && line) { lines.push(line); line = w; } else line = t; } lines.push(line); lines.slice(0, 2).forEach((l, i) => g.fillText(l, x, y + i * lh - ((Math.min(lines.length, 2) - 1) * lh) / 2)); }
