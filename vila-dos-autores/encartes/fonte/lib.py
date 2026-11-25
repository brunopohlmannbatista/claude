import os, re, qrcode, qrcode.image.svg
BASE=os.path.dirname(os.path.abspath(__file__))
ICON_DIR=os.path.join(BASE,'node_modules/lucide-static/icons')
def ic(name,size=20,color=None,sw=2):
    p=os.path.join(ICON_DIR,name+'.svg')
    if not os.path.exists(p): raise SystemExit('icone nao existe: '+name)
    s=open(p).read()
    s=re.sub(r'<!--.*?-->','',s,flags=re.S).strip()
    s=re.sub(r'width="24"',f'width="{size}"',s,1); s=re.sub(r'height="24"',f'height="{size}"',s,1)
    s=re.sub(r'stroke-width="2"',f'stroke-width="{sw}"',s,1)
    s=re.sub(r'class="[^"]*"','',s)
    st=f' style="color:{color}"' if color else ''
    return s.replace('<svg',f'<svg{st} class="ic"',1)
def qr(url,path):
    img=qrcode.make(url,image_factory=qrcode.image.svg.SvgPathImage,box_size=10,border=0)
    img.save(path)
CSS_BASE='''
@font-face{font-family:"PJS";font-weight:400;src:url(assets/fonts/plus-jakarta-sans-latin-400-normal.woff2)}
@font-face{font-family:"PJS";font-weight:600;src:url(assets/fonts/plus-jakarta-sans-latin-600-normal.woff2)}
@font-face{font-family:"PJS";font-weight:700;src:url(assets/fonts/plus-jakarta-sans-latin-700-normal.woff2)}
@font-face{font-family:"PJS";font-weight:800;src:url(assets/fonts/plus-jakarta-sans-latin-800-normal.woff2)}
@font-face{font-family:"GS";font-weight:800;src:url(assets/fonts/grandstander-latin-800-normal.woff2)}
@font-face{font-family:"GS";font-weight:900;src:url(assets/fonts/grandstander-latin-900-normal.woff2)}
:root{--ink:#2b1d3d;--cream:#fff6e6;--paper:#fdecc8;--coral:#ff5c39;--amber:#ffb454;--lilac:#8e63d6;--blue:#2f86d6;--green:#3fa65a;--teal:#17a89b;--dark:#1f1530;--mute:#6b5a7e;--line:#2b1d3d}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"PJS",sans-serif;color:var(--ink);background:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{position:relative;overflow:hidden;page-break-after:always;break-after:page;background:var(--cream)}
.page:last-child{page-break-after:auto;break-after:auto}
.ic{display:inline-block;vertical-align:middle;flex:none}
h1,h2,h3,.gs{font-family:"GS",sans-serif;font-weight:900;letter-spacing:-.01em}
.shot{border:2px solid var(--ink);border-radius:10px;overflow:hidden;background:#fff;position:relative}
.shot img{display:block;width:100%;height:100%;object-fit:cover}
.num{display:inline-flex;align-items:center;justify-content:center;width:7mm;height:7mm;border-radius:50%;background:var(--coral);color:#fff;font:800 11pt "PJS";flex:none}
.cap{display:flex;gap:2.5mm;align-items:flex-start;font-size:9.4pt;line-height:1.38;margin-top:2.2mm}
.chip{display:inline-flex;align-items:center;gap:1.6mm;border:1.6px solid var(--ink);border-radius:99px;padding:1mm 3.2mm;font:700 8.6pt "PJS";background:#fff;color:var(--ink)}
.box{border:2px solid var(--ink);border-radius:10px;background:#fff;padding:3.6mm 4.2mm}
.box h4{font:800 9pt "PJS";letter-spacing:.06em;text-transform:uppercase;margin-bottom:1.6mm;display:flex;align-items:center;gap:1.8mm}
.box p,.box li{font-size:9.3pt;line-height:1.42}
.box ul{list-style:none}
.box li{display:flex;gap:2mm;margin-top:1.1mm}
.box li:first-child{margin-top:0}
.b-amber{background:#ffe9bd}.b-lilac{background:#ece3fa}.b-blue{background:#dcecfb}.b-green{background:#dcf1e1}.b-coral{background:#ffe0d8}.b-teal{background:#d3f1ee}
'''
