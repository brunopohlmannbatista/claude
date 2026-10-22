// ============================================================
// Jogo: jogador, câmera, interações, Pena, tutorial, painéis, crafting, decoração, salas
// ============================================================
const P = { pos: null, vel: null, dir: null, facing: 1, bb: null, sitting: null, target: null, autoAct: null, walkT: 0, crown: null, stuck: 0, lastPos: null, stepPh: 0 };
const camFocus = { x: 0, z: 0 };
let CAM_POS, CAM_LOOK, _ct, _cl, _v, RAY, GROUND;
const CAM = { zoom: 1 };
const ANIMS = [];
function anim(fn) { ANIMS.push(fn); }
function runAnims(dt) { for (let i = ANIMS.length - 1; i >= 0; i--) { let done = true; try { done = ANIMS[i](dt); } catch (e) { console.warn(e); } if (done) ANIMS.splice(i, 1); } }
function it_hop(obj, hh = 0.3) { const b = obj.userData.baseY ?? obj.position.y; obj.userData.baseY = b; let k = 0; anim((dt) => { k += dt / 0.35; obj.position.y = b + Math.sin(Math.min(1, k) * Math.PI) * hh; if (k >= 1) { obj.position.y = b; return true; } }); }

// ---------- interações ----------
const INTERS = [];
function inter(o) { o.area = o.area || 'vila'; o.r = o.r || 1.8; if (o.obj) o.obj.userData.baseY = o.obj.position.y; INTERS.push(o); return o; }
function updateInters(dt) {
  let best = null, bs = 1e9;
  const free = GAME.started && !GAME.lock && !GAME.placing;
  for (const it of INTERS) {
    if (it.dead || it.area !== GAME.area) continue;
    const d = Math.hypot(it.x - P.pos.x, it.z - P.pos.z);
    if (it.obj) {
      const near = d < 3.0 && GAME.started;
      if (near && !it.near) it.hop = 0;
      it.near = near;
      if (it.hop !== undefined && it.hop < 0.42) { it.hop += dt; const k = Math.sin(Math.min(1, it.hop / 0.42) * Math.PI); it.obj.position.y = it.obj.userData.baseY + k * (it.hopH || 0.3); }
    }
    if (!free || d > it.r) continue;
    const lab = it.label(); if (!lab) continue;
    const sc = d + ((it.prio || 0) < 0 ? 1.2 : 0);
    if (sc < bs) { bs = sc; best = it; best._lab = lab; }
  }
  GAME.cur = best;
  const act = $('#act');
  if (best || P.sitting) { act.hidden = false; $('#actTx').textContent = best ? best._lab : 'Levantar'; }
  else act.hidden = true;
}
function doInteract(it) { if (!it || it.dead) return; Snd.ensure(); P.target = null; P.autoAct = null; it.act(); }

// ---------- rótulos ----------
const FLOATS = [];
function worldToScreen(x, y, z) { _v.set(x, y, z).project(camera); return { x: (_v.x * 0.5 + 0.5) * innerWidth, y: (-_v.y * 0.5 + 0.5) * innerHeight, ok: _v.z < 1 && _v.z > -1 }; }
function placeLabel(el, x, y, z) { const s = worldToScreen(x, y, z); if (!s.ok) { el.style.display = 'none'; return; } el.style.display = ''; el.style.transform = `translate(${s.x.toFixed(1)}px,${s.y.toFixed(1)}px) translate(-50%,-100%)`; }
let PROMPT_EL, ME_LBL;
function updateLabels() {
  const cur = GAME.cur;
  if (cur && !GAME.lock) { PROMPT_EL.hidden = false; PROMPT_EL.firstChild.textContent = cur._lab; placeLabel(PROMPT_EL, cur.x, cur.y || 2.4, cur.z); } else PROMPT_EL.hidden = true;
  if (GAME.started && P.bb) { ME_LBL.hidden = false; placeLabel(ME_LBL, P.pos.x, P.bb.root.position.y + P.bb.h + 0.35, P.pos.z - 0.4); } else ME_LBL.hidden = true;
  for (let i = FLOATS.length - 1; i >= 0; i--) { const f = FLOATS[i]; f.t += 1 / 60; placeLabel(f.el, P.pos.x, 2.6 + f.t * 1.6 + f.o, P.pos.z); f.el.style.opacity = String(Math.max(0, 1 - f.t / 1.3)); if (f.t > 1.3) { f.el.remove(); FLOATS.splice(i, 1); } }
}
function floatText(txt, icon) { const el = h('div', { class: 'lbl float' }, icon ? h('img', { src: icon, alt: '' }) : null, txt); $('#labels').append(el); FLOATS.push({ el, t: 0, o: FLOATS.length * 0.5 }); }
function toast(msg, icon) { const box = $('#toasts'); while (box.children.length > 2) box.firstChild.remove(); const el = h('div', { class: 'toast' }, icon ? h('img', { src: icon, alt: '' }) : null, h('span', {}, msg)); box.append(el); setTimeout(() => { el.style.transition = 'opacity .4s'; el.style.opacity = '0'; setTimeout(() => el.remove(), 420); }, 3400); }

// ---------- confete e brilhos ----------
const CONF = { parts: [], run: false };
function confetti(x, y, n = 120) {
  const c = $('#fxc'); c.width = innerWidth * (devicePixelRatio || 1); c.height = innerHeight * (devicePixelRatio || 1);
  const cols = ['#ffc93c', '#6ec6ff', '#ff6f91', '#78cf62', '#8f72ff', '#ffffff'];
  for (let i = 0; i < n; i++) { const a = rnd(Math.PI * 2), sp = rnd(4, 13); CONF.parts.push({ x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp - rnd(4, 9), r: rnd(6.28), vr: rnd(-0.3, 0.3), w: rnd(6, 12), h: rnd(4, 8), c: pick(cols), life: rnd(1.6, 2.6) }); }
  if (!CONF.run) { CONF.run = true; requestAnimationFrame(confStep); }
}
function confettiAtEl(el) { const r = el.getBoundingClientRect(); confetti(r.left + r.width / 2, r.top + r.height / 2, 70); }
let confLast = 0;
function confStep(ts) {
  const cdt = confLast ? Math.min(0.05, (ts - confLast) / 1000) : 1 / 60; confLast = ts;
  const c = $('#fxc'), g = c.getContext('2d'), k = devicePixelRatio || 1; g.setTransform(k, 0, 0, k, 0, 0); g.clearRect(0, 0, innerWidth, innerHeight);
  for (let i = CONF.parts.length - 1; i >= 0; i--) { const p = CONF.parts[i]; const f = cdt * 60; p.vy += 0.35 * f; p.vx *= Math.pow(0.985, f); p.x += p.vx * f; p.y += p.vy * f; p.r += p.vr * f; p.life -= cdt; if (p.life <= 0 || p.y > innerHeight + 30) { CONF.parts.splice(i, 1); continue; } g.save(); g.translate(p.x, p.y); g.rotate(p.r); g.fillStyle = p.c; g.strokeStyle = INK; g.lineWidth = 1.5; g.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); g.strokeRect(-p.w / 2, -p.h / 2, p.w, p.h); g.restore(); }
  if (CONF.parts.length) requestAnimationFrame(confStep); else { CONF.run = false; confLast = 0; g.clearRect(0, 0, innerWidth, innerHeight); }
}
function burst(x, y, z, color = 0xfff6a0) {
  for (let i = 0; i < 12; i++) {
    const s = starMesh(0.16, color); s.position.set(x, y, z); scene.add(s); const a = (i / 12) * Math.PI * 2, v = new T.Vector3(Math.cos(a) * 2.6, rnd(1.5, 3.5), Math.sin(a) * 1.4); let k = 0;
    anim((dt) => { k += dt; s.position.addScaledVector(v, dt); v.y -= dt * 5; s.rotation.z += dt * 6; s.lookAt(camera.position); s.scale.setScalar(Math.max(0.01, 1 - k / 0.8)); if (k > 0.8) { scene.remove(s); return true; } });
  }
}

