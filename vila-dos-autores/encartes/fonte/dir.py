import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ic, CSS_BASE

BASE = os.path.dirname(os.path.abspath(__file__))

CSS = CSS_BASE + '''
@page{size:297mm 210mm;margin:0}
.page{width:297mm;height:210mm;padding:12mm 15mm 14mm}
.hd .tag{font:800 8.6pt "PJS";letter-spacing:.14em;text-transform:uppercase;color:var(--coral);display:flex;gap:2mm;align-items:center}
.hd h2{font-size:27pt;line-height:1.04;margin-top:1.4mm}
.hd .lead{font-size:11pt;line-height:1.42;margin-top:2.4mm;max-width:215mm}
.ft{position:absolute;left:15mm;right:15mm;bottom:6mm;display:flex;justify-content:space-between;font:600 7.6pt "PJS";color:var(--mute);border-top:1.4px solid var(--ink);padding-top:1.6mm}
.row{display:grid;gap:5mm}
.mt2{margin-top:2.5mm}.mt3{margin-top:3.6mm}.mt4{margin-top:6.4mm}.mt5{margin-top:6.5mm}
.cover{background:var(--dark);color:#fff;padding:0}
.cover .left{position:absolute;left:16mm;top:15mm;width:118mm}
.cover .brand{display:flex;align-items:center;gap:2.6mm;font:800 9pt "PJS";letter-spacing:.16em;text-transform:uppercase;color:var(--amber)}
.diam{width:3.6mm;height:3.6mm;background:var(--coral);transform:rotate(45deg);display:inline-block}
.cover h1{font-size:54pt;line-height:.94;margin-top:9mm;color:#fff}
.cover h1 span{color:var(--amber)}
.cover .tagline{font:800 15pt "GS";line-height:1.25;margin-top:7mm;color:#fff}
.cover .sub{font-size:11.2pt;line-height:1.45;margin-top:4mm;color:#e7d9f8}
.cover .chips{position:absolute;left:16mm;bottom:22mm;display:flex;gap:3mm;flex-wrap:wrap;width:118mm}
.cover .chip{background:var(--dark);border-color:var(--amber);color:#fff}
.cover .hero{position:absolute;left:146mm;top:14mm;width:136mm;height:182mm;border:2.4px solid var(--amber);border-radius:14px;overflow:hidden}
.cover .hero img{width:100%;height:100%;object-fit:cover;display:block}
.cover .foot{position:absolute;left:16mm;bottom:9mm;font:600 8.2pt "PJS";color:#cdbbe6}
.stp{margin-top:0}
.stp h3{font-size:14pt;margin-top:2mm;display:flex;gap:2.4mm;align-items:center}
.stp p{font-size:10pt;line-height:1.42;margin-top:1.4mm}
.pt{display:flex;gap:3mm;align-items:flex-start}
.pt .bub{width:11mm;height:11mm;border-radius:50%;border:2px solid var(--ink);display:flex;align-items:center;justify-content:center;flex:none}
.pt b{display:block;font-size:11pt;line-height:1.2}
.pt span.d{display:block;font-size:9.6pt;line-height:1.38;margin-top:.8mm}
.lab{font:800 9pt "PJS";line-height:1.2;margin-top:1.8mm}
.lab small{display:block;font:600 8.2pt "PJS";margin-top:.5mm;color:var(--mute)}
.band{display:flex;gap:3mm;flex-wrap:wrap}
.who{border:2px solid var(--ink);border-radius:12px;background:#fff;overflow:hidden}
.who .wh{display:flex;gap:2.4mm;align-items:center;padding:3mm 4mm;border-bottom:2px solid var(--ink);font:900 14pt "GS"}
.who ul{list-style:none;padding:4.2mm 4.4mm 5mm}
.who li{display:flex;gap:2.2mm;font-size:10.4pt;line-height:1.4;margin-top:3.2mm}
.who li:first-child{margin-top:0}
.qrw{display:flex;gap:5mm;align-items:center}
.qrw img{width:34mm;height:34mm;background:#fff;padding:2mm;border:2px solid var(--ink);border-radius:9px;display:block}
.safe{display:flex;gap:3.4mm;align-items:flex-start;border:2px solid var(--ink);border-radius:12px;background:#d3f1ee;padding:3.6mm 4.4mm}
.safe p{font-size:10pt;line-height:1.42}
'''


