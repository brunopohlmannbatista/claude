// ============================================================
// EDIÇÃO PAPEL (teste): camada visual por cima do jogo.
// Não muda regras, missões, salvamento nem servidor. Só o jeito de desenhar:
// cartolina fosca, recorte com filete de papel cru, árvores de cartão cruzado,
// sombra macia, lente de miniatura e tudo se levantando do chão como livro pop-up.
// Este arquivo entra entre 08-cantinho.js e 99-inicio.js (ver build-papel.sh).
// ============================================================
const PAPEL = { folds: [], tex: null, borda: null, last: 0, flapT: 0, sombras: true, nivel: 0, perf: { n: 0, acc: 0, espera: 4 }, vec: null, caixa: null };

// ---------- paleta de cartolina ----------
const PAPEL_ESTACAO = {
  primavera: { sky: 0xf6e7c6, ground: 0xb2d867, ground2: 0x9bc853, path: 0xf8dfa6, leafA: 0xff8f97, leafB: 0x98c94e, pine: 0x3f8f58, water: 0x35c4bd, light: 0xfff3dc },
  verao: { sky: 0xf8e5b4, ground: 0xa6d655, ground2: 0x8dc544, path: 0xfae09c, leafA: 0x6fc043, leafB: 0x48a443, pine: 0x34834e, water: 0x27c0c6, light: 0xfff0c8 },
  outono: { sky: 0xf2d39c, ground: 0xecc968, ground2: 0xdcb04f, path: 0xf6dba0, leafA: 0xff8a1f, leafB: 0xe0492a, pine: 0x447a47, water: 0x35b6b3, light: 0xffe8c0 },
  inverno: { sky: 0xe6e6e0, ground: 0xeef2f1, ground2: 0xd9e4ea, path: 0xdcd5c4, leafA: 0xf3f6f6, leafB: 0xcfe0ea, pine: 0x3c7a5c, water: 0xa9dfea, light: 0xf6f3ea },
};
let _papelHSL = null, _papelMix = null;
function tomPapel(hex) {
  // tinta de impressão sobre cartolina: um pouco menos néon e um pouco mais quente
  if (!_papelHSL) { _papelHSL = { h: 0, s: 0, l: 0 }; _papelMix = new T.Color(0xe2b384); }
  const c = new T.Color(hex); c.getHSL(_papelHSL);
  c.setHSL(_papelHSL.h, Math.min(1, _papelHSL.s * 1.12), 0.03 + _papelHSL.l * 0.95); c.lerp(_papelMix, 0.035);
  return c.getHex();
}

// ---------- textura de fibra de papel ----------
function texPapel(size, vinco) {
  const c = mkCanvas(size, size), g = c.getContext('2d'), R = seeded(11);
  const id = g.createImageData(size, size), d = id.data;
  for (let i = 0; i < d.length; i += 4) { const n = 232 + R() * 23; d[i] = n; d[i + 1] = n - 2; d[i + 2] = n - 7; d[i + 3] = 255; }
  g.putImageData(id, 0, 0);
  for (let i = 0; i < size * 0.9; i++) {
    const x = R() * size, y = R() * size, a = R() * 6.28, L = 5 + R() * 16;
    g.strokeStyle = R() < 0.55 ? 'rgba(255,255,255,.5)' : 'rgba(110,80,50,.17)'; g.lineWidth = 0.5 + R() * 0.8;
    g.beginPath(); g.moveTo(x, y); g.quadraticCurveTo(x + Math.cos(a) * L * 0.5 + R() * 4 - 2, y + Math.sin(a) * L * 0.5 + R() * 4 - 2, x + Math.cos(a) * L, y + Math.sin(a) * L); g.stroke();
  }
  if (vinco) { // vinco da página: a grade de dobras do livro
    g.fillStyle = 'rgba(90,65,40,.16)'; g.fillRect(0, 0, size, 1.5); g.fillRect(0, 0, 1.5, size);
    g.fillStyle = 'rgba(255,255,255,.4)'; g.fillRect(0, 1.5, size, 1.5); g.fillRect(1.5, 0, 1.5, size);
  }
  const t = canvasTex(c); t.wrapS = t.wrapT = T.RepeatWrapping; return t;
}

