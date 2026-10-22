import { workflow, node, trigger, ifElse, newCredential } from '@n8n/workflow-sdk';

const T_VOZES = '3XxVQ9t3OVGvQB7d';
const T_ALUNOS = 'uPAuphP8XCg9YdxE';
const T_SALAS = 'i65e920eijJvgEY6';
const tab = (id) => ({ __rl: true, mode: 'id', value: id });
const eq = (k, v) => ({ keyName: k, condition: 'eq', keyValue: v });
const hdr = (list) => ({ responseHeaders: { entries: list.map((p) => ({ name: p[0], value: p[1] })) } });
const whGet = (name, path, y) => trigger({ type: 'n8n-nodes-base.webhook', version: 2.1, config: { name, parameters: { httpMethod: 'GET', path, responseMode: 'responseNode', options: { allowedOrigins: '*' } }, position: [200, y] }, output: [{ query: {} }] });
const code = (name, js, x, y) => node({ type: 'n8n-nodes-base.code', version: 2, config: { name, parameters: { mode: 'runOnceForAllItems', jsCode: js }, position: [x, y] }, output: [{ ok: true }] });
const sim = (name, leftExpr, x, y) => ifElse({ version: 2.3, config: { name, parameters: { conditions: { options: { caseSensitive: true, leftValue: '', typeValidation: 'loose' }, conditions: [{ id: name, leftValue: leftExpr, rightValue: '', operator: { type: 'boolean', operation: 'true', singleValue: true } }], combinator: 'and' }, looseTypeValidation: true }, position: [x, y] } });
const dtGet = (name, table, conds, x, y) => node({ type: 'n8n-nodes-base.dataTable', version: 1.1, config: { name, parameters: { resource: 'row', operation: 'get', dataTableId: tab(table), matchType: 'allConditions', filters: { conditions: conds }, returnAll: false, limit: 1 }, alwaysOutputData: true, executeOnce: true, position: [x, y] }, output: [{ id: 1 }] });
const baixarTexto = (name, arquivo, x, y) => node({ type: 'n8n-nodes-base.httpRequest', version: 4.2, config: { name, parameters: { method: 'GET', url: "={{ 'https://cdn.jsdelivr.net/gh/brunopohlmannbatista/claude@' + (/^[a-f0-9]{7,40}$/.test(String($json.query.v || '')) ? $json.query.v : '8d64d1c012c763095df5623ca73c86d9f7e4d2cb') + '/vila-dos-autores/" + arquivo + "' }}", options: { response: { response: { responseFormat: 'text', outputPropertyName: 'data' } }, timeout: 15000 } }, retryOnFail: true, maxTries: 2, waitBetweenTries: 1000, position: [x, y] }, output: [{ data: '<html></html>' }] });
const respHtml = (name, x, y) => node({ type: 'n8n-nodes-base.respondToWebhook', version: 1.5, config: { name, parameters: { respondWith: 'text', responseBody: '={{ $json.data }}', options: hdr([['Content-Type', 'text/html; charset=utf-8'], ['Cache-Control', 'no-cache']]) }, position: [x, y] } });
const respBin = (name, cache, x, y) => node({ type: 'n8n-nodes-base.respondToWebhook', version: 1.5, config: { name, parameters: { respondWith: 'binary', responseDataSource: 'automatically', options: hdr([['Cache-Control', cache]]) }, position: [x, y] } });
const resp404 = (name, x, y) => node({ type: 'n8n-nodes-base.respondToWebhook', version: 1.5, config: { name, parameters: { respondWith: 'json', responseBody: '={{ JSON.stringify({ ok: false }) }}', options: Object.assign({ responseCode: 404 }, hdr([['Cache-Control', 'no-store']])) }, position: [x, y] } });
const toBin = (name, mime, file, x, y) => node({ type: 'n8n-nodes-base.convertToFile', version: 1.1, config: { name, parameters: { operation: 'toBinary', sourceProperty: 'b64', options: { mimeType: mime, fileName: file, dataIsBase64: true } }, position: [x, y] } });

// ---------- páginas ----------
const wJogo = whGet('GET /vila', 'vila', 100);
const hJogo = baixarTexto('Baixar o jogo', 'index.html', 420, 100);
const rJogo = respHtml('Mostrar o jogo', 640, 100);

const wPainel = whGet('GET /vila-professora', 'vila-professora', 300);
const hPainel = baixarTexto('Baixar o painel', 'painel.html', 420, 300);
const rPainel = respHtml('Mostrar o painel', 640, 300);

// ---------- vozes da Pena ----------
const wVoz = whGet('GET /vila-voz', 'vila-voz', 500);
const cVoz = code('Qual fala', "const q = $input.first().json.query || {};\nconst n = String(q.n || '').replace(/[^0-9]/g, '').padStart(2, '0').slice(-2);\nreturn [{ json: { n } }];", 420, 500);
const gVoz = dtGet('Buscar a fala', T_VOZES, [eq('n', '={{ $json.n }}')], 640, 500);
const iVoz = sim('Tem a fala?', '={{ !!$json.b64 }}', 860, 500);
const bVoz = toBin('Virar áudio', 'audio/mpeg', "={{ 'pena-' + $json.n + '.mp3' }}", 1080, 440);
const rVoz = respBin('Tocar a fala', 'public, max-age=2592000', 1300, 440);
const rVoz404 = resp404('Fala não existe', 1080, 580);

