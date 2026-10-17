"""Cerca una stringa (bytes) nelle sezioni decodificate dei DRM di una baseline. Uso: grep_drm.py BASE PATTERN [file_substr]"""
import sys,os
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm
R='/path/to/trudlcport/work/baseline/'
base,pat=sys.argv[1],sys.argv[2].encode(); sub=sys.argv[3] if len(sys.argv)>3 else ''
for r,_,fs in os.walk(R+base+'/mods'):
    for f in sorted(fs):
        if not f.endswith('.drm') or sub not in f: continue
        try: sc=drm.sections_with_data(drm.cdrm_decode(open(os.path.join(r,f),'rb').read(),'le'),'le')[1]
        except Exception: continue
        for s in sc:
            d=s['data']
            if d and pat in d:
                i=d.find(pat); print(f,'sez',s['i'],'type',s['type'],'id',s['id'],'@',hex(i),d[max(0,i-30):i+60])
