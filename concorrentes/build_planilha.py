from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

ARIAL = "Arial"
H_FILL = PatternFill("solid", fgColor="0A0514")   # roxo escuro Aceleradora
H_FONT = Font(name=ARIAL, size=10, bold=True, color="FFFFFF")
YOU_FILL = PatternFill("solid", fgColor="FFE6F2")  # destaque Aceleradora
IN_FILL  = PatternFill("solid", fgColor="FFFF00")  # célula de input
BLUE = Font(name=ARIAL, size=10, color="0000FF")   # input hardcoded
BLACK = Font(name=ARIAL, size=10)
BOLD = Font(name=ARIAL, size=10, bold=True)
TITLE = Font(name=ARIAL, size=13, bold=True, color="8A2BE2")
NOTE = Font(name=ARIAL, size=9, italic=True, color="555555")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
BRL = 'R$ #,##0;(R$ #,##0);-'
BRL2 = 'R$ #,##0.00;(R$ #,##0.00);-'
PCT = '0.0%;(0.0%);-'

wb = Workbook()

# ---------------------------------------------------------------- Concorrentes
ws = wb.active
ws.title = "Concorrentes"
ws["A1"] = "Concorrentes — Criação de Sites | Aceleradora EDU"
ws["A1"].font = TITLE
ws["A2"] = "Levantamento em 15/08/2026. Valores em R$. Ver aba Fontes."
ws["A2"].font = NOTE

hdr = ["Concorrente","Tipo","Setup mín","Setup máx","Mensalidade","Prazo prometido",
       "O que entrega","Quem compra","Ponto fraco (sua brecha)","Confiança do dado"]
for c,h in enumerate(hdr, start=1):
    cell = ws.cell(row=4, column=c, value=h)
    cell.font = H_FONT; cell.fill = H_FILL; cell.border = BOX
    cell.alignment = Alignment(vertical="center", wrap_text=True)

rows = [
 ("C2TI","Fábrica de sites (volume, vende por Google Ads)",500,1200,59.90,"5 dias úteis",
  "Site em CMS próprio (.aspx): páginas de texto, notícias, galeria de imagens e vídeos, página de contato e Google Maps. Garantia de 7 dias. +7.000 projetos entregues.",
  "PME de qualquer setor que clicou no anúncio",
  "Prazo real relatado no Reclame Aqui de 30 a 135 dias; template genérico; o site fica na plataforma deles (cliente não leva o código); zero pesquisa de conteúdo; sem SEO local dedicado; briga por reembolso",
  "Verificado — site + Reclame Aqui, ago/2026"),

 ("Wix / Hostinger (faça você mesmo)","Construtor DIY",0,0,None,"Imediato",
  "Template pronto. O próprio dono monta, escreve e publica.",
  "Dono que tem tempo e paciência",
  "O custo real é o tempo do dono; sem conteúdo, sem foto, sem SEO. Quase sempre para no meio.",
  "Estimado — mensalidade não verificada"),

 ("Freelancer (99Freelas / Workana / indicação)","Pessoa física",1500,8000,None,"Variável",
  "Site sob medida, sem processo definido.",
  "PME que 'conhece alguém que faz site'",
  "Risco de abandono do projeto, qualidade variável, sem suporte depois da entrega",
  "Verificado — faixa de mercado 2026"),

 ("Agência local — institucional simples","Agência",2500,4500,None,"15 a 30 dias",
  "Site institucional de até 5 páginas.",
  "PME em geral",
  "Não é especialista em escola: conteúdo genérico, não fala de matrícula, não conhece o funil de pai procurando escola",
  "Verificado — faixa de mercado 2026"),

 ("Agência — institucional personalizado com SEO","Agência",4500,9000,None,"30 a 60 dias",
  "Site personalizado com trabalho de SEO.",
  "Empresa média",
  "Preço fora do bolso da escola de bairro; não entrega plano de Google Negócios nem estratégia de avaliações",
  "Verificado — faixa de mercado 2026"),

 ("Landing page de conversão","Agência / freelancer",1500,4000,None,"7 a 15 dias",
  "Página única focada em conversão.",
  "Quem já roda tráfego pago",
  "Uma página = um alvo no Google. Não ranqueia para as buscas de bairro.",
  "Verificado — faixa de mercado 2026"),

 ("ERP escolar com site incluso (Sponte, WPensar, Escolas Web)","Sistema de gestão",None,None,None,"—",
  "Site entra como brinde da mensalidade do sistema de gestão.",
  "Escola que já paga o ERP",
  "Template idêntico entre todas as escolas do sistema, sem SEO local, sem conteúdo próprio",
  "NÃO VERIFICADO — confirmar preços antes de usar em reunião"),

 ("Aceleradora EDU (você)","Especialista em escola",4500,4500,350.00,"—",
  "Pesquisa do lead (Google Maps + resenhas + Instagram), texto escrito a partir de resenha real de mãe, fotos geradas por IA com a farda e o logo da escola, site completo com quiz, galeria, FAQ e duas trilhas de matrícula, estudo de SEO local, plano de Google Negócios, estratégia de avaliações, páginas por bairro. Cliente leva os arquivos.",
  "Escola particular de bairro, mensalidade R$ 800+",
  "Preço 4x a 9x o da C2TI no setup — só fecha se a conta do LTV vier ANTES do site",
  "Interno — tabela da skill sites-para-escolas"),
]

