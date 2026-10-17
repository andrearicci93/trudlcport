import sys;sys.path.insert(0,'.')
import dm,struct,re
def search(pat,lo=0,hi=1<<32,maxn=50):
    out=[]
    for a,s,p in dm.RG:
        if a+s<lo or a>=hi: continue
        dm.F.seek(p); d=dm.F.read(s)
        for m in re.finditer(re.escape(pat),d,re.S):
            out.append(a+m.start())
            if len(out)>=maxn: return out
    return out
if __name__=='__main__':
    pat=bytes.fromhex(sys.argv[1])
    print([hex(x) for x in search(pat)])
