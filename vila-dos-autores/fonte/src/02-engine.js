// ============================================================
// Motor 2.5D: WebGPU (preferencial) com reserva WebGL2, toon, contornos, billboards
// ============================================================
let T, renderer, scene, camera, ENGINE = 'WebGL';
let GRAD, OUTLINE, SHADOW_MAT, WINDOW_MAT, ROOM_WIN;
const MATS = new Map(), GC = new Map(), M = {};
let LIGHT_AMB, LIGHT_DIR;

async function loadEngine() {
  let pref = 'auto'; try { pref = localStorage.getItem('vila-engine') || 'auto'; } catch (e) {}
  const base = `https://cdn.jsdelivr.net/npm/three@${V3}/build/`;
  if (pref !== 'webgl' && (navigator.gpu || pref === 'webgpu-gl')) {
    try {
      const mod = await import(base + 'three.webgpu.min.js');
      const r = new mod.WebGPURenderer({ antialias: true, forceWebGL: pref === 'webgpu-gl' });
      await r.init();
      T = mod; renderer = r;
      ENGINE = r.backend && r.backend.isWebGPUBackend ? 'WebGPU' : 'WebGPU (modo WebGL2)';
      return;
    } catch (e) { console.warn('WebGPU indisponível, usando WebGL2', e); }
  }
  const mod = await import(base + 'three.module.min.js');
  T = mod; renderer = new mod.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' }); ENGINE = 'WebGL2';
}

function initMats() {
  const d = new Uint8Array([96, 96, 96, 255, 182, 182, 182, 255, 255, 255, 255, 255]);
  GRAD = new T.DataTexture(d, 3, 1, T.RGBAFormat); GRAD.minFilter = GRAD.magFilter = T.NearestFilter; GRAD.generateMipmaps = false; GRAD.needsUpdate = true;
  OUTLINE = new T.MeshBasicMaterial({ color: INKHEX, side: T.BackSide });
  SHADOW_MAT = new T.MeshBasicMaterial({ color: INKHEX, transparent: true, opacity: 0.2, depthWrite: false });
  WINDOW_MAT = new T.MeshBasicMaterial({ color: 0xffe9a3 });
  ROOM_WIN = new T.MeshBasicMaterial({ color: 0xbfe8ff });
  const u = { unique: true };
  Object.assign(M, {
    grass: toon(0x8fd16c, u), grass2: toon(0x7cc25c, u), path: toon(0xf0d9a8, u), stoneDark: toon(0xb9aa98, u),
    stone: toon(0xece3d4), stone2: toon(0xd2c6b6), water: toon(0x5ec8ff, u), trunk: toon(0x8b5a2b),
    leafA: toon(0xffa9c9, u), leafB: toon(0x9bdc6a, u), pine: toon(0x4f9e5a, u), snow: toon(0xffffff),
    wood: toon(0xc98b4f), woodDark: toon(0x8a5a33), paper: toon(0xfffdf5), gold: toon(0xffc928, { p: { emissive: 0x6a4500 } }),
    rug: toon(0xff9fc0, u), lamp: new T.MeshBasicMaterial({ color: 0xfff2b0 }), ink: toon(0x3b3355), white: toon(0xffffff),
    flag: [toon(0xff8fb8, u), toon(0x8fd3ff, u), toon(0xfff07a, u)], fire1: new T.MeshBasicMaterial({ color: 0xff7a1a }), fire2: new T.MeshBasicMaterial({ color: 0xffd23f }),
  });
}
function toon(color, opts = {}) {
  const key = color + '|' + JSON.stringify(opts.p || {});
  if (!opts.unique && MATS.has(key)) return MATS.get(key);
  const m = new T.MeshToonMaterial(Object.assign({ color, gradientMap: GRAD }, opts.p || {}));
  if (!opts.unique) MATS.set(key, m);
  return m;
}
function geo(key, make) { if (!GC.has(key)) GC.set(key, make()); return GC.get(key); }
const box = (w, h, d) => geo(`b${w},${h},${d}`, () => new T.BoxGeometry(w, h, d));
const cyl = (rt, rb, h, s = 16) => geo(`c${rt},${rb},${h},${s}`, () => new T.CylinderGeometry(rt, rb, h, s));
const sph = (r, ws = 16, hs = 12) => geo(`s${r},${ws},${hs}`, () => new T.SphereGeometry(r, ws, hs));
const cone = (r, h, s = 16) => geo(`k${r},${h},${s}`, () => new T.ConeGeometry(r, h, s));
const tor = (r, t, rs = 10, ts = 28) => geo(`t${r},${t},${rs},${ts}`, () => new T.TorusGeometry(r, t, rs, ts));