r = 5
for row in rows:
    you = row[0].startswith("Aceleradora")
    for c, v in enumerate(row, start=1):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font = BOLD if you else BLACK
        cell.border = BOX
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        if you: cell.fill = YOU_FILL
        if c in (3,4): cell.number_format = BRL
        if c == 5: cell.number_format = BRL2
    r += 1

ws.cell(row=5, column=5).comment = Comment(
    "R$ 59,90/mês de manutenção a partir do 2º mês, mais R$ 8,90/mês adicionais citados no site da C2TI. "
    "Fonte: c2ti.com.br, consultado em 15/08/2026.", "Aceleradora EDU")

widths = [30,26,12,12,13,15,52,26,52,26]
for i,w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w
for rr in range(5, r):
    ws.row_dimensions[rr].height = 96
ws.freeze_panes = "A5"

# ---------------------------------------------------------------- TCO 3 anos
t = wb.create_sheet("TCO_3anos")
t["A1"] = "O que o cliente realmente paga em 3 anos"
t["A1"].font = TITLE
t["A2"] = "A C2TI não custa R$ 500. Custa R$ 500 mais uma mensalidade que nunca para. Compare no mesmo prazo."
t["A2"].font = NOTE

t["A4"] = "Anos de comparação"; t["A4"].font = BOLD
t["B4"] = 3; t["B4"].font = BLUE; t["B4"].fill = IN_FILL; t["B4"].border = BOX

hdr2 = ["Cenário","Setup","Mensalidade","Custo dos meses","Total no período","x vezes a C2TI barata"]
for c,h in enumerate(hdr2, start=1):
    cell = t.cell(row=6, column=c, value=h)
    cell.font = H_FONT; cell.fill = H_FILL; cell.border = BOX
    cell.alignment = Alignment(vertical="center", wrap_text=True)

tco = [
 ("C2TI — piso da tabela", 500, 59.90),
 ("C2TI — teto da tabela", 1200, 59.90),
 ("Freelancer R$ 2.000 sem mensal", 2000, 0),
 ("Agência institucional simples", 3500, 0),
 ("Aceleradora EDU", 4500, 350),
]
rr = 7
for nome, setup, mensal in tco:
    you = nome.startswith("Aceleradora")
    t.cell(row=rr, column=1, value=nome)
    t.cell(row=rr, column=2, value=setup).number_format = BRL
    t.cell(row=rr, column=3, value=mensal).number_format = BRL2
    t.cell(row=rr, column=4, value=f"=C{rr}*12*$B$4").number_format = BRL
    t.cell(row=rr, column=5, value=f"=B{rr}+D{rr}").number_format = BRL
    t.cell(row=rr, column=6, value=f"=E{rr}/$E$7").number_format = '0.0"x"'
    for c in range(1,7):
        cell = t.cell(row=rr, column=c)
        cell.border = BOX
        cell.font = BOLD if you else (BLUE if c in (2,3) else BLACK)
        if you: cell.fill = YOU_FILL
    rr += 1

