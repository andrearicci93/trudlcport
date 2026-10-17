import sys,os,glob,struct
sys.path.insert(0,'/path/to/trudlcport/tools'); sys.path.insert(0,'.')
import drm_write as DW, drm_reloc as R
W='/path/to/trudlcport/work/baseline/'
def mats(p):
    D=DW.read(open(p,'rb').read(),'le'); return {s.id:s for s in D.sections if s.type==10}
def ent(s):
    rel=R.parse(s.reloc,'le'); T=dict(rel.internal)[0x54]; n=len(rel and [o for t,o in rel.idref+rel.idref_a if t==5])
    return [s.data[T+16*i:T+16*i+16] for i in range(n)]
def chk(tag,q,p):
    a=mats(q);b=mats(p)
    for k in a:
        if a[k].data==b[k].data and a[k].reloc==b[k].reloc: continue
        ea,eb=ent(a[k]),ent(b[k]); ha=a[k].data[0x50:0x53]; hb=b[k].data[0x50:0x53]
        c51=ha[1]; c52=ha[2]
        new=[i for i,e in enumerate(eb) if e not in ea or eb.count(e)>ea.count(e)]
        ok=(len(eb)==len(ea)+1) and eb[:c52]==ea[:c52] if False else None
        # expected: new entry at old c52 index (end of groups A+B), group C content unchanged and located after
        ins=[i for i in range(len(eb)) if eb[:i]+eb[i+1:]==ea]
        print(tag,k,'old hdr',tuple(ha),'new hdr',tuple(hb),'inserted idx',ins,'ty',struct.unpack_from('<I',eb[ins[0]],8)[0] if ins else None,
              'OK' if ins and ins[0]==c52 and hb[0]==ha[0] else 'MISPLACED')
for r in ('dlc_caverns_hall.drm','streamgroups/dlc_water_wheel_waterwheel_main.drm','streamgroups/dlc_pillory_pillorymain.drm','streamgroups/dlc_pillory_pillory_b.drm'):
    chk('B10 '+r,W+'B8/mods/'+r,W+'B10/mods/'+r)
for r,o in (('dlc_caverns_hall.drm','out/dlc_caverns_hall.drm'),('streamgroups/dlc_water_wheel_waterwheel_main.drm','out/StreamGroups/dlc_water_wheel_waterwheel_main.drm')):
    chk('OUT '+r,W+'B8/mods/'+r,o)