// ---------- materiais: cartolina fosca com filete de papel cru no lugar do nanquim ----------
const _toon0 = toon;
toon = function (color, opts = {}) {
  const m = _toon0(tomPapel(color), opts);
  if (PAPEL.tex && !m.map) { m.map = PAPEL.tex; m.needsUpdate = true; }
  return m;
};
const _part0 = part;
part = function (g, m, x, y, z, ol, parent) {
  const mesh = _part0(g, m, x, y, z, ol, parent);
  if (m && m.isMeshToonMaterial) { mesh.castShadow = true; mesh.receiveShadow = true; }
  return mesh;
};
const _initMats0 = initMats;
initMats = function () {
  PAPEL.vec = new T.Vector3(); PAPEL.caixa = new T.Box3();
  PAPEL.tex = texPapel(256, false);
  for (const k in SEASONS) {
    const s = SEASONS[k], p = PAPEL_ESTACAO[k];
    s.flags = s.flags.map(tomPapel); s.rug = tomPapel(s.rug);
    Object.assign(s, p); s.css = hexCss(p.sky); s.amb *= 0.88; s.dir *= 1.2;
  }
  _initMats0();
  // degraus de sombra mais macios (papel fosco, não desenho animado)
  GRAD.image.data.set([146, 146, 146, 255, 212, 212, 212, 255, 255, 255, 255, 255]); GRAD.needsUpdate = true;
  OUTLINE.color.setHex(0xfbf0da); // a beirada cortada do papel
  SHADOW_MAT.color.setHex(0x4a3320); SHADOW_MAT.opacity = 0.24;
  WINDOW_MAT.color.setHex(0xffc861); M.lamp.color.setHex(0xffd27a);
  PAPEL.borda = _toon0(0xfbf0da, { unique: true }); PAPEL.borda.map = PAPEL.tex;
  // o chão é a página do livro: fibra miúda e a grade de vincos
  const chao = texPapel(256, true); chao.repeat.set(15, 15); M.grass.map = chao; M.grass.needsUpdate = true;
  const fino = texPapel(128, false); fino.repeat.set(3, 3); [M.grass2, M.path, M.stone, M.stone2, M.stoneDark, M.water].forEach((m) => { m.map = fino; m.needsUpdate = true; });
};
const _initLights0 = initLights;
initLights = function () {
  _initLights0();
  // luz-chave quente com sombra macia + preenchimento frio do outro lado
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = T.PCFSoftShadowMap;
  const sh = LIGHT_DIR.shadow; LIGHT_DIR.castShadow = true; sh.mapSize.set(1536, 1536);
  sh.camera.left = -30; sh.camera.right = 30; sh.camera.top = 30; sh.camera.bottom = -30; sh.camera.near = 2; sh.camera.far = 90; sh.bias = -0.0007; sh.normalBias = 0.06;
  PAPEL.fill = new T.DirectionalLight(0x9db6d6, 0.42); PAPEL.fill.position.set(14, 12, -10); scene.add(PAPEL.fill);
  scene.background = new T.Color(SEASONS.primavera.sky); scene.fog.color.setHex(SEASONS.primavera.sky);
};