def shot(img, style='', pos=''):
    p = f' style="object-position:{pos}"' if pos else ''
    return f'<div class="shot" style="{style}"><img src="assets/img/{img}.jpg" alt=""{p}></div>'


def page(tag, icon, title, lead, body, n):
    return f'''<section class="page">
<div class="hd"><div class="tag">{ic(icon, 15, 'var(--coral)')} {tag}</div><h2>{title}</h2>{('<p class="lead">' + lead + '</p>') if lead else ''}</div>
{body}
<div class="ft"><span>Vila dos Autores · Apresentação para a direção</span><span>Fábrica de Autores · {n}</span></div>
</section>'''


def pt(icon, color, bg, title, desc):
    return f'<div class="pt"><div class="bub" style="background:{bg}">{ic(icon, 19, color)}</div><div><b>{title}</b><span class="d">{desc}</span></div></div>'


pages = []

# 1 capa
pages.append(f'''<section class="page cover">
<div class="left">
<div class="brand"><span class="diam"></span> Fábrica de Autores apresenta</div>
<h1>Vila dos<br><span>Autores</span></h1>
<p class="tagline">O personagem que o seu aluno desenhou ganha uma vila para morar.</p>
<p class="sub">Um jogo no navegador, ligado ao livro que a criança escreve e ilustra. Veja como é, o que a professora acompanha e onde a turma se encontra.</p>
</div>
<div class="chips"><span class="chip">{ic('school', 14, 'var(--amber)')} Apresentação para a direção</span></div>
<div class="hero"><img src="assets/img/praca-agora.jpg" alt=""></div>
<div class="foot">Fábrica de Autores · Recife, PE</div>
</section>''')

# 2 do livro para a tela
body = f'''
<div class="row mt4" style="grid-template-columns:1fr 1fr 1fr">
<div class="stp">{shot('p-004-020')}<h3><span class="num">1</span> O livro traz a chave</h3><p>Cada livro tem um <b>QR Code</b> e uma <b>senha curta</b>. A criança aponta a câmera, digita a senha e entra.</p></div>
<div class="stp">{shot('p-005-029')}<h3><span class="num">2</span> O desenho vira personagem</h3><p>O personagem desenhado no livro é recortado sozinho e passa a andar pela vila, como uma <b>figurinha de papel</b>.</p></div>
<div class="stp">{shot('p-006-034')}<h3><span class="num">3</span> A Pena guia a aventura</h3><p>Uma guardiã das histórias, com <b>voz gravada</b>, ensina cada passo e leva a criança de casa em casa.</p></div>
</div>
<div class="band mt5">
<span class="chip" style="font-size:9.6pt;padding:1.6mm 4mm">{ic('download', 15, 'var(--coral)')} Sem instalar nada</span>
<span class="chip" style="font-size:9.6pt;padding:1.6mm 4mm">{ic('monitor-smartphone', 15, 'var(--coral)')} Computador, tablet e celular</span>
<span class="chip" style="font-size:9.6pt;padding:1.6mm 4mm">{ic('house', 15, 'var(--coral)')} Continua em casa com o QR e a senha do livro</span>
<span class="chip" style="font-size:9.6pt;padding:1.6mm 4mm">{ic('save', 15, 'var(--coral)')} O progresso fica guardado</span>
</div>
<div class="row mt5" style="grid-template-columns:1fr 12mm 1fr 12mm 1fr;align-items:stretch">
<div class="box b-lilac">{ic('pen-line', 24, 'var(--coral)')}<h3 style="font-size:12.5pt;margin-top:1.6mm">A criança escreve na vila</h3><p style="margin-top:1mm">Personagem, cenário, problema e final, uma parte em cada casa.</p></div>
<div style="display:flex;align-items:center;justify-content:center">{ic('arrow-right', 28, 'var(--coral)', 2.6)}</div>
<div class="box b-teal">{ic('clipboard-list', 24, 'var(--coral)')}<h3 style="font-size:12.5pt;margin-top:1.6mm">A professora lê no painel</h3><p style="margin-top:1mm">Vê o que cada criança escreveu e copia os textos da turma.</p></div>
<div style="display:flex;align-items:center;justify-content:center">{ic('arrow-right', 28, 'var(--coral)', 2.6)}</div>
<div class="box b-amber">{ic('book-open', 24, 'var(--coral)')}<h3 style="font-size:12.5pt;margin-top:1.6mm">Os textos vão para o livro</h3><p style="margin-top:1mm">O título na capa, a primeira frase na página ilustrada e as partes da história.</p></div>
</div>
'''
pages.append(page('Como começa', 'qr-code', 'Do livro de papel para a tela', 'A criança joga com o desenho que ela mesma fez. E a história que escreve na vila volta para o livro.', body, 2))

