# Fundos (arte fixa) do livro formato Céu para a Bia 07 (Google Slides, página 200 x 200 mm).
# Tudo o que é igual em todo livro vai assado na imagem de fundo; o que muda (textos, desenhos,
# fotos, logo) a Bia 07 coloca por cima. As caixas abaixo são as MESMAS usadas no código da Bia 07.
# uso: python3 -I fundos.py <pasta saida> <pasta fontes> <arte_ceu.py dir>
import sys, os, asyncio, html
SAIDA, FONTES, ARTE = [os.path.abspath(a) for a in sys.argv[1:4]]
sys.path.insert(0, ARTE)
import arte_ceu as A
os.makedirs(SAIDA, exist_ok=True)
P = 200
QR = 'file://' + os.path.abspath(os.path.join(os.path.dirname(__file__), 'qr_vila.svg'))
EXT = ['UM', 'DOIS', 'TRÊS', 'QUATRO', 'CINCO', 'SEIS']

# ---- caixas (mm) ----
CAPA_JANELA = (42, 52, 116, 94)
SELO = (157, 157, 30, 30)
DED_POLA = (86, 92, 96, 92)
DES_CARD = (22, 22, 156, 156)
LETRA_CARD = (13, 62, 174, 120)
J16_CARD = (13, 62, 174, 62)
BIO_POLA = (124, 14, 62, 82)
MSG_POLA = (14, 13, 42, 52)
MSG_LOGO = (151, 15, 36, 36)

def f(n, a, w, s='normal'):
    return f"@font-face{{font-family:'{n}';src:url('file://{FONTES}/{a}');font-weight:{w};font-style:{s}}}"
CSS = f"""{f('Poppins','poppins-latin-500-normal.woff2',500)}{f('Poppins','poppins-latin-600-normal.woff2',600)}
{f('Poppins','poppins-latin-700-normal.woff2',700)}{f('Poppins','poppins-latin-800-normal.woff2',800)}
{f('Lora','Lora-Regular.ttf',400)}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{P}mm;height:{P}mm;overflow:hidden}}
.pg{{width:{P}mm;height:{P}mm;position:relative;overflow:hidden;background:#fff;font-family:Poppins,Arial,sans-serif}}
.abs{{position:absolute;left:0;top:0;width:{P}mm;height:{P}mm}}
.t{{position:absolute;font-weight:700;color:#3b1fa0}}
.sub{{position:absolute;font-weight:600;font-size:8.5pt;letter-spacing:.12em;text-transform:uppercase;color:#f6921e}}
.box{{position:absolute;background:#fff}}
.card{{border:.8mm solid #d8cdf6;border-radius:5mm}}
.pola{{border:.45mm solid #d8cdf6}}
.ph{{position:absolute;background:#d8cdf6;display:flex;align-items:center;justify-content:center;text-align:center;font-weight:600;font-size:8.5pt;line-height:1.3;color:#3b1fa0}}
.selo{{position:absolute;border-radius:50%;background:#fff;border:1mm solid #26147a}}
.lf{{position:absolute;display:flex;align-items:center;justify-content:center;text-align:center;font-weight:700;font-size:6pt;line-height:1.25;color:#6b6390;border:.4mm dashed #6b6390;border-radius:50%}}
.folio{{position:absolute;bottom:7mm;font-weight:600;font-size:8.5pt;color:#6b6390}}
.num{{position:absolute;left:13mm;font-weight:800;line-height:1;color:#3b1fa0}}
.pill{{position:absolute;left:14mm;background:#ffc23d;color:#26147a;font-weight:700;font-size:9pt;letter-spacing:.1em;padding:1.4mm 3.6mm;border-radius:10mm}}
.qr{{position:absolute;display:flex;gap:4mm;align-items:center}}
.qr img{{display:block}}
.qr p{{font-weight:500;font-size:8.5pt;line-height:1.4}}
"""
CEU = None

def bx(b, cls='box', extra=''):
    x, y, w, h = b
    return f"<div class='{cls}' style='left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm;{extra}'></div>"

def mini(evitar, n, sem):
    return A.miniaturas_svg(P, P, n, evitar, semente=sem, margem=8)

def folio(n):
    lado = 'left:13mm' if n % 2 == 0 else 'right:13mm'
    return f"<div class='folio' style='{lado}'>{n}</div>"

def selo(b):
    x, y, w, h = b
    return (f"<div class='selo' style='left:{x}mm;top:{y}mm;width:{w}mm;height:{h}mm'></div>"
            f"<div class='lf' style='left:{x+5.5}mm;top:{y+5.5}mm;width:{w-11}mm;height:{h-11}mm'>LOGO<br>DA ESCOLA</div>")

