"""Extract literal, replayed public witnesses from a pinned upstream mirror."""
import argparse, collections, json, re, subprocess
from pathlib import Path

def extract(mirror,ref,count):
    git=['git','--git-dir='+str(mirror)]
    head=subprocess.check_output(git+['rev-parse',ref],text=True).strip()
    commits=subprocess.check_output(git+['log','-n',str(count),'--format=%H%x09%s',head],text=True).splitlines()
    roots=[sum(1<<i for i in range(64) if i>>j&1) for j in range(6)]
    out=[]
    with subprocess.Popen(git+['cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE) as p:
        for line in commits:
            c,s=line.split('\t',1);m=re.match(r'L-meta-(\d+)\b',s)
            if not m:continue
            n=m[1];p.stdin.write((f'{c}:lean/PEqualNP/Outside/L_meta_{n}.lean\n').encode());p.stdin.flush()
            z=p.stdout.readline().split()
            if not z or z[-1]==b'missing':continue
            src=p.stdout.read(int(z[-1])).decode('utf-8','replace');p.stdout.read(1)
            # Honor source-language restrictions conservatively.
            if re.search(r'[\u0400-\u052f]',src):continue
            t=re.search(r'Nat.testBit\s*\((\d+)\s*\*\s*2\s*\^\s*32\s*\+\s*(\d+)\)',src)
            if not t:continue
            mask=int(t[1])*2**32+int(t[2])
            w=re.search(r'(?m)^def\s+(?:wgates|witness|sixWitness|mono|witGates)\s*:\s*(?:List Gate|Circuit)\s*:=\s*(?:⟨\s*)?\[(.*?)\]\s*(?:,\s*\d+\s*⟩)?\s*$',src,re.S|re.M)
            if not w or len(w[1])>10000:continue
            gates=re.findall(r'⟨\s*(?:GateOp)?\.(and|or)\s*,\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*⟩',w[1])
            if not 0<len(gates)<=13:continue
            bank=roots[:]
            try:
                for op,a,b in gates:
                    if not 0<=int(a)<len(bank) or not 0<=int(b)<len(bank):raise ValueError()
                    bank.append((bank[int(a)]&bank[int(b)]) if op=='and' else (bank[int(a)]|bank[int(b)]))
            except (ValueError,IndexError):continue
            if bank[-1]!=mask:continue
            out.append(dict(id='L-meta-'+n,commit=c,blob=z[0].decode(),mask=mask,gates=gates))
        p.stdin.close();p.wait(timeout=30)
    return head,out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mirror',type=Path);p.add_argument('ref');p.add_argument('output',type=Path)
    p.add_argument('--count',type=int,default=400)
    a=p.parse_args()
    h,data=extract(a.mirror,a.ref,a.count)
    a.output.write_text(json.dumps(data,indent=2)+'\n')
    print(h,len(data),collections.Counter(len(x['gates']) for x in data))
