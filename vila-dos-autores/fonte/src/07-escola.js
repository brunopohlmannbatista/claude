// ============================================================
// Vila dos Autores — escola: servidor (n8n), entrada pelo código do aluno,
// vozes da Pena, título e primeira frase, missões das casas, álbum
// ============================================================

// ---------- servidor ----------
const API = { base: 'https://roundrooster-n8n.cloudfy.live/webhook/', ok: null };
try { if (/^https?:$/.test(location.protocol) && /^\/webhook(-test)?\//.test(location.pathname)) API.base = location.protocol + '//' + location.host + '/webhook/'; } catch (e) {}
if (window.__vilaAPI) API.base = window.__vilaAPI;
async function apiPost(path, body, opts = {}) {
  const ctl = typeof AbortController === 'function' ? new AbortController() : null;
  const tm = ctl ? setTimeout(() => ctl.abort(), opts.timeout || 15000) : 0;
  try {
    const r = await fetch(API.base + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), keepalive: !!opts.keepalive, signal: ctl ? ctl.signal : undefined, cache: 'no-store', credentials: 'omit' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const j = await r.json(); API.ok = true; return j;
  } catch (e) { API.ok = false; throw e; } finally { if (tm) clearTimeout(tm); }
}
function apiURL(path, q) { return API.base + path + '?' + new URLSearchParams(q).toString(); }
function parseJSON(s, d) { try { const v = JSON.parse(s); return v == null ? d : v; } catch (e) { return d; } }
function hash32(s) { let x = 2166136261 >>> 0; for (let i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 16777619) >>> 0; } return x.toString(36); }

// ---------- as 20 falas gravadas da Pena (o texto na tela é igual ao áudio) ----------
const VOZES = {
  1: 'Oi! Que bom que você chegou na Vila dos Autores! Eu sou a Pena, a guardiã das histórias daqui.',
  2: 'Aqui cada criança é autora. E olha só: você veio com o personagem do seu próprio desenho!',
  3: 'Para andar, use as setas do teclado. No tablet, é só tocar no chão ou arrastar o dedo.',
  4: 'Primeira missão: junte três flores e um graveto aqui pela praça. É só passar por cima deles!',
  5: 'Você achou tudo! Agora vou te ensinar a criar coisas. Toque no martelinho e faça uma Guirlanda.',
  6: 'Uma guirlanda linda! Agora leve até a porta de uma casa e toque em Colocar para pendurar.',
  7: 'Ficou a cara da vila! Agora vou para casa preparar uma surpresa. Me encontre na Casa da Pena, a amarelinha de telhado vermelho!',
  8: 'Que bom ter você na minha casa! Aqui é onde as histórias começam.',
  9: 'Tenho quatro tarefas para você: guardar uma ideia no Caderno de Ideias, escrever o título e a primeira frase da sua história, acender a lareira e achar três folhas douradas que escondi por aqui.',
  10: 'Quando terminar, abra o Baú de Conquistas. Ah, e a Mesa de Criação já está liberada!',
  11: 'Que começo maravilhoso! Toda grande história nasce de uma primeira frase.',
  12: 'Você fez tudo! Corre lá no Baú de Conquistas, pertinho da porta!',
  13: 'Parabéns! Você ganhou o selo da Vila dos Autores!',
  14: 'As receitas do livro foram liberadas: a Página Ilustrada no Ateliê, e a Capa e o Mini-livro na Gráfica.',
  15: 'As outras casas têm missões novas para você. Eu volto para a praça e fico te esperando por lá!',
  16: 'Na Biblioteca, você vai descobrir quem é o seu personagem: do que ele mais gosta e do que tem medo.',
  17: 'No Ateliê, você escolhe onde a sua história acontece: as cores, os sons e os cheiros desse lugar.',
  18: 'Na Gráfica, a gente descobre o problema. Toda história fica emocionante quando alguma coisa dá errado!',
  19: 'No Correio, você escreve como a sua história termina e manda para quem vai ler.',
  20: 'Que história incrível! Personagem, cenário, problema e final: agora a sua história está completinha!',
};
const Voz = {
  cache: {}, cur: null,
  get(n) {
    const k = String(n).padStart(2, '0');
    if (!this.cache[k]) { const a = new Audio(); a.preload = 'auto'; a.src = apiURL('vila-voz', { n: k }); this.cache[k] = a; }
    return this.cache[k];
  },
  play(n) {
    this.stop(); if (S.mute) return;
    try { const a = this.get(n); a.currentTime = 0; a.volume = 0.95; const p = a.play(); if (p && p.catch) p.catch(() => {}); this.cur = a; } catch (e) {}
    this.preload([n + 1, n + 2]);
  },
  stop() { if (this.cur) { try { this.cur.pause(); } catch (e) {} this.cur = null; } },
  preload(list) { list.forEach((n) => { if (VOZES[n]) this.get(n); }); },
};
function falaTexto(l) { return typeof l === 'number' ? VOZES[l] || '' : String(l); }

// ---------- recorte do desenho do livro (tira papel, moldura e textinhos) ----------
function cutDrawing(src) {
  const c = fitCanvas(src, 560, 700), g = c.getContext('2d', { willReadFrequently: true }), W = c.width, H = c.height, N = W * H;
  const id = g.getImageData(0, 0, W, H), d = id.data;
  const rs = [], gs = [], bs = [];
  const take = (x, y) => { const i = (y * W + x) * 4; rs.push(d[i]); gs.push(d[i + 1]); bs.push(d[i + 2]); };
  for (let x = 0; x < W; x += 2) { take(x, 1); take(x, H - 2); } for (let y = 0; y < H; y += 2) { take(1, y); take(W - 2, y); }
  const med = (a) => a.sort((p, q) => p - q)[a.length >> 1]; const pr = med(rs), pgc = med(gs), pb = med(bs);
  const paper = new Uint8Array(N);
  for (let k = 0; k < N; k++) {
    const i = k * 4, r = d[i], gg = d[i + 1], b = d[i + 2], dr = r - pr, dg = gg - pgc, db = b - pb, mx = Math.max(r, gg, b), mn = Math.min(r, gg, b);
    paper[k] = dr * dr + dg * dg + db * db < 58 * 58 || ((r + gg + b) / 3 > 205 && mx - mn < 34) ? 1 : 0;
  }
  // traços de tinta: acha moldura da folha e linhas compridas e trata como papel
  const lab = new Int32Array(N).fill(-1), q = [];
  for (let k = 0; k < N; k++) {
    if (paper[k] || lab[k] >= 0) continue;
    let n = 0, x0 = W, y0 = H, x1 = 0, y1 = 0; const px = []; q.length = 0; q.push(k); lab[k] = k;
    while (q.length) { const j = q.pop(), x = j % W, y = (j / W) | 0; n++; px.push(j); if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
      if (x > 0 && !paper[j - 1] && lab[j - 1] < 0) { lab[j - 1] = k; q.push(j - 1); } if (x < W - 1 && !paper[j + 1] && lab[j + 1] < 0) { lab[j + 1] = k; q.push(j + 1); }
      if (y > 0 && !paper[j - W] && lab[j - W] < 0) { lab[j - W] = k; q.push(j - W); } if (y < H - 1 && !paper[j + W] && lab[j + W] < 0) { lab[j + W] = k; q.push(j + W); } }
    const bw = x1 - x0 + 1, bh = y1 - y0 + 1;
    const moldura = bw >= 0.7 * W && bh >= 0.7 * H && n < 0.12 * bw * bh;
    const linha = (bw >= 0.5 * W && bh <= 0.035 * H) || (bh >= 0.5 * H && bw <= 0.035 * W);
    if (moldura || linha) for (const j of px) paper[j] = 1;
  }
  // fundo = papel ligado às bordas
  const bg = new Uint8Array(N), st = [];
  const seed = (k) => { if (!bg[k] && paper[k]) { bg[k] = 1; st.push(k); } };
  for (let x = 0; x < W; x++) { seed(x); seed((H - 1) * W + x); } for (let y = 0; y < H; y++) { seed(y * W); seed(y * W + W - 1); }
  while (st.length) { const k = st.pop(), x = k % W, y = (k / W) | 0; if (x > 0) seed(k - 1); if (x < W - 1) seed(k + 1); if (y > 0) seed(k - W); if (y < H - 1) seed(k + W); }
  // ilhas: fica só o que tem tamanho de desenho (tira números, códigos e sujeirinhas)
  const isl = new Int32Array(N).fill(-1), sizes = [];
  for (let k = 0; k < N; k++) {
    if (bg[k] || isl[k] >= 0) continue; const ci = sizes.length; let n = 0; q.length = 0; q.push(k); isl[k] = ci;
    while (q.length) { const j = q.pop(), x = j % W, y = (j / W) | 0; n++;
      if (x > 0 && !bg[j - 1] && isl[j - 1] < 0) { isl[j - 1] = ci; q.push(j - 1); } if (x < W - 1 && !bg[j + 1] && isl[j + 1] < 0) { isl[j + 1] = ci; q.push(j + 1); }
      if (y > 0 && !bg[j - W] && isl[j - W] < 0) { isl[j - W] = ci; q.push(j - W); } if (y < H - 1 && !bg[j + W] && isl[j + W] < 0) { isl[j + W] = ci; q.push(j + W); } }
    sizes.push(n);
  }
  const big = sizes.length ? Math.max(...sizes) : 0;
  let tinta = 0;
  for (let k = 0; k < N; k++) { const ci = isl[k]; if (bg[k] || ci < 0 || sizes[ci] < big * 0.06) d[k * 4 + 3] = 0; else if (!paper[k]) tinta++; }
  if (big < N * 0.004 || tinta < N * 0.0025) return null;
  for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) { const k = y * W + x; if (d[k * 4 + 3] && paper[k] && (!d[(k - 1) * 4 + 3] || !d[(k + 1) * 4 + 3] || !d[(k - W) * 4 + 3] || !d[(k + W) * 4 + 3])) d[k * 4 + 3] = 0; }
  g.putImageData(id, 0, 0); return cropAlpha(c);
}
function placeholderSticker(nome) {
  const c = mkCanvas(180, 230), g = c.getContext('2d');
  g.fillStyle = '#fff8ec'; g.strokeStyle = INK; g.lineWidth = 7; g.beginPath(); g.roundRect(10, 10, 160, 210, 26); g.fill(); g.stroke();
  g.fillStyle = '#ffc93c'; g.beginPath(); g.arc(90, 92, 50, 0, 7); g.fill(); g.stroke();
  g.fillStyle = INK; g.font = '900 64px Grandstander, sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText((String(nome || '?').trim()[0] || '?').toUpperCase(), 90, 96);
  g.font = '800 22px Andika, sans-serif'; g.fillText('autor(a)', 90, 182);
  return c;
}

