import sys,os,struct,collections
sys.path.insert(0,'/path/to/trudlcport/tools')
import dtp_audit as DA, drm_reloc as R, drm_write as DW
MAGIC=bytes.fromhex('04c20453')
dirs=DA.INSTALLED+['mods_fix20']+(sys.argv[1].split(',') if len(sys.argv)>1 else [])
tot=collections.Counter()
for rel,path in sorted(DA.overlay(dirs).items()):
    xs=DA.xsecs(rel)
    if xs is None: print('nosrc',rel); continue
    D=DW.read(open(path,'rb').read(),'le')
    for x,i in DA.section_pairs(xs,D):
        sec=D.sections[i]
        if x['type']!=7 or x['data'][:4]!=MAGIC: continue
        xd=x['data']; pd=sec.data
        if len(xd)<0x80 or len(pd)!=len(xd): 
            if x['data'][:4]==MAGIC and len(pd)!=len(xd): print('SIZEDIFF',rel,x['id'],len(xd),len(pd))
            continue
        rel_=R.parse(x['reloc'],'be'); it=dict(rel_.internal)
        n=struct.unpack_from('>I',xd,0x5c)[0]; a=it.get(0x60)
        npc=struct.unpack_from('<I',pd,0x5c)[0]
        if n!=npc: print('NCOUNT',rel,x['id'],n,npc)
        if not n or a is None: continue
        for q in range(n):
            o=a+32*q
            if o+32>len(xd): print('OOB',rel,x['id']); break
            xt=struct.unpack_from('>H',xd,o+2)[0]; xs_=struct.unpack_from('>H',xd,o)[0]
            pt=struct.unpack_from('<H',pd,o+2)[0]; ps=struct.unpack_from('<H',pd,o)[0]
            xid=struct.unpack_from('>I',xd,o+0x1c)[0]; pid=struct.unpack_from('<I',pd,o+0x1c)[0]
            tot['pts']+=1
            flag='' if (xt,xs_)==(pt,ps) else ' MISMATCH'
            if flag: tot['mismatch']+=1
            print('%s dtp%d sec%d pt%d seg %d/%d type %d/%d id %d/%d%s'%(rel,x['id'],sec.id,q,xs_,ps,xt,pt,xid,pid,flag))
print(dict(tot))
