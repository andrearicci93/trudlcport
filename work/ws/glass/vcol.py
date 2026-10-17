import sys,struct,collections,re
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC, drm_reloc as R
log=open('/path/to/trudlcport/work/runs/ch_B8_3/a1/engine.log').read()
names={m.lower().replace('\\','/') for m in re.findall(r'Loading PC-W\\(\S+\.drm) from mods',log)}
rows=[l.rstrip('\n').split('\t') for l in open('/path/to/trudlcport/work/ws/rebuild/installed_effective.tsv')][1:]
for r in rows:
    if r[0].lower() not in names: continue
    raw=cdrm_decode(open(r[4],'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['type']!=12 or s['data'][0x10:0x14] in (b'hseM',b'Mesh'): continue
        d=s['data']; T=TC.parse(d,'<'); H=T['H']; rel=R.parse(s['reloc'],'le')
        ml=[struct.unpack_from('<I',d,o)[0] for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]) if t==10]
        idx=np.frombuffer(d,'<u2',count=T['nIdx'],offset=H+T['offIdx']).astype(int)
        seen=set(); per=collections.defaultdict(set)
        for k,seq,es in TC.draw_lists(d,T,'<'):
            for y,n,st in es:
                if (y,st,n) in seen: continue
                seen.add((y,st,n)); Y=T['Y'][y]
                vb=T['vbs'][Y[1]]; vf=T['vfs'][vb[3]]
                col=[e for e in vf['elems'] if e[2]==4]
                if not col: continue
                stv=vf['stride']; arr=np.frombuffer(d,np.uint8,count=vb[2]*stv,offset=H+vb[0]).reshape(vb[2],stv)
                for v in set(idx[st:st+n].tolist()):
                    per[ml[Y[0]]].add(bytes(arr[v,col[0][1]:col[0][1]+4]))
        for m,cs in per.items():
            a=np.array([list(c) for c in cs])
            # color bytes order unknown: report distinct count and channel stats on first 3 bytes
            rgb=a[:,:3]; sat=(rgb.max(1)-rgb.min(1))
            print(r[0],s['id'],'mat',m,'distinct',len(cs),'maxsat',sat.max(),'n sat>80:',(sat>80).sum(), 'samples',[c.hex() for c in list(cs)[:4]])
