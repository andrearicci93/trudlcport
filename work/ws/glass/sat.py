import sys,pickle
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from drm import cdrm_decode, sections_with_data
import tex_convert as T
from PIL import Image, ImageDraw
rows=[l.rstrip('\n').split('\t') for l in open('../rebuild/installed_effective.tsv')][1:]
seen={};
for r in rows:
    if not r[0].endswith('.drm') or r[0]=='generalbank.drm': continue
    raw=cdrm_decode(open(r[4],'rb').read(),'le'); _,ps=sections_with_data(raw,'le')
    for s in ps:
        if s['type']!=5 or s['id'] in seen: continue
        h=T.parse_pc(s['data'])
        if h['fmt']==0x35545844 and False: pass
        im=T.pc_image(s['data']); rgb=im[...,:3].astype(float)
        sat=(rgb.max(2)-rgb.min(2)).mean()
        gnormal = (abs(rgb[...,1].mean()-255)<30 and rgb[...,2].mean()<30)
        seen[s['id']]=(sat,gnormal,r[0],h['w'],h['h'],hex(h['fmt']),im)
print(len(seen))
c=[(v[0],k,v) for k,v in seen.items() if not v[1]]
c.sort(key=lambda x:-x[0])
for sat,k,v in c[:60]: print(k,round(sat,1),v[2],v[3],v[4],v[5])
cell=128;cols=10;top=c[:60];rows_=(len(top)+cols-1)//cols
sh=Image.new('RGB',(cols*cell,rows_*(cell+12)),(40,40,40));d=ImageDraw.Draw(sh)
for n,(sat,k,v) in enumerate(top):
    x,y=(n%cols)*cell,(n//cols)*(cell+12); sh.paste(Image.fromarray(v[6]).convert('RGB').resize((cell,cell)),(x,y)); d.text((x+2,y+cell),str(k),fill=(255,255,0))
sh.save('png/sat_top.png')
