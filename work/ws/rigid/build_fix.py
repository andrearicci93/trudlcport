"""B5 candidate = B4/mods + ONE word: dlc1_uo_dragon_slider.drm DTP 20457 +0x10a0 (DESC@0x1088 +0x18 model_idx u8, +0x19) 00020000 -> 02000000."""
import sys,os,hashlib,shutil
sys.path.insert(0,'/path/to/trudlcport/work/ws/rigid')
import common as C
DW=C.DW
SRC=os.path.join(C.W,'baseline/B4/mods'); OUT=os.path.join(C.W,'ws/rigid/out')
rel='dlc1_uo_dragon_slider.drm'
raw=open(os.path.join(SRC,rel),'rb').read()
D=DW.read(raw,'le')
sec=[s for s in D.sections if s.type==7 and s.id==20457][0]
b=bytearray(sec.data); o=0x10a0
assert bytes(b[o:o+4]).hex()=='00020000', bytes(b[o:o+4]).hex()
b[o:o+4]=bytes.fromhex('02000000'); sec.data=bytes(b)
out=D.write('le')
if raw[:4]==b'CDRM': out=DW.cdrm_encode(out,'le')
os.makedirs(OUT,exist_ok=True)
dst=os.path.join(OUT,rel); open(dst,'wb').write(out)
# verify: only that word differs
D0=DW.read(raw,'le'); D2=DW.read(open(dst,'rb').read(),'le')
assert D0.names==D2.names and len(D0.sections)==len(D2.sections)
ch=[]
for a0,a2 in zip(D0.sections,D2.sections):
    assert (a0.type,a0.id,a0.reloc,a0.ver,a0.flags)==(a2.type,a2.id,a2.reloc,a2.ver,a2.flags)
    if a0.data!=a2.data: ch+=[(a0.id,j,a0.data[j],a2.data[j]) for j in range(len(a0.data)) if a0.data[j]!=a2.data[j]]
print(ch)
h=hashlib.md5(out).hexdigest(); open(os.path.join(OUT,'md5.txt'),'w').write('%s  %s\n'%(h,rel))
open(os.path.join(OUT,'diff.txt'),'w').write('%s DTP 20457 (object dragon_slider) @0x10a0 [DESC@0x1088 +0x18 model_idx u8 (+0x19 u8)] installed(B4)=00020000 -> 02000000 (Xbox bytes 02000000; engine reads BYTE +0x18: PC 0x4d795f movzx eax,byte[eax+0x18] / Xbox 0x8216cbb0 lbz r4,0x18(r27))\nbyte diffs: %s\nmd5 %s\n'%(rel,ch,h))
print(h)