// ---------- jogador ----------
async function playerCanvas() {
  if (S.charKey === 'img' && DRAWING) { try { return await loadImgCanvas(DRAWING); } catch (e) {} }
  return sampleSticker(SAMPLES[S.charKey] ? S.charKey : 'lia');
}
function updateCrown() { if (P.crown) { P.crown.visible = S.wearing === 'coroa' && (S.inv.coroa || 0) > 0; P.crown.position.set(0, P.bb.h * 0.93 - 0.08, -P.bb.h * 0.35 + 0.05); } }
function sitAt(x, z, y, facing) { P.sitting = { x, z, y }; P.target = null; P.autoAct = null; P.pos.set(x, 0, z); P.vel.set(0, 0, 0); P.facing = facing; Snd.pop(); toast('Ande ou toque em Levantar para sair.'); }
function standUp() { if (!P.sitting) return; P.sitting = null; P.pos.z += 0.9; resolveColl(GAME.area, P.pos, 0.45); Snd.pop(); }
const KEYS = {};
const PTR = { down: false, sx: 0, sy: 0, id: null, joy: false, jx: 0, jz: 0, t0: 0 };
function updatePlayer(dt, t) {
  if (!P.bb || !GAME.started) return;
  let ix = 0, iz = 0;
  if (!GAME.lock) {
    if (KEYS.KeyA || KEYS.ArrowLeft) ix -= 1; if (KEYS.KeyD || KEYS.ArrowRight) ix += 1; if (KEYS.KeyW || KEYS.ArrowUp) iz -= 1; if (KEYS.KeyS || KEYS.ArrowDown) iz += 1;
    if (PTR.joy) { ix = PTR.jx; iz = PTR.jz; }
  }
  if (ix || iz) { P.target = null; P.autoAct = null; }
  else if (P.target && !GAME.lock) {
    const dx = P.target.x - P.pos.x, dz = P.target.z - P.pos.z, d = Math.hypot(dx, dz);
    const reach = P.autoAct ? Math.max(0.4, P.autoAct.r * 0.6) : 0.2;
    if (d < reach) { const a = P.autoAct; P.target = null; P.autoAct = null; if (a && Math.hypot(a.x - P.pos.x, a.z - P.pos.z) <= a.r) doInteract(a); }
    else { ix = dx / d; iz = dz / d; }
  }
  const len = Math.hypot(ix, iz); if (len > 1) { ix /= len; iz /= len; }
  if (P.sitting) { if (len > 0.1) standUp(); else { P.pos.set(P.sitting.x, 0, P.sitting.z); } }
  const sp = GAME.area === 'vila' ? 6.2 : 4.4, kk = 1 - Math.exp(-dt * 12);
  if (!P.sitting) {
    P.vel.x = lerp(P.vel.x, ix * sp, kk); P.vel.z = lerp(P.vel.z, iz * sp, kk);
    const ox = P.pos.x, oz = P.pos.z;
    P.pos.x += P.vel.x * dt; P.pos.z += P.vel.z * dt; resolveColl(GAME.area, P.pos, 0.45);
    const moved = Math.hypot(P.pos.x - ox, P.pos.z - oz);
    if (P.target && moved < sp * dt * 0.25) { P.stuck += dt; if (P.stuck > 0.5) { const a = P.autoAct; P.target = null; P.autoAct = null; P.stuck = 0; if (a && Math.hypot(a.x - P.pos.x, a.z - P.pos.z) <= a.r + 0.3) doInteract(a); } } else P.stuck = 0;
    if (len > 0.1) P.dir.set(ix, 0, iz).normalize();
  }
  const speed = Math.hypot(P.vel.x, P.vel.z), moving = speed > 0.6 && !P.sitting;
  if (Math.abs(P.vel.x) > 0.5) P.facing = P.vel.x > 0 ? 1 : -1;
  const bb = P.bb; bb.root.position.set(P.pos.x, 0, P.pos.z);
  bb.pivot.scale.x = lerp(bb.pivot.scale.x, P.facing, 1 - Math.exp(-dt * 14));
  if (moving) { P.walkT += dt * 11; const hop = Math.abs(Math.sin(P.walkT)); bb.pivot.position.y = hop * 0.17; bb.pivot.scale.y = 1 - (1 - hop) * 0.05; const ph = Math.floor(P.walkT / Math.PI); if (ph !== P.stepPh) { P.stepPh = ph; Snd.step(); } }
  else { bb.pivot.position.y = P.sitting ? P.sitting.y : 0; bb.pivot.scale.y = 1 + Math.sin(t * 2.2) * 0.015; }
  bb.sh.visible = !P.sitting;
}
function updateCamera(dt) { camTarget(_ct, _cl); const k = 1 - Math.exp(-dt * 5); CAM_POS.lerp(_ct, k); CAM_LOOK.lerp(_cl, k); camera.position.copy(CAM_POS); camera.lookAt(CAM_LOOK); }
function aspectZoom() { const a = innerWidth / innerHeight; return a < 1.25 ? Math.pow(clamp(1.25 / a, 1, 2.4), 0.55) : 1; }
function camTarget(out, look) {
  const az = aspectZoom();
  if (GAME.area === 'vila') { const z = CAM.zoom * az; out.set(P.pos.x, 17 * z, P.pos.z + 16.5 * z); look.set(P.pos.x, 0.9, P.pos.z); camFocus.x = P.pos.x; camFocus.z = P.pos.z; }
  else { const R = ROOMS[GAME.area], lx = R.ox + (P.pos.x - R.ox) * 0.35, lz = P.pos.z * 0.22 + 0.4; out.set(lx, 8.6 * az, lz + 11.4 * az); look.set(lx, 1.3, lz - 0.9); }
}
function snapCam() { camTarget(CAM_POS, CAM_LOOK); camera.position.copy(CAM_POS); camera.lookAt(CAM_LOOK); }

// ---------- áreas: entrar e sair das casas ----------
function setArea(a) {
  if (ROOMS[GAME.area]) ROOMS[GAME.area].g.visible = false;
  GAME.area = a; VILLAGE.group.visible = a === 'vila';
  if (ROOMS[a]) ROOMS[a].g.visible = true;
  if (a === 'vila') { const s = SEASONS[GAME.season]; scene.background.setHex(s.sky); scene.fog.color.setHex(s.sky); scene.fog.near = 48; scene.fog.far = 120; }
  else { scene.background.setHex(0x3a2b4a); scene.fog.color.setHex(0x3a2b4a); scene.fog.near = 80; scene.fog.far = 220; }
  S.area = a; save(); updatePenaArea(); Net.sendPresence(true);
}
function irisTo(fn) {
  GAME.lock = true; const ir = $('#iris'), s = worldToScreen(P.pos.x, 1, P.pos.z); ir.style.left = s.x + 'px'; ir.style.top = s.y + 'px'; ir.classList.add('shut'); Snd.whoosh();
  setTimeout(() => { fn(); requestAnimationFrame(() => { const s2 = worldToScreen(P.pos.x, 1, P.pos.z); ir.style.left = s2.x + 'px'; ir.style.top = s2.y + 'px'; ir.classList.remove('shut'); }); setTimeout(() => { GAME.lock = !!(GAME.dlg || GAME.panel); }, 380); }, 400);
}
function enterHouse(id) {
  if (GAME.panel) closePanel();
  if (id === 'pena' && S.tut < 4) { say(['A Casa da Pena ainda está fechada. Termine as missões da praça e a Pena abre a porta para você!'], null, 'Placa da porta'); return; }
  irisTo(() => { setArea(id); const R = ROOMS[id]; P.pos.set(R.ox, 0, 3.4); P.vel.set(0, 0, 0); P.target = null; P.sitting = null; snapCam(); Snd.door(); if (!S.visited[id]) { S.visited[id] = 1; save(); if (Object.keys(S.visited).length >= 5) setTimeout(() => award('explorador'), 900); } onEnterHouse(id); refreshQuest(); });
}
function exitHouse() { const id = GAME.area, H = HOUSES[id]; if (!H) return; irisTo(() => { setArea('vila'); P.pos.set(H.doorX, 0, H.doorZ); P.vel.set(0, 0, 0); P.sitting = null; snapCam(); Snd.door(); }); }
function onEnterHouse(id) {
  if (id === 'pena' && S.tut === 4) { S.tut = 5; save(); PENA.mode = 'inside'; updatePenaArea(); setTimeout(() => say([8, 9, 10], () => refreshQuest()), 450); }
  else if (id !== 'pena' && !S.flags['tour_' + id]) { S.flags['tour_' + id] = 1; save(); const msg = { biblioteca: 'A Biblioteca: gire o globo, leia as estantes e sente na poltrona.', atelie: 'O Ateliê: seu desenho está no cavalete! Toque os lápis gigantes e veja o varal da turma.', grafica: 'A Gráfica: puxe a alavanca da impressora e folheie o livro grande.', correio: 'O Correio: toque o sino, leia as cartas e cole figurinhas no mural.' }[id]; setTimeout(() => toast(msg), 500); }
  if (id !== 'pena' && S.selos.autor && !(S.missoes && S.missoes[id])) setTimeout(() => toast(`⭐ Missão da história aqui: ${MISSOES[id].nomeEl}! Procure a placa com "!".`), 1600);
}

