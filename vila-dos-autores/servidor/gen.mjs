// Expande helpers em código SDK literal (o validador do n8n não aceita funções).
// Uso: node gen.mjs entrada.js > saida.sdk.js
import fs from 'fs';
const src = fs.readFileSync(process.argv[2], 'utf8');
const [defs, chain] = src.split(/^export default /m);
const body = defs.replace(/^import .*$/m, '');
const names = [...body.matchAll(/^const (\w+) = (\w+)\(/gm)].map((m) => m[1]).filter((n, i, a) => a.indexOf(n) === i);
const mk = (kind) => (cfg) => ({ __kind: kind, cfg });
const SDK = { node: mk('node'), trigger: mk('trigger'), ifElse: mk('ifElse'), switchCase: mk('switchCase'), newCredential: (n) => '@@CRED:' + n + '@@' };
const fn = new Function('SDK', 'const {node, trigger, ifElse, switchCase, newCredential} = SDK;\n' + body + '\nreturn {' + names.join(',') + '};');
const vals = fn(SDK);
let out = "import { workflow, node, trigger, ifElse, switchCase, newCredential } from '@n8n/workflow-sdk';\n\n";
for (const n of names) {
  const v = vals[n];
  if (!v || !v.__kind) continue;
  let j = JSON.stringify(v.cfg);
  j = j.replace(/"@@CRED:([^@]+)@@"/g, (_, c) => 'newCredential(' + JSON.stringify(c) + ')');
  out += 'const ' + n + ' = ' + v.__kind + '(' + j + ');\n\n';
}
out += 'export default ' + chain;
process.stdout.write(out);
