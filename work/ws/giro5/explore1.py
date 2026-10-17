import sys,io,contextlib,json,struct
sys.path.insert(0,'/path/to/trudlcport/work/ws/codefirst')
with contextlib.redirect_stdout(io.StringIO()):
    import real_tex_gate as G
F,C,H,F12,F10,sm3asm,libs=G.F,G.C,G.H,G.F12,G.F10,G.sm3asm,G.libs
T=G.T
mid=int(sys.argv[1]) if len(sys.argv)>1 else 20264
CT=G.CT; v=CT[str(mid)]
D=libs()['D']
xblob=D[v['dlc_lib']]['entries'][D[v['dlc_lib']]['slots'][0]]['blob']
sh=G.XL.parse(xblob)
print('XBOX ctab:'); 
for c in sh.ctab: print('  ',c)
t87=C.read_tree(T+'work/baseline/B87_materiali19/mods')
rel=v['drms'][0]
bcs=G.lib_bcs(t87,rel,v['lib'])
prog=sm3asm.decode(bcs[0])
import sm3dis
print('PC ctab:')
bc=bcs[0]
for n in (sm3dis.ctab_of(bc) or []): print('  ',n)
