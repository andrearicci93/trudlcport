import sys,os,hashlib,struct
sys.path.insert(0,'/path/to/trudlcport/tools')
import unbound_fix as U, drm_write as DW, drm_reloc as R, material_reslot as MR
B='/path/to/trudlcport/work/baseline/B8/mods/'; O='/path/to/trudlcport/work/ws/glass/out/'
lines=[]
for setn in ('lvl','all'):
    for dp,dn,fn in os.walk(O+setn):
        for f in sorted(fn):
            if not f.endswith('.drm'): continue
            rel=os.path.relpath(os.path.join(dp,f),O+setn)
            a=DW.read(open(B+rel,'rb').read(),'le'); b=DW.read(open(os.path.join(dp,f),'rb').read(),'le')
            assert len(a.sections)==len(b.sections) and a.names==b.names and a.pad==b.pad
            ch=[]
            for x,y in zip(a.sections,b.sections):
                assert (x.type,x.id,x.flags,x.ver,x.spec,x.pad)==(y.type,y.id,y.flags,y.ver,y.spec,y.pad)
                if x.data!=y.data or x.reloc!=y.reloc: ch.append((x,y))
            for x,y in ch:
                assert x.type==10
                u0,_=U.unbound(x.data,x.reloc); u1,_=U.unbound(y.data,y.reloc)
                e0=MR.tex_entries(x.data,R.parse(x.reloc,'le'),'<'); e1=MR.tex_entries(y.data,R.parse(y.reloc,'le'),'<')
                # everything outside the entry list identical modulo +16 shift
                T=dict(R.parse(x.reloc,'le').internal)[0x54]; ins=min(o for o,t,ty,sl in e1 if (o,)  and all(o!=q[0] or t!=q[1] for q in e0)) if False else None
                new=[e for e in e1 if e[1:]not in [q[1:] for q in e0]]
                line='%s [%s] sec type10 id %d: size %d->%d reloc %d->%d unbound %s -> %s; entries %d->%d; new entry %s; hdr50 %s -> %s; check=%s'%(rel,setn,x.id,len(x.data),len(y.data),len(x.reloc),len(y.reloc),[r for r,_,_ in u0],[r for r,_,_ in u1],len(e0),len(e1),[(t,ty,sl) for o,t,ty,sl in new],x.data[0x50:0x54].hex(),y.data[0x50:0x54].hex(),R.check(R.parse(y.reloc,'le'),len(y.data)))
                # old entries preserved (same id,type,slot) in order
                assert [(t,ty,sl) for o,t,ty,sl in e0]==[(t,ty,sl) for o,t,ty,sl in e1 if (t,ty,sl) not in [(n[1],n[2],n[3]) for n in new]]
                # params block identical
                pp=struct.unpack_from('<I',x.data,0x58)[0]; P0=dict(R.parse(x.reloc,'le').internal)[0x5c]; assert x.data[P0:P0+16*pp]==y.data[P0:P0+16*pp]
                lines.append(line)
            lines.append('%s [%s]: sections %d, changed %d, md5 %s'%(rel,setn,len(a.sections),len(ch),hashlib.md5(open(os.path.join(dp,f),'rb').read()).hexdigest()))
open(O+'DIFF.txt','w').write('\n'.join(lines)+'\n'); print('\n'.join(lines))
