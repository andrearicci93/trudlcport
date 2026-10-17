import sys,io,contextlib,json,struct
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import real_tex_gate as G
F,C,H,F12,F10,sm3asm,libs=G.F,G.C,G.H,G.F12,G.F10,G.sm3asm,G.libs
T=G.T
tree=C.read_tree(T+'work/baseline/B87_materiali19/mods')
secs={(s.type,s.id):s for s in tree['dlc_caverns_hall.drm'].sections}
L=libs(); DM,D=L['DM'],L['D']
for mid in (22587,22588,22589):
    m=secs[(10,mid)]; pl=struct.unpack_from('<4I',m.data,0x28)
    xl=struct.unpack_from('>4I',DM[mid][0],0x28)
    print('== mat',mid,'PC libs',pl,'Xbox libs',xl)
    xe=C.entries(*DM[mid],'be'); pe=C.entries(m.data,m.reloc,'le')
    for k,(a,b) in enumerate(zip(xe,pe)): print('  entry',k,'X',a,'PC',b)
    lib=pl[2]; f=C.frame_lib(secs[(9,lib)].data)
    for k,o in enumerate(f['slots']):
        if o==0xFFFFFFFF: continue
        bc=f['entries'][o]['bc']; p=sm3asm.decode(bc)
        samp=sorted(i.ops[0].num for i in p.instrs() if i.op=='dcl' and i.ops[0].rtype==sm3asm.RT_SAMPLER)
        print('  variante',k,'sampler dcl',samp,'ninstr',len(p.instrs()))
    xs=XL=G.XL
    for s in set(D[xl[2]]['slots'])-{0xFFFFFFFF}:
        sh=XL.parse(D[xl[2]]['entries'][s]['blob'])
        print('  Xbox sampler ctab',[(c['name'][:40],c['reg']) for c in sh.ctab if c['set']==3])
