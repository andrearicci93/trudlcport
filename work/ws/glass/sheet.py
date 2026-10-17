import sys,os
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from drm import cdrm_decode, sections_with_data
import tex_convert as T
from PIL import Image, ImageDraw
f,out=sys.argv[1],sys.argv[2]
raw=cdrm_decode(open(f,'rb').read(),'le'); h,secs=sections_with_data(raw,'le')
ims=[]
for s in secs:
    if s['type']!=5: continue
    try: im=T.pc_image(s['data'])
    except Exception as e: continue
    ims.append((s['id'],Image.fromarray(im).convert('RGB')))
cell=128;cols=10
rows=(len(ims)+cols-1)//cols
sh=Image.new('RGB',(cols*cell,rows*(cell+12)),(40,40,40));d=ImageDraw.Draw(sh)
for n,(i,im) in enumerate(ims):
    im=im.resize((cell,cell)); x,y=(n%cols)*cell,(n//cols)*(cell+12); sh.paste(im,(x,y)); d.text((x+2,y+cell),str(i),fill=(255,255,0))
sh.save(out)
