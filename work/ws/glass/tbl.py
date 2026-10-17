import sys,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
import terrain_convert as TC, drm_reloc as R
V={}
for l in open('../mat/out/materials.tsv'):
    p=l.rstrip('\n').split('\t'); V[p[0]]=(p[1],p[7] if len(p)>7 else '')
Rt='/path/to/trudlcport/work/'
for f,ids in [(Rt+'mods_dlc1_rc/streamgroups/dlc_water_wheel_waterwheel_main.drm',(24024,24026)),(Rt+'mods_fix20/dlc_caverns_hall.drm',(20804,20806))]:
    raw=cdrm_decode(open(f,'rb').read(),'le'); _,secs=sections_with_data(raw,'le')
    for s in secs:
        if s['id'] not in ids: continue
        d=s['data']; T=TC.parse(d,'<'); rel=R.parse(s['reloc'],'le')
        mats=[struct.unpack_from('<I',d,o)[0] for t,o in sorted(rel.idref+rel.idref_a,key=lambda x:x[1]) if t==10]
        cnt=collections.Counter()
        for k,seq,es in TC.draw_lists(d,T,'<'):
            for y,n,st in es: cnt[T['Y'][y][0]]+=n
        print(s['id'])
        for i,m in enumerate(mats):
            v=V.get(str(m),('?',''))
            print('  mat#%d id %d idx %6d verdict %-18s %s'%(i,m,cnt[i],v[0],v[1][:70]))
