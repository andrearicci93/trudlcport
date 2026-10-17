import sys,os,struct,collections,json
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtp_audit as A, drm_write as DW, drm_reloc as R, dtpid_sweep as DS
W='/path/to/trudlcport/work'
DIRS=['vm_mods_expected','mods_fix12','mods_fix14','mods_glitchfix','mods_next','mods_fix16','mods_current','mods_current_webs','mods_fix18','mods_fix18_awf_extra','mods_fix20','chain_aim/mods_chainfix_min','menu_dlc/B','mods_dlc1_rc','ws/vmprep/chainsphere']
files=A.overlay([os.path.join(W,d) for d in DIRS])
st,ids=DS.ctx()
res=[]
def swap(v): return struct.unpack('<I',struct.pack('>I',v))[0]
for rel,path in sorted(files.items()):
    xs=A.xsecs(rel)
    if xs is None: continue
    D=DW.read(open(path,'rb').read(),'le')
    for x,i in A.section_pairs(xs,D):
        if x['type']!=7: continue
        sec=D.sections[i]
        if len(sec.data)!=len(x['data']): continue
        xr=R.parse(x['reloc'],'be')
        skip=set(xr.pointer_offsets())|set(xr.id_offsets())
        n=len(x['data'])//4
        xw=struct.unpack('>%dI'%n,x['data'][:n*4]); pw=struct.unpack('<%dI'%n,sec.data[:n*4])
        for k in range(n):
            if k*4 in skip: continue
            xv,pv=xw[k],pw[k]
            if pv==swap(xv) or xv==0: continue
            for t in (2,5,6,8,9,10,11,12):
                m=ids.base.get(t,{}).get(xv)
                if m is not None and m!=xv and m==pv:
                    res.append(dict(file=rel,sec=sec.id,xid=x['id'],off=k*4,xv=xv,pv=pv,t=t,base=bool(A.base_content(x)))); break
json.dump(res,open('otherid_scan.json','w'))
c=collections.Counter((r['t'],r['base']) for r in res); print(c)
for r in res:
    if not r['base'] and r['t']==9: print(r)