def svg(conteudo):
    return 'data:image/svg+xml;utf8,' + html.escape(conteudo).replace('#', '%23')

def ceu_cheio(nuv_topo, est_evitar, sem):
    return ("<img class='abs' src='@@CEU@@'>"
            f"<img class='abs' src='{svg(A.estrelas_svg(P, P, 16, sem, (0.05, 0.04, 0.95, 0.66), evitar=est_evitar))}'>"
            f"<img class='abs' src='{svg(A.nuvens_svg(P, P, nuv_topo, semente=sem + 10))}'>")

paginas = {}
# ---------- capa
paginas['capa'] = (ceu_cheio(124, [(36, 48, 164, 150), (10, 10, 190, 52)], 5)
    + "<div style='position:absolute;left:0;right:0;top:14mm;text-align:center;font-weight:500;font-size:9.5pt;color:#fff'>Fábrica de Autores · Aceleradora EDU</div>"
    + bx(CAPA_JANELA, 'box', 'border:3.2mm solid #26147a;border-radius:5mm')
    + "<div style='position:absolute;left:0;right:0;top:153mm;text-align:center;font-weight:500;font-size:10.5pt;color:#2b2160'>Escrito e ilustrado por</div>"
    + selo(SELO))
# ---------- contracapa
paginas['contra'] = (ceu_cheio(106, [(10, 18, 190, 100)], 31)
    + "<div class='t' style='left:13mm;top:22mm;font-size:19pt;color:#fff'>Sobre esta história</div>"
    + "<div style='position:absolute;left:0;right:0;top:138mm;text-align:center;font-weight:700;font-size:14pt;color:#26147a;line-height:1.25'>Fábrica de Autores<div style='font-weight:500;font-size:8pt;color:#6b6390'>Aceleradora EDU</div></div>"
    + f"<div class='qr' style='left:13mm;top:160mm'><img src='{QR}' style='width:22mm;height:22mm'><p style='width:62mm;color:#2b2160'>Aponte a câmera para entrar na <b>Vila dos Autores</b>, onde esta história vira jogo.</p></div>"
    + selo(SELO))
# ---------- 1 folha de rosto
paginas['p01'] = (ceu_cheio(152, [(10, 40, 190, 120)], 51)
    + "<div style='position:absolute;left:0;right:0;top:96mm;text-align:center;font-weight:500;font-size:10.5pt;color:#fff;opacity:.85'>Escrito e ilustrado por</div>")
# ---------- 2 créditos
paginas['p02'] = (mini([(12, 18, 160, 104), (12, 156, 120, 190)], 12, 302)
    + f"<div class='qr' style='left:13mm;top:162mm'><img src='{QR}' style='width:22mm;height:22mm'><p style='width:70mm;color:#2b2160'>Aponte a câmera para entrar na <b>Vila dos Autores</b>, onde esta história vira jogo.</p></div>")
# ---------- 3 dedicatória
paginas['p03'] = (mini([(12, 14, 110, 32), (12, 32, 188, 82), DED_POLA[:2] + (DED_POLA[0] + DED_POLA[2], DED_POLA[1] + DED_POLA[3])], 14, 303)
    + "<div class='t' style='left:13mm;top:16mm;font-size:24pt'>Dedicatória</div>"
    + bx(DED_POLA, 'box pola') + folio(3))
# ---------- 4..15 partes
for i in range(6):
    nt, nd = 4 + 2 * i, 5 + 2 * i
    fim = "<div class='t' style='right:13mm;bottom:12mm;font-size:22pt;font-weight:800'>Fim.</div>" if i == 5 else ''
    paginas[f'p{nt:02d}_dig'] = (mini([(12, 6, 74, 58), (12, 80, 188, 176), (150, 170, 190, 192)], 16, 310 + i)
        + f"<div class='num' style='top:8mm;font-size:96pt'>{i+1}</div><div class='pill' style='top:46mm'>PARTE {EXT[i]}</div>" + fim + folio(nt))
    paginas[f'p{nt:02d}_let'] = (mini([(12, 4, 74, 52), (LETRA_CARD[0], LETRA_CARD[1], 187, 182), (150, 182, 190, 196)], 12, 330 + i)
        + f"<div class='num' style='top:5mm;font-size:80pt'>{i+1}</div><div class='pill' style='top:39mm'>PARTE {EXT[i]}</div>"
        + bx(LETRA_CARD, 'box card') + (fim.replace('bottom:12mm', 'bottom:4mm').replace('22pt', '16pt') if fim else '') + folio(nt))
    paginas[f'p{nd:02d}'] = (mini([(DES_CARD[0], DES_CARD[1], 178, 178), (40, 178, 160, 192)], 18, 350 + i)
        + bx(DES_CARD, 'box card', 'border-radius:6mm') + folio(nd))
