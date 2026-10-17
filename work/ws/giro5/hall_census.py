import sys,io,contextlib,json,struct,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import real_tex_gate as G
C=G.C; T=G.T; libs=G.libs
name=sys.argv[1] if len(sys.argv)>1 else 'dlc_caverns_hall.drm'
base=sys.argv[2] if len(sys.argv)>2 else 'B87_materiali19'
tree=C.read_tree(T+'work/baseline/'+base+'/mods')
secs=tree[name].sections
sm=json.load(open(T+'work/render/dlc_shader_map.json'))
mats=[s for s in secs if s.type==10]
libids={s.id for s in secs if s.type==9}
print(name,base,'materiali',len(mats),'lib',len(libids))
cnt=collections.Counter()
rows=[]
for m in mats:
    l=struct.unpack_from('<4I',m.data,0x28)
    ent=C.entries(m.data,m.reloc,'le')
    rows.append((m.id,l,len(ent)))
    for p,x in enumerate(l):
        if x in (0,0xffffffff): continue
        cnt[(p, 'dlc-dedicata' if x>=2700 and x in libids else ('in-drm' if x in libids else 'base'))]+=1
print(cnt)
for r in rows[:200]: print(r)
print('--- classi per lib (pos0..3)')
for mid,l,ne in rows:
    d=[]
    for p,x in enumerate(l):
        if x in (0,0xffffffff): d.append('-'); continue
        e=sm.get(str(x)); d.append('%d:%s' % (x, e['cls']+('>'+str(e['pc']) if e and e.get('surrogate') else '') if e else '?'))
    print(mid,ne,' '.join(d))
