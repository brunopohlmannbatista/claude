import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import ic, qr, CSS_BASE

BASE = os.path.dirname(os.path.abspath(__file__))
qr('https://fabricadeautores.com.br/vila/', os.path.join(BASE, 'assets/qr-vila.svg'))
qr('https://fabricadeautores.com.br/vila/professora/', os.path.join(BASE, 'assets/qr-painel.svg'))

CSS = CSS_BASE + '''
@page{size:210mm 297mm;margin:0}
.page{width:210mm;height:297mm;padding:13mm 14mm 16mm}
.hd .tag{font:800 8.4pt "PJS";letter-spacing:.14em;text-transform:uppercase;color:var(--coral);display:flex;gap:2mm;align-items:center}
.hd h2{font-size:24pt;line-height:1.05;margin-top:1.6mm}
.hd .lead{font-size:10.4pt;line-height:1.45;margin-top:2.6mm}
.ft{position:absolute;left:14mm;right:14mm;bottom:6.5mm;display:flex;justify-content:space-between;font:600 7.6pt "PJS";color:var(--mute);border-top:1.4px solid var(--ink);padding-top:1.8mm}
.grid{display:grid;gap:4mm}
.g2{grid-template-columns:1fr 1fr}
.g3{grid-template-columns:1fr 1fr 1fr}
.mt2{margin-top:2.5mm}.mt4{margin-top:4.5mm}.mt6{margin-top:6.5mm}
.cover{background:var(--dark);color:#fff;padding:0}
.cover .top{padding:14mm 15mm 0}
.cover .brand{display:flex;align-items:center;gap:2.6mm;font:800 9pt "PJS";letter-spacing:.16em;text-transform:uppercase;color:var(--amber)}
.diam{width:3.6mm;height:3.6mm;background:var(--coral);transform:rotate(45deg);display:inline-block}
.cover h1{font-size:50pt;line-height:.95;margin-top:7mm;color:#fff}
.cover h1 span{color:var(--amber)}
.cover .sub{font-size:13pt;line-height:1.4;margin-top:5mm;max-width:150mm;color:#f2e7ff}
.cover .hero{position:absolute;left:15mm;right:15mm;top:104mm;height:150mm;border:2.4px solid var(--amber);border-radius:12px;overflow:hidden}
.cover .hero img{width:100%;height:100%;object-fit:cover;display:block}
.cover .chips{position:absolute;left:15mm;right:15mm;top:262mm;display:flex;gap:3mm;flex-wrap:wrap}
.cover .chip{background:var(--dark);border-color:var(--amber);color:#fff}
.cover .foot{position:absolute;left:15mm;right:15mm;bottom:9mm;display:flex;justify-content:space-between;font:600 8.2pt "PJS";color:#cdbbe6}
.flow{display:grid;grid-template-columns:1fr 9mm 1fr 9mm 1fr;align-items:stretch;margin-top:4mm}
.flow .arrow{display:flex;align-items:center;justify-content:center;color:var(--coral)}
.step{border:2px solid var(--ink);border-radius:10px;background:#fff;padding:3.6mm 4mm}
.step h3{font-size:12.6pt;margin-top:1.8mm}
.step p{font-size:9.2pt;line-height:1.4;margin-top:1.4mm}
.stats{display:grid;grid-template-columns:repeat(7,1fr);gap:2.4mm;margin-top:4mm}
.stat{border:2px solid var(--ink);border-radius:10px;background:var(--paper);padding:2.6mm 1mm;text-align:center}
.stat b{display:block;font:900 19pt "GS";line-height:1}
.stat span{display:block;font:700 7.4pt "PJS";line-height:1.2;margin-top:1.2mm}
.jour{display:grid;grid-template-columns:repeat(5,1fr);gap:3mm;margin-top:3.6mm}
.jc{border:2px solid var(--ink);border-radius:10px;background:#fff;padding:3mm 2.6mm;position:relative;min-height:33mm}
.jc .num{position:absolute;top:-3.4mm;left:2.4mm}
.jc h5{font:800 9.2pt "PJS";margin-top:3mm;line-height:1.2}
.jc p{font-size:8.2pt;line-height:1.35;margin-top:1mm}
.kbd{display:inline-block;border:1.6px solid var(--ink);border-radius:5px;padding:0 1.8mm;font:800 8.4pt "PJS";background:#fff;min-width:5.2mm;text-align:center}
table.t{width:100%;border-collapse:collapse;font-size:9pt}
table.t td{padding:1.5mm 1mm;border-top:1.3px solid #cbb9a0;vertical-align:top;line-height:1.35}
table.t tr:first-child td{border-top:0}
table.t td:first-child{white-space:nowrap;padding-right:3mm}
.pill{display:inline-block;border-radius:99px;padding:.6mm 2.4mm;font:800 7.6pt "PJS";letter-spacing:.04em;text-transform:uppercase;border:1.5px solid var(--ink);background:var(--amber)}
.rec{display:flex;align-items:center;gap:1.6mm;flex-wrap:wrap;font-size:8.8pt;font-weight:700}
.ing{display:inline-block;border:1.5px solid var(--ink);border-radius:6px;background:#fff;padding:.5mm 2mm;font-weight:700;font-size:8.2pt}
.seal{display:flex;gap:2.4mm;align-items:flex-start;border:1.6px solid var(--ink);border-radius:9px;background:#fff;padding:2mm 2.6mm}
.seal b{font-size:8.8pt;display:block;line-height:1.2}
.seal span{font-size:7.9pt;line-height:1.3;display:block;margin-top:.4mm}
.sealico{width:8mm;height:8mm;border-radius:50%;background:var(--amber);border:1.6px solid var(--ink);display:flex;align-items:center;justify-content:center;flex:none}
.qrbox{display:flex;gap:4mm;align-items:center}
.qrbox img{width:27mm;height:27mm;display:block;background:#fff;padding:1.6mm;border:2px solid var(--ink);border-radius:8px}
'''