// ---------- recortes de cartão (formas 2D com espessura) ----------
function chapa(key, shape, mat, parent, z = 0, esp = 0.09, borda = 0.07, sx = 1) {
  const g = geo('pp' + key, () => { const e = new T.ExtrudeGeometry(shape(), { depth: esp, bevelEnabled: false, curveSegments: 4 }); e.translate(0, 0, -esp / 2); e.computeBoundingBox(); return e; });
  const m = new T.Mesh(g, mat); m.position.z = z; m.scale.x = sx; m.castShadow = true; m.receiveShadow = true; parent.add(m);
  if (borda > 0) { // filete de papel cru em volta do recorte, como adesivo destacado
    const s = PAPEL.vec; g.boundingBox.getSize(s); const kx = 1 + (2 * borda) / (s.x * sx), ky = 1 + (2 * borda) / s.y;
    const cx = (g.boundingBox.min.x + g.boundingBox.max.x) / 2, cy = (g.boundingBox.min.y + g.boundingBox.max.y) / 2;
    const b = new T.Mesh(g, PAPEL.borda); b.scale.set(kx, ky, 0.5); b.position.set(cx * (1 - kx), cy * (1 - ky), 0); b.userData.outline = true; b.receiveShadow = true; m.add(b);
  }
  return m;
}
function formaCopa(cx, cy, rx, ry, n, bojo = 0.22, giro = 0) {
  return () => { const s = new T.Shape();
    for (let i = 0; i <= n; i++) {
      const a = giro + (i / n) * Math.PI * 2, x = cx + Math.cos(a) * rx, y = cy + Math.sin(a) * ry;
      if (i === 0) { s.moveTo(x, y); continue; }
      const am = giro + ((i - 0.5) / n) * Math.PI * 2, k = 1 + bojo;
      s.quadraticCurveTo(cx + Math.cos(am) * rx * k, cy + Math.sin(am) * ry * k, x, y);
    }
    return s; };
}
function formaPinho(r, y0, y1, dentes = 5, serra = 0.24) {
  return () => { const s = new T.Shape(); s.moveTo(-r, y0);
    for (let i = 1; i <= dentes; i++) { s.lineTo(-r + (2 * r * (i - 0.5)) / dentes, y0 + serra); s.lineTo(-r + (2 * r * i) / dentes, y0); }
    s.lineTo(0.09, y1); s.lineTo(-0.09, y1); s.closePath(); return s; };
}
function formaTronco(b, t, h) { return () => { const s = new T.Shape(); s.moveTo(-b, 0); s.lineTo(b, 0); s.lineTo(t, h); s.lineTo(-t, h); s.closePath(); return s; }; }
function arvorePapel(g, kind) {
  const frutoG = geo('ppfruto', () => { const c = new T.CylinderGeometry(0.15, 0.15, 0.05, 10); c.rotateX(Math.PI / 2); return c; });
  [0, 1].forEach((lado) => {
    const c = new T.Group(); c.rotation.y = lado * (Math.PI / 2); g.add(c);
    const sx = lado ? 0.82 : 1;
    if (kind === 'pine') {
      chapa('tr-p', formaTronco(0.3, 0.2, 1.3), M.trunk, c, 0, 0.09, 0.05, sx);
      [[1.9, 0.65, 2.9], [1.5, 1.95, 3.9], [1.02, 3.2, 4.8]].forEach(([r, a, b], i) => {
        chapa('pn' + i, formaPinho(r, a, b), M.pine, c, 0.02 + i * 0.05, 0.09, 0.075, sx);
        seasonTag(chapa('pnn' + i, formaPinho(r * 0.5, b - (b - a) * 0.42, b, 3, 0.14), M.snow, c, 0.1 + i * 0.05, 0.05, 0, sx), 'inverno');
      });
    } else {
      chapa('tr-r', formaTronco(0.42, 0.24, 2.5), M.trunk, c, 0, 0.09, 0.05, sx);
      chapa('cpB', formaCopa(-0.12, 3.05, 1.78, 1.55, 9, 0.2, 0.2), M.leafB, c, -0.06, 0.09, 0.08, sx);
      chapa('cpA', formaCopa(0.14, 3.38, 1.4, 1.26, 8, 0.22, 0.5), M.leafA, c, 0.06, 0.09, 0.075, sx);
      if (!lado) {
        chapa('cpC', formaCopa(1.02, 2.55, 0.72, 0.62, 6, 0.24, 0.1), M.leafB, c, 0.13, 0.07, 0.06);
        chapa('cpD', formaCopa(-1.0, 2.5, 0.6, 0.52, 6, 0.24, 0.6), M.leafA, c, 0.13, 0.07, 0.06);
        const fr = new T.Group(); c.add(fr); seasonTag(fr, 'primavera', 'verao');
        [[-0.55, 3.75], [0.6, 3.0], [0.2, 4.05], [-0.85, 2.95], [0.95, 3.7]].forEach(([fx, fy], i) => { const f = new T.Mesh(frutoG, _toon0(tomPapel(i % 2 ? 0xfff6e4 : 0xe5484f))); f.position.set(fx, fy, 0.15); c.add(f); fr.add(f); });
      }
    }
  });
}
buildTree = function (V, x, z, s, kind) {
  const g = new T.Group(); g.position.set(x, 0, z); g.scale.setScalar(s); g.rotation.y = Math.sin(x * 1.7 + z * 2.3) * 0.45; V.add(g);
  arvorePapel(g, kind);
  g.userData.ph = x * 0.3 + z * 0.17; VILLAGE.trees.push(g);
  addCircle('vila', x, z, 0.65 * s);
};
cantArvore = function (g, x, z, s, kind) {
  const t = new T.Group(); t.position.set(x, 0, z); t.scale.setScalar(s); t.rotation.y = Math.sin(x * 1.7 + z * 2.3) * 0.45; g.add(t);
  arvorePapel(t, kind);
  t.userData.ph = x * 0.3 + z * 0.17; CANT.trees.push(t);
  addCircle('cantinho', cwX(x), cwZ(z), 0.65 * s);
};

