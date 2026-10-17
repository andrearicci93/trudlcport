"""Build out/all (every B8 DRM with a fixable unbound CUBE sampler) and out/min (only streamgroups/dlc_water_wheel_waterwheel_main.drm). Never writes into work/baseline."""
import sys,os,hashlib,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import unbound_fix as U, drm_write as DW, drm_reloc as R, material_reslot as MR
B='/path/to/trudlcport/work/baseline/B8/mods/'
O='/path/to/trudlcport/work/ws/glass/out/'
rows=U.scan(B)
files=sorted({f for f,mid,u,pt in rows if any(k==['cube'] for r,ns,k in u)})
rep=[]; md5=[]
LVL=['streamgroups/dlc_water_wheel_waterwheel_main.drm','dlc_caverns_hall.drm','streamgroups/dlc_pillory_pillorymain.drm','streamgroups/dlc_pillory_pillory_b.drm']
for set_name,flist in (('all',files),('lvl',LVL)):
    for f in flist:
        dst=O+set_name+'/'+f; os.makedirs(os.path.dirname(dst),exist_ok=True)
        n,r,m=U.fix_drm(B+f,dst,cube=569,coload=True)
        if n==0: print('SKIP unchanged',f,r); continue
        md5.append((set_name,f,m,n,r))
        if set_name=='all': pass
for set_name in ('all','lvl'):
    with open(O+set_name+'/md5.txt','w') as w:
        for s,f,m,n,r in md5:
            if s==set_name: w.write('%s  %s\n'%(m,f))
    print(set_name,[ (f,n,[(a,b) for a,b in r]) for s,f,m,n,r in md5 if s==set_name])
