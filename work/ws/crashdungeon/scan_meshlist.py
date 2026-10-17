import sys,os,struct,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtp_audit as A, drm_write as DW, drm_reloc as R, dtpid_sweep as DS
exec(open('scan_otherid.py').read().split('res=[]')[0].split('files=')[0])
W='/path/to/trudlcport/work'
DIRS=['vm_mods_expected','mods_fix12','mods_fix14','mods_glitchfix','mods_next','mods_fix16','mods_current','mods_current_webs','mods_fix18','mods_fix18_awf_extra','mods_fix20','chain_aim/mods_chainfix_min','menu_dlc/B','mods_dlc1_rc','ws/vmprep/chainsphere']
files=A.overlay([os.path.join(W,d) for d in DIRS])
def swap(v): return struct.unpack('<I',struct.pack('>I',v))[0]
tot=0;lists=0;bad=[]
for rel,path in sorted(files.items()):
    xs=A.xsecs(rel)
    if xs is None: continue
    D=DW.read(open(path,'rb').read(),'le')
    for x,i in A.section_pairs(xs,D):
        if x['type']!=7: continue
        sec=D.sections[i]; xd=x['data']
        if len(sec.data)!=len(xd) or len(xd)<12: continue
        xr=R.parse(x['reloc'],'be'); ids_=xr.id_offsets()
        n=struct.unpack('>I',xd[:4])[0]
        if not(ids_.get(4)==12 and n<64 and len(xd)>=8+16*n-12 and len(xd)<=8+16*n+8): continue
        if A.base_content(x): continue
        lists+=1
        # entries at 8+16k: {0 or flags,1?,idx,idref}
        for k in range(n):
            for w in (8+16*k, 12+16*k,16+16*k):
                if w+4>len(xd): continue
                xv=struct.unpack_from('>I',xd,w)[0]; pv=struct.unpack_from('<I',sec.data,w)[0]
                if pv!=xv: bad.append((rel,sec.id,w,xv,pv))
print('lists',lists,'bad',len(bad)); 
for b in bad: print(b)