// ---------- progresso guardado na Fábrica de Autores ----------
function resumoProfessora() {
  return { tut: S.tut, selos: Object.keys(S.selos), douradas: goldCount(), casas: Object.keys(S.visited).length, criacoes: S.crafts || 0, album: albumCount(),
    titulo: String(S.titulo || '').slice(0, 80), frase: String(S.frase || '').slice(0, 300), hist: S.hist || {}, missoes: Object.keys(S.missoes || {}), ideias: S.ideas.length,
    personagem: S.charKey === 'img' ? (S.desenhoSlot != null ? 'desenho do livro' : 'foto') : 'exemplo', estacao: GAME.season };
}
function figurinhaNova() {
  if (S.charKey !== 'img' || !PLAYER_CANVAS) return null;
  const sig = S.desenhoSlot != null ? 'livro:' + S.desenhoSlot + (S.desenhoCrop ? ':' + hash32(JSON.stringify(S.desenhoCrop)) : '') : 'foto:' + hash32(DRAWING || '');
  if (sig === S.figSig) return null;
  // o próprio aparelho diminui: 300x360 em WebP; se o navegador não fizer WebP (Safari), PNG cada vez menor até caber
  const LIMITE = 88000;
  try {
    for (const [w, hh] of [[300, 360], [260, 312], [220, 264], [180, 216], [132, 164]]) {
      const c = fitCanvas(PLAYER_CANVAS, w, hh);
      for (const q of [0.88, 0.78, 0.66]) { const u = c.toDataURL('image/webp', q); if (!u.startsWith('data:image/webp')) break; if (u.length < LIMITE) return { url: u, sig }; }
      const png = c.toDataURL('image/png'); if (png.length < LIMITE) return { url: png, sig };
    }
  } catch (e) {}
  return null;
}
const Srv = {
  dirty: false, busy: false, last: 0, t: 0, erro: false,
  get on() { return !!(S.codigo && S.vid); },
  tick(dt) { if (!this.on || !GAME.started) return; this.t += dt; if (this.dirty && this.t > 25) this.enviar(); },
  agora() { if (!this.on) return; this.dirty = true; clearTimeout(this._a); this._a = setTimeout(() => this.enviar(), 500); },
  async enviar(keepalive) {
    if (!this.on || this.busy) return; this.busy = true; this.t = 0; this.dirty = false;
    const progresso = JSON.stringify(S);
    const body = { c: S.codigo, vid: S.vid, progresso, resumo: JSON.stringify(resumoProfessora()) };
    const fig = keepalive ? null : figurinhaNova(); if (fig) body.fig = fig.url;
    if (keepalive && progresso.length > 58000) { this.busy = false; return; }
    try {
      const r = await apiPost('vila-salvar', body, { keepalive });
      if (r && r.ok) { this.last = Date.now(); this.erro = false; if (fig) { S.figSig = fig.sig; S.figV = r.fig_v || Date.now(); S.figAprov = 'PENDENTE'; lsSet(SAVE_KEY, JSON.stringify(S)); this.dirty = true; clearTimeout(this._a); this._a = setTimeout(() => this.enviar(), 1500); } }
      else { this.dirty = true; this.erro = true; }
    } catch (e) { this.dirty = true; this.erro = true; }
    this.busy = false;
  },
};
function aoSalvar() { try { if (Srv.on) Srv.dirty = true; } catch (e) {} }
addEventListener('visibilitychange', () => { if (document.hidden && Srv.on && Srv.dirty) Srv.enviar(true); });
addEventListener('pagehide', () => { if (Srv.on && Srv.dirty) Srv.enviar(true); });