// ---------- a Pena ----------
const PENA = { bb: null, pos: null, area: 'vila', mode: 'idle', path: [], facing: -1, inter: null, home: null, bubble: null, walkT: 0, wander: 0, wx: 0, wz: 0 };
function createPena() {
  PENA.bb = makeBillboard(drawPena(), 1.8); scene.add(PENA.bb.root);
  PENA.home = new T.Vector3(2.6, 0, 6.4); PENA.pos = PENA.home.clone(); PENA.wx = PENA.home.x; PENA.wz = PENA.home.z;
  const bc = bubbleCanvas('!'); PENA.bubble = makeBillboard(bc, 1.3); PENA.bubble.sh.visible = false; scene.add(PENA.bubble.root);
  PENA.inter = inter({ x: 0, z: 0, r: 2.3, y: 2.6, label: () => '💬 Falar com a Pena', act: talkPena });
  if (S.tut >= 4 && S.tut < 7) PENA.mode = 'inside';
}
function updatePenaArea() {
  if (!PENA.bb) return;
  if (PENA.mode === 'walk') return;
  let a;
  if (S.tut < 4) a = 'vila'; else if (S.tut < 7) a = 'pena'; else a = GAME.area === 'pena' ? 'pena' : 'vila';
  PENA.area = a;
  if (a === 'pena') { PENA.pos.copy(ROOMS.pena.perch); PENA.mode = 'inside'; } else { PENA.pos.set(PENA.home.x, 0, PENA.home.z); PENA.mode = 'idle'; }
}
function penaGoHome() {
  const H = HOUSES.pena; PENA.mode = 'walk';
  PENA.path = [{ x: 5.0, z: 1.5 }, { x: 3.8, z: -6.0 }, { x: 0.6, z: -10 }, { x: H.doorX, z: H.doorZ + 0.4 }];
}
function updatePena(dt, t) {
  if (!PENA.bb) return;
  const bb = PENA.bb, vis = PENA.area === GAME.area; bb.root.visible = vis;
  if (PENA.mode === 'walk') {
    const tg = PENA.path[0];
    if (tg) { const dx = tg.x - PENA.pos.x, dz = tg.z - PENA.pos.z, d = Math.hypot(dx, dz); if (d < 0.2) PENA.path.shift(); else { const s = Math.min(d, 3.6 * dt); PENA.pos.x += (dx / d) * s; PENA.pos.z += (dz / d) * s; if (Math.abs(dx) > 0.1) PENA.facing = dx > 0 ? 1 : -1; PENA.walkT += dt * 12; } }
    else { PENA.mode = 'inside'; PENA.area = 'pena'; PENA.pos.copy(ROOMS.pena.perch); Snd.door(); if (GAME.area === 'vila') toast('A Pena entrou em casa! Siga o "!" na porta amarela.'); }
  } else if (PENA.mode === 'idle' && GAME.area === 'vila') {
    PENA.wander -= dt;
    if (PENA.wander < 0) { PENA.wander = rnd(4, 8); const a = rnd(6.28); PENA.wx = PENA.home.x + Math.cos(a) * 1.4; PENA.wz = PENA.home.z + Math.sin(a) * 0.9; }
    const dx = PENA.wx - PENA.pos.x, dz = PENA.wz - PENA.pos.z, d = Math.hypot(dx, dz);
    if (d > 0.1 && !(GAME.dlg && GAME.dlg.who === 'Pena')) { const s = Math.min(d, 1.4 * dt); PENA.pos.x += (dx / d) * s; PENA.pos.z += (dz / d) * s; PENA.walkT += dt * 9; if (Math.abs(dx) > 0.05) PENA.facing = dx > 0 ? 1 : -1; }
  }
  if (vis && GAME.started && Math.hypot(P.pos.x - PENA.pos.x, P.pos.z - PENA.pos.z) < 4 && PENA.mode !== 'walk') PENA.facing = P.pos.x > PENA.pos.x ? 1 : -1;
  bb.root.position.copy(PENA.pos);
  bb.pivot.scale.x = lerp(bb.pivot.scale.x, PENA.facing, 1 - Math.exp(-dt * 12));
  const walking = PENA.mode === 'walk' || (PENA.mode === 'idle' && Math.hypot(PENA.wx - PENA.pos.x, PENA.wz - PENA.pos.z) > 0.1);
  bb.pivot.position.y = walking ? Math.abs(Math.sin(PENA.walkT)) * 0.2 : Math.max(0, Math.sin(t * 3.1)) * 0.06;
  bb.sh.visible = PENA.mode !== 'inside';
  const it = PENA.inter; it.area = PENA.mode === 'walk' ? '-' : PENA.area; it.x = PENA.pos.x; it.z = PENA.pos.z + (PENA.mode === 'inside' ? 1.4 : 0); it.y = PENA.pos.y + 2.5;
  const H = HOUSES.pena, showB = S.tut === 4 && GAME.area === 'vila' && PENA.mode !== 'walk';
  PENA.bubble.root.visible = showB; if (showB) PENA.bubble.root.position.set(H.doorX - H.nx * 0.4, 5.3 + Math.sin(t * 3) * 0.25, H.doorZ - H.nz * 0.4);
  if (S.tut === 0 && GAME.started && !GAME.lock && GAME.area === 'vila' && Math.hypot(P.pos.x - PENA.pos.x, P.pos.z - PENA.pos.z) < 3.8) penaIntro();
}
function penaIntro() {
  say([1, 2, 3, 4], () => { S.tut = 1; save(); refreshQuest(); checkTutorial(); });
}
function talkPena() {
  if (S.tut === 0) return penaIntro();
  const g3 = ['p1', 'p2', 'p3'].filter((k) => S.found[k]).length;
  const L = {
    1: [`Junte 3 flores 🌼 e 1 graveto pela praça, ${S.nome}. É só passar por cima!`],
    2: ['Abra o Livro de Receitas no botão 🔨 (ou tecla C) e crie a Guirlanda.'],
    3: ['Abra a Mochila 🎒, escolha a Guirlanda e toque em Colocar. Chegue pertinho de uma porta para pendurar!'],
    4: ['Me encontre na minha casa, a amarelinha de telhado vermelho!'],
    5: [`Faltam umas coisinhas: ${S.flags.idea ? '' : 'a ideia no Caderno, '}${escritaOk() ? '' : 'o título e a primeira frase (no Caderno), '}${S.flags.fogo ? '' : 'acender a lareira, '}${g3 >= 3 ? '' : `achar ${3 - g3} folha(s) dourada(s) aqui dentro, `}e depois o Baú!`.replace(', e depois', ' e depois')],
    6: ['O Baú de Conquistas está esperando por você!'],
  }[S.tut];
  if (L) return say(L);
  const pend = MISSAO_IDS.filter((id) => !(S.missoes && S.missoes[id]));
  if (pend.length && Math.random() < 0.6) { const id = pend[0]; return say([`A próxima missão da história está na ${HOUSES[id].nome}: ${MISSOES[id].nomeEl.toLowerCase()}. Procure a placa azul com "!" lá dentro!`]); }
  const v = Object.keys(S.visited).length;
  const pool = [
    `Seu álbum tem ${albumCount()} de ${Object.keys(ITEMS).length} figurinhas. Toque em 📒 Álbum para ver o que falta!`,
    `Você já visitou ${v} de 5 casas. ${v < 5 ? 'Visite todas e ganhe o selo de Explorador(a)!' : 'Você conhece a vila inteira!'}`,
    `Já achou ${goldCount()} de ${GOLD_SPOTS.length} folhas douradas escondidas. Elas brilham, mas gostam de se esconder atrás das coisas.`,
    `Estamos no ${SEASONS[GAME.season].nome}. Cada estação traz receitas novas no Livro de Receitas!`,
    'Plante uma semente com água num cantinho da vila e volte daqui a uns minutos: ela cresce!',
    'Na Gráfica você encaderna 5 Páginas Ilustradas num Mini-livro. Seu primeiro livro de verdade!',
    'Quando seus colegas da turma entram com o código deles, vocês se encontram aqui na vila.',
    'O Baú da Turma, aqui na praça, junta doações de todo mundo para montar o Arco da Turma.',
    'Dica de autora: ' + pick(DICAS),
  ];
  say([pick(pool)]);
}

// ---------- diálogo ----------
function say(lines, done, who = 'Pena') {
  if (!lines || !lines.length) { done && done(); return; }
  if (GAME.dlg) { const prev = GAME.dlg; prev.lines.push(...lines); const pd = prev.done; prev.done = () => { pd && pd(); done && done(); }; return; }
  GAME.dlg = { lines: lines.slice(), i: 0, done, who, typing: 0, full: '' }; GAME.lock = true;
  $('#dWho').textContent = who; const por = $('#dPor'); por.innerHTML = '';
  if (who === 'Pena') { const c = drawPena(SEASONS[GAME.season].scarf, !!SEASONS[GAME.season].stripes); por.append(c); por.style.background = 'var(--sky)'; }
  else { por.append(h('img', { src: iconURL('ideia'), alt: '', style: 'width:70px;margin:auto' })); por.style.background = 'var(--paper-2)'; }
  $('#dialog').hidden = false; showLine();
}
function showLine() {
  const d = GAME.dlg, raw = d.lines[d.i], txt = falaTexto(raw), el = $('#dTxt'); el.textContent = ''; let n = 0; clearInterval(d.typing); d.full = txt; d.voz = typeof raw === 'number' ? raw : 0;
  d.typing = setInterval(() => { n += 2; el.textContent = txt.slice(0, n); if (n % 8 === 0) Snd.tone(880 + Math.random() * 260, 0.03, 'triangle', 0.025); if (n >= txt.length) { clearInterval(d.typing); d.typing = 0; } }, 22);
  if (d.voz) { try { speechSynthesis.cancel(); } catch (e) {} Voz.play(d.voz); } else { Voz.stop(); speak(txt); }
}
function advance() {
  const d = GAME.dlg; if (!d) return; Snd.ensure();
  if (d.typing) { clearInterval(d.typing); d.typing = 0; $('#dTxt').textContent = d.full; return; }
  d.i++;
  if (d.i >= d.lines.length) { $('#dialog').hidden = true; GAME.dlg = null; GAME.dlgClosed = performance.now(); GAME.lock = !!GAME.panel; try { speechSynthesis.cancel(); } catch (e) {} d.done && d.done(); checkTutorial(); }
  else showLine();
}
function speak(txt) {
  if (!S.voz || !window.speechSynthesis) return;
  try { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(txt.replace(/\p{Extended_Pictographic}/gu, '').replace(/\(a\)/g, '')); u.lang = 'pt-BR'; u.rate = 1.0; u.pitch = 1.15; const v = speechSynthesis.getVoices().find((x) => /pt(-|_)BR/i.test(x.lang)); if (v) u.voice = v; speechSynthesis.speak(u); } catch (e) {}
}

