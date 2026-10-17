import sys,re,glob,bisect,pickle,os
D=os.path.expanduser('~/Downloads/ghidra_out/full')
IDX='/private/tmp/claude-501/-Users-user-Downloads-tru-port/e25a373a-023f-4b1d-95c4-ee8d35eac56e/scratchpad/idx.pkl'
if os.path.exists(IDX): starts,locs=pickle.load(open(IDX,'rb'))
else:
    L=[]
    for f in sorted(glob.glob(D+'/*.c')):
        t=open(f,errors='replace').read()
        ms=list(re.finditer(r'^//=== (\S+) @ ([0-9a-fA-F]+)',t,re.M))
        for i,m in enumerate(ms):
            e=ms[i+1].start() if i+1<len(ms) else len(t)
            L.append((int(m.group(2),16),f,m.start(),e))
    L.sort(); starts=[x[0] for x in L]; locs=L
    pickle.dump((starts,locs),open(IDX,'wb'))
def get(a):
    i=bisect.bisect_right(starts,a)-1
    s,f,b,e=locs[i]
    return s,open(f,errors='replace').read()[b:e]
if __name__=='__main__':
    for x in sys.argv[1:]:
        a=int(x,16); s,t=get(a)
        print(f'##### {x} -> fn @ {s:08x} ({len(t)} bytes)'); print(t if '-n' not in sys.argv else '')
