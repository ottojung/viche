#!/usr/bin/env python3
"""Add the `lb-cert` operation to relay.mjs (idempotent). usage: patch_relay.py RELAY.mjs"""
import sys
p = sys.argv[1]
s = open(p).read()
if "'lb-cert'" in s:
    print('already patched'); sys.exit(0)


def rep(old, new):
    global s
    assert s.count(old) == 1, 'anchor not unique: ' + old[:60]
    s = s.replace(old, new)


rep("const ops=new Set(['ping','lean-check']);",
    "const ops=new Set(['ping','lean-check','lb-cert']);\nconst MAX_LB=8;")
rep("    if(x.op==='lean-check'&&(!x.payload||typeof x.payload!=='object'||!(/^[0-9a-f]{64}$/.test(x.payload.job))))throw Error();",
    "    if(x.op==='lean-check'&&(!x.payload||typeof x.payload!=='object'||!(/^[0-9a-f]{64}$/.test(x.payload.job))))throw Error();\n"
    "    if(x.op==='lb-cert'&&!lbOK(x.payload))throw Error();")
rep("function open(c,box,raw){",
    "// lb-cert: a lower-bound certificate request (data only: statement text, module name, two bounded integers).\n"
    "function lbOK(p){return !!p&&typeof p==='object'&&typeof p.statement==='string'&&Buffer.byteLength(p.statement)<=16384&&\n"
    " /^PEqualNP\\.Outside\\.[A-Za-z0-9_]{1,80}$/.test(p.module)&&Number.isSafeInteger(p.maxstates)&&p.maxstates>=1&&p.maxstates<=300000&&\n"
    " Number.isSafeInteger(p.chunks)&&p.chunks>=1&&p.chunks<=200;}\n"
    "function open(c,box,raw){")
rep("  return {ping:true,lean_bases,max_parallel_lean:MAX_LEAN};",
    "  return {ping:true,lean_bases,max_parallel_lean:MAX_LEAN,lb_cert:fs.existsSync(path.join(HERE,'lb-handler.py')),max_parallel_lb:MAX_LB};")
rep("async function worker(c){",
    "function launchLb(req){\n"
    " // Fixed handler, no shell; the request supplies only validated data on stdin.\n"
    " const child=spawn(path.join(HOME,'.local/bin/python3'),[path.join(HERE,'lb-handler.py')],{\n"
    "  stdio:['pipe','pipe','ignore'],env:{HOME,PATH:path.join(HOME,'.elan/bin')+':'+(process.env.PATH||'/usr/bin:/bin'),LANG:'C.UTF-8'},shell:false\n"
    " });\n"
    " let out=Buffer.alloc(0),failed=false;\n"
    " const deadline=setTimeout(()=>{failed=true;child.kill('SIGTERM');},1800000);deadline.unref();\n"
    " child.stdout.on('data',b=>{if(out.length+b.length>1536*1024){failed=true;child.kill('SIGTERM');}else out=Buffer.concat([out,b]);});\n"
    " child.stdin.on('error',()=>{});\n"
    " child.stdin.end(JSON.stringify(req.payload));\n"
    " const promise=new Promise(resolve=>{\n"
    "  child.on('error',()=>resolve({error:'cannot start lb-cert handler'}));\n"
    "  child.on('close',code=>{\n"
    "   clearTimeout(deadline);\n"
    "   if(code!==0||failed)return resolve({error:'lb-cert handler failed'});\n"
    "   try{const result=JSON.parse(out);if(!result||result.module!==req.payload.module)throw Error();resolve({result});}\n"
    "   catch{resolve({error:'invalid lb-cert handler response'});}\n"
    "  });\n"
    " });\n"
    " return {promise,cancel:()=>child.kill('SIGTERM')};\n"
    "}\n"
    "async function worker(c){")
rep("    if(req.op==='ping'){\n     const result=",
    "    if(req.op==='lb-cert'&&[...active.values()].filter(a=>a.op==='lb-cert'&&!a.finished).length>=MAX_LB)continue;\n"
    "    if(req.op==='ping'){\n     const result=")
rep("     const job=launchLean(req),a={...job,op:req.op,rss:req.payload.rss_mib,finished:false};",
    "     const job=req.op==='lb-cert'?launchLb(req):launchLean(req),a={...job,op:req.op,rss:req.payload.rss_mib||0,finished:false};")
rep(" throw Error('unknown relay operation');\n}",
    " if(op==='lb-cert'){\n"
    "  if(args.length!==1)throw Error('lb-cert requires one request JSON file');\n"
    "  const st=fs.statSync(args[0]);if(!st.isFile()||st.size>65536)throw Error('invalid lb-cert request file');\n"
    "  const value=JSON.parse(fs.readFileSync(args[0],'utf8'));\n"
    "  if(!lbOK(value))throw Error('invalid lb-cert request: statement, module, maxstates, chunks');\n"
    "  return value;\n"
    " }\n"
    " throw Error('unknown relay operation');\n}")
rep("lean-check JOB.json | submit OP [argument]", "lean-check JOB.json | submit OP [argument] (OP: ping, lean-check, lb-cert REQ.json)")
open(p, 'w').write(s)
print('patched')