// ---------- tutorial e missões ----------
function tutTasksDone() { return !!S.flags.idea && escritaOk() && !!S.flags.fogo && ['p1', 'p2', 'p3'].every((k) => S.found[k]); }
function checkTutorial() {
  if (!GAME.started || GAME.dlg) return;
  if (S.tut === 1 && (S.inv.flor || 0) >= 3 && (S.inv.graveto || 0) >= 1) { S.tut = 2; save(); checkDiscoveries(true); S.flags.rec_guirlanda = 1; say([5], () => refreshQuest()); }
  if (S.tut === 5 && tutTasksDone()) { S.tut = 6; save(); Srv.agora(); say([12]); }
  refreshQuest();
}
function questData() {
  const inv = (k) => S.inv[k] || 0;
  switch (S.tut) {
    case 0: return ['Chegada na Vila', [['Siga o caminho e fale com a Pena, perto da fonte', 0]]];
    case 1: return ['Materiais da praça', [[`Flores 🌼 ${Math.min(inv('flor'), 3)}/3`, inv('flor') >= 3], [`Graveto ${Math.min(inv('graveto'), 1)}/1`, inv('graveto') >= 1]]];
    case 2: return ['Sua primeira criação', [['Abra as Receitas (🔨 ou C)', 0], ['Crie uma Guirlanda', 0]]];
    case 3: return ['Decore uma porta', [['Mochila 🎒 → Guirlanda → Colocar', 0], ['Pendure pertinho da porta de uma casa', 0]]];
    case 4: return ['A surpresa da Pena', [['Entre na Casa da Pena, a amarela com "!"', 0]]];
    case 5: case 6: { const g = ['p1', 'p2', 'p3'].filter((k) => S.found[k]).length; return ['Tarefas da Casa da Pena', [['Guardar uma ideia no Caderno de Ideias', !!S.flags.idea], ['Escrever o título e a primeira frase (no Caderno)', escritaOk()], ['Acender a lareira', !!S.flags.fogo], [`Achar folhas douradas aqui dentro ${g}/3`, g >= 3], ['Abrir o Baú de Conquistas', 0]]]; }
    default: {
      if (missoesFeitas() < 4) { const m = (id) => !!(S.missoes && S.missoes[id]); return ['Missões da história', [['Biblioteca: quem é o personagem', m('biblioteca')], ['Ateliê: onde a história acontece', m('atelie')], ['Gráfica: o problema', m('grafica')], ['Correio: o final', m('correio')]]]; } const v = Object.keys(S.visited).length, c = S.crafts || 0; return ['Explore a vila', [[`Visitar as 5 casas ${Math.min(v, 5)}/5`, v >= 5], [`Folhas douradas ${goldCount()}/${GOLD_SPOTS.length}`, goldCount() >= GOLD_SPOTS.length], [`Criar coisas ${Math.min(c, 5)}/5`, c >= 5], ['Encadernar um Mini-livro na Gráfica', !!S.selos.livro], [`Álbum ${albumCount()}/${Object.keys(ITEMS).length}`, albumCount() >= Object.keys(ITEMS).length]]]; }
  }
}
function refreshQuest() {
  if (!$('#qTitle')) return;
  const q = questData(); $('#qEyebrow').textContent = S.tut >= 7 ? (missoesFeitas() < 4 ? `Missões da história · ${missoesFeitas()}/4` : 'Livre para explorar') : `Missão ${Math.min(S.tut + 1, 7)} de 7`; $('#qTitle').textContent = q[0];
  const ul = $('#qList'); ul.innerHTML = ''; q[1].forEach(([tx, d]) => ul.append(h('li', { class: d ? 'done' : '' }, h('span', { class: 'ck' }, d ? '✓' : ''), h('span', {}, tx))));
}
const SELOS = {
  autor: { nome: 'Autor(a) da Vila', ic: '🏅', desc: 'Completou as missões da Pena.' },
  explorador: { nome: 'Explorador(a) da Vila', ic: '🧭', desc: 'Visitou as 5 casas.' },
  douradas: { nome: 'Caçador(a) de Folhas Douradas', ic: '🍂', desc: 'Achou as 9 folhas douradas escondidas.' },
  artesao: { nome: 'Mãos de Artesã(o)', ic: '🔨', desc: 'Criou 5 coisas no Livro de Receitas.' },
  livro: { nome: 'Primeiro Mini-livro', ic: '📚', desc: 'Encadernou um mini-livro na Gráfica.' },
  historia: { nome: 'História Completa', ic: '📜', desc: 'Personagem, cenário, problema e final.' },
  album: { nome: 'Colecionador(a)', ic: '📒', desc: 'Encontrou os 31 itens do álbum.' },
};
function award(id) { if (S.selos[id]) return; S.selos[id] = Date.now(); save(); Srv.agora(); Snd.fanfare(); confetti(innerWidth / 2, innerHeight / 2, 170); toast(`${SELOS[id].ic} Novo selo: ${SELOS[id].nome}!`); if (id === 'autor') checkDiscoveries(); refreshQuest(); }
function updateBadges() {
  const b = $('#bReceitas'); if (!b) return; const n = RECIPES.filter((r) => { const s = recipeState(r); return s.disc && !s.lockBook && s.seasonOk && !r.onde && s.has; }).length;
  let dot = b.querySelector('.dot'); if (n) { if (!dot) { dot = h('span', { class: 'dot' }); b.append(dot); } dot.textContent = n; } else if (dot) dot.remove();
}
function onCrafted(id) {
  if (S.tut === 2 && id === 'guirlanda') { S.tut = 3; save(); GAME.afterPanel = () => say([6]); }
  if ((S.crafts || 0) >= 5) award('artesao');
  if (id === 'miniLivro') award('livro');
  refreshQuest();
}

