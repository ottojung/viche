import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {createCipheriv,createDecipheriv,randomBytes,randomUUID} from 'node:crypto';
import {setTimeout as sleep} from 'node:timers/promises';

const MAX=4*1024*1024, JOB_MAX=2*1024*1024, TTL=30*60*1000, SKEW=120000, LIMIT=32;
const MAX_LEAN=2, LEAN_BUDGET=16384;
const BASE='https://vau.place/_skrynia/store/antonina/';
const HOME=os.homedir(), HERE=path.dirname(fileURLToPath(import.meta.url));
const confPath=path.join(HOME,'.config/marceline-relay/config.json');
const stateRoot=path.join(HOME,'.local/state/marceline-relay');
const ops=new Set(['ping','lean-check','lb-cert','sibling']);
const MAX_LB=6, MAX_LB_CHECK=1, LB_CHECK_MAX=768*1024;
function config(){
 const st=fs.lstatSync(confPath);
 if(!st.isFile()||st.uid!==process.getuid()||(st.mode&0o077))throw Error('private relay config required');
 const c=JSON.parse(fs.readFileSync(confPath,'utf8'));
 if(!['key','request','response'].every(k=>/^[0-9a-f]{64}$/.test(c[k]))||c.request===c.response)throw Error('invalid relay config');
 return c;
}
function idok(id){return typeof id==='string'&&/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/.test(id);}
function seal(c,box,value){
 const iv=randomBytes(12),cipher=createCipheriv('aes-256-gcm',Buffer.from(c.key,'hex'),iv);
 cipher.setAAD(Buffer.from('marceline-relay-v1:'+box+':'+c[box]));
 const data=Buffer.concat([cipher.update(JSON.stringify(value),'utf8'),cipher.final()]);
 return JSON.stringify({v:1,iv:iv.toString('base64'),data:data.toString('base64'),tag:cipher.getAuthTag().toString('base64')});
}
// lb-cert: a lower-bound certificate request (data only: statement text, module name, two bounded integers).
function lbOK(p){return !!p&&typeof p==='object'&&typeof p.statement==='string'&&Buffer.byteLength(p.statement)<=16384&&
 /^PEqualNP\.Outside\.[A-Za-z0-9_]{1,80}$/.test(p.module)&&Number.isSafeInteger(p.maxstates)&&p.maxstates>=1&&p.maxstates<=300000&&
 Number.isSafeInteger(p.chunks)&&p.chunks>=1&&p.chunks<=200&&
 (p.check_file_gz_b64===undefined||(
  p.statement==='check'&&typeof p.check_file_gz_b64==='string'&&
  p.check_file_gz_b64.length>0&&p.check_file_gz_b64.length<=LB_CHECK_MAX&&
  /^[A-Za-z0-9+/]+={0,2}$/.test(p.check_file_gz_b64)&&
  Number.isSafeInteger(p.timeout)&&p.timeout>=1&&p.timeout<=900));}
// sibling: transfer of a merged same-skeleton proof (data only: statement, module, imports, a bound).
function sibOK(p){return !!p&&typeof p==='object'&&typeof p.statement==='string'&&Buffer.byteLength(p.statement)<=16384&&
 /^PEqualNP\.Outside\.[A-Za-z0-9_]{1,80}$/.test(p.module)&&Array.isArray(p.imports)&&p.imports.length<=16&&
 p.imports.every(i=>typeof i==='string'&&/^[A-Za-z][A-Za-z0-9_.]{0,120}$/.test(i))&&
 Number.isSafeInteger(p.max_tries)&&p.max_tries>=1&&p.max_tries<=16;}
