# Vila dos Autores · Fase 2: Meu Cantinho

O lote individual de cada criança, no mesmo estilo da Fase 1: 2.5D tipo Paper Mario, cel-shading com contorno preto grosso (casca invertida), cores planas e personagens billboard 2D.

## Como a criança chega

- Na praça sai um **caminho de flores** (nordeste) até um portal de madeira com telhadinho e a placa **MEU CANTINHO**.
- O cantinho abre depois do selo **Autor(a) da Vila** (fim da Casa da Pena). Antes disso, o portal mostra 🔒 e explica.
- Na primeira vez, um balão rosa com "!" fica em cima do portal e a Pena dá as boas-vindas (3 falas com voz gravada).
- Do cantinho, a placa **Praça da Vila** na Rua dos Cantinhos leva de volta.

## O lote

| Parte | Como é | Interação |
| --- | --- | --- |
| Casa | Fachada com porta (janelinha redonda), janela com floreira, telhado de duas águas, chaminé, lanterna e plaquinha "Cantinho de Nome" | 🚪 Entrar em casa |
| Cores | Parede, telhado e porta/caixa de correio: 6 cores cada | 🎨 Pintar a casa (latinha de tinta) |
| Jardim | Gramado dentro da cerca branca, caminho de pedras da rua até a porta | colocar até 3 decorações livres |
| Canteiro | Caixa de madeira com 3 covas | 🌱 Plantar uma flor (usa a receita Flor Plantada) |
| Cerca e portão | Cerca baixa com portão de madeira, guirlanda que muda com a estação | — |
| Quadro da história | Painel com telhadinho perto da entrada: desenho + trecho da história | 🖼 Quadro da história |
| Caixa de correio | Na rua, com o nome da criança | 📬 Visitar colegas |
| Vizinhança | Duas casinhas vizinhas, árvores, postes com bandeirinhas e, no morro ao fundo, a vila em miniatura (as 5 casas e a fonte) | — |

**Fachada:** a Guirlanda pendura sozinha na porta e o Enfeite de Janela na janela (chegando perto com o item em "Colocar"). Colocar outro no mesmo lugar troca, e o antigo volta para a mochila.

**Flores:** a flor do canteiro cresce com o tempo: semente, brotinho (2 min), flor (5 min) e flor cheia com um segundo botão (30 min).

## Dentro de casa (casinha de boneca)

Parede da frente invisível, câmera mais perto, transição de íris como nas casas da Fase 1. Papel de parede com corações e bolinhas na cor escolhida para a parede.

| Objeto | Interação |
| --- | --- |
| Cama com colcha (cor do telhado) | 🛏 Deitar na cama |
| Escrivaninha com cadeira, caderno, lápis e porta-retrato com o personagem | ✏️ Escrivaninha: senta e abre "Minha história" (título, primeira frase, mudar o quadro) |
| Estantinha (mostra o Mini-livro quando a criança tem o selo) | 📚 Minha estante |
| Janela com vista pintada de cada estação (primavera, mar no verão, folhas no outono, neve no inverno) | 🪟 Olhar pela janela |
| Luminária de pé (luz quente; a janela de fora também acende) | 💡 Acender/Apagar |
| Quadro da história na parede (mesma imagem do painel de fora) | 🖼 Quadro da história |
| Baú: selos, criações para decorar e lista do que está no cantinho (com "Guardar") | 🧰 Baú do cantinho |
| Até 3 decorações livres dentro de casa | colocar pela Mochila ou pelo Baú |

Todos os objetos dão um pulinho quando a criança chega perto e respondem à tecla E ou ao toque.

## Estações

- **Fora:** cor da grama, do céu e das árvores (as mesmas da vila), neve no telhado, na cerca, na caixa de correio e no canteiro, pingentes de gelo, fumaça na chaminé (outono, inverno ou luz acesa), flores na cerca e borboletas (primavera), girassóis e boia (verão), folhas no chão, abóboras e monte de folhas (outono), bonequinho de neve e montinhos (inverno).
- **Dentro:** vista da janela, tapete, enfeite da janela e da escrivaninha, canto da sala (vaso de flores, bola de praia, abóboras, pinheirinho com luzes), varal de bandeirinhas (primavera e verão) e luzinhas piscando (inverno).
- **Enfeites que mudam:** guirlanda (folhas no outono, neve e frutinhas no inverno), enfeite de janela (pingentes de gelo), flor (chapeuzinho de neve), boneco de neve (óculos escuros no verão), lembrancinha de praia (neve).
- As receitas de estação continuam só na estação delas (Coroa, Lembrancinha, Buquê, Boneco de Neve).

## Missão opcional e selo

**Decore seu cantinho:** colocar pelo menos 1 item criado (jardim, porta, janela ou dentro de casa) e plantar uma flor no canteiro. Dá o selo **🏡 Cantinho Decorado** (o 8º selo). O painel da professora mostra o selo e quantos enfeites e flores cada criança tem.

## Colegas da turma

