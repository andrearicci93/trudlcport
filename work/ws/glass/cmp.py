import sys,os,csv,collections,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from archive import Archive
from drm import cdrm_decode, sections_with_data
from names import crc
import tex_convert as T
X=Archive('/path/to/Xenia-SteveRepack/Content/534307EC/00000002/9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000','be')
rows=[l.rstrip('\n').split('\t') for l in open('../rebuild/installed_effective.tsv')][1:]
res=[]
for r in rows:
    rel,abs_=r[0],r[4]
    if not rel.endswith('.drm'): continue
    name='xenon-w\\'+rel.replace('/','\\')
    rec=X.find(crc(name))
    if not rec: print('noxbox',rel); continue
    xraw=cdrm_decode(X.read(rec[0]),'be'); _,xs=sections_with_data(xraw,'be')
    praw=cdrm_decode(open(abs_,'rb').read(),'le'); _,ps=sections_with_data(praw,'le')
    xt=[s for s in xs if s['type']==5]; pt=[s for s in ps if s['type']==5]
    if len(xt)!=len(pt): print('count differs',rel,len(xt),len(pt)); 
    for a,b in zip(xt,pt):
        try: c=T.convert(a['data'])
        except Exception as e: res.append((rel,a['i'],a['id'],b['id'],'xerr',str(e))); continue
        if c==b['data']: res.append((rel,a['i'],a['id'],b['id'],'exact',''))
        else:
            hx=T.parse_pc(c); hp=T.parse_pc(b['data'])
            if (hx['fmt'],hx['w'],hx['h'],hx['mips'])!=(hp['fmt'],hp['w'],hp['h'],hp['mips']): res.append((rel,a['i'],a['id'],b['id'],'hdr',(hex(hx['fmt']),hx['w'],hx['h'],hx['mips'],hex(hp['fmt']),hp['w'],hp['h'],hp['mips'])))
            else:
                ix=T.pc_image(c).astype(int); ip=T.pc_image(b['data']).astype(int)
                res.append((rel,a['i'],a['id'],b['id'],'diff',round(float(np.abs(ix-ip).mean()),2)))
pickle.dump(res,open('cmp.pkl','wb'))
print(collections.Counter(r[4] for r in res))
for r in res:
    if r[4]!='exact': print(r)
