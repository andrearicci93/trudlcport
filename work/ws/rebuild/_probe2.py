import sys, os, struct
sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/tools')); sys.path.insert(0, os.path.expanduser('~/Downloads/tru-port/work/ws/rebuild'))
import convert_fresh as CF, drm as D
from archive import Archive
from names import crc
import compare_rebuild as C
rel='dlc1_uo_pillar_of_doom_a.drm'; k=(7,22575,0)
arc=Archive(CF.PACK10,'be'); name=CF.pack10_drms()
nm=[n for n in name if n.endswith(rel)][0]
recs=[r for r in arc.find(crc(nm)) if r['spec']==0xffffffff]
raw=D.cdrm_decode(arc.read(recs[0]),'be'); h,secs,_=D.parse_drm(raw,'be')
xs=[s for s in secs if s['type']==7 and s['id']==22575][0]
xd=raw[xs['data_off']:xs['data_off']+xs['size']]
print('xbox BE word 0x60 =', '%08x'%struct.unpack_from('>I',xd,0x60)[0], 'xbox word0', '%08x'%struct.unpack_from('>I',xd,0)[0], 'size', len(xd))
ins,_,_=C.load(os.path.expanduser('~/Downloads/tru-port/work/mods_fix20/'+rel))
fr,_,_=C.load(os.path.join(C.HERE,'out_fresh',rel))
vm,_,_=C.load(os.path.expanduser('~/Downloads/tru-port/work/vm_mods_expected/'+rel))
for lab,d in (('inst',ins),('fresh',fr),('vm_base',vm)):
    x=d[k]['data']; print(lab, 'w0=%08x'%struct.unpack_from('<I',x,0)[0], 'w1=%08x'%struct.unpack_from('<I',x,4)[0], 'w0x60=%08x'%struct.unpack_from('<I',x,0x60)[0], 'w0x58..0x68', ['%08x'%struct.unpack_from('<I',x,o)[0] for o in range(0x58,0x68,4)])
print('xbox 0x58..0x68 BE', ['%08x'%struct.unpack_from('>I',xd,o)[0] for o in range(0x58,0x68,4)])