TOTAL = 11


def shot(img, h=None, cls='', style='', pos=''):
    # h e ignorado de proposito: as telas mantem a proporcao natural (sem cortar).
    p = f' style="object-position:{pos}"' if pos else ''
    return f'<div class="shot {cls}" style="{style}"><img src="assets/img/{img}.jpg" alt=""{p}></div>'



def cap(n, text):
    return f'<div class="cap"><span class="num">{n}</span><div>{text}</div></div>'


def page(tag, icon, title, lead, body, n):
    return f'''<section class="page">
<div class="hd"><div class="tag">{ic(icon, 15, 'var(--coral)')} {tag}</div><h2>{title}</h2>{('<p class="lead">' + lead + '</p>') if lead else ''}</div>
{body}
<div class="ft"><span>Vila dos Autores · Guia da coordenação</span><span>Fábrica de Autores · {n}</span></div>
</section>'''


pages = []

# 1 capa
pages.append(f'''<section class="page cover">
<div class="top">
<div class="brand"><span class="diam"></span> Fábrica de Autores apresenta</div>
<h1>Vila dos<br><span>Autores</span></h1>
<p class="sub">Guia da coordenação: como o jogo funciona, passo a passo, e o que a professora acompanha.</p>
</div>
<div class="hero"><img src="assets/img/praca-agora.jpg" alt=""></div>
<div class="chips">
<span class="chip">{ic('gamepad-2', 14, 'var(--amber)')} Fase 1 · Chegada na Vila</span>
<span class="chip">{ic('house', 14, 'var(--amber)')} Fase 2 · Meu Cantinho</span>
<span class="chip">{ic('clipboard-list', 14, 'var(--amber)')} Painel da professora</span>
</div>
<div class="foot"><span>Para a coordenação pedagógica</span><span>Fábrica de Autores · Recife, PE</span></div>
</section>''')

# 2 visao geral
jour = [
    ('qr-code', 'Entrar', 'QR do livro e senha de 4 letras ou números.'),
    ('user-round', 'Personagem', 'O desenho do livro vira o boneco.'),
    ('bird', 'A Pena', 'A guardiã das histórias recebe na praça.'),
    ('hammer', 'Criar', 'Junta materiais e faz a primeira Guirlanda.'),
    ('house', 'Casa da Pena', 'Ideia, título, primeira frase, lareira e folhas.'),
    ('award', 'Selo de Autor(a)', 'Abre as 4 casas de missões.'),
    ('pen-line', '4 missões', 'Personagem, cenário, problema e final.'),
    ('book-open', 'O livro', 'Página Ilustrada, Capa e Mini-livro.'),
    ('flower-2', 'Meu Cantinho', 'Uma casinha só dela, com jardim.'),
    ('mail', 'Decorar e visitar', 'Enfeites, flores e visita aos colegas.'),
]
j = ''.join(f'<div class="jc"><span class="num">{i + 1}</span>{ic(ico, 20, "var(--lilac)")}<h5>{t}</h5><p>{d}</p></div>' for i, (ico, t, d) in enumerate(jour))
body = f'''
<div class="flow">
<div class="step b-amber">{ic('book-open', 22, 'var(--coral)')}<h3>O livro de papel</h3><p>Cada livro traz um <b>QR Code</b> e uma <b>senha de 4 letras ou números</b>. Ela é a chave da criança.</p></div>
<div class="arrow">{ic('arrow-right', 26, 'var(--coral)', 2.6)}</div>
<div class="step b-lilac">{ic('gamepad-2', 22, 'var(--coral)')}<h3>A Vila dos Autores</h3><p>O desenho vira personagem. A criança explora, cria e escreve a história em <b>4 partes</b>.</p></div>
<div class="arrow">{ic('arrow-right', 26, 'var(--coral)', 2.6)}</div>
<div class="step b-teal">{ic('clipboard-list', 22, 'var(--coral)')}<h3>O painel da professora</h3><p>Ela lê o que cada criança escreveu e <b>leva os textos para o livro</b>.</p></div>
</div>
<div class="stats">
<div class="stat"><b>2</b><span>fases</span></div>
<div class="stat"><b>5</b><span>casas na vila</span></div>
<div class="stat"><b>4</b><span>missões de escrita</span></div>
<div class="stat"><b>12</b><span>receitas</span></div>
<div class="stat"><b>31</b><span>itens no álbum</span></div>
<div class="stat"><b>8</b><span>selos</span></div>
<div class="stat"><b>4</b><span>estações do ano</span></div>
</div>
<h3 class="mt6" style="font-size:15pt">O caminho da criança, em 10 passos</h3>
<div class="jour" style="grid-template-columns:repeat(5,1fr)">{j}</div>
<div class="box b-green mt6"><h4>{ic('info', 15, 'var(--green)')} Como a criança sabe o que fazer</h4>
<p>O quadro de missões, no canto da tela, mostra a tarefa de agora e marca a tarefa como feita quando ela fica pronta. Um balão azul com “!” em cima de uma casa avisa que tem missão nova lá dentro. A Pena explica cada passo com <b>voz gravada</b>, e o texto na tela é igual ao áudio.</p></div>
'''
pages.append(page('Visão geral', 'map', 'O livro e a vila se conversam',
                  'Na Vila dos Autores, a criança entra com o personagem que desenhou no próprio livro. Junto com a Pena, ela explora a vila, cria coisas com materiais e, casa por casa, monta a sua história. Com o selo de Autor(a), ganha também o seu Meu Cantinho.', body, 2))

