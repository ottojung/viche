import assert from 'node:assert/strict';
import {seal,open,live,event,makeRequest,enqueue,get,change} from './relay.mjs';
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