t["A13"] = ("Leitura: no setup você é 9,0x o piso da C2TI (R$ 4.500 contra R$ 500). Em 3 anos de contrato "
            "a distância cai para 6,4x o piso e 5,1x o teto dela. É essa a conta que vai para a reunião, "
            "não a do setup — e é ela que torna a diferença defensável.")
t["A13"].font = NOTE
t.merge_cells("A13:F13")
for i,w in enumerate([34,14,15,18,18,20], start=1):
    t.column_dimensions[get_column_letter(i)].width = w

# ---------------------------------------------------------------- LTV
l = wb.create_sheet("LTV_Ancoragem")
l["A1"] = "Por que você consegue cobrar caro — e quando não consegue"
l["A1"].font = TITLE
l["A2"] = "Células amarelas: preencher com os dados reais da escola antes da reunião."
l["A2"].font = NOTE

l["A4"] = "Dados da escola"; l["A4"].font = H_FONT; l["A4"].fill = H_FILL
l["B4"] = ""; l["B4"].fill = H_FILL

inputs = [("Mensalidade média (R$)", 1200, BRL),
          ("Meses cobrados por ano", 11, '0'),
          ("Anos de permanência do aluno", 5, '0')]
rr = 5
for label, val, fmt in inputs:
    l.cell(row=rr, column=1, value=label).font = BOLD
    c = l.cell(row=rr, column=2, value=val)
    c.font = BLUE; c.fill = IN_FILL; c.border = BOX; c.number_format = fmt
    rr += 1

l["A9"] = "LTV de UM aluno"; l["A9"].font = BOLD
l["B9"] = "=B5*B6*B7"; l["B9"].number_format = BRL; l["B9"].font = Font(name=ARIAL, size=10, bold=True)

l["A11"] = "Comparação com o preço"; l["A11"].font = H_FONT; l["A11"].fill = H_FILL
l["B11"] = ""; l["B11"].fill = H_FILL

comp = [
 ("Seu setup", "=Concorrentes!C12", BRL),
 ("Seu preço em 3 anos (setup + mensal)", "=TCO_3anos!E11", BRL),
 ("C2TI piso em 3 anos", "=TCO_3anos!E7", BRL),
 ("Seu preço de 3 anos como % do LTV de 1 aluno", "=B13/B9", PCT),
 ("1 matrícula paga o SETUP (x vezes)", "=B9/B12", '0.0"x"'),
 ("1 matrícula paga os 3 ANOS (x vezes)", "=B9/B13", '0.0"x"'),
]
rr = 12
for label, f, fmt in comp:
    l.cell(row=rr, column=1, value=label).font = BOLD
    c = l.cell(row=rr, column=2, value=f)
    c.number_format = fmt; c.font = BLACK; c.border = BOX
    rr += 1

rr += 1
l.cell(row=rr, column=1, value="Onde o preço alto SE SUSTENTA").font = H_FONT
l.cell(row=rr, column=1).fill = H_FILL
l.cell(row=rr, column=2, value="").fill = H_FILL
rr += 1
sustenta = [
 "Escola com mensalidade de R$ 800 ou mais — o LTV de um aluno paga o site dezenas de vezes",
 "Escola com 5 ou mais avaliações e nota 4,0+ — há matéria-prima real para escrever e ela já tem reputação a defender",
 "Escola com 10+ anos de casa — tem caixa, não vai fechar, e o tempo de casa vira o argumento do site",
 "Escola que JÁ gasta com marketing (impulsiona post, tem designer) — o orçamento existe, você só o redireciona",
 "Escola que é unidade de uma REDE — a proposta deixa de ser de um site e passa a ser do grupo",
]
for s in sustenta:
    l.cell(row=rr, column=1, value="✔ " + s).font = BLACK
    l.merge_cells(f"A{rr}:D{rr}")
    rr += 1