# 3 entrar e personagem
body = f'''
<div class="grid g2 mt2">
<div>{shot('p-004-020', 62)}{cap(1, '<b>Tela de entrada.</b> A criança digita a senha e toca em <b>Entrar com meu código</b>. A vila procura o livro dela e já traz os desenhos digitalizados.')}</div>
<div>{shot('p-005-031', 62)}{cap(2, '<b>Escolha do personagem.</b> Os desenhos do livro aparecem primeiro. Dá para mandar a foto de um desenho ou escolher um personagem pronto (Lia, Dino, Miau e Bip).')}</div>
</div>
<div class="grid g2 mt4">
<div class="box b-amber"><h4>{ic('key-round', 15, 'var(--coral)')} Como a criança entra</h4>
<ul>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Aponta a câmera para o <b>QR Code do livro</b> ou digita o endereço do jogo.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Digita a <b>senha do livro</b> (pode ser em minúscula, a vila arruma).</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>A vila diz “Oi” com o nome dela e mostra os desenhos do livro.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>O progresso fica <b>salvo no servidor</b>: ela continua em outro computador ou tablet com o mesmo código.</span></li>
</ul></div>
<div class="box b-lilac"><h4>{ic('scissors', 15, 'var(--coral)')} Como o desenho vira boneco</h4>
<ul>
<li>{ic('check', 14, 'var(--green)', 3)}<span>A vila tira o papel, a moldura e as linhas sozinha.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Página com cenário? Toca em <b>Escolher só o personagem</b> e faz um retângulo em volta dele.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>O desenho vira uma <b>figurinha</b>. Os colegas só a veem depois que a professora aprova.</span></li>
</ul></div>
</div>
<div class="grid g2 mt4">
<div>{shot('p-005-030', 52)}{cap(3, '<b>Recorte do personagem.</b> A criança marca o desenho na página e a vila faz o resto.')}</div>
<div class="grid" style="gap:3.5mm;align-content:start">
<div class="box b-coral"><h4>{ic('circle-help', 15, 'var(--coral)')} Perdeu a senha?</h4><p>Ela está no livro e nas folhas da criança. A coordenação também tem a lista da turma, e a professora vê a senha ao lado do nome, no painel. Sem senha dá para entrar como <b>visitante</b>, mas o progresso não fica guardado.</p></div>
<div class="box b-blue"><h4>{ic('users', 15, 'var(--coral)')} Dois alunos no mesmo aparelho</h4><p>Ao terminar, a criança abre <b>Selos</b> e toca em <b>Sair (outra criança vai jogar)</b>. A próxima entra com o código dela.</p></div>
</div>
</div>
'''
pages.append(page('Passos 1 e 2', 'qr-code', 'Entrar com o livro e escolher o personagem', 'O QR e a senha do livro abrem a vila. É o desenho da própria criança que anda por ela.', body, 3))

