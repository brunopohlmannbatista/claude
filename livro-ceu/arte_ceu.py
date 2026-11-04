# Arte da linha "Céu" (identidade Fábrica de Autores): céu pintado roxo, estrelas e faixas de nuvens.
# Tudo gerado aqui (sem imagem de terceiros). Determinístico por semente.
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROXO_ALTO, ROXO_BAIXO = (38, 20, 120), (92, 52, 206)
NUVENS = ['#6b2fb8', '#f6921e', '#ef5a4f', '#e9578f']   # roxo, laranja, coral, rosa (de trás para a frente)
CREME = '#fbf2de'
ESTRELAS = ['#ffc23d', '#f6921e', '#ef6a8a', '#ffffff']

def ceu_png(caminho, larg_px, alt_px, semente=7):
    """Céu com degradê e pinceladas largas e suaves, como guache."""
    rnd = random.Random(semente)
    y = np.linspace(0, 1, alt_px)[:, None, None]
    a = np.array(ROXO_ALTO) * (1 - y) + np.array(ROXO_BAIXO) * y
    base = Image.fromarray(np.broadcast_to(a, (alt_px, larg_px, 3)).astype(np.uint8))
    tinta = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(tinta)
    for _ in range(int(larg_px * alt_px / 9000)):
        x0 = rnd.uniform(-0.1, 1.0) * larg_px; y0 = rnd.uniform(0, 1) * alt_px
        comp = rnd.uniform(0.08, 0.35) * larg_px; esp = rnd.uniform(0.004, 0.018) * larg_px
        ang = rnd.uniform(-0.25, 0.1)
        claro = rnd.random() < 0.55
        cor = (130, 95, 235, rnd.randint(14, 34)) if claro else (24, 12, 90, rnd.randint(14, 30))
        x1 = x0 + comp * math.cos(ang); y1 = y0 + comp * math.sin(ang)
        d.line([(x0, y0), (x1, y1)], fill=cor, width=max(2, int(esp)))
    tinta = tinta.filter(ImageFilter.GaussianBlur(larg_px / 900))
    base = Image.alpha_composite(base.convert('RGBA'), tinta).convert('RGB')
    base.save(caminho, quality=92, dpi=(300, 300))

def estrela(x, y, r, cor, giro=0):
    """Estrela de 4 pontas, desenhada como à mão."""
    pts = []
    for i in range(8):
        ang = giro + i * math.pi / 4
        rr = r if i % 2 == 0 else r * 0.28
        pts.append(f'{x + rr * math.sin(ang):.2f},{y - rr * math.cos(ang):.2f}')
    return f'<polygon points="{" ".join(pts)}" fill="{cor}"/>'

def estrelas_svg(w, h, n, semente=3, zona=(0, 0, 1, 1), evitar=()):
    """SVG (unidades em mm) com n estrelas espalhadas, longe dos retângulos em 'evitar'."""
    rnd = random.Random(semente)
    out = []
    tent = 0
    while len(out) < n and tent < n * 60:
        tent += 1
        x = rnd.uniform(zona[0], zona[2]) * w; y = rnd.uniform(zona[1], zona[3]) * h
        if any(a <= x <= c and b <= y <= d for a, b, c, d in evitar):
            continue
        r = rnd.choice([1.4, 1.8, 2.2, 2.8, 3.6])
        out.append(estrela(x, y, r, rnd.choice(ESTRELAS), rnd.uniform(-0.2, 0.2)))
    return f'<svg viewBox="0 0 {w} {h}" width="{w}mm" height="{h}mm" xmlns="http://www.w3.org/2000/svg">{"".join(out)}</svg>'

def onda(w, base_y, amp, n, fase, semente):
    """Contorno de nuvem: sequência de bolhas (arcos) ao longo da largura."""
    rnd = random.Random(semente)
    xs = [0]
    while xs[-1] < w:
        xs.append(xs[-1] + w / n * rnd.uniform(0.75, 1.3))
    d = f'M -2 {base_y + amp * 2}'
    prev = (-2, base_y + rnd.uniform(-amp, amp) * 0.4)
    d += f' L {prev[0]} {prev[1]:.2f}'
    for i in range(1, len(xs)):
        x = min(xs[i], w + 2); y = base_y + math.sin(i * 1.7 + fase) * amp * 0.35 + rnd.uniform(-amp, amp) * 0.25
        larg = x - prev[0]
        r = larg / 2 * rnd.uniform(1.0, 1.25)
        d += f' A {r:.2f} {r * rnd.uniform(0.75, 1.0):.2f} 0 0 1 {x:.2f} {y:.2f}'
        prev = (x, y)
    return d

def nuvens_svg(w, h, topo, cores=NUVENS, creme=CREME, semente=11, amp=7, n=6):
    """Faixa de nuvens em camadas, terminando no creme. topo = onde começa a primeira camada (mm)."""
    camadas = []
    passo = 6.5
    for i, cor in enumerate(cores):
        y = topo + i * passo
        camadas.append(f'<path d="{onda(w, y, amp, n, i * 1.3, semente + i)} L {w + 2} {h + 2} L -2 {h + 2} Z" fill="{cor}"/>')
    y = topo + len(cores) * passo + 3
    camadas.append(f'<path d="{onda(w, y, amp * 1.1, n - 1, 2.2, semente + 9)} L {w + 2} {h + 2} L -2 {h + 2} Z" fill="{creme}"/>')
    return f'<svg viewBox="0 0 {w} {h}" width="{w}mm" height="{h}mm" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">{"".join(camadas)}</svg>'