rr += 1
l.cell(row=rr, column=1, value="Onde o preço alto NÃO se sustenta — desqualifique o lead").font = H_FONT
l.cell(row=rr, column=1).fill = H_FILL
l.cell(row=rr, column=2, value="").fill = H_FILL
rr += 1
nao = [
 "Escola que só quer 'uma paginazinha para ter presença' — contra essa necessidade a C2TI de R$ 500 ganha, e ganha com razão",
 "Escola com mensalidade abaixo de R$ 500 — o LTV não sustenta a conta e ela vai regatear até o fim",
 "Escola sem avaliação nenhuma e sem Instagram — não há matéria-prima; o site sai genérico e vira commodity",
 "Curso livre e curso de idioma — mensalidade R$ 150 a R$ 400 e permanência de 18 meses, LTV baixo demais",
 "Reunião onde ele viu o site ANTES da conta do LTV — o cérebro dele ancorou em 'quanto custa uma página' e você já perdeu",
]
for s in nao:
    l.cell(row=rr, column=1, value="✘ " + s).font = BLACK
    l.merge_cells(f"A{rr}:D{rr}")
    rr += 1

rr += 1
l.cell(row=rr, column=1, value="A brecha da C2TI — use na reunião").font = H_FONT
l.cell(row=rr, column=1).fill = H_FILL
l.cell(row=rr, column=2, value="").fill = H_FILL
rr += 1
brechas = [
 "Prazo: prometem 5 dias úteis. O Reclame Aqui registra entregas de 30 a 135 dias.",
 "Posse: o site vive no CMS .aspx deles. Parou de pagar a mensalidade, o site sai do ar. Você entrega os arquivos e a escola é dona.",
 "Conteúdo: eles pedem o texto ao cliente. Você escreve a partir das resenhas reais das mães e das legendas do Instagram dela.",
 "Foto: eles usam banco de imagem. Você gera foto com a farda e o logo reais da escola — e criança de IA não tem direito de imagem para renovar.",
 "SEO local: eles entregam o site. Você entrega o plano de Google Negócios, a estratégia de avaliações e as páginas por bairro — que é o que de fato ranqueia.",
]
for s in brechas:
    l.cell(row=rr, column=1, value="→ " + s).font = BLACK
    l.merge_cells(f"A{rr}:D{rr}")
    rr += 1

for i,w in enumerate([46,18,18,18], start=1):
    l.column_dimensions[get_column_letter(i)].width = w

# ---------------------------------------------------------------- Fontes
f = wb.create_sheet("Fontes")
f["A1"] = "Fontes consultadas em 15/08/2026"; f["A1"].font = TITLE
srcs = [
 ("C2TI — página de criação de sites","https://c2ti.com.br/w/Site/criacao-de-sites.aspx","Faixa R$ 500 a R$ 1.200; manutenção a partir de R$ 59,90/mês do 2º mês; adicional de R$ 8,90/mês; garantia de 7 dias; escopo do plano"),
 ("C2TI — landing de site profissional","https://conteudo.c2ti.com.br/criacao-site-profissional-m","+7.000 projetos, 15+ anos"),
 ("Reclame Aqui — C2TI Softwares","https://www.reclameaqui.com.br/empresa/c2ti-softwares/","92,9% de reclamações resolvidas; casos de atraso de 30 e de 135 dias; disputas de reembolso"),
 ("SEO Criação — tabela de preços 2026","https://seocriacao.com.br/quanto-custa-criar-um-site-profissional-em-2026/","Landing R$ 1.500–4.000; institucional simples R$ 2.500–4.500; institucional com SEO R$ 4.500–9.000"),
 ("Wix Brasil — quanto custa um site","https://pt.wix.com/blog/quanto-custa-um-site-profissional","Site profissional R$ 3.000–12.000 no mercado brasileiro"),
 ("Skill interna sites-para-escolas","—","Tabela da Aceleradora: R$ 4.500 de setup + R$ 350/mês; LTV por tipo de escola; ordem da reunião"),
]
for c,h in enumerate(["Fonte","Link","O que foi extraído"], start=1):
    cell = f.cell(row=3, column=c, value=h); cell.font = H_FONT; cell.fill = H_FILL; cell.border = BOX
rr = 4
for s in srcs:
    for c,v in enumerate(s, start=1):
        cell = f.cell(row=rr, column=c, value=v)
        cell.font = BLACK; cell.border = BOX
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    rr += 1
for i,w in enumerate([34,52,66], start=1):
    f.column_dimensions[get_column_letter(i)].width = w
for x in range(4, rr):
    f.row_dimensions[x].height = 44

wb.save("Concorrentes_Criacao_Sites.xlsx")
print("ok")