- No cantinho, a caixa de correio abre **Visitar colegas**: lista da turma, com "🏡 em casa agora" e "👋 na vila".
- Visitando, a criança vê a casa com as cores, enfeites e flores do colega, pode entrar, sentar e acender a luz, mas não muda nada.
- Quem está no mesmo cantinho (fora ou dentro de casa) se vê, como nas casas da Fase 1. O dono recebe o aviso "👋 Fulano veio visitar o seu cantinho!".
- **Privacidade:** quem visita vê só o primeiro nome e a figurinha já aprovada pela professora. O trecho da história no quadro aparece só para o dono. O servidor guarda do cantinho apenas cores, itens da lista de enfeites, posições e horários de plantio (nenhum texto livre).

## Onde fica guardado

Tudo do cantinho (cores, quadro, luz, enfeites, flores) faz parte do progresso da criança: vai junto para o servidor da escola (vila-salvar) e, quando o navegador deixa, também fica no aparelho. Para as visitas, uma cópia só com o desenho do lote vai para a tabela `vila_salas` (colunas `cant` e `cant_em`).

## Servidor (precisa publicar)

No fluxo **Vila — salas da turma (sync)** entram dois endpoints novos:
- `POST /vila-cantinho-salvar` {c, vid, cant}: limpa e grava o lote.
- `POST /vila-cantinho` {c, vid} lista os colegas da turma; {c, vid, de} devolve o lote de um colega (só se for da mesma turma).

Antes de publicar, criar as colunas `cant` (texto) e `cant_em` (número) na tabela `vila_salas`. Enquanto isso não acontece, o jogo funciona normalmente e a lista de visitas avisa que as visitas "ainda vão ser ligadas".

## Lista de assets

Tudo é gerado no navegador (Three.js e Canvas 2D). Não há arquivos de imagem, modelo ou som para baixar além do que a Fase 1 já usa.

| Tipo | Asset | Como é feito |
| --- | --- | --- |
| Modelo 3D | Casa do cantinho (base, paredes, telhado extrudado, chaminé, porta, janela, floreira, lanterna, telhadinho) | Primitivas com contorno, materiais toon únicos para parede, telhado e porta |
| Modelo 3D | Cerca com postes pontudos, portão com placa e guirlanda sazonal | Primitivas |
| Modelo 3D | Canteiro (3 covas), placa "Canteiro" | Primitivas |
| Modelo 3D | Flor do canteiro em 4 estágios | `MODEL.florPlantada({ solo: true })` |
| Modelo 3D | Quadro da história com telhadinho | Primitivas + textura de canvas |
| Modelo 3D | Caixa de correio, latinha de tinta com pincel, placa da Rua dos Cantinhos | Primitivas |
| Modelo 3D | Duas casas vizinhas com cerca, árvores redondas e pinheiros | Primitivas |
| Modelo 3D | Morro com a vila em miniatura (5 casas e a fonte com o livro) | Primitivas |
| Modelo 3D | Interior: cama, luminária, baú com tampa, escrivaninha, cadeira, estantinha, mini-livro, porta-retrato, janela com cortinas | Primitivas |
| Modelo 3D | Enfeites de estação (fora e dentro), luzinhas, pinheirinho, bola de praia | Primitivas |
| Modelo 3D | Portal "Meu Cantinho" na vila e caminho de flores | Primitivas |
| Textura | Quadro da história (640 × 480): desenho + título + trecho + "por Nome" | Canvas, redesenhado quando muda |
| Textura | Placas com o nome (casa, portão, caixa de correio) | `textCanvas` |
| Textura | Papel de parede na cor da parede | Canvas 256 × 256 repetido |
| Textura | 4 vistas da janela (uma por estação) | Canvas 512 × 400 pintado com contorno |
| Textura | Desenhos do livro para o quadro | `/vila-desenho` (já existente) |
| Som | plantar, pincel, luminária, portão, cama (boing), caixa de correio, baú | Web Audio (osciladores e ruído) |
| Som | passos, porta, pop, fanfarra do selo | Os da Fase 1 |
| Voz | 4 falas novas da Pena (21 a 24) | ElevenLabs, servidas por `/vila-voz` |
| Luz | Luz quente da luminária | `PointLight` |

## Voz da Pena

As 4 falas da Fase 2 têm voz gravada (ElevenLabs, voz Yasmin, mesmas configurações das 20 da Fase 1) e ficam na tabela `vila_vozes` como 21 a 24:
- 21: "Que bom ter você aqui no seu cantinho! Esta casinha é só sua, e o caminho de flores leva de volta para a praça."
- 22: "Plante uma flor no canteiro, pendure enfeites na porta e na janela, e coloque até três decorações no jardim."
- 23: "No quadro da entrada fica um pedacinho da sua história. Dá para trocar o desenho e o trecho quando quiser!"
- 24: "Que cantinho mais lindo! Agora ele tem a sua cara. Você ganhou o selo Cantinho Decorado!"

O texto na tela é igual ao áudio.

## Guia em PDF

O guia ilustrado (`guia/Vila-dos-Autores-Guia-de-jogo.pdf`) tem 5 páginas da Fase 2: a casinha e como chegar, plantar/enfeitar/pintar, dentro de casa, as 4 estações e as visitas.