# 3 vila pop-up
houses = [
    ('sala-pena', 'Casa da Pena', 'Aqui começa: ideia, título e primeira frase'),
    ('sala-biblio', 'Biblioteca', 'Quem é o personagem?'),
    ('sala-atelie', 'Ateliê de Desenho', 'Onde a história acontece?'),
    ('sala-grafica', 'Gráfica', 'O que dá errado?'),
    ('sala-correio', 'Correio das Histórias', 'Como termina?'),
]
hh = ''.join(f'<div>{shot(i)}<div class="lab">{t}<small>{d}</small></div></div>' for i, t, d in houses)
body = f'''
<div class="row mt3" style="grid-template-columns:150mm 1fr;align-items:start">
<div>{shot('praca-agora')}</div>
<div style="display:grid;gap:4.6mm;padding-top:1mm">
{pt('building-2', 'var(--coral)', '#ffe9bd', '5 casas para explorar', 'Casas, árvores e enfeites de papel pintado que se levantam do chão quando a criança chega perto.')}
{pt('pen-line', 'var(--lilac)', '#ece3fa', 'Missões que viram história', 'Em 4 casas a criança escreve uma parte da sua história: personagem, cenário, problema e final.')}
{pt('hammer', 'var(--green)', '#dcf1e1', 'Criar, juntar e colecionar', 'Materiais pela praça, 12 receitas, um álbum de 31 itens e 8 selos de conquista.')}
{pt('sun-snow', 'var(--blue)', '#dcecfb', 'A vila muda com o ano', 'Primavera, verão, outono e inverno, no calendário do Brasil.')}
</div>
</div>
<div class="row mt3" style="grid-template-columns:repeat(5,1fr);gap:3.6mm">{hh}</div>
'''
pages.append(page('A vila', 'trees', 'Uma vila de livro pop-up', 'É uma vila de papel pintado, feita para a criança andar, descobrir e escrever.', body, 3))

# 4 meu cantinho
body = f'''
<div class="row mt3" style="grid-template-columns:1fr 1fr">
<div>{shot('cant-ext')}</div>
<div>{shot('cant-int')}</div>
</div>
<div class="row mt4" style="grid-template-columns:repeat(3,1fr);gap:7mm">
{pt('paintbrush', 'var(--coral)', '#ffe0d8', 'Pinta a casa', 'Escolhe a cor da parede, do telhado e da porta. O papel de parede de dentro acompanha a cor.')}
{pt('flower-2', 'var(--green)', '#dcf1e1', 'Planta flores', 'As flores do canteiro crescem com o tempo, da semente até a flor cheia.')}
{pt('sparkles', 'var(--lilac)', '#ece3fa', 'Decora com o que criou', 'Enfeites de porta, janela, jardim e de dentro de casa. Um quadro mostra um pedacinho da história dela.')}
</div>
<div class="safe mt4" style="background:#ffe9bd">{ic('award', 24, 'var(--coral)')}<p><b>Missão opcional: Decore seu cantinho.</b> Colocar um enfeite que ela criou e plantar uma flor rende o selo <b>Cantinho Decorado</b>. A casa também muda com as estações: neve no inverno, flores na primavera, folhas no outono.</p></div>
'''
pages.append(page('Segunda fase · Meu Cantinho', 'house', 'Uma casinha só dela', 'Depois do primeiro selo de Autor(a), cada criança ganha um lote na Rua dos Cantinhos: um lugar para voltar, decorar e mostrar aos colegas.', body, 4))