# 4 praca, Pena e criar
body = f'''
<div class="grid g2 mt2">
<div>{shot('p-006-034', 56)}{cap(1, '<b>A Pena recebe na praça.</b> “Oi! Que bom que você chegou na Vila dos Autores!” Toda fala tem voz, e o botão “Ler em voz alta” repete.')}</div>
<div>{shot('p-006-037', 56)}{cap(2, '<b>Primeira missão:</b> 3 flores e 1 graveto. É só passar por cima. Tudo vai para a Mochila e o primeiro de cada item entra no Álbum.')}</div>
</div>
<div class="grid g2 mt4">
<div>{shot('p-007-050', 56)}{cap(3, '<b>Livro de Receitas.</b> A receita que já dá para fazer fica destacada. A primeira é a Guirlanda.')}</div>
<div>{shot('p-007-056', 56)}{cap(4, '<b>Colocar o enfeite.</b> Na Mochila, a criança escolhe a Guirlanda e leva até a porta de uma casa. A tecla R gira o enfeite.')}</div>
</div>
<div class="grid g2 mt4">
<div class="box"><h4>{ic('monitor', 15, 'var(--coral)')} No computador</h4>
<table class="t">
<tr><td><span class="kbd">{ic('arrow-left',11)}</span> <span class="kbd">{ic('arrow-up',11)}</span> <span class="kbd">{ic('arrow-right',11)}</span> <span class="kbd">{ic('arrow-down',11)}</span></td><td>ou W A S D: andar pela vila</td></tr>
<tr><td><span class="kbd">E</span> <span class="kbd">Enter</span></td><td>falar, entrar nas casas e usar as coisas</td></tr>
<tr><td><span class="kbd">C</span> <span class="kbd">I</span> <span class="kbd">L</span></td><td>Receitas, Mochila e Álbum</td></tr>
<tr><td><span class="kbd">R</span> <span class="kbd">Esc</span></td><td>gira o enfeite · fecha a janela</td></tr>
</table></div>
<div class="box"><h4>{ic('smartphone', 15, 'var(--coral)')} No tablet e no celular</h4>
<ul>
<li>{ic('hand', 14, 'var(--lilac)')}<span>Toque no chão para ir até lá, ou arraste o dedo como num controle.</span></li>
<li>{ic('tag', 14, 'var(--lilac)')}<span>Perto de algo aparece uma etiqueta: toque nela para usar.</span></li>
<li>{ic('message-circle', 14, 'var(--lilac)')}<span>Toque na tela para passar as falas da Pena.</span></li>
</ul></div>
</div>
<div class="box b-teal mt4"><h4>{ic('lightbulb', 15, 'var(--teal)')} Para a coordenação saber</h4>
<p>O jogo <b>salva sozinho</b> enquanto a criança joga (a hora aparece em Selos). A vila é um livro pop-up: as casas e as árvores de papel pintado se levantam do chão quando a criança chega perto. Funciona no navegador, sem instalar nada.</p></div>
'''
pages.append(page('Passos 3 e 4', 'bird', 'A praça, a Pena e as primeiras criações', 'A criança aprende a andar, juntar materiais e criar coisas antes de começar a escrever.', body, 4))

# 5 casa da pena e selo
body = f'''
<div class="grid g2 mt2">
<div>{shot('p-008-067', 58)}{cap(1, '<b>A Casa da Pena</b> é a amarelinha de telhado vermelho. Lá dentro: o Caderno de Ideias, a lareira, o Baú de Conquistas e a Mesa de Criação.')}</div>
<div>{shot('p-008-068', 58)}{cap(2, '<b>Caderno de Ideias.</b> Na aba “Minha história”, a criança escreve o <b>título</b> e a <b>primeira frase</b>. Há ideias prontas para tocar.')}</div>
</div>
<div class="grid g2 mt4">
<div class="box b-amber"><h4>{ic('list-checks', 15, 'var(--coral)')} As 4 tarefas da Pena</h4>
<ul>
<li>{ic('notebook-pen', 15, 'var(--lilac)')}<span>Guardar uma ideia no Caderno de Ideias.</span></li>
<li>{ic('pen-line', 15, 'var(--lilac)')}<span>Escrever o título e a primeira frase.</span></li>
<li>{ic('flame', 15, 'var(--coral)')}<span>Acender a lareira.</span></li>
<li>{ic('leaf', 15, 'var(--green)')}<span>Achar 3 folhas douradas escondidas na casa. Elas brilham, mas vale olhar atrás dos móveis.</span></li>
</ul></div>
<div class="box b-coral"><h4>{ic('book-marked', 15, 'var(--coral)')} Isso vai para o livro</h4>
<p>O <b>título</b> aparece na Capa e a <b>primeira frase</b> aparece na Página Ilustrada. A professora vê os dois no painel.</p>
<p class="mt2">Já na primeira casa a criança escreve de verdade: é a primeira parte do livro dela.</p></div>
</div>
<div class="grid g2 mt4" style="grid-template-columns:1.05fr .95fr;align-items:start">
<div>{shot('p-009-074', 58)}{cap(3, '<b>Baú de Conquistas.</b> Com as 4 tarefas prontas, a criança abre o baú: confete e o selo de <b>Autor(a) da Vila</b>.')}</div>
<div class="box b-green"><h4>{ic('award', 15, 'var(--green)')} O que o selo abre</h4>
<ul>
<li>{ic('book-open', 15, 'var(--green)')}<span>As receitas do livro: Página Ilustrada (Ateliê), Capa e Mini-livro (Gráfica).</span></li>
<li>{ic('star', 15, 'var(--green)')}<span>As missões da história nas outras 4 casas, em qualquer ordem.</span></li>
<li>{ic('package', 15, 'var(--green)')}<span>As caixas de capas da Gráfica.</span></li>
<li>{ic('flower-2', 15, 'var(--green)')}<span>O caminho para o Meu Cantinho (Fase 2).</span></li>
</ul>
<p class="mt2">A Pena volta para a praça e fica esperando. As casas com missão ganham um balão azul com “!”.</p></div>
</div>
'''
pages.append(page('Passos 5 e 6', 'house', 'A Casa da Pena e o selo de Autor(a)', 'Aqui a criança começa a escrever. Quando termina as 4 tarefas, ganha o selo que libera o resto da vila.', body, 5))

