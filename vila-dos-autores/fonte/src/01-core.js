// ============================================================
// Vila dos Autores — núcleo: salvamento, utilidades, som, pintura 2D
// ============================================================
const V3 = '0.170.0';
const INK = '#221a2b', INKHEX = 0x221a2b;
const SAVE_BASE = 'vila-autores-v2';
let SAVE_KEY = SAVE_BASE, DRAW_KEY = SAVE_BASE + '-desenho';
const $ = (s, r = document) => r.querySelector(s);
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const rnd = (a = 1, b) => (b === undefined ? Math.random() * a : a + Math.random() * (b - a));
const pick = (a) => a[Math.floor(Math.random() * a.length)];
const uid = () => Math.random().toString(36).slice(2, 9) + Date.now().toString(36).slice(-4);
function seeded(seed) { let s = (seed * 2654435761) >>> 0 || 1; return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }
function slug(t) { return String(t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 30) || 'turma'; }

function h(tag, a, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(a || {})) {
    if (v === false || v == null) continue;
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else if (k === 'style') e.style.cssText = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v === true ? '' : v);
  }
  for (const c of kids.flat(3)) { if (c == null || c === false) continue; e.append(c.nodeType ? c : document.createTextNode(String(c))); }
  return e;
}

// ---------- salvamento no aparelho (um espaço por código de aluno) ----------
function defSave() {
  return { v: 2, nome: '', turma: '', charKey: 'lia', inv: {}, seen: {}, tut: 0, flags: {}, found: {}, visited: {}, selos: {},
    ideas: [], placed: [], season: 'auto', mute: false, voz: false, area: 'vila', x: 0, z: 25, coletiva: { flor: 0, fita: 0, graveto: 0 },
    cartas: [], wearing: null, nomePers: '', crafts: 0, cd: {},
    titulo: '', frase: '', hist: {}, missoes: {}, codigo: '', vid: '', turmaId: '', colegio: '', tituloLivro: '', livroDesenhos: [], desenhoSlot: null, desenhoCrop: null, figSig: '', figV: 0, figAprov: '', salvoEm: 0 };
}
function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function lsSet(k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } }
function lsDel(k) { try { localStorage.removeItem(k); } catch (e) {} }
let S = defSave(), DRAWING = null;
function useSlot(codigo) {
  SAVE_KEY = codigo ? SAVE_BASE + ':' + codigo : SAVE_BASE; DRAW_KEY = codigo ? SAVE_KEY + ':desenho' : SAVE_BASE + '-desenho';
  S = defSave(); const raw = lsGet(SAVE_KEY); if (raw) { try { S = Object.assign(defSave(), JSON.parse(raw)); } catch (e) {} }
  DRAWING = lsGet(DRAW_KEY);
}
useSlot(null);
let _st = 0;
function save() { S.salvoEm = Date.now(); clearTimeout(_st); _st = setTimeout(() => lsSet(SAVE_KEY, JSON.stringify(S)), 250); aoSalvar(); }
function saveDrawing(url) {
  DRAWING = url; if (!url) { lsDel(DRAW_KEY); return; }
  if (lsSet(DRAW_KEY, url)) return;
  // aparelho da escola cheio: apaga desenhos guardados de outras crianças e tenta de novo
  try { const ks = []; for (let i = 0; i < localStorage.length; i++) { const k = localStorage.key(i); if (k && k !== DRAW_KEY && /desenho$/.test(k) && k.startsWith(SAVE_BASE)) ks.push(k); } ks.forEach(lsDel); } catch (e) {}
  lsSet(DRAW_KEY, url);
}
function cooldown(key, sec) { const now = Date.now(); if ((S.cd[key] || 0) > now) return Math.ceil((S.cd[key] - now) / 1000); S.cd[key] = now + sec * 1000; save(); return 0; }