// ---------- painéis ----------
function openPanel(title, build, opts = {}) {
  if (GAME.dlg) return;
  GAME.panel = true; GAME.lock = true; P.target = null;
  const sh = $('#sheet'); sh.innerHTML = '';
  const body = h('div', {});
  sh.append(h('button', { class: 'x', 'aria-label': 'Fechar', onclick: closePanel }, '✕'), h('header', {}, opts.icon ? h('img', { src: opts.icon, width: 48, height: 48, alt: '' }) : null, h('div', {}, opts.eyebrow ? h('div', { class: 'eyebrow' }, opts.eyebrow) : null, h('h3', {}, title))), body);
  GAME.panelOnClose = opts.onClose || null;
  build(body); $('#panel').hidden = false; Snd.click();
  sh.tabIndex = -1; setTimeout(() => { if (GAME.panel) sh.focus({ preventScroll: true }); }, 30);
}
function closePanel() {
  if (!GAME.panel) return; $('#panel').hidden = true; GAME.panel = false; GAME.lock = !!GAME.dlg;
  const f = GAME.panelOnClose; GAME.panelOnClose = null; f && f();
  const a = GAME.afterPanel; GAME.afterPanel = null; a && a();
  renderer.domElement.focus({ preventScroll: true });
}
function openMochila(sel) {
  openPanel('Mochila', (body) => {
    const ids = Object.keys(S.inv).filter((k) => S.inv[k] > 0 && ITEMS[k]);
    if (!ids.length) { body.append(h('p', {}, 'Sua mochila está vazia. Ande pela praça: flores, gravetos e conchas aparecem pelo chão!')); return; }
    const order = Object.keys(ITEMS); ids.sort((a, b) => order.indexOf(a) - order.indexOf(b));
    const detail = h('div', { class: 'detail' });
    const groups = [['Ingredientes', ids.filter((k) => ITEMS[k].tipo === 'ing')], ['Coisas do livro', ids.filter((k) => ITEMS[k].tipo === 'livro')], ['Criações e enfeites', ids.filter((k) => ITEMS[k].tipo === 'deco')]];
    const all = [];
    for (const [nm, list] of groups) {
      if (!list.length) continue; body.append(h('div', { class: 'sec' }, nm)); const grid = h('div', { class: 'inv' });
      list.forEach((k) => { const b = h('button', { class: 'slot' + (k === sel ? ' sel' : ''), onclick: () => { all.forEach((s) => s.classList.remove('sel')); b.classList.add('sel'); showDetail(k); } }, h('span', { class: 'n' }, '×' + S.inv[k]), h('img', { src: iconURL(k), alt: '' }), ITEMS[k].nome); all.push(b); grid.append(b); });
      body.append(grid);
    }
    body.append(detail);
    function showDetail(k) {
      detail.innerHTML = ''; const it = ITEMS[k], acts = h('div', { class: 'acts' });
      if (it.tipo === 'deco') acts.append(h('button', { class: 'btn leaf', onclick: () => startPlace(k) }, '📍 Colocar aqui'));
      if (it.wear) { const on = S.wearing === k; acts.append(h('button', { class: 'btn sky', onclick: () => { S.wearing = on ? null : k; save(); updateCrown(); Net.sendPresence(true); closePanel(); toast(on ? 'Você tirou a coroa.' : 'Que coroa linda! 👑'); } }, on ? 'Tirar' : '👑 Vestir')); }
      if (Net.giftTargets().length) acts.append(h('button', { class: 'btn grape', onclick: () => openGift(k) }, '🎁 Dar para colega'));
      detail.append(h('img', { src: iconURL(k), alt: '' }), h('div', { class: 'info' }, h('b', { style: 'font-family:var(--display);font-size:18px;display:block' }, it.nome), h('div', {}, it.desc || '')), acts);
    }
    if (sel && ITEMS[sel]) showDetail(sel); else detail.append(h('div', { class: 'info' }, 'Toque num item para ver o que dá para fazer com ele.'));
  }, { eyebrow: 'Seus itens' });
}
function openCraft(station) {
  GAME.station = station || null; checkDiscoveries(true);
  openPanel('Livro de Receitas', (body) => renderRecipes(body), { eyebrow: station ? STATION_NOME[station] : 'Menu geral · funciona em qualquer lugar', onClose: () => { GAME.station = null; updateBadges(); } });
}
function renderRecipes(body) {
  body.innerHTML = '';
  body.append(h('p', { style: 'font-size:14px;color:var(--muted)' }, GAME.station ? 'Nesta mesa você cria as receitas da vila e as especiais deste lugar.' : 'As receitas da vila e da estação funcionam em qualquer lugar. As do livro pedem a mesa do Ateliê ou da Gráfica.'));
  for (const [g, nm] of [['vila', 'Receitas da vila'], ['estacao', 'Receitas da estação'], ['livro', 'Receitas do livro']]) {
    body.append(h('div', { class: 'sec' }, nm)); const grid = h('div', { class: 'grid' });
    RECIPES.filter((r) => r.grupo === g).forEach((r) => grid.append(recipeCard(r, body))); body.append(grid);
  }
}
function recipeCard(r, body) {
  const st = recipeState(r), it = ITEMS[r.id], known = st.disc || st.lockBook;
  const ings = h('div', { class: 'ings' }, Object.entries(r.ing).map(([k, v]) => { const have = S.inv[k] || 0; return h('span', { class: 'chip ' + (have >= v ? 'ok' : 'no') }, h('img', { src: iconURL(k), alt: '' }), `${ITEMS[k].nome} ${Math.min(have, v)}/${v}`); }));
  let why;
  if (st.lockBook) why = '🔒 Abre com o selo Autor(a) da Vila';
  else if (!st.disc) why = 'Encontre todos os ingredientes para descobrir';
  else if (!st.seasonOk) why = `${SEASONS[r.estacao].ic} Só no ${SEASONS[r.estacao].nome}`;
  else if (!st.stationOk) why = `🔨 Só na ${STATION_NOME[r.onde]}`;
  else if (!st.has) why = 'Faltam ingredientes';
  else why = '✨ Pronto para criar!';
  return h('div', { class: 'rec' + (known ? '' : ' lock') },
    h('div', { class: 'top' }, h('img', { src: iconURL(r.id), alt: '' }), h('div', {}, h('div', { class: 'nm' }, known ? it.nome : 'Receita misteriosa'), r.estacao ? h('span', { class: 'chip st' }, SEASONS[r.estacao].ic + ' ' + SEASONS[r.estacao].nome) : r.onde ? h('span', { class: 'chip st' }, r.onde === 'atelie' ? '🎨 Ateliê' : '🖨 Gráfica') : null)),
    ings, h('div', { class: 'why' }, why), h('button', { class: 'btn leaf sm', disabled: !st.can, onclick: () => doCraft(r, body) }, 'Criar!'));
}
function doCraft(r, body) {
  if (!recipeState(r).can) return;
  takeItems(r.ing); body.innerHTML = '';
  const msg = h('p', { style: 'text-align:center;font-weight:700;font-size:18px' }, 'Misturando…'), forge = h('div', { class: 'forge' }, h('div', { class: 'bowl' }));
  body.append(msg, forge);
  const imgs = []; Object.entries(r.ing).forEach(([k, v]) => { for (let i = 0; i < Math.min(v, 4); i++) { const im = h('img', { src: iconURL(k), alt: '' }); forge.append(im); imgs.push(im); } });
  imgs.forEach((im, i) => { const a = (i / imgs.length) * Math.PI * 2, dx = Math.cos(a) * 150, dy = Math.sin(a) * 66; im.animate([{ transform: `translate(${dx}px,${dy}px) rotate(0deg) scale(1)` }, { transform: 'translate(0px,0px) rotate(540deg) scale(.3)', opacity: 0.2 }], { duration: 700, delay: i * 60, easing: 'cubic-bezier(.6,-0.3,.7,1)', fill: 'forwards' }); });
  Snd.craft();
  setTimeout(() => {
    forge.innerHTML = ''; const out = h('img', { src: iconURL(r.id), alt: '', style: 'width:100px;height:100px;left:calc(50% - 50px);top:calc(50% - 50px)' }); forge.append(h('div', { class: 'bowl' }), out);
    out.animate([{ transform: 'scale(0) rotate(-30deg)' }, { transform: 'scale(1.25) rotate(8deg)' }, { transform: 'scale(1) rotate(0deg)' }], { duration: 520, easing: 'ease-out' });
    confettiAtEl(out); S.crafts = (S.crafts || 0) + 1; addItem(r.id, 1, { silent: true }); save(); burst(P.pos.x, 2, P.pos.z); onCrafted(r.id);
    msg.textContent = `Você criou: ${ITEMS[r.id].nome}!`;
    const acts = h('div', { class: 'row', style: 'justify-content:center' });
    if (ITEMS[r.id].tipo === 'deco') acts.append(h('button', { class: 'btn leaf', onclick: () => startPlace(r.id) }, '📍 Colocar agora'));
    if (ITEMS[r.id].wear) acts.append(h('button', { class: 'btn sky', onclick: () => { S.wearing = r.id; save(); updateCrown(); Net.sendPresence(true); closePanel(); } }, '👑 Vestir'));
    acts.append(h('button', { class: 'btn plain', onclick: () => renderRecipes(body) }, '📖 Voltar às receitas'));
    body.append(acts);
  }, 950);
}
function openSelos() {
  openPanel('Selos e conquistas', (body) => {
    const m = h('div', { class: 'medals' });
    for (const [k, s2] of Object.entries(SELOS)) m.append(h('div', { class: 'medal' + (S.selos[k] ? ' got' : '') }, h('div', { class: 'm' }, S.selos[k] ? s2.ic : '?'), h('div', {}, h('b', {}, s2.nome), s2.desc)));
    body.append(m);
    body.append(h('div', { class: 'sec' }, 'Seu progresso'), h('p', {}, `Casas visitadas: ${Object.keys(S.visited).length}/5 · Folhas douradas: ${goldCount()}/${GOLD_SPOTS.length} · Coisas criadas: ${S.crafts || 0} · Álbum: ${albumCount()}/${Object.keys(ITEMS).length} · Missões da história: ${missoesFeitas()}/4`));
    body.append(h('div', { class: 'sec' }, 'Estação da vila'), h('div', { class: 'row' }, h('span', {}, `${SEASONS[GAME.season].ic} Agora é ${SEASONS[GAME.season].nome}.`), h('button', { class: 'btn plain sm', onclick: () => { closePanel(); openEstacao(); } }, 'Trocar a estação')));
    const reset = h('button', { class: 'btn plain sm', onclick: () => {
      if (!reset.dataset.k) { reset.dataset.k = 1; reset.textContent = Srv.on ? 'Toque de novo: apaga também o que está guardado na Fábrica' : 'Toque de novo para apagar tudo'; return; }
      const keep = { codigo: S.codigo, vid: S.vid, nome: S.nome, turma: S.turma, turmaId: S.turmaId, colegio: S.colegio, tituloLivro: S.tituloLivro, livroDesenhos: S.livroDesenhos };
      S = Object.assign(defSave(), Srv.on ? keep : {}); S.salvoEm = Date.now(); lsSet(SAVE_KEY, JSON.stringify(S)); lsDel(DRAW_KEY);
      if (Srv.on) { Srv.busy = false; Srv.enviar().finally(() => location.reload()); setTimeout(() => location.reload(), 4000); } else location.reload();
    } }, 'Recomeçar do zero');
    const st = !Srv.on ? 'Jogando como visitante: o progresso fica só neste aparelho.'
      : Srv.last ? `☁️ Progresso guardado na Fábrica de Autores às ${new Date(Srv.last).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}.` : Srv.erro ? '⚠️ Sem conexão agora. O progresso fica guardado neste aparelho e sobe quando a internet voltar.' : '☁️ Guardando o progresso na Fábrica de Autores…';
    const figTx = Srv.on && S.charKey === 'img' ? ({ SIM: 'Sua figurinha já aparece para os colegas ✔', NAO: 'A professora pediu outro desenho para a figurinha. Troque o personagem quando quiser.' }[S.figAprov] || 'Sua figurinha está esperando a professora aprovar para aparecer para os colegas.') : '';
    const row = h('div', { class: 'row' }, h('button', { class: 'btn sky sm', onclick: () => { closePanel(); GAME.started = false; ENTRY.modo = Srv.on ? 'codigo' : 'visitante'; showEntry(2); } }, '🎨 Trocar personagem'));
    if (Srv.on) row.append(h('button', { class: 'btn plain sm', onclick: () => { closePanel(); sairDaVila(); } }, '🚪 Sair (outra criança vai jogar)'));
    else row.append(h('button', { class: 'btn leaf sm', onclick: () => { closePanel(); GAME.started = false; showEntry(1); } }, '🔑 Entrar com o código do livro'));
    row.append(reset);
    body.append(h('div', { class: 'sec' }, 'Você na vila'), row, h('p', { style: 'font-size:13px;color:var(--muted);margin-top:10px' }, st + (figTx ? ' ' + figTx : '') + ` Motor gráfico: ${ENGINE}.`));
  }, { eyebrow: S.codigo ? `${S.nome} · ${S.turma}` : S.nome ? `${S.nome} · visitante` : 'Conquistas' });
}
function openEstacao() {
  openPanel('Estações da vila', (body) => {
    body.append(h('p', {}, 'Folhagem, céu, luz, enfeites, interiores e receitas mudam com a estação. No modo automático, a vila segue o calendário do Brasil.'));
    const row = h('div', { class: 'row' });
    const mk = (k, label) => h('button', { class: 'btn ' + ((S.season === k) ? 'leaf' : 'plain'), onclick: () => { S.season = k; save(); applySeason(k === 'auto' ? seasonByDate() : k, true); closePanel(); } }, label);
    row.append(mk('auto', `📅 Automática (${SEASONS[seasonByDate()].nome})`));
    for (const [k, s] of Object.entries(SEASONS)) row.append(mk(k, `${s.ic} ${s.nome}`));
    body.append(row);
  }, { eyebrow: `Agora: ${SEASONS[GAME.season].nome}` });
}
function openCaderno(aba) {
  let cur = null;
  if (!aba) aba = S.tut === 5 && S.flags.idea && !escritaOk() ? 'escrita' : 'ideias';
  openPanel('Caderno de Ideias', (body) => {
    const tabs = h('div', { class: 'tabs' });
    const mk = (k, tx) => h('button', { type: 'button', class: 'btn sm ' + (aba === k ? 'leaf' : 'plain'), 'aria-pressed': aba === k ? 'true' : 'false', onclick: () => { closePanel(); openCaderno(k); } }, tx);
    tabs.append(mk('ideias', '🎲 Sortear ideias'), mk('escrita', '✏️ Minha história' + (escritaOk() ? ' ✔' : '')));
    body.append(tabs);
    if (aba === 'escrita') { abaEscrita(body); return; }
    const cards = h('div', { class: 'idea' }); const mkc = (lab) => { const v = h('div', {}, '…'); cards.append(h('div', { class: 'card' }, h('div', { class: 'eyebrow' }, lab), v)); return v; };
    const a2 = mkc('Personagem'), b2 = mkc('Lugar'), c2 = mkc('Problema');
    body.append(h('p', {}, 'Sorteie uma ideia de história. Gostou? Guarde no baú e use depois para fazer uma Página Ilustrada no Ateliê.'), cards);
    const cnt = h('span', { style: 'font-size:14px;color:var(--muted)' }, `Ideias guardadas: ${S.ideas.length}`);
    const saveBtn = h('button', { class: 'btn leaf', onclick: () => { if (!cur) return; S.ideas.push(Object.assign({ em: Date.now() }, cur)); S.flags.idea = 1; save(); addItem('ideia'); saveBtn.disabled = true; saveBtn.textContent = 'Guardada no baú ✔'; cnt.textContent = `Ideias guardadas: ${S.ideas.length}`; Snd.pop(); if (!escritaOk()) toast('Agora toque em ✏️ Minha história para escrever o título e a primeira frase.'); } }, '💾 Guardar no baú');
    const roll = () => { let n = 0; saveBtn.disabled = true; const iv = setInterval(() => { cur = { p: pick(IDEIAS.personagem), l: pick(IDEIAS.lugar), q: pick(IDEIAS.problema) }; a2.textContent = cur.p; b2.textContent = cur.l; c2.textContent = cur.q; Snd.tick(); if (++n >= 8) { clearInterval(iv); Snd.pop(); saveBtn.disabled = false; saveBtn.textContent = '💾 Guardar no baú'; } }, 75); };
    body.append(h('div', { class: 'row' }, h('button', { class: 'btn', onclick: roll }, '🎲 Sortear'), saveBtn, cnt));
    roll();
  }, { eyebrow: 'Casa da Pena', icon: iconURL('ideia'), onClose: () => checkTutorial() });
}
function openBau() {
  if (!S.selos.autor) {
    if (S.tut >= 5 && tutTasksDone()) {
      const lid = ROOM_FX.chestLid; let k = 0; Snd.lever(); anim((dt) => { k += dt / 0.7; lid.rotation.x = -Math.min(1, k) * 1.9; return k >= 1; });
      setTimeout(() => { S.tut = 7; save(); award('autor'); burst(rw('pena', 4.6), 1.5, 2.3); say([13, 14, 15], () => { updatePenaArea(); refreshQuest(); }); }, 700);
      return;
    }
    const g3 = ['p1', 'p2', 'p3'].filter((k) => S.found[k]).length;
    openPanel('Baú de Conquistas', (body) => {
      body.append(h('p', {}, 'O baú está trancado com um laço de fita. Para abrir, complete as tarefas da Pena:'));
      const ul = h('div', { class: 'list' });
      [['Guardar uma ideia no Caderno de Ideias', S.flags.idea], ['Escrever o título e a primeira frase (no Caderno)', escritaOk()], ['Acender a lareira', S.flags.fogo], [`Achar 3 folhas douradas aqui dentro (${g3}/3)`, g3 >= 3]].forEach(([t, d]) => ul.append(h('div', { class: 'it' }, h('span', { class: 'chip ' + (d ? 'ok' : 'no') }, d ? '✓ feito' : 'falta'), t)));
      body.append(ul);
    }, { eyebrow: 'Casa da Pena' });
    return;
  }
  openPanel('Baú de Conquistas', (body) => {
    body.append(h('div', { class: 'sec' }, 'Selos'));
    const m = h('div', { class: 'medals' }); for (const [k, s] of Object.entries(SELOS)) if (S.selos[k]) m.append(h('div', { class: 'medal got' }, h('div', { class: 'm' }, s.ic), h('div', {}, h('b', {}, s.nome), s.desc))); body.append(m);
    const mh = minhaHistoria();
    if (mh.length) { body.append(h('div', { class: 'sec' }, 'Minha história até agora')); const hl = h('div', { class: 'list' }); mh.forEach(([k, v]) => hl.append(h('div', { class: 'it' }, h('b', { style: 'min-width:110px' }, k), h('span', {}, v)))); body.append(hl); }
    body.append(h('div', { class: 'sec' }, `Ideias guardadas (${S.ideas.length})`));
    const ul = h('div', { class: 'list' }); S.ideas.slice(-8).reverse().forEach((i) => ul.append(h('div', { class: 'it' }, h('img', { src: iconURL('ideia'), alt: '' }), `${i.p[0].toUpperCase() + i.p.slice(1)}, ${i.l}, que ${i.q}.`)));
    if (!S.ideas.length) ul.append(h('div', { class: 'it' }, 'Nenhuma ideia ainda. Use o Caderno de Ideias na mesa.'));
    body.append(ul);
  }, { eyebrow: 'Casa da Pena' });
}
function toggleFire() { S.flags.fogoOn = !S.flags.fogoOn; if (S.flags.fogoOn) { S.flags.fogo = 1; Snd.noise(0.6, 0.25, 900); Snd.tone(220, 0.4, 'sine', 0.08, 0, 440); } else Snd.noise(0.4, 0.15, 400); save(); applyFire(); checkTutorial(); }
function applyFire() { const on = !!S.flags.fogoOn; if (ROOM_FX.fire) ROOM_FX.fire.visible = on; Snd.fire(on); VILLAGE.smoke.pena.forEach((p) => (p.visible = on)); }
function pullLever() {
  const w = cooldown('papel', 10);
  ROOM_FX.lever.rotation.z = -0.25; let k = 0; Snd.lever();
  anim((dt) => { k += dt; ROOM_FX.lever.rotation.z = -0.25 - Math.sin(Math.min(1, k / 0.6) * Math.PI) * 1.1; ROOM_FX.rollers.forEach((r) => (r.rotation.x += dt * 8)); return k > 0.6; });
  if (w) { toast(`A impressora está esfriando… volte em ${w}s.`); return; }
  const sh = ROOM_FX.sheet; sh.visible = true; sh.position.z = 0.7; let j = 0;
  anim((dt) => { j += dt; sh.position.z = 0.7 + Math.min(1, j / 0.8) * 0.6; if (j > 1.6) { sh.visible = false; return true; } });
  setTimeout(() => addItem('papel'), 700);
}
function ringBell() { ROOM_FX.bellT = 0; Snd.bell(); }
function openVaral() {
  openPanel('Varal da turma', (body) => {
    const list = varalList();
    body.append(h('p', {}, Net.on ? 'Os personagens da sua turma aparecem aqui depois que a professora aprova cada figurinha.' : 'Entrando com o código do livro, os personagens da sua turma aparecem aqui. Por enquanto, veja exemplos.'));
    const grid = h('div', { class: 'inv' });
    list.forEach((it) => { const im = h('img', { alt: '', style: 'width:72px;height:88px;object-fit:contain' }); if (it.canvas) im.src = it.canvas.toDataURL(); else if (it.url) im.src = it.url; grid.append(h('div', { class: 'slot' }, im, it.nome)); });
    body.append(grid);
  }, { eyebrow: 'Ateliê de Desenho' });
}
function openQuadro() {
  openPanel('Quadro de nomes', (body) => {
    const inp = h('input', { id: 'qNome', maxlength: 24, placeholder: 'Ex.: Tito, o dragão cozinheiro', value: S.nomePers || '' });
    body.append(h('p', {}, 'Escreva o nome do personagem da sua história. Ele vai para a Capa do Livro.'), h('label', { class: 'field' }, h('span', {}, 'Nome do personagem'), inp));
    body.append(h('button', { class: 'btn leaf', onclick: () => { const v = inp.value.trim().slice(0, 24); if (!v) { inp.focus(); return; } S.nomePers = v; save(); drawChalk(); addItem('nomePers'); Snd.pop(); closePanel(); } }, '✏️ Escrever no quadro'));
    setTimeout(() => inp.focus(), 60);
  }, { eyebrow: 'Ateliê de Desenho', icon: iconURL('nomePers') });
}
function openCartas() {
  S.cartas.forEach((c) => (c.lida = true)); save();
  openPanel('Caixa de correio', (body) => {
    const ul = h('div', { class: 'list' });
    S.cartas.slice(-12).reverse().forEach((c) => ul.append(h('div', { class: 'it' }, h('img', { src: iconURL(c.item || 'papel'), alt: '' }), h('div', {}, h('b', {}, 'De: ' + String(c.de || 'Alguém').slice(0, 16)), h('div', {}, c.txt || (c.item ? `Um presente: ${ITEMS[c.item] ? ITEMS[c.item].nome : c.item}.` : ''))))));
    body.append(ul);
  }, { eyebrow: 'Correio das Histórias' });
}
function openMural() {
  openPanel('Mural da turma', (body) => {
    body.append(h('p', {}, 'Escolha uma figurinha para colar no mural. Cada pessoa tem um cantinho, e a figurinha nova troca a antiga.'));
    const figs = h('div', { class: 'figs' }); FIGURINHAS.forEach((f, i) => figs.append(h('button', { class: 'btn plain sm', onclick: () => { postMural(i); closePanel(); } }, f)));
    body.append(figs);
  }, { eyebrow: 'Correio das Histórias' });
}
function refreshColetiva() { const t = coletivaTotals(); const ok = Object.keys(COLETIVA_META).every((k) => t[k] >= COLETIVA_META[k]); if (VILLAGE.coletivaArch) { if (ok && !VILLAGE.coletivaArch.visible && GAME.started) { toast('🎉 O Arco da Turma ficou pronto na praça!'); burst(0, 4, 9.9); } VILLAGE.coletivaArch.visible = ok; } }
function openColetiva() {
  openPanel('Baú da Turma', (body) => {
    const render = () => {
      body.innerHTML = ''; const t = coletivaTotals();
      body.append(h('p', {}, Net.on ? 'Todo mundo da turma pode doar. Quando o baú encher, o Arco da Turma aparece na entrada da praça para todos.' : 'Doe materiais para montar o Arco da Turma. Com as salas ligadas, a turma inteira enche o mesmo baú.'));
      for (const [k, meta] of Object.entries(COLETIVA_META)) {
        const v = Math.min(meta, t[k]);
        body.append(h('div', { class: 'row', style: 'margin:10px 0' }, h('img', { src: iconURL(k), alt: '', width: 36, height: 36 }), h('div', { style: 'flex:1 1 160px;min-width:0' }, h('b', {}, `${ITEMS[k].nome}: ${v}/${meta}`), h('div', { class: 'bar' }, h('i', { style: `width:${(v / meta) * 100}%` }))), h('button', { class: 'btn leaf sm', disabled: !(S.inv[k] > 0) || t[k] >= meta, onclick: () => { takeItems({ [k]: 1 }); S.coletiva[k] = (S.coletiva[k] || 0) + 1; save(); Net.pushTurma(); Snd.pop(); refreshColetiva(); render(); } }, `Doar 1 (você tem ${S.inv[k] || 0})`)));
      }
      if (VILLAGE.coletivaArch && VILLAGE.coletivaArch.visible) body.append(h('p', { style: 'font-weight:700' }, '🎉 O Arco da Turma está montado na praça!'));
    };
    render();
  }, { eyebrow: 'Decoração Coletiva da Praça' });
}
function openGift(item) {
  openPanel('Dar um presente', (body) => {
    const list = Net.giftTargets();
    body.append(h('p', {}, `Escolha um colega perto de você para receber 1 ${ITEMS[item].nome}. O presente chega na caixa de correio dele.`));
    const ul = h('div', { class: 'list' });
    list.forEach((p) => ul.append(h('div', { class: 'it' }, h('b', { style: 'flex:1' }, p.nome), h('button', { class: 'btn grape sm', onclick: () => { Net.sendGift(p.u, item); closePanel(); } }, '🎁 Enviar'))));
    if (!list.length) ul.append(h('div', { class: 'it' }, 'Nenhum colega por perto agora.'));
    body.append(ul);
  }, { eyebrow: 'Mochila', icon: iconURL(item) });
}
async function refreshVaral() {
  const list = varalList();
  for (let i = 0; i < ROOM_FX.varal.length; i++) {
    const slot = ROOM_FX.varal[i], it = list[i]; slot.fr.visible = !!it; if (!it) continue;
    let c = it.canvas; if (!c && it.url) { try { c = await loadImgCanvas(it.url); } catch (e) { c = null; } }
    if (c) { if (slot.m.map) slot.m.map.dispose(); slot.m.map = canvasTex(c); slot.m.needsUpdate = true; }
  }
}

