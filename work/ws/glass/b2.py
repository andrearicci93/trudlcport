import sys,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import numpy as np
from archive import Archive
from drm import cdrm_decode, sections_with_data
import tex_convert as T
from PIL import Image
d=json.load(open('/path/to/trudlcport/work/idx_xbox_base.json'))
r=[x for x in d if x[5] and not isinstance(x[5],str) and any(s[0]==5 and s[1]==1006 for s in x[5])][0]
a=Archive(r[0],'be'); raw=cdrm_decode(a.read(a.idx[r[1]]),'be'); _,secs=sections_with_data(raw,'be')
for s in secs:
    if s['type']==5 and s['id']==1006:
        h=T.parse_xbox(s['data']); print('xbase',h)
        c=T.convert(s['data']); Image.fromarray(T.pc_image(c)).save('png/xbase_1006.png'); print(T.parse_pc(c))