# 5 turma se encontra
body = f'''
<div class="row mt3" style="grid-template-columns:repeat(3,1fr);gap:5mm;align-items:start">
<div>{shot('p-020-314')}<div class="lab">Na praça<small>A Luna encontra o Theo.</small></div></div>
<div>{shot('p-017-150')}<div class="lab">No cantinho<small>O Theo visita a casa da Luna.</small></div></div>
<div>{shot('p-020-315')}<div class="lab">No Correio<small>O mural da turma.</small></div></div>
</div>
<div class="row mt4" style="grid-template-columns:repeat(4,1fr);gap:5mm">
{pt('users', 'var(--coral)', '#ffe0d8', 'A praça é da turma', 'Os colegas se veem andando juntos, ao vivo, cada um com o seu personagem.')}
{pt('door-open', 'var(--lilac)', '#ece3fa', 'Visitas', 'Pela caixa de correio, a criança visita o cantinho dos colegas. Visita olha e senta, mas não muda nada.')}
{pt('pin', 'var(--blue)', '#dcecfb', 'Mural, varal e presentes', 'Figurinhas no mural, os personagens da turma no varal e presentes entre amigos.')}
{pt('trees', 'var(--green)', '#dcf1e1', 'Baú da Turma', 'Juntos, a turma doa flores, fitas e gravetos e faz aparecer o Arco da Turma na praça.')}
</div>
<div class="safe mt4">{ic('shield-check', 24, 'var(--teal)')}<p><b>Segurança em primeiro lugar.</b> Só crianças da mesma turma se encontram, aparece apenas o primeiro nome, e a figurinha de cada uma só aparece para os colegas depois que a professora aprova.</p></div>
'''
pages.append(page('Jogar junto', 'users', 'É aqui que a turma se encontra', 'Cada turma tem a sua sala na vila. Dentro da história de cada criança, a turma vira uma comunidade.', body, 5))

# 6 professora
body = f'''
<div class="row mt3" style="grid-template-columns:172mm 1fr;gap:6mm;align-items:start">
<div class="row" style="gap:4mm">
{shot('p-023-322')}
{shot('p-024-324')}
</div>
<div style="display:grid;gap:3.6mm">
{pt('log-in', 'var(--coral)', '#ffe0d8', 'Abre e escolhe a turma', 'Com o código do colégio. Funciona no computador, no tablet e no celular.')}
{pt('bar-chart-3', 'var(--lilac)', '#ece3fa', 'Vê a turma de relance', 'Quem já entrou, quem está na vila agora e quem já escreveu o título e a primeira frase.')}
{pt('route', 'var(--blue)', '#dcecfb', 'Sabe até onde cada um foi', 'Barra de progresso, missões e selos de cada criança.')}
{pt('file-text', 'var(--green)', '#dcf1e1', 'Lê o que a criança escreveu', 'Personagem, cenário, problema e final, tudo no cartão da criança.')}
{pt('thumbs-up', 'var(--coral)', '#ffe9bd', 'Aprova as figurinhas', 'A turma só vê o personagem depois do OK da professora.')}
{pt('copy', 'var(--teal)', '#d3f1ee', 'Leva os textos para o livro', 'Um botão copia os textos da turma para o documento do livro.')}
</div>
</div>
<div class="row mt4" style="grid-template-columns:repeat(3,1fr);gap:5mm">
<div class="box b-amber" style="padding:3mm 4mm"><h4>{ic('clock', 15, 'var(--coral)')} Antes · 5 min</h4><p>Abre o painel e testa o jogo num aparelho.</p></div>
<div class="box b-lilac" style="padding:3mm 4mm"><h4>{ic('play', 15, 'var(--coral)')} Durante a aula</h4><p>A Pena conduz a criança. A professora acompanha pelo painel quem travou.</p></div>
<div class="box b-green" style="padding:3mm 4mm"><h4>{ic('clipboard-check', 15, 'var(--green)')} Depois · 5 min</h4><p>Aprova as figurinhas, lê as partes e copia os textos para o livro.</p></div>
</div>
'''
pages.append(page('Para a professora', 'clipboard-list', 'O que a professora vê e acompanha', 'O painel é a tela da professora na vila. Nada técnico: ela abre, escolhe a turma e vê.', body, 6))