// ---------- colegas da turma (sincronia pelo servidor) ----------
const REMOTES = new Map();
function makeRemote(id) {
  const bb = makeBillboard(placeholderSticker('?'), 2.1); scene.add(bb.root);
  const crown = MODEL.coroa(); crown.scale.setScalar(0.9); crown.visible = false; bb.pivot.add(crown);
  const lab = h('div', { class: 'lbl name' }); $('#labels').append(lab);
  return {
    id, bb, lab, crown, x: 0, z: 0, tx: 0, tz: 0, area: '', f: 1, k: '', a: 0, nome: '', init: false, walkT: 0, sit: false, texSig: '',
    upd(peer) {
      const pr = parseJSON(peer.p || '{}', {});
      this.tx = Number.isFinite(+pr.x) ? +pr.x : 0; this.tz = Number.isFinite(+pr.z) ? +pr.z : 0;
      const area = String(pr.a || 'vila').slice(0, 20); if (area !== this.area) { this.area = area; this.init = false; }
      this.f = +pr.f < 0 ? -1 : 1; this.sit = !!pr.s; this.crown.visible = !!pr.w;
      const nome = String(peer.n || 'Colega').slice(0, 16); if (nome !== this.nome) { this.nome = nome; lab.textContent = nome; }
      this.k = String(pr.k || '').slice(0, 8); this.a = +peer.a || 0;
      const sig = this.k + ':' + this.a; if (sig !== this.texSig) { this.texSig = sig; this.refreshTex(); }
      if (!this.init) { this.x = this.tx; this.z = this.tz; this.init = true; }
    },
    async refreshTex() {
      let c = null;
      if (SAMPLES[this.k]) c = sampleSticker(this.k);
      else if (this.a) { try { c = await loadImgCanvas(apiURL('vila-fig', { v: this.id, fv: this.a })); } catch (e) { c = null; } }
      if (!c) c = placeholderSticker(this.nome);
      bb.setCanvas(c); this.crown.position.set(0, bb.h * 0.93 - 0.08, -bb.h * 0.35 + 0.05);
    },
    dispose() { scene.remove(bb.root); lab.remove(); },
  };
}
function updateRemotes(dt, t) {
  for (const r of REMOTES.values()) {
    const vis = r.area === GAME.area && GAME.started; r.bb.root.visible = vis; r.lab.hidden = !vis; if (!vis) continue;
    const dx = r.tx - r.x, dz = r.tz - r.z, d = Math.hypot(dx, dz); let walking = false;
    if (d > 14) { r.x = r.tx; r.z = r.tz; }
    else if (d > 0.03) { const s = Math.min(d, Math.max(3.4, d / 0.9) * dt); r.x += (dx / d) * s; r.z += (dz / d) * s; walking = true; if (Math.abs(dx) > 0.05) r.f = dx > 0 ? 1 : -1; }
    r.bb.root.position.set(r.x, 0, r.z); r.bb.pivot.scale.x = lerp(r.bb.pivot.scale.x, r.f, 1 - Math.exp(-dt * 12));
    if (walking && !r.sit) { r.walkT += dt * 11; r.bb.pivot.position.y = Math.abs(Math.sin(r.walkT)) * 0.17; } else r.bb.pivot.position.y = r.sit ? 0.6 : 0;
    placeLabel(r.lab, r.x, r.bb.h + 0.35 + r.bb.pivot.position.y, r.z - 0.4);
  }
}
const Net = {
  mural: [], turma: [], turmaSig: '', coletivaSrv: null, prox: 3500, t: 0, busy: false, falhas: 0, ligado: false, idle: 0, lastP: '',
  get on() { return Srv.on; },
  start() { this.t = 1e9; this.ui(); },
  presenceObj() { return { a: GAME.area, x: Math.round(P.pos.x * 50) / 50, z: Math.round(P.pos.z * 50) / 50, f: P.facing, s: P.sitting ? 1 : 0, w: S.wearing === 'coroa' && (S.inv.coroa || 0) > 0 ? 1 : 0, k: S.charKey }; },
  sendPresence() { this.t = Math.max(this.t, this.prox - 250); this.idle = 0; },
  tick(dt) {
    if (!this.on || !GAME.started || document.hidden) return;
    const p = JSON.stringify(this.presenceObj()); if (p !== this.lastP) { this.lastP = p; this.idle = 0; } else this.idle += dt;
    this.t += dt * 1000; const wait = this.prox * (this.idle > 90 ? 2 : 1);
    if (!this.busy && this.t >= wait) this.sync(p);
  },
  async sync(p) {
    this.busy = true; this.t = 0;
    try {
      const r = await apiPost('vila-sync', { c: S.codigo, vid: S.vid, p }, { timeout: 9000 });
      if (r && r.ok) {
        this.ligado = true; this.falhas = 0; this.prox = clamp(+r.prox || 3500, 2000, 15000);
        this.onPeers(Array.isArray(r.peers) ? r.peers : []);
        this.mural = (Array.isArray(r.mural) ? r.mural : []).filter((m) => Number.isInteger(m.f) && m.f >= 0 && m.f < FIGURINHAS.length); drawMural();
        this.coletivaSrv = r.coletiva || null; refreshColetiva();
        if (Array.isArray(r.turma)) { const sig = r.turma.map((x) => x.v + x.a).join(','); this.turma = r.turma; if (sig !== this.turmaSig) { this.turmaSig = sig; refreshVaral(); } }
        if (r.eu && typeof r.eu.aprov === 'string') S.figAprov = r.eu.aprov;
        (Array.isArray(r.presentes) ? r.presentes : []).forEach((g) => this.receiveGift(g));
      } else this.ligado = false;
    } catch (e) { this.ligado = false; this.falhas++; this.prox = Math.min(20000, 3500 * (1 + this.falhas)); }
    this.busy = false; this.ui();
  },
  onPeers(peers) {
    const seen = new Set();
    for (const pe of peers) { if (!pe || !pe.v || pe.v === S.vid) continue; seen.add(pe.v); let r = REMOTES.get(pe.v); if (!r) { r = makeRemote(pe.v); REMOTES.set(pe.v, r); } r.upd(pe); }
    for (const [id, r] of REMOTES) if (!seen.has(id)) { r.dispose(); REMOTES.delete(id); }
  },
  pushTurma() {
    if (!this.on) return; clearTimeout(this._pt);
    this._pt = setTimeout(async () => {
      const doacoes = Object.assign({ flor: 0, fita: 0, graveto: 0 }, S.coletiva);
      try { const r = await apiPost('vila-turma', { c: S.codigo, vid: S.vid, mural: Number.isInteger(S.flags.muralFig) ? S.flags.muralFig : -1, mural_em: S.flags.muralEm || Date.now(), doacoes }); if (r && r.ok) { S.flags.colEnviado = doacoes; save(); } } catch (e) {}
    }, 1200);
  },
  giftTargets() { if (!this.on) return []; return [...REMOTES.values()].filter((r) => r.area === GAME.area && Math.hypot(r.x - P.pos.x, r.z - P.pos.z) < 8).map((r) => ({ u: r.id, nome: r.nome })); },
  async sendGift(to, item) {
    if (!(S.inv[item] > 0)) return; takeItems({ [item]: 1 });
    try { const r = await apiPost('vila-presente', { c: S.codigo, vid: S.vid, para: to, item }); if (!r || !r.ok) throw new Error('recusado'); toast('🎁 Presente enviado!'); Snd.bell(); Srv.agora(); }
    catch (e) { addItem(item, 1, { silent: true }); toast('Não deu para enviar agora. O presente voltou para a sua mochila.'); }
  },
  receiveGift(g) {
    const item = String(g.item || ''); if (!ITEMS[item]) return;
    const de = String(g.de || 'Colega').slice(0, 16);
    addItem(item, 1, { silent: true }); S.cartas.push({ de, item, em: Date.now(), lida: false }); save(); Srv.agora();
    toast(`🎁 ${de} te mandou: ${ITEMS[item].nome}!`, iconURL(item)); Snd.bell();
  },
  fx() {},
  ui() {
    const el = $('#net'), tx = $('#netTx'); if (!el) return; const n = REMOTES.size, small = innerWidth < 760;
    if (!this.on) { el.classList.remove('on'); tx.textContent = small ? 'visitante' : 'Visitante · jogando sozinho(a)'; }
    else if (this.ligado) { el.classList.add('on'); tx.textContent = small ? `👥 ${n + 1}` : `${S.turma || 'Turma'} · ${n ? n + (n === 1 ? ' colega na vila' : ' colegas na vila') : 'só você agora'}`; }
    else { el.classList.remove('on'); tx.textContent = small ? '…' : `${S.turma || 'Turma'} · ligando…`; }
    el.title = S.colegio ? `${S.turma} · ${S.colegio}` : 'Vila dos Autores';
  },
};
function muralPosts() {
  if (!Net.on) return S.flags.muralLocal || [];
  const out = Net.mural.map((m) => ({ fig: m.f, nome: m.n, em: m.em || 0 }));
  if (Number.isInteger(S.flags.muralFig) && S.flags.muralFig >= 0) out.push({ fig: S.flags.muralFig, nome: S.nome, em: S.flags.muralEm || 0 });
  return out.sort((a, b) => b.em - a.em);
}
function postMural(i) {
  Snd.pop(); toast('Figurinha colada no mural! 📌');
  if (Net.on) { S.flags.muralFig = i; S.flags.muralEm = Date.now(); save(); drawMural(); Net.pushTurma(); }
  else { const arr = (S.flags.muralLocal || []).filter((p) => p.nome !== S.nome); arr.unshift({ fig: i, nome: S.nome, em: Date.now() }); S.flags.muralLocal = arr.slice(0, 9); save(); drawMural(); }
}
function coletivaTotals() {
  const mine = Object.assign({ flor: 0, fita: 0, graveto: 0 }, S.coletiva);
  if (!Net.on || !Net.coletivaSrv) return mine;
  const sent = Object.assign({ flor: 0, fita: 0, graveto: 0 }, S.flags.colEnviado), t = {};
  for (const k of ['flor', 'fita', 'graveto']) t[k] = Math.max(0, (+Net.coletivaSrv[k] || 0) - (+sent[k] || 0)) + (+mine[k] || 0);
  return t;
}
function varalList() {
  const out = [{ canvas: PLAYER_CANVAS, nome: (S.nome || 'Você') + ' (você)' }];
  for (const p of Net.turma) { if (out.length >= 8) break; if (p.v === S.vid || !p.a) continue; out.push({ url: apiURL('vila-fig', { v: p.v, fv: p.a }), nome: String(p.n || 'Colega').slice(0, 16) }); }
  if (out.length < 4) ['dino', 'miau', 'bip', 'lia'].forEach((k) => { if (out.length < 5) out.push({ canvas: sampleSticker(k), nome: SAMPLES[k].nome + ' (exemplo)' }); });
  return out;
}

