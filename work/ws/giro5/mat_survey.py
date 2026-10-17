"""Censimento materiali di uno o piu' DRM di una baseline: lib Xbox (DM) vs lib PC, classe del surrogato.
Uso: mat_survey.py BASE drm1.drm [drm2...]"""
import sys,io,contextlib,json,struct,collections
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import real_tex_gate as G
C=G.C; T=G.T; L=G.libs()
DM,D,P=L['DM'],L['D'],L['P']
sm=json.load(open(T+'work/render/dlc_shader_map.json'))
base=sys.argv[1]; tree=C.read_tree(T+'work/baseline/'+base+'/mods')
for name in sys.argv[2:]:
    secs=tree[name].sections; libsec={s.id:s for s in secs if s.type==9}
    print('==',name,'materiali',sum(1 for s in secs if s.type==10))
    for m in secs:
        if m.type!=10: continue
        pl=struct.unpack_from('<4I',m.data,0x28)
        if m.id in DM:
            xl=struct.unpack_from('>4I',DM[m.id][0],0x28)
        else: xl=None
        ent=C.entries(m.data,m.reloc,'le')
        cl=[]
        for p in range(4):
            x=xl[p] if xl else None
            e=sm.get(str(x)) if x not in (None,0,0xffffffff) else None
            cl.append('%s/%s%s'%(x,(e['cls']+(' sur' if e and e.get('surrogate') else '')) if e else '-',''))
        print(' mat',m.id,'PClib',pl,'Xlib',cl,'entries',[(e['type'],e['flag'],e['tex']) for e in ent])