// ---------- pop-up: tudo se levanta do chão com mola ----------
function somDobra(tam) {
  if (!Snd.ctx || S.mute) return; const now = performance.now(); if (now - PAPEL.flapT < 55) return; PAPEL.flapT = now;
  const f = rnd(1700, 3600) / (0.75 + tam * 0.09);
  Snd.noise(0.06 + tam * 0.008, 0.055, f, 0, 0.8); Snd.noise(0.045, 0.04, f * 1.9, 0.035, 1.2); Snd.tone(rnd(150, 230), 0.07, 'sine', 0.035, 0.01, 95);
}
// Só casa e árvore fazem o "flap" ao subir (pedido do Bruno em 17/11: com tudo soando, a praça virava um barulho contínuo).
function fazBarulho(o) { return VILLAGE.trees.includes(o) || CANT.trees.includes(o) || o === CANT.casa || Object.values(HOUSES).some((h) => h.group === o); }
function registraDobra(o, area, modo) {
  const p = PAPEL.vec, b = PAPEL.caixa; b.setFromObject(o);
  let x, z; if (modo === 'achata') { x = (b.min.x + b.max.x) / 2; z = (b.min.z + b.max.z) / 2; } else { o.getWorldPosition(p); x = p.x; z = p.z; }
  if (modo === 'dobra' && (Math.abs(o.rotation.x) > 1e-4 || Math.abs(o.rotation.z) > 1e-4 || o.position.y > 1.2)) modo = 'brota'; // peça inclinada ou presa na parede: cresce em vez de dobrar
  if (modo === 'dobra') o.rotation.order = 'YXZ';
  PAPEL.folds.push({ o, area, modo, som: fazBarulho(o), x, z, h: Math.max(0.5, b.max.y), tam: Math.max(b.max.y, b.max.x - b.min.x), k: 1, v: 0, alvo: 1, quieto: true, atraso: 0, sx: 1, sy: 1, sz: 1, y0: 0, lift: 0.05 + (PAPEL.folds.length % 9) * 0.011 });
}
function coletaDobras(grupo, area, desde = 0) {
  grupo.updateWorldMatrix(true, true);
  const b = new T.Box3(), s = new T.Vector3(), c = new T.Vector3(), w = new T.Vector3();
  const visita = (o) => {
    if (o.userData.outline || o.isInstancedMesh || o.isLight || o.userData.w1) return;
    b.setFromObject(o); if (b.isEmpty()) return; b.getSize(s); b.getCenter(c); o.getWorldPosition(w);
    if (b.max.y < 0.42) return; // peças chatas (chão, caminho, pedrinhas) ficam impressas na página
    const longe = Math.hypot(c.x - w.x, c.z - w.z);
    if (o.isGroup) {
      if ((s.x > 13 || s.z > 13 || longe > Math.max(s.x, s.z) * 0.5 + 1.5) && o.children.length > 1) { o.children.slice().forEach(visita); return; }
      registraDobra(o, area, 'dobra');
    } else if (o.isMesh) registraDobra(o, area, longe > 2.5 ? 'achata' : 'brota');
  };
  grupo.children.slice(desde).forEach(visita);
}
function capturaBase(f) { const o = f.o; f.sx = o.scale.x; f.sy = o.scale.y; f.sz = o.scale.z; f.y0 = o.position.y; }
function aplicaDobra(f) {
  const o = f.o, k = f.k, kc = clamp(k, 0, 1), e = kc * kc * (3 - 2 * kc);
  if (f.modo === 'dobra') {
    o.rotation.x = k <= 1 ? -(1 - k) * 1.5708 : (k - 1) * 0.85;
    o.scale.set(f.sx, f.sy, f.sz * lerp(0.05, 1, e)); o.position.y = f.y0 + (1 - e) * f.lift;
  } else if (f.modo === 'brota') { const s = Math.max(0.001, k); o.scale.set(f.sx * s, f.sy * s, f.sz * s); o.position.y = f.y0 * kc; }
  else o.scale.y = f.sy * Math.max(0.001, kc);
}
// deita tudo de uma área; depois cada peça sobe em onda, a partir de (ondaX, ondaZ) ou de onde o jogador estiver
function deitaTudo(area, ondaX, ondaZ, passo) {
  for (const f of PAPEL.folds) {
    if (f.area !== area) continue;
    if (f.quieto && f.k >= 1) capturaBase(f);
    f.k = 0; f.v = 0; f.alvo = 0; f.quieto = false; f.onda = passo; f.ox = ondaX; f.oz = ondaZ; aplicaDobra(f);
  }
}
function atualizaDobras(dt) {
  const area = GAME.area, abre = GAME.entryOrbit, v = PAPEL.vec;
  for (const f of PAPEL.folds) {
    if (f.area !== area) continue;
    let alvo = f.alvo;
    if (abre || area !== 'vila') alvo = 1; // no cantinho e nas salas a câmera quase não anda: tudo fica em pé depois da onda de abertura
    else {
      v.set(f.x, Math.min(f.h * 0.35, 1.6), f.z).project(camera);
      // sobe quando entra no quadro (pelo alto, que é o "lá na frente"); dos lados já chega quase em pé
      if (v.z < 1 && Math.abs(v.x) < 0.95 && v.y < 0.64 && v.y > -1.5) alvo = 1;
      else if (v.z >= 1 || Math.abs(v.x) > 1.1 || v.y > 0.84 || v.y < -1.9) alvo = 0;
    }
    if (alvo !== f.alvo) {
      if (f.quieto && f.k >= 1) capturaBase(f);
      f.alvo = alvo; f.quieto = false;
      if (alvo === 1) { const ox = f.ox === null && P.pos ? P.pos.x : f.ox || 0, oz = f.oz === null && P.pos ? P.pos.z : f.oz || 0; f.atraso = (f.onda ? Math.min(2.2, Math.hypot(f.x - ox, f.z - oz) * f.onda) : 0) + Math.random() * 0.07; f.onda = 0; f.soa = true; }
    }
    if (f.quieto) continue;
    if (f.alvo === 1 && f.atraso > 0) { f.atraso -= dt; continue; }
    if (f.soa) { f.soa = false; if (f.som && f.o.visible && (!f.o.parent || f.o.parent.visible)) somDobra(f.tam); }
    const sobe = f.alvo === 1, K = sobe ? 135 : 90, C = sobe ? 10.5 : 19;
    f.v += ((f.alvo - f.k) * K - f.v * C) * dt; f.k += f.v * dt;
    if (f.k < 0) { f.k = 0; f.v = 0; }
    if (Math.abs(f.k - f.alvo) < 0.002 && Math.abs(f.v) < 0.03) {
      f.k = f.alvo; f.v = 0; f.quieto = true;
      if (f.alvo === 1) { const o = f.o; if (f.modo === 'dobra') o.rotation.x = 0; o.scale.set(f.sx, f.sy, f.sz); o.position.y = f.y0; continue; }
    }
    aplicaDobra(f);
  }
}

