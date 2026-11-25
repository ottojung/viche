import assert from 'node:assert/strict';
import {seal,open,live,event,makeRequest,enqueue,get,change,payload} from './relay.mjs';
const c={key:'a'.repeat(64),request:'b'.repeat(64),response:'c'.repeat(64)};
const a=makeRequest('ping','confidential'),b=makeRequest('ping','another');
const v={v:1,entries:[a]};
const raw=seal(c,'request',v);
assert(!raw.includes('confidential'));assert.deepEqual(open(c,'request',raw),v);
assert.notEqual(raw,seal(c,'request',v));assert.throws(()=>open(c,'response',raw));
const e=JSON.parse(raw);e.tag=Buffer.alloc(16).toString('base64');assert.throws(()=>open(c,'request',JSON.stringify(e)));
assert.throws(()=>open(c,'request',seal(c,'request',{v:1,entries:[a,a]})));
assert(live({expires:1001},1000));assert(!live({expires:1000},121000));assert(live({expires:1800000+40000},0));
assert.equal(event({events:[]},'ack','received').state,'ack');
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {randomBytes} from 'node:crypto';
import {gzipSync} from 'node:zlib';
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'relay-large-'));
try {
 const file=path.join(dir,'check.json');
 const check={statement:'check',module:'PEqualNP.Outside.L_meta_8479',maxstates:1,chunks:1,
              timeout:900,check_file_gz_b64:gzipSync(randomBytes(446*1024)).toString('base64')};
 fs.writeFileSync(file,JSON.stringify(check));
 assert(fs.statSync(file).size>65536);
 assert.deepEqual(payload('lb-cert',[file]),check);
 const req=makeRequest('lb-cert',check), envelope={v:1,entries:[req]};
 assert.deepEqual(open(c,'request',seal(c,'request',envelope)),envelope);
 fs.writeFileSync(file,JSON.stringify({...check,check_file_gz_b64:'A'.repeat(768*1024+4)}));
 assert.throws(()=>payload('lb-cert',[file]));
}finally{fs.rmSync(dir,{recursive:true,force:true});}
const store=new Map();let counter=0,conflicts=0;
globalThis.fetch=async(url,o)=>{
 const key=url.split('/').at(-1),old=store.get(key);
 if(o.method==='POST'){
  if(old){conflicts++;return new Response('',{status:409});}
  assert.equal(o.headers['X-Skrynia-Mode'],'public-write');
  store.set(key,{body:o.body,etag:'"'+(++counter)+'"'});return new Response('',{status:201});
 }
 if(o.method==='PUT'){
  if(o.headers['If-Match']!==old?.etag){conflicts++;return new Response('',{status:412});}
  store.set(key,{body:o.body,etag:'"'+(++counter)+'"'});return new Response('',{status:200});
 }
 return old?new Response(old.body,{status:200,headers:{etag:old.etag}}):new Response('',{status:404});
};
await Promise.all([enqueue(c,a),enqueue(c,b)]);
assert.equal((await get(c,'request')).value.entries.length,2);
assert(conflicts>0);await enqueue(c,a);
assert.equal((await get(c,'request')).value.entries.length,2);
await assert.rejects(enqueue(c,{...a,payload:'different'}),/identity conflict/);
await change(c,'request',v=>({...v,entries:v.entries.filter(x=>x.id!==a.id)}));
assert.deepEqual((await get(c,'request')).value.entries,[b]);
console.log('PASS: crypto, direction binding, tamper, schema, clock skew, concurrent CAS, deduplication, cleanup');