// ---------- entrada: código do aluno ou visitante ----------
const ULTIMO_KEY = 'vila-autores-v2:ultimo';
let ENTRY = { pick: 'lia', canvas: null, src: null, modo: 'codigo', slot: null, carregando: null, desenhos: [] };
function showEntry(step) {
  GAME.entryOrbit = true; $('#hud').hidden = true; $('#entry').hidden = false; Voz.stop();
  if (step === 2) return showStep2();
  $('#eStep1').hidden = false; $('#eStep2').hidden = true; $('#eMsg1').textContent = ''; $('#eForm').classList.remove('s2');
  const ult = lsGet(ULTIMO_KEY); $('#eCod').value = ult && /^[A-Z0-9]{4}$/.test(ult) ? ult : '';
  setTimeout(() => $('#eCod').focus(), 60);
}
function showStep2() {
  $('#eStep1').hidden = true; $('#eStep2').hidden = false; $('#eMsg').textContent = ''; $('#eForm').classList.add('s2');
  const cod = ENTRY.modo === 'codigo';
  $('#eNomeF').hidden = cod; $('#eHello').hidden = !cod;
  if (cod) {
    const hello = $('#eHello'); hello.innerHTML = '';
    hello.append(h('div', { class: 'oi' }, `Oi, ${S.nome}! 👋`), h('div', { class: 'tm' }, [S.turma, S.colegio].filter(Boolean).join(' · ')),
      h('button', { type: 'button', class: 'lnk', onclick: () => { lsDel(ULTIMO_KEY); useSlot(null); ENTRY.modo = 'codigo'; showEntry(1); } }, 'Não é você? Trocar o código'));
  } else $('#eNome').value = S.nome || '';
  ENTRY.desenhos = cod ? (Array.isArray(S.livroDesenhos) ? S.livroDesenhos.slice(0, 8) : []) : [];
  ENTRY.pick = S.charKey || 'lia'; ENTRY.canvas = null; ENTRY.slot = S.desenhoSlot != null ? S.desenhoSlot : null;
  ENTRY.src = null; ENTRY.crop = null; ENTRY.pre = false; $('#eCrop').hidden = true; $('#eCropRow').hidden = true;
  const grid = $('#eChars'); grid.innerHTML = '';
  for (const d of ENTRY.desenhos) {
    grid.append(h('button', { type: 'button', class: 'ch livro', 'data-s': d.s, onclick: () => pickLivro(d.s, false) }, h('img', { src: apiURL('vila-desenho', { c: S.codigo, s: d.s }), alt: '', loading: 'lazy', decoding: 'async' }), String(d.r || 'Desenho').slice(0, 14)));
  }
  const up = h('button', { type: 'button', class: 'ch', id: 'eUp', 'data-k': 'foto', onclick: () => $('#eFile').click() }, h('span', { class: 'up' }, '📷'), 'Foto');
  grid.append(up);
  for (const k of Object.keys(SAMPLES)) grid.append(h('button', { type: 'button', class: 'ch', 'data-k': k, onclick: () => { ENTRY.pick = k; ENTRY.slot = null; ENTRY.carregando = null; ENTRY.src = null; $('#eCrop').hidden = true; $('#eCropRow').hidden = true; markPick(); drawPreview(sampleSticker(k)); $('#eNote').textContent = `${SAMPLES[k].nome} é um personagem de exemplo. O melhor é usar um desenho do seu livro!`; } }, h('img', { src: sampleSticker(k).toDataURL(), alt: '' }), SAMPLES[k].nome));
  $('#eNote').textContent = ENTRY.desenhos.length ? 'Escolha um desenho do seu livro para ser o seu personagem.' : (cod ? 'Seu livro ainda não tem desenhos digitalizados. Envie uma foto do desenho ou escolha um exemplo.' : 'Envie uma foto do desenho do seu livro. A vila recorta o fundo do papel e cola um contorno de figurinha.');
  if (ENTRY.pick === 'img' && DRAWING) { loadImgCanvas(DRAWING).then((c) => { ENTRY.canvas = c; drawPreview(c); }).catch(() => {}); }
  else if (ENTRY.pick === 'img' && cod && ENTRY.slot != null && ENTRY.desenhos.some((d) => d.s === ENTRY.slot)) { pickLivro(ENTRY.slot, true); }
  else if (ENTRY.pick === 'img' && cod && S.figV) { $('#eNote').textContent = 'Buscando o seu personagem…'; loadImgCanvas(apiURL('vila-fig', { v: S.vid, c: S.codigo, fv: S.figV })).then((c) => { ENTRY.canvas = c; ENTRY.pre = true; drawPreview(c); markPick(); $('#eNote').textContent = 'Este é o seu personagem. Pode trocar se quiser.'; }).catch(() => { ENTRY.pick = 'lia'; markPick(); drawPreview(sampleSticker('lia')); }); }
  else if (cod && S.tut === 0 && ENTRY.desenhos.length && ENTRY.pick !== 'img' && !S.flags.escolheu) { pickLivro(ENTRY.desenhos[0].s, false); }
  else { if (ENTRY.pick === 'img') ENTRY.pick = 'lia'; drawPreview(sampleSticker(SAMPLES[ENTRY.pick] ? ENTRY.pick : 'lia')); }
  markPick();
}
function markPick() {
  document.querySelectorAll('#eChars .ch').forEach((b) => {
    const isLivro = b.classList.contains('livro');
    const sel = ENTRY.pick === 'img' ? (isLivro ? +b.dataset.s === ENTRY.slot : b.dataset.k === 'foto' && ENTRY.slot == null) : b.dataset.k === ENTRY.pick;
    b.classList.toggle('sel', !!sel);
  });
}
function drawPreview(c) { const pv = $('#ePrev'), g = pv.getContext('2d'); g.clearRect(0, 0, pv.width, pv.height); if (!c) return; const k = Math.min((pv.width - 16) / c.width, (pv.height - 16) / c.height); g.drawImage(c, (pv.width - c.width * k) / 2, (pv.height - c.height * k) / 2, c.width * k, c.height * k); }
async function pickLivro(s, manterCorte) {
  ENTRY.pick = 'img'; ENTRY.slot = s; ENTRY.carregando = s; ENTRY.canvas = null; markPick();
  ENTRY.crop = manterCorte && S.desenhoSlot === s && S.desenhoCrop ? S.desenhoCrop : null; $('#eCrop').hidden = true;
  $('#eNote').textContent = 'Recortando o desenho do papel…';
  try {
    const im = await loadImg(apiURL('vila-desenho', { c: S.codigo, s }));
    if (ENTRY.carregando !== s) return;
    ENTRY.src = im; processDrawing(true);
  } catch (e) { if (ENTRY.carregando === s) { $('#eNote').textContent = 'Não consegui abrir esse desenho agora. Tente outro ou um personagem de exemplo.'; ENTRY.pick = 'lia'; ENTRY.slot = null; markPick(); drawPreview(sampleSticker('lia')); } }
}
function fonteRecortada() {
  const src = ENTRY.src, cr = ENTRY.crop; if (!cr) return src;
  const W = src.naturalWidth || src.width, H = src.naturalHeight || src.height;
  const x = Math.round(cr.x * W), y = Math.round(cr.y * H), w = Math.max(8, Math.round(cr.w * W)), hh = Math.max(8, Math.round(cr.h * H));
  const c = mkCanvas(w, hh); c.getContext('2d').drawImage(src, x, y, w, hh, 0, 0, w, hh); return c;
}
function processDrawing(doLivro) {
  if (!ENTRY.src) return;
  $('#eCropRow').hidden = false; $('#eCropTx').textContent = ENTRY.crop ? 'Usando só um pedaço do desenho.' : '';
  try {
    const fonte = fonteRecortada();
    let base = $('#eCut').checked ? cutDrawing(fonte) : fitCanvas(fonte, 340, 400);
    if (!base) {
      $('#eNote').textContent = doLivro ? 'Esse desenho parece estar em branco. Escolha outro desenho ou um personagem de exemplo.' : 'Não achei o desenho nessa foto. Tente outra, bem iluminada, ou desmarque "Recortar o fundo do papel".';
      ENTRY.pick = 'lia'; ENTRY.slot = null; markPick(); drawPreview(sampleSticker('lia')); return;
    }
    ENTRY.canvas = stickerize(fitCanvas(base, 300, 360)); ENTRY.pre = false; ENTRY.pick = 'img'; if (!doLivro) ENTRY.slot = null;
    drawPreview(ENTRY.canvas); markPick();
    $('#eNote').textContent = 'Pronto! Se o recorte comeu partes do desenho, desmarque "Recortar o fundo do papel".';
  } catch (e) { console.warn(e); $('#eNote').textContent = 'Não consegui ler essa imagem. Tente outra foto, bem iluminada.'; }
}
function aplicarAluno(r) {
  useSlot(r.codigo);
  const srv = r.progresso ? parseJSON(r.progresso, null) : null;
  if (srv && typeof srv === 'object' && (+srv.salvoEm || 0) > (+S.salvoEm || 0) + 2000) {
    S = Object.assign(defSave(), srv);
    if (S.charKey === 'img' && DRAWING && S.figSig && S.figSig.startsWith('livro:') && String(S.desenhoSlot) !== S.figSig.slice(6).split(':')[0]) DRAWING = null;
  }
  Object.assign(S, { codigo: r.codigo, vid: r.vid, nome: String(r.primeiro || 'Autor').slice(0, 16), turma: String(r.turma_nome || ''), turmaId: String(r.turma_id || ''), colegio: String(r.colegio_nome || ''), tituloLivro: String(r.titulo_livro || ''), livroDesenhos: Array.isArray(r.desenhos) ? r.desenhos : [] });
  lsSet(SAVE_KEY, JSON.stringify(S)); lsSet(ULTIMO_KEY, r.codigo);
}
function bindEntry() {
  const cod = $('#eCod');
  cod.addEventListener('input', () => { const v = cod.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 4); if (v !== cod.value) cod.value = v; });
  let buscando = false;
  const entrarCodigo = async () => {
    if (buscando) return; Snd.ensure();
    const c = cod.value.trim().toUpperCase(), msg = $('#eMsg1'); msg.textContent = '';
    if (!/^[A-Z0-9]{4}$/.test(c)) { msg.textContent = 'O código tem 4 letras ou números. Ele está na folha do seu livro.'; cod.focus(); Snd.nope(); return; }
    buscando = true; const bt = $('#eGoCod'), tx0 = bt.textContent; bt.disabled = true; bt.textContent = 'Procurando seu livro…';
    try {
      const r = await apiPost('vila-entrar', { c });
      if (!r || !r.ok) { msg.textContent = 'Não achei esse código. Confira com a professora.'; Snd.nope(); }
      else { aplicarAluno(r); ENTRY.modo = 'codigo'; Snd.pop(); showStep2(); }
    } catch (e) { msg.textContent = 'Não consegui falar com a vila agora. Tente de novo ou entre como visitante.'; Snd.nope(); }
    bt.disabled = false; bt.textContent = tx0; buscando = false;
  };
  $('#eGoCod').addEventListener('click', entrarCodigo);
  cod.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); entrarCodigo(); } });
  $('#eVisit').addEventListener('click', () => { Snd.ensure(); useSlot(null); ENTRY.modo = 'visitante'; showStep2(); setTimeout(() => $('#eNome').focus(), 60); });
  $('#eBack').addEventListener('click', () => showEntry(1));
  $('#eFile').addEventListener('change', (e) => { const f = e.target.files && e.target.files[0]; if (!f) return; const rd = new FileReader(); rd.onload = () => loadImg(rd.result).then((im) => { ENTRY.src = im; ENTRY.slot = null; ENTRY.carregando = null; ENTRY.crop = null; $('#eCrop').hidden = true; processDrawing(false); }).catch(() => { $('#eNote').textContent = 'Não consegui abrir essa imagem.'; }); rd.readAsDataURL(f); e.target.value = ''; });
  bindCorte();
  $('#eCut').addEventListener('change', () => { if (ENTRY.src && ENTRY.pick === 'img' && !ENTRY.pre) processDrawing(ENTRY.slot != null); });
  let entering = false;
  const enter = async () => {
    if (entering) return; Snd.ensure();
    const msg = $('#eMsg'); msg.textContent = '';
    if (ENTRY.modo !== 'codigo') {
      const nome = $('#eNome').value.trim().slice(0, 16);
      if (!nome) { msg.textContent = 'Escreva seu apelido para entrar.'; $('#eNome').focus(); Snd.nope(); return; }
      S.nome = nome; S.turma = ''; S.codigo = ''; S.vid = '';
    }
    if (ENTRY.pick === 'img') {
      if (ENTRY.canvas) { const url = ENTRY.canvas.toDataURL('image/png'); saveDrawing(url); S.desenhoSlot = ENTRY.slot != null ? ENTRY.slot : null; S.desenhoCrop = ENTRY.slot != null && ENTRY.crop ? ENTRY.crop : null; if (ENTRY.pre && S.desenhoSlot == null) S.figSig = 'foto:' + hash32(DRAWING || ''); }
      else if (!DRAWING) ENTRY.pick = 'lia';
    }
    S.charKey = ENTRY.pick; S.flags.escolheu = 1; save();
    entering = true;
    try { await startGame(); } catch (er) { console.error(er); $('#entry').hidden = false; GAME.entryOrbit = true; msg.textContent = 'Algo deu errado ao abrir a vila. Recarregue a página e tente de novo.'; }
    entering = false;
  };
  $('#eGo').addEventListener('click', enter);
  $('#eNome').addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); enter(); } });
}
// recorte manual: a criança marca só o personagem numa página com cenário
function bindCorte() {
  const cv = $('#eCropCv'), g = cv.getContext('2d'); let fit = null, sel = null, drag = null;
  const desenha = () => {
    g.clearRect(0, 0, cv.width, cv.height); if (!fit) return;
    g.drawImage(ENTRY.src, fit.x, fit.y, fit.w, fit.h);
    if (sel && sel.w > 4 && sel.h > 4) {
      g.fillStyle = 'rgba(34,26,43,.45)'; g.beginPath(); g.rect(0, 0, cv.width, cv.height); g.rect(sel.x, sel.y, sel.w, sel.h); g.fill('evenodd');
      g.setLineDash([10, 7]); g.lineWidth = 4; g.strokeStyle = '#ffc93c'; g.strokeRect(sel.x, sel.y, sel.w, sel.h); g.setLineDash([]);
    }
  };
  const pos = (e) => { const r = cv.getBoundingClientRect(); return { x: ((e.clientX - r.left) / r.width) * cv.width, y: ((e.clientY - r.top) / r.height) * cv.height }; };
  $('#eCropBt').addEventListener('click', () => {
    if (!ENTRY.src) return; const W = ENTRY.src.naturalWidth || ENTRY.src.width, H = ENTRY.src.naturalHeight || ENTRY.src.height;
    const k = Math.min(cv.width / W, cv.height / H); fit = { w: W * k, h: H * k }; fit.x = (cv.width - fit.w) / 2; fit.y = (cv.height - fit.h) / 2;
    sel = ENTRY.crop ? { x: fit.x + ENTRY.crop.x * fit.w, y: fit.y + ENTRY.crop.y * fit.h, w: ENTRY.crop.w * fit.w, h: ENTRY.crop.h * fit.h } : null;
    $('#eCrop').hidden = false; $('#eCropOk').disabled = !sel; desenha(); cv.scrollIntoView({ block: 'nearest' });
  });
  cv.addEventListener('pointerdown', (e) => { if (!fit) return; drag = pos(e); sel = { x: drag.x, y: drag.y, w: 0, h: 0 }; try { cv.setPointerCapture(e.pointerId); } catch (er) {} desenha(); });
  cv.addEventListener('pointermove', (e) => { if (!drag) return; const p = pos(e); const x0 = clamp(Math.min(drag.x, p.x), fit.x, fit.x + fit.w), y0 = clamp(Math.min(drag.y, p.y), fit.y, fit.y + fit.h), x1 = clamp(Math.max(drag.x, p.x), fit.x, fit.x + fit.w), y1 = clamp(Math.max(drag.y, p.y), fit.y, fit.y + fit.h); sel = { x: x0, y: y0, w: x1 - x0, h: y1 - y0 }; desenha(); });
  const fim = () => { if (!drag) return; drag = null; $('#eCropOk').disabled = !(sel && sel.w > 24 && sel.h > 24); };
  cv.addEventListener('pointerup', fim); cv.addEventListener('pointercancel', fim);
  $('#eCropOk').addEventListener('click', () => { if (!sel || !fit) return; ENTRY.crop = { x: (sel.x - fit.x) / fit.w, y: (sel.y - fit.y) / fit.h, w: sel.w / fit.w, h: sel.h / fit.h }; $('#eCrop').hidden = true; Snd.pop(); processDrawing(ENTRY.slot != null); });
  $('#eCropAll').addEventListener('click', () => { ENTRY.crop = null; sel = null; $('#eCrop').hidden = true; processDrawing(ENTRY.slot != null); });
}