# 6 as 4 missoes
def mis(img, icon, casa, pergunta, texto, premio):
    return f'''<div>{shot(img, 47)}
<div class="box mt2" style="padding:3mm 3.6mm"><h4 style="margin-bottom:1mm">{ic(icon, 15, 'var(--coral)')} {casa}</h4>
<p><b>{pergunta}</b> {texto}</p>
<p style="margin-top:1.2mm;font-size:8.4pt"><span class="pill">Prêmio</span> {premio}</p></div></div>'''

body = f'''
<div class="grid g2 mt2" style="gap:4mm 4.5mm">
{mis('p-011-097', 'library', 'Biblioteca · o personagem', 'Quem é o personagem?', 'Nome, do que ele mais gosta e do que tem medo. É isso que faz a gente torcer por ele.', 'Fita e Botão')}
{mis('p-011-098', 'palette', 'Ateliê de Desenho · o cenário', 'Onde a história acontece?', 'O lugar, a cor, o som e o cheiro. Assim quem lê consegue imaginar que está lá dentro.', '2 Tintas')}
{mis('p-011-099', 'printer', 'Gráfica · o problema', 'O que dá errado?', 'Toda história boa tem um problema. E quem ajuda a resolver? Isso deixa tudo emocionante.', 'Capa em branco e Papel')}
{mis('p-011-100', 'mail', 'Correio das Histórias · o final', 'Como termina?', 'O tipo de final, a última frase e para quem a criança vai mandar a história.', 'Fita e Folha dourada')}
</div>
<div class="grid g3 mt4">
<div class="box b-amber"><h4>{ic('mouse-pointer-click', 15, 'var(--coral)')} Como funciona</h4><p>Dentro da casa, a criança chega perto da <b>placa amarela de MISSÃO</b>. A Pena explica, com voz, o que é aquela parte. Depois ela escreve ou toca nas ideias prontas e confirma em <b>Pronto!</b></p></div>
<div class="box b-lilac"><h4>{ic('lightbulb', 15, 'var(--coral)')} Ideias prontas</h4><p>São só um empurrãozinho. Vale escrever do jeito dela. Missão pronta vira <b>Rever a missão</b>: dá para ler e mudar.</p></div>
<div class="box b-green"><h4>{ic('scroll-text', 15, 'var(--green)')} Fica tudo junto</h4><p>As 4 partes aparecem em “Minha história”, no Baú da Casa da Pena. Com as 4 prontas, a Pena parabeniza e a criança ganha o selo <b>História Completa</b>.</p></div>
</div>
'''
pages.append(page('Passo 7', 'pen-line', 'Quatro casas, quatro partes da história', 'Cada casa ensina uma parte e pede que a criança escreva a dela. É assim que a história é planejada, sem prova e sem folha em branco.', body, 6))

# 7 historia vira livro + album e selos
seals = [
    ('award', 'Autor(a) da Vila', 'Completou as tarefas da Casa da Pena.'),
    ('compass', 'Explorador(a) da Vila', 'Visitou as 5 casas.'),
    ('leaf', 'Caçador(a) de Folhas Douradas', 'Achou as 9 folhas douradas.'),
    ('hammer', 'Mãos de Artesã(o)', 'Criou 5 coisas no Livro de Receitas.'),
    ('library', 'Primeiro Mini-livro', 'Encadernou um mini-livro na Gráfica.'),
    ('scroll-text', 'História Completa', 'Personagem, cenário, problema e final.'),
    ('notebook', 'Colecionador(a)', 'Encontrou os 31 itens do álbum.'),
    ('house', 'Cantinho Decorado', 'Decorou o cantinho e plantou uma flor.'),
]
sl = ''.join(f'<div class="seal"><div class="sealico">{ic(i, 15, "var(--ink)")}</div><div><b>{t}</b><span>{d}</span></div></div>' for i, t, d in seals)
body = f'''
<div class="grid g3 mt2">
<div class="box b-amber"><h4>{ic('book-image', 15, 'var(--coral)')} Página Ilustrada</h4>
<p>Mesa do Ateliê.</p>
<div class="rec mt2"><span class="ing">Ideia de História</span> + <span class="ing">Desenho</span></div>
<p class="mt2" style="font-size:8.6pt">A Ideia vem do Caderno da Pena. O Desenho, do cavalete do Ateliê. Mostra o desenho com a primeira frase.</p></div>
<div class="box b-lilac"><h4>{ic('book-open', 15, 'var(--coral)')} Capa do Livro</h4>
<p>Mesa da Gráfica.</p>
<div class="rec mt2"><span class="ing">Capa em Branco</span> + <span class="ing">Nome do Personagem</span> + <span class="ing">Tinta</span></div>
<p class="mt2" style="font-size:8.6pt">O personagem, o título e “por” com o nome da criança.</p></div>
<div class="box b-teal"><h4>{ic('library', 15, 'var(--coral)')} Mini-livro Encadernado</h4>
<p>Mesa da Gráfica.</p>
<div class="rec mt2"><span class="ing">5 Páginas Ilustradas</span> + <span class="ing">Fita</span></div>
<p class="mt2" style="font-size:8.6pt">Ganha o selo Primeiro Mini-livro.</p></div>
</div>
<div class="grid g2 mt4">
<div>{shot('p-019-312', 56)}{cap(1, '<b>Álbum de Vila.</b> Guarda cada item que a criança encontra ou cria. Os que faltam aparecem com uma dica. São 31 itens.')}</div>
<div>{shot('p-019-313', 56)}{cap(2, '<b>Selos e conquistas.</b> Mostra os selos, a estação, se está tudo salvo e a figurinha.')}</div>
</div>
<h3 class="mt4" style="font-size:13.5pt">Os 8 selos</h3>
<div class="grid g2 mt2" style="gap:2.4mm 3mm">{sl}</div>
<div class="box b-coral mt4"><h4>{ic('copy', 15, 'var(--coral)')} Da vila para o livro de papel</h4>
<p>A professora usa o botão <b>Copiar os textos da turma</b>, no painel. Ele junta título, primeira frase e as 4 partes de todas as crianças. É só colar no documento de digitação do livro e revisar com cada autor.</p></div>
'''
pages.append(page('Passo 8', 'book-open', 'A história completa vira livro', 'O que a criança escreve na vila é a matéria-prima do livro. As receitas do livro e os selos mostram cada etapa vencida.', body, 7))