// ---------- sons gerados no navegador ----------
const Snd = {
  ctx: null, out: null, fireTimer: 0,
  ensure() {
    if (this.ctx) { if (this.ctx.state === 'suspended') this.ctx.resume().catch(() => {}); return; }
    try { const C = window.AudioContext || window.webkitAudioContext; this.ctx = new C(); this.out = this.ctx.createGain(); this.out.gain.value = S.mute ? 0 : 0.55; this.out.connect(this.ctx.destination); } catch (e) { this.ctx = null; }
  },
  setMute(m) { S.mute = m; save(); if (this.out) this.out.gain.value = m ? 0 : 0.55; },
  tone(f, d = 0.15, type = 'sine', v = 0.25, delay = 0, f2 = 0) {
    const c = this.ctx; if (!c || S.mute) return;
    const t = c.currentTime + delay, o = c.createOscillator(), g = c.createGain();
    o.type = type; o.frequency.setValueAtTime(f, t); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t + d);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(v, t + 0.012); g.gain.exponentialRampToValueAtTime(0.0001, t + d);
    o.connect(g); g.connect(this.out); o.start(t); o.stop(t + d + 0.05);
  },
  noise(d = 0.2, v = 0.2, freq = 1500, delay = 0, q = 1) {
    const c = this.ctx; if (!c || S.mute) return;
    const t = c.currentTime + delay, n = Math.max(1, Math.floor(c.sampleRate * d)), b = c.createBuffer(1, n, c.sampleRate), a = b.getChannelData(0);
    for (let i = 0; i < n; i++) a[i] = (Math.random() * 2 - 1) * (1 - i / n);
    const s = c.createBufferSource(); s.buffer = b; const fl = c.createBiquadFilter(); fl.type = 'bandpass'; fl.frequency.value = freq; fl.Q.value = q;
    const g = c.createGain(); g.gain.value = v; s.connect(fl); fl.connect(g); g.connect(this.out); s.start(t);
  },
  pickup() { this.tone(880, 0.09, 'triangle', 0.22); this.tone(1320, 0.14, 'triangle', 0.18, 0.06); },
  gold() { [988, 1319, 1568, 1976].forEach((f, i) => this.tone(f, 0.25, 'sine', 0.16, i * 0.07)); },
  craft() { [523, 659, 784, 1047].forEach((f, i) => this.tone(f, 0.18, 'triangle', 0.2, i * 0.07)); this.noise(0.35, 0.1, 6000, 0.28, 0.7); this.tone(1568, 0.6, 'sine', 0.12, 0.32); },
  pop() { this.tone(420, 0.09, 'sine', 0.25, 0, 900); },
  click() { this.tone(700, 0.04, 'square', 0.05); },
  door() { this.noise(0.45, 0.16, 500, 0, 0.6); this.tone(190, 0.25, 'sine', 0.12, 0, 120); },
  bell() { [1046, 2093, 3136].forEach((f, i) => this.tone(f, 1.8 - i * 0.4, 'sine', 0.2 / (i + 1))); },
  note(i) { const sc = [523.25, 587.33, 659.25, 783.99, 880, 1046.5]; const f = sc[i % sc.length]; this.tone(f, 0.55, 'triangle', 0.25); this.tone(f * 2, 0.3, 'sine', 0.06); },
  lever() { this.tone(150, 0.12, 'square', 0.1, 0, 90); this.noise(0.14, 0.25, 900, 0.02); this.tone(300, 0.08, 'square', 0.06, 0.28); this.noise(0.6, 0.08, 3200, 0.32, 0.5); },
  page() { this.noise(0.22, 0.2, 2600, 0, 0.4); },
  tick() { this.tone(2000, 0.03, 'square', 0.05); this.tone(1500, 0.03, 'square', 0.05, 0.5); },
  chime(n) { for (let i = 0; i < n; i++) { this.tone(659, 0.8, 'sine', 0.14, i * 0.45); this.tone(988, 0.5, 'sine', 0.05, i * 0.45); } },
  fanfare() { [523, 659, 784, 1047, 784, 1047].forEach((f, i) => this.tone(f, i === 5 ? 0.7 : 0.16, 'square', 0.08, i * 0.12)); this.noise(0.6, 0.1, 5000, 0.62, 0.5); },
  whoosh() { this.noise(0.35, 0.14, 800, 0, 0.4); },
  nope() { this.tone(320, 0.12, 'triangle', 0.18, 0, 200); },
  chirp() { const f = rnd(2400, 3400); this.tone(f, 0.07, 'sine', 0.045, 0, f * 1.3); this.tone(f * 1.1, 0.07, 'sine', 0.035, 0.11, f * 1.4); },
  step() { this.noise(0.04, 0.035, 700, 0, 1.5); },
  fire(on) { clearInterval(this.fireTimer); if (on) this.fireTimer = setInterval(() => { if (typeof GAME !== 'undefined' && GAME.area === 'pena') this.noise(0.04 + Math.random() * 0.06, 0.04 + Math.random() * 0.08, 1800 + Math.random() * 2200, 0, 0.8); }, 150); },
};

