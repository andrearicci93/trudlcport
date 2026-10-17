import sys,struct;sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import fnd
P='/path/to/trudlcport/work/baseline/B6/mods/dlc_dungeon.drm'
h,secs=fnd.load(P)
for s in secs:
    if s['i'] in (28,43,47,66):
        d=s['data']; print(s['i'],len(d),s['type'],s['id'])
        pat=b'\x00\x00\x80\xbf\x00\x00\x00\x00'
        i=d.find(pat); n=0
        while i>=0 and n<6:
            print(hex(i),d[i-0x14:i+0x30].hex()); i=d.find(pat,i+1); n+=1
