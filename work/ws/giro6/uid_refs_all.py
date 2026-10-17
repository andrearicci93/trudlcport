"""Giro 6 task 2: tutte le occorrenze (qualsiasi allineamento) dei 5 uid +20000 (u32 LE) in sezioni decodificate di OGNI DRM e nei file non-DRM (.mul ecc.). Uso: uid_refs_all.py MODS_DIR"""
import sys, os, glob, struct, re
ROOT='/path/to/trudlcport'; sys.path.insert(0, ROOT+'/tools')
import drm
R=sys.argv[1]; U=[29392,29397,29395,29396,26713]
pats={u:struct.pack('<I',u) for u in U}
n=0
for p in sorted(glob.glob(R+'/**/*', recursive=True)):
    if os.path.isdir(p): continue
    rel=os.path.relpath(p,R)
    if p.endswith('.drm'):
        try: secs=drm.sections_with_data(drm.cdrm_decode(open(p,'rb').read(),'le'),'le')[1]
        except Exception: continue
        for s in secs:
            d=s['data']
            for u,b in pats.items():
                for m in re.finditer(re.escape(b), d):
                    o=m.start(); n+=1
                    print('%-48s t%-2d id %-6d off %-7d%s uid %d' % (rel, s['type'], s['id'], o, ' (non allineato)' if o%4 else '', u))
    elif p.endswith(('.mul','.raw','.bin','.txt')):
        d=open(p,'rb').read()
        for u,b in pats.items():
            for m in re.finditer(re.escape(b), d):
                n+=1; print('%-48s FILE off %d uid %d' % (rel, m.start(), u))
print('tot', n)
