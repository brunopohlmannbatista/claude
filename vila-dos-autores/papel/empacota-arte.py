# Recorta, limpa e embute as artes do piloto em papel/arte-dados.js (WebP em data URI).
# uso: python3 empacota.py <pasta das artes> <saida arte-dados.js>
import sys, io, base64, json
import numpy as np
from PIL import Image
from scipy import ndimage

SRC, OUT = sys.argv[1], sys.argv[2]

def sangra(im):
    """Espalha a cor da borda para dentro da área transparente (evita filete escuro no recorte)."""
    a = np.array(im)
    alfa = a[..., 3]
    opaco = alfa > 128
    idx = ndimage.distance_transform_edt(~opaco, return_distances=False, return_indices=True)
    rgb = a[..., :3][idx[0], idx[1]]
    return Image.fromarray(np.dstack([rgb, alfa]), 'RGBA')

def recorta(im, folga=3):
    a = np.array(im.getchannel('A')) > 128
    r = np.where(a.any(1))[0]; c = np.where(a.any(0))[0]
    return im.crop((max(0, c[0] - folga), max(0, r[0] - folga), min(im.width, c[-1] + 1 + folga), min(im.height, r[-1] + 1 + folga)))

def webp(im, q=84):
    b = io.BytesIO(); im.save(b, 'WEBP', quality=q, method=6, alpha_quality=90, exact=True); return b.getvalue()

def reduz(im, lado, por='h'):
    k = lado / (im.height if por == 'h' else im.width)
    if k >= 1: return im
    return im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)

dados, total = {}, 0
def guarda(nome, im, q=84, **extra):
    global total
    b = webp(im, q); total += len(b)
    dados[nome] = dict(src='data:image/webp;base64,' + base64.b64encode(b).decode(), w=im.width, h=im.height, **extra)
    print(f'{nome:9s} {im.width}x{im.height} {len(b)/1024:6.1f} KB')

# cartões recortados (fundo transparente)
for nome, arq, alt in [('arvore', 'arvore.png', 512), ('pinho', 'pinho.png', 512), ('poste', 'poste.png', 512)]:
    im = recorta(sangra(Image.open(f'{SRC}/{arq}').convert('RGBA')))
    a = np.array(im.getchannel('A')) > 128
    base = np.where(a[-8])[0]; cx = (base[0] + base[-1]) / 2 / im.width  # onde o tronco pisa no chão
    guarda(nome, reduz(im, alt), cx=round(float(cx), 4))

# fachada da Casa da Pena (só a parede da frente)
fa = recorta(sangra(Image.open(f'{SRC}/fachada.png').convert('RGBA')), 2)
guarda('fachada', reduz(fa, 768, 'w'), q=86)

# olho-de-boi e faixa de pedra, tirados da primeira arte da casa
casa = Image.open(f'{SRC}/casa.png').convert('RGBA')
R = 84; cx, cy = 510, 328
olho = casa.crop((cx - R, cy - R, cx + R, cy + R)).copy()
yy, xx = np.mgrid[0:2 * R, 0:2 * R]; d = np.hypot(xx - R + 0.5, yy - R + 0.5)
o = np.array(olho); o[..., 3] = np.where(d <= R - 2, 255, 0).astype('uint8'); olho = sangra(Image.fromarray(o, 'RGBA'))
guarda('olho', olho.resize((128, 128), Image.LANCZOS))
base = sangra(casa).crop((66, 808, 958, 912))
guarda('base', reduz(base, 512, 'w').convert('RGB'), q=82)

# texturas que se repetem: telha e reboco (o reboco é afinado para a cor da fachada)
telha = Image.open(f'{SRC}/telha.png').convert('RGB').resize((320, 320), Image.LANCZOS)
guarda('telha', telha, q=82)
par = np.array(Image.open(f'{SRC}/parede.png').convert('RGB').resize((256, 256), Image.LANCZOS)).astype(float)
ref = np.array(Image.open(f'{SRC}/fachada.png').convert('RGB')).astype(float)[70:180, 250:800].reshape(-1, 3).mean(0)  # faixa lisa acima da porta
par = np.clip(par * (ref / par.reshape(-1, 3).mean(0)), 0, 255).astype('uint8')
guarda('parede', Image.fromarray(par, 'RGB'), q=80)
print('cor do reboco', ref.round(0))

with open(OUT, 'w') as f:
    f.write('// Artes do piloto ilustrado (geradas por IA a partir de capturas do proprio jogo, 17/11/2026).\n// Arquivo gerado por empacota.py. Nao editar a mao.\n')
    f.write('const PAPEL_ARTE = ' + json.dumps(dados, separators=(',', ':')) + ';\n')
print(f'imagens: {total/1024:.0f} KB · arte-dados.js: {len(open(OUT).read())/1024:.0f} KB')