// ---------- decorar: colocar itens no mundo ----------
const PLACED_MESH = new Map();
function plantStage(rec) { if (rec.item !== 'florPlantada') return 0; const min = (Date.now() - rec.t) / 60000; return min < 2 ? 0 : min < 5 ? 1 : 2; }
function spawnPlaced(rec) {
  if (!MODEL[rec.item]) return;
  const stage = plantStage(rec);
  const m = rec.item === 'florPlantada' ? MODEL.florPlantada({ stage, c: rec.c }) : MODEL[rec.item]();
  m.position.set(rec.x, rec.y || 0, rec.z); m.rotation.y = rec.r || 0; scene.add(m);
  const it = rec.door ? null : inter({ area: rec.area, x: rec.x, z: rec.z, r: 1.3, y: 1.6, prio: -1, label: () => `✋ Guardar ${ITEMS[rec.item].nome}`, act: () => pickUpPlaced(rec) });
  PLACED_MESH.set(rec.id, { m, it, stage, rec });
}
function pickUpPlaced(rec) { const e = PLACED_MESH.get(rec.id); if (e) { scene.remove(e.m); if (e.it) e.it.dead = true; PLACED_MESH.delete(rec.id); } S.placed = S.placed.filter((p) => p.id !== rec.id); save(); addItem(rec.item, 1); Snd.pop(); }
let plantT = 0;
function updatePlaced(dt, t) {
  plantT += dt; const check = plantT > 3; if (check) plantT = 0;
  for (const e of PLACED_MESH.values()) {
    e.m.visible = e.rec.area === GAME.area;
    if (e.rec.item === 'enfeiteJanela' && e.m.visible) e.m.children.forEach((c) => { if (c.userData.sw !== undefined) c.rotation.z = Math.sin(t * 2 + c.userData.sw) * 0.25; });
    if (check && e.rec.item === 'florPlantada') { const s = plantStage(e.rec); if (s !== e.stage) { scene.remove(e.m); e.m = MODEL.florPlantada({ stage: s, c: e.rec.c }); e.m.position.set(e.rec.x, 0, e.rec.z); scene.add(e.m); e.stage = s; if (s === 2 && GAME.area === e.rec.area) toast('🌼 Sua flor plantada desabrochou!'); } }
  }
}
function startPlace(item) {
  closePanel(); if (!(S.inv[item] > 0)) return;
  const ghost = item === 'florPlantada' ? MODEL.florPlantada({ stage: 0 }) : MODEL[item](); scene.add(ghost);
  GAME.placing = { item, ghost, rot: 0, door: null, pos: null };
  $('#placeBar').hidden = false; $('#placeMsg').textContent = ITEMS[item].door ? 'Ande até uma porta para pendurar (ou escolha um lugar no chão)' : 'Ande para escolher o lugar';
}
function updatePlace(dt, t) {
  const pl = GAME.placing; if (!pl) return;
  let x = P.pos.x + P.dir.x * 1.5, z = P.pos.z + P.dir.z * 1.5, y = ITEMS[pl.item].groundY || 0, ry = pl.rot; pl.door = null;
  if (ITEMS[pl.item].door && GAME.area === 'vila') for (const H of Object.values(HOUSES)) { if (Math.hypot(H.doorX - P.pos.x, H.doorZ - P.pos.z) < 3.2) { pl.door = H.id; x = H.wreathX; z = H.wreathZ; y = 2.2; ry = H.rot; break; } }
  if (GAME.area !== 'vila') { const b = BOUNDS[GAME.area]; x = clamp(x, b.x0 + 0.3, b.x1 - 0.3); z = clamp(z, b.z0 + 0.2, b.z1 - 0.6); }
  pl.ghost.position.set(x, y + (pl.door ? 0 : Math.sin(t * 6) * 0.05), z); pl.ghost.rotation.y = ry; pl.ghost.visible = Math.sin(t * 10) > -0.7;
  pl.pos = { x, y, z, ry };
  $('#placeMsg').textContent = pl.door ? `Pendurar na porta: ${HOUSES[pl.door].nome}` : (S.tut === 3 && pl.item === 'guirlanda' ? 'Chegue pertinho de uma porta para pendurar' : 'Ande para escolher o lugar');
}
function confirmPlace() {
  const pl = GAME.placing; if (!pl || !pl.pos) return;
  if (S.tut === 3 && pl.item === 'guirlanda' && !pl.door) { toast('Para a missão, chegue pertinho de uma porta 🚪'); Snd.nope(); return; }
  if (pl.door && S.placed.some((p) => p.door === pl.door)) { toast('Essa porta já tem uma guirlanda!'); Snd.nope(); return; }
  if (!(S.inv[pl.item] > 0)) return cancelPlace();
  takeItems({ [pl.item]: 1 });
  const rec = { id: uid(), item: pl.item, area: GAME.area, x: pl.pos.x, y: pl.pos.y, z: pl.pos.z, r: pl.pos.ry, door: pl.door, t: Date.now() };
  if (pl.item === 'florPlantada') rec.c = pick([0xffd23f, 0xff8fb8, 0xa77bff, 0xff5e5e]);
  S.placed.push(rec); save(); spawnPlaced(rec);
  scene.remove(pl.ghost); GAME.placing = null; $('#placeBar').hidden = true; Snd.pop(); burst(rec.x, (rec.y || 0) + 0.8, rec.z);
  if (S.tut === 3 && rec.item === 'guirlanda' && rec.door) { S.tut = 4; save(); refreshQuest(); setTimeout(() => say([7], () => { penaGoHome(); refreshQuest(); }), 300); }
}
function cancelPlace() { const pl = GAME.placing; if (!pl) return; scene.remove(pl.ghost); GAME.placing = null; $('#placeBar').hidden = true; }