// aplica o progresso escolhido ao mundo já montado (itens colocados, folhas douradas, lareira, Pena)
function aplicarSave() {
  for (const e of PLACED_MESH.values()) { scene.remove(e.m); if (e.it) e.it.dead = true; } PLACED_MESH.clear();
  S.placed.forEach(spawnPlaced);
  for (let i = WITEMS.length - 1; i >= 0; i--) { const w = WITEMS[i]; if (w.fixed || w.tut) { scene.remove(w.m); WITEMS.splice(i, 1); } }
  spawnFixedGold(); if (S.tut <= 1) seedTutorialItems();
  applyFire(); applySeason(S.season === 'auto' || !SEASONS[S.season] ? seasonByDate() : S.season);
  PENA.mode = S.tut >= 4 && S.tut < 7 ? 'inside' : 'idle'; updatePenaArea();
  if (ROOM_FX.chestLid) ROOM_FX.chestLid.rotation.x = S.selos.autor ? -1.9 : 0;
  drawChalk(); drawMural(); refreshColetiva();
}
async function startGame() {
  $('#entry').hidden = true; GAME.entryOrbit = false;
  PLAYER_CANVAS = await playerCanvas();
  if (!P.bb) { P.bb = makeBillboard(PLAYER_CANVAS, 2.15); scene.add(P.bb.root); P.crown = MODEL.coroa(); P.crown.scale.setScalar(0.9); P.bb.pivot.add(P.crown); }
  else P.bb.setCanvas(PLAYER_CANVAS);
  updateCrown(); ME_LBL.textContent = S.nome;
  if (ROOM_FX.easelMat) { if (ROOM_FX.easelMat.map) ROOM_FX.easelMat.map.dispose(); ROOM_FX.easelMat.map = canvasTex(PLAYER_CANVAS); ROOM_FX.easelMat.needsUpdate = true; }
  aplicarSave();
  refreshVaral();
  const area = ROOMS[S.area] ? S.area : 'vila';
  setArea(area);
  if (area === 'vila') { P.pos.set(Number.isFinite(S.x) ? S.x : 0, 0, Number.isFinite(S.z) ? S.z : 25); } else { P.pos.set(ROOMS[area].ox, 0, 3.4); }
  resolveColl(GAME.area, P.pos, 0.45);
  snapCam(); $('#hud').hidden = false; GAME.started = true;
  if (!S.cartas.length) { S.cartas.push({ de: 'Pena', txt: 'Bem-vindo(a) à Vila dos Autores! Aqui no Correio chegam cartas e presentes da sua turma. Com carinho, Pena.', em: Date.now(), lida: false }); save(); }
  checkDiscoveries(true); refreshQuest(); updateBadges(); refreshColetiva();
  $('#somIc').textContent = S.mute ? '🔇' : '🔊'; $('#voz').classList.toggle('on', !!S.voz);
  Net.start(); if (Srv.on) Srv.agora();
  Voz.preload(S.tut === 0 ? [1, 2, 3, 4] : S.tut < 5 ? [5, 6, 7, 8] : S.tut < 7 ? [9, 10, 11, 12] : missoesFeitas() < 4 ? [16, 17, 18, 19] : []);
  if (S.tut === 0) toast('Siga o caminho até a fonte: a Pena está esperando! 👣');
  renderer.domElement.focus({ preventScroll: true });
}
function sairDaVila() {
  const fim = () => { lsDel(ULTIMO_KEY); location.reload(); };
  if (Srv.on) { Srv.busy = false; Srv.enviar().finally(fim); setTimeout(fim, 4000); } else fim();
}