// ---------- lente de miniatura, luz que acompanha e qualidade automática ----------
const _camTarget0 = camTarget;
camTarget = function (out, look) {
  _camTarget0(out, look);
  if (areaExterna(GAME.area)) { out.sub(look).multiplyScalar(1.27).add(look); } // lente mais longa: achata a perspectiva, cara de maquete
};
function papelQualidade(n) {
  PAPEL.nivel = n; try { localStorage.setItem('vila-papel-q', String(n)); } catch (e) {}
  document.body.classList.toggle('papel-leve', n >= 1);
  PAPEL.sombras = n < 2; LIGHT_DIR.castShadow = PAPEL.sombras;
}
function papelFrame() {
  const now = performance.now(), bruto = (now - (PAPEL.last || now)) / 1000, dt = Math.min(0.05, bruto); PAPEL.last = now;
  const fov = GAME.entryOrbit || !areaExterna(GAME.area) ? 38 : 30;
  if (camera.fov !== fov) { camera.fov = fov; camera.updateProjectionMatrix(); }
  const sala = ROOMS[GAME.area], fx = areaExterna(GAME.area) ? Math.round(camFocus.x * 2) / 2 : sala ? sala.ox : 0, fz = areaExterna(GAME.area) ? Math.round(camFocus.z * 2) / 2 : 0;
  LIGHT_DIR.target.position.set(fx, 0, fz); LIGHT_DIR.position.set(fx - 12, 26.4, fz + 16.8);
  atualizaDobras(dt);
  // se o aparelho não acompanhar, tira primeiro o desfoque e depois a sombra
  const pf = PAPEL.perf;
  if (GAME.started && !document.hidden && PAPEL.nivel < 2 && !PAPEL.fixo) {
    if (pf.espera > 0) pf.espera -= bruto;
    else { pf.n++; pf.acc += Math.min(bruto, 0.1); if (pf.n >= 150) { if (pf.acc / pf.n > 1 / 38) { papelQualidade(PAPEL.nivel + 1); pf.espera = 3; } pf.n = 0; pf.acc = 0; } }
  }
}
const _loop0 = loop;
loop = function () { papelFrame(); _loop0(); };
const _setArea0 = setArea;
setArea = function (a) {
  _setArea0(a);
  const fora = areaExterna(a);
  document.body.classList.toggle('papel-int', !fora);
  if (!fora) { scene.background.setHex(0x2a1b13); scene.fog.color.setHex(0x2a1b13); }
  LIGHT_DIR.castShadow = PAPEL.sombras;
  const sc = LIGHT_DIR.shadow.camera, e = fora ? 30 : 11; sc.left = -e; sc.right = e; sc.top = e; sc.bottom = -e; sc.updateProjectionMatrix(); // sala pequena: sombra mais nítida
  deitaTudo(a, null, null, a === 'vila' ? 0.035 : a === 'cantinho' ? 0.05 : 0.075);
  PAPEL.perf.espera = 3; PAPEL.perf.n = 0; PAPEL.perf.acc = 0;
};
// última coisa do boot: registra o que dobra e abre o livro
const _bindEntry0 = bindEntry;
bindEntry = function () {
  [VILLAGE.group, CANT.group].forEach((g) => g && g.traverse((o) => { if (o.isMesh && !o.isInstancedMesh && o.material && o.material.isMeshToonMaterial) o.receiveShadow = true; }));
  Object.values(ROOMS).forEach((r) => r.g.children.forEach((o) => { if (o.isMesh && o.geometry && o.geometry.parameters && (o.geometry.parameters.height > 5 || o.geometry.parameters.width > 13)) o.castShadow = false; })); // parede e piso não fazem sombra
  coletaDobras(VILLAGE.group, 'vila'); if (CANT.group) { const vis = CANT.group.visible; coletaDobras(CANT.group, 'cantinho'); CANT.group.visible = vis; }
  deitaTudo('vila', 0, 0, 0.055);
  let q = 0; try { q = Math.min(2, parseInt(localStorage.getItem('vila-papel-q') || '0', 10) || 0); } catch (e) {}
  if (q) papelQualidade(q);
  document.title = 'Vila dos Autores';
  if (window.__vilaTest) { window.__papel = PAPEL; PAPEL.luz = LIGHT_DIR; PAPEL.foco = camFocus; }
  return _bindEntry0();
};
