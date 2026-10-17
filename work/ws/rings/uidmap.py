import sys,struct,os,glob
sys.path.insert(0,'/path/to/trudlcport/work/ws/rings')
import intros as I
objs={}
for l in open('/path/to/trudlcport/work/generic/merged/tr8/pc-w/objectlist.txt',encoding='latin1').read().splitlines()[1:]:
    a=l.strip().split(',',1)
    if len(a)==2 and a[0].isdigit(): objs[int(a[0])]=a[1]   # PC ids (installed DRMs hold PC ids)
def allmap():
    m={}
    for p in sorted(glob.glob('/path/to/trudlcport/work/mods_current/dlc*.drm')):
        u=os.path.basename(p)[:-4]
        try: its=I.intros(p)
        except Exception as e: continue
        if not its: continue
        for uid,oid,f,o,si in its:
            dat=I.load(p)[si]['data']; pos=struct.unpack_from('<3f',dat,o+0x10)
            m.setdefault(uid,[]).append((u,objs.get(oid,'?%d'%oid),pos))
    return m