// ---------- título e primeira frase ----------
function escritaOk() { return String(S.titulo || '').trim().length >= 3 && String(S.frase || '').trim().split(/\s+/).filter(Boolean).length >= 3; }
function abaEscrita(body) {
  const tit = h('input', { maxlength: 60, autocomplete: 'off', placeholder: 'Ex.: O dragão que tinha medo de fogo' });
  tit.value = S.titulo || S.tituloLivro || '';
  const fr = h('textarea', { rows: 3, maxlength: 220, placeholder: 'Ex.: Era uma vez um dragão que espirrava bolhas de sabão.' });
  fr.value = S.frase || '';
  const prev = h('img', { alt: 'Prévia da capa', class: 'capaPrev' });
  const upd = () => { prev.src = coverCanvas('#ff6f91', false, tit.value.trim()).toDataURL(); };
  tit.addEventListener('input', upd); upd();
  body.append(h('p', {}, 'Todo livro começa com um título e uma primeira frase. Escreva os da sua história: eles vão aparecer na Página Ilustrada e na Capa do seu livro.'));
  const wrap = h('div', { class: 'escrita' });
  const col = h('div', { style: 'min-width:0' });
  col.append(h('label', { class: 'field' }, h('span', {}, 'Título da história'), tit));
  if (S.tituloLivro && !S.titulo) col.append(h('p', { style: 'font-size:13px;color:var(--muted);margin-top:-6px' }, 'Esse é o título que está no cadastro do seu livro. Pode mudar se quiser.'));
  col.append(h('label', { class: 'field' }, h('span', {}, 'Primeira frase'), fr));
  col.append(h('div', { class: 'figs' }, ['Era uma vez', 'Num dia de sol,', 'Lá longe, depois do rio,', 'Ninguém sabia que'].map((c) => h('button', { type: 'button', class: 'btn plain sm', onclick: () => { if (!fr.value.trim()) fr.value = c + ' '; else if (!fr.value.startsWith(c)) fr.value = c + ' ' + fr.value.trim(); fr.focus(); Snd.pop(); } }, c + '…'))));
  wrap.append(col, prev); body.append(wrap);
  const msg = h('div', { role: 'alert', style: 'color:#c2334f;font-weight:700;min-height:22px;margin:8px 0 4px' });
  const bt = h('button', { class: 'btn leaf', onclick: () => {
    const t = tit.value.trim().replace(/\s+/g, ' '), f = fr.value.trim().replace(/\s+/g, ' ');
    if (t.length < 3) { msg.textContent = 'Escreva um título com pelo menos 3 letras.'; tit.focus(); Snd.nope(); return; }
    if (f.split(' ').length < 3) { msg.textContent = 'A primeira frase precisa de pelo menos 3 palavras.'; fr.focus(); Snd.nope(); return; }
    const primeira = !S.flags.escrita; S.titulo = t; S.frase = f; S.flags.escrita = 1; save(); Srv.agora(); Snd.pop();
    if (primeira) { GAME.afterPanel = () => say([11], () => checkTutorial()); }
    closePanel(); toast('Título e primeira frase guardados no Caderno ✏️');
  } }, '💾 Guardar no Caderno');
  body.append(msg, bt);
}

