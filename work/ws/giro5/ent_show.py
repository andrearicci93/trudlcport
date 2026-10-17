import sys,io,contextlib,json,struct
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import real_tex_gate as G
C=G.C;T=G.T;L=G.libs();DM=L['DM']
tree=C.read_tree(T+'work/baseline/B87_materiali19/mods')
for spec in sys.argv[1:]:
    rel,mid=spec.split(':'); mid=int(mid)
    d=tree[rel]; s=[x for x in d.sections if x.type==10 and x.id==mid][0]
    xe=C.entries(*DM[mid],'be'); pe=C.entries(s.data,s.reloc,'le')
    print('== ',rel,mid,'PClib',struct.unpack_from('<4I',s.data,0x28),'Xlib',struct.unpack_from('>4I',DM[mid][0],0x28), 'len X/PC',len(DM[mid][0]),len(s.data))
    for k,(a,b) in enumerate(zip(xe,pe)):
        print('  e%d  X slot%d t%d f%d tex%d | PC slot%d t%d f%d tex%d  filt X%d PC%d bias %08x/%08x'%(k,a['slot'],a['type'],a['flag'],a['tex'],b['slot'],b['type'],b['flag'],b['tex'],a['filter'],b['filter'],a['bias'],b['bias']))
