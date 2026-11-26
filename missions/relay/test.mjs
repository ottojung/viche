// Focused offline test: every retired relay entry point must fail closed and
// spawn no transport. This runs locally with node and makes no network calls.
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const here = path.dirname(fileURLToPath(import.meta.url));
for (const f of ['relay.mjs', 'pnp-remote-check.py', 'lean-handler.py',
                 'lb-handler.py', 'sib-handler.py', 'refresh-cache.py',
                 'worker-lock.py']) {
  const cmd = f.endsWith('.mjs') ? ['node', path.join(here, f)] : ['python3', path.join(here, f)];
  const r = spawnSync(cmd[0], cmd.slice(1), {encoding: 'utf8'});
  assert.equal(r.status, 9, f + ' must exit 9');
  assert.match(r.stdout + r.stderr, /remote_transport_disabled/, f + ' must report refusal');
}
console.log(JSON.stringify({status: 'ok', checked: 7}));