// ---------- missões das casas: os elementos da história ----------
const MISSOES = {
  biblioteca: { el: 'personagem', nomeEl: 'Personagem', voz: 16, titulo: 'Quem é o seu personagem?', placa: 'Quem é?',
    ensina: 'O personagem é quem vive a história. Um bom personagem tem um nome, uma coisa que adora e um medo. É isso que deixa a gente torcer por ele!',
    campos: [
      { k: 'nome', rot: 'Nome do personagem', ph: 'Ex.: Tito, o dragão cozinheiro', max: 40 },
      { k: 'gosta', rot: 'Do que ele mais gosta?', ph: 'Ex.: de bolo de cenoura', chips: ['de bolo de chocolate', 'de voar bem alto', 'de contar piadas', 'de ler livros', 'de brincar na chuva'] },
      { k: 'medo', rot: 'Do que ele tem medo?', ph: 'Ex.: do escuro', chips: ['do escuro', 'de trovão', 'de ficar sozinho', 'de aranha', 'de altura'] },
    ], premio: { fita: 1, botao: 1 } },
  atelie: { el: 'cenario', nomeEl: 'Cenário', voz: 17, titulo: 'Onde a sua história acontece?', placa: 'Onde?',
    ensina: 'O cenário é o lugar da história. Quando a gente conta a cor, o som e o cheiro do lugar, quem lê consegue imaginar que está lá dentro.',
    campos: [
      { k: 'lugar', rot: 'Qual é o lugar?', ph: 'Ex.: uma floresta encantada', chips: ['uma floresta encantada', 'um castelo nas nuvens', 'o fundo do mar', 'uma cidade de doces', 'a minha escola', 'o espaço sideral'] },
      { k: 'cor', rot: 'Que cor tem esse lugar?', ph: 'Ex.: verde-esmeralda', cores: [['azul', '#6ec6ff'], ['verde', '#78cf62'], ['roxo', '#a77bff'], ['dourado', '#ffc93c'], ['rosa', '#ff8fb8'], ['laranja', '#ff9b4a']] },
      { k: 'som', rot: 'Que som se ouve lá?', ph: 'Ex.: passarinhos cantando', chips: ['passarinhos cantando', 'ondas do mar', 'vento assobiando', 'risadas', 'sinos tocando'] },
      { k: 'cheiro', rot: 'Que cheiro tem?', ph: 'Ex.: de bolo saindo do forno', chips: ['de bolo saindo do forno', 'de flores', 'de chuva na terra', 'de pipoca', 'de mar'] },
    ], premio: { tinta: 2 } },
  grafica: { el: 'problema', nomeEl: 'Problema', voz: 18, titulo: 'O que dá errado?', placa: 'O problema',
    ensina: 'Toda história boa tem um problema: alguma coisa dá errado e o personagem precisa resolver. É o problema que deixa a história emocionante!',
    campos: [
      { k: 'oque', rot: 'Qual é o problema?', ph: 'Ex.: o mapa do tesouro sumiu', longo: true, max: 160, chips: ['o mapa do tesouro sumiu', 'uma tempestade chegou', 'o melhor amigo se perdeu', 'a chave mágica quebrou', 'a festa ficou sem bolo'] },
      { k: 'ajuda', rot: 'Quem ajuda a resolver?', ph: 'Ex.: uma coruja muito esperta', chips: ['o melhor amigo', 'a vovó', 'um bicho falante', 'uma fada', 'ninguém: ele resolve sozinho'] },
    ], premio: { capa: 1, papel: 1 } },
  correio: { el: 'final', nomeEl: 'Final', voz: 19, titulo: 'Como a sua história termina?', placa: 'Como termina?',
    ensina: 'O final é o fechamento da história: mostra como o problema foi resolvido e como o personagem ficou. Depois, é só mandar para alguém ler!',
    campos: [
      { k: 'tipo', rot: 'Que tipo de final?', ph: 'Ex.: feliz', chips: ['feliz', 'com surpresa', 'engraçado', 'com uma lição'] },
      { k: 'frase', rot: 'Escreva a última frase', ph: 'Ex.: E desde aquele dia, Tito nunca mais teve medo do escuro.', longo: true, max: 220 },
      { k: 'para', rot: 'Para quem você vai mandar?', ph: 'Ex.: minha família', chips: ['minha família', 'a professora', 'meus colegas', 'todo mundo'] },
    ], premio: { fita: 1, dourada: 1 } },
};
const MISSAO_IDS = ['biblioteca', 'atelie', 'grafica', 'correio'];
const MISSAO_BUB = {};
function missoesFeitas() { return MISSAO_IDS.filter((id) => S.missoes && S.missoes[id]).length; }
function missaoStand(room, x, z) {
  const id = room.id, MS = MISSOES[id], s = new T.Group(); s.position.set(x, 0, z); room.g.add(s);
  part(box(0.12, 2.2, 0.12), M.woodDark, -0.82, 1.1, 0, 0.03, s); part(box(0.12, 2.2, 0.12), M.woodDark, 0.82, 1.1, 0, 0.03, s);
  signBoard('MISSÃO · ' + MS.nomeEl.toUpperCase(), 2.3, 0.6, s, 0, 2.35, 0.05, { bg: '#ffc93c', size: 46, weight: 900 });
  signBoard(MS.placa, 1.6, 0.8, s, 0, 1.45, 0.05, { bg: '#fff8ec', size: 60, weight: 900 });
  addCircle(id, rw(id, x), z, 0.45);
  const bub = makeBillboard(bubbleCanvas('!', '#6ec6ff'), 1.0); bub.sh.visible = false; bub.root.position.set(rw(id, x), 3.35, z); bub.root.visible = false; scene.add(bub.root);
  MISSAO_BUB[id] = bub;
  inter({ area: id, x: rw(id, x), z: z + 0.8, r: 1.7, y: 3.1, obj: s, hopH: 0.1, label: () => (!S.selos.autor ? '🔒 Missão da história' : S.missoes && S.missoes[id] ? '📜 Rever a missão' : '⭐ Missão: ' + MS.nomeEl), act: () => openMissao(id) });
}
const PORTA_BUB = {};
function initMissoes() {
  for (const id of MISSAO_IDS) { const H = HOUSES[id], b = makeBillboard(bubbleCanvas('!', '#6ec6ff'), 1.2); b.sh.visible = false; b.root.position.set(H.doorX - H.nx * 0.4, 5.2, H.doorZ - H.nz * 0.4); b.root.visible = false; scene.add(b.root); PORTA_BUB[id] = b; }
}
function updateMissoes(dt, t) {
  const on = GAME.started && !!S.selos.autor;
  for (const id of MISSAO_IDS) {
    const pend = on && !(S.missoes && S.missoes[id]);
    const b = MISSAO_BUB[id]; if (b) { b.root.visible = pend && GAME.area === id; if (b.root.visible) b.root.position.y = 3.35 + Math.sin(t * 3 + 1) * 0.15; }
    const pb = PORTA_BUB[id]; if (pb) { pb.root.visible = pend && GAME.area === 'vila'; if (pb.root.visible) pb.root.position.y = 5.2 + Math.sin(t * 3 + id.length) * 0.22; }
  }
}
function openMissao(id) {
  if (!S.selos.autor) { say(['Esta missão abre quando você ganhar o selo de Autor(a) da Vila. Termine as tarefas da Pena na casa amarela!']); return; }
  if (!S.flags['mvoz_' + id]) { S.flags['mvoz_' + id] = 1; save(); say([MISSOES[id].voz], () => openMissaoPainel(id)); return; }
  openMissaoPainel(id);
}
function openMissaoPainel(id) {
  const MS = MISSOES[id], salvo = (S.hist && S.hist[MS.el]) || {}, feita = !!(S.missoes && S.missoes[id]);
  openPanel(MS.titulo, (body) => {
    body.append(h('p', { class: 'ensina' }, h('b', {}, MS.nomeEl + ': '), MS.ensina));
    const vals = {};
    for (const f of MS.campos) {
      const inp = f.longo ? h('textarea', { rows: 2, maxlength: f.max || 160, placeholder: f.ph || '' }) : h('input', { maxlength: f.max || 60, placeholder: f.ph || '', autocomplete: 'off' });
      inp.value = salvo[f.k] || (f.k === 'nome' ? S.nomePers || '' : '');
      vals[f.k] = inp;
      body.append(h('label', { class: 'field' }, h('span', {}, f.rot), inp));
      if (f.chips) body.append(h('div', { class: 'figs chipsM' }, f.chips.map((c) => h('button', { type: 'button', class: 'btn plain sm', onclick: () => { inp.value = c; Snd.pop(); } }, c))));
      if (f.cores) body.append(h('div', { class: 'figs chipsM' }, f.cores.map(([nm, cor]) => h('button', { type: 'button', class: 'btn plain sm', onclick: () => { inp.value = nm; Snd.pop(); } }, h('i', { class: 'cor', style: `background:${cor}` }), nm))));
    }
    const msg = h('div', { role: 'alert', style: 'color:#c2334f;font-weight:700;min-height:22px;margin:6px 0' });
    const premio = Object.entries(MS.premio).map(([k, n]) => `${n} ${ITEMS[k].nome}`).join(' + ');
    body.append(msg, h('div', { class: 'row' }, h('button', { class: 'btn leaf', onclick: () => {
      const out = {};
      for (const f of MS.campos) { const v = vals[f.k].value.trim().replace(/\s+/g, ' '); if (v.length < 2) { msg.textContent = `Falta responder: ${f.rot}`; vals[f.k].focus(); Snd.nope(); return; } out[f.k] = v.slice(0, f.max || 160); }
      S.hist = S.hist || {}; S.missoes = S.missoes || {}; S.hist[MS.el] = out;
      if (id === 'biblioteca' && out.nome) { S.nomePers = out.nome.slice(0, 24); drawChalk(); if (!(S.inv.nomePers > 0)) addItem('nomePers', 1, { silent: true }); }
      if (!feita) {
        S.missoes[id] = Date.now();
        Object.entries(MS.premio).forEach(([k, n]) => addItem(k, n));
        Snd.fanfare(); confetti(innerWidth / 2, innerHeight / 2, 140);
        const todas = missoesFeitas() === 4;
        GAME.afterPanel = () => { toast(`⭐ Missão completa: ${MS.nomeEl}! Você ganhou ${premio}.`); if (todas) setTimeout(() => say([20], () => award('historia')), 600); };
      } else toast('Missão atualizada ✏️');
      save(); Srv.agora(); refreshQuest(); closePanel();
    } }, feita ? '💾 Guardar mudanças' : '✔ Pronto!'), feita ? null : h('span', { style: 'font-size:14px;color:var(--muted)' }, `Prêmio: ${premio}`)));
  }, { eyebrow: `${HOUSES[id].nome} · Elemento da história`, onClose: () => refreshQuest() });
}
function minhaHistoria() {
  const hs = S.hist || {}, p = hs.personagem, c = hs.cenario, pr = hs.problema, f = hs.final, out = [];
  if (S.titulo) out.push(['Título', S.titulo]);
  if (S.frase) out.push(['Primeira frase', S.frase]);
  if (p) out.push(['Personagem', `${p.nome}, que gosta ${p.gosta} e tem medo ${p.medo}.`]);
  if (c) out.push(['Cenário', `${c.lugar}, de cor ${c.cor}, com som de ${c.som} e cheiro ${c.cheiro}.`]);
  if (pr) out.push(['Problema', `${pr.oque}. Quem ajuda: ${pr.ajuda}.`]);
  if (f) out.push(['Final', `Um final ${f.tipo}: ${f.frase}`]);
  return out;
}

