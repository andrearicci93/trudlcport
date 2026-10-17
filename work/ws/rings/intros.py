import sys,os,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm, unit_ids as U
def load(path):
    raw=drm.cdrm_decode(open(path,'rb').read(),'le')
    h,secs=drm.sections_with_data(raw,'le')
    return secs
def intros(path):
    secs=load(path); L=U.level_info(secs,'le')
    out=[]
    if not L: return out
    for si,o in L['intros']:
        d=secs[si]['data']
        f=struct.unpack_from('<4f',d,o); 
        oid=struct.unpack_from('<H',d,o+0x50)[0]; uid=struct.unpack_from('<I',d,o+0x58)[0]
        out.append((uid,oid,f,o,si))
    return out
if __name__=='__main__':
    objs={}
    for l in open('/path/to/trudlcport/work/generic/merged/tr8/pc-w/objectlist.txt'):
        a=l.strip().split(',',1)
        if len(a)==2 and a[0].isdigit(): objs[int(a[0])]=a[1]
    for p in sys.argv[1:]:
        print('==',p)
        for uid,oid,f,o,si in intros(p):
            nm=objs.get(oid,'?')
            if 'grapple' in nm or 'raft' in nm or 'bend' in nm or 'dragon' in nm or 'chain' in nm:
                print(uid,oid,nm,['%.0f'%x for x in f[:3]],hex(o))
