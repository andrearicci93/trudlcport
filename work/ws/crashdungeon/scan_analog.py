import sys,os,struct,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtpid_sweep as DS, dlc_generic as DG, dtp_audit as A, drm_reloc as R, drm_write as DW
W='/path/to/trudlcport/work'
DIRS=['vm_mods_expected','mods_fix12','mods_fix14','mods_glitchfix','mods_next','mods_fix16','mods_current','mods_current_webs','mods_fix18','mods_fix18_awf_extra','mods_fix20','chain_aim/mods_chainfix_min','menu_dlc/B','mods_dlc1_rc','ws/vmprep/chainsphere']
files=A.overlay([os.path.join(W,d) for d in DIRS])
st,ids=DS.ctx(); G0=DG._G0(); T=DG.table()
out=[];nan=0;ntot=0
for rel,path in sorted(files.items()):
    xs=A.xsecs(rel)
    if xs is None: continue
    ids.local={}
    D=DW.read(open(path,'rb').read(),'le')
    pairs=list(A.section_pairs(xs,D))
    labs0=None
    for x,i in pairs:
        if x['type']!=7 or x['id'] in ids.base.get(7,{}): continue
        ntot+=1
        res=DG.analog_convert(x,xs,ids,st,())
        if res is None: continue
        nan+=1
        sec=D.sections[i]
        if labs0 is None: labs0=G0.labels(xs,'be')
        k=xs.index(x); r=R.parse(x['reloc'],'be')
        gen=G0.convert_section0(x['data'],labs0[k],r,G0.table7(),ids,T)
        ad=res[0]
        if len(ad)!=len(gen) or len(sec.data)!=len(ad): continue
        n=len(ad)//4
        for w in range(0,n*4,4):
            a=ad[w:w+4]; g=gen[w:w+4]
            if a!=g:
                xv=struct.unpack_from('>I',x['data'],w)[0]
                out.append(dict(file=rel,sec=sec.id,off=w,xv=xv,analog=struct.unpack('<I',a)[0],gen=struct.unpack('<I',g)[0],inst=struct.unpack_from('<I',sec.data,w)[0] if w+4<=len(sec.data) else None))
json.dump(out,open('analog_vs_gen.json','w'))
print('type7 DLC-new',ntot,'analog',nan,'words analog!=gen',len(out))
c=collections.Counter(o['file'] for o in out); print(c.most_common(10))
