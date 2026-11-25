import sys, os, subprocess
from playwright.sync_api import sync_playwright
BASE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto('file://' + os.path.join(BASE, name + '.html'))
    pg.wait_for_load_state('networkidle')
    pg.evaluate('document.fonts.ready')
    # detecta estouro de pagina
    over = pg.evaluate('''() => [...document.querySelectorAll('.page')].map((p,i)=>{
      const pr=p.getBoundingClientRect(); let worst=0;
      p.querySelectorAll('*').forEach(e=>{ if(e.closest('.ft')) return; const r=e.getBoundingClientRect(); if(r.height>0 && r.bottom-pr.bottom>worst) worst=r.bottom-pr.bottom; });
      // conteudo vs rodape
      const ft=p.querySelector('.ft'); let clash=0;
      if(ft){const fr=ft.getBoundingClientRect(); p.querySelectorAll('*').forEach(e=>{ if(e.closest('.ft')||e===ft) return; const r=e.getBoundingClientRect(); if(r.height>0 && r.bottom>fr.top-4 && r.top<fr.bottom && e.children.length===0) clash=Math.max(clash,r.bottom-(fr.top-4));});}
      return [i+1, Math.round(worst), Math.round(clash)];})''')
    print('pagina, estouro_px, invade_rodape_px:', over)
    pg.pdf(path=os.path.join(BASE, name + '.pdf'), prefer_css_page_size=True, print_background=True)
    b.close()
print(subprocess.run(['pdfinfo', os.path.join(BASE, name + '.pdf')], capture_output=True, text=True).stdout)
