import sys,re,os
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
W='/path/to/trudlcport/work/'
B=W+'baseline/B8/mods/'
for f in sys.argv[1:]:
    raw=drm.cdrm_decode(open(B+f,'rb').read(),'le'); secs=drm.sections_with_data(raw,'le')[1]
    print('##',f)
    for s in secs:
        if s['type']==8 and s['size']>200:
            out=[m.group(0).decode() for m in re.finditer(rb'[ -~]{6,}',s['data'])]
            out=[o for o in out if ' ' in o or o.endswith(':')]
            if out: print('  script',s['id'],s['size'],' | '.join(out)[:400])
