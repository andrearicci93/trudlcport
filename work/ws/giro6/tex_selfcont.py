"""Giro 6: autocontenimento texture. Per ogni DRM della baseline: texture puntate (idref tipo 5) NON contenute nel DRM stesso.
Classifica: contenuta in altri DRM mods / solo nel gioco base (bigfile PC) / in nessun posto.
Uso: tex_selfcont.py BASELINE"""
import sys, os, glob, struct, json, collections
ROOT='/path/to/trudlcport'; sys.path.insert(0, ROOT+'/tools')
import drm, drm_reloc as R
B=sys.argv[1]; base=B if os.path.isdir(B) else ROOT+'/work/baseline/%s/mods'%B; B=os.path.basename(B.rstrip('/')) if os.path.isdir(B) else B
held={}; refs={}
for p in sorted(glob.glob(base+'/**/*.drm',recursive=True)):
    rel=os.path.relpath(p,base)
    try: secs=drm.sections_with_data(drm.cdrm_decode(open(p,'rb').read(),'le'),'le')[1]
    except Exception: continue
    held[rel]={s['id'] for s in secs if s['type']==5}
    r_=[]
    for s in secs:
        if not s['data'] or not s['reloc']: continue
        r=R.parse(s['reloc'],'le')
        for t,o in r.idref:
            if t==5: r_.append((s['type'],s['id'],struct.unpack_from('<I',s['data'],o)[0]))
    refs[rel]=r_
anyheld=collections.defaultdict(set)
for rel,h in held.items():
    for t in h: anyheld[t].add(rel)
basetex=set()
for e in json.load(open(ROOT+'/work/idx_pc.json')):
    if isinstance(e[5],list):
        for s in e[5]:
            if s[0]==5: basetex.add(s[1])
out=collections.defaultdict(list)
for rel,r_ in refs.items():
    for st,sid,t in r_:
        if t in held[rel]: continue
        cls='altri_mods' if anyheld.get(t) else ('solo_base' if t in basetex else 'NESSUNO')
        out[cls].append((rel,st,sid,t))
print(B,'DRM',len(held))
for cls,l in out.items():
    print(cls,len(l),'texture distinte',len({x[3] for x in l}),'DRM',len({x[0] for x in l}))
json.dump({c:l for c,l in out.items()}, open(ROOT+'/work/ws/giro6/selfcont_%s.json'%B,'w'))
for cls in ('solo_base','NESSUNO'):
    c=collections.Counter(x[3] for x in out.get(cls,[]))
    print(cls,'top texture:',c.most_common(15))
