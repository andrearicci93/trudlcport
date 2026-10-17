import sys,os,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
B=W+'baseline/B8/mods/'
hit={}
for root,_,fs in os.walk(B):
    for f in fs:
        if not f.endswith('.drm'): continue
        p=os.path.join(root,f)
        try:
            raw=drm.cdrm_decode(open(p,'rb').read(),'le'); h,secs,_=drm.parse_drm(raw,'le')
        except Exception: continue
        for s in secs:
            if s['type']==9 and s['id'] in (975,976,332): hit.setdefault(s['id'],[]).append(os.path.relpath(p,B))
for k,v in hit.items(): print(k,len(v),v[:12])
