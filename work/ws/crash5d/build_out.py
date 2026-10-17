import sys,os,struct,hashlib
sys.path.insert(0,'/path/to/trudlcport/tools')
import drm_write as DW
W='/path/to/trudlcport/work/'
B=W+'baseline/B5/mods/'; O=W+'ws/crash5d/out/'
FIX=[('dlc_caverns.drm',20872,0x54b0+0x30,0xce),('dlc_dungeonhalla.drm',20493,0x6630+0x30,0xdd),('dlc_dungeonhallb.drm',20133,0x5b40+0x30,0xdf)]
md5=[];rows=['file\tdtp\toff\tinstalled\tcorrected\txbox_BE_word']
for f,sid,off,val in FIX:
    src=open(B+f,'rb').read(); raw=DW.cdrm_decode(src,'le'); D=DW.read(src,'le')
    assert D.write('le')==raw
    sec=[s for s in D.sections if s.type==7 and s.id==sid]; assert len(sec)==1; s=sec[0]
    old=struct.unpack_from('<I',s.data,off)[0]; assert old==val<<24,hex(old)
    assert s.data[off-0x30:off-0x30+16]==struct.pack('<IIII',0x403,0,0,0x300)
    b=bytearray(s.data); struct.pack_into('<I',b,off,val); s.data=bytes(b)
    new=D.write('le'); assert len(new)==len(raw)
    diff=[i for i in range(len(raw)) if raw[i]!=new[i]]; assert len(diff)==2,diff   # 0xdd000000 -> 0x000000dd: due byte (byte0 e byte3)
    out=DW.cdrm_encode(new,'le'); assert DW.cdrm_decode(out,'le')==new
    assert DW.read(out,'le').write('le')==new
    open(O+f,'wb').write(out)
    md5.append('%s  %s'%(hashlib.md5(out).hexdigest(),f)); rows.append('%s\t%d\t0x%x\t0x%08x\t0x%08x\t%08x'%(f,sid,off,old,val,val))
    print(f,'ok bytes diff',diff,'cdrm same-format-as-source?',DW.cdrm_encode(raw,'le')==src)
open(O+'md5.txt','w').write('\n'.join(md5)+'\n'); open(O+'words.tsv','w').write('\n'.join(rows)+'\n')
