#!/usr/bin/env python3
"""Add the `sibling` operation to relay.mjs (requires the lb-cert patch; idempotent)."""
import sys
p = sys.argv[1]
s = open(p).read()
if "'sibling'" in s:
    print('already patched'); sys.exit(0)
assert "'lb-cert'" in s, 'apply patch_relay.py first'


def rep(old, new):
    global s
    assert s.count(old) == 1, 'anchor not unique: ' + old[:70]
    s = s.replace(old, new)


rep("const ops=new Set(['ping','lean-check','lb-cert']);",
    "const ops=new Set(['ping','lean-check','lb-cert','sibling']);")
rep("    if(x.op==='lb-cert'&&!lbOK(x.payload))throw Error();",
    "    if(x.op==='lb-cert'&&!lbOK(x.payload))throw Error();\n"
    "    if(x.op==='sibling'&&!sibOK(x.payload))throw Error();")
rep("function open(c,box,raw){",
    "// sibling: transfer of a merged same-skeleton proof (data only: statement, module, imports, a bound).\n"
    "function sibOK(p){return !!p&&typeof p==='object'&&typeof p.statement==='string'&&Buffer.byteLength(p.statement)<=16384&&\n"
    " /^PEqualNP\\.Outside\\.[A-Za-z0-9_]{1,80}$/.test(p.module)&&Array.isArray(p.imports)&&p.imports.length<=16&&\n"
    " p.imports.every(i=>typeof i==='string'&&/^[A-Za-z][A-Za-z0-9_.]{0,120}$/.test(i))&&\n"
    " Number.isSafeInteger(p.max_tries)&&p.max_tries>=1&&p.max_tries<=16;}\n"
    "function open(c,box,raw){")
rep("function launchLb(req){",
    "function launchLb(req){return launchHandler(req,'lb-handler.py');}\n"
    "function launchHandler(req,script){")
rep("[path.join(HERE,'lb-handler.py')],{", "[path.join(HERE,script)],{")
rep("    if(req.op==='lb-cert'&&[...active.values()].filter(a=>a.op==='lb-cert'&&!a.finished).length>=MAX_LB)continue;",
    "    if(req.op==='lb-cert'&&[...active.values()].filter(a=>a.op==='lb-cert'&&!a.finished).length>=MAX_LB)continue;\n"
    "    if(req.op==='sibling'&&[...active.values()].filter(a=>a.op==='sibling'&&!a.finished).length>=4)continue;")
rep("     const job=req.op==='lb-cert'?launchLb(req):launchLean(req)",
    "     const job=req.op==='lb-cert'?launchLb(req):req.op==='sibling'?launchHandler(req,'sib-handler.py'):launchLean(req)")
rep(" if(op==='lb-cert'){",
    " if(op==='sibling'){\n"
    "  if(args.length!==1)throw Error('sibling requires one request JSON file');\n"
    "  const st=fs.statSync(args[0]);if(!st.isFile()||st.size>65536)throw Error('invalid sibling request file');\n"
    "  const value=JSON.parse(fs.readFileSync(args[0],'utf8'));\n"
    "  if(!sibOK(value))throw Error('invalid sibling request: statement, module, imports, max_tries');\n"
    "  return value;\n"
    " }\n"
    " if(op==='lb-cert'){")
rep("lb_cert:fs.existsSync(path.join(HERE,'lb-handler.py')),",
    "lb_cert:fs.existsSync(path.join(HERE,'lb-handler.py')),sibling:fs.existsSync(path.join(HERE,'sib-handler.py')),")
rep("(OP: ping, lean-check, lb-cert REQ.json)", "(OP: ping, lean-check, lb-cert REQ.json, sibling REQ.json)")
open(p, 'w').write(s)
print('patched')
