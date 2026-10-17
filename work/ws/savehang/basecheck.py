import sys,re
sys.path.insert(0,'tools')
import pairs as P
names=sorted(v[5:] for v in P.pcn.values() if v.lower().startswith('pc-w\\') and v.lower().endswith('.drm') and '\\' not in v[5:])
cmp=0;diff=0;nopair=0;tabs=0
for n in names:
    a=P.pc_drm(n); b=P.xbox_drm(n); a=a and a[1]; b=b and b[1]
    if not a or not b: nopair+=1; continue
    xt=[s for s in b if s['type']==0 and s['data'] and b'default\0' in s['data']]
    for x in xt:
        o=x['data'].find(b'default\0')
        m=[s for s in a if s['type']==0 and s['data'] and len(s['data'])==len(x['data']) and s['data'].find(b'default\0')==o]
        for s in m:
            if not all(c==0 or 32<=c<127 for c in x['data'][o:]): continue
            tabs+=1
            if s['data'][o:]!=x['data'][o:]: diff+=1; print('DIFF',n,s['data'][o:o+60],x['data'][o:o+60])
    cmp+=1
print('units',len(names),'paired',cmp,'nopair',nopair,'tables compared',tabs,'differing',diff)
