import sys, os, struct, collections
sys.path.insert(0,'tools')
import drm_reloc as R, drm_write as DW, dtpid_sweep as DS
import dtp_audit as A, soundplex_nodes as N, soundplex_fix as SF
def pairs_for(name, dirs=None):
    dirs = dirs or A.INSTALLED
    ov = A.overlay(dirs, {name}); path = ov[name]
    xs = A.xsecs(name); D = DW.read(open(path,'rb').read(),'le')
    return xs, D, A.section_pairs(xs, D)
if __name__=='__main__':
    name, did = sys.argv[1], int(sys.argv[2])
    xs, D, prs = pairs_for(name)
    for x,i in prs:
        sec=D.sections[i]
        if sec.id!=did: continue
        xd=x['data']; pd=sec.data; rel=R.parse(x['reloc'],'be')
        nd,slots=N.nodes(xd,x['reloc'])
        print('len',len(xd),'nodes',len(nd))
        it=dict(rel.internal)
        for o in range(0,len(xd),4):
            tag='P' if o in set(rel.pointer_offsets()) else 'I' if o in set(rel.id_offsets()) else ' '
            print('%04x %s x=%s p=%s %s'%(o,tag,xd[o:o+4].hex(),pd[o:o+4].hex(), ('->%x'%it[o]) if o in it else ''))
