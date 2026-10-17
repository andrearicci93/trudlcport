import sys,io,contextlib,json
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import real_tex_gate as G
L=G.libs(); D,P=L['D'],L['P']
XL=G.XL
def xinfo(i):
    lib=D[i]; out=[]
    for s in sorted(set(lib['slots'])-{0xFFFFFFFF}):
        sh=XL.parse(lib['entries'][s]['blob'])
        out.append((s,len(lib['entries'][s]['blob']),[ (c['name'][:30],c['set'],c['reg'],c['count']) for c in sh.ctab]))
    return out
for a in sys.argv[1:]:
    i=int(a)
    if i in D:
        print('== DLC lib',i,'kind',D[i].get('kind'),'slots',D[i]['slots'])
        for s,n,ct in xinfo(i)[:1]: print('  slot',s,'blob',n,'ctab',ct)
    if i in P: print('== PC lib',i,'slots',P[i]['slots'])