# 8 meu cantinho
body = f'''
<div class="grid g2 mt2">
<div>{shot('cant-ext', 58)}{cap(1, '<b>A casinha de cada criança.</b> Casa, jardim com cerca, canteiro e um quadro com um pedacinho da história dela.')}</div>
<div>{shot('cant-int', 58)}{cap(2, '<b>Por dentro.</b> A casa abre como uma casinha de boneca, com o papel de parede na cor escolhida. Os objetos dão um pulinho quando ela chega perto.')}</div>
</div>
<div class="grid g3 mt4">
<div class="box b-amber"><h4>{ic('map-pin', 15, 'var(--coral)')} Como chegar</h4>
<ul>
<li><span class="num" style="width:5mm;height:5mm;font-size:8pt">1</span><span>Só depois do selo de Autor(a).</span></li>
<li><span class="num" style="width:5mm;height:5mm;font-size:8pt">2</span><span>Na praça, seguir o <b>caminho de flores</b> até o portal Meu Cantinho.</span></li>
<li><span class="num" style="width:5mm;height:5mm;font-size:8pt">3</span><span>Voltar pela placa Praça da Vila.</span></li>
</ul></div>
<div class="box b-lilac"><h4>{ic('paintbrush', 15, 'var(--coral)')} Pintar e enfeitar</h4>
<p>Na latinha de tinta: <b>6 cores</b> para a parede, 6 para o telhado e 6 para a porta e a caixa de correio. Cabem 3 decorações no jardim e 3 dentro, além da porta e da janela.</p></div>
<div class="box b-green"><h4>{ic('flower-2', 15, 'var(--green)')} O canteiro cresce</h4>
<p>Flor Plantada = Semente + Água da fonte. Semente na hora, brotinho em 2 min, flor em 5 min e flor cheia em 30 min. Cabem 3 flores.</p></div>
</div>
<div class="grid g2 mt4">
<div class="box b-coral"><h4>{ic('house', 15, 'var(--coral)')} O que tem dentro de casa</h4>
<table class="t">
<tr><td><b>Cama</b></td><td>deitar um pouquinho</td></tr>
<tr><td><b>Escrivaninha</b></td><td>senta e abre “Minha história”</td></tr>
<tr><td><b>Estantinha</b></td><td>mostra o Mini-livro, quando fica pronto</td></tr>
<tr><td><b>Janela</b></td><td>uma vista diferente em cada estação</td></tr>
<tr><td><b>Luminária</b></td><td>acende e apaga; de fora, a janela acende</td></tr>
<tr><td><b>Baú</b></td><td>selos, criações e o que está no cantinho</td></tr>
</table></div>
<div class="grid" style="gap:3.5mm;align-content:start">
<div class="box b-teal"><h4>{ic('target', 15, 'var(--teal)')} Missão opcional: Decore seu cantinho</h4>
<ul>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Colocar 1 enfeite criado por ela.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Plantar 1 flor no canteiro.</span></li>
</ul>
<p class="mt2">Ganha o selo <b>Cantinho Decorado</b>, o 8º selo.</p></div>
<div class="box b-blue"><h4>{ic('quote', 15, 'var(--blue)')} Quadro da história</h4>
<p>A criança escolhe o desenho (personagem, capa ou página ilustrada) e o trecho que aparece no quadro, dentro e fora da casa.</p></div>
</div>
</div>
'''
pages.append(page('Fase 2 · Meu Cantinho', 'flower-2', 'Uma casinha só dela', 'Depois do selo de Autor(a), cada criança ganha um lote na Rua dos Cantinhos. É a recompensa que a mantém voltando à vila e à sua história.', body, 8))