// ---------- pintura 2D com contorno de nanquim ----------
function mkCanvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
function painter(g) {
  g.lineJoin = 'round'; g.lineCap = 'round'; g.strokeStyle = INK; if (g.lineWidth === 1) g.lineWidth = 3;
  const P = {
    ns: false, g,
    fs(f) { if (f) { g.fillStyle = f; g.fill(); } if (!P.ns) g.stroke(); },
    c(x, y, r, f) { g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); P.fs(f); },
    e(x, y, rx, ry, rot, f) { g.beginPath(); g.ellipse(x, y, rx, ry, rot || 0, 0, Math.PI * 2); P.fs(f); },
    r(x, y, w, hh, rad, f) { g.beginPath(); g.roundRect(x, y, w, hh, rad); P.fs(f); },
    p(pts, f) { g.beginPath(); g.moveTo(pts[0], pts[1]); for (let i = 2; i < pts.length; i += 2) g.lineTo(pts[i], pts[i + 1]); g.closePath(); P.fs(f); },
    l(pts, w, col) { g.save(); if (w) g.lineWidth = w; if (col) g.strokeStyle = col; g.beginPath(); g.moveTo(pts[0], pts[1]); for (let i = 2; i < pts.length; i += 2) g.lineTo(pts[i], pts[i + 1]); g.stroke(); g.restore(); },
    il(pts, w, col) { P.l(pts, w + 5, INK); P.l(pts, w, col); },
    blob(cx, cy, rx, ry, seed, f, j = 0.07) {
      const R = seeded(seed), n = 16, pts = [];
      for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2, k = 1 + (R() - 0.5) * j * 2; pts.push([cx + Math.cos(a) * rx * k, cy + Math.sin(a) * ry * k]); }
      g.beginPath(); g.moveTo((pts[0][0] + pts[n - 1][0]) / 2, (pts[0][1] + pts[n - 1][1]) / 2);
      for (let i = 0; i < n; i++) { const p = pts[i], q = pts[(i + 1) % n]; g.quadraticCurveTo(p[0], p[1], (p[0] + q[0]) / 2, (p[1] + q[1]) / 2); }
      g.closePath(); P.fs(f);
    },
    t(txt, x, y, size, col, weight = 800, font = 'Grandstander') { g.save(); g.font = `${weight} ${size}px ${font}, 'Trebuchet MS', sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = col || INK; g.fillText(txt, x, y); g.restore(); },
    star(x, y, r, f) { const pts = []; for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2 - Math.PI / 2, rr = i % 2 ? r * 0.38 : r; pts.push(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } P.p(pts, f); },
  };
  return P;
}
function silhouette(src, color) { const c = mkCanvas(src.width, src.height), g = c.getContext('2d'); g.drawImage(src, 0, 0); g.globalCompositeOperation = 'source-in'; g.fillStyle = color; g.fillRect(0, 0, c.width, c.height); return c; }
function stickerize(src, white = 7, black = 4) {
  const pad = Math.ceil(white + black + 3), c = mkCanvas(src.width + pad * 2, src.height + pad * 2), g = c.getContext('2d');
  const dil = (img, r) => { for (let rr = r; rr > 0.5; rr -= 2) { const n = Math.max(8, Math.ceil(rr * 3.4)); for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2; g.drawImage(img, pad + Math.cos(a) * rr, pad + Math.sin(a) * rr); } } g.drawImage(img, pad, pad); };
  dil(silhouette(src, INK), white + black); dil(silhouette(src, '#ffffff'), white); g.drawImage(src, pad, pad);
  return c;
}
function fitCanvas(src, maxW, maxH) {
  const sw = src.width || src.naturalWidth, sh = src.height || src.naturalHeight, k = Math.min(1, maxW / sw, maxH / sh);
  const c = mkCanvas(Math.max(1, Math.round(sw * k)), Math.max(1, Math.round(sh * k))); const g = c.getContext('2d'); g.imageSmoothingQuality = 'high'; g.drawImage(src, 0, 0, c.width, c.height); return c;
}
function cropAlpha(c) {
  const g = c.getContext('2d'), d = g.getImageData(0, 0, c.width, c.height).data; let x0 = c.width, y0 = c.height, x1 = -1, y1 = -1;
  for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) if (d[(y * c.width + x) * 4 + 3] > 20) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  if (x1 < x0 || (x1 - x0) < 8 || (y1 - y0) < 8) return c;
  const o = mkCanvas(x1 - x0 + 1, y1 - y0 + 1); o.getContext('2d').drawImage(c, -x0, -y0); return o;
}
// Recorta o fundo do papel a partir das bordas (flood fill), mantendo brancos internos do desenho.
function removePaper(src) {
  const c = fitCanvas(src, 340, 400), g = c.getContext('2d'), W = c.width, H = c.height, id = g.getImageData(0, 0, W, H), d = id.data;
  let br = 0, bg = 0, bb = 0, n = 0;
  const acc = (x, y) => { const i = (y * W + x) * 4; br += d[i]; bg += d[i + 1]; bb += d[i + 2]; n++; };
  for (let x = 0; x < W; x += 3) { acc(x, 0); acc(x, H - 1); } for (let y = 0; y < H; y += 3) { acc(0, y); acc(W - 1, y); }
  br /= n; bg /= n; bb /= n;
  const isBg = (i) => { const r = d[i], gg = d[i + 1], b = d[i + 2], dr = r - br, dg = gg - bg, db = b - bb; if (dr * dr + dg * dg + db * db < 62 * 62) return true; const mx = Math.max(r, gg, b), mn = Math.min(r, gg, b); return (r + gg + b) / 3 > 200 && mx - mn < 38; };
  const seen = new Uint8Array(W * H), st = [];
  const push = (x, y) => { const k = y * W + x; if (seen[k]) return; seen[k] = 1; if (isBg(k * 4)) st.push(k); };
  for (let x = 0; x < W; x++) { push(x, 0); push(x, H - 1); } for (let y = 0; y < H; y++) { push(0, y); push(W - 1, y); }
  while (st.length) { const k = st.pop(); d[k * 4 + 3] = 0; const x = k % W, y = (k / W) | 0; if (x > 0) push(x - 1, y); if (x < W - 1) push(x + 1, y); if (y > 0) push(x, y - 1); if (y < H - 1) push(x, y + 1); }
  // suaviza a franja: pixel opaco ao lado de fundo fica meio transparente
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) { const k = y * W + x; if (d[k * 4 + 3] && (!d[(k - 1) * 4 + 3] || !d[(k + 1) * 4 + 3] || !d[(k - W) * 4 + 3] || !d[(k + W) * 4 + 3]) && isBg(k * 4)) d[k * 4 + 3] = 0; }
  g.putImageData(id, 0, 0); return cropAlpha(c);
}
function loadImg(url) { return new Promise((res, rej) => { const im = new Image(); if (!/^(data|blob):/.test(url)) im.crossOrigin = 'anonymous'; im.onload = () => res(im); im.onerror = rej; im.src = url; }); }
async function loadImgCanvas(url) { const im = await loadImg(url); const c = mkCanvas(im.naturalWidth, im.naturalHeight); c.getContext('2d').drawImage(im, 0, 0); return c; }

// ---------- personagens de exemplo (traço de giz de cera) ----------
function drawLia(P) {
  P.il([84, 214, 82, 244], 9, '#f4b38a'); P.il([116, 214, 119, 244], 9, '#f4b38a');
  P.e(78, 248, 15, 8, 0, '#e23b5a'); P.e(124, 248, 15, 8, 0, '#e23b5a');
  P.il([82, 146, 52, 184], 9, '#f4b38a'); P.il([118, 146, 150, 180], 9, '#f4b38a');
  P.blob(100, 176, 44, 46, 4, '#ff8a3c', 0.05); P.p([58, 220, 142, 220, 124, 150, 76, 150], '#ff8a3c');
  P.ns = true; [[86, 186], [110, 200], [98, 168], [122, 178], [78, 206]].forEach(([x, y]) => P.c(x, y, 4, '#ffd23f')); P.ns = false;
  P.blob(100, 84, 54, 48, 3, '#6b3a1f', 0.12);
  P.blob(100, 94, 40, 38, 7, '#f7c39a', 0.04);
  P.blob(100, 62, 38, 14, 5, '#6b3a1f', 0.1);
  P.ns = true; P.c(84, 98, 5, INK); P.c(116, 98, 5, INK); P.c(78, 110, 6, '#ff9aa8'); P.c(122, 110, 6, '#ff9aa8'); P.ns = false;
  P.g.beginPath(); P.g.arc(100, 106, 11, 0.2, Math.PI - 0.2); P.g.stroke();
  P.p([70, 52, 76, 28, 89, 44, 100, 22, 111, 44, 124, 28, 130, 52], '#ffd23f');
  P.ns = true; P.c(100, 40, 4, '#ff4f6d'); P.ns = false;
}
function drawDino(P) {
  P.p([150, 200, 196, 172, 160, 214], '#5ccf6a');
  P.e(74, 244, 18, 9, 0, '#3f9e4c'); P.e(128, 244, 18, 9, 0, '#3f9e4c');
  P.p([60, 120, 22, 92, 40, 150], '#a77bff'); P.p([140, 120, 178, 92, 160, 150], '#a77bff');
  P.blob(100, 180, 56, 62, 9, '#5ccf6a', 0.05);
  P.blob(100, 196, 32, 38, 2, '#fff0a8', 0.05);
  [[74, 58], [100, 44], [126, 58]].forEach(([x, y]) => P.p([x - 10, y + 14, x, y - 6, x + 10, y + 14], '#ffb13b'));
  P.blob(100, 96, 50, 44, 6, '#5ccf6a', 0.05);
  P.c(80, 92, 13, '#fff'); P.c(120, 92, 13, '#fff'); P.ns = true; P.c(83, 94, 6, INK); P.c(117, 94, 6, INK); P.ns = false;
  P.g.beginPath(); P.g.arc(100, 112, 16, 0.25, Math.PI - 0.25); P.g.stroke();
  P.ns = true; P.c(90, 118, 3, INK); P.c(110, 118, 3, INK); P.ns = false;
  P.il([62, 168, 38, 188], 9, '#5ccf6a'); P.il([138, 168, 162, 188], 9, '#5ccf6a');
}
function drawMiau(P) {
  P.e(74, 246, 17, 9, 0, '#8a7bd6'); P.e(126, 246, 17, 9, 0, '#8a7bd6');
  P.r(52, 170, 26, 50, 10, '#c4c9d6');
  P.blob(100, 196, 46, 46, 11, '#f4f6fb', 0.04);
  P.r(84, 182, 32, 22, 6, '#ff6f91'); P.ns = true; P.c(92, 193, 3, '#fff'); P.c(108, 193, 3, '#ffd23f'); P.ns = false;
  P.il([58, 186, 40, 214], 10, '#f4f6fb'); P.il([142, 186, 160, 210], 10, '#f4f6fb');
  P.p([62, 74, 70, 34, 92, 64], '#ffa24a'); P.p([138, 74, 130, 34, 108, 64], '#ffa24a');
  P.blob(100, 98, 44, 40, 8, '#ffa24a', 0.04);
  P.ns = true; P.c(84, 96, 5, INK); P.c(116, 96, 5, INK); P.p([94, 108, 106, 108, 100, 115], '#ff6f91'); P.ns = false;
  P.l([60, 108, 82, 112], 3); P.l([60, 118, 82, 116], 3); P.l([140, 108, 118, 112], 3); P.l([140, 118, 118, 116], 3);
  P.g.save(); P.g.globalAlpha = 0.28; P.c(100, 96, 66, '#bfe8ff'); P.g.restore();
  P.ns = true; P.g.save(); P.g.globalAlpha = 0.7; P.e(72, 64, 12, 6, -0.7, '#fff'); P.g.restore(); P.ns = false;
}
function drawBip(P) {
  P.c(76, 244, 13, '#4a4f63'); P.c(124, 244, 13, '#4a4f63');
  P.r(58, 150, 84, 86, 14, '#59b7ff');
  P.r(80, 168, 40, 32, 8, '#e8f6ff'); P.ns = true; P.c(94, 182, 7, '#ff4f6d'); P.c(106, 182, 7, '#ff4f6d'); P.p([88, 185, 112, 185, 100, 198], '#ff4f6d'); P.ns = false;
  P.il([58, 168, 30, 150, 22, 124], 8, '#9aa3b8'); P.il([142, 168, 170, 186, 180, 210], 8, '#9aa3b8');
  P.il([100, 54, 100, 30], 5, '#9aa3b8'); P.c(100, 26, 8, '#ffd23f');
  P.r(52, 56, 96, 82, 18, '#9fd9ff');
  P.r(66, 74, 68, 40, 10, '#2b2d42'); P.ns = true; P.c(86, 94, 8, '#7dffb0'); P.c(114, 94, 8, '#7dffb0'); P.ns = false;
  P.l([84, 124, 116, 124], 4);
}
const SAMPLES = { lia: { nome: 'Lia', draw: drawLia }, dino: { nome: 'Dino', draw: drawDino }, miau: { nome: 'Miau', draw: drawMiau }, bip: { nome: 'Bip', draw: drawBip } };
const _sampleCache = {};
function sampleSticker(k) {
  if (_sampleCache[k]) return _sampleCache[k];
  const c = mkCanvas(200, 262), g = c.getContext('2d'); g.lineWidth = 4.5; const P = painter(g); g.lineWidth = 4.5; (SAMPLES[k] || SAMPLES.lia).draw(P);
  return (_sampleCache[k] = stickerize(cropAlpha(c)));
}

// ---------- Pena, a guia ----------
function drawPena(scarf = '#ff7aa8', stripes = false) {
  const c = mkCanvas(210, 250), g = c.getContext('2d'); g.lineWidth = 4.5; const P = painter(g); g.lineWidth = 4.5;
  P.il([84, 206, 80, 236], 6, '#ff9f1c'); P.il([116, 206, 120, 236], 6, '#ff9f1c');
  P.l([70, 238, 90, 238], 5, '#ff9f1c'); P.l([110, 238, 130, 238], 5, '#ff9f1c');
  P.e(42, 150, 17, 36, 0.35, '#3b8fe6'); P.e(158, 150, 17, 36, -0.35, '#3b8fe6');
  P.blob(100, 142, 66, 72, 11, '#4fa8ff', 0.04);
  P.blob(100, 166, 38, 42, 4, '#d7f0ff', 0.04);
  P.r(52, 118, 96, 20, 10, scarf); P.p([118, 134, 136, 134, 140, 172, 122, 168], scarf);
  if (stripes) { P.ns = true; for (let x = 62; x < 146; x += 16) P.r(x, 120, 6, 16, 2, '#ffffff'); P.ns = false; }
  P.c(78, 90, 18, '#fff'); P.c(122, 90, 18, '#fff');
  P.ns = true; P.c(82, 93, 8, INK); P.c(118, 93, 8, INK); P.c(85, 89, 3, '#fff'); P.c(121, 89, 3, '#fff'); P.c(66, 112, 7, '#ff9aa8'); P.c(134, 112, 7, '#ff9aa8'); P.ns = false;
  g.save(); g.lineWidth = 3.5; g.beginPath(); g.arc(78, 90, 22, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.arc(122, 90, 22, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.moveTo(100, 88); g.lineTo(100, 88); g.stroke(); g.restore();
  P.l([96, 86, 104, 86], 3.5);
  P.p([88, 104, 112, 104, 100, 122], '#ff9f1c');
  P.e(128, 40, 12, 34, 0.55, '#ffffff'); P.l([116, 62, 140, 18], 3); P.p([112, 66, 118, 60, 108, 78], '#3b3355');
  return stickerize(cropAlpha(c));
}

// ---------- ícones dos itens (desenhados com contorno) ----------
const ICON_DRAW = {
  flor: (P) => { P.il([32, 60, 32, 38], 4, '#3c9a3c'); P.e(41, 50, 7, 3.5, -0.5, '#5cc05a'); for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2 - Math.PI / 2; P.c(32 + Math.cos(a) * 10, 26 + Math.sin(a) * 10, 8, '#ff8fb8'); } P.c(32, 26, 6.5, '#ffd23f'); },
  folha: (P) => { P.e(32, 32, 23, 11, -0.7, '#6cc657'); P.l([15, 48, 47, 17], 2.5); },
  dourada: (P) => { P.e(30, 34, 22, 11, -0.7, '#ffc928'); P.l([14, 50, 45, 19], 2.5); P.star(50, 14, 9, '#fffbe0'); P.star(14, 18, 5, '#fffbe0'); },
  folhaColorida: (P) => { P.e(26, 36, 18, 9, -0.9, '#e0502a'); P.e(38, 28, 19, 10, -0.5, '#f2832c'); P.l([16, 52, 50, 14], 2.5); },
  graveto: (P) => { P.il([12, 50, 52, 16], 6, '#8b5a2b'); P.il([34, 32, 40, 14], 4, '#8b5a2b'); },
  papel: (P) => { P.p([14, 16, 46, 10, 52, 50, 20, 56], '#fffdf5'); P.l([22, 24, 42, 20], 2.5, '#6ec6ff'); P.l([24, 33, 44, 29], 2.5, '#6ec6ff'); P.l([25, 42, 40, 39], 2.5, '#6ec6ff'); },
  tinta: (P) => { P.r(18, 22, 28, 34, 7, '#e8f6ff'); P.r(21, 34, 22, 19, 5, '#4a7dff'); P.r(15, 14, 34, 10, 4, '#ff6b6b'); },
  fita: (P) => { P.e(20, 28, 13, 9, -0.4, '#ff4f6d'); P.e(44, 28, 13, 9, 0.4, '#ff4f6d'); P.p([28, 34, 20, 56, 30, 50], '#ff4f6d'); P.p([36, 34, 46, 54, 34, 50], '#ff4f6d'); P.c(32, 30, 6, '#ff8aa0'); },
  botao: (P) => { P.c(32, 32, 21, '#38c6c0'); P.c(32, 32, 14, '#5ad9d2'); P.ns = true; [[27, 27], [37, 27], [27, 37], [37, 37]].forEach(([x, y]) => P.c(x, y, 3, INK)); P.ns = false; },
  concha: (P) => { P.g.beginPath(); P.g.moveTo(32, 54); P.g.lineTo(10, 30); P.g.arc(32, 30, 22, Math.PI, 0); P.g.closePath(); P.fs('#ffb3c7'); for (let i = 0; i < 5; i++) { const a = Math.PI + (i + 0.5) * (Math.PI / 5); P.l([32, 52, 32 + Math.cos(a) * 20, 30 + Math.sin(a) * 20], 2.2); } P.r(26, 50, 12, 8, 3, '#ffd0dc'); },
  pedra: (P) => { P.p([12, 44, 18, 24, 34, 16, 50, 24, 54, 42, 40, 52, 22, 52], '#a9a6b8'); P.ns = true; P.e(28, 28, 6, 3, -0.4, '#d7d5e2'); P.ns = false; },
  semente: (P) => { P.e(25, 36, 9, 14, 0.4, '#a8692e'); P.e(41, 30, 8, 13, -0.4, '#c48542'); P.l([41, 22, 41, 34], 2); },
  agua: (P) => { const g = P.g; g.beginPath(); g.moveTo(32, 8); g.bezierCurveTo(40, 22, 48, 30, 48, 40); g.arc(32, 40, 16, 0, Math.PI); g.bezierCurveTo(16, 30, 24, 22, 32, 8); g.closePath(); P.fs('#5ab8ff'); P.ns = true; P.e(26, 40, 4, 7, 0.3, '#d6efff'); P.ns = false; },
  algodao: (P) => { P.c(22, 36, 12, '#fff'); P.c(42, 36, 12, '#fff'); P.c(32, 24, 13, '#fff'); P.c(32, 42, 11, '#fff'); },
  areia: (P) => { P.g.beginPath(); P.g.moveTo(6, 50); P.g.quadraticCurveTo(32, 6, 58, 50); P.g.closePath(); P.fs('#f3d48b'); P.ns = true; [[24, 40], [34, 32], [40, 44], [30, 46]].forEach(([x, y]) => P.c(x, y, 2, '#c9a353')); P.ns = false; },
  ideia: (P) => { P.c(32, 26, 16, '#fff3a0'); P.r(24, 40, 16, 12, 3, '#c4c9d6'); P.l([26, 46, 38, 46], 2); P.l([32, 4, 32, 0], 3); P.l([10, 14, 6, 10], 3); P.l([54, 14, 58, 10], 3); P.l([28, 30, 32, 22, 36, 30], 2.5, '#ff9f1c'); },
  desenho: (P) => { P.r(10, 10, 44, 44, 4, '#fffdf5'); P.ns = true; P.c(40, 22, 6, '#ffd23f'); P.ns = false; P.p([18, 44, 28, 32, 38, 44], '#ff6f91'); P.l([12, 46, 52, 46], 2.5, '#5cc05a'); },
  capa: (P) => { P.r(12, 8, 40, 48, 5, '#d9ccff'); P.l([20, 8, 20, 56], 3); P.r(26, 18, 20, 8, 2, '#fff'); },
  nomePers: (P) => { P.r(6, 18, 52, 28, 8, '#fff'); P.c(14, 32, 3, '#ff6f91'); P.t('Aa', 36, 33, 18, INK, 900); },
  pagina: (P) => { P.r(12, 6, 40, 52, 4, '#fffdf5'); P.r(17, 11, 30, 22, 3, '#bfe8ff'); P.ns = true; P.c(39, 18, 4, '#ffd23f'); P.ns = false; P.p([19, 31, 27, 22, 35, 31], '#5cc05a'); P.l([18, 40, 46, 40], 2.5); P.l([18, 47, 40, 47], 2.5); },
  guirlanda: (P) => { P.g.save(); P.g.lineWidth = 15; P.g.beginPath(); P.g.arc(32, 30, 19, 0, Math.PI * 2); P.g.stroke(); P.g.lineWidth = 9; P.g.strokeStyle = '#4fae4c'; P.g.stroke(); P.g.restore(); P.ns = true; [[18, 20], [46, 22], [32, 11], [14, 38], [50, 38]].forEach(([x, y], i) => P.c(x, y, 4, i % 2 ? '#ff8fb8' : '#ffd23f')); P.ns = false; P.p([24, 50, 32, 46, 30, 58], '#ff4f6d'); P.p([40, 50, 32, 46, 34, 58], '#ff4f6d'); P.c(32, 47, 4, '#ff4f6d'); },
  selo: (P) => { const pts = []; for (let i = 0; i < 20; i++) { const a = (i / 20) * Math.PI * 2, r = i % 2 ? 19 : 23; pts.push(32 + Math.cos(a) * r, 32 + Math.sin(a) * r); } P.p(pts, '#d6334a'); P.c(32, 32, 14, '#e8495e'); P.star(32, 32, 9, '#ffd23f'); },
  marcador: (P) => { P.p([22, 4, 42, 4, 42, 56, 32, 48, 22, 56], '#7a5cff'); P.c(32, 18, 6, '#38c6c0'); P.il([32, 4, 30, 0], 2, '#ff4f6d'); P.l([26, 30, 38, 30], 2.5, '#fff'); },
  enfeiteJanela: (P) => { P.il([8, 10, 56, 10], 4, '#8b5a2b'); [[16, 30, 'concha'], [32, 40, 'pedra'], [48, 30, 'concha']].forEach(([x, y, k]) => { P.l([x, 10, x, y - 7], 2); if (k === 'concha') P.e(x, y, 7, 6, 0, '#ffb3c7'); else P.c(x, y, 7, '#a9a6b8'); }); },
  florPlantada: (P) => { P.p([16, 38, 48, 38, 43, 58, 21, 58], '#d9774a'); P.r(13, 34, 38, 7, 3, '#e98a5c'); P.il([32, 34, 32, 18], 3.5, '#3c9a3c'); P.e(24, 26, 6, 3, 0.5, '#5cc05a'); for (let i = 0; i < 5; i++) { const a = (i / 5) * Math.PI * 2; P.c(32 + Math.cos(a) * 7, 13 + Math.sin(a) * 7, 5.5, '#ffd23f'); } P.c(32, 13, 4, '#ff8a3c'); },
  capaLivro: (P) => { P.r(12, 6, 40, 52, 5, '#ff6f91'); P.l([18, 6, 18, 58], 3); P.r(24, 14, 22, 20, 4, '#fff'); P.ns = true; P.c(35, 24, 5, '#ffd23f'); P.ns = false; P.r(24, 40, 22, 6, 2, '#fff'); },
  miniLivro: (P) => { P.r(8, 16, 46, 36, 5, '#ffd23f'); P.r(12, 46, 42, 8, 2, '#fffdf5'); P.l([20, 16, 20, 52], 3); P.r(28, 24, 18, 10, 2, '#fff'); P.il([42, 16, 42, 60], 3, '#ff4f6d'); },
  buque: (P) => { P.e(22, 22, 8, 16, -0.4, '#e0502a'); P.e(32, 18, 8, 17, 0, '#ffb13b'); P.e(42, 22, 8, 16, 0.4, '#f2832c'); P.p([22, 34, 42, 34, 36, 58, 28, 58], '#c98b4f'); P.r(22, 40, 20, 6, 2, '#ff4f6d'); },
  bonecoNeve: (P) => { P.c(32, 44, 15, '#fff'); P.c(32, 22, 11, '#fff'); P.r(22, 4, 20, 10, 2, INK); P.r(18, 12, 28, 4, 2, INK); P.ns = true; P.c(28, 20, 2, INK); P.c(36, 20, 2, INK); P.ns = false; P.p([32, 24, 42, 26, 32, 28], '#ff8a3c'); P.r(20, 30, 24, 6, 3, '#ff4f6d'); P.ns = true; P.c(32, 42, 2.5, '#38c6c0'); P.c(32, 50, 2.5, '#38c6c0'); P.ns = false; },
  coroa: (P) => { P.e(32, 40, 24, 10, 0, null); P.g.save(); P.g.lineWidth = 7; P.g.strokeStyle = '#4fae4c'; P.g.beginPath(); P.g.ellipse(32, 40, 24, 10, 0, 0, Math.PI * 2); P.g.stroke(); P.g.restore(); [[12, 36, '#ff8fb8'], [24, 30, '#ffd23f'], [36, 29, '#a77bff'], [48, 34, '#ff8fb8'], [30, 50, '#ffd23f']].forEach(([x, y, c]) => P.c(x, y, 6, c)); },
  lembrancinha: (P) => { P.r(16, 18, 32, 40, 8, '#e8f6ff'); P.r(19, 38, 26, 17, 5, '#f3d48b'); P.e(30, 34, 6, 5, 0, '#ffb3c7'); P.r(13, 10, 38, 9, 4, '#38c6c0'); },
};
const _iconCache = {};
function iconURL(k) {
  if (_iconCache[k]) return _iconCache[k];
  const c = mkCanvas(128, 128), g = c.getContext('2d'); g.scale(2, 2); g.lineWidth = 3; const P = painter(g); g.lineWidth = 3;
  try { (ICON_DRAW[k] || ICON_DRAW.ideia)(P); } catch (e) { console.warn(k, e); }
  return (_iconCache[k] = c.toDataURL());
}

// ---------- textos da vila ----------
const IDEIAS = {
  personagem: ['uma tartaruga que quer voar', 'um robô que tem medo do escuro', 'uma menina que conversa com as nuvens', 'um dragão que adora sopa', 'um gato detetive', 'uma árvore que anda', 'um pinguim que mora no deserto', 'uma bruxinha que esqueceu as mágicas', 'um menino que coleciona sons', 'uma formiga muito forte', 'um dinossauro tímido', 'uma estrela que caiu no quintal', 'um sapo que sonha ser cantor', 'uma avó astronauta'],
  lugar: ['numa ilha de chocolate', 'no fundo do mar', 'numa cidade nas nuvens', 'dentro de um livro gigante', 'numa escola de monstros', 'na praia de Boa Viagem', 'numa floresta encantada', 'num trem que nunca para', 'na Lua', 'num castelo de areia', 'no sertão, numa noite de São João', 'numa biblioteca mágica', 'no Marco Zero, em dia de frevo', 'dentro de uma geladeira'],
  problema: ['perdeu a chave do arco-íris', 'precisa encontrar um amigo perdido', 'quer ganhar um concurso de bolos', 'tem que salvar a festa da vila', 'descobriu um mapa misterioso', 'não consegue parar de espirrar purpurina', 'precisa devolver um ovo ao ninho', 'tem medo de altura mas precisa subir', 'ficou sem cores para pintar o mundo', 'ganhou um poder muito estranho', 'precisa acordar um gigante', 'esqueceu o próprio nome', 'encolheu do tamanho de um grão de feijão'],
};
const DICAS = ['Toda boa história tem começo, meio e fim.', 'Dê um nome bem especial para o seu personagem.', 'Conte o que o seu personagem mais quer na vida.', 'Use os cinco sentidos: qual é o cheiro desse lugar?', 'Um problema deixa a história emocionante!', 'Se quiser, desenhe primeiro. A ideia aparece no papel.', 'Leia sua história em voz alta para alguém da família.', 'Diálogos dão vida: o que os personagens dizem um para o outro?', 'Um final surpresa faz o leitor sorrir.', 'Releia e troque uma palavra sem graça por uma divertida.'];
const FIGURINHAS = ['Oi, turma! 👋', 'Terminei uma página! 📄', 'Achei uma folha dourada! ✨', 'Vamos criar juntos? 🔨', 'Amei a vila! 💛', 'Minha história tem um dragão! 🐉', 'Quem quer trocar presentes? 🎁', 'Já sou Autor(a)! 🏅', 'Visitei as 5 casas! 🧭'];