// ---------- vila: portas, fonte, baú da turma ----------
function villageInters() {
  for (const H of Object.values(HOUSES)) inter({ x: H.doorX, z: H.doorZ, r: 2.3, y: 3.4, label: () => (H.id === 'pena' && S.tut < 4 ? '🔒 Casa da Pena' : `🚪 Entrar · ${H.nome}`), act: () => enterHouse(H.id) });
  inter({ x: 0, z: 3.9, r: 1.9, y: 3.2, label: () => '💧 Pegar água da fonte', act: () => { if (cooldown('agua', 2)) return; addItem('agua'); Snd.tone(600, 0.2, 'sine', 0.15, 0, 1200); Snd.noise(0.3, 0.1, 2500); } });
  const b = VILLAGE.bauTurma.position; inter({ x: b.x + 0.9, z: b.z + 0.5, r: 1.8, y: 2.4, obj: VILLAGE.bauTurma, hopH: 0.2, label: () => '🧺 Baú da Turma', act: openColetiva });
}

// ---------- ambiente animado ----------
let clockSec = -1, chirpT = 4;
function updateAmbient(dt, t) {
  if (GAME.area === 'vila') {
    for (const d of VILLAGE.drops) { const u = (t * 0.6 + d.userData.p) % 1, a = d.userData.a, r = 1.35 + u * 1.3; d.position.set(Math.cos(a) * r, 2.85 + Math.sin(u * Math.PI) * 0.5 - u * 2.1, Math.sin(a) * r); }
    for (const tr of VILLAGE.trees) tr.rotation.z = Math.sin(t * 0.8 + tr.userData.ph) * 0.018;
    if (VILLAGE.flags) for (const f of VILLAGE.flags) f.rotation.x = Math.sin(t * 2.2 + f.userData.sw) * 0.25;
    for (const key of ['pena', 'grafica']) for (const p of VILLAGE.smoke[key]) { if (key === 'grafica') p.visible = true; if (!p.visible) continue; const u = (t * 0.25 + p.userData.ph) % 1; p.position.y = 0.5 + HH + 3.3 + u * 2.6; p.position.x = (key === 'pena' ? -1.8 : 1.9) + Math.sin(u * 5 + p.userData.ph * 6) * 0.3 + u * 0.6; p.scale.setScalar(0.5 + u * 0.9); }
    if (VILLAGE.vane) VILLAGE.vane.rotation.y = Math.sin(t * 0.5) * 1.2;
    if (VILLAGE.gear) VILLAGE.gear.rotation.y = t * 0.6;
    for (const b of VILLAGE.butterflies) { if (!b.parent.visible) break; const u = b.userData; b.position.set(u.cx + Math.sin(t * 0.5 + u.ph) * 3, 1.4 + Math.sin(t * 1.7 + u.ph) * 0.4, u.cz + Math.cos(t * 0.37 + u.ph) * 2.5); u.w1.rotation.z = Math.sin(t * 18 + u.ph) * 0.9; u.w2.rotation.z = -u.w1.rotation.z; b.rotation.y = t * 0.5 + u.ph; }
    chirpT -= dt; if (chirpT < 0) { chirpT = rnd(6, 13); if (GAME.started && (GAME.season === 'primavera' || GAME.season === 'verao')) Snd.chirp(); }
  } else {
    if (GAME.area === 'pena') {
      const on = !!S.flags.fogoOn; const lt = ROOM_FX.fireLight; lt.intensity = lerp(lt.intensity, on ? 16 + Math.sin(t * 13) * 2.5 + Math.sin(t * 7.1) * 2 : 0, 1 - Math.exp(-dt * 6));
      if (on) ROOM_FX.fire.children.forEach((c, i) => { c.scale.y = 1 + Math.sin(t * 9 + i * 1.7) * 0.18; c.scale.x = c.scale.z = 1 + Math.cos(t * 7 + i) * 0.08; });
      ROOM_FX.pend.rotation.z = Math.sin(t * Math.PI) * 0.28;
      const d = new Date(), s = d.getSeconds(); if (s !== clockSec) { clockSec = s; const hh = d.getHours() % 12, mm = d.getMinutes(); ROOM_FX.hands.hH.rotation.z = -((hh + mm / 60) / 12) * Math.PI * 2; ROOM_FX.hands.mH.rotation.z = -(mm / 60) * Math.PI * 2; if (s % 2 === 0 && Math.hypot(P.pos.x - rw('pena', 5.3), P.pos.z + 4) < 4) Snd.tone(1900, 0.02, 'square', 0.025); }
    }
    if (GAME.area === 'biblioteca' && ROOM_FX.globe) { ROOM_FX.globeV *= Math.exp(-dt * 0.7); ROOM_FX.globe.rotation.y += dt * (0.2 + ROOM_FX.globeV); }
    if (GAME.area === 'grafica' && ROOM_FX.flipping) { let busy = false; ROOM_FX.pages.forEach((p) => { if (p.t < 1) { p.t += dt * 1.6; busy = true; } p.pv.rotation.z = Math.max(0, Math.min(1, p.t)) * Math.PI; }); if (!busy) { ROOM_FX.flipping = false; setTimeout(() => ROOM_FX.pages.forEach((p) => { p.t = -1; p.pv.rotation.z = 0; }), 900); } }
    if (GAME.area === 'correio' && ROOM_FX.bell) { ROOM_FX.bellT += dt; ROOM_FX.bell.rotation.z = Math.sin(ROOM_FX.bellT * 9) * 0.5 * Math.exp(-ROOM_FX.bellT * 1.6); }
  }
}

