import sys,json,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from archive import Archive
from drm import cdrm_decode, sections_with_data
import tex_convert as T
from PIL import Image
idx=json.load(open('/path/to/trudlcport/work/idx_pc.json'))
pc=Archive('/path/to/trudlcport/pc/bigfile.000','le')
def find_pc(tid):
    for r in idx:
        if r[5] and not isinstance(r[5],str) and any(s[0]==5 and s[1]==tid for s in r[5]): return r
r=find_pc(1207); print(r[:5])
rec=pc.idx[r[1]]; raw=cdrm_decode(pc.read(rec),'le'); _,secs=sections_with_data(raw,'le')
for s in secs:
    if s['type']==5 and s['id']==1207:
        print(T.parse_pc(s['data'])); Image.fromarray(T.pc_image(s['data'])).save('png/pcbase_1207.png')
