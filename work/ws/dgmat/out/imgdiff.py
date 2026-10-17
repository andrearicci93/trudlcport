"""imgdiff.py REF.png AFTER.png [thr=24]: confronta l'area di gioco (640x480 in alto a sinistra) e riporta % pixel cambiati + bbox + un PNG di maschera.
Uso: tools/venv/bin/python -I imgdiff.py a1/shots/ref0.png a1/shots/after_m20530.png"""
import sys,numpy as np
from PIL import Image
a=np.asarray(Image.open(sys.argv[1]).convert('RGB').crop((0,0,640,480))).astype(int)
b=np.asarray(Image.open(sys.argv[2]).convert('RGB').crop((0,0,640,480))).astype(int)
t=int(sys.argv[3]) if len(sys.argv)>3 else 24
m=np.abs(a-b).max(2)>t; ys,xs=np.where(m)
print('changed %.2f%%'%(100*m.mean()), 'bbox',(xs.min(),ys.min(),xs.max(),ys.max()) if len(xs) else None)
Image.fromarray((m*255).astype('uint8')).save(sys.argv[2]+'.diff.png')