function open(c,box,raw){
 try{
  const e=JSON.parse(raw);
  if(e.v!==1)throw Error();
  const iv=Buffer.from(e.iv,'base64'),tag=Buffer.from(e.tag,'base64');
  if(iv.length!==12||tag.length!==16)throw Error();
  const d=createDecipheriv('aes-256-gcm',Buffer.from(c.key,'hex'),iv);
  d.setAAD(Buffer.from('marceline-relay-v1:'+box+':'+c[box]));d.setAuthTag(tag);
  const v=JSON.parse(Buffer.concat([d.update(Buffer.from(e.data,'base64')),d.final()]));
  if(v.v!==1||!Array.isArray(v.entries)||v.entries.length>LIMIT)throw Error();
  const ids=new Set();
  for(const x of v.entries){
   if(!x||!idok(x.id)||ids.has(x.id)||!Number.isSafeInteger(x.expires))throw Error();
   ids.add(x.id);
   if(box==='request'){
    if(!ops.has(x.op)||!Number.isSafeInteger(x.created)||x.expires-x.created!==TTL)throw Error();
    if(x.op==='ping'&&(typeof x.payload!=='string'||Buffer.byteLength(x.payload)>4096))throw Error();
    if(x.op==='lean-check'&&(!x.payload||typeof x.payload!=='object'||!(/^[0-9a-f]{64}$/.test(x.payload.job))))throw Error();
    if(x.op==='lb-cert'&&!lbOK(x.payload))throw Error();
    if(x.op==='sibling'&&!sibOK(x.payload))throw Error();
   }
   if(box==='response'&&(!['ack','running','done','error'].includes(x.state)||!Array.isArray(x.events)))throw Error();
  }
  return v;
 }catch{throw Error('relay envelope authentication/schema failed');}
}
async function http(c,box,options={}){
 try{return await fetch(BASE+c[box],{...options,redirect:'error',signal:AbortSignal.timeout(10000)});}
 catch{throw Error('relay HTTP unavailable');}
}
async function get(c,box){
 const r=await http(c,box,{cache:'no-store'});
 if(r.status===404){await r.body?.cancel();return {etag:null,value:{v:1,entries:[],heartbeat:null}};}
 if(r.status!==200||!r.headers.get('etag')){await r.body?.cancel();throw Error('relay read HTTP '+r.status);}
 const reader=r.body.getReader();let length=0;const chunks=[];
 for(;;){
  const {done,value}=await reader.read();if(done)break;length+=value.length;
  if(length>MAX){await reader.cancel();throw Error('oversized mailbox');}
  chunks.push(Buffer.from(value));
 }
 return {etag:r.headers.get('etag'),value:open(c,box,Buffer.concat(chunks))};
}
async function change(c,box,fn){
 for(let i=0;i<8;i++){
  const {etag,value}=await get(c,box),next=fn(value);
  if(!next)return value;
  const body=seal(c,box,next);if(Buffer.byteLength(body)>MAX)throw Error('mailbox capacity exceeded');
  const headers={'Content-Type':'application/json',...(etag?{'If-Match':etag}:{'X-Skrynia-Mode':'public-write'})};
  const r=await http(c,box,{method:etag?'PUT':'POST',headers,body});
  await r.body?.cancel();
  if(r.status===(etag?200:201))return next;
  if(![409,412].includes(r.status))throw Error('relay write HTTP '+r.status);
  await sleep(50+Math.random()*150);
 }
 throw Error('mailbox contention; retry');
}
function live(e,now){return Number.isSafeInteger(e.expires)&&e.expires+SKEW>now&&e.expires<=now+TTL+SKEW;}
function privateDir(root){
 fs.mkdirSync(root,{recursive:true,mode:0o700});
 const st=fs.lstatSync(root);
 if(!st.isDirectory()||st.uid!==process.getuid()||(st.mode&0o077))throw Error('relay state directory must be private');
 return root;
}
function localFile(kind,id){
 if(!idok(id))throw Error('invalid request ID');
 return path.join(privateDir(path.join(privateDir(stateRoot),kind)),id+'.json');
}
function save(kind,id,value){
 const dest=localFile(kind,id),tmp=dest+'.'+randomUUID()+'.tmp';
 try{
  const fd=fs.openSync(tmp,'wx',0o600);
  try{fs.writeFileSync(fd,JSON.stringify(value));fs.fsyncSync(fd);}finally{fs.closeSync(fd);}
  fs.renameSync(tmp,dest);
  const dir=fs.openSync(path.dirname(dest),'r');try{fs.fsyncSync(dir);}finally{fs.closeSync(dir);}
 }finally{try{fs.unlinkSync(tmp);}catch(e){if(e.code!=='ENOENT')throw e;}}
}
function load(kind,id){
 try{
  const p=localFile(kind,id),fd=fs.openSync(p,fs.constants.O_RDONLY|fs.constants.O_NOFOLLOW|fs.constants.O_NONBLOCK);
  try{
   const st=fs.fstatSync(fd);if(!st.isFile()||st.uid!==process.getuid()||(st.mode&0o077)||st.size>MAX)throw Error('invalid private relay receipt');
   return JSON.parse(fs.readFileSync(fd,'utf8'));
  }finally{fs.closeSync(fd);}
 }catch(e){if(e.code==='ENOENT')return null;throw e;}
}
function remove(kind,id){try{fs.unlinkSync(localFile(kind,id));}catch(e){if(e.code!=='ENOENT')throw e;}}
function pruneLocal(kind,maxAge){
 const dir=privateDir(path.join(privateDir(stateRoot),kind)),now=Date.now();
 for(const ent of fs.readdirSync(dir,{withFileTypes:true})){
  if(!ent.isFile()||!/^[-0-9a-f]{36}\.json$/.test(ent.name))continue;
  const p=path.join(dir,ent.name);try{if(now-fs.statSync(p).mtimeMs>maxAge)fs.unlinkSync(p);}catch(e){if(e.code!=='ENOENT')throw e;}
 }
}
function makeRequest(op,payload,id=randomUUID(),now=Date.now()){
 if(!ops.has(op)||!idok(id))throw Error('invalid relay operation or ID');
 return {id,op,payload,created:now,expires:now+TTL};
}
async function enqueue(c,request){
 if(!live(request,Date.now()))throw Error('request expired');
 await change(c,'request',v=>{
  const entries=v.entries.filter(e=>live(e,Date.now()));
  const old=entries.find(e=>e.id===request.id);
  if(old){
   if(JSON.stringify(old)!==JSON.stringify(request))throw Error('request identity conflict');
   return null;
  }
  if(entries.length>=LIMIT)throw Error('relay queue full');
  return {...v,entries:[...entries,request]};
 });
}
async function cleanup(c,id){
 await change(c,'request',v=>v.entries.some(e=>e.id===id)?{...v,entries:v.entries.filter(e=>e.id!==id)}:null);
 remove('requests',id);
}
function terminal(e){return e&&['done','error'].includes(e.state);}
function returnResult(e){
 console.log(JSON.stringify(e));
 return e.state==='done'?0:1;
}
async function wait(c,id,seconds){
 if(!idok(id))throw Error('invalid request ID');
 const cached=load('receipts',id);
 if(cached){try{await cleanup(c,id);}catch{console.error('cleanup deferred to expiry');}return returnResult(cached);}
 let last='',lastReport=0,lastBeat=null,lastObserved=null,lastEnqueue=0;
 const deadline=Date.now()+seconds*1000;
 while(Date.now()<deadline){
  if(load('cancelled',id)){try{await cleanup(c,id);}catch{}console.error('request cancelled');return 1;}
  try{
   const v=(await get(c,'response')).value,e=v.entries.find(x=>x.id===id);
   const now=Date.now();
   if(v.heartbeat!==lastBeat){lastBeat=v.heartbeat;lastObserved=now;}
   const nextState=e?.state||'waiting_for_ack',changed=nextState!==last;
   if(changed||now-lastReport>=10000){
    last=nextState;lastReport=now;
    console.error(JSON.stringify({id,state:last,heartbeat:v.heartbeat,heartbeat_age_seconds:v.heartbeat?Math.max(0,Math.round((now-v.heartbeat)/1000)):null,
      heartbeat_observed_seconds:lastObserved===null?null:Math.round((now-lastObserved)/1000),events:changed?e?.events:undefined}));
   }
   if(terminal(e)){
    // Persist before output or cleanup: a restarted client can retrieve the same result.
    save('receipts',id,e);
    try{await cleanup(c,id);}catch{console.error('cleanup deferred to expiry');}
    return returnResult(e);
   }
   const request=load('requests',id);
   if(request&&!e&&!load('cancelled',id)&&now-lastEnqueue>=10000){
    lastEnqueue=now;
    await enqueue(c,request);
    if(load('cancelled',id))await cleanup(c,id);
   }
  }catch(e){if(Date.now()-lastReport>=10000){console.error('poll: '+e.message);lastReport=Date.now();}}
  await sleep(last==='waiting_for_ack'?1000:1500);
 }
 console.error('timeout; resume with marceline-request wait '+id);return 2;
}
function event(entry,state,message){return {...entry,state,events:[...(entry.events||[]),{at:Date.now(),state,message}].slice(-12)};}
async function putResponse(c,entry){
 return change(c,'response',v=>({...v,heartbeat:Date.now(),entries:[...v.entries.filter(e=>e.id!==entry.id),entry]}));
}
function leanConfig(){
 const p=path.join(HOME,'.config/marceline-relay/lean.json');
 try{
  const st=fs.lstatSync(p);
  if(!st.isFile()||st.uid!==process.getuid()||(st.mode&0o077))throw Error('invalid Lean configuration permissions');
  return p;
 }catch(e){if(e.code==='ENOENT')return null;throw e;}
}
function capabilities(){
 try{
  const p=leanConfig();
  if(!p)return {ping:true,lean_bases:[]};
  const cfg=JSON.parse(fs.readFileSync(p,'utf8'));
  const lean_bases=fs.readdirSync(cfg.manifests).filter(x=>/^[0-9a-f]{40}\.json$/.test(x))
   .filter(x=>{const st=fs.lstatSync(path.join(cfg.manifests,x));return st.isFile()&&st.uid===process.getuid()&&!(st.mode&0o077);})
   .map(x=>x.slice(0,-5)).filter(base=>{try{const st=fs.lstatSync(path.join(cfg.manifests,base+'.provenance.json'));return st.isFile()&&st.uid===process.getuid()&&!(st.mode&0o077);}catch{return false;}}).sort();
  return {ping:true,lean_bases,max_parallel_lean:MAX_LEAN,lb_cert:fs.existsSync(path.join(HERE,'lb-handler.py')),sibling:fs.existsSync(path.join(HERE,'sib-handler.py')),max_parallel_lb:MAX_LB,max_parallel_lb_check:MAX_LB_CHECK};
 }catch{return {ping:true,lean_bases:[]};}
}
function launchLean(req){
 let configuration;
 try{configuration=leanConfig();}catch{return {promise:Promise.resolve({error:'invalid Lean operator configuration'}),cancel:()=>{}};}
 if(!configuration)return {promise:Promise.resolve({error:'remote Lean compiler is not configured'}),cancel:()=>{}};
 // The request selects only data, never a command, interpreter, path or shell.
 const child=spawn(path.join(HOME,'.local/bin/python3'),[path.join(HERE,'lean-handler.py'),configuration],{
  stdio:['pipe','pipe','ignore'],env:{HOME,PATH:process.env.PATH||'/usr/bin:/bin',LANG:'C.UTF-8'},shell:false
 });
 let out=Buffer.alloc(0),failed=false;
 const deadline=setTimeout(()=>{failed=true;child.kill('SIGTERM');},1000000);deadline.unref();
 child.stdout.on('data',b=>{if(out.length+b.length>256*1024){failed=true;child.kill('SIGTERM');}else out=Buffer.concat([out,b]);});
 child.stdin.on('error',()=>{});
 child.stdin.end(JSON.stringify(req.payload));
 const promise=new Promise(resolve=>{
  child.on('error',()=>resolve({error:'cannot start isolated Lean handler'}));
  child.on('close',code=>{
   clearTimeout(deadline);
   if(code!==0||failed)return resolve({error:'isolated Lean handler failed'});
   try{
    const result=JSON.parse(out);
    if(result?.error)return resolve({error:'Lean request rejected by handler'});
    if(!result||typeof result!=='object'||result.job!==req.payload.job||result.base!==req.payload.base||
       result.toolchain!==req.payload.toolchain||result.attempt!==req.payload.attempt||result.source_sha256!==req.payload.source_sha256)throw Error();
    resolve({result});
   }
   catch{resolve({error:'invalid isolated Lean handler response'});}
  });
 });
 return {promise,cancel:()=>child.kill('SIGTERM')};
}
function launchLb(req){return launchHandler(req,'lb-handler.py');}
function launchHandler(req,script){
 // Fixed handler, no shell; the request supplies only validated data on stdin.
 const child=spawn(path.join(HOME,'.local/bin/python3'),[path.join(HERE,script)],{
  stdio:['pipe','pipe','ignore'],env:{HOME,PATH:path.join(HOME,'.elan/bin')+':'+(process.env.PATH||'/usr/bin:/bin'),LANG:'C.UTF-8'},shell:false,detached:true
 });
 function killGroup(){
  if(!child.pid)return;
  try{process.kill(-child.pid,'SIGTERM');}catch{}
  const escalation=setTimeout(()=>{try{process.kill(-child.pid,'SIGKILL');}catch{}},1500);
  escalation.unref();
 }
 let out=Buffer.alloc(0),failed=false;
 const deadline=setTimeout(()=>{failed=true;killGroup();},1800000);deadline.unref();
 child.stdout.on('data',b=>{if(out.length+b.length>1536*1024){failed=true;killGroup();}else out=Buffer.concat([out,b]);});
 child.stdin.on('error',()=>{});
 child.stdin.end(JSON.stringify(req.payload));
 const promise=new Promise(resolve=>{
  child.on('error',()=>resolve({error:'cannot start lb-cert handler'}));
  child.on('close',code=>{
   clearTimeout(deadline);
   if(code!==0||failed)return resolve({error:'lb-cert handler failed'});
   try{const result=JSON.parse(out);if(!result||result.module!==req.payload.module)throw Error();resolve({result});}
   catch{resolve({error:'invalid lb-cert handler response'});}
  });
 });
 return {promise,cancel:()=>killGroup()};
}
// Generation and verification have independent admission; compiler memory
// remains governed by the common compile_admission.py lock.
function lbAdmitted(req,active){
 const check=Boolean(req.payload.check_file_gz_b64);
 const count=active.filter(a=>a.op==='lb-cert'&&!a.finished&&Boolean(a.check)===check).length;
 return count<(check?MAX_LB_CHECK:MAX_LB);
}
async function worker(c){
 const host=os.hostname();
 if(host!=='marceline-dev')throw Error('worker must run on marceline-dev');
 console.error('relay worker started');
 const active=new Map();let lastError='',lastErrorAt=0,stopping=false;
 const stop=()=>{stopping=true;for(const a of active.values())if(!a.finished)a.cancel();};
 process.on('SIGTERM',stop);process.on('SIGINT',stop);
 while(!stopping){
  try{
   const now=Date.now(),rq=(await get(c,'request')).value.entries.filter(e=>live(e,now)),ids=new Set(rq.map(e=>e.id));
   for(const [id,a] of active)if(!ids.has(id)&&!a.finished)a.cancel();
   const response=await change(c,'response',v=>{
    const entries=v.entries.filter(e=>ids.has(e.id));
    if(v.heartbeat&&now-v.heartbeat<10000&&entries.length===v.entries.length)return null;
    return {...v,heartbeat:now,entries,capabilities:capabilities()};
   });
   const priority=req=>req.op==='ping'?0:req.op==='lean-check'&&req.payload.mode==='elaborate'?1:
    req.op==='lb-cert'&&req.payload.check_file_gz_b64?2:req.op==='lb-cert'?3:req.op==='lean-check'?4:5;
   for(const req of [...rq].sort((a,b)=>priority(a)-priority(b)||a.created-b.created)){
    const old=response.entries.find(e=>e.id===req.id);
    if(terminal(old))continue;
    const receipt=load('worker-receipts',req.id);
    if(receipt){await putResponse(c,receipt);continue;}
    if(active.has(req.id))continue;
    let entry=old;
    if(!entry||entry.state==='running'){
     entry=event(entry||{id:req.id,expires:req.expires},'ack','request authenticated and received');
     await putResponse(c,entry);
    }
    if(stopping)break;
    if(req.op==='lean-check'){
     const running=[...active.values()].filter(a=>a.op==='lean-check'&&!a.finished);
     const wanted=req.payload.rss_mib;
     if(running.length>=MAX_LEAN||running.reduce((n,a)=>n+a.rss,0)+wanted>LEAN_BUDGET)continue;
    }
    if(req.op==='lb-cert'&&!lbAdmitted(req,[...active.values()]))continue;
    if(req.op==='sibling'&&[...active.values()].filter(a=>a.op==='sibling'&&!a.finished).length>=4)continue;
    if(req.op==='ping'){
     const result=event({...entry,result:{host,echo:req.payload}},'done','ping complete');
     save('worker-receipts',req.id,result);await putResponse(c,result);
    }else{
     entry=event(entry,'running','isolated Lean handler dispatched');
     await putResponse(c,entry);
     const job=req.op==='lb-cert'?launchLb(req):req.op==='sibling'?launchHandler(req,'sib-handler.py'):launchLean(req),a={...job,op:req.op,check:Boolean(req.payload.check_file_gz_b64),rss:req.payload.rss_mib||0,finished:false};
     active.set(req.id,a);
     job.promise.then(out=>{
      a.finished=true;
      a.receipt=out.error?event(entry,'error',out.error):event({...entry,result:out.result},'done','isolated Lean handler returned');
      // Only the worker loop publishes to the response mailbox.
      try{save('worker-receipts',req.id,a.receipt);}catch{console.error('worker receipt persistence failed');}
     });
    }
   }
   for(const [id,a] of active){
    if(!a.finished)continue;
    if(ids.has(id))await putResponse(c,a.receipt);
    active.delete(id);
   }
   pruneLocal('worker-receipts',24*60*60*1000);
  }catch(e){
   const now=Date.now();if(e.message!==lastError||now-lastErrorAt>60000){console.error('relay cycle: '+e.message);lastError=e.message;lastErrorAt=now;}
  }
  if(!stopping)await sleep(active.size?800:1500);
 }
 for(const a of active.values())if(!a.finished)a.cancel();
 await Promise.race([Promise.allSettled([...active.values()].map(a=>a.promise)),sleep(20000,undefined,{ref:false})]);
}
function payload(op,args){
 if(op==='ping'){
  const msg=args.join(' ');if(Buffer.byteLength(msg)>4096)throw Error('ping payload too large');return msg;
 }
 if(op==='lean-check'){
  if(args.length!==1)throw Error('lean-check requires one validated job JSON file');
  const st=fs.statSync(args[0]);if(!st.isFile()||st.size>JOB_MAX)throw Error('invalid Lean job file');
  const value=JSON.parse(fs.readFileSync(args[0],'utf8'));
  if(!value||!(/^[0-9a-f]{64}$/.test(value.job)))throw Error('invalid Lean job identity');
  return value;
 }
 if(op==='sibling'){
  if(args.length!==1)throw Error('sibling requires one request JSON file');
  const st=fs.statSync(args[0]);if(!st.isFile()||st.size>65536)throw Error('invalid sibling request file');
  const value=JSON.parse(fs.readFileSync(args[0],'utf8'));
  if(!sibOK(value))throw Error('invalid sibling request: statement, module, imports, max_tries');
  return value;
 }
 if(op==='lb-cert'){
  if(args.length!==1)throw Error('lb-cert requires one request JSON file');
  const st=fs.statSync(args[0]);if(!st.isFile()||st.size>LB_CHECK_MAX+65536)throw Error('invalid lb-cert request file');
  const value=JSON.parse(fs.readFileSync(args[0],'utf8'));
  if(!lbOK(value))throw Error('invalid lb-cert request: statement, module, maxstates, chunks');
  return value;
 }
 throw Error('unknown relay operation');
}
async function main(){
 const [cmd,arg,...rest]=process.argv.slice(2);
 if(!cmd||cmd==='--help'){
  console.log('marceline-request status [BASE_SHA] | ping [message] | lean-check JOB.json | submit OP [argument] (OP: ping, lean-check, lb-cert REQ.json, sibling REQ.json) | wait ID [seconds] | cancel ID');return 0;
 }
 const c=config();
 if(cmd!=='worker'){pruneLocal('requests',TTL+SKEW);pruneLocal('receipts',24*60*60*1000);pruneLocal('cancelled',24*60*60*1000);}
 if(cmd==='worker'){await worker(c);return 0;}
 if(cmd==='status'){
  const r=(await get(c,'response')).value,delta=r.heartbeat?Math.round((Date.now()-r.heartbeat)/1000):null;
  const summary={heartbeat:r.heartbeat,age_seconds:delta===null?null:Math.max(0,delta),
   server_ahead_seconds:delta===null?null:Math.max(0,-delta),entries:r.entries.map(({id,state})=>({id,state}))};
  if(arg){
   if(!/^[0-9a-f]{40}$/.test(arg))throw Error('status base must be a 40-hex SHA');
   summary.base=arg;summary.base_available=delta!==null&&delta>=-120&&delta<=180&&(r.capabilities?.lean_bases||[]).includes(arg);
   summary.running=r.entries.filter(e=>e.state==='running').length;
   summary.queued=r.entries.filter(e=>e.state==='ack').length;
   summary.queue=summary.running+summary.queued;
   summary.parallel=r.capabilities?.max_parallel_lean||1;
  }else summary.capabilities=r.capabilities||null;
  console.log(JSON.stringify(summary));return 0;
 }
 if(cmd==='ping'||cmd==='lean-check'||cmd==='submit'){
  const op=cmd==='submit'?arg:cmd,args=cmd==='submit'?rest:[arg,...rest].filter(x=>x!==undefined);
  const request=makeRequest(op,payload(op,args));
  pruneLocal('requests',TTL+SKEW);pruneLocal('receipts',24*60*60*1000);
  save('requests',request.id,request);console.error('request '+request.id);
  if(cmd==='submit'){await enqueue(c,request);console.log(request.id);return 0;}
  try{await enqueue(c,request);}catch(e){console.error('initial send: '+e.message);}
  return wait(c,request.id,op==='ping'?90:1100);
 }
 if(cmd==='wait'){
  const n=Number(rest[0]??90);if(!Number.isFinite(n)||n<1||n>1800)throw Error('wait must be 1–1800 seconds');
  return wait(c,arg,n);
 }
 if(cmd==='cancel'){
  if(!idok(arg)||!load('requests',arg))throw Error('no pending local request with that ID');
  save('cancelled',arg,{id:arg,at:Date.now()});remove('requests',arg);
  await cleanup(c,arg);console.log(JSON.stringify({id:arg,cancel_requested:true}));return 0;
 }
 throw Error('unknown command; use --help');
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))main().then(n=>{process.exitCode=n;}).catch(e=>{console.error(e.message);process.exitCode=1;});
export {seal,open,live,event,makeRequest,enqueue,get,change,payload,lbAdmitted};
