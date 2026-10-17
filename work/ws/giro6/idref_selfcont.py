"""Giro 6: come tex_selfcont ma per TUTTI i tipi di idref (gruppo 'idref' = puntatore). Per ogni DRM: (tipo,id) puntati e non contenuti nel DRM.
Classifica: altri_mods / solo_base (bigfile PC o nessun mods) .  Uso: idref_selfcont.py MODS_DIR"""
import sys, os, glob, struct, json, collections
ROOT='/path/to/trudlcport'; sys.path.insert(0, ROOT+'/tools')
import drm, drm_reloc as R
base=sys.argv[1]
held={}; refs={}
for p in sorted(glob.glob(base+'/**/*.drm',recursive=True)):
    rel=os.path.relpath(p,base)
    try: secs=drm.sections_with_data(drm.cdrm_decode(open(p,'rb').read(),'le'),'le')[1]
    except Exception: continue
    held[rel]={(s['type'],s['id']) for s in secs}
    r_=[]
    for s in secs:
        if not s['data'] or not s['reloc']: continue
        r=R.parse(s['reloc'],'le')
        for t,o in r.idref: r_.append((s['type'],s['id'],t,struct.unpack_from('<I',s['data'],o)[0]))
    refs[rel]=r_
anyheld=collections.defaultdict(set)
for rel,h in held.items():
    for k in h: anyheld[k].add(rel)
basek=set()
for e in json.load(open(ROOT+'/work/idx_pc.json')):
    if isinstance(e[5],list):
        for s in e[5]: basek.add((s[0],s[1]))
res=collections.defaultdict(list)
for rel,r_ in refs.items():
    for st,sid,t,i in r_:
        if (t,i) in held[rel]: continue
        res['altri_mods' if anyheld.get((t,i)) else ('solo_base' if (t,i) in basek else 'NESSUNO')].append((rel,st,sid,t,i))
for cls,l in res.items():
    byt=collections.Counter(x[3] for x in l)
    print(cls,len(l),'(tipo:n)',dict(byt),'chiavi distinte',len({(x[3],x[4]) for x in l}))
json.dump(res,open(ROOT+'/work/ws/giro6/idref_selfcont.json','w'))
for cls in ('solo_base','NESSUNO'):
    c=collections.Counter((x[3],x[4]) for x in res.get(cls,[])); print(cls,c.most_common(20))
