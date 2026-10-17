import sys, pickle, struct, collections
T='/path/to/trudlcport/'
sys.path.insert(0,T+'tools')
import dtpid_sweep as DS, drm_write as DW
from soundplex_fix import xsecs_of
st, ids = DS.ctx(); ids.local={}
o=pickle.load(open(T+'work/ws/hintwire/scan.pkl','rb'))
for rel,v in sorted(o.items()):
    if v[0]=='ERR': continue
    xs=xsecs_of(rel); 
    D=DW.read(open(v[1],'rb').read(),'le')
    byid={(s.type,s.id):i for i,s in enumerate(D.sections)}
    for k,s in enumerate(xs):
        if s['type']!=8: continue
        b=s['data']; i=0
        while True:
            i=b.find(bytes.fromhex('beebbeeb'),i)
            if i<0: break
            if i+8<=len(b) and b[i+6:i+8]==b'\0\0':
                x=struct.unpack_from('>H',b,i+4)[0]
                if 1284<=x<=1406 and s['id']!=74:
                    nid=ids(8,s['id']); j=byid.get((8,nid))
                    pcl = len(D.sections[j].data) if j is not None else None
                    same = (j==k)
                    print(rel,v[0],'xsec',k,s['id'],'len',len(b),'off',i,'x',x,'pc idx',j,'pc len',pcl, 'samelen',pcl==len(b))
            i+=4
