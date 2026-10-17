"""Confronto sezione per sezione di un DRM PC fra due baseline. Uso: cmp_drm.py NOME.drm [BASE_A BASE_B]"""
import sys,hashlib,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
from drm import cdrm_decode, sections_with_data
R='/path/to/trudlcport/work/baseline/'
def load(base,name):
    raw=open(R+base+'/mods/'+name,'rb').read(); raw=cdrm_decode(raw,'le'); return sections_with_data(raw,'le')
if __name__=='__main__':
    name=sys.argv[1]; A=sys.argv[2] if len(sys.argv)>2 else 'B84'; B=sys.argv[3] if len(sys.argv)>3 else 'B86_contratti'
    ha,sa=load(A,name); hb,sb=load(B,name)
    print(name,A,len(sa),'sezioni;',B,len(sb))
    import collections; ch=collections.Counter(); tot=collections.Counter()
    for a,b in zip(sa,sb):
        tot[a['type']]+=1
        if a['data']!=b['data'] or a['reloc']!=b['reloc'] or a['size']!=b['size']:
            ch[a['type']]+=1; print(f"  CAMBIATA sez{a['i']} type{a['type']} id{a['id']} size {a['size']}->{b['size']}")
    print('tipi totali',dict(tot),'cambiati',dict(ch))