// ---------- controles ----------
function bindInput() {
  const cv = renderer.domElement; cv.tabIndex = 0;
  addEventListener('keydown', (e) => {
    const tag = e.target && e.target.tagName; if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    Snd.ensure();
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) e.preventDefault();
    KEYS[e.code] = true;
    if (!GAME.started) return;
    if (e.code === 'Escape') { if (GAME.panel) closePanel(); else if (GAME.placing) cancelPlace(); return; }
    if (GAME.dlg) { if (['KeyE', 'Enter', 'Space'].includes(e.code)) advance(); return; }
    if (GAME.panel) return;
    if (GAME.placing) { if (e.code === 'Enter' || e.code === 'KeyE') confirmPlace(); if (e.code === 'KeyR') GAME.placing.rot += Math.PI / 4; return; }
    if (['KeyE', 'Enter', 'Space'].includes(e.code) && performance.now() - (GAME.dlgClosed || 0) > 450) { if (GAME.cur) doInteract(GAME.cur); else if (P.sitting) standUp(); }
    if (e.code === 'KeyC') openCraft(null);
    if (e.code === 'KeyI' || e.code === 'KeyB') openMochila();
    if (e.code === 'KeyL') openAlbum();
  });
  addEventListener('keyup', (e) => { KEYS[e.code] = false; });
  addEventListener('blur', () => { for (const k in KEYS) KEYS[k] = false; });
  cv.addEventListener('pointerdown', (e) => { Snd.ensure(); if (!GAME.started) return; if (GAME.dlg) { advance(); return; } PTR.down = true; PTR.sx = e.clientX; PTR.sy = e.clientY; PTR.id = e.pointerId; PTR.joy = false; PTR.t0 = performance.now(); try { cv.setPointerCapture(e.pointerId); } catch (er) {} });
  cv.addEventListener('pointermove', (e) => { if (!PTR.down || e.pointerId !== PTR.id) return; const dx = e.clientX - PTR.sx, dy = e.clientY - PTR.sy, d = Math.hypot(dx, dy); if (d > 14) { PTR.joy = true; const k = Math.min(1, d / 70); PTR.jx = (dx / d) * k; PTR.jz = (dy / d) * k; } });
  const up = (e) => { if (e.pointerId !== PTR.id) return; const wasJoy = PTR.joy; PTR.down = false; PTR.joy = false; PTR.jx = PTR.jz = 0; if (!wasJoy && e.type === 'pointerup' && performance.now() - PTR.t0 < 450) tapAt(e.clientX, e.clientY); };
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('wheel', (e) => { if (GAME.area === 'vila') CAM.zoom = clamp(CAM.zoom + Math.sign(e.deltaY) * 0.06, 0.7, 1.35); }, { passive: true });
  $('#dialog').addEventListener('click', (e) => { if (e.target.id === 'voz') return; advance(); });
  $('#voz').addEventListener('click', (e) => { e.stopPropagation(); if (GAME.dlg && GAME.dlg.voz) { Voz.play(GAME.dlg.voz); return; } S.voz = !S.voz; save(); $('#voz').classList.toggle('on', S.voz); if (S.voz && GAME.dlg) speak(GAME.dlg.full); else try { speechSynthesis.cancel(); } catch (er) {} });
  $('#act').addEventListener('click', () => { Snd.ensure(); if (GAME.dlg) return advance(); if (performance.now() - (GAME.dlgClosed || 0) < 450) return; if (GAME.cur) doInteract(GAME.cur); else if (P.sitting) standUp(); });
  $('#bMochila').addEventListener('click', () => openMochila());
  $('#bReceitas').addEventListener('click', () => openCraft(null));
  $('#bSelos').addEventListener('click', openSelos);
  $('#bAlbum').addEventListener('click', openAlbum);
  $('#bEstacao').addEventListener('click', openEstacao);
  $('#bSom').addEventListener('click', () => { Snd.ensure(); Snd.setMute(!S.mute); $('#somIc').textContent = S.mute ? '🔇' : '🔊'; if (!S.mute) Snd.pop(); });
  $('#qToggle').addEventListener('click', () => { const q = $('#quest'); q.classList.toggle('min'); $('#qToggle').textContent = q.classList.contains('min') ? '+' : '–'; });
  $('#pOk').addEventListener('click', confirmPlace); $('#pNo').addEventListener('click', cancelPlace); $('#pRot').addEventListener('click', () => { if (GAME.placing) GAME.placing.rot += Math.PI / 4; });
  $('#panel').addEventListener('click', (e) => { if (e.target.id === 'panel') closePanel(); });
}
function tapAt(cx, cy) {
  if (GAME.lock || GAME.placing) return;
  const ndc = new T.Vector2((cx / innerWidth) * 2 - 1, -(cy / innerHeight) * 2 + 1); RAY.setFromCamera(ndc, camera);
  const pt = new T.Vector3(); if (!RAY.ray.intersectPlane(GROUND, pt)) return;
  let best = null, bd = 1.5;
  for (const it of INTERS) { if (it.dead || it.area !== GAME.area || !it.label()) continue; const d = Math.hypot(it.x - pt.x, it.z - pt.z); if (d < bd) { bd = d; best = it; } }
  if (best) { if (Math.hypot(best.x - P.pos.x, best.z - P.pos.z) <= best.r) { doInteract(best); return; } P.autoAct = best; P.target = { x: best.x, z: best.z }; }
  else { P.autoAct = null; P.target = { x: pt.x, z: pt.z }; }
  P.stuck = 0;
}
function onResize() { Net.ui(); renderer.setSize(innerWidth, innerHeight); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }

// ---------- laço principal ----------
let lastT = performance.now(), posSaveT = 0;
function loop() {
  const now = performance.now(), dt = Math.min(0.05, (now - lastT) / 1000); lastT = now; GAME.t += dt; const t = GAME.t;
  if (GAME.entryOrbit) { const a = t * 0.06; camera.position.set(Math.sin(a) * 30, 17, Math.cos(a) * 30 + 2); camera.lookAt(0, 1.5, -3); camFocus.x = 0; camFocus.z = 0; }
  else { updatePlayer(dt, t); updateCamera(dt); }
  updatePena(dt, t); updateWorldItems(dt, t); updateInters(dt); updateAmbient(dt, t); updateParticles(dt, t); updatePlace(dt, t); updatePlaced(dt, t); updateRemotes(dt, t); updateMissoes(dt, t); runAnims(dt); Net.tick(dt); Srv.tick(dt); updateLabels();
  posSaveT += dt; if (posSaveT > 2 && GAME.started) { posSaveT = 0; if (GAME.area === 'vila') { S.x = Math.round(P.pos.x * 10) / 10; S.z = Math.round(P.pos.z * 10) / 10; save(); } }
  renderer.render(scene, camera);
}

// ---------- início ----------
async function boot() {
  const lt = $('#loadTx');
  try { await loadEngine(); } catch (e) { console.error(e); lt.textContent = 'Não consegui abrir o 3D neste navegador. Tente o Chrome atualizado.'; return; }
  try { await Promise.race([Promise.all([document.fonts.load('800 40px Grandstander'), document.fonts.load('700 20px Andika')]), new Promise((r) => setTimeout(r, 2500))]); } catch (e) {}
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5)); renderer.setSize(innerWidth, innerHeight); $('#stage').appendChild(renderer.domElement);
  scene = new T.Scene(); camera = new T.PerspectiveCamera(38, innerWidth / innerHeight, 0.5, 260);
  _v = new T.Vector3(); _ct = new T.Vector3(); _cl = new T.Vector3(); CAM_POS = new T.Vector3(0, 20, 40); CAM_LOOK = new T.Vector3(); RAY = new T.Raycaster(); GROUND = new T.Plane(new T.Vector3(0, 1, 0), 0);
  P.pos = new T.Vector3(0, 0, 25); P.vel = new T.Vector3(); P.dir = new T.Vector3(0, 0, -1);
  PROMPT_EL = h('div', { class: 'lbl prompt', hidden: true }, h('span', {}, ''), h('kbd', {}, 'E')); ME_LBL = h('div', { class: 'lbl name me', hidden: true }); $('#labels').append(PROMPT_EL, ME_LBL);
  initMats(); initLights(); buildVillage(); Object.keys(ROOM_DEFS).forEach(buildRoom);
  initGoldSpots(); initSpawnPoints(); createPena(); villageInters(); initMissoes();
  applySeason(S.season === 'auto' || !SEASONS[S.season] ? seasonByDate() : S.season);
  for (let i = 0; i < 10 && SPAWN_PTS.length; i++) { const p = SPAWN_PTS[(i * 7) % SPAWN_PTS.length]; spawnWorldItem(pickSpawnItem(), 'vila', p.x, p.z); }
  applyFire(); bindInput(); bindEntry(); addEventListener('resize', onResize);
  if (window.__vilaTest) window.__vila = { get S() { return S; }, GAME, P, Srv, Voz, iconURL, ITEMS, RECIPES, SELOS, SEASONS, drawPena, sampleSticker, coverCanvas, pageCanvas, openSelos, openMural, openColetiva, openCaderno, say, refreshQuest, applyFire, drawChalk, startPlace, openAlbum, openMissao, openCaderno, MISSOES, cutDrawing, API, HOUSES, ROOMS, Net, REMOTES, postMural, coletivaTotals, advance, startPlace, confirmPlace, openBau, PENA, WITEMS, enterHouse, exitHouse, startGame, openCraft, openMochila, applySeason, addItem, award, renderer, scene, get ENGINE() { return ENGINE; } };
  renderer.setAnimationLoop(loop);
  $('#loading').hidden = true; showEntry(1);
}