# 9 turma na vila
body = f'''
<div class="grid g2 mt2" style="grid-template-columns:1.1fr .9fr;align-items:start">
<div>{shot('p-020-314', 62)}{cap(1, '<b>A Luna encontra o Theo na praça.</b> Quem entra com o código vê os colegas da mesma turma andando pela vila, ao vivo, só com o primeiro nome.')}</div>
<div>{shot('p-017-150', 62)}{cap(2, '<b>Visita ao cantinho.</b> O Theo abre a lista da turma na caixa de correio e escolhe a casa da Luna. Quem visita entra, senta e acende a luz, mas não muda nada.')}</div>
</div>
<div class="grid g2 mt4">
<div>{shot('p-020-315', 50)}{cap(3, '<b>Mural da turma</b>, no Correio: cada criança cola uma figurinha.')}</div>
<div class="grid g2" style="gap:2.4mm">
{shot('p-021-317', 24)}{shot('p-021-318', 24)}{shot('p-021-319', 24)}{shot('p-021-320', 24)}
<div style="grid-column:1/3" class="cap"><span class="num">4</span><div><b>As 4 estações.</b> A vila segue o calendário do Brasil: muda o céu, as árvores, os enfeites, os materiais e a receita da época.</div></div>
</div>
</div>
<div class="grid g3 mt4">
<div class="box b-amber"><h4>{ic('users', 15, 'var(--coral)')} Salas por turma</h4><p>Cada turma tem a sua sala na vila. Só crianças da <b>mesma turma</b> se encontram.</p></div>
<div class="box b-lilac"><h4>{ic('gift', 15, 'var(--coral)')} Presentes e varal</h4><p>Na Mochila, “Dar para colega” manda um item para a caixa de correio dele. No Ateliê, o varal mostra os personagens da turma.</p></div>
<div class="box b-green"><h4>{ic('trees', 15, 'var(--green)')} Baú da Turma</h4><p>Na praça. Juntos, a turma doa 12 flores, 6 fitas e 8 gravetos, e o <b>Arco da Turma</b> aparece para todos.</p></div>
</div>
<div class="box b-teal mt4"><h4>{ic('shield-check', 15, 'var(--teal)')} Privacidade, em resumo</h4>
<ul>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Os colegas veem só o <b>primeiro nome</b> e a figurinha que a professora aprovou. Antes disso, aparece um bonequinho com o nome.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>O trecho da história no quadro do Meu Cantinho aparece <b>só para o dono</b>.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>O servidor guarda do cantinho apenas cores, enfeites, posições e a hora em que cada flor foi plantada.</span></li>
</ul></div>
'''
pages.append(page('Jogar junto', 'users', 'A turma na vila', 'A vila é o lugar onde as crianças da sala se encontram dentro da história de cada uma.', body, 9))

# 10 painel
body = f'''
<div class="grid mt2" style="grid-template-columns:.9fr 1.1fr;gap:4mm;align-items:start">
<div>{shot('p-022-321', None, style='height:34mm', pos='72% 55%')}{cap(1, '<b>Entrada.</b> A professora digita o <b>código de acesso do colégio</b> (6 números, o mesmo que a coordenação usa com a Bia) e escolhe a turma.')}</div>
<div>{shot('p-023-322', None, style='height:auto')}{cap(2, '<b>O mapa da turma.</b> Quatro números no alto: quantas crianças já entraram, quantas estão na vila agora, quantas escreveram título e primeira frase e quantas figurinhas esperam a aprovação.')}</div>
</div>
<div class="grid mt4" style="grid-template-columns:1fr;gap:3mm">
<div>{shot('p-023-323', None, style='height:auto')}{cap(3, '<b>Um cartão por criança.</b> Nome, senha, se está na vila agora, barra de progresso, selos e figurinha.')}</div>
<div>{shot('p-024-324', None, style='height:auto')}{cap(4, '<b>O cartão aberto</b> (“Ver a história e o progresso”): título, primeira frase, as 4 partes, os selos e o que ela já fez na vila.')}</div>
</div>
<div class="grid g3 mt4" style="gap:3mm">
<div class="box b-amber" style="padding:3mm 3.4mm"><h4>{ic('thumbs-up', 15, 'var(--coral)')} Figurinhas</h4><p style="font-size:8.6pt"><b>Aprovar</b>: a turma passa a ver. <b>Recusar</b>: a criança continua jogando. “Aprovar todas” libera de uma vez. Olhe antes se é o desenho dela, sem rosto em foto, nome completo, endereço ou telefone.</p></div>
<div class="box b-lilac" style="padding:3mm 3.4mm"><h4>{ic('refresh-cw', 15, 'var(--coral)')} Atualizar</h4><p style="font-size:8.6pt">O que as crianças fazem chega ao painel em cerca de <b>meio minuto</b>. O painel fica liberado por 12 horas; ao recarregar, pede o código de novo.</p></div>
<div class="box b-green" style="padding:3mm 3.4mm"><h4>{ic('copy', 15, 'var(--green)')} Copiar textos</h4><p style="font-size:8.6pt">Junta título, primeira frase e as 4 partes de toda a turma para colar no documento do livro.</p></div>
</div>
<div class="box b-coral mt4" style="padding:3mm 4mm"><h4>{ic('triangle-alert', 15, 'var(--coral)')} Ponto importante</h4>
<p style="font-size:8.8pt">Quem escreve é a criança. O painel <b>não tem campo para a professora digitar</b> a parte de um aluno: ela lê, copia e aprova. Para escrever junto, abre a vila no aparelho da criança com a <b>senha dela</b> (não com o código do colégio), vai até a casa da parte que falta, toca na placa azul e escreve com ela. Depois, toca em Atualizar no painel.</p></div>
'''
pages.append(page('Para a professora', 'clipboard-list', 'O painel: a tela da professora', 'Funciona no computador, no tablet e no celular, sem instalar nada. Por ele ela vê quem já entrou, até onde cada criança chegou e o que escreveu.', body, 10))