# 7 quem ganha + CTA
def who(color, icon, title, items):
    li = ''.join(f'<li>{ic("check", 15, "var(--green)", 3)}<span>{t}</span></li>' for t in items)
    return f'<div class="who"><div class="wh" style="background:{color}">{ic(icon, 20, "var(--ink)")} {title}</div><ul>{li}</ul></div>'

body = f'''
<div class="row mt3" style="grid-template-columns:repeat(4,1fr);gap:4mm">
{who('#ffe0d8', 'smile', 'A criança', ['Vê o próprio desenho ganhar vida e andar pela vila.', 'Escreve a história parte por parte, com a Pena e ideias prontas.', 'Ganha selos e uma casinha para decorar.'])}
{who('#ffe9bd', 'heart', 'A família', ['A criança continua de onde parou, em casa, com o QR e a senha do livro.', 'Um livro de verdade para a estante, com a história que ela escreveu.', 'A história de papel e a da tela se encontram.'])}
{who('#ece3fa', 'graduation-cap', 'A professora', ['Painel com o progresso e os textos da turma.', 'Sabe quem travou sem passar de mesa em mesa.', 'Leva os textos da vila direto para o livro.'])}
{who('#d3f1ee', 'school', 'A escola', ['Tecnologia na sala com propósito: a criança escreve.', 'Um diferencial que a família vê, fotografa e comenta.', 'Privacidade cuidada: primeiro nome, mesma turma e figurinha aprovada.'])}
</div>
<div class="row mt5" style="grid-template-columns:1fr 1fr;gap:5mm">
<div class="box b-amber qrw" style="padding:4mm 5mm"><img src="assets/qr-vila.svg" alt=""><div><h3 style="font-size:15pt">Experimente a Vila</h3><p style="font-size:10pt;line-height:1.4;margin-top:1.6mm">Aponte a câmera do celular e toque em <b>Entrar como visitante</b> para passear pela praça.</p><p style="font-size:9pt;margin-top:1.6mm;font-weight:700">fabricadeautores.com.br/vila</p></div></div>
<div class="box b-lilac" style="padding:4mm 5mm;display:flex;flex-direction:column;justify-content:center"><h3 style="font-size:15pt">Vamos fazer na sua escola?</h3><p style="font-size:10pt;line-height:1.4;margin-top:1.6mm">Uma conversa de 30 minutos: a gente leva um livro pronto na mão, você escolhe uma turma para começar e montamos juntos o calendário até a tarde de autógrafos.</p>
<p style="font-size:10.4pt;margin-top:2.6mm;font-weight:800;display:flex;gap:2mm;align-items:center">{ic('phone', 16, 'var(--coral)')} WhatsApp (81) 95168-7966 {ic('globe', 16, 'var(--coral)')} fabricadeautores.com.br</p></div>
</div>
'''
pages.append(page('Benefícios', 'sparkles', 'O que cada um ganha', 'A Vila dos Autores faz o livro render mais do que as folhas: a história ganha lugar, personagem e turma.', body, 7))

html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Vila dos Autores · Apresentação para a direção</title><style>{CSS}</style></head><body>' + ''.join(pages) + '</body></html>'
open(os.path.join(BASE, 'dir.html'), 'w').write(html)
print('ok', len(pages))
