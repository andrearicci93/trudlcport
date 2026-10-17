import sys,os,struct,hashlib
sys.path.insert(0,'/path/to/trudlcport/tools');sys.path.insert(0,'/path/to/trudlcport/work/ws/crash167')
import drm_write as DW, soundplex_fix as S, pairfix
W='/path/to/trudlcport/work/'
B=W+'baseline/B6/mods/'; O=W+'ws/crash167/out/'
f='dlc_dungeon.drm'
src=open(B+f,'rb').read(); raw=DW.cdrm_decode(src,'le'); D=DW.read(src,'le')
assert D.write('le')==raw
xs=S.xsecs_of(f); rows=['file\tsec_index\tsec_id\toff\tinstalled\tcorrected\txbox_BE_word']
n=0
for k,(x,s) in enumerate(zip(xs,D.sections)):
    if x['type']!=0 or x['data'] is None or len(x['data'])!=len(s.data): continue
    nd,ch=pairfix.fix_section(x['data'],s.data)
    if ch:
        for o,old,new in ch: rows.append('%s\t%d\t%d\t0x%x\t%s\t%s\t%s'%(f,k,s.id,o,old.hex(),new.hex(),x['data'][o:o+4].hex()))
        s.data=nd; n+=len(ch)
new=D.write('le'); assert len(new)==len(raw)
diff=[i for i in range(len(raw)) if raw[i]!=new[i]]
out=DW.cdrm_encode(new,'le'); assert DW.cdrm_decode(out,'le')==new and DW.read(out,'le').write('le')==new
print('words',n,'bytes differing in raw',len(diff),'cdrm same-format',DW.cdrm_encode(raw,'le')==src)
open(O+f,'wb').write(out)
open(O+'md5.txt','w').write('%s  %s\n'%(hashlib.md5(out).hexdigest(),f)); open(O+'words.tsv','w').write('\n'.join(rows)+'\n')
print(hashlib.md5(src).hexdigest(),'->',hashlib.md5(out).hexdigest(),len(src),len(out))