// ---------- desenho do livro ----------
const wDes = whGet('GET /vila-desenho', 'vila-desenho', 760);
const cDes = code('Qual desenho', "const q = $input.first().json.query || {};\nconst c = String(q.c || '').trim().toUpperCase();\nconst s = parseInt(q.s, 10);\nconst ok = /^[A-Z0-9]{4}$/.test(c) && s >= 0 && s < 100;\nreturn [{ json: { c: ok ? c : 'NADA', s: ok ? s : -1 } }];", 420, 760);
const gDes = dtGet('Buscar aluno (desenho)', T_ALUNOS, [eq('codigo', '={{ $json.c }}')], 640, 760);
const cDes2 = code('Achar arquivo', "const pedido = $('Qual desenho').first().json;\nconst row = $input.first().json || {};\nlet lista = [];\ntry { lista = JSON.parse(row.desenhos || '[]'); } catch (e) {}\nconst d = lista.find(x => Number(x.s) === pedido.s);\nconst arquivo = d && /^[A-Za-z0-9_-]{10,}$/.test(String(d.a)) ? String(d.a) : '';\nreturn [{ json: { arquivo, achou: !!arquivo } }];", 860, 760);
const iDes = sim('Tem o desenho?', '={{ $json.achou }}', 1080, 760);
const dDes = node({ type: 'n8n-nodes-base.googleDrive', version: 3, config: { name: 'Baixar do Drive', parameters: { resource: 'file', operation: 'download', fileId: { __rl: true, mode: 'id', value: '={{ $json.arquivo }}' }, options: { binaryPropertyName: 'data' } }, credentials: { googleDriveOAuth2Api: newCredential('Google Drive account') }, retryOnFail: true, maxTries: 2, waitBetweenTries: 1500, position: [1300, 700] } });
const eDes = node({ type: 'n8n-nodes-base.editImage', version: 1, config: { name: 'Diminuir desenho', parameters: { operation: 'resize', dataPropertyName: 'data', width: 720, height: 720, resizeOption: 'onlyIfLarger', options: { format: 'jpeg', quality: 86, fileName: 'desenho.jpg' } }, position: [1520, 700] } });
const rDes = respBin('Mandar desenho', 'private, max-age=86400', 1740, 700);
const rDes404 = resp404('Desenho não existe', 1300, 840);

// ---------- figurinha de colega ----------
const wFig = whGet('GET /vila-fig', 'vila-fig', 1000);
const cFig = code('Qual figurinha', "const q = $input.first().json.query || {};\nconst v = String(q.v || '').replace(/[^a-z0-9]/g, '').slice(0, 24);\nconst c = String(q.c || '').trim().toUpperCase();\nreturn [{ json: { v: v.length > 8 ? v : 'nada', c } }];", 420, 1000);
const gFig = dtGet('Buscar figurinha', T_SALAS, [eq('vid', '={{ $json.v }}')], 640, 1000);
const cFig2 = code('Pode mostrar?', "const pedido = $('Qual figurinha').first().json;\nconst row = $input.first().json || {};\nconst fig = String(row.fig || '');\nconst m = fig.match(/^data:(image\\/(?:png|webp|jpeg));base64,(.+)$/);\nconst dono = !!row.codigo && pedido.c === String(row.codigo);\nconst ok = !!m && (row.aprov === 'SIM' || dono);\nreturn [{ json: { ok, mime: m ? m[1] : '', b64: ok ? m[2] : '' } }];", 860, 1000);
const iFig = sim('Figurinha liberada?', '={{ $json.ok }}', 1080, 1000);
const bFig = toBin('Virar imagem', '={{ $json.mime }}', 'figurinha', 1300, 940);
const rFig = respBin('Mandar figurinha', 'private, max-age=300', 1520, 940);
const rFig404 = resp404('Figurinha não liberada', 1300, 1080);

export default workflow('vila-paginas', 'Vila — páginas, vozes e imagens', { settings: { executionOrder: 'v1', saveDataSuccessExecution: 'none', saveDataErrorExecution: 'all', saveManualExecutions: true } })
  .add(wJogo).to(hJogo).to(rJogo)
  .add(wPainel).to(hPainel).to(rPainel)
  .add(wVoz).to(cVoz).to(gVoz).to(iVoz.onTrue(bVoz.to(rVoz)).onFalse(rVoz404))
  .add(wDes).to(cDes).to(gDes).to(cDes2).to(iDes.onTrue(dDes.to(eDes.to(rDes))).onFalse(rDes404))
  .add(wFig).to(cFig).to(gFig).to(cFig2).to(iFig.onTrue(bFig.to(rFig)).onFalse(rFig404));