# ---------- 16
paginas['p16_dig'] = (mini([(12, 12, 150, 44), (12, 58, 188, 126), (12, 126, 188, 190)], 14, 370)
    + "<div class='sub' style='left:13mm;top:17mm'>A parte um, na letra original</div>"
    + "<div class='t' style='left:13mm;top:23mm;font-size:24pt'>Do jeitinho que eu escrevi</div>"
    + bx(J16_CARD, 'box card', 'border-radius:4mm')
    + "<div class='sub' style='left:13mm;top:130mm;color:#3b1fa0;font-weight:700'>Como ficou no livro</div>" + folio(16))
paginas['p16_let'] = (mini([(12, 12, 160, 44), (12, 46, 188, 192)], 8, 371)
    + "<div class='sub' style='left:13mm;top:17mm'>Para ler junto</div>"
    + "<div class='t' style='left:13mm;top:23mm;font-size:24pt'>A história passada a limpo</div>" + folio(16))
# ---------- 17 biografia
x, y, w, h = BIO_POLA
paginas['p17'] = (mini([(12, 12, 112, 56), (x - 2, y - 2, x + w + 2, y + h + 2), (12, 98, 188, 192)], 12, 372)
    + "<div class='sub' style='left:13mm;top:17mm'>Conheça</div>"
    + "<div class='t' style='left:13mm;top:23mm;font-size:24pt;line-height:1.1'>Quem escreveu<br>este livro</div>"
    + bx(BIO_POLA, 'box pola')
    + f"<div class='ph' style='left:{x+3.5}mm;top:{y+3.5}mm;width:{w-7}mm;height:{h-14}mm'>foto da autora<br>ou do autor</div>" + folio(17))
# ---------- 18 mensagem da professora
x, y, w, h = MSG_POLA
lx, ly, lw, lh = MSG_LOGO
paginas['p18'] = (mini([(x - 2, y - 2, x + w + 2, y + h + 2), (60, 14, 150, 56), (lx - 2, ly - 2, lx + lw + 2, ly + lh + 2), (12, 70, 188, 194)], 9, 373)
    + "<div class='sub' style='left:64mm;top:20mm'>Para a turma</div>"
    + "<div class='t' style='left:64mm;top:26mm;font-size:21pt;line-height:1.1;width:84mm'>Uma mensagem da professora</div>"
    + bx(MSG_POLA, 'box pola')
    + f"<div class='ph' style='left:{x+3.5}mm;top:{y+3.5}mm;width:{w-7}mm;height:{h-14}mm;font-size:7.5pt'>foto da<br>professora</div>"
    + bx(MSG_LOGO, 'box card', 'border-radius:4mm;border-width:.6mm')
    + f"<div class='lf' style='left:{lx+6}mm;top:{ly+6}mm;width:{lw-12}mm;height:{lh-12}mm;border-radius:2mm'>LOGO<br>DA ESCOLA</div>" + folio(18))

async def main():
    global CEU
    from playwright.async_api import async_playwright
    ceu = os.path.join(SAIDA, '_ceu.jpg')
    A.ceu_png(ceu, 2362, 2362)
    CEU = 'file://' + ceu
    import importlib
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--allow-file-access-from-files'])
        pg = await b.new_page(viewport={'width': 756, 'height': 756}, device_scale_factor=2362 / 756)
        for nome, corpo in paginas.items():
            corpo = corpo.replace('@@CEU@@', CEU)
            doc = f"<!doctype html><meta charset=utf-8><style>{CSS}</style><div class='pg'>{corpo}</div>"
            tmp = os.path.join(SAIDA, '_tmp.html'); open(tmp, 'w').write(doc)
            await pg.goto('file://' + tmp); await pg.evaluate('document.fonts.ready')
            await pg.wait_for_timeout(150)
            png = os.path.join(SAIDA, f'_{nome}.png')
            await pg.screenshot(path=png, clip={'x': 0, 'y': 0, 'width': 756, 'height': 756})
            from PIL import Image
            Image.open(png).convert('RGB').resize((2362, 2362)).save(os.path.join(SAIDA, f'{nome}.jpg'), quality=88, dpi=(300, 300))
            os.remove(png)
        await b.close()
    os.remove(os.path.join(SAIDA, '_tmp.html')); os.remove(ceu)

asyncio.run(main())
print(len(paginas), 'fundos')