// ---------- álbum de coleção (31 itens) ----------
function albumCount() { return Object.keys(ITEMS).filter((k) => S.seen[k]).length; }
function checkAlbum() { const tot = Object.keys(ITEMS).length; if (GAME.started && albumCount() >= tot && !S.selos.album) award('album'); }
function dicaAlbum(k) {
  const it = ITEMS[k], has = !!S.seen[k], r = RECIPES.find((x) => x.id === k);
  if (has) return it.desc || '';
  if (!r) return it.desc || 'Procure pela vila.';
  const st = recipeState(r);
  let tx = st.disc ? 'Receita: ' + Object.entries(r.ing).map(([i, n]) => `${n} ${ITEMS[i].nome}`).join(' + ') : 'Uma receita misteriosa do Livro de Receitas.';
  if (r.estacao) tx += ` Só no ${SEASONS[r.estacao].nome}.`;
  if (r.onde) tx += ` Feita na ${STATION_NOME[r.onde]}.`;
  if (r.grupo === 'livro' && !S.selos.autor) tx += ' Abre com o selo de Autor(a).';
  return tx;
}
function openAlbum() {
  openPanel('Álbum da Vila', (body) => {
    const ks = Object.keys(ITEMS), tot = ks.length, n = albumCount();
    body.append(h('p', {}, `Você já encontrou ${n} de ${tot} itens. Cada item novo vira uma figurinha colorida aqui.`), h('div', { class: 'bar', style: 'margin-bottom:4px' }, h('i', { style: `width:${(n / tot) * 100}%` })));
    const detail = h('div', { class: 'detail' });
    for (const [nm, tp] of [['Ingredientes', 'ing'], ['Coisas do livro', 'livro'], ['Criações e enfeites', 'deco']]) {
      const list = ks.filter((k) => ITEMS[k].tipo === tp), got = list.filter((k) => S.seen[k]).length;
      body.append(h('div', { class: 'sec' }, `${nm} · ${got}/${list.length}`));
      const grid = h('div', { class: 'inv' }); const btns = [];
      list.forEach((k) => { const has = !!S.seen[k]; const b = h('button', { class: 'slot' + (has ? '' : ' nope'), onclick: () => { body.querySelectorAll('.slot.sel').forEach((x) => x.classList.remove('sel')); b.classList.add('sel'); show(k); } }, h('img', { src: iconURL(k), alt: '' }), has ? ITEMS[k].nome : '???'); btns.push(b); grid.append(b); });
      body.append(grid);
    }
    body.append(detail);
    function show(k) { detail.innerHTML = ''; const has = !!S.seen[k]; detail.append(h('img', { src: iconURL(k), alt: '', class: has ? '' : 'nope' }), h('div', { class: 'info' }, h('b', { style: 'font-family:var(--display);font-size:18px;display:block' }, has ? ITEMS[k].nome : 'Ainda não encontrado'), h('div', {}, dicaAlbum(k)))); }
    detail.append(h('div', { class: 'info' }, 'Toque numa figurinha para ver onde ela aparece.'));
  }, { eyebrow: 'Coleção', icon: iconURL('marcador') });
}