def borda_nuvem_svg(w, h, y, cor=CREME, semente=21, amp=6, n=7):
    """Uma única borda de nuvem (céu em cima, cor embaixo), para as páginas de miolo."""
    return f'<svg viewBox="0 0 {w} {h}" width="{w}mm" height="{h}mm" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"><path d="{onda(w, y, amp, n, 0.8, semente)} L {w + 2} {h + 2} L -2 {h + 2} Z" fill="{cor}"/></svg>'

# ---- mini desenhos de traço (versão econômica do miolo): só contorno, pouca tinta ----
# cada ícone numa caixa 0..10, desenhado com stroke (sem preenchimento)
ICONES = {
    'estrela': 'M5 0.6 L6.3 3.6 L9.6 3.9 L7.1 6.1 L7.9 9.4 L5 7.7 L2.1 9.4 L2.9 6.1 L0.4 3.9 L3.7 3.6 Z',
    'coracao': 'M5 9 C1 6.2 0.4 4 1.4 2.4 C2.5 0.8 4.4 1.2 5 2.8 C5.6 1.2 7.5 0.8 8.6 2.4 C9.6 4 9 6.2 5 9 Z',
    'nuvem': 'M2.2 7.6 C0.6 7.6 0.3 5.4 1.9 5 C1.8 3.2 3.9 2.4 4.9 3.6 C5.6 1.8 8.4 2.2 8.3 4.4 C9.9 4.6 9.9 7.6 8.1 7.6 Z',
    'brilho': 'M5 0.5 Q5.6 4.4 9.5 5 Q5.6 5.6 5 9.5 Q4.4 5.6 0.5 5 Q4.4 4.4 5 0.5 Z',
    'lapis': 'M1.2 8.8 L2 6.2 L7.4 0.8 L9.2 2.6 L3.8 8 Z M6.4 1.8 L8.2 3.6 M2 6.2 L3.8 8',
    'livro': 'M5 2.6 C3.6 1.6 2 1.4 0.6 1.8 L0.6 8.4 C2 8 3.6 8.2 5 9.2 C6.4 8.2 8 8 9.4 8.4 L9.4 1.8 C8 1.4 6.4 1.6 5 2.6 Z M5 2.6 L5 9.2',
    'sol': 'M5 3.1 A1.9 1.9 0 1 1 4.99 3.1 Z M5 0.4 L5 1.6 M5 8.4 L5 9.6 M0.4 5 L1.6 5 M8.4 5 L9.6 5 M1.8 1.8 L2.6 2.6 M7.4 7.4 L8.2 8.2 M8.2 1.8 L7.4 2.6 M2.6 7.4 L1.8 8.2',
    'espiral': 'M5 5 m0 0 c0.6 0 0.8 -0.9 0.2 -1.2 c-1 -0.5 -2 0.4 -1.8 1.4 c0.2 1.5 2.2 2 3.2 0.9 c1.4 -1.4 0.6 -3.8 -1.3 -4.2 c-2.4 -0.5 -4.3 1.8 -3.7 4.1',
    'flor': 'M5 3.8 A1.2 1.2 0 1 1 4.99 3.8 Z M5 3.8 C3.6 0.8 6.4 0.8 5 3.8 M6.2 5 C9.2 3.6 9.2 6.4 6.2 5 M5 6.2 C6.4 9.2 3.6 9.2 5 6.2 M3.8 5 C0.8 6.4 0.8 3.6 3.8 5',
    'balao': 'M1 1.4 L9 1.4 L9 6.6 L4.2 6.6 L2.2 8.8 L2.6 6.6 L1 6.6 Z',
}
CORES_TRACO = ['#3b1fa0', '#f6921e', '#ef5a4f', '#e9578f', '#6b2fb8']

def miniaturas_svg(w, h, n, evitar=(), semente=1, margem=9, tam=(5, 8.5), folga=3.5):
    """Espalha n mini desenhos de traço pela página (mm), fora dos retângulos em 'evitar'."""
    rnd = random.Random(semente)
    nomes = list(ICONES)
    feitos = []
    out = []
    tent = 0
    while len(feitos) < n and tent < n * 400:
        tent += 1
        s = rnd.uniform(*tam)
        x = rnd.uniform(margem, w - margem - s); y = rnd.uniform(margem, h - margem - s)
        cx, cy = x + s / 2, y + s / 2
        if any(a - folga <= cx <= c + folga and b - folga <= cy <= d + folga for a, b, c, d in evitar):
            continue
        if any((cx - fx) ** 2 + (cy - fy) ** 2 < (s / 2 + fs / 2 + 5) ** 2 for fx, fy, fs in feitos):
            continue
        feitos.append((cx, cy, s))
        nome = nomes[len(feitos) % len(nomes)] if rnd.random() < 0.5 else rnd.choice(nomes)
        cor = rnd.choice(CORES_TRACO)
        giro = rnd.uniform(-18, 18)
        k = s / 10
        out.append(f'<g transform="translate({x:.2f} {y:.2f}) rotate({giro:.1f} {s/2:.2f} {s/2:.2f}) scale({k:.3f})">'
                   f'<path d="{ICONES[nome]}" fill="none" stroke="{cor}" stroke-width="{0.45 / k:.3f}" stroke-linecap="round" stroke-linejoin="round"/></g>')
    return f'<svg viewBox="0 0 {w} {h}" width="{w}mm" height="{h}mm" xmlns="http://www.w3.org/2000/svg">{"".join(out)}</svg>'
