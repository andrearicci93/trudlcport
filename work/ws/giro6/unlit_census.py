"""Materiali DLC il cui PS (pos2) e' un surrogato PC di classe C/D e la lib Xbox NON ha luci: candidati f13 (traduzione diretta)."""
import sys,io,contextlib,json,struct,collections,re
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import real_tex_gate as G
C=G.C; T=G.T; L=G.libs(); DM,D,P=L['DM'],L['D'],L['P']; XL=G.XL
LN=re.compile(r'p_Lights|ParallelShadow|ShadowMap|p_ShadowEnabled|p_ProjectionEnabled|LightEnabled|Irradiance|ModulationMaps')
sm=json.load(open(T+'work/render/dlc_shader_map.json'))
tree=C.read_tree(T+'work/ws/giro6/compose/mods')
use=collections.defaultdict(list)
for rel,d in tree.items():
    pcm={s.id:s for s in d.sections if s.type==10}
    for mid,s in pcm.items():
        if mid not in DM: continue
        pl=struct.unpack_from('<4I',s.data,0x28); xl=struct.unpack_from('>4I',DM[mid][0],0x28)
        use[(mid,xl,pl)].append(rel)
cand={}
for (mid,xl,pl),drms in use.items():
    x=xl[2]
    if x in (0,0xffffffff) or x not in D: continue
    e=sm.get(str(x),{})
    if D[x].get('kind')!=1: continue
    names=set()
    for s in set(D[x]['slots'])-{0xFFFFFFFF}:
        names|={c['name'] for c in XL.parse(D[x]['entries'][s]['blob']).ctab}
    lit=[n for n in names if LN.search(n)]
    cand.setdefault(x,[]).append((mid,pl[2],e.get('cls'),e.get('score'),bool(lit),sorted(set(drms))))
rows=[]
for x,v in sorted(cand.items()):
    cls=v[0][2]
    rows.append((x,cls,v[0][3],v[0][4],[(m,pc) for m,pc,*_ in v],sorted({d for *_,ds in v for d in ds})))
print('lib PS pos2 di materiali DLC:',len(rows))
print('--- NON illuminate (nessun nome luci) con classe C/D:')
for x,cls,sc,lit,ms,ds in rows:
    if not lit and cls in ('C1','C2','C3','D'): print(x,cls,sc,'mat',ms[:6],'DRM',[d.replace('streamgroups/','sg/') for d in ds][:5])
print('--- classi A/B non illuminate:', sum(1 for r in rows if not r[3] and r[1] in ('A','B')))
print('--- illuminate (C/D):', sum(1 for r in rows if r[3] and r[1] in ('C1','C2','C3','D')))