function addOutline(mesh, ol) {
  const g = mesh.geometry; if (!g.boundingBox) g.computeBoundingBox();
  const s = new T.Vector3(), c = new T.Vector3(); g.boundingBox.getSize(s); g.boundingBox.getCenter(c);
  const o = new T.Mesh(g, OUTLINE);
  const sx = 1 + (2 * ol) / Math.max(s.x, 0.02), sy = 1 + (2 * ol) / Math.max(s.y, 0.02), sz = 1 + (2 * ol) / Math.max(s.z, 0.02);
  o.scale.set(sx, sy, sz); o.position.set(c.x * (1 - sx), c.y * (1 - sy), c.z * (1 - sz));
  o.userData.outline = true; mesh.add(o); return o;
}
// Peça com contorno preto (casca invertida). ol = espessura do traço em unidades do mundo.
function part(g, m, x = 0, y = 0, z = 0, ol = 0.05, parent) {
  const mesh = new T.Mesh(g, m); mesh.position.set(x, y, z);
  if (ol > 0) addOutline(mesh, ol);
  if (parent) parent.add(mesh);
  return mesh;
}
function canvasTex(c) { const t = new T.CanvasTexture(c); t.colorSpace = T.SRGBColorSpace; t.anisotropy = 4; return t; }
function textCanvas(text, { w = 512, h = 128, bg = '#fff8ec', fg = INK, size = 64, weight = 800 } = {}) {
  const c = mkCanvas(w, h), g = c.getContext('2d'); g.fillStyle = bg; g.fillRect(0, 0, w, h);
  g.fillStyle = fg; g.font = `${weight} ${size}px Grandstander, 'Trebuchet MS', sans-serif`; g.textAlign = 'center'; g.textBaseline = 'middle';
  let s = size; while (g.measureText(text).width > w - 30 && s > 18) { s -= 2; g.font = `${weight} ${s}px Grandstander, 'Trebuchet MS', sans-serif`; }
  g.fillText(text, w / 2, h / 2 + 3); return c;
}
function textPlane(text, w, h, opts = {}) {
  const c = textCanvas(text, Object.assign({ w: Math.round(w * 160), h: Math.round(h * 160) }, opts));
  return new T.Mesh(new T.PlaneGeometry(w, h), new T.MeshBasicMaterial({ map: canvasTex(c) }));
}
function signBoard(text, w, h, parent, x, y, z, opts) {
  const g = new T.Group(); g.position.set(x, y, z);
  part(box(w + 0.16, h + 0.16, 0.12), M.wood, 0, 0, 0, 0.05, g);
  const p = textPlane(text, w, h, opts); p.position.z = 0.07; g.add(p);
  if (parent) parent.add(g); return g;
}

// ---------- personagens billboard (papel recortado, estilo Paper Mario) ----------
const BB_TILT = -0.36;
function makeBillboard(canvas, height = 2.1) {
  const root = new T.Group(), pivot = new T.Group(); root.add(pivot);
  const mat = new T.MeshBasicMaterial({ alphaTest: 0.5, side: T.DoubleSide });
  const mesh = new T.Mesh(new T.PlaneGeometry(1, 1), mat); mesh.rotation.x = BB_TILT; pivot.add(mesh);
  const sh = new T.Mesh(geo('shadow', () => new T.CircleGeometry(0.5, 20)), SHADOW_MAT); sh.rotation.x = -Math.PI / 2; sh.position.y = 0.03; root.add(sh);
  const bb = {
    root, pivot, mesh, sh, h: height, w: 1, tex: null,
    setCanvas(c) {
      if (this.tex) this.tex.dispose();
      this.tex = canvasTex(c); mat.map = this.tex; mat.needsUpdate = true;
      this.w = (height * c.width) / c.height;
      const g = new T.PlaneGeometry(this.w, height); g.translate(0, height / 2, 0); mesh.geometry.dispose(); mesh.geometry = g;
      sh.scale.set(clamp(this.w * 0.75, 0.8, 1.8), clamp(this.w * 0.75, 0.8, 1.8) * 0.55, 1);
    },
  };
  bb.setCanvas(canvas);
  return bb;
}
function bubbleCanvas(txt, bg = '#ffc93c') {
  const c = mkCanvas(128, 150), g = c.getContext('2d'); g.lineWidth = 6; const P = painter(g); g.lineWidth = 6;
  P.p([50, 112, 78, 112, 64, 140], bg); P.c(64, 62, 52, bg); P.t(txt, 64, 66, 72, INK, 900); return c;
}