# 11 coordenação
body = f'''
<div class="grid g3 mt2">
<div class="box b-amber"><h4>{ic('clock', 15, 'var(--coral)')} Antes · 5 min</h4>
<ul>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Abrir o painel da turma.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Separar o livro ou a lista de senhas.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Testar o jogo num aparelho, com som.</span></li>
</ul></div>
<div class="box b-lilac"><h4>{ic('play', 15, 'var(--coral)')} Durante</h4>
<ul>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Cada criança entra com a sua senha.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Deixar a Pena conduzir: ela explica cada passo.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Acompanhar pelo painel quem travou.</span></li>
</ul></div>
<div class="box b-green"><h4>{ic('clipboard-check', 15, 'var(--green)')} Depois · 5 min</h4>
<ul>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Aprovar as figurinhas.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Ler as partes escritas.</span></li>
<li>{ic('check', 14, 'var(--green)', 3)}<span>Copiar os textos para o livro.</span></li>
</ul></div>
</div>
<div class="box mt4" style="padding:3.4mm 4mm"><p><b>Meta da primeira aula:</b> cada criança ganhar o selo de <b>Autor(a) da Vila</b>. É ele que abre as 4 missões da história.</p></div>
<div class="grid g2 mt4">
<div class="box"><h4>{ic('eye', 15, 'var(--coral)')} O que observar no painel</h4>
<table class="t">
<tr><td><span class="pill" style="background:#fff">Barra vazia</span></td><td>Ainda não entrou. Confira se ela tem a senha.</td></tr>
<tr><td><span class="pill" style="background:#fff">Pela metade</span></td><td>Parou no caminho. O cartão mostra qual missão falta.</td></tr>
<tr><td><span class="pill" style="background:var(--amber)">Missões 4/4</span></td><td>História completa, pronta para ir ao livro.</td></tr>
<tr><td><span class="pill" style="background:#fff">Sem figurinha</span></td><td>Não entrou, não escolheu o desenho ou usa um personagem pronto (não há o que aprovar).</td></tr>
</table></div>
<div class="box"><h4>{ic('circle-help', 15, 'var(--coral)')} Dúvidas rápidas</h4>
<table class="t">
<tr><td><b>Perdeu a senha</b></td><td>Está no livro, nas folhas e ao lado do nome no painel.</td></tr>
<tr><td><b>Não apareceu</b></td><td>Tocar em Atualizar. Leva cerca de meio minuto.</td></tr>
<tr><td><b>Jogo lento</b></td><td>Fechar outras abas. Em aparelho fraco, a vila tira sozinha os efeitos mais pesados.</td></tr>
<tr><td><b>Sem som</b></td><td>Conferir o volume e o botão de som da tela.</td></tr>
</table></div>
</div>
<div class="box b-blue mt4" style="padding:3.4mm 4mm"><h4>{ic('house', 15, 'var(--blue)')} Em casa</h4>
<p>O livro impresso de cada criança traz o QR Code da vila e a senha dela. A família aponta a câmera, digita a senha e a criança continua de onde parou na escola. A senha é a mesma das folhas, do livro e do painel.</p></div>
<div class="grid g2 mt4" style="align-items:stretch">
<div class="box b-amber qrbox"><img src="assets/qr-vila.svg" alt=""><div><h4 style="margin-bottom:1mm">{ic('gamepad-2', 15, 'var(--coral)')} A vila</h4><p style="font-size:9pt">fabricadeautores.com.br/vila</p><p style="font-size:8.2pt;margin-top:1mm">Aponte a câmera. Dá para passear como visitante.</p></div></div>
<div class="box b-lilac qrbox"><img src="assets/qr-painel.svg" alt=""><div><h4 style="margin-bottom:1mm">{ic('clipboard-list', 15, 'var(--coral)')} O painel</h4><p style="font-size:9pt">fabricadeautores.com.br/vila/professora</p><p style="font-size:8.2pt;margin-top:1mm">Peça o código do colégio à coordenação.</p></div></div>
</div>
'''
pages.append(page('Para a coordenação', 'calendar-check', 'Como conduzir a primeira aula', 'Uma sugestão simples para começar, o que olhar no painel e como resolver os imprevistos mais comuns.', body, 11))

html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Vila dos Autores · Guia da coordenação</title><style>{CSS}</style></head><body>' + ''.join(pages) + '</body></html>'
open(os.path.join(BASE, 'coord.html'), 'w').write(html)
print('ok', len(pages))
